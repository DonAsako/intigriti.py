"""Typed models for every payload the Intigriti researcher API returns."""

from __future__ import annotations

from intigriti.models._base import IntigritiModel
from intigriti.models.activity import Activity, ProgramActivity
from intigriti.models.common import Attachment, Enumeration, Money, Page, Version, VersionWithAttachments
from intigriti.models.domain import Domain, Skill
from intigriti.models.payout import Payout
from intigriti.models.program import (
    Program,
    ProgramDetail,
    ProgramDomains,
    ProgramRulesOfEngagement,
    ProgramWebLinks,
)
from intigriti.models.rules_of_engagement import RulesOfEngagement, TestingRequirements

__all__ = [
    'Activity',
    'Attachment',
    'Domain',
    'Enumeration',
    'IntigritiModel',
    'Money',
    'Page',
    'Payout',
    'Program',
    'ProgramActivity',
    'ProgramDetail',
    'ProgramDomains',
    'ProgramRulesOfEngagement',
    'ProgramWebLinks',
    'RulesOfEngagement',
    'Skill',
    'TestingRequirements',
    'Version',
    'VersionWithAttachments',
]
