"""Typed failures raised by the domain and the application services."""


class DomainError(Exception):
    """Base error for an expected business failure."""


class AuthenticationError(DomainError):
    """The caller could not be authenticated."""


class ForbiddenError(DomainError):
    """The caller is authenticated but not allowed to perform the action."""


class NotFoundError(DomainError):
    """The requested record does not exist in the caller's scope."""


class ConflictError(DomainError):
    """The requested record collides with an existing one."""


class ValidationError(DomainError):
    """The input does not satisfy a business rule."""
