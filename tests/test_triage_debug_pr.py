import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class TriageDebugPrTests(unittest.TestCase):
    def test_profile_declares_triage_and_debug_pr_settings(self):
        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))

        triage = profile["triage"]
        self.assertEqual(triage["analysis_reply_min_confidence"], 50)
        self.assertEqual(triage["auto_pr_min_confidence"], 70)
        self.assertEqual(triage["max_deep_analysis_rounds"], 2)
        self.assertEqual(profile["replies"]["poll_seconds"], 300)

        debug = profile["debug_pull_request"]
        self.assertTrue(debug["enabled"])
        self.assertEqual(debug["branch_prefix"], "ai-debug/")
        self.assertTrue(debug["instrumentation_only"])
        self.assertFalse(debug["merge"])

        for key in ("reproduction_plan_comment", "debug_pr_comment"):
            self.assertEqual(profile["publication"][key], "auto")

    def test_propose_fix_produces_a_confidence_score(self):
        content = (ROOT / "skills/propose-fix/SKILL.md").read_text(encoding="utf-8")

        for value in (
            "fix_confidence",
            "root_cause",
            "unknowns",
            "90–100",
            "50–69",
            "不得无依据给高分",
        ):
            self.assertIn(value, content, value)

    def test_workflow_enforces_confidence_gate_and_loop_cap(self):
        workflow = (ROOT / "skills/run-issue-workflow/SKILL.md").read_text(encoding="utf-8")

        for value in (
            "auto_pr_min_confidence",
            "analysis_reply_min_confidence",
            "max_deep_analysis_rounds",
            "draft-debug-patch",
            "create-debug-pull-request",
            "phase",
            "direction_wait_since",
        ):
            self.assertIn(value, workflow, value)

    def test_analysis_options_lists_compact_investigation_options(self):
        content = (ROOT / "skills/draft-analysis-options/SKILL.md").read_text(encoding="utf-8")

        for value in ("修复置信度", "D. 复现与验证方案", "E. 调试 PR", "F. 深入分析", "只列选项，不展开"):
            self.assertIn(value, content, value)

    def test_debug_patch_is_instrumentation_only(self):
        content = (ROOT / "skills/draft-debug-patch/SKILL.md").read_text(encoding="utf-8")

        for value in (
            "只加日志",
            "不改变任何行为",
            "openfde<issue号>",
            "debug-0001",
            "not_run",
            "debug_patch_proposed",
        ):
            self.assertIn(value, content, value)

    def test_debug_pr_is_created_on_an_ai_debug_branch_and_not_merged(self):
        content = (ROOT / "skills/create-debug-pull-request/SKILL.md").read_text(encoding="utf-8")

        for value in (
            "ai-debug/",
            "只创建",
            "不得合入",
            "debug_pull_request_created",
            "openfde-ai:debug-pr",
            "adb logcat -s openfde",
        ):
            self.assertIn(value, content, value)

    def test_comment_and_publish_paths_handle_plan_and_debug_types(self):
        publish = (ROOT / "skills/publish-policy-comment/SKILL.md").read_text(encoding="utf-8")
        for value in ("reproduction-plan", "debug-pr", "awaiting_direction", "direction_wait_since"):
            self.assertIn(value, publish, value)

        sync = (ROOT / "skills/sync-github-replies/SKILL.md").read_text(encoding="utf-8")
        for value in ("reproduction_plan", "debug_pr", "deep_analysis", "调试日志"):
            self.assertIn(value, sync, value)


if __name__ == "__main__":
    unittest.main()
