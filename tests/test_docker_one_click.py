import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class DockerOneClickTests(unittest.TestCase):
    def test_one_click_assets_exist(self):
        for name in ("up.sh", "pi.sh", "sync-sources.sh", "select-sources.py", "github-sources.tsv"):
            self.assertTrue((ROOT / "deploy/docker" / name).is_file(), name)

    def test_up_script_checks_prerequisites_and_starts_compose(self):
        content = (ROOT / "deploy/docker/up.sh").read_text(encoding="utf-8")

        for value in (
            "GH_TOKEN",
            "DEEPSEEK_API_KEY",
            "OPENAI_API_KEY",
            "PI_PROVIDER",
            "load_env",
            "cp \"$ROOT/deploy/server/env.example\"",
            "docker compose build",
            "docker compose up -d",
            "config/openfde-ai-server.json",
            "fde-manifests",
            "fde-sources",
            "--force-sync",
            "docker exec -it openfde-ai",
        ):
            self.assertIn(value, content, value)

    def test_pi_wrapper_uses_the_fixed_container_name(self):
        content = (ROOT / "deploy/docker/pi.sh").read_text(encoding="utf-8")

        for value in ("docker exec -it openfde-ai pi", "openfde-ai"):
            self.assertIn(value, content, value)

    def test_sync_script_uses_repo_and_only_selected_modules(self):
        content = (ROOT / "deploy/docker/sync-sources.sh").read_text(encoding="utf-8")

        for value in (
            "repo init",
            "repo sync",
            "FDE_SOURCE_MODULES",
            "openfde-sdk",
            "select-sources.py",
            ".fde-ai-sync.json",
            "FORCE_SYNC",
            "chmod -R a+rX",
            "FDE_SYNC_MODE",
            "github-sources.tsv",
            "sync_one_github",
        ):
            self.assertIn(value, content, value)

    def test_github_source_map_covers_the_current_tree(self):
        rows = [
            line.split("\t")
            for line in (ROOT / "deploy/docker/github-sources.tsv").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        self.assertEqual(len(rows), 48)
        paths = {row[0] for row in rows}
        for path in (
            "frameworks/base",
            "packages/apps/TaskPlugin",
            "device/openfde/ftg340",
            "openfde-sdk",
        ):
            self.assertIn(path, paths)
        for row in rows:
            self.assertTrue(row[1].startswith("https://github.com/openfde/"), row)

    def test_select_sources_filters_by_top_level_path(self):
        manifest = """<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <project name="platform/frameworks/base" path="frameworks/base" />
  <project name="platform/packages/apps/Settings" path="packages/apps/Settings" />
  <project name="platform/external/skia" path="external/skia" />
  <project name="platform/build/make" path="build/make" />
</manifest>
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.xml"
            path.write_text(manifest, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "deploy/docker/select-sources.py"),
                    str(path),
                    "frameworks",
                    "packages",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        names = result.stdout.split()
        self.assertEqual(names, ["platform/frameworks/base", "platform/packages/apps/Settings"])

    def test_entrypoint_injects_model_settings_and_git_auth(self):
        content = (ROOT / "deploy/docker-entrypoint.sh").read_text(encoding="utf-8")

        for value in (
            "PI_PROVIDER",
            "PI_MODEL",
            "settings.json",
            "safe.directory",
            "gh auth setup-git",
        ):
            self.assertIn(value, content, value)

    def test_scanner_and_poller_share_the_per_issue_lock(self):
        server = (ROOT / "automation/openfde_ai_server.py").read_text(encoding="utf-8")
        poller = (ROOT / "deploy/reply-poll.sh").read_text(encoding="utf-8")

        for content in (server, poller):
            self.assertIn(".workflow.lock", content)
        self.assertIn("fcntl.flock", server)
        self.assertIn("flock -n", poller)


if __name__ == "__main__":
    unittest.main()
