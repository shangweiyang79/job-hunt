# job-hunt (private)

Weekly job radar plus resume-template sync for Joy Yang. North Taiwan and Japan; DA / BI / DS / DE / AE roles.

| Path | What |
|---|---|
| `ROUTINE_PROMPT.md` | Prompt the weekly cloud routine runs (Mon 09:00 Taipei) |
| `config/criteria.yaml` | Titles, locations, sources, scoring, already-applied list |
| `profile/candidate_facts.md` | The only facts a tailored CV may use |
| `templates/` | Mirrored from `E:\面試準備\Resume` and `中文履歷` by `drive_sync.py`; don't edit here |
| `scripts/search_sources.py` | 104 JSON API and LinkedIn guest API search; `--detail 104:<id>` for a full JD |
| `scripts/tailor.py` | Apply a JSON edit spec to a template; rejects invented numbers and overflow |
| `scripts/render_pdf.sh` | LibreOffice → PDF and page count (approximate in the cloud) |
| `scripts/notify_telegram.py` | Bot API message and attachments |
| `scripts/drive_sync.py` | Local templates → Drive 求職/應徵最新; `--upload` for routine outputs |
| `data/seen_jobs.csv` | Dedupe ledger |
| `runs/` | One report per week |

Routine environment variables: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GDRIVE_TOKEN_JSON`.
