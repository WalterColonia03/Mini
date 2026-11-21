from django.contrib.auth import SESSION_KEY, logout
from django.db import transaction
from django.urls import reverse

from .audit import bind_request_id, normalize_request_id, reset_request_id, safe_record_rejection_event


class LoginTransactionMiddleware:
    """Keep the account lock until SessionMiddleware persists a login response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method != "POST" or request.path != reverse("login"):
            return self.get_response(request)
        with transaction.atomic():
            response = self.get_response(request)
            if response.status_code >= 500:
                transaction.set_rollback(True)
            return response


class RequestIdMiddleware:
    """Attach a validated correlation request_id to each HTTP request and response."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        req_id = normalize_request_id(request.META.get("HTTP_X_REQUEST_ID"))
        request.request_id = req_id
        token = bind_request_id(req_id)
        try:
            response = self.get_response(request)
        finally:
            reset_request_id(token)
        response["X-Request-ID"] = req_id
        return response


class RevokeRejectedSessionMiddleware:
    """Discard identity sessions the authentication backend no longer accepts.

    ModelBackend returns AnonymousUser for inactive accounts, so checking
    user.is_active only after is_authenticated misses surviving sessions.
    Anonymous browsing without identity context remains untouched.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if SESSION_KEY in request.session and (
            not request.user.is_authenticated or not request.user.is_active
        ):
            actor = request.user if request.user.is_authenticated else None
            actor_id = request.session.get(SESSION_KEY, "")
            logout(request)
            safe_record_rejection_event(
                action="SESSION_REVOKED_INACTIVE",
                target_type="Session",
                target_id=str(actor_id),
                actor=actor,
                request_id=getattr(request, "request_id", None),
                metadata={"path": request.path, "reason": "inactive_or_unaccepted_session"},
                persist_db=False,
            )
        return self.get_response(request)
