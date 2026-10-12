import json
import unittest
from pathlib import Path


class OpenFdeSkillsTests(unittest.TestCase):
    def test_project_exposes_skills_and_only_the_server_automation_entry(self):
        root = Path(__file__).parents[1]
        expected = {
            "load-project-profile",
            "build-project-context",
            "list-github-issues",
            "fetch-github-issue",
            "extract-log-evidence",
            "extract-text-evidence",
            "resolve-manifest-components",
            "cache-provenanced-sources",
            "retrieve-knowledge",
            "trace-evidence-to-source",
            "verify-analysis",
            "propose-fix",
            "draft-patch",
            "validate-patch-artifact",
            "confirm-component-mapping",
            "request-build",
            "collect-build-artifacts",
            "collect-device-evidence",
            "draft-issue-comment",
            "publish-policy-comment",
            "sync-github-replies",
            "archive-case",
            "propose-knowledge",
            "promote-knowledge",
            "validate-knowledge",
            "run-issue-workflow",
            "scan-github-issues",
        }

        profile = json.loads((root / "profiles/openfde/profile.json").read_text())
        self.assertEqual(profile["github"]["repository"], "openfde/openfde")
        self.assertNotIn("artifact_helper", profile)
        self.assertTrue((root / "automation/openfde_ai_server.py").is_file())
        self.assertFalse((root / "automation/openfde_workflow.py").exists())
        self.assertFalse((root / "server").exists())
        self.assertFalse((root / "tools").exists())
        self.assertFalse((root / "skills/legacy").exists())
        self.assertEqual(
            {entry.name for entry in (root / ".pi/skills").iterdir() if entry.is_symlink()},
            expected,
        )

    def test_server_delegates_analysis_to_the_project_skill(self):
        body = (Path(__file__).parents[1] / "automation/openfde_ai_server.py").read_text(
            encoding="utf-8"
        )

        self.assertIn('"--no-session", "--skill"', body)
        self.assertIn('root / "skills/run-issue-workflow"', body)
        self.assertNotIn("openfde_workflow.py", body)
        self.assertNotIn("fetch-openfde-issue", body)

    def test_fetch_requires_an_explicit_trusted_selection(self):
        root = Path(__file__).parents[1]
        fetch = (root / "skills/fetch-github-issue/SKILL.md").read_text(encoding="utf-8")
        orchestrator = (root / "skills/run-issue-workflow/SKILL.md").read_text(
            encoding="utf-8"
        )
        context = (root / "AGENTS.md").read_text(encoding="utf-8")

        for content in (fetch, orchestrator, context):
            self.assertIn("显式指定的问题编号或完整 URL", content)
            self.assertIn("不得从问题列表、旧产物或上下文自行选择", content)
        self.assertIn("受信任的服务器队列", fetch)

    def test_skill_descriptions_and_usage_are_chinese_and_use_the_generic_entry(self):
        root = Path(__file__).parents[1]
        for skill in (root / "skills").glob("*/SKILL.md"):
            content = skill.read_text(encoding="utf-8")
            self.assertIn("description: 当", content, skill)
            self.assertNotIn("description: Use when", content, skill)

        usage = (root / "docs/guides/pi-usage.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("/skill:run-issue-workflow", usage)
        self.assertIn("/skill:scan-github-issues", usage)
        self.assertNotIn("openfde_workflow.py", usage)


if __name__ == "__main__":
    unittest.main()
