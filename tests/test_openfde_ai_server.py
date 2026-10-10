import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SERVER = Path(__file__).parents[1] / "automation/openfde_ai_server.py"


def load_server():
    spec = importlib.util.spec_from_file_location("openfde_ai_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class OpenFdeAiServerTests(unittest.TestCase):
    def test_queue_requeues_only_a_completed_issue_with_new_update_time(self):
        server = load_server()
        with tempfile.TemporaryDirectory() as directory:
            store = server.QueueStore(Path(directory) / "state.db")
            store.initialize()
            first = store.upsert_issue({"number": 470, "title": "Bluetooth failure", "updatedAt": "2026-08-17T01:00:00Z"})
            claimed = store.claim_next()
            self.assertEqual(first["action"], "queued")
            self.assertEqual(claimed["issue_number"], 470)
            self.assertIsNone(store.claim_next())
            store.finish(470, claimed["revision"], exit_code=0)
            unchanged = store.upsert_issue({"number": 470, "title": "Bluetooth failure", "updatedAt": "2026-08-17T01:00:00Z"})
            changed = store.upsert_issue({"number": 470, "title": "More logs", "updatedAt": "2026-08-17T02:00:00Z"})
            self.assertEqual(unchanged["action"], "unchanged")
            self.assertEqual(changed, {"action": "requeued", "revision": 2})
            self.assertEqual(store.claim_next()["revision"], 2)

    def test_queue_marks_failed_after_retry_limit(self):
        server = load_server()
        with tempfile.TemporaryDirectory() as directory:
            store = server.QueueStore(Path(directory) / "state.db")
            store.initialize()
            store.upsert_issue({"number": 471, "title": "worker failure", "updatedAt": "2026-08-17T01:00:00Z"})
            claimed = store.claim_next(retry_limit=1)
            assert claimed is not None
            store.finish(471, claimed["revision"], exit_code=1, retry_limit=1, error="Pi failed")
            self.assertEqual(store.counts()["failed"], 1)
            self.assertIsNone(store.claim_next(retry_limit=1))

    def test_successful_nonterminal_step_is_requeued_without_consuming_retries(self):
        server = load_server()
        with tempfile.TemporaryDirectory() as directory:
            store = server.QueueStore(Path(directory) / "state.db")
            store.initialize()
            store.upsert_issue({"number": 470, "title": "Bluetooth failure", "updatedAt": "2026-08-17T01:00:00Z"})
            claimed = store.claim_next(retry_limit=1)
            assert claimed is not None
            store.finish(470, claimed["revision"], exit_code=0, terminal=False)
            self.assertEqual(store.counts()["queued"], 1)
            next_claim = store.claim_next(retry_limit=1)
            self.assertIsNotNone(next_claim)
            self.assertEqual(next_claim["attempts"], 1)

    def test_scan_runs_multiple_atomic_steps_until_terminal_state(self):
        server = load_server()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = root / "profiles/openfde/profile.json"
            profile_path.parent.mkdir(parents=True)
            profile_path.write_text(json.dumps({"github": {"repository": "openfde/openfde"}, "artifacts": {"issue_layout": {"root": ".fde-ai/issues/{issue_number}"}}}), encoding="utf-8")
            config = {"profile": "profiles/openfde/profile.json", "data_root": "data", "pi_command": "pi", "scan": {"state": "open", "max_issues_per_run": 5, "max_workers_per_run": 1}, "worker": {"execute": True, "timeout_seconds": 60, "retry_limit": 2, "max_atomic_steps_per_issue": 2}}
            calls = []

            def runner(command, **kwargs):
                if command[:3] == ["gh", "api", "graphql"]:
                    return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"data": {"repository": {"issues": {"nodes": [{"number": 470, "title": "issue", "updatedAt": "2026-08-17T01:00:00Z"}], "pageInfo": {"endCursor": None, "hasNextPage": False}}}}}), stderr="")
                calls.append(command)
                state = root / ".fde-ai/issues/470/state.json"
                state.parent.mkdir(parents=True, exist_ok=True)
                state.write_text(json.dumps({"state": "initialized" if len(calls) == 1 else "archived"}), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            result = server.scan(root, config, runner=runner)
            self.assertEqual(result["workers_started"], 1)
            self.assertEqual(len(calls), 2)
            self.assertEqual(server.QueueStore(root / "data/state.db").counts()["completed"], 1)

    def test_configuration_paths_cannot_escape_workspace(self):
        server = load_server()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                server.resolve_path(Path(directory), "../outside")

    def test_worker_prompt_has_profile_and_non_mutation_boundaries(self):
        server = load_server()
        prompt = server.build_worker_prompt(profile_path="profiles/openfde/profile.json", issue_number=470, revision=3)
        for value in ("profiles/openfde/profile.json", "问题 #470", "受信任的服务器队列", "不得从问题列表、旧产物或上下文自行选择", "不可信", "不得修改源码", "不得运行构建、安装或测试", "publish-policy-comment", "request-build"):
            self.assertIn(value, prompt)
        self.assertNotIn("gh issue comment", prompt)

    def test_build_wait_state_stops_without_running_worker(self):
        server = load_server()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = root / "profiles/openfde/profile.json"
            profile_path.parent.mkdir(parents=True)
            profile_path.write_text(json.dumps({"github": {"repository": "openfde/openfde"}, "artifacts": {"issue_layout": {"root": ".fde-ai/issues/{issue_number}"}}}), encoding="utf-8")
            state_path = root / ".fde-ai/issues/470/state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(json.dumps({"state": "build_requested"}), encoding="utf-8")
            config = {"profile": "profiles/openfde/profile.json", "data_root": "data", "pi_command": "pi", "scan": {"state": "open", "max_issues_per_run": 5, "max_workers_per_run": 1}, "worker": {"execute": True, "timeout_seconds": 60, "retry_limit": 2, "max_atomic_steps_per_issue": 16}}
            calls = []

            def runner(command, **kwargs):
                calls.append(command)
                if command[:3] == ["gh", "api", "graphql"]:
                    return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"data": {"repository": {"issues": {"nodes": [{"number": 470, "title": "issue", "updatedAt": "2026-08-17T01:00:00Z"}], "pageInfo": {"endCursor": None, "hasNextPage": False}}}}}), stderr="")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            server.scan(root, config, runner=runner)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][:3], ["gh", "api", "graphql"])
            self.assertEqual(server.QueueStore(root / "data/state.db").counts()["queued"], 1)
            self.assertEqual(state_path.read_text(encoding="utf-8"), json.dumps({"state": "build_requested"}))

    def test_repeated_state_stops_as_no_progress(self):
        server = load_server()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = root / "profiles/openfde/profile.json"
            profile_path.parent.mkdir(parents=True)
            profile_path.write_text(json.dumps({"github": {"repository": "openfde/openfde"}, "artifacts": {"issue_layout": {"root": ".fde-ai/issues/{issue_number}"}}}), encoding="utf-8")
            state_path = root / ".fde-ai/issues/470/state.json"
            config = {"profile": "profiles/openfde/profile.json", "data_root": "data", "pi_command": "pi", "scan": {"state": "open", "max_issues_per_run": 5, "max_workers_per_run": 1}, "worker": {"execute": True, "timeout_seconds": 60, "retry_limit": 2, "max_atomic_steps_per_issue": 16}}
            worker_calls = []

            def runner(command, **kwargs):
                if command[:3] == ["gh", "api", "graphql"]:
                    return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"data": {"repository": {"issues": {"nodes": [{"number": 470, "title": "issue", "updatedAt": "2026-08-17T01:00:00Z"}], "pageInfo": {"endCursor": None, "hasNextPage": False}}}}}), stderr="")
                worker_calls.append(command)
                state_path.parent.mkdir(parents=True, exist_ok=True)
                state_path.write_text(json.dumps({"state": "initialized"}), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            server.scan(root, config, runner=runner)
            self.assertEqual(len(worker_calls), 2)
            self.assertEqual(server.QueueStore(root / "data/state.db").counts()["queued"], 1)

    def test_discovery_uses_graphql_cursor_and_ignores_pull_requests(self):
        server = load_server()
        commands = []
        def runner(command, **kwargs):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"data": {"repository": {"issues": {"nodes": [{"number": 470, "title": "issue", "updatedAt": "2026-08-17T01:00:00Z", "url": "https://example.test/470"}, {"number": 471, "title": "PR", "updatedAt": "2026-08-17T01:00:01Z", "isPullRequest": True}], "pageInfo": {"endCursor": "cursor-2", "hasNextPage": True}}}}}), stderr="")
        issues, cursor, has_next_page = server.discover_issues("openfde/openfde", "open", 20, after="cursor-1", runner=runner)
        self.assertEqual(issues, [{"number": 470, "title": "issue", "updatedAt": "2026-08-17T01:00:00Z", "url": "https://example.test/470"}])
        self.assertEqual(cursor, "cursor-2")
        self.assertTrue(has_next_page)
        self.assertEqual(commands[0][:3], ["gh", "api", "graphql"])
        self.assertIn("owner=openfde", commands[0])
        self.assertIn("name=openfde", commands[0])
        self.assertIn("after=cursor-1", commands[0])

    def test_sync_cursor_advances_then_resets_after_final_page(self):
        server = load_server()
        with tempfile.TemporaryDirectory() as directory:
            store = server.QueueStore(Path(directory) / "state.db")
            store.initialize()
            self.assertIsNone(store.get_sync_cursor())
            store.set_sync_cursor("cursor-2")
            self.assertEqual(store.get_sync_cursor(), "cursor-2")
            store.set_sync_cursor(None)
            self.assertIsNone(store.get_sync_cursor())

    def test_scan_continues_from_persisted_cursor_until_full_sweep(self):
        server = load_server()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = root / "profiles/openfde/profile.json"
            profile_path.parent.mkdir(parents=True)
            profile_path.write_text(json.dumps({"github": {"repository": "openfde/openfde"}}), encoding="utf-8")
            config = {"profile": "profiles/openfde/profile.json", "data_root": "data", "pi_command": "pi", "scan": {"state": "open", "sync_page_size": 2, "max_workers_per_run": 0}, "worker": {"execute": False, "timeout_seconds": 60, "retry_limit": 2}}
            commands = []
            responses = [
                {"data": {"repository": {"issues": {"nodes": [{"number": 1, "title": "first", "updatedAt": "2026-08-17T01:00:00Z"}, {"number": 2, "title": "second", "updatedAt": "2026-08-17T01:00:01Z"}], "pageInfo": {"endCursor": "cursor-2", "hasNextPage": True}}}}},
                {"data": {"repository": {"issues": {"nodes": [{"number": 3, "title": "third", "updatedAt": "2026-08-17T01:00:02Z"}], "pageInfo": {"endCursor": "cursor-3", "hasNextPage": False}}}}},
            ]

            def runner(command, **kwargs):
                commands.append(command)
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps(responses.pop(0)), stderr="")

            first = server.scan(root, config, runner=runner)
            second = server.scan(root, config, runner=runner)
            self.assertEqual(first["discovered"], 2)
            self.assertFalse(first["sync_complete"])
            self.assertEqual(second["discovered"], 1)
            self.assertTrue(second["sync_complete"])
            self.assertIn("after=cursor-2", commands[1])
            self.assertEqual(server.QueueStore(root / "data/state.db").counts()["queued"], 3)

    def test_discovery_failure_preserves_gh_stderr(self):
        server = load_server()
        def runner(command, **kwargs):
            raise subprocess.CalledProcessError(1, command, stderr="HTTP 502: upstream unavailable")
        with self.assertRaisesRegex(RuntimeError, "HTTP 502: upstream unavailable"):
            server.discover_issues("openfde/openfde", "open", 20, after=None, runner=runner)

    def test_dry_run_scan_queues_without_starting_pi(self):
        server = load_server()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile_path = root / "profiles/openfde/profile.json"
            profile_path.parent.mkdir(parents=True)
            profile_path.write_text(json.dumps({"github": {"repository": "openfde/openfde"}}), encoding="utf-8")
            config = {"profile": "profiles/openfde/profile.json", "data_root": "data", "pi_command": "pi", "scan": {"state": "open", "max_issues_per_run": 5, "max_workers_per_run": 1}, "worker": {"execute": False, "timeout_seconds": 60, "retry_limit": 2}}
            calls = []
            def runner(command, **kwargs):
                calls.append(command)
                return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"data": {"repository": {"issues": {"nodes": [{"number": 470, "title": "issue", "updatedAt": "2026-08-17T01:00:00Z"}], "pageInfo": {"endCursor": None, "hasNextPage": False}}}}}), stderr="")
            result = server.scan(root, config, runner=runner)
            self.assertEqual(result, {"discovered": 1, "queued": 1, "requeued": 0, "workers_started": 0, "sync_complete": True})
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0:3], ["gh", "api", "graphql"])
            self.assertTrue((root / "data/state.db").is_file())


if __name__ == "__main__":
    unittest.main()
