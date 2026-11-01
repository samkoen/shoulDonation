"""Roles stored on a membership."""

from enum import Enum


class Role(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    LEAD_PROJECTOR = "lead_projector"
    SUB_PROJECTOR = "sub_projector"
