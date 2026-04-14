# Scenario Design

## Overview

Each scenario defines a set of parameters that control the demand regime,
supplier behaviour, logistics conditions, and disruption events during
the simulation. Scenarios are selected by name when running the simulation.

All scenarios share the same network topology and module set — only the
parameters vary. This makes comparisons meaningful and reproducible.

## Scenario Definitions

### 1. Peacetime Baseline (`peacetime_baseline`)

**Purpose**: Establish steady-state performance under normal conditions.

| Parameter | Value |
|-----------|-------|
| Demand multiplier | 1.0× throughout |
| Surge trigger week | None (no surge) |
| Supplier disruption probability | 0.02 per week |
| Transit time multiplier | 1.0× |
| Expedite available | Yes |
| Horizon | 52 weeks |

**Expected outcome**: High fill rate (>95%), low backlog, moderate inventory,
low utilisation, minimal expedite cost.

---

### 2. Short Sharp Surge (`short_sharp_surge`)

**Purpose**: Model a sudden, intense but brief conflict-driven demand spike.

| Parameter | Value |
|-----------|-------|
| Demand multiplier (pre-surge) | 1.0× |
| Demand multiplier (surge) | 3.0× |
| Surge trigger week | 12 |
| Surge duration | 12 weeks (weeks 12–24) |
| Demand multiplier (post-surge) | 1.5× (elevated wind-down) |
| Supplier disruption probability | 0.05 during surge |
| Transit time multiplier | 1.0× |
| Horizon | 52 weeks |

**Expected outcome**: Fill rate drops sharply during surge, backlog builds,
then gradually recovers. Expedite costs spike.

---

### 3. Prolonged Attritional Conflict (`prolonged_attritional_conflict`)

**Purpose**: Model sustained elevated demand over an extended period.

| Parameter | Value |
|-----------|-------|
| Demand multiplier (pre-surge) | 1.0× |
| Demand multiplier (surge) | 2.0× |
| Surge trigger week | 8 |
| Surge duration | 44 weeks (weeks 8–52) |
| Supplier disruption probability | 0.05 during surge |
| Transit time multiplier | 1.2× during surge |
| Horizon | 78 weeks |

**Expected outcome**: Persistent backlog growth, inventory depletion,
declining fill rate, high expedite costs, utilisation at ceiling.

---

### 4. Supplier Shock During Surge (`supplier_shock_during_surge`)

**Purpose**: Test resilience when a sole-source supplier fails during peak demand.

| Parameter | Value |
|-----------|-------|
| Demand multiplier (surge) | 2.5× |
| Surge trigger week | 10 |
| Surge duration | 20 weeks |
| Supplier disruption | SubTierSupplierC offline weeks 14–26 |
| Other supplier disruption probability | 0.05 |
| Transit time multiplier | 1.0× |
| Horizon | 52 weeks |

**Expected outcome**: Severe component shortage cascading to finished goods.
Backlog grows steeply. Fill rate collapses. Recovery slow after supplier returns.

---

### 5. Logistics Disruption in Surge (`logistics_disruption_in_surge`)

**Purpose**: Model transport delays compounding a demand surge.

| Parameter | Value |
|-----------|-------|
| Demand multiplier (surge) | 2.0× |
| Surge trigger week | 10 |
| Surge duration | 20 weeks |
| Transit time multiplier | 2.0× during weeks 12–30 |
| Supplier disruption probability | 0.03 |
| Horizon | 52 weeks |

**Expected outcome**: Pipeline inventory grows but arrives late. Fill rate
degrades. Backlog builds from delivery delays, not just capacity.

---

## Scenario File Format

Each scenario is a JSON file in `src/scse/scenarios/`:

```json
{
  "name": "short_sharp_surge",
  "description": "Sudden 3x demand spike for 12 weeks",
  "time_horizon": 52,
  "demand": {
    "baseline_multiplier": 1.0,
    "surge_multiplier": 3.0,
    "surge_trigger_week": 12,
    "surge_duration_weeks": 12,
    "post_surge_multiplier": 1.5
  },
  "suppliers": {
    "disruption_probability": 0.05,
    "forced_disruptions": {}
  },
  "logistics": {
    "transit_time_multiplier": 1.0,
    "transit_disruption_start_week": null,
    "transit_disruption_end_week": null
  }
}
```

## How to Add a New Scenario

1. Create a new JSON file in `src/scse/scenarios/`
2. Set the scenario parameters (demand, supplier, logistics)
3. Run: `python run_defence_sim.py --scenario your_scenario_name`
4. Compare outputs in `output/your_scenario_name/`

## Limitations

- Scenarios are deterministic given a random seed. Stochasticity comes from
  supplier disruption draws and demand noise, not from scenario parameters.
- Scenarios do not currently support multi-item BOM dependencies or
  labour model parameters — these are planned for Phase 2.
- All values are fictional and for simulation purposes only.
