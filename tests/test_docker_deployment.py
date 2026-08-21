import unittest
from pathlib import Path


class DockerDeploymentTests(unittest.TestCase):
    def test_compose_scanner_runs_the_persistent_scan_loop(self):
        root = Path(__file__).parents[1]
        compose = (root / "compose.yaml").read_text(encoding="utf-8")
        dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("scanner:", compose)
        self.assertIn("restart: unless-stopped", compose)
        self.assertIn("SCAN_INTERVAL_SECONDS", compose)
        self.assertIn("/usr/local/bin/openfde-scan-loop", compose)
        self.assertIn("read_only: true", compose)
        self.assertIn("HOME: /tmp", compose)
        self.assertIn("GH_TOKEN: ${GH_TOKEN:?", compose)
        self.assertIn("DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:?", compose)
        self.assertIn("/workspace/.fde-ai", compose)
        self.assertIn("/workspace/data", compose)
        self.assertIn("COPY deploy/run-scan-loop.sh /usr/local/bin/openfde-scan-loop", dockerfile)

    def test_scan_loop_has_a_bounded_interval_and_no_docker_systemd_timer(self):
        root = Path(__file__).parents[1]
        loop_path = root / "deploy/run-scan-loop.sh"
        self.assertTrue(loop_path.exists())
        loop = loop_path.read_text(encoding="utf-8")

        self.assertIn("SCAN_INTERVAL_SECONDS", loop)
        self.assertIn("automation/openfde_ai_server.py", loop)
        self.assertIn("sleep", loop)
        self.assertFalse((root / "deploy/systemd/openfde-ai-docker-scan.service").exists())
        self.assertFalse((root / "deploy/systemd/openfde-ai-docker-scan.timer").exists())


if __name__ == "__main__":
    unittest.main()
