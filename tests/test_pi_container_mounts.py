import unittest
from pathlib import Path


class PiContainerMountTests(unittest.TestCase):
    def test_image_precreates_the_knowledge_volume_mountpoint(self):
        dockerfile = (Path(__file__).parents[1] / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("mkdir -p /workspace/data", dockerfile)


if __name__ == "__main__":
    unittest.main()
