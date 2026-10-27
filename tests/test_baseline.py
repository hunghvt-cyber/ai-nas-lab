"""Offline baseline tests written during review; not the original NAS test suite."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "src" / "gemini-task"
loader = importlib.machinery.SourceFileLoader("gemini_task", str(path))
spec = importlib.util.spec_from_loader(loader.name, loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)


class Response:
    status = 200
    headers = {}
    def __init__(self, payload):
        self.raw = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self.raw


class Baseline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name) / "config"
        for name, value in {
            "CONFIG_DIR": root,
            "KEYS_FILE": root / "keys.json",
            "STATE_FILE": root / "state.json",
            "LOCK_FILE": root / "state.lock",
        }.items():
            p = patch.object(m, name, value)
            p.start()
            self.addCleanup(p.stop)
        m.atomic_json(m.KEYS_FILE, {
            "active": "key1",
            "keys": {
                "key1": {"key": "FAKE_KEY_1", "group": "key1", "priority": 1},
                "key2": {"key": "FAKE_KEY_2", "group": "key2", "priority": 2},
            },
        })

    def run_prompt(self, key=None):
        _, args = m.parse_args((["--key", key] if key else []) + ["--timeout", "10"])
        with patch.object(m.sys, "stdin", io.StringIO("Public test prompt")), \
             contextlib.redirect_stdout(io.StringIO()) as out, \
             contextlib.redirect_stderr(io.StringIO()):
            m.run_request(args)
        return out.getvalue()

    def test_success_text(self):
        response = Response({"candidates": [{
            "finishReason": "STOP", "content": {"parts": [{"text": "OK"}]}
        }]})
        with patch.object(m.urllib.request, "urlopen", return_value=response):
            self.assertEqual(self.run_prompt(), "OK\n")

    def test_503_does_not_read_error_body(self):
        exc = urllib.error.HTTPError("https://example.invalid", 503, "", {}, io.BytesIO(b"ignored"))
        with patch.object(m.urllib.request, "urlopen", side_effect=exc), \
             patch.object(m, "read_http_error_body", side_effect=AssertionError("must not read")):
            with self.assertRaises(m.ApiFailure) as raised:
                m.send_request({"key": "FAKE"}, m.DEFAULT_MODEL, "test", 5)
        self.assertEqual(raised.exception.http, 503)

    def test_503_three_same_key_requests_no_rotation(self):
        with patch.object(m, "send_request", side_effect=m.ApiFailure(503, "", [], None)) as send, \
             patch.object(m.time, "sleep") as sleep:
            with self.assertRaises(m.TaskError) as raised:
                self.run_prompt()
        self.assertEqual(raised.exception.code, 69)
        self.assertEqual(send.call_count, 3)
        self.assertTrue(all(c.args[0]["key"] == "FAKE_KEY_1" for c in send.call_args_list))
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2])

    def test_429_rotates_and_records_model_cooldown(self):
        with patch.object(m, "send_request", side_effect=[
            m.ApiFailure(429, "RESOURCE_EXHAUSTED", [], 60), "OK"
        ]) as send:
            self.assertEqual(self.run_prompt(), "OK\n")
        self.assertEqual([c.args[0]["key"] for c in send.call_args_list], ["FAKE_KEY_1", "FAKE_KEY_2"])
        self.assertEqual(m.read_keys()["active"], "key2")
        self.assertIn(m.cooldown_key("key1", m.DEFAULT_MODEL), m.state_snapshot()["cooldowns"])

    def test_explicit_429_does_not_rotate(self):
        with patch.object(m, "send_request", side_effect=m.ApiFailure(429, "", [], 60)) as send:
            with self.assertRaises(m.TaskError):
                self.run_prompt("key1")
        self.assertEqual(send.call_count, 1)
        self.assertEqual(m.read_keys()["active"], "key1")

    def test_prompt_rejection_does_not_rotate(self):
        with patch.object(m, "send_request", side_effect=m.ApiFailure(400, "INVALID_ARGUMENT", [], None)) as send:
            with self.assertRaises(m.TaskError) as raised:
                self.run_prompt()
        self.assertEqual(raised.exception.code, 65)
        self.assertEqual(send.call_count, 1)

    def test_request_budget_enforced(self):
        with patch.object(m, "send_request") as send:
            with self.assertRaises(m.TaskError):
                m.request_with_retry({"key": "FAKE"}, m.DEFAULT_MODEL, "test", time.monotonic() + 10, 3, [0])
        send.assert_not_called()

    def test_private_permissions(self):
        m.state_snapshot()
        self.assertEqual(m.CONFIG_DIR.stat().st_mode & 0o777, 0o700)
        for p in (m.KEYS_FILE, m.STATE_FILE, m.LOCK_FILE):
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)

    # Characterization: these passing cases document unresolved behavior.
    def test_known_issue_truncated_answer_accepted(self):
        response = Response({"candidates": [{
            "finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "unfinished"}]}
        }]})
        with patch.object(m.urllib.request, "urlopen", return_value=response):
            self.assertEqual(self.run_prompt(), "unfinished\n")

    def test_known_issue_fractional_delay_rounds_down(self):
        detail = {"error": {"details": [{
            "@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "0.1s"
        }]}}
        self.assertEqual(m.retry_delay({}, detail), 0)

    def test_known_issue_error_status_not_filtered(self):
        status, _ = m.safe_error({"error": {"status": "untrusted\nprovider text"}})
        self.assertEqual(status, "untrusted\nprovider text")


if __name__ == "__main__":
    unittest.main()
