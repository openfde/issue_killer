import unittest
from pathlib import Path


class ContainerTests(unittest.TestCase):
    def test_runtime_image_contract(self):
        root = Path(__file__).parents[1]
        dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
        ignored = (root / ".dockerignore").read_text(encoding="utf-8")

        for value in (
            "node:24-bookworm-slim",
            "git gh ca-certificates",
            "ripgrep",
            "repo",
            "adb version",
            "PYTHONDONTWRITEBYTECODE=1",
            "openfde-scan-loop",
        ):
            self.assertIn(value, dockerfile, value)
        for value in (".git/", "fde-manifests/", "fde-sources/", "sources/", ".fde-ai/", "data/"):
            self.assertIn(value, ignored, value)


if __name__ == "__main__":
    unittest.main()
