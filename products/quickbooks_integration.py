import base64
import hashlib
import logging
import os
import secrets
from datetime import timedelta
from urllib.parse import urlencode

import requests
from cryptography.fernet import Fernet, InvalidToken

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .quickbooks_models import QuickBooksConnection

logger = logging.getLogger(__name__)

INTUIT_AUTHORIZE_URL = "https://appcenter.intuit.com/connect/oauth2"
INTUIT_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
INTUIT_REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
PAYMENTS_SCOPE = "com.intuit.quickbooks.payment"


def _is_staff(user):
    return user.is_authenticated and user.is_staff


def _credentials():
    return (
        os.environ.get("QUICKBOOKS_CLIENT_ID", "").strip(),
        os.environ.get("QUICKBOOKS_CLIENT_SECRET", "").strip(),
    )


def _redirect_uri(request):
    configured = os.environ.get("QUICKBOOKS_REDIRECT_URI", "").strip()
    return configured or request.build_absolute_uri(
        reverse("quickbooks_callback")
    )


def _environment():
    value = os.environ.get("QUICKBOOKS_ENVIRONMENT", "sandbox").strip().lower()
    return "production" if value == "production" else "sandbox"


def _fernet():
    # Derive a stable encryption key from Django's secret key.
    # Never log or return this key.
    material = (settings.SECRET_KEY + "|TheLabelGroup|QuickBooksOAuth|v1").encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(material).digest())
    return Fernet(key)


def _encrypt(value):
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def _decrypt(value):
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeError):
        raise RuntimeError(
            "Could not decrypt QuickBooks credentials. "
            "Check that Django SECRET_KEY has not changed."
        )


def _save_tokens(connection, token_data, realm_id, username):
    access = token_data.get("access_token")
    refresh = token_data.get("refresh_token")
    if not access or not refresh:
        raise RuntimeError("Intuit did not return both required OAuth tokens.")

    now = timezone.now()
    connection.realm_id = str(realm_id)
    connection.encrypted_access_token = _encrypt(access)
    connection.encrypted_refresh_token = _encrypt(refresh)
    connection.access_token_expires_at = now + timedelta(
        seconds=int(token_data.get("expires_in", 3600))
    )
    refresh_lifetime = token_data.get("x_refresh_token_expires_in")
    connection.refresh_token_expires_at = (
        now + timedelta(seconds=int(refresh_lifetime))
        if refresh_lifetime
        else None
    )
    connection.connected_by = username[:150]
    connection.save()


def get_valid_access_token(connection):
    """Return a valid access token, refreshing it when it is near expiry."""
    if connection.access_token_expires_at > timezone.now() + timedelta(minutes=2):
        return _decrypt(connection.encrypted_access_token)

    client_id, client_secret = _credentials()
    if not client_id or not client_secret:
        raise RuntimeError("QuickBooks OAuth credentials are not configured.")

    refresh_token = _decrypt(connection.encrypted_refresh_token)
    response = requests.post(
        INTUIT_TOKEN_URL,
        auth=(client_id, client_secret),
        headers={"Accept": "application/json"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=25,
    )
    if not response.ok:
        logger.warning("QuickBooks token refresh failed with HTTP %s.", response.status_code)
        raise RuntimeError(
            "QuickBooks authorization needs attention. Please reconnect the account."
        )

    data = response.json()
    _save_tokens(connection, data, connection.realm_id, connection.connected_by)
    return _decrypt(connection.encrypted_access_token)


@login_required
@user_passes_test(_is_staff)
def quickbooks_connection_page(request):
    connection = QuickBooksConnection.objects.order_by("-connected_at").first()
    client_id, client_secret = _credentials()
    return render(
        request,
        "products/quickbooks_connection.html",
        {
            "connection": connection,
            "configured": bool(client_id and client_secret),
            "environment": _environment(),
        },
    )


@login_required
@user_passes_test(_is_staff)
def quickbooks_connect(request):
    client_id, client_secret = _credentials()
    if not client_id or not client_secret:
        messages.error(
            request,
            "QuickBooks is not configured yet. Add the Intuit sandbox credentials "
            "to this server's environment, then try again.",
        )
        return redirect("quickbooks_connection")

    state = secrets.token_urlsafe(32)
    request.session["quickbooks_oauth_state"] = state
    request.session["quickbooks_oauth_started"] = timezone.now().isoformat()

    params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": PAYMENTS_SCOPE,
        "redirect_uri": _redirect_uri(request),
        "state": state,
    }
    return redirect(INTUIT_AUTHORIZE_URL + "?" + urlencode(params))


@login_required
@user_passes_test(_is_staff)
def quickbooks_callback(request):
    provider_error = request.GET.get("error")
    if provider_error:
        messages.error(
            request,
            "QuickBooks authorization was cancelled or declined. No connection was saved.",
        )
        return redirect("quickbooks_connection")

    expected_state = request.session.pop("quickbooks_oauth_state", None)
    received_state = request.GET.get("state", "")
    if not expected_state or not secrets.compare_digest(expected_state, received_state):
        messages.error(request, "QuickBooks authorization could not be verified. Please retry.")
        return redirect("quickbooks_connection")

    code = request.GET.get("code", "").strip()
    realm_id = request.GET.get("realmId", "").strip()
    client_id, client_secret = _credentials()

    if not code or not realm_id or not client_id or not client_secret:
        messages.error(
            request,
            "QuickBooks did not return all required connection details. Please retry.",
        )
        return redirect("quickbooks_connection")

    try:
        response = requests.post(
            INTUIT_TOKEN_URL,
            auth=(client_id, client_secret),
            headers={"Accept": "application/json"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _redirect_uri(request),
            },
            timeout=25,
        )
        if not response.ok:
            logger.warning(
                "QuickBooks authorization exchange failed with HTTP %s.",
                response.status_code,
            )
            messages.error(
                request,
                "QuickBooks could not complete the connection. Check the Intuit app "
                "credentials and registered redirect URI.",
            )
            return redirect("quickbooks_connection")

        token_data = response.json()
        username = getattr(request.user, "get_username", lambda: "")()
        connection = QuickBooksConnection.objects.filter(realm_id=realm_id).first()

        # Keep one company connection for this website. Replace any previously
        # connected company only after Intuit has authorized the new one.
        if connection is None:
            connection = QuickBooksConnection()
        _save_tokens(connection, token_data, realm_id, username)
        QuickBooksConnection.objects.exclude(pk=connection.pk).delete()

        messages.success(
            request,
            "QuickBooks has been connected successfully. Payment processing remains "
            "disabled until its separate checkout integration is completed and tested.",
        )
    except Exception:
        logger.exception("QuickBooks OAuth callback failed.")
        messages.error(
            request,
            "The QuickBooks connection could not be saved. Review the server log "
            "and try again.",
        )

    return redirect("quickbooks_connection")


@login_required
@user_passes_test(_is_staff)
@require_POST
def quickbooks_disconnect(request):
    connection = QuickBooksConnection.objects.order_by("-connected_at").first()
    if connection:
        try:
            client_id, client_secret = _credentials()
            if client_id and client_secret:
                requests.post(
                    INTUIT_REVOKE_URL,
                    auth=(client_id, client_secret),
                    headers={"Accept": "application/json"},
                    data={
                        "token": _decrypt(connection.encrypted_refresh_token),
                    },
                    timeout=15,
                )
        except Exception:
            # Remove locally stored credentials even if remote revocation fails.
            logger.warning("QuickBooks remote token revocation failed.", exc_info=True)

        connection.delete()
        messages.success(request, "The saved QuickBooks connection was removed.")

    return redirect("quickbooks_connection")
