import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ReproductionPlanTests(unittest.TestCase):
    def test_skill_covers_reproduction_verification_and_experiments(self):
        content = (ROOT / "skills/design-reproduction-plan/SKILL.md").read_text(encoding="utf-8")

        for value in ("触发方案", "稳定复现判定", "修复后验证判定", "根因确认实验", "not_run"):
            self.assertIn(value, content, value)

    def test_workflow_offers_the_reproduction_plan_at_the_root_cause_node(self):
        workflow = (ROOT / "skills/run-issue-workflow/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("design-reproduction-plan", workflow)
        self.assertIn("复现与验证方案", workflow)

        usage = (ROOT / "docs/guides/pi-usage.md").read_text(encoding="utf-8")
        self.assertIn("design-reproduction-plan", usage)

    def test_plan_can_be_published_as_a_follow_up_issue_reply(self):
        content = (ROOT / "skills/design-reproduction-plan/SKILL.md").read_text(encoding="utf-8")

        for value in ("comment/reproduction-plan.md", "openfde-ai:reproduction-plan", "publish-policy-comment"):
            self.assertIn(value, content, value)


if __name__ == "__main__":
    unittest.main()
