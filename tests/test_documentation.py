import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
CURRENT_DOCUMENTS = (
    ROOT / "README.md",
    ROOT / "docs/README.md",
    ROOT / "docs/guides/pi-usage.md",
    ROOT / "docs/guides/server-deployment.md",
    ROOT / "docs/architecture/workflow.md",
    ROOT / "docs/architecture/server-worker.md",
)
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


class DocumentationTests(unittest.TestCase):
    def test_current_documentation_has_a_single_navigation_structure(self):
        for path in CURRENT_DOCUMENTS:
            self.assertTrue(path.is_file(), path)
        self.assertFalse((ROOT / "docs/superpowers").exists())

    def test_current_documentation_has_no_obsolete_workflow_references(self):
        forbidden = (
            "automation/openfde_workflow.py",
            "tools/openfde_workflow.py",
            "server/openfde_ai_server.py",
            "fetch-openfde-issue",
            "setup-issue-workspace",
            "tests/test_openfde_workflow.py",
        )
        for path in CURRENT_DOCUMENTS:
            content = path.read_text(encoding="utf-8")
            for value in forbidden:
                self.assertNotIn(value, content, f"{path}: {value}")

    def test_archived_documents_are_marked_non_operational(self):
        archived = list((ROOT / "docs/archive").rglob("*.md"))
        self.assertTrue(archived)
        for path in archived:
            self.assertIn("仅供历史参考，不可作为当前操作依据", path.read_text(encoding="utf-8"))

    def test_current_markdown_links_resolve_to_existing_files(self):
        for path in CURRENT_DOCUMENTS:
            content = path.read_text(encoding="utf-8")
            for target in MARKDOWN_LINK.findall(content):
                target = target.strip().strip("<>")
                if "://" in target or target.startswith(("#", "mailto:")):
                    continue
                relative = target.split("#", 1)[0]
                if relative:
                    self.assertTrue((path.parent / relative).resolve().is_file(), f"{path}: {target}")

    def test_all_documentation_local_links_resolve(self):
        paths = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
        paths = [path for path in paths if "knowledge" not in path.parts]
        for path in paths:
            content = path.read_text(encoding="utf-8")
            for target in MARKDOWN_LINK.findall(content):
                target = target.strip().strip("<>")
                if "://" in target or target.startswith(("#", "mailto:")):
                    continue
                relative = target.split("#", 1)[0]
                if relative:
                    self.assertTrue((path.parent / relative).resolve().is_file(), f"{path}: {target}")


if __name__ == "__main__":
    unittest.main()
