import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "profiles" / "openfde" / "knowledge" / "cases"
SECRET_RE = re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}")


class VersionedKnowledgeCaseTests(unittest.TestCase):
    def test_index_only_contains_verified_cases_that_exist(self):
        index = json.loads((CASES / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["schema_version"], 1)
        self.assertTrue(index["cases"])
        self.assertTrue(index["generated_at"])

        for entry in index["cases"]:
            self.assertTrue(entry["verified"])
            self.assertEqual(entry["knowledge_status"], "verified")
            self.assertEqual(entry["source"], "versioned")
            self.assertFalse(Path(entry["path"]).is_absolute())

            case_path = CASES / entry["path"]
            self.assertTrue(case_path.is_file(), case_path)
            case = json.loads(case_path.read_text(encoding="utf-8"))
            self.assertEqual(case["issue"], entry["issue"])
            self.assertEqual(case["title"], entry["title"])
            self.assertEqual(case["revision"], entry["revision"])
            self.assertEqual(case["knowledge_status"], "verified")
            self.assertTrue(case["verification"]["verified"])
            self.assertEqual(
                [component["project"] for component in case["components"]],
                [component["project"] for component in entry["components"]],
            )

    def test_issue_500_case_is_a_verified_frameworks_base_fix(self):
        case = json.loads((CASES / "500" / "case.json").read_text(encoding="utf-8"))
        self.assertEqual(case["case_id"], "issue-500")
        self.assertEqual(case["repo"], "openfde/openfde")
        self.assertEqual(case["status"], "confirmed_fixed")
        self.assertEqual(case["knowledge_status"], "verified")
        self.assertTrue(case["verification"]["verified"])
        self.assertIn("frameworks_base", {component["project"] for component in case["components"]})
        self.assertEqual(case["fix"]["pull_request"], "10")

        markdown = (CASES / "500" / "case.md").read_text(encoding="utf-8")
        self.assertIn("Issue #500", markdown)
        self.assertIn("windowIsFloating", markdown)

    def test_versioned_case_files_do_not_contain_tokens(self):
        for path in CASES.rglob("*"):
            if path.is_file() and path.suffix in {".json", ".md"}:
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(text, SECRET_RE, str(path))

    def test_retrieval_reads_versioned_seed_before_runtime(self):
        skill = (ROOT / "skills" / "retrieve-knowledge" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("profiles/openfde/knowledge/cases/index.json", skill)
        self.assertIn("data/knowledge/index.json", skill)
        self.assertIn("versioned", skill)
        self.assertIn("runtime", skill)

        guide = (ROOT / "docs" / "guides" / "knowledge-base.md").read_text(encoding="utf-8")
        self.assertIn("profiles/openfde/knowledge/cases/", guide)
        self.assertIn("运行时", guide)


if __name__ == "__main__":
    unittest.main()
