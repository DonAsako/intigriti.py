"""Shared configuration for the API response models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class IntigritiModel(BaseModel):
    """Base class for every model decoded from an API response.

    The API speaks camelCase while these attributes are snake_case; both spellings are
    accepted on input. Instances are frozen because they are snapshots of a response
    rather than local state, and fields absent from this library are ignored so that a
    field added by Intigriti never breaks decoding.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        frozen=True,
        extra='ignore',
    )
