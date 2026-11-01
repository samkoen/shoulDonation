"""Signed tokens that carry the actor. The client cannot choose the role."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from shoul_donation.domain.actor import Actor
from shoul_donation.domain.errors import AuthenticationError
from shoul_donation.domain.role import Role


class TokenIssuer:
    def __init__(self, secret: str, ttl_minutes: int) -> None:
        self._secret = secret
        self._ttl_minutes = ttl_minutes

    def issue(self, actor: Actor) -> str:
        payload = {
            "sub": str(actor.user_id),
            "role": actor.role.value,
            "synagogue_id": None if actor.synagogue_id is None else str(actor.synagogue_id),
            "exp": datetime.now(UTC) + timedelta(minutes=self._ttl_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def read(self, token: str) -> Actor:
        payload = self._decode(token)
        synagogue_id = payload.get("synagogue_id")
        return Actor(
            user_id=UUID(str(payload["sub"])),
            role=Role(str(payload["role"])),
            synagogue_id=None if synagogue_id is None else UUID(str(synagogue_id)),
        )

    def _decode(self, token: str) -> dict[str, object]:
        try:
            decoded = jwt.decode(token, self._secret, algorithms=["HS256"])
        except jwt.PyJWTError as error:
            raise AuthenticationError("Invalid token") from error
        if not isinstance(decoded, dict):
            raise AuthenticationError("Invalid token")
        return decoded
