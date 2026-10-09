"""HTTPS requests restricted to the reviewed Nexyzen API endpoints."""

import json
import urllib.error
import urllib.request

BASE_URL = "https://webapp.cameracompensazione.it/webservices/index.php"
ALLOWED_URLS = frozenset((BASE_URL, BASE_URL + "/connect", BASE_URL + "/send_manual"))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "Redirects are not allowed", headers, fp)


def post_json(url: str, payload: dict) -> dict:
    if url not in ALLOWED_URLS:
        raise ValueError("Only the fixed Nexyzen HTTPS API endpoints are allowed")
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))
