"""Load optimiser configuration from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models.session import EVSession
from ..models.site import PriceSignal, SiteConfig


def load_config(path: Path) -> dict[str, Any]:
    """
    Load and parse an optimiser config JSON file.

    Returns a dict with:
      - 'type': 'single_ev' or 'fleet'
      For single_ev: 'session' (EVSession), 'price_signal' (PriceSignal | None), 'flat_rate' (float)
      For fleet: 'site_config' (SiteConfig), 'sessions' (list[EVSession])

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the config type is unknown.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = json.loads(path.read_text())
    config_type = raw.get("type")

    if config_type == "single_ev":
        session = EVSession.model_validate(raw["session"])
        price_signal = None
        if raw.get("price_signal"):
            price_signal = PriceSignal.model_validate(raw["price_signal"])
        return {
            "type": "single_ev",
            "session": session,
            "price_signal": price_signal,
            "flat_rate": raw.get("flat_rate", 0.25),
        }

    elif config_type == "fleet":
        site_config = SiteConfig.model_validate(raw["site_config"])
        sessions = [EVSession.model_validate(s) for s in raw["sessions"]]
        return {
            "type": "fleet",
            "site_config": site_config,
            "sessions": sessions,
        }

    else:
        raise ValueError(
            f"Unknown config type: '{config_type}'. Expected 'single_ev' or 'fleet'."
        )
