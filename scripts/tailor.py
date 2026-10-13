"""Apply a JSON edit spec to a resume template (.docx or .pptx) without touching the layout.

  python scripts/tailor.py spec.json

spec.json:
{
  "template": "templates/Resume_Shangwei Yang_Data Analyst.docx",
  "output":   "out/2026-10-20_Acme_Data-Analyst/Resume_Shangwei Yang_Acme.docx",
  "edits": [
    {"match": "Business Insights:", "text": "Business Insights: Analyzed ..."},
    {"match": "Coordinated cross-border", "delete": true}
  ]
}

"match" is a prefix of exactly one existing paragraph. "text" replaces it; a leading
"Label: " / "標籤：" goes into the original bold label run and the rest into the body run,
so fonts, bullets, and bold labels are preserved.

Guards (the script exits 1 and writes nothing if either fails):
  * numbers: every number in the new text must already appear in profile/candidate_facts.md
    or in the template, so tailoring can never invent a metric;
  * length: docx paragraphs may grow at most --max-growth (default 1.3x); pptx text boxes
    must not exceed their original character count, so the one-page photo CV stays one page.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUM = re.compile(r"\d+(?:[.,]\d+)*(?:\s?[%xX倍萬KM](?![A-Za-z]))?")
LABEL = re.compile(r"^(.{1,40}?(?::\s|：))(.*)$", re.S)


def numbers(text, with_bare=False):
    """Number tokens keep their unit, so "2M" is not excused by an unrelated "2" elsewhere."""
    out = set()
    for n in NUM.findall(text):
        tok = n.replace(",", "").replace(" ", "").replace("X", "x")
        out.add(tok)
        if with_bare:
            out.add(re.match(r"[\d.]+", tok).group(0))
    return out


def is_bold(run):
    # python-docx runs expose .bold; python-pptx runs only .font.bold
    return bool(run.bold) if hasattr(run, "bold") else bool(run.font.bold)


def set_paragraph_text(runs, text):
    """Write text into existing runs, keeping a bold label prefix bold."""
    runs = [r for r in runs]
    if not runs:
        raise ValueError("paragraph has no runs")
    n_label = 0
    while n_label < len(runs) and is_bold(runs[n_label]):
        n_label += 1
    m = LABEL.match(text)
    if m and 0 < n_label < len(runs):
        label, body = m.group(1), m.group(2)
        # keep the template's spacing convention: either "Label:" + " body" or "Label: " + "body"
        runs[0].text = label.rstrip() if runs[n_label].text.startswith(" ") else label
        for r in runs[1:n_label]:
            r.text = ""
        runs[n_label].text = (" " + body.lstrip()) if runs[n_label].text.startswith(" ") else body
        for r in runs[n_label + 1:]:
            r.text = ""
    else:
        runs[0].text = text
        for r in runs[1:]:
            r.text = ""


def paragraphs_docx(doc):
    for p in doc.paragraphs:
        yield None, p
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield None, p


def paragraphs_pptx(prs):
    def walk(shapes):
        for sh in shapes:
            if sh.shape_type == 6:  # group
                yield from walk(sh.shapes)
            elif sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    yield sh, p
    for slide in prs.slides:
        yield from walk(slide.shapes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--max-growth", type=float, default=1.3)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    template = ROOT / spec["template"]
    out = Path(spec["output"])
    out = out if out.is_absolute() else ROOT / out
    is_pptx = template.suffix.lower() == ".pptx"

    if is_pptx:
        from pptx import Presentation
        doc = Presentation(str(template))
        paras = list(paragraphs_pptx(doc))
    else:
        import docx
        doc = docx.Document(str(template))
        paras = list(paragraphs_docx(doc))

    template_text = "\n".join(p.text for _, p in paras)
    facts = (ROOT / "profile" / "candidate_facts.md").read_text(encoding="utf-8")
    allowed = numbers(template_text, with_bare=True) | numbers(facts, with_bare=True)
    original_box_len = {}
    if is_pptx:
        for sh, p in paras:
            original_box_len[sh.shape_id] = original_box_len.get(sh.shape_id, 0) + len(p.text)

    problems = []
    for e in spec["edits"]:
        hits = [(sh, p) for sh, p in paras if p.text.strip().startswith(e["match"])]
        if len(hits) != 1:
            problems.append(f"match {e['match']!r}: {len(hits)} paragraphs (need exactly 1)")
            continue
        sh, p = hits[0]
        if e.get("delete"):
            p._p.getparent().remove(p._p)
            continue
        new = e["text"]
        invented = numbers(new) - allowed
        if invented:
            problems.append(f"match {e['match']!r}: numbers not in facts/template: {sorted(invented)}")
        if not is_pptx and len(new) > len(p.text) * a.max_growth + 20:
            problems.append(f"match {e['match']!r}: {len(new)} chars > {a.max_growth}x original {len(p.text)}")
        set_paragraph_text(p.runs, new)

    if is_pptx:
        current = {}
        for sh, p in paragraphs_pptx(doc):
            current[sh.shape_id] = current.get(sh.shape_id, 0) + len(p.text)
        for sid, n in current.items():
            if n > original_box_len.get(sid, n):
                problems.append(f"text box {sid}: {n} chars > original {original_box_len[sid]} (would overflow the page)")

    if problems:
        print("REJECTED\n  " + "\n  ".join(problems))
        sys.exit(1)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    print(f"OK {out}")


if __name__ == "__main__":
    main()
