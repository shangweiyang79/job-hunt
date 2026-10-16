"""Dump a CV (.docx or .pptx) as plain text, each line tagged with the employer it sits under.

  python scripts/cv_text.py applications/<dir>/中文履歷_楊上瑋_公司.pptx

Used by the cv-judge agent, which reviews text instead of binary files. Employer tags come from
profile/attribution.yaml via tailor.employer_sections, the same mapping tailor.py enforces.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tailor import employer_sections, paragraphs_docx, paragraphs_pptx  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    path = Path(sys.argv[1])
    is_pptx = path.suffix.lower() == ".pptx"
    if is_pptx:
        from pptx import Presentation
        paras = list(paragraphs_pptx(Presentation(str(path))))
    else:
        import docx
        paras = list(paragraphs_docx(docx.Document(str(path))))
    section, _ = employer_sections(paras, is_pptx)
    for _, p in paras:
        text = p.text.strip()
        if text:
            owner = section.get(id(p._p))
            print(f"[{owner}] {text}" if owner else text)


if __name__ == "__main__":
    main()
