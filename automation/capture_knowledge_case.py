#!/usr/bin/env python3
"""Capture one archived issue as a draft knowledge case.

The script is deliberately read-only with respect to issue artifacts. It reads
`.fde-ai/issues/<issue>/` and writes only under the knowledge root
(`data/knowledge/` by default):

  cases/<issue>/case.json
  cases/<issue>/case.md
  index.json

It never promotes a case to the wiki, never calls GitHub, and never edits source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SCHEMA_VERSION = 1
DEFAULT_DATA_ROOT = "data/knowledge"
MAX_TEXT = 12000
MAX_COMPONENTS = 30
MAX_SIGNALS = 80

SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)((?:token|password|secret|api[_-]?key)\s*[:=]\s*)[^\s,;]+"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_text(value: Any, limit: int = MAX_TEXT) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        try:
            value = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            value = str(value)
    for pattern in SECRET_PATTERNS:
        if pattern.groups:
            value = pattern.sub(lambda match: match.group(1) + "***REDACTED***", value)
        else:
            value = pattern.sub("***REDACTED***", value)
    value = value.strip()
    if len(value) > limit:
        value = value[:limit] + "\n... [truncated]"
    return value


def first(mapping: Any, keys: Iterable[str], default: Any = None) -> Any:
    if not isinstance(mapping, dict):
        return default
    for key in keys:
        if key in mapping and mapping[key] not in (None, "", [], {}):
            return mapping[key]
    return default


def relative(workspace: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(workspace.resolve()))
    except ValueError:
        return str(path)


def normalize_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return list(value.values())
    return [value]


def collect_components(issue_dir: Path) -> List[Dict[str, Any]]:
    candidates = []
    analysis = read_json(issue_dir / "analysis" / "components.json")
    if isinstance(analysis, dict):
        listed = first(analysis, ("components", "items", "resolved", "matches"), None)
        if isinstance(listed, dict):
            # Tolerate a mapping of project -> component details.
            for key, value in listed.items():
                if isinstance(value, dict):
                    item = dict(value)
                    item.setdefault("project", key)
                    candidates.append(item)
                elif isinstance(value, str):
                    candidates.append({"project": key, "local_path": value})
        elif listed is not None:
            candidates.extend(normalize_list(listed))
        else:
            # Tolerate a top-level mapping of project -> component details.
            for key, value in analysis.items():
                if isinstance(value, dict):
                    item = dict(value)
                    item.setdefault("project", key)
                    candidates.append(item)
                elif isinstance(value, str):
                    candidates.append({"project": key, "local_path": value})
    elif isinstance(analysis, list):
        candidates.extend(analysis)

    archive = read_json(issue_dir / "archive" / "case.json")
    if isinstance(archive, dict):
        candidates.extend(normalize_list(first(archive, ("components", "component_map"), [])))

    components: List[Dict[str, Any]] = []
    seen = set()
    for item in candidates:
        if isinstance(item, str):
            item = {"project": item}
        if not isinstance(item, dict):
            continue
        project = first(item, ("project", "repo", "repository", "name")) or ""
        local_path = first(item, ("local_path", "path", "localPath")) or ""
        confidence = first(item, ("confidence", "certainty")) or ""
        source = first(item, ("source", "matched_by", "basis")) or ""
        key = (str(project), str(local_path))
        if key in seen:
            continue
        seen.add(key)
        record: Dict[str, Any] = {
            "project": safe_text(project, 300),
            "local_path": safe_text(local_path, 300),
            "confidence": safe_text(confidence, 40),
            "source": safe_text(source, 80),
        }
        signals = item.get("signals")
        if signals:
            record["signals"] = normalize_list(signals)[:10]
        components.append(record)
        if len(components) >= MAX_COMPONENTS:
            break
    return components


def collect_signals(issue_dir: Path, components: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    raw = []
    for name in ("evidence/evidence.json", "analysis/evidence.json", "input/evidence.json"):
        data = read_json(issue_dir / name)
        if isinstance(data, dict):
            raw.extend(normalize_list(first(data, ("signals", "items", "evidence"), [])))
        elif isinstance(data, list):
            raw.extend(data)

    for component in components:
        raw.extend(normalize_list(component.get("signals")))

    signals: List[Dict[str, str]] = []
    seen = set()
    for item in raw:
        if isinstance(item, str):
            kind, value = "keyword", item
        elif isinstance(item, dict):
            kind = first(item, ("kind", "type", "signal")) or "keyword"
            value = first(item, ("value", "text", "name", "pattern")) or ""
        else:
            continue
        kind_text = safe_text(kind, 60)
        value_text = safe_text(value, 500)
        if not value_text:
            continue
        key = (kind_text, value_text)
        if key in seen:
            continue
        seen.add(key)
        signals.append({"kind": kind_text, "value": value_text})
        if len(signals) >= MAX_SIGNALS:
            break
    return signals


def collect_issue_meta(issue_dir: Path, state: Dict[str, Any], archive: Dict[str, Any]) -> Dict[str, Any]:
    issue = read_json(issue_dir / "input" / "issue.json")
    if not isinstance(issue, dict):
        issue = {}
    body = first(issue, ("body", "description"), "")
    if not body:
        markdown = issue_dir / "input" / "issue.md"
        try:
            body = markdown.read_text(encoding="utf-8")
        except OSError:
            body = ""
    labels = []
    for label in normalize_list(issue.get("labels")):
        if isinstance(label, dict):
            labels.append(str(label.get("name", "")))
        else:
            labels.append(str(label))
    tags = [item for item in labels if item]
    for key in ("tags", "labels"):
        tags.extend(str(item) for item in normalize_list(archive.get(key)) if item)
    return {
        "title": safe_text(first(issue, ("title",), first(archive, ("title",), first(state, ("title",), ""))), 500),
        "url": safe_text(first(issue, ("html_url", "url"), first(archive, ("url", "issue_url"), "")), 500),
        "body": safe_text(body, 4000),
        "issue_number": first(issue, ("number", "issue"), None),
        "tags": sorted(set(tags)),
    }


def collect_device(issue_dir: Path, state: Dict[str, Any], archive: Dict[str, Any], body: str) -> Dict[str, Any]:
    device = first(archive, ("device",), first(state, ("device",), {}))
    result: Dict[str, Any] = {}
    if isinstance(device, dict):
        result = {
            "model": safe_text(first(device, ("model", "device", "product")), 120),
            "build": safe_text(first(device, ("build", "build_id", "display_id")), 120),
            "android": safe_text(first(device, ("android", "version", "release")), 80),
        }
    build_match = re.search(r"\b(CP2A\.[0-9A-Za-z.\-_]+)", body)
    if build_match and not result.get("build"):
        result["build"] = build_match.group(1)
    model_match = re.search(r"\b(fde_[A-Za-z0-9_]+)", body)
    if model_match and not result.get("model"):
        result["model"] = model_match.group(1)
    return {key: value for key, value in result.items() if value}


def collect_fix(issue_dir: Path, archive: Dict[str, Any], workspace: Path) -> Dict[str, Any]:
    raw = first(archive, ("fix", "solution", "patch", "pull_request", "pr"), {})
    fix: Dict[str, Any] = {}
    if isinstance(raw, str):
        fix["summary"] = safe_text(raw, 2000)
    elif isinstance(raw, dict):
        for key in ("summary", "description", "pr", "pull_request", "commit", "branch", "status"):
            value = raw.get(key)
            if value not in (None, "", [], {}):
                fix[key] = safe_text(value, 1000)
    for key in ("pr", "pull_request", "commit", "branch"):
        value = first(archive, (key,))
        if value not in (None, "", [], {}):
            fix.setdefault(key, safe_text(value, 1000))

    patches = sorted((issue_dir / "patch").glob("*.patch")) if (issue_dir / "patch").is_dir() else []
    if patches:
        fix["patch"] = relative(workspace, patches[0])
        fix["patch_sha256"] = sha256_file(patches[0])
    return fix


def collect_verification(archive: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    raw = first(archive, ("verification", "user_report", "result"), {})
    verification: Dict[str, Any] = {"status": "", "verified": False, "verified_by": "", "verified_at": "", "evidence": []}
    if isinstance(raw, str):
        verification["status"] = safe_text(raw, 500)
    elif isinstance(raw, dict):
        verification["status"] = safe_text(first(raw, ("status", "result", "outcome")), 200)
        verification["verified_by"] = safe_text(first(raw, ("verified_by", "reviewer", "user")), 120)
        verification["verified_at"] = safe_text(first(raw, ("verified_at", "time", "updated_at")), 120)
        verification["evidence"] = [safe_text(item, 500) for item in normalize_list(first(raw, ("evidence", "attachments"), [])) if item]

    state_value = str(state.get("state", "")).lower()
    status_value = verification["status"].lower()
    verification["verified"] = bool(
        state_value == "confirmed_fixed"
        or "verified" in status_value
        or "confirmed" in status_value
        or "验证通过" in verification["status"]
    )
    if not verification["status"]:
        verification["status"] = "confirmed_fixed" if verification["verified"] else state.get("state", "unknown")
    return verification


def capture(workspace: Path, issue: int, data_root: Path) -> Dict[str, Any]:
    issue_dir = workspace / ".fde-ai" / "issues" / str(issue)
    state = read_json(issue_dir / "state.json")
    if not isinstance(state, dict):
        raise SystemExit(f"missing or invalid state.json: {issue_dir / 'state.json'}")
    archive_path = issue_dir / "archive" / "case.json"
    archive = read_json(archive_path)
    if not isinstance(archive, dict):
        raise SystemExit(f"missing or invalid archive case: {archive_path}")

    meta = collect_issue_meta(issue_dir, state, archive)
    components = collect_components(issue_dir)
    signals = collect_signals(issue_dir, components)
    device = collect_device(issue_dir, state, archive, meta["body"])
    verification = collect_verification(archive, state)
    fix = collect_fix(issue_dir, archive, workspace)
    revision = int(first(state, ("revision",), first(archive, ("revision",), 1)) or 1)
    status = safe_text(first(state, ("state",), first(archive, ("state",), "unknown")), 80)
    knowledge_status = "verified" if verification.get("verified") else "draft"
    confidence = first(state, ("fix_confidence", "confidence"), None)
    if isinstance(confidence, dict):
        confidence = first(confidence, ("score", "value", "confidence"), None)

    root_cause = first(archive, ("root_cause", "cause"), "")
    if not root_cause and isinstance(archive.get("analysis"), dict):
        root_cause = first(archive["analysis"], ("root_cause", "cause"), "")
    symptom = first(archive, ("symptom", "summary"), "")
    if not symptom:
        symptom = meta["body"]

    provenance: Dict[str, Any] = {"issue_dir": relative(workspace, issue_dir), "hashes": {}}
    for label, path in (
        ("state", issue_dir / "state.json"),
        ("archive_case", archive_path),
        ("components", issue_dir / "analysis" / "components.json"),
        ("issue_snapshot", issue_dir / "input" / "issue.json"),
        ("evidence", issue_dir / "evidence" / "evidence.json"),
    ):
        if path.is_file():
            provenance[label] = relative(workspace, path)
            provenance["hashes"][label] = sha256_file(path)

    case = {
        "schema_version": SCHEMA_VERSION,
        "case_id": f"issue-{issue}",
        "issue": issue,
        "repo": safe_text(first(archive, ("repo", "repository"), "openfde/openfde"), 200),
        "title": meta["title"] or f"Issue {issue}",
        "url": meta["url"],
        "status": status,
        "revision": revision,
        "created_at": safe_text(first(state, ("created_at",), first(archive, ("created_at",))), 80),
        "updated_at": utc_now(),
        "device": device,
        "components": components,
        "signals": signals,
        "symptom": safe_text(symptom, MAX_TEXT),
        "root_cause": safe_text(root_cause, MAX_TEXT),
        "fix": fix,
        "verification": verification,
        "knowledge_status": knowledge_status,
        "confidence": confidence,
        "tags": meta["tags"],
        "provenance": provenance,
    }

    case_dir = data_root / "cases" / str(issue)
    case_dir.mkdir(parents=True, exist_ok=True)
    case_path = case_dir / "case.json"
    write_json_atomic(case_path, case)
    write_text_atomic(case_dir / "case.md", render_markdown(case))
    index_path = rebuild_index(data_root)
    return {"case": str(case_path), "markdown": str(case_dir / "case.md"), "index": str(index_path), "knowledge_status": knowledge_status}


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(str(tmp), str(path))


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))


def render_markdown(case: Dict[str, Any]) -> str:
    def lines(items: List[Dict[str, Any]], keys: List[str]) -> str:
        if not items:
            return "- （无）"
        output = []
        for item in items:
            values = [safe_text(item.get(key), 300) for key in keys]
            output.append("- " + " | ".join(value for value in values if value))
        return "\n".join(output)

    device = case.get("device") or {}
    device_text = ", ".join(f"{key}={value}" for key, value in device.items() if value) or "（未记录）"
    fix = case.get("fix") or {}
    fix_text = "\n".join(f"- {key}: {safe_text(value, 1000)}" for key, value in fix.items()) or "- （未记录）"
    verification = case.get("verification") or {}
    verification_text = "\n".join(f"- {key}: {safe_text(value, 1000)}" for key, value in verification.items()) or "- （未记录）"
    provenance = case.get("provenance") or {}
    provenance_text = "\n".join(f"- {key}: {safe_text(value, 500)}" for key, value in provenance.items()) or "- （未记录）"

    return f"""# Issue #{case['issue']} · {case['title']}

