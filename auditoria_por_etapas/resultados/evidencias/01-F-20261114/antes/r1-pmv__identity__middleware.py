from django.contrib.auth import SESSION_KEY, logout


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
            logout(request)
        return self.get_response(request)
