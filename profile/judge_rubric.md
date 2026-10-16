# CV judge rubric

The judge reviews one tailored CV against one JD. Deterministic checks already passed before the
judge runs (`tailor.py`: no new numbers, no project under the wrong employer, no overflow), so the
judge spends its effort on what a script cannot decide. Every FAIL must quote the CV line and the
evidence (a `candidate_facts.md` line or a JD line).

## 1. Fact fidelity — blocking
Every claim in the CV must trace to a specific line in `profile/candidate_facts.md`. "Plausible" is
not enough. FAIL when the CV:
- states a tool, method, scale or outcome that the facts file doesn't contain (e.g. Airflow, Spark,
  Kafka; "production" for the dbt layer, whose cutover is not done);
- upgrades a claim: "led" when the facts say "built", "deployed to N teams" with no source, or a
  number reused in a different meaning (e.g. +30% retrieval efficiency written as +30% revenue);
- changes a job title, employer, or date.

## 2. Attribution — blocking
Each bullet sits under the employer where the work happened (`profile/attribution.yaml`).
`cv_text.py` prefixes each bullet with its employer. Also check work the term list misses, e.g. a
generic "built dashboards" under the gallery when the dashboard facts are TaiwanPlus.

## 3. JD alignment
List the JD's top 3 core requirements. For each, say where the CV covers it, or that it's a gap.
FAIL only when the CV ignores a requirement the facts *do* support (a missed opportunity) or papers
over a gap with vague wording that implies experience the candidate lacks.

## 4. Narrative type (CLAUDE.md)
- DA / BI roles: Insight → Recommendation → Impact; tools secondary.
- DE / DS / AE / ML roles: method, architecture, rigor (pipelines, modeling, evals).
FAIL when the framing clearly fights the role (e.g. a DE CV led by marketing bullets).

## 5. Consistency and language
Title box matches the role; one language per CV (no stray English sentence in a Chinese CV beyond
tool names); no typos, broken punctuation, or duplicated content.

## Verdict
- **PASS** — 1 and 2 pass, and nothing in 3–5 would embarrass the candidate if sent today.
- **REVISE** — fixable issues; give concrete `suggested_edits` in `tailor.py` spec form
  (`{"match": "...", "text": "..."}`) using only facts-file content.
- **REJECT** — the JD needs experience the facts can't support (e.g. Spark in production as the
  core of the role). Say so plainly; do not try to rescue it.

Write the result as JSON to `<application dir>/judge.json`:
```json
{"verdict": "PASS|REVISE|REJECT",
 "checks": {"fact_fidelity": "PASS|FAIL", "attribution": "PASS|FAIL", "jd_alignment": "PASS|FAIL",
            "narrative": "PASS|FAIL", "consistency": "PASS|FAIL"},
 "jd_top3": [{"requirement": "...", "covered_by": "CV line or null"}],
 "issues": [{"check": "...", "cv_line": "...", "evidence": "...", "why": "..."}],
 "suggested_edits": [{"match": "...", "text": "..."}]}
```
