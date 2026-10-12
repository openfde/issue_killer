import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class ServerDeploymentTests(unittest.TestCase):
    def test_ai_image_derives_from_builder_with_node_pi_and_gh(self):
        dockerfile = (ROOT / "deploy/server/Dockerfile.ai").read_text(encoding="utf-8")

        self.assertIn("FROM aosp17-builder:latest", dockerfile)
        self.assertIn("registry.npmmirror.com", dockerfile)
        self.assertIn("@earendil-works/pi-coding-agent", dockerfile)
        self.assertIn("android-tools-adb", dockerfile)
        self.assertIn("/usr/local/bin/gh", dockerfile)
        self.assertIn("PI_CODING_AGENT_DIR=/workspace/pi-agent", dockerfile)

    def test_build_helper_locks_tree_and_always_reverts_patch(self):
        helper = (ROOT / "deploy/server/fde-ai-build.sh").read_text(encoding="utf-8")

        for value in ("flock -n 9", ".siso_lock", "apply -R", "build-result.json", "build_done", "build_failed"):
            self.assertIn(value, helper, value)

    def test_run_container_mounts_workspace_sources_and_build_tree(self):
        script = (ROOT / "deploy/server/run-ai-container.sh").read_text(encoding="utf-8")

        for value in ("/workspace", "fde-sources:ro", "fde-build", "/aosp3/out_fde17", "aosp17-ai:latest", "--env-file"):
            self.assertIn(value, script, value)

    def test_profile_build_helper_points_to_the_deploy_script(self):
        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))
        helper = profile["build"]["helper"]

        self.assertEqual(helper, "deploy/server/fde-ai-build.sh")
        self.assertTrue((ROOT / helper).is_file())

    def test_env_example_keeps_tokens_blank(self):
        content = (ROOT / "deploy/server/env.example").read_text(encoding="utf-8")

        self.assertIn("GH_TOKEN=\n", content)
        self.assertIn("DEEPSEEK_API_KEY=\n", content)


if __name__ == "__main__":
    unittest.main()
