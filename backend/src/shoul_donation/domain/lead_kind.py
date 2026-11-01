"""The two lead pipelines stay separate."""

from enum import Enum


class LeadKind(str, Enum):
    DONOR = "donor"
    SYNAGOGUE_CUSTOMER = "synagogue_customer"
