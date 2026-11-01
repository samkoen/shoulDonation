"""Synagogue and user registration."""

from uuid import UUID, uuid4

from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.actor import Actor
from shoul_donation.domain.authorization import assert_can_register_user, assert_platform_admin
from shoul_donation.domain.entities import Membership, Synagogue, UserAccount
from shoul_donation.domain.errors import AuthenticationError, ConflictError, NotFoundError
from shoul_donation.domain.role import Role
from shoul_donation.domain.validation import normalize_email, require_name, require_password


class IdentityService:
    def __init__(self, unit_of_work: UnitOfWork, password_hasher: PasswordHasher) -> None:
        self._unit_of_work = unit_of_work
        self._password_hasher = password_hasher

    def create_synagogue(self, actor: Actor, name: str) -> Synagogue:
        assert_platform_admin(actor)
        cleaned = require_name(name, "Synagogue name")
        self._reject_duplicate_synagogue(cleaned)
        synagogue = Synagogue(id=uuid4(), name=cleaned)
        self._unit_of_work.synagogues.add(synagogue)
        self._unit_of_work.commit()
        return synagogue

    def list_synagogues(self, actor: Actor) -> list[Synagogue]:
        assert_platform_admin(actor)
        return self._unit_of_work.synagogues.list_all()

    def register_user(
        self,
        actor: Actor,
        email: str,
        password: str,
        role: Role,
        synagogue_id: UUID | None,
    ) -> UserAccount:
        assert_can_register_user(actor, role, synagogue_id)
        self._require_synagogue(synagogue_id)
        cleaned_email = normalize_email(email)
        require_password(password)
        self._reject_duplicate_email(cleaned_email)
        return self._store_user(cleaned_email, password, role, synagogue_id)

    def authenticate(self, email: str, password: str) -> Actor:
        user = self._unit_of_work.users.get_by_email(normalize_email(email))
        if user is None or not self._password_hasher.verify(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        membership = self._unit_of_work.memberships.get_for_user(user.id)
        if membership is None:
            raise AuthenticationError("Invalid email or password")
        return Actor(user_id=user.id, role=membership.role, synagogue_id=membership.synagogue_id)

    def _store_user(
        self,
        email: str,
        password: str,
        role: Role,
        synagogue_id: UUID | None,
    ) -> UserAccount:
        user = UserAccount(id=uuid4(), email=email, password_hash=self._password_hasher.hash(password))
        membership = Membership(id=uuid4(), user_id=user.id, synagogue_id=synagogue_id, role=role)
        self._unit_of_work.users.add(user)
        self._unit_of_work.memberships.add(membership)
        self._unit_of_work.commit()
        return user

    def _require_synagogue(self, synagogue_id: UUID | None) -> None:
        if synagogue_id is None:
            return
        if self._unit_of_work.synagogues.get(synagogue_id) is None:
            raise NotFoundError("Synagogue was not found")

    def _reject_duplicate_synagogue(self, name: str) -> None:
        if self._unit_of_work.synagogues.get_by_name(name) is not None:
            raise ConflictError("A synagogue with this name already exists")

    def _reject_duplicate_email(self, email: str) -> None:
        if self._unit_of_work.users.get_by_email(email) is not None:
            raise ConflictError("A user with this email already exists")
