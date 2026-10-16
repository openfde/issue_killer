import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class InteractionLoopTests(unittest.TestCase):
    def test_profile_enables_interaction_comments_and_reply_polling(self):
        profile = json.loads((ROOT / "profiles/openfde/profile.json").read_text(encoding="utf-8"))

        self.assertEqual(profile["publication"]["interaction_comments"], "auto")
        self.assertEqual(profile["replies"]["poll_seconds"], 180)

    def test_escalation_skill_publishes_options_and_waits(self):
        content = (ROOT / "skills/escalate-issue/SKILL.md").read_text(encoding="utf-8")

        for value in ("openfde-ai:escalation", "awaiting_direction", "A/B/C", "interaction_comments", "耗时预算"):
            self.assertIn(value, content, value)

    def test_reply_sync_handles_direction_regression_and_confirmation(self):
        content = (ROOT / "skills/sync-github-replies/SKILL.md").read_text(encoding="utf-8")
        for value in ("replies-seen.json", "direction_received", "confirmed_fixed", "awaiting_verification", "revision"):
            self.assertIn(value, content, value)

        publish = (ROOT / "skills/publish-policy-comment/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("awaiting_verification", publish)

    def test_reply_poll_script_checks_only_waiting_issues(self):
        script = (ROOT / "deploy/reply-poll.sh").read_text(encoding="utf-8")

        for value in ("awaiting_direction", "awaiting_verification", "180"):
            self.assertIn(value, script, value)

    def test_description_level_evidence_and_no_collection_option(self):
        extract = (ROOT / "skills/extract-text-evidence/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("description", extract)

        collect = (ROOT / "skills/collect-device-evidence/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("不采集", collect)


if __name__ == "__main__":
    unittest.main()
