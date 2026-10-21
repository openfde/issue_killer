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

        for value in ("bugreport", "screencap", "screenrecord", "data/intake/", "issue-draft", "不写 SHA-256", "系统版本号", "scp -r", "开始采集", "复现完成", "不得执行", "不得自动挑选", "禁止 root", "禁止 `logcat -c`", "issue-draft.md 全文"):
            self.assertIn(value, content, value)

    def test_removed_planning_skills_and_templates_are_gone(self):
        for name in ("plan-evidence-collection", "run-evidence-collection", "validate-intake-package"):
            self.assertFalse((ROOT / "skills" / name).exists(), name)
        self.assertFalse((ROOT / "profiles/openfde/intake-templates").exists())

    def test_intake_supports_post_hoc_evidence_and_manual_issue_enrichment(self):
        skill = (ROOT / "skills/collect-device-evidence/SKILL.md").read_text(encoding="utf-8")
        for value in ("事后证据", "推测", "时间线", "下次偶现采集建议"):
            self.assertIn(value, skill, value)

        enrich = (ROOT / "skills/enrich-issue-intake/SKILL.md").read_text(encoding="utf-8")
        for value in ("openfde-ai:intake", "时间线", "复现步骤（推测，未确认）", "原始描述", "gh issue edit", "初步分析（未验证）", "视觉", "无日志证据"):
            self.assertIn(value, enrich, value)

        self.assertFalse((ROOT / "deploy/intake-watch.sh").exists())
        reply_poll = (ROOT / "deploy/reply-poll.sh").read_text(encoding="utf-8")
        self.assertNotIn("intake-watch", reply_poll)

        helper = (ROOT / "deploy/enrich-issue.sh").read_text(encoding="utf-8")
        self.assertIn("enrich-issue-intake", helper)

    def test_intake_documentation_exists_and_links_from_the_index(self):
        doc = ROOT / "docs/architecture/intake.md"
        self.assertTrue(doc.is_file())
        index = (ROOT / "docs/README.md").read_text(encoding="utf-8")
        self.assertIn("architecture/intake.md", index)


if __name__ == "__main__":
    unittest.main()
