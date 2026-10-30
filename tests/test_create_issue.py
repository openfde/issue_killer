import importlib.util
import json
import subprocess
import sys
import tempfile
import types
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
        (self.intake / "bugreport.zip").write_bytes(b"PK\x03\x04test")
        (self.intake / "screen.png").write_bytes(b"\x89PNG\r\n\x1a\ntest")
        (self.intake / "summary.md").write_text("summary", encoding="utf-8")

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
        self.assertEqual(len(payload["attachments"]), 2)
        names = {item["name"] for item in payload["attachments"]}
        self.assertIn("2026-10-28-test-bugreport.zip", names)
        self.assertIn("2026-10-28-test-screen.png", names)
        self.assertTrue(all("releases/download/intake-evidence/" in item["url"] for item in payload["attachments"]))
        self.assertIn("2026-10-28-test-bugreport.zip", payload["body_preview"])
        self.assertFalse((self.intake / "issue.json").exists())

    def test_no_upload_attachments_leaves_body_without_release_links(self):
        result = self._run("--dry-run", "--no-upload-attachments")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["attachments"], [])
        self.assertNotIn("## 取证包", payload["body_preview"])

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

    def test_auth_check_uses_repo_api_not_auth_status(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('["api", f"repos/{repo}", "--jq", ".full_name"]', source)
        self.assertNotIn('["auth", "status"]', source)

    def test_publish_skill_wraps_confirm_and_attachments(self):
        skill = (ROOT / "skills" / "publish-intake-issue" / "SKILL.md").read_text(encoding="utf-8")
        for value in ("/skill:publish-intake-issue", "create_issue.py", "--dry-run", "--confirm", "Release asset", "附件"):
            self.assertIn(value, skill, value)
        self.assertIn("不自动关闭", skill)

    def test_upload_creates_release_when_missing(self):
        spec = importlib.util.spec_from_file_location("create_issue_module", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        calls = []

        def fake_run(args, timeout=120):
            calls.append(args)
            if args[:2] == ["release", "view"]:
                return types.SimpleNamespace(returncode=1, stdout="", stderr="not found")
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

        module.run_gh = fake_run
        planned = [{"path": str(self.intake / "bugreport.zip"), "name": "slug-bugreport.zip", "url": "https://example.com/x"}]
        module.upload_attachments(planned, "openfde/openfde", "intake-evidence")
        self.assertEqual(calls[0][:2], ["release", "view"])
        self.assertEqual(calls[1][:2], ["release", "create"])
        self.assertEqual(calls[2][:2], ["release", "upload"])
        self.assertIn("--clobber", calls[2])


if __name__ == "__main__":
    unittest.main()
