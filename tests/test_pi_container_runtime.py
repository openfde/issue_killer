import unittest
from pathlib import Path


class PiContainerRuntimeTests(unittest.TestCase):
    def test_entrypoint_copies_only_optional_pi_login_to_tmpfs(self):
        root = Path(__file__).parents[1]
        dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn('ENTRYPOINT ["/usr/local/bin/openfde-entrypoint"]', dockerfile)
        entrypoint = (root / "deploy/docker-entrypoint.sh").read_text(encoding="utf-8")
        self.assertIn("/run/secrets/pi-agent", entrypoint)
        self.assertIn("/tmp/pi-agent", entrypoint)
        self.assertNotIn("/run/secrets/gh", entrypoint)
        self.assertNotIn("GH_CONFIG_DIR", entrypoint)
        self.assertNotIn("/tmp/gh", entrypoint)


if __name__ == "__main__":
    unittest.main()
