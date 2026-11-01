"""Authenticated caller. The API builds this from a token, never from the client body."""

from dataclasses import dataclass
from uuid import UUID

from shoul_donation.domain.role import Role


@dataclass(frozen=True, slots=True)
class Actor:
    user_id: UUID
    role: Role
    synagogue_id: UUID | None
