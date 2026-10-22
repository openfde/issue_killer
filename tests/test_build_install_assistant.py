import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BuildInstallAssistantTests(unittest.TestCase):
    def test_single_command_and_remote_builder_exist(self):
        for name in ("deploy/assist/build-install.sh", "deploy/assist/build-remote.sh", "deploy/install/fde-install.sh", "deploy/install/fde-start.sh", "deploy/docker/build-install.sh", "skills/build-install/SKILL.md"):
            self.assertTrue((ROOT / name).is_file(), name)

        skill = (ROOT / "skills/build-install/SKILL.md").read_text(encoding="utf-8")
        for value in ("/skill:build-install", "--pr", "--no-pr", "--latest-pr", "--branch", "--jobs", "modules.json", "BoringdroidSystemUI", "自然语言"):
            self.assertIn(value, skill, value)

        command = (ROOT / "deploy/assist/build-install.sh").read_text(encoding="utf-8")
        for value in ("--pr", "--no-pr", "--module", "--no-install", "--no-start", "--latest-pr", "--branch", "--jobs", "--start-only", "build-remote.sh", "fde-install.sh"):
            self.assertIn(value, command, value)

        installer = (ROOT / "deploy/install/fde-install.sh").read_text(encoding="utf-8")
        self.assertIn("--start-only", installer)

        wrapper = (ROOT / "deploy/docker/build-install.sh").read_text(encoding="utf-8")
        self.assertIn('docker exec -u agent', wrapper)
        self.assertIn('/workspace/deploy/assist/build-install.sh', wrapper)

        starter = (ROOT / "deploy/install/fde-start.sh").read_text(encoding="utf-8")
        for value in ("fde_ctrl", "waydroid session start", "fde_shortcut"):
            self.assertIn(value, starter, value)

    def test_module_map_and_profile(self):
        modules = json.loads((ROOT / "deploy/assist/modules.json").read_text(encoding="utf-8"))
        documents = modules["DocumentsUI"]
        self.assertEqual(documents["project"], "packages/apps/DocumentsUI")
        self.assertEqual(documents["repository"], "openfde/packages_apps_documentsui")
        self.assertEqual(documents["artifact"], "system/priv-app/DocumentsUI/DocumentsUI.apk")
        self.assertEqual(documents["image"], "system")
        self.assertEqual(documents["dest"], "/system/priv-app/DocumentsUI/DocumentsUI.apk")
        self.assertEqual(documents["kind"], "apk")
        self.assertEqual(documents["jobs"], 4)
        self.assertEqual(modules["SystemUI"]["jobs"], 8)
        self.assertEqual(modules["libinput"]["jobs"], 4)
        self.assertEqual(modules["FdeSystemUI"]["aliases"], ["BoringdroidSystemUI", "boringdroidsystemui"])
        self.assertEqual(modules["FdeSystemUI"]["project"], "packages/apps/BoringdroidSystemUI")
        self.assertEqual(modules["FdeSystemUI"]["repository"], "openfde/boringdroidsystemui")
        self.assertEqual(modules["FdeSystemUI"]["artifact"], "system/system_ext/priv-app/FdeSystemUI/FdeSystemUI.apk")
        self.assertEqual(modules["FdeSystemUI"]["jobs"], 8)

        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))
        build = profile["build"]
        self.assertTrue(build["enabled"])
        self.assertTrue(build["install"])
        self.assertEqual(build["mode"], "assist")
        self.assertEqual(build["target"], "fde_arm64-cp2a-user")
        self.assertEqual(build["product"], "fde_arm64")
        self.assertEqual(build["module_map"], "deploy/assist/modules.json")
        self.assertEqual(build["modules"], ["DocumentsUI"])

    def test_dockerfile_has_ssh_client(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("openssh-client", dockerfile)

    def test_docs_and_workflow_mention_build_install(self):
        docs = (ROOT / "docs/guides/build-install.md").read_text(encoding="utf-8")
        for value in ("build-install.sh", "--pr", "--no-pr", "fde-start.sh"):
            self.assertIn(value, docs, value)
        workflow = (ROOT / "skills/run-issue-workflow/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("build-install.sh", workflow)
        self.assertIn("build.install=true", workflow)


if __name__ == "__main__":
    unittest.main()
