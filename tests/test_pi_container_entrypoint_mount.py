import unittest
from pathlib import Path


class PiContainerEntrypointMountTests(unittest.TestCase):
    def test_entrypoint_is_copied_outside_the_bind_mounted_workspace(self):
        dockerfile = (Path(__file__).parents[1] / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("COPY deploy/docker-entrypoint.sh /usr/local/bin/openfde-entrypoint", dockerfile)
        self.assertNotIn("ln -s /workspace/deploy/docker-entrypoint.sh", dockerfile)


if __name__ == "__main__":
    unittest.main()
