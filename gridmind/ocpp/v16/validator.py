"""
Validate OCPP 1.6 SetChargingProfile.req against the JSON schema.
"""

from __future__ import annotations

from datetime import datetime
import importlib.resources
import json

import jsonschema

from ...models.ocpp_types import OCPP16SetChargingProfileRequest


def _load_schema() -> dict:
    schema_path = importlib.resources.files("gridmind.ocpp.v16.schemas").joinpath(
        "SetChargingProfile.json"
    )
    return json.loads(schema_path.read_text())


def _serialise(obj: object) -> str:
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    raise TypeError(f"Cannot serialise {type(obj)}")


def validate_set_charging_profile_request(
    request: OCPP16SetChargingProfileRequest,
) -> list[str]:
    """
    Validate against the OCPP 1.6 JSON schema.

    Returns:
        List of validation error strings. Empty list = valid.
    """
    schema = _load_schema()
    data = json.loads(
        json.dumps(request.model_dump(exclude_none=True), default=_serialise)
    )
    validator = jsonschema.Draft7Validator(schema)
    return [e.message for e in validator.iter_errors(data)]
