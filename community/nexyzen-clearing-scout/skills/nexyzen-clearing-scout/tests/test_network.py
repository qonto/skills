"""Regression tests for credential and invoice destination restrictions."""

import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from email.message import Message
from unittest.mock import patch
import urllib.error
import urllib.request
import urllib.response

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
check = importlib.import_module("check_compensations")
submit = importlib.import_module("submit_to_nexyzen")

BASE_URL = "https://webapp.cameracompensazione.it/webservices/index.php"


@contextlib.contextmanager
def fake_transport(status=200, location=None):
    """Keep urllib validation/redirect handling real; replace HTTPS transport."""
    requests = []

    class HTTPSHandler(urllib.request.HTTPSHandler):
        def https_open(self, request):
            requests.append((request.full_url, json.loads(request.data) if request.data else None))
            headers = Message()
            if location:
                headers["Location"] = location
            response = urllib.response.addinfourl(
                io.BytesIO(b'{"jwt": "FAKE_JWT", "compensazioni": [], "lettere": []}'),
                headers, request.full_url, status,
            )
            response.msg = "Test response"
            return response

    with patch.object(urllib.request, "HTTPSHandler", HTTPSHandler), \
            patch.object(urllib.request, "_opener", None):
        yield requests


class NetworkTests(unittest.TestCase):
    def test_allowed_endpoint_returns_json(self):
        for module in (check, submit):
            with self.subTest(script=module.__name__), fake_transport() as requests:
                response = module.post_json(BASE_URL + "/connect", {"token": "FAKE_SECRET"})
                self.assertEqual(response["jwt"], "FAKE_JWT")
                self.assertEqual(requests, [(BASE_URL + "/connect", {"token": "FAKE_SECRET"})])

    def test_unapproved_destinations_rejected_before_transport(self):
        urls = (
            "https://attacker.invalid/api",
            "http://webapp.cameracompensazione.it/webservices/index.php",
            "https://webapp.cameracompensazione.it.attacker.invalid/webservices/index.php",
            "https://webapp.cameracompensazione.it@attacker.invalid/webservices/index.php",
            "https://webapp.cameracompensazione.it:444/webservices/index.php",
            BASE_URL + "?forward=https://attacker.invalid",
            BASE_URL + "/other",
        )
        for module in (check, submit):
            for url in urls:
                with self.subTest(script=module.__name__, url=url), fake_transport() as requests:
                    with self.assertRaises(ValueError):
                        module.post_json(url, {"token": "FAKE_SECRET"})
                    self.assertEqual(requests, [])

    def test_redirects_refused_without_second_request(self):
        for module in (check, submit):
            for status in (301, 302, 303, 307, 308):
                for target in ("https://attacker.invalid/api", BASE_URL + "/send_manual"):
                    with self.subTest(script=module.__name__, status=status, target=target), \
                            fake_transport(status, target) as requests, \
                            contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises((urllib.error.HTTPError, SystemExit)):
                            module.post_json(BASE_URL + "/connect", {"token": "FAKE_SECRET"})
                        self.assertEqual(len(requests), 1)
                        self.assertEqual(requests[0][0], BASE_URL + "/connect")

    def test_lookup_ignores_endpoint_override(self):
        env = {"NEXYZEN_BASE_URL": "https://attacker.invalid/api",
               "NEXYZEN_AFFILIATE_CODE": "FAKE_AFFILIATE", "NEXYZEN_TOKEN": "FAKE_SECRET"}
        for command in ("list", "letters"):
            with self.subTest(command=command), patch.dict(os.environ, env), \
                    patch.object(sys, "argv", ["check_compensations.py", command, "--org-vat", "TEST_ORG"]), \
                    fake_transport() as requests, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(check.main(), 0)
                self.assertEqual([url for url, _ in requests], [BASE_URL + "/connect", BASE_URL])
                self.assertEqual(requests[0][1]["dati"]["token"], "FAKE_SECRET")
                self.assertEqual(requests[1][1]["dati"]["partita_iva"], "TEST_ORG")

    def test_submission_ignores_endpoint_override(self):
        ledger = {"counterparties": [{"vat": "TEST_COUNTERPARTY", "vat_country": "",
                  "invoices": [{"kind": "receivable", "number": "TEST-001", "issue_date": "2026-10-08",
                                "total_amount": "100.00", "open_amount": "100.00"}]}]}
        env = {"NEXYZEN_BASE_URL": "https://attacker.invalid/api",
               "NEXYZEN_AFFILIATE_CODE": "FAKE_AFFILIATE", "NEXYZEN_TOKEN": "FAKE_SECRET"}
        with tempfile.TemporaryDirectory() as directory:
            ledger_path = Path(directory) / "ledger.json"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            with patch.dict(os.environ, env), \
                    patch.object(sys, "argv", ["submit_to_nexyzen.py", "--ledger", str(ledger_path),
                                               "--org-vat", "TEST_ORG", "--send"]), \
                    patch.object(submit, "confirm_on_user_terminal", return_value=True), \
                    fake_transport() as requests, contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(submit.main(), 0)
                self.assertEqual([url for url, _ in requests],
                                 [BASE_URL + "/connect", BASE_URL + "/send_manual"])
                self.assertEqual(requests[0][1]["dati"]["token"], "FAKE_SECRET")
                self.assertEqual(requests[1][1]["dati"]["numero_fattura"], "TEST-001")


if __name__ == "__main__":
    unittest.main()
