# miniSCOT

miniSCOT is a simulation tool that lets users play with the supply chain
architecture and algorithms at any level of fidelity. The system allows users to
snap together their own customer supply chain out of pre-built modules, and
the open-source Python codebase allows easy development of new components and
baselines.

---

## UK Defence Prime Supply Chain Surge Simulation

This repository has been extended with a **fictional UK defence prime contractor
supply chain simulation** focused on wartime surge demand resilience. It models
how a UK-based prime contractor's supply chain performs when demand suddenly
spikes due to mobilisation or geopolitical crisis.

> **Important**: All names, data, scenarios, and outputs are entirely fictional
> and for research/simulation purposes only. Nothing in this code represents
> real classified processes, real companies, or operational military planning.

### What Changed from the Base Repo

The original miniSCOT newsvendor demo models a retail supply chain (single
product, infinite-inventory vendor, Poisson demand). The defence extension:

| Original | Defence Extension |
|----------|-------------------|
| Single consumer product (ISBN) | 5 defence programme items (munitions, radar, comms, etc.) |
| Stationary Poisson demand | Scenario-driven MOD demand with baseline/surge regimes |
| 3-node chain (Manufacturer->Warehouse->Customer) | 5-node multi-tier network (sub-tier->tier-1->factory->MOD) |
| Infinite-inventory vendor | Constrained suppliers with capacity, disruption, lead-time variability |
| P90 service-level buying | Safety-stock policy with expedite and strategic reserve |
| Closest-warehouse fulfillment | Priority-based allocation with production capacity constraints |
| Cash accounting metrics | Fill rate, backlog, inventory, utilisation, expedite cost |
| No scenarios | 5 named scenarios (peacetime through extreme surge) |

### How the Defence Model Works

**Network topology**: A fictional prime contractor (Albion Defence Systems)
near Bristol sources components from two Tier-1 suppliers (UK and allied) and
one sub-tier sole-source supplier. The factory produces finished goods that
ship to an MOD depot.

**Demand**: The MOD generates weekly demand for 5 programme items. In peacetime,
demand follows a baseline rate with noise. When a surge scenario activates,
demand multiplies by 2-3x for the specified duration.

**Suppliers**: Tier-1 suppliers have finite weekly dispatch capacity, variable
lead times, and stochastic disruption probability. The sub-tier supplier is
fragile and can be forced offline by scenario configuration.

**Production**: The factory converts component inventory to finished goods,
subject to a weekly capacity ceiling. When components run short, production
drops.

**Fulfillment**: Customer orders are fulfilled from finished goods by programme
priority (e.g., munitions before spares). Unfulfilled orders accumulate as
backlog.

**Buying policy**: A safety-stock reorder policy monitors inventory position
and orders to maintain coverage. During surge, safety stock targets increase.
When critically low, expedited orders are triggered at premium cost.

### Scenario Definitions

| Scenario | Description |
|----------|-------------|
| `peacetime_baseline` | Normal MOD demand, no disruptions - steady-state baseline |
| `short_sharp_surge` | 3x demand spike for 12 weeks starting week 12 |
| `prolonged_attritional_conflict` | 2x demand sustained for 44 weeks with logistics friction |
| `supplier_shock_during_surge` | 2.5x surge + sole-source supplier offline for 12 weeks |
| `logistics_disruption_in_surge` | 2x surge + doubled transit times for 18 weeks |

### How to Run Experiments

**Install**:
```bash
pip install -e .
```

**Run a scenario**:
```bash
python run_defence_sim.py --scenario peacetime_baseline
python run_defence_sim.py --scenario short_sharp_surge --seed 42 --quiet
```

**List available scenarios**:
```bash
python run_defence_sim.py --list-scenarios
```

**Output** is saved to `output/<scenario_name>/` with:
- `metrics_log.csv` - per-week metrics (fill rate, backlog, inventory, etc.)
- `summary.txt` - headline metrics summary

### Limitations

- **Single BOM level**: Components are generic per item; no multi-level BOM yet.
- **No labour model**: Overtime, shift changes, and ramp-up delay are not modelled.
- **No quality model**: Scrap and rework are not modelled.
- **No alternate suppliers**: Qualification constraints for backup sources not yet implemented.
- **Deterministic production**: Production uses components 1:1 without yield or batch effects.
- **Simplified logistics**: Sea/air/road modes exist as labels but all use the same time-based model.

These are planned for future phases. See `docs/defence-architecture-plan.md` for the roadmap.

### Documentation

- [Gap Analysis](docs/defence-gap-analysis.md) - comparison of original vs defence model
- [Architecture Plan](docs/defence-architecture-plan.md) - phased engineering plan
- [Scenario Design](docs/scenario-design.md) - scenario definitions and parameters

---

## Original miniSCOT Documentation

### Plain-old-python-setup.py

* Clone the git repository

* Build a source distribution:
  - `python setup.py sdist`

* Install:
  - `python setup.py install`

* Switch to develop mode (recommended):
  - `python setup.py develop`

* Start the original command-line application:
  - `miniscot`
