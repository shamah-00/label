"""
The Label Group - UPS integration foundation.

Safe while waiting for UPS API credentials.
No shipping rates are invented.
No checkout or order models are modified.
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


def _setting(name, default=""):
    """Read a setting from environment variables."""
    return os.environ.get(name, default).strip()


def get_ups_config():
    """Read UPS configuration without exposing secrets."""
    environment = _setting("UPS_ENVIRONMENT", "sandbox").lower()

    if environment not in {"sandbox", "production"}:
        environment = "sandbox"

    if environment == "production":
        api_base = "https://onlinetools.ups.com"
    else:
        api_base = "https://wwwcie.ups.com"

    return {
        "client_id": _setting("UPS_CLIENT_ID"),
        "client_secret": _setting("UPS_CLIENT_SECRET"),
        "account_number": _setting("UPS_ACCOUNT_NUMBER"),
        "environment": environment,
        "api_base": api_base,
        "origin_postal_code": _setting("UPS_ORIGIN_POSTAL_CODE"),
        "origin_country_code": _setting(
            "UPS_ORIGIN_COUNTRY_CODE", "US"
        ).upper(),
        "currency_code": _setting("UPS_CURRENCY_CODE", "USD").upper(),
        "timeout": 20,
    }


def ups_status():
    """
    Return readiness information safe to display in staff diagnostics.
    Never return credentials or tokens.
    """
    config = get_ups_config()

    missing = []

    if not config["client_id"]:
        missing.append("UPS_CLIENT_ID")

    if not config["client_secret"]:
        missing.append("UPS_CLIENT_SECRET")

    if not config["account_number"]:
        missing.append("UPS_ACCOUNT_NUMBER")

    if not config["origin_postal_code"]:
        missing.append("UPS_ORIGIN_POSTAL_CODE")

    if not config["origin_country_code"]:
        missing.append("UPS_ORIGIN_COUNTRY_CODE")

    ready = not missing

    return {
        "provider": "UPS",
        "environment": config["environment"],
        "configured": ready,
        "live_rates_available": False,
        "missing_settings": missing,
        "message": (
            "UPS credentials are configured. API authentication and "
            "service approval must still be tested before live rates "
            "can be enabled."
            if ready
            else
            "UPS setup is waiting for credentials and shipping details. "
            "Checkout must not treat estimated rates as live UPS quotes."
        ),
    }


def _http_json(url, method="GET", headers=None, payload=None, timeout=20):
    """Make a JSON HTTP request using Python's standard library."""
    request_headers = {
        "Accept": "application/json",
        "User-Agent": "TheLabelGroup-Django/1.0",
    }

    if headers:
        request_headers.update(headers)

    data = None

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=request_headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}

    except urllib.error.HTTPError as exc:
        # Do not include request headers or secrets in error messages.
        try:
            response_body = exc.read().decode("utf-8")
            parsed = json.loads(response_body) if response_body else {}
        except (ValueError, UnicodeDecodeError):
            parsed = {}

        raise RuntimeError(
            "UPS returned HTTP status "
            f"{exc.code}. Check API access, account permissions, "
            "request details, and UPS documentation."
        ) from None

    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError(
            "UPS could not be reached. Check the internet connection, "
            "firewall, and UPS service status."
        ) from None

    except (ValueError, UnicodeDecodeError):
        raise RuntimeError(
            "UPS returned an unexpected response format."
        ) from None


def get_ups_access_token():
    """
    Request a fresh UPS OAuth client-credentials token.

    Call only after UPS has supplied valid API credentials.
    Tokens are deliberately not cached or written to disk.
    """
    config = get_ups_config()

    if not config["client_id"] or not config["client_secret"]:
        raise RuntimeError(
            "UPS credentials are missing. Set UPS_CLIENT_ID and "
            "UPS_CLIENT_SECRET before testing authentication."
        )

    token_url = config["api_base"] + "/security/v1/oauth/token"

    credentials = (
        config["client_id"] + ":" + config["client_secret"]
    ).encode("utf-8")

    import base64

    authorization = base64.b64encode(credentials).decode("ascii")

    body = urllib.parse.urlencode({
        "grant_type": "client_credentials"
    }).encode("utf-8")

    request = urllib.request.Request(
        token_url,
        data=body,
        headers={
            "Authorization": "Basic " + authorization,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request, timeout=config["timeout"]
        ) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            "UPS OAuth authentication failed with HTTP "
            f"{exc.code}. Verify credentials, environment, and "
            "the UPS application's enabled APIs."
        ) from None

    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError(
            "Could not reach the UPS OAuth service."
        ) from None

    except (ValueError, UnicodeDecodeError):
        raise RuntimeError(
            "UPS OAuth returned an invalid response."
        ) from None

    token = result.get("access_token")

    if not token:
        raise RuntimeError(
            "UPS did not return an access token."
        )

    return token


def test_ups_authentication():
    """
    Test OAuth without creating shipments or buying labels.
    Never return the token itself.
    """
    token = get_ups_access_token()

    return {
        "provider": "UPS",
        "authenticated": bool(token),
        "environment": get_ups_config()["environment"],
        "message": (
            "UPS authentication succeeded. Shipping rates and "
            "production permissions still need separate testing."
        ),
    }


def get_ups_rate_endpoint():
    """
    Return the UPS Rating API endpoint for the selected environment.
    The request body must be built from validated shipment details.
    """
    config = get_ups_config()

    return (
        config["api_base"]
        + "/api/rating/v2403/Rate"
    )


def get_ups_rate_placeholder():
    """
    Deliberately refuse to fabricate a shipping price.
    A real rating request should be added after confirming the UPS
    account, API version, shipping origin, package data, and services.
    """
    return {
        "provider": "UPS",
        "available": False,
        "price": None,
        "currency": get_ups_config()["currency_code"],
        "message": (
            "Live UPS rates are not enabled yet. No shipping amount "
            "has been estimated or fabricated."
        ),
    }


def get_ups_tracking_endpoint(tracking_number):
    """Build a tracking endpoint only for a supplied tracking number."""
    tracking_number = str(tracking_number).strip()

    if not tracking_number:
        raise ValueError("A tracking number is required.")

    if len(tracking_number) > 50:
        raise ValueError("The tracking number is too long.")

    if not all(
        char.isalnum() or char in "-_"
        for char in tracking_number
    ):
        raise ValueError("The tracking number contains invalid characters.")

    config = get_ups_config()

    return (
        config["api_base"]
        + "/api/track/v1/details/"
        + urllib.parse.quote(tracking_number, safe="")
    )
