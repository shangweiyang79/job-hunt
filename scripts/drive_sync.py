"""Mirror the resume templates in E:\\面試準備 to Google Drive 求職/應徵最新.

Local is the source of truth:
  Resume/            -> 應徵最新/英文/最新      Resume/archive/   -> 應徵最新/英文/archive
  中文履歷/           -> 應徵最新/中文/最新      中文履歷/archive/  -> 應徵最新/中文/archive

Changed files are overwritten in place (files.update), so Drive keeps the
revision history. Files moved into a local archive/ folder are moved on Drive
too; nothing is ever deleted.

Usage:
  python drive_sync.py --login                 one-time OAuth consent (local)
  python drive_sync.py                         dry run: print what would change
  python drive_sync.py --apply                 sync
  python drive_sync.py --auto --apply          sync only if local files changed (Stop hook)
  python drive_sync.py --apply --archive-stale also move Drive-only files out of 最新
  python drive_sync.py --upload a.pdf b.pptx --folder-path 自動客製/2026-10-20_公司_職稱
                                               upload outputs (used by the weekly routine)

Credentials: .secrets/drive_token.json under --root, or the GDRIVE_TOKEN_JSON
environment variable (authorized-user JSON) in the cloud routine.
"""
import argparse
import hashlib
import json
import mimetypes
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"

APPLY_ROOT_ID = "1-XemFVnfTAh8N2RfyaelW-IcX7BiYsrq"  # 求職/應徵最新
MAPPINGS = [
    {   # local dir, Drive 最新 folder, Drive language folder (parent of 最新 and archive)
        "local": "Resume",
        "latest_id": "108jdGVDk6H-48H2QW2-2qAX_SdV03N9U",  # 應徵最新/英文/最新
        "lang_id": "1-a3sJEQ7MxEcATGF2K2_Tpl4N5gyxJ7F",    # 應徵最新/英文
    },
    {
        "local": "中文履歷",
        "latest_id": "15JMNbtiB1lMIti0ETfUlspFc5IuZ61AH",  # 應徵最新/中文/最新
        "lang_id": "1-k9hIQVBV0jcaiWcZ3r4JDqUR1nlfOAZ",    # 應徵最新/中文
    },
]
SYNC_EXTS = {".docx", ".pdf", ".pptx"}
MANIFEST_NAME = ".drive_sync_manifest.json"

mimetypes.add_type("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx")
mimetypes.add_type("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def local_files(root):
    """{relpath: Path} for every template and archived file, skipping Office lock files."""
    out = {}
    for m in MAPPINGS:
        base = root / m["local"]
        for sub in (base, base / "archive"):
            if not sub.is_dir():
                continue
            for p in sub.iterdir():
                if p.is_file() and p.suffix.lower() in SYNC_EXTS and not p.name.startswith("~$"):
                    out[p.relative_to(root).as_posix()] = p
    return out


# ---------------------------------------------------------------- credentials

def load_creds(root, interactive=False):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    token_path = root / ".secrets" / "drive_token.json"
    env = os.environ.get("GDRIVE_TOKEN_JSON")
    if env:
        creds = Credentials.from_authorized_user_info(json.loads(env), SCOPES)
    elif token_path.exists() and not interactive:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    else:
        if not interactive:
            sys.exit(f"drive_sync: no credentials. Run `python {Path(__file__).name} --login` first.")
        from google_auth_oauthlib.flow import InstalledAppFlow
        secret = root / ".secrets" / "client_secret.json"
        if not secret.exists():
            sys.exit(f"drive_sync: missing {secret}")
        creds = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES).run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        print(f"Saved token to {token_path}")
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        if not env:
            token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def service(root, interactive=False):
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=load_creds(root, interactive), cache_discovery=False)


# ---------------------------------------------------------------- Drive helpers

def q_escape(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def list_folder(svc, folder_id):
    items, token = [], None
    while True:
        r = svc.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(id, name, mimeType, md5Checksum, webViewLink)",
            pageSize=200, pageToken=token).execute()
        items += r["files"]
        token = r.get("nextPageToken")
        if not token:
            return items


def ensure_folder(svc, parent_id, name, apply):
    r = svc.files().list(
        q=f"'{parent_id}' in parents and name = '{q_escape(name)}' and mimeType = '{FOLDER_MIME}' and trashed = false",
        fields="files(id)").execute()["files"]
    if r:
        return r[0]["id"]
    if not apply:
        return None
    return svc.files().create(body={"name": name, "mimeType": FOLDER_MIME, "parents": [parent_id]},
                              fields="id").execute()["id"]


def upload(svc, path, parent_id, file_id=None):
    from googleapiclient.http import MediaFileUpload
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    media = MediaFileUpload(str(path), mimetype=mime, resumable=True)
    if file_id:
        return svc.files().update(fileId=file_id, media_body=media, fields="id, md5Checksum, webViewLink").execute()
    return svc.files().create(body={"name": path.name, "parents": [parent_id]}, media_body=media,
                              fields="id, md5Checksum, webViewLink").execute()


def move(svc, file_id, old_parent, new_parent):
    svc.files().update(fileId=file_id, addParents=new_parent, removeParents=old_parent, fields="id").execute()


# ---------------------------------------------------------------- sync

