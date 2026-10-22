import unittest
from pathlib import Path


class PiContainerTests(unittest.TestCase):
    def test_runtime_container_includes_node_and_pi(self):
        dockerfile = (Path(__file__).parents[1] / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("node:24-bookworm-slim", dockerfile)
        self.assertIn("python3 python-is-python3 git openssh-client gh ca-certificates", dockerfile)
        self.assertIn("@earendil-works/pi-coding-agent@0.84.2", dockerfile)
        self.assertIn("PI_TELEMETRY=0", dockerfile)


if __name__ == "__main__":
    unittest.main()
