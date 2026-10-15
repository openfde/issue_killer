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

    def test_comment_draft_references_pull_request_when_present(self):
        content = (ROOT / "skills/draft-issue-comment/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("pull-request.json", content)
        self.assertIn("只创建、未合入、未验证", content)


if __name__ == "__main__":
    unittest.main()
