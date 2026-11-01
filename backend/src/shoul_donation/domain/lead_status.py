"""Progress of one lead until the conversation closes."""

from enum import Enum


class LeadStatus(str, Enum):
    NEW = "new"
    IN_MEETING = "in_meeting"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"
