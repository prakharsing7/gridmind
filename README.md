# gridmind

[![Tests](https://github.com/prakharsing7/gridmind/actions/workflows/ci.yml/badge.svg)](https://github.com/prakharsing7/gridmind/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()

Optimise EV charging schedules using convex optimisation and output
OCPP-native `SetChargingProfile` messages ready to send to real chargers.

## Why this exists

OCPP Python libraries handle protocol parsing but have no optimisation.
Energy optimisation tools have no OCPP awareness. gridmind fills that gap —
it is developed as part of research investigating the gap between OCPP smart
charging specifications and real-world grid-responsive charging behaviour.

## What it does

```text
EV sessions + grid constraints + price signal
                    ↓
         CVXPY LP optimiser
       (minimise cost subject to
        SoC + power + feeder limits)
                    ↓
  OCPP 1.6 SetChargingProfile.req JSON
    (ready to send to real chargers)
```

## Installation

```bash
pip install gridmind
# With visualisation support:
pip install "gridmind[viz]"
```

## Quickstart

```python
from datetime import datetime, timezone
from gridmind import SingleEVOptimizer, EVSession, build_set_charging_profile_request, to_json

session = EVSession(
    session_id="s001",
    charger_id="charger-001",
    arrival_time=datetime(2026, 6, 1, 18, 0, tzinfo=timezone.utc),
    departure_time=datetime(2026, 6, 2, 8, 0, tzinfo=timezone.utc),
    initial_soc=30.0,
    target_soc=80.0,
    battery_capacity_kwh=60.0,
    max_charge_rate_w=7360.0,
)

optimizer = SingleEVOptimizer(interval_minutes=15)
schedule = optimizer.optimize(session)

ocpp_req = build_set_charging_profile_request(schedule)
print(to_json(ocpp_req))
```

## CLI Usage

```bash
# Single EV with TOU pricing
gridmind run --config examples/configs/single_ev.json --output results/ --plot

# EV fleet on shared feeder
gridmind run --config examples/configs/fleet_10ev.json --output results/

# Compare optimised vs uncontrolled charging
gridmind compare --config examples/configs/single_ev.json

# Generate a template config file
gridmind generate-config --type single-ev --output my_session.json

# Validate a config without running
gridmind validate --config my_session.json
```

## Supported Scenarios

| Use Case | Description |
|----------|-------------|
| UC-1 | Single EV, price-optimised (TOU or flat-rate) |
| UC-2 | EV fleet with shared feeder capacity limit |
| UC-3 | Demand response — grid-requested load reduction |
| UC-4 | Simulation with synthetic sessions and metrics |
| UC-5 | Strategy comparison: optimised vs uncontrolled |

## Output Format

The output is a valid OCPP 1.6 `SetChargingProfile.req` payload:

```json
{
  "connectorId": 1,
  "csChargingProfiles": {
    "chargingProfileId": 1,
    "stackLevel": 0,
    "chargingProfilePurpose": "TxDefaultProfile",
    "chargingProfileKind": "Absolute",
    "validFrom": "2026-06-01T18:00:00Z",
    "validTo": "2026-06-02T08:00:00Z",
    "chargingSchedule": {
      "duration": 50400,
      "startSchedule": "2026-06-01T18:00:00Z",
      "chargingRateUnit": "W",
      "chargingSchedulePeriod": [
        {"startPeriod": 0, "limit": 0.0},
        {"startPeriod": 18000, "limit": 7360.0}
      ]
    }
  }
}
```

`startPeriod` is **seconds from `startSchedule`** — as required by the OCPP 1.6 specification (Section 7.14).

## Project Structure

```
gridmind/
├── models/          # Pydantic data models (session, site, schedule, OCPP types)
├── optimizer/       # LP optimisers (single EV, fleet, demand response, baselines)
├── ocpp/            # OCPP 1.6 and 2.0.1 builders and validators
├── inputs/          # JSON/CSV config loaders and price signal helpers
├── outputs/         # Metrics, JSON writer, CSV writer
├── viz/             # Matplotlib visualisation modules
└── cli/             # Click CLI entry point
```

## Development

```bash
git clone https://github.com/prakharsing7/gridmind
cd gridmind
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"
pre-commit install
pytest
```

## Research Context

This tool provides the theoretical optimal schedule that the OCPP protocol
should be able to deliver, enabling comparison with real-world measured
charger compliance.

## Citation

```bibtex
@software{singh2026gridmind,
  author = {Singh, Prakhar},
  title  = {gridmind: OCPP-native EV charging schedule optimiser},
  year   = {2026},
  url    = {https://github.com/prakharsing7/gridmind}
}
```

## License

MIT
