import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SEED = ROOT / "profiles/openfde/component-map"


class ComponentMapTests(unittest.TestCase):
    def test_profile_declares_component_map_locations(self):
        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))

        components = profile["components"]
        self.assertEqual(components["map_seed"], "profiles/openfde/component-map")
        self.assertEqual(components["map_learned"], "data/knowledge/component-map")
        self.assertEqual(components["review_state"], "component_review_requested")

    def test_seed_entries_document_format_and_real_projects(self):
        readme = (SEED / "README.md").read_text(encoding="utf-8")
        entries = (SEED / "entries.md").read_text(encoding="utf-8")

        for kind in ("log-tag", "package", "path", "module", "property-prefix", "keyword"):
            self.assertIn(kind, readme)
        for value in (
            "device_fde",
            "packages_apps_TaskManager",
            "waydroid_android_external_mesa3d",
            "external_pulseaudio",
            "packages_modules_Bluetooth",
        ):
            self.assertIn(value, entries, value)
        self.assertIn("data/knowledge/component-map", readme)

    def test_resolve_skill_uses_three_layers_and_stops_for_review(self):
        content = (ROOT / "skills/resolve-manifest-components/SKILL.md").read_text(encoding="utf-8")

        for value in ("component-map", "fde-sources/", ".git", "component_review_requested", "confirm-component-mapping"):
            self.assertIn(value, content, value)

    def test_confirm_skill_persists_human_mapping(self):
        content = (ROOT / "skills/confirm-component-mapping/SKILL.md").read_text(encoding="utf-8")

        for value in ("component_review_requested", "manifest_resolved", "data/knowledge/component-map/entries.md", "source: human"):
            self.assertIn(value, content, value)

    def test_component_attribution_document_is_linked_from_the_index(self):
        doc = ROOT / "docs/architecture/component-attribution.md"
        self.assertTrue(doc.is_file())
        index = (ROOT / "docs/README.md").read_text(encoding="utf-8")
        self.assertIn("architecture/component-attribution.md", index)


if __name__ == "__main__":
    unittest.main()