def sync(root, apply, archive_stale):
    svc = service(root)
    manifest_path = root / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    files = local_files(root)
    changes = 0

    for m in MAPPINGS:
        latest_id = m["latest_id"]
        archive_id = ensure_folder(svc, m["lang_id"], "archive", apply)
        latest = {f["name"]: f for f in list_folder(svc, latest_id) if f["mimeType"] != FOLDER_MIME}
        archived = {f["name"]: f for f in list_folder(svc, archive_id)} if archive_id else {}
        tracked = set()

        for rel, path in sorted(files.items()):
            if not rel.startswith(m["local"] + "/"):
                continue
            in_archive = rel.startswith(m["local"] + "/archive/")
            target_id = archive_id if in_archive else latest_id
            here = archived if in_archive else latest
            there = latest if in_archive else archived
            local_md5 = md5(path)
            tracked.add(path.name)

            if path.name in here:
                remote = here[path.name]
                if remote.get("md5Checksum") == local_md5:
                    manifest[rel] = {"id": remote["id"], "md5": local_md5}
                    continue
                action, fid = "UPDATE", remote["id"]
            elif path.name in there:
                # moved between 最新 and archive locally: move on Drive, then compare content
                remote = there[path.name]
                print(f"  MOVE    {rel}  ({'最新 -> archive' if in_archive else 'archive -> 最新'})")
                changes += 1
                if apply:
                    move(svc, remote["id"], latest_id if in_archive else archive_id, target_id)
                if remote.get("md5Checksum") == local_md5:
                    manifest[rel] = {"id": remote["id"], "md5": local_md5}
                    continue
                action, fid = "UPDATE", remote["id"]
            else:
                action, fid = "CREATE", None

            print(f"  {action:<7} {rel}")
            changes += 1
            if apply:
                r = upload(svc, path, target_id or "", fid)
                manifest[rel] = {"id": r["id"], "md5": r.get("md5Checksum", local_md5)}

        stale = [f for name, f in latest.items() if name not in tracked]
        for f in stale:
            print(f"  STALE   {m['local']}: Drive 最新 has '{f['name']}' with no local copy"
                  + (" -> archive" if archive_stale else " (use --archive-stale to move it)"))
            if archive_stale:
                changes += 1
                if apply:
                    move(svc, f["id"], latest_id, archive_id)

    # forget manifest entries for files that no longer exist locally
    for rel in [r for r in manifest if r not in files]:
        del manifest[rel]
    if apply:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{changes} change(s){'' if apply else ' (dry run; add --apply to sync)'}")
    return changes


def unchanged_since_last_sync(root):
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.exists():
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = local_files(root)
    if set(files) != set(manifest):
        return False
    return all(md5(p) == manifest[rel]["md5"] for rel, p in files.items())


def mirror_to_repo(root):
    """Copy current templates (not archive) into job-hunt/templates and push, for the cloud routine."""
    repo = root / "job-hunt"
    if not (repo / ".git").exists():
        return
    dest = repo / "templates"
    dest.mkdir(exist_ok=True)
    wanted = {}
    for m in MAPPINGS:
        for p in (root / m["local"]).iterdir():
            if p.is_file() and p.suffix.lower() in {".docx", ".pptx"} and not p.name.startswith("~$"):
                wanted[p.name] = p
    for old in dest.iterdir():
        if old.is_file() and old.name not in wanted:
            old.unlink()
    for name, p in wanted.items():
        if not (dest / name).exists() or md5(dest / name) != md5(p):
            shutil.copy2(p, dest / name)
    git = ["git", "-C", str(repo)]
    subprocess.run(git + ["add", "-A", "templates"], check=True)
    if subprocess.run(git + ["diff", "--cached", "--quiet"]).returncode != 0:
        subprocess.run(git + ["commit", "-q", "-m", "Update resume templates from local"], check=True)
        if subprocess.run(git + ["push", "-q"]).returncode != 0:
            print("drive_sync: templates committed but git push failed", file=sys.stderr)
        else:
            print("  REPO    templates pushed to job-hunt")


def upload_outputs(root, paths, folder_path):
    svc = service(root)
    parent = APPLY_ROOT_ID
    for part in [p for p in folder_path.split("/") if p]:
        parent = ensure_folder(svc, parent, part, apply=True)
    for p in map(Path, paths):
        r = upload(svc, p, parent)
        print(json.dumps({"file": p.name, "id": r["id"], "link": r.get("webViewLink")}, ensure_ascii=False))
    print(json.dumps({"folder": f"https://drive.google.com/drive/folders/{parent}"}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]),
                    help="folder containing Resume/ and 中文履歷/ (default: E:\\面試準備)")
    ap.add_argument("--login", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--auto", action="store_true", help="no-op when nothing changed since last sync")
    ap.add_argument("--archive-stale", action="store_true")
    ap.add_argument("--upload", nargs="+")
    ap.add_argument("--folder-path", default="自動客製")
    a = ap.parse_args()
    root = Path(a.root)

    if a.login:
        service(root, interactive=True)
        return
    if a.upload:
        upload_outputs(root, a.upload, a.folder_path)
        return
    if a.auto:
        if not os.environ.get("GDRIVE_TOKEN_JSON") and not (root / ".secrets" / "drive_token.json").exists():
            return  # not set up yet; stay quiet in the Stop hook
        if unchanged_since_last_sync(root):
            return
    sync(root, a.apply, a.archive_stale)
    if a.apply:
        mirror_to_repo(root)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
