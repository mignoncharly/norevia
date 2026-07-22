import asyncio

import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from app.config import get_settings

bearer = HTTPBearer(auto_error=False)
_jwks_clients: dict[str, PyJWKClient] = {}


async def current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> str:
    settings = get_settings()
    if settings.env == "development" and settings.allow_development_identity and x_user_id:
        return x_user_id
    if not settings.oidc_issuer or credentials is None:
        raise HTTPException(
            401, detail={"code": "unauthorized", "messageKey": "errors.authenticationRequired"}
        )
    issuer = settings.oidc_issuer.rstrip("/")
    jwks_client = _jwks_clients.setdefault(
        issuer, PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_keys=True, lifespan=300)
    )
    try:
        signing_key = await asyncio.to_thread(
            jwks_client.get_signing_key_from_jwt, credentials.credentials
        )
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=settings.oidc_audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except (PyJWTError, OSError) as error:
        raise HTTPException(
            401, detail={"code": "invalid_token", "messageKey": "errors.invalidToken"}
        ) from error
    return str(claims["sub"])
