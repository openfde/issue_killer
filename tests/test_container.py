import unittest
from pathlib import Path


class ContainerTests(unittest.TestCase):
    def test_clean_test_container_contract(self):
        root = Path(__file__).parents[1]
        dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
        ignored = (root / ".dockerignore").read_text(encoding="utf-8")

        self.assertIn("python:3.11-slim-bookworm", dockerfile)
        self.assertIn("git gh ca-certificates", dockerfile)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", dockerfile)
        self.assertIn("python", dockerfile)
        self.assertIn("unittest", dockerfile)
        for value in (".git/", "fde-manifests/", "sources/", ".fde-ai/", "data/"):
            self.assertIn(value, ignored)


if __name__ == "__main__":
    unittest.main()
