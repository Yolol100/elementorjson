from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "orchestrator_runtime_request.py"
spec = importlib.util.spec_from_file_location("orchestrator_runtime_request", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def valid_request() -> dict:
    return {
        "schema_version": "1.0",
        "request_id": "elementor-123",
        "enabled": True,
        "owner": "elementor",
        "project_id": "project-elementor",
        "for": "Controlled Elementor runtime verification",
        "task": "Run the existing pinned Elementor QA workflow",
        "why": "Produce correlated controlled-runtime evidence",
        "trigger_when": "Only for an explicit controller request",
        "do_not_trigger_when": "Never for production mutation or confidential input",
        "requested_by": "webactueel-workflow",
        "source_context": {
            "project_id": "project-elementor",
            "source_set_version": "2026-08-15.2-controlled-runtime-hardened",
        },
    }


class OrchestratorRuntimeRequestTests(unittest.TestCase):
    def test_valid_request(self):
        data = valid_request()
        self.assertEqual(module.validate_request(data), data)

    def test_rejects_unknown_keys(self):
        data = valid_request()
        data["secret"] = "nope"
        with self.assertRaisesRegex(ValueError, "unsupported request keys"):
            module.validate_request(data)

    def test_rejects_wrong_owner(self):
        data = valid_request()
        data["owner"] = "seo"
        with self.assertRaisesRegex(ValueError, "owner/project mismatch"):
            module.validate_request(data)

    def test_rejects_multiline_text(self):
        data = valid_request()
        data["why"] = "unsafe\nvalue"
        with self.assertRaisesRegex(ValueError, "missing or unsafe why"):
            module.validate_request(data)

    def test_rejects_bad_source_context(self):
        data = valid_request()
        data["source_context"]["extra"] = "drift"
        with self.assertRaisesRegex(ValueError, "source_context"):
            module.validate_request(data)

    def test_rejects_untrusted_requester(self):
        data = valid_request()
        data["requested_by"] = "someone-else"
        with self.assertRaisesRegex(ValueError, "requested_by"):
            module.validate_request(data)


if __name__ == "__main__":
    unittest.main()
