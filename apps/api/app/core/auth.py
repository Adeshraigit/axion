from __future__ import annotations

from dataclasses import dataclass
import json
import time
import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings


@dataclass
class AuthContext:
    user_id: str
    claims: dict
    access_token: str


class SupabaseJWTVerifier:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._jwks_cache: dict | None = None
        self._jwks_cached_at: float = 0.0

    async def _get_jwks(self) -> dict:
        now = time.time()
        if self._jwks_cache and now - self._jwks_cached_at < 3600:
            return self._jwks_cache

        if not self.settings.supabase_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SUPABASE_URL is not configured")

        url = f"{self.settings.supabase_url}/auth/v1/.well-known/jwks.json"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._jwks_cached_at = now
            return self._jwks_cache

    async def verify_token(self, token: str) -> AuthContext:
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header") from exc

        jwks = await self._get_jwks()
        key_data = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                key_data = key
                break

        if not key_data:
            return await self._verify_with_auth_server(token)

        if key_data.get("kty") != "RSA":
            return await self._verify_with_auth_server(token)

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_data))
        issuer = f"{self.settings.supabase_url}/auth/v1"

        decode_kwargs: dict = {
            "algorithms": ["RS256"],
            "issuer": issuer,
        }

        if self.settings.supabase_jwt_audience:
            decode_kwargs["audience"] = self.settings.supabase_jwt_audience

        try:
            claims = jwt.decode(token, public_key, **decode_kwargs)
        except Exception as exc:
            return await self._verify_with_auth_server(token)

        sub = claims.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

        return AuthContext(user_id=sub, claims=claims, access_token=token)

    async def _verify_with_auth_server(self, token: str) -> AuthContext:
        if not self.settings.supabase_url or not self.settings.supabase_anon_key:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Supabase auth config is incomplete")

        url = f"{self.settings.supabase_url}/auth/v1/user"
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": self.settings.supabase_anon_key,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        data = response.json()
        user_id = data.get("id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

        claims = {"sub": user_id, "source": "supabase_auth_server"}
        return AuthContext(user_id=user_id, claims=claims, access_token=token)


bearer_scheme = HTTPBearer(auto_error=True)
verifier = SupabaseJWTVerifier()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> AuthContext:
    return await verifier.verify_token(credentials.credentials)
