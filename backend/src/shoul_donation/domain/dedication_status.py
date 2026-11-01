"""Lifecycle of one architectural dedication."""

from enum import Enum


class DedicationStatus(str, Enum):
    OPEN = "open"
    FUNDRAISING = "fundraising"
    REALIZED = "realized"
