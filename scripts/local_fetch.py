"""Weekly local fetch, run by Windows Task Scheduler before the cloud routine.

104 refuses cloud-server IPs, so this PC searches 104 (with full JDs) and pushes the result
to data/raw_jobs_local.json. The Monday cloud routine reads that file.

  python scripts/local_fetch.py
Log: data/local_fetch.log (not committed).
"""
import datetime as dt
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "raw_jobs_local.json"
LOG = REPO / "data" / "local_fetch.log"


def run(*cmd):
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log(f"$ {' '.join(cmd)} -> {r.returncode}\n{r.stdout[-2000:]}{r.stderr[-2000:]}")
    return r.returncode


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")


def main():
    log("=== local fetch start")
    run("git", "pull", "-q", "--ff-only")
    if run(sys.executable, "scripts/search_sources.py", "--source", "104", "linkedin",
           "--with-details", "--out", str(OUT)) != 0:
        log("search failed; nothing pushed")
        sys.exit(1)
    run("git", "add", str(OUT.relative_to(REPO)))
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO).returncode != 0:
        run("git", "-c", "user.name=Shangwei Yang", "-c", "user.email=shangweiyang79@gmail.com",
            "commit", "-q", "-m", f"Local 104 fetch {dt.date.today():%Y-%m-%d}")
        if run("git", "push", "-q") != 0:
            log("push failed")
            sys.exit(1)
    log("=== local fetch done")


if __name__ == "__main__":
    main()
