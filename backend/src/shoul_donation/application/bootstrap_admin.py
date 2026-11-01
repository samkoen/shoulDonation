"""Install the first platform admin. This path has no actor because the database is empty."""

from uuid import uuid4

from shoul_donation.application.password_hasher import PasswordHasher
from shoul_donation.application.ports import UnitOfWork
from shoul_donation.domain.entities import Membership, UserAccount
from shoul_donation.domain.role import Role
from shoul_donation.domain.validation import normalize_email, require_password


def ensure_platform_admin(
    unit_of_work: UnitOfWork,
    password_hasher: PasswordHasher,
    email: str,
    password: str,
) -> None:
    cleaned_email = normalize_email(email)
    require_password(password)
    if unit_of_work.users.get_by_email(cleaned_email) is not None:
        return
    user = UserAccount(
        id=uuid4(),
        email=cleaned_email,
        password_hash=password_hasher.hash(password),
    )
    membership = Membership(
        id=uuid4(),
        user_id=user.id,
        synagogue_id=None,
        role=Role.PLATFORM_ADMIN,
    )
    unit_of_work.users.add(user)
    unit_of_work.memberships.add(membership)
    unit_of_work.commit()
