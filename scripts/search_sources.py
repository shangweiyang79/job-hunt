"""Collect recent job postings from sources with usable endpoints (104, LinkedIn guest API).

Other boards (CakeResume, Yourator, TokyoDev, Japan Dev, Daijob) are searched by the routine
itself with WebSearch/WebFetch; see config/criteria.yaml.

  python scripts/search_sources.py --source 104 linkedin --out data/raw_jobs.json
  python scripts/search_sources.py --detail 104:92w1u      print one full JD

Output: JSON list of {source, job_id, url, title, company, location, posted, salary, snippet}
filtered by title include/exclude rules and the date window. Failures are reported per source
in the "errors" key, never raised, so one blocked site does not stop the run.
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"}


def load_cfg():
    return yaml.safe_load((ROOT / "config" / "criteria.yaml").read_text(encoding="utf-8"))


def title_ok(title, cfg):
    t = title.lower()
    return (any(k in t for k in cfg["roles"]["include_title"])
            and not any(k in t for k in cfg["roles"]["exclude_title"]))


def search_104(cfg, since):
    jobs, seen = [], set()
    for kw in cfg["search_keywords"]["tw"]:
        for page in range(1, 4):
            r = requests.get("https://www.104.com.tw/jobs/search/api/jobs",
                             params={"keyword": kw, "area": cfg["locations"]["tw"]["area_104"],
                                     "order": 16, "page": page, "pagesize": 30, "jobsource": "index_s"},
                             headers={**UA, "Referer": "https://www.104.com.tw/jobs/search/"}, timeout=30)
            r.raise_for_status()
            data = r.json().get("data", [])
            if not data:
                break
            fresh = 0
            for x in data:
                posted = dt.datetime.strptime(x["appearDate"], "%Y%m%d").date()
                if posted < since:
                    continue
                fresh += 1
                job_id = x["link"]["job"].rstrip("/").split("/")[-1].split("?")[0]
                if job_id in seen or not title_ok(x["jobName"], cfg):
                    continue
                seen.add(job_id)
                lo, hi = x.get("salaryLow") or 0, x.get("salaryHigh") or 0
                jobs.append({
                    "source": "104", "job_id": job_id, "url": f"https://www.104.com.tw/job/{job_id}",
                    "title": x["jobName"], "company": x["custName"], "location": x["jobAddrNoDesc"],
                    "posted": posted.isoformat(),
                    "salary": f"{lo:,}–{hi:,}" if hi and hi < 9999999 else (f"{lo:,}+" if lo else "面議"),
                    "snippet": re.sub(r"\s+", " ", x.get("description", ""))[:300],
                })
            if fresh == 0:   # results are newest-first after the pinned ad; stop paging once stale
                break
            time.sleep(1)
    return jobs


def search_linkedin(cfg, since):
    jobs, seen = [], set()
    days = (dt.date.today() - since).days or 1
    for region, loc in (("tw", "Taiwan"), ("jp", "Japan")):
        for kw in cfg["search_keywords"][region]:
            r = requests.get("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
                             params={"keywords": kw, "location": loc, "f_TPR": f"r{days * 86400}", "start": 0},
                             headers=UA, timeout=30)
            if r.status_code == 429:
                raise RuntimeError("LinkedIn rate-limited (HTTP 429); use WebSearch fallback")
            r.raise_for_status()
            for card in r.text.split("<li>")[1:]:
                m_id = re.search(r"jobPosting:(\d+)", card)
                m_t = re.search(r'base-search-card__title">\s*(.*?)\s*<', card, re.S)
                m_c = re.search(r'base-search-card__subtitle">.*?>\s*(.*?)\s*<', card, re.S)
                m_l = re.search(r'job-search-card__location">\s*(.*?)\s*<', card, re.S)
                m_d = re.search(r'datetime="(\d{4}-\d{2}-\d{2})"', card)
                if not (m_id and m_t):
                    continue
                jid, title = m_id.group(1), m_t.group(1).strip()
                if jid in seen or not title_ok(title, cfg):
                    continue
                seen.add(jid)
                jobs.append({
                    "source": "linkedin", "job_id": jid, "url": f"https://www.linkedin.com/jobs/view/{jid}",
                    "title": title, "company": m_c.group(1).strip() if m_c else "",
                    "location": m_l.group(1).strip() if m_l else loc,
                    "posted": m_d.group(1) if m_d else "", "salary": "", "snippet": "",
                })
            time.sleep(2)
    return jobs


def detail(spec):
    source, jid = spec.split(":", 1)
    if source == "104":
        r = requests.get(f"https://www.104.com.tw/job/ajax/content/{jid}",
                         headers={**UA, "Referer": f"https://www.104.com.tw/job/{jid}"}, timeout=30)
        d = r.json()["data"]
        c = d["condition"]
        return {
            "title": d["header"]["jobName"], "company": d["header"]["custName"],
            "description": d["jobDetail"]["jobDescription"],
            "work_exp": c.get("workExp"), "edu": c.get("edu"),
            "skills": [s["description"] for s in (c.get("specialty") or []) + (c.get("skill") or [])],
            "language": c.get("language"), "other": c.get("other"),
            "salary": d["jobDetail"].get("salary"), "address": d["jobDetail"].get("addressRegion"),
        }
    if source == "linkedin":
        r = requests.get(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}", headers=UA, timeout=30)
        r.raise_for_status()
        m = re.search(r'show-more-less-html__markup[^>]*>(.*?)</div>', r.text, re.S)
        text = re.sub(r"<[^>]+>", "\n", m.group(1)) if m else ""
        return {"description": re.sub(r"\n\s*\n+", "\n", text).strip()}
    raise SystemExit(f"unknown source {source}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", nargs="+", default=["104", "linkedin"])
    ap.add_argument("--out")
    ap.add_argument("--detail")
    ap.add_argument("--with-details", action="store_true",
                    help="also fetch the full 104 JD for every job (the cloud routine can't reach 104)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if a.detail:
        print(json.dumps(detail(a.detail), ensure_ascii=False, indent=2))
        return

    cfg = load_cfg()
    since = dt.date.today() - dt.timedelta(days=cfg["window_days"])
    result = {"fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
              "since": since.isoformat(), "jobs": [], "errors": {}}
    for s in a.source:
        try:
            found = {"104": search_104, "linkedin": search_linkedin}[s](cfg, since)
            result["jobs"] += found
            print(f"{s}: {len(found)} jobs", file=sys.stderr)
        except Exception as e:
            result["errors"][s] = str(e)
            print(f"{s}: FAILED {e}", file=sys.stderr)
    if a.with_details:
        for job in result["jobs"]:
            if job["source"] != "104":
                continue
            try:
                job["detail"] = detail(f"104:{job['job_id']}")
            except Exception as e:
                job["detail_error"] = str(e)
            time.sleep(0.5)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
