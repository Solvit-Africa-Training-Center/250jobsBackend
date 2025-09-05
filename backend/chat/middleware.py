from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication

class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner
        self.jwt_auth = JWTAuthentication()
    
    async def __call__(self, scope, receive, send):
        query_string  = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token", [])
        user = AnonymousUser()

        if token_list:
            raw_token = token_list[0]
            try:
                validated = self.jwt_auth.get_validated_token(raw_token)
                user = self.jwt_auth.get_user(validated)
            except Exception:
                user = AnonymousUser()
        
        scope["user"] = user
        return await self.inner(scope, receive, send)