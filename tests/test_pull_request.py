import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class PullRequestTests(unittest.TestCase):
    def test_skill_creates_a_merge_request_without_merging(self):
        content = (ROOT / "skills/create-fix-pull-request/SKILL.md").read_text(encoding="utf-8")

        for value in ("merge_request.create", "fde_17", "只创建", "不合入", "pull_request_created", "data/pr-work", "git apply --check"):
            self.assertIn(value, content, value)

    def test_workflow_and_context_allow_the_confirmed_pr_step(self):
        workflow = (ROOT / "skills/run-issue-workflow/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("create-fix-pull-request", workflow)

        context = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("create-fix-pull-request", context)
        self.assertIn("只创建不合入", context)

    def test_comment_draft_references_pull_request_when_present(self):
        content = (ROOT / "skills/draft-issue-comment/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("pull-request.json", content)
        self.assertIn("只创建、未合入、未验证", content)


if __name__ == "__main__":
    unittest.main()
