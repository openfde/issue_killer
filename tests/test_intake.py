import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
TEMPLATES = ROOT / "profiles/openfde/intake-templates"


class IntakeTests(unittest.TestCase):
    def test_profile_declares_the_intake_channel(self):
        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))

        intake = profile["intake"]
        self.assertEqual(intake["root"], "data/intake")
        self.assertEqual(intake["templates"], "profiles/openfde/intake-templates")
        self.assertEqual(intake["size_budget_mb"], 20)
        self.assertEqual(intake["default_channel"], "server_adb")
        self.assertFalse(intake["allow_root"])

    def test_intake_templates_cover_required_subsystems(self):
        for name in (
            "README.md",
            "common.md",
            "bluetooth.md",
            "display.md",
            "audio.md",
            "camera.md",
            "boot-crash.md",
            "network.md",
        ):
            path = TEMPLATES / name
            self.assertTrue(path.is_file(), name)
            self.assertGreater(len(path.read_text(encoding="utf-8")), 50, name)

    def test_intake_templates_stay_read_only(self):
        for path in TEMPLATES.glob("*.md"):
            if path.name == "README.md":
                continue
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("logcat -c", content, path)
            self.assertNotIn("adb root", content, path)
            self.assertNotIn("adb install", content, path)
            self.assertNotIn("adb uninstall", content, path)

    def test_intake_skills_keep_human_confirmed_read_only_boundaries(self):
        for name in ("plan-evidence-collection", "run-evidence-collection", "validate-intake-package"):
            content = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("只读", content, name)
            self.assertIn("data/intake/", content, name)

        run = (ROOT / "skills/run-evidence-collection/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("不得自动挑选", run)
        self.assertIn("禁止 root", run)
        self.assertIn("禁止清日志缓冲", run)

    def test_intake_documentation_exists_and_links_from_the_index(self):
        doc = ROOT / "docs/architecture/intake.md"
        self.assertTrue(doc.is_file())
        index = (ROOT / "docs/README.md").read_text(encoding="utf-8")
        self.assertIn("architecture/intake.md", index)


if __name__ == "__main__":
    unittest.main()
