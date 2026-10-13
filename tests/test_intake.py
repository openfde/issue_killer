import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class IntakeTests(unittest.TestCase):
    def test_profile_declares_the_intake_channel(self):
        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))

        intake = profile["intake"]
        self.assertEqual(intake["root"], "data/intake")
        self.assertEqual(intake["size_budget_mb"], 24)
        self.assertEqual(intake["default_channel"], "server_adb")
        self.assertFalse(intake["allow_root"])

    def test_intake_skill_is_interactive_and_read_only(self):
        content = (ROOT / "skills/collect-device-evidence/SKILL.md").read_text(encoding="utf-8")

        for value in ("bugreport", "screencap", "screenrecord", "data/intake/", "issue-draft", "不得自动挑选", "禁止 root", "禁止 `logcat -c`"):
            self.assertIn(value, content, value)

    def test_removed_planning_skills_and_templates_are_gone(self):
        for name in ("plan-evidence-collection", "run-evidence-collection", "validate-intake-package"):
            self.assertFalse((ROOT / "skills" / name).exists(), name)
        self.assertFalse((ROOT / "profiles/openfde/intake-templates").exists())

    def test_intake_documentation_exists_and_links_from_the_index(self):
        doc = ROOT / "docs/architecture/intake.md"
        self.assertTrue(doc.is_file())
        index = (ROOT / "docs/README.md").read_text(encoding="utf-8")
        self.assertIn("architecture/intake.md", index)


if __name__ == "__main__":
    unittest.main()