- 状态：`{case['status']}`
- revision：`{case['revision']}`
- 知识状态：`{case['knowledge_status']}`
- 设备/构建：{device_text}
- 标签：{', '.join(case.get('tags') or []) or '（无）'}
- 更新时间：{case['updated_at']}

## 现象

{case.get('symptom') or '（未记录）'}

## 组件

{lines(case.get('components') or [], ['project', 'local_path', 'confidence', 'source'])}

## 信号

{lines(case.get('signals') or [], ['kind', 'value'])}

## 根因

{case.get('root_cause') or '（未记录 / 未验证）'}

## 修复

{fix_text}

## 验证

{verification_text}

## 来源

{provenance_text}

> 本 case 由自动化脚本生成；`draft` 不代表已验证，晋升 Wiki 需要人工审核。
"""


def rebuild_index(data_root: Path) -> Path:
    cases_dir = data_root / "cases"
    items = []
    if cases_dir.is_dir():
        for case_path in sorted(cases_dir.glob("*/case.json")):
            case = read_json(case_path)
            if not isinstance(case, dict):
                continue
            items.append(
                {
                    "issue": case.get("issue"),
                    "title": case.get("title"),
                    "status": case.get("status"),
                    "knowledge_status": case.get("knowledge_status"),
                    "verified": bool((case.get("verification") or {}).get("verified")),
                    "revision": case.get("revision"),
                    "components": [
                        {
                            "project": component.get("project"),
                            "local_path": component.get("local_path"),
                            "confidence": component.get("confidence"),
                        }
                        for component in (case.get("components") or [])[:10]
                    ],
                    "signals": (case.get("signals") or [])[:20],
                    "tags": case.get("tags") or [],
                    "updated_at": case.get("updated_at"),
                    "path": str(case_path.relative_to(data_root)).replace(os.sep, "/"),
                }
            )
    items.sort(key=lambda item: (item.get("issue") or 0))
    index = {"schema_version": SCHEMA_VERSION, "generated_at": utc_now(), "cases": items}
    index_path = data_root / "index.json"
    write_json_atomic(index_path, index)
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=".", help="repository/workspace root")
    parser.add_argument("--issue", type=int, help="issue number to capture")
    parser.add_argument("--data-root", default=DEFAULT_DATA_ROOT, help="knowledge root, relative to workspace")
    parser.add_argument("--rebuild-index", action="store_true", help="only rebuild index.json from existing cases")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    data_root = (workspace / args.data_root).resolve()
    if args.rebuild_index and not args.issue:
        print(json.dumps({"index": str(rebuild_index(data_root))}, ensure_ascii=False))
        return 0
    if not args.issue:
        parser.error("--issue is required unless --rebuild-index is used")
    result = capture(workspace, args.issue, data_root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
