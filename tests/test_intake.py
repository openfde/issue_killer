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

        for value in ("bugreport", "screencap", "screenrecord", "data/intake/", "issue-draft", "不写 SHA-256", "系统版本号", "scp huyang@", "复现完成", "不得执行", "不得自动挑选", "禁止 root", "禁止 `logcat -c`"):
            self.assertIn(value, content, value)

    def test_removed_planning_skills_and_templates_are_gone(self):
        for name in ("plan-evidence-collection", "run-evidence-collection", "validate-intake-package"):
            self.assertFalse((ROOT / "skills" / name).exists(), name)
        self.assertFalse((ROOT / "profiles/openfde/intake-templates").exists())

    def test_intake_supports_post_hoc_evidence_and_issue_enrichment(self):
        skill = (ROOT / "skills/collect-device-evidence/SKILL.md").read_text(encoding="utf-8")
        for value in ("事后证据", "推测", "时间线", "下次偶现采集建议"):
            self.assertIn(value, skill, value)

        enrich = (ROOT / "skills/enrich-issue-intake/SKILL.md").read_text(encoding="utf-8")
        for value in ("openfde-ai:intake", "时间线（事后补抓）", "复现步骤（推测，未确认）", "原始描述", "gh issue edit"):
            self.assertIn(value, enrich, value)

        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["publication"]["issue_enrichment"], "auto")

        watcher = (ROOT / "deploy/intake-watch.sh").read_text(encoding="utf-8")
        for value in ("enrich-issue-intake", "watch-state.json", "user-attachments"):
            self.assertIn(value, watcher, value)

    def test_intake_documentation_exists_and_links_from_the_index(self):
        doc = ROOT / "docs/architecture/intake.md"
        self.assertTrue(doc.is_file())
        index = (ROOT / "docs/README.md").read_text(encoding="utf-8")
        self.assertIn("architecture/intake.md", index)


if __name__ == "__main__":
    unittest.main()
