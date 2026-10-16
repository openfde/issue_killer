import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class PullRequestTests(unittest.TestCase):
    def test_profile_declares_the_pull_request_target(self):
        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))

        pull_request = profile["pull_request"]
        self.assertTrue(pull_request["enabled"])
        self.assertEqual(pull_request["provider"], "github")
        self.assertEqual(pull_request["base_branch"], "fde_17")

    def test_skill_creates_a_pull_request_without_merging(self):
        content = (ROOT / "skills/create-fix-pull-request/SKILL.md").read_text(encoding="utf-8")

        for value in ("gh pr create", "github.com/openfde", "fde_17", "只创建", "不合入", "pull_request_created", "data/pr-work", "git apply --check"):
            self.assertIn(value, content, value)

    def test_workflow_and_context_allow_the_confirmed_pr_step(self):
        workflow = (ROOT / "skills/run-issue-workflow/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("create-fix-pull-request", workflow)

        context = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("create-fix-pull-request", context)
        self.assertIn("只创建不合入", context)

    def test_disclaimers_use_the_fix_assistant_role_name(self):
        draft = (ROOT / "skills/draft-issue-comment/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("由 AI 修复助手生成", draft)

        pull_request = (ROOT / "skills/create-fix-pull-request/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("由 AI 修复助手生成", pull_request)

    def test_pr_updates_must_be_surfaced_to_the_issue(self):
        skill = (ROOT / "skills/create-fix-pull-request/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("必须立即继续", skill)

        workflow = (ROOT / "skills/run-issue-workflow/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("必须立即发布到 issue", workflow)

    def test_comment_draft_references_pull_request_when_present(self):
        content = (ROOT / "skills/draft-issue-comment/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("pull-request.json", content)
        self.assertIn("只创建、未合入、未验证", content)

    def test_multi_project_fixes_create_one_pull_request_per_project(self):
        content = (ROOT / "skills/create-fix-pull-request/SKILL.md").read_text(encoding="utf-8")

        for value in ("多个项目", "分别生成", "pull_requests", "每个项目一个", "全部 PR 链接"):
            self.assertIn(value, content, value)

    def test_comment_lists_every_project_pull_request_link(self):
        content = (ROOT / "skills/draft-issue-comment/SKILL.md").read_text(encoding="utf-8")

        for value in ("pull_requests", "逐个列出", "单项目"):
            self.assertIn(value, content, value)

    def test_published_texts_use_fixed_fix_assistant_footer_without_internal_paths(self):
        draft = (ROOT / "skills/draft-issue-comment/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("*由 AI 修复助手生成、未验证；内容仅供参考，不代表已验证结论。*", draft)
        self.assertIn("不得写出 `.fde-ai/`、`data/` 等内部产物路径", draft)
        self.assertIn("“分析产物”字样", draft)

        pull_request = (ROOT / "skills/create-fix-pull-request/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "*由 AI 修复助手生成、未构建未测试（not_run）、未合入；内容仅供参考。*",
            pull_request,
        )
        self.assertIn("不得写出 `.fde-ai/`、`data/` 等内部产物路径", pull_request)

        publish = (ROOT / "skills/publish-policy-comment/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("no_internal_paths", publish)


if __name__ == "__main__":
    unittest.main()
