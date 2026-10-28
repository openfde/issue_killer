#!/usr/bin/env python3
"""Create a GitHub issue from an intake draft after explicit confirmation.

GitHub's issue API can create the title/body but cannot upload arbitrary
attachments in the same request. This script therefore creates the issue body
only; evidence files still need a manual upload or an external evidence URL
passed with --evidence-url.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCHEMA_VERSION = 1
DEFAULT_REPO = "openfde/openfde"
INTAKE_ROOT = "data/intake"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(path))


def default_repo(workspace: Path) -> str:
    profile = read_json(workspace / "profiles" / "openfde" / "profile.json")
    if isinstance(profile, dict):
        repo = (profile.get("github") or {}).get("repository")
        if isinstance(repo, str) and repo.strip():
            return repo.strip()
    return DEFAULT_REPO


def intake_dir(workspace: Path, slug: str) -> Path:
    root = (workspace / INTAKE_ROOT).resolve()
    target = (root / slug).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise SystemExit(f"intake slug escapes {INTAKE_ROOT}: {slug}")
    if not target.is_dir():
        raise SystemExit(f"intake directory not found: {target}")
    return target


def strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.S)


def parse_title(draft_text: str, title_file: Path) -> str:
    if title_file.is_file():
        value = title_file.read_text(encoding="utf-8").strip()
        value = re.sub(r"^(?:标题|Title)\s*[:：]\s*", "", value, flags=re.I).strip()
        if value:
            return value

    text = strip_frontmatter(draft_text)
    front = re.match(r"\A---\s*\n(.*?)\n---\s*\n", draft_text, flags=re.S)
    if front:
        match = re.search(r"^title\s*:\s*(.+)$", front.group(1), flags=re.M | re.I)
        if match:
            return match.group(1).strip().strip("'\"")
    for line in text.splitlines():
        value = line.strip()
        if not value:
            continue
        match = re.match(r"^标题\s*[:：]\s*(.+)$", value)
        if match:
            return match.group(1).strip()
        if value.startswith("# "):
            return value[2:].strip()
        break
    raise SystemExit("title not found: write data/intake/<slug>/title.txt or pass --title")


def extract_body(draft_text: str, title: str) -> str:
    text = strip_frontmatter(draft_text)
    fenced = re.findall(r"```(?:markdown|md)?\s*\n(.*?)```", text, flags=re.S | re.I)
    if fenced:
        selected = next((block for block in fenced if "## 现象" in block), fenced[0])
        text = selected
    lines = text.strip().splitlines()
    if lines and lines[0].strip().lstrip("# ").strip() == title.strip():
        lines = lines[1:]
    return "\n".join(lines).strip()


def build_body(draft_text: str, title: str, slug: str, evidence_url: Optional[str]) -> str:
    body = extract_body(draft_text, title)
    marker = f"<!-- openfde-ai:intake slug={slug} -->"
    if marker not in body:
        body = body.rstrip() + "\n\n" + marker
    if evidence_url:
        if evidence_url.rstrip() not in body:
            body = body.rstrip() + "\n\n## 取证包\n" + evidence_url.strip()
    return body.rstrip() + "\n"


def run_gh(args: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.setdefault("GH_PROMPT_DISABLED", "1")
    env.setdefault("GH_NO_UPDATE_NOTIFIER", "1")
    return subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", timeout=timeout, env=env)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=".", help="repository/workspace root")
    parser.add_argument("--intake", required=True, help="intake directory name under data/intake")
    parser.add_argument("--repo", help="owner/repo; defaults to profile github.repository")
    parser.add_argument("--title", help="title override; otherwise read title.txt / issue-draft.md")
    parser.add_argument("--evidence-url", help="optional URL to append under 取证包")
    parser.add_argument("--label", action="append", default=[], help="issue label (repeatable)")
    parser.add_argument("--force", action="store_true", help="ignore an existing issue.json record")
    parser.add_argument("--dry-run", action="store_true", help="build and print the issue without creating it")
    parser.add_argument("--confirm", action="store_true", help="required to actually create the issue")
    args = parser.parse_args()

    if not args.dry_run and not args.confirm:
        parser.error("refusing to create without --confirm (use --dry-run to preview)")

    workspace = Path(args.workspace).resolve()
    directory = intake_dir(workspace, args.intake)
    draft_path = directory / "issue-draft.md"
    if not draft_path.is_file():
        raise SystemExit(f"issue draft not found: {draft_path}")

    draft_text = draft_path.read_text(encoding="utf-8")
    title = (args.title or "").strip() or parse_title(draft_text, directory / "title.txt")
    if not title:
        raise SystemExit("empty issue title")
    body = build_body(draft_text, title, args.intake, args.evidence_url)
    body_hash = sha256_text(body)
    repo = (args.repo or default_repo(workspace)).strip()
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "slug": args.intake,
        "repo": repo,
        "title": title,
        "body_sha256": body_hash,
        "marker": f"openfde-ai:intake slug={args.intake}",
        "attachments_uploaded": False,
        "evidence_url": args.evidence_url,
    }

    record_path = directory / "issue.json"
    existing = read_json(record_path)
    if isinstance(existing, dict) and existing.get("url") and not args.force:
        result.update({"created": False, "existing": True, "url": existing.get("url"), "number": existing.get("number")})
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0

    if not args.dry_run:
        auth = run_gh(["auth", "status"], timeout=30)
        if auth.returncode != 0:
            sys.stderr.write(auth.stderr or "gh auth status failed\n")
            return 1

        fd, temp_name = tempfile.mkstemp(prefix="intake-issue-", suffix=".md")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(body)
            cmd = ["issue", "create", "--repo", repo, "--title", title, "--body-file", temp_name]
            for label in args.label:
                cmd.extend(["--label", label])
            created = run_gh(cmd, timeout=120)
        finally:
            try:
                os.unlink(temp_name)
            except OSError:
                pass

        if created.returncode != 0:
            sys.stderr.write(created.stderr or created.stdout or "gh issue create failed\n")
            return 1
        output = (created.stdout or "").strip().splitlines()
        url = output[-1].strip() if output else ""
        match = re.search(r"/issues/(\d+)", url)
        number = int(match.group(1)) if match else None
        record = {
            "schema_version": SCHEMA_VERSION,
            "slug": args.intake,
            "repo": repo,
            "number": number,
            "url": url,
            "title": title,
            "body_sha256": body_hash,
            "evidence_url": args.evidence_url,
            "created_at": utc_now(),
            "source": str(directory.relative_to(workspace)).replace(os.sep, "/"),
        }
        write_json_atomic(record_path, record)
        result.update({"created": True, "url": url, "number": number})
        if not args.evidence_url:
            sys.stderr.write(
                "warning: GitHub issue attachments are not uploaded automatically; "
                f"upload {directory} manually or rerun with --evidence-url.\n"
            )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0

    result.update({"created": False, "dry_run": True, "would_create": True, "body_preview": body[:1200]})
    if not args.evidence_url:
        sys.stderr.write("warning: attachments require a manual upload or --evidence-url.\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
