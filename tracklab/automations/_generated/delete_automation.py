# Generated by ariadne-codegen
# Source: tools/graphql_codegen/automations/

from __future__ import annotations

from typing import Optional

from tracklab._pydantic import GQLBase

from .fragments import DeleteAutomationResult


class DeleteAutomation(GQLBase):
    result: Optional[DeleteAutomationResult]


DeleteAutomation.model_rebuild()
