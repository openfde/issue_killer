import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class AnalysisOptionsTests(unittest.TestCase):
    def test_skill_requires_a_technical_cause_chain_and_fix_options(self):
        content = (ROOT / "skills/draft-analysis-options/SKILL.md").read_text(encoding="utf-8")

        for value in (
            "问题原因链",
            "直接原因",
            "根本原因",
            "放大因素",
            "容错",
            "未证实",
            "修复选项 A/B/C",
            "改动点",
            "验证方法",
            "套话",
            "openfde-ai:analysis-options",
            "analysis_options_drafted",
        ):
            self.assertIn(value, content, value)

    def test_workflow_requires_developer_choice_before_fixing(self):
        workflow = (ROOT / "skills/run-issue-workflow/SKILL.md").read_text(encoding="utf-8")

        for value in (
            "draft-analysis-options",
            "analysis-options",
            "不得自行选择修复路线",
            "awaiting_direction",
        ):
            self.assertIn(value, workflow, value)

    def test_publication_allows_analysis_options_comment(self):
        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["publication"]["analysis_options_comment"], "auto")

        publish = (ROOT / "skills/publish-policy-comment/SKILL.md").read_text(encoding="utf-8")
        for value in ("analysis_options_comment", "analysis-options", "awaiting_direction"):
            self.assertIn(value, publish, value)

    def test_resume_stops_at_the_next_key_node(self):
        workflow = (ROOT / "skills/run-issue-workflow/SKILL.md").read_text(encoding="utf-8")

        for value in (
            "硬性停止点",
            "下一个关键节点",
            "必须结束本轮",
            "不得在同一轮调用",
            "根因重点解析",
            "根因重点解析与置信度分流",
            "判定清单",
            "不得因用户说“继续”而跳过",
            "不得只问",
        ):
            self.assertIn(value, workflow, value)

    def test_skill_updates_require_a_new_pi_session(self):
        for name in ("AGENTS.md", "docs/guides/pi-usage.md"):
            content = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("pi -c", content, name)
            self.assertIn("新开会话", content, name)

    def test_analysis_and_solution_artifacts_include_the_new_requirements(self):
        trace = (ROOT / "skills/trace-evidence-to-source/SKILL.md").read_text(encoding="utf-8")
        for value in (
            "触发条件与前置状态",
            "直接原因",
            "根本原因",
            "容错路径失效原因",
            "未证实环节",
            "已排除项",
        ):
            self.assertIn(value, trace, value)

        propose = (ROOT / "skills/propose-fix/SKILL.md").read_text(encoding="utf-8")
        for value in ("A/B/C", "改动点", "验证方法与判据", "工作量", "推荐"):
            self.assertIn(value, propose, value)


if __name__ == "__main__":
    unittest.main()
