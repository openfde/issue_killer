import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ArtifactLayoutTests(unittest.TestCase):
    def test_profile_declares_the_single_canonical_issue_layout(self):
        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))

        layout = profile["artifacts"]["issue_layout"]
        self.assertEqual(layout["root"], ".fde-ai/issues/{issue_number}")
        self.assertEqual(layout["patch"], "patch/0001-{slug}.patch")
        self.assertEqual(
            layout["required_directories"],
            ["input", "evidence", "analysis", "solution", "patch", "build", "comment", "archive"],
        )

    def test_profile_declares_the_local_tree_sources_and_manual_build_channel(self):
        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))

        self.assertEqual(profile["sources"]["mode"], "local_tree")
        self.assertTrue(profile["sources"]["read_only"])
        build = profile["build"]
        self.assertEqual(build["mode"], "manual")
        self.assertEqual(build["helper"], "deploy/server/fde-ai-build.sh")
        self.assertEqual(build["tree"], "fde-build")
        self.assertIn("systemimage", build["modules"])
        self.assertIn("vendorimage", build["modules"])
        self.assertTrue(all(item.startswith("target/product/") for item in build["artifacts"]))

    def test_active_workflow_documents_one_patch_entrypoint_and_forbids_runs(self):
        paths = [
            ROOT / "AGENTS.md",
            ROOT / "docs/architecture/artifact-layout.md",
            ROOT / "docs/architecture/workflow.md",
            ROOT / "skills/run-issue-workflow/SKILL.md",
            ROOT / "skills/draft-patch/SKILL.md",
            ROOT / "skills/validate-patch-artifact/SKILL.md",
            ROOT / "skills/request-build/SKILL.md",
            ROOT / "skills/collect-build-artifacts/SKILL.md",
            ROOT / "skills/archive-case/SKILL.md",
        ]
        for path in paths:
            content = path.read_text(encoding="utf-8")
            self.assertIn(".fde-ai/issues/<issue号>/patch/0001-<名称>.patch", content, path)
            self.assertIn("不得在 `.fde-ai/runs/` 创建新产物", content, path)


if __name__ == "__main__":
    unittest.main()
