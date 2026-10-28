import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation" / "create_issue.py"


class CreateIssueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.slug = "2026-10-28-test"
        self.intake = self.workspace / "data" / "intake" / self.slug
        self.intake.mkdir(parents=True, exist_ok=True)
        (self.intake / "title.txt").write_text("状态栏下拉异常（CP2A.260605.016）\n", encoding="utf-8")
        (self.intake / "issue-draft.md").write_text(
            "## 现象\n\n下拉状态栏出现异常。\n\n## 附件清单\n\n- bugreport.zip\n- screen.png\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--workspace", str(self.workspace), "--intake", self.slug, *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_dry_run_builds_marker_and_evidence_link(self):
        result = self._run("--dry-run", "--evidence-url", "https://example.com/evidence.zip")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["title"], "状态栏下拉异常（CP2A.260605.016）")
        self.assertEqual(payload["slug"], self.slug)
        self.assertTrue(payload["would_create"])
        self.assertFalse(payload["attachments_uploaded"])
        self.assertEqual(len(payload["body_sha256"]), 64)
        self.assertIn("openfde-ai:intake slug=", payload["body_preview"])
        self.assertIn("## 取证包", payload["body_preview"])
        self.assertIn("https://example.com/evidence.zip", payload["body_preview"])
        self.assertFalse((self.intake / "issue.json").exists())

    def test_missing_title_is_rejected(self):
        (self.intake / "title.txt").unlink()
        (self.intake / "issue-draft.md").write_text("## 现象\n\n没有标题。\n", encoding="utf-8")
        result = self._run("--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("title not found", result.stderr)

    def test_existing_record_is_idempotent(self):
        record = {
            "schema_version": 1,
            "slug": self.slug,
            "repo": "openfde/openfde",
            "number": 493,
            "url": "https://github.com/openfde/openfde/issues/493",
        }
        (self.intake / "issue.json").write_text(json.dumps(record), encoding="utf-8")
        result = self._run("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["created"])
        self.assertTrue(payload["existing"])
        self.assertEqual(payload["number"], 493)

    def test_confirm_is_required_for_creation(self):
        result = self._run("--title", "x")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--confirm", result.stderr)


if __name__ == "__main__":
    unittest.main()
