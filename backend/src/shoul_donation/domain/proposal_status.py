"""Lifecycle of a simulated financing proposal."""

from enum import Enum


class ProposalStatus(str, Enum):
    AWAITING_RATE_TABLE = "awaiting_rate_table"
