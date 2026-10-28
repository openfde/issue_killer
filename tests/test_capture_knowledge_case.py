import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "capture_knowledge_case.py"


class CaptureKnowledgeCaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.issue = self.workspace / ".fde-ai" / "issues" / "493"
        for name in ("input", "evidence", "analysis", "patch", "archive"):
            (self.issue / name).mkdir(parents=True, exist_ok=True)

        self._write(
            "state.json",
            {
                "state": "archived",
                "revision": 2,
                "fix_confidence": {"score": 82},
                "profile_sha256": "profile",
            },
        )
        self._write(
            "input/issue.json",
            {
                "number": 493,
                "title": "状态栏下拉仍显示系统原生控制中心",
                "html_url": "https://github.com/openfde/openfde/issues/493",
                "labels": [{"name": "bug"}, {"name": "systemui"}],
                "body": "设备：fde_arm64；版本：CP2A.260605.016。",
            },
        )
        self._write(
            "analysis/components.json",
            {
                "components": [
                    {
                        "project": "frameworks_base",
                        "local_path": "frameworks/base",
                        "confidence": "high",
                        "source": "human",
                        "signals": [{"kind": "log-tag", "value": "SHADE_EXPAND"}],
                    }
                ]
            },
        )
        self._write(
            "evidence/evidence.json",
            {"signals": [{"kind": "window", "value": "NotificationShade"}]},
        )
        self._write(
            "archive/case.json",
            {
                "root_cause": "原生 NotificationShade 仍可展开",
                "fix": {"summary": "禁用原生 shade 展开", "pr": 110},
                "verification": {"status": "confirmed_fixed", "verified_by": "developer", "verified_at": "2026-10-28T00:00:00Z"},
            },
        )
        (self.issue / "patch" / "0001-native-shade.patch").write_text("diff --git a/a b/a\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def _write(self, relative, payload):
        path = self.issue / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--workspace", str(self.workspace), *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_capture_is_structured_idempotent_and_indexed(self):
        result = self._run("--issue", "493")
        self.assertEqual(result.returncode, 0, result.stderr)

        case_path = self.workspace / "data/knowledge/cases/493/case.json"
        self.assertTrue(case_path.is_file())
        case = json.loads(case_path.read_text(encoding="utf-8"))
        self.assertEqual(case["case_id"], "issue-493")
        self.assertEqual(case["issue"], 493)
        self.assertEqual(case["revision"], 2)
        self.assertEqual(case["knowledge_status"], "verified")
        self.assertTrue(case["verification"]["verified"])
        self.assertEqual(case["components"][0]["project"], "frameworks_base")
        self.assertEqual(case["confidence"], 82)
        self.assertTrue(any(item["value"] == "NotificationShade" for item in case["signals"]))
        self.assertIn("patch", case["fix"])
        self.assertIn("patch_sha256", case["fix"])
        self.assertIn("archive_case", case["provenance"]["hashes"])

        markdown = (self.workspace / "data/knowledge/cases/493/case.md").read_text(encoding="utf-8")
        self.assertIn("Issue #493", markdown)
        self.assertIn("NotificationShade", markdown)

        index = json.loads((self.workspace / "data/knowledge/index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(index["cases"]), 1)
        self.assertEqual(index["cases"][0]["issue"], 493)
        self.assertTrue(index["cases"][0]["verified"])

        # Idempotent: a second capture must not duplicate the index entry.
        second = self._run("--issue", "493")
        self.assertEqual(second.returncode, 0, second.stderr)
        index = json.loads((self.workspace / "data/knowledge/index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(index["cases"]), 1)

    def test_capture_requires_archive_case(self):
        (self.issue / "archive" / "case.json").unlink()
        result = self._run("--issue", "493")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive case", result.stderr)

    def test_unverified_case_stays_draft(self):
        state = json.loads((self.issue / "state.json").read_text(encoding="utf-8"))
        state["state"] = "awaiting_verification"
        (self.issue / "state.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        archive = json.loads((self.issue / "archive" / "case.json").read_text(encoding="utf-8"))
        archive["verification"] = {"status": "pending"}
        (self.issue / "archive" / "case.json").write_text(json.dumps(archive, ensure_ascii=False), encoding="utf-8")

        result = self._run("--issue", "493")
        self.assertEqual(result.returncode, 0, result.stderr)
        case = json.loads((self.workspace / "data/knowledge/cases/493/case.json").read_text(encoding="utf-8"))
        self.assertEqual(case["knowledge_status"], "draft")
        self.assertFalse(case["verification"]["verified"])

    def test_rebuild_index_only_mode(self):
        first = self._run("--issue", "493")
        self.assertEqual(first.returncode, 0, first.stderr)
        result = self._run("--rebuild-index")
        self.assertEqual(result.returncode, 0, result.stderr)
        index = json.loads((self.workspace / "data/knowledge/index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["schema_version"], 1)
        self.assertEqual(len(index["cases"]), 1)


if __name__ == "__main__":
    unittest.main()
