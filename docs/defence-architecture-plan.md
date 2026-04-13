# Defence Prime Supply Chain Simulation — Architecture Plan

## Phased Engineering Plan

### Phase 1 — Minimal Runnable Defence Simulation (Milestone 1)

**Goal**: A thin vertical slice that runs from the CLI with at least two scenarios
and produces meaningful output differences (backlog, fill rate, inventory).

#### Deliverables
1. **Defence Selection Module** — defines programme items (e.g. precision munitions, radar modules)
2. **Defence Topology Module** — multi-node network: sub-tier → tier-1 → prime factory → MOD depot
3. **Defence Customer Module** — MOD demand with baseline and surge regimes
4. **Defence Vendor Module** — constrained suppliers with variable lead times and disruption
5. **Defence Buying Module** — safety-stock policy with expedite lever
6. **Defence Fulfillment Module** — priority allocation with production capacity constraint
7. **Defence Metrics Module** — fill rate, backlog, inventory, utilisation, expedite cost
8. **Defence Profile** — JSON config wiring all modules together
9. **Scenario System** — named scenario configs (peacetime, surge, etc.)
10. **CLI Runner** — `python run_defence_sim.py --scenario peacetime_baseline`
11. **Tests** — unit tests for defence modules
12. **Documentation** — README update, scenario descriptions

### Phase 2 — Richer Model (Future)

- Multi-item BOM dependencies (component → assembly)
- Qualification constraints for alternate suppliers
- Labour model (overtime, second shift, ramp delay)
- Quality model (scrap rate, rework)
- Export control / regulated component constraints
- MRO / sustainment demand stream
- Disruption event injection (port delay, customs friction)
- Monte Carlo scenario runs

### Phase 3 — Analysis and Visualisation (Future)

- Scenario comparison dashboards
- Sensitivity analysis
- Policy optimisation hooks
- Integration with Jupyter notebooks

## Target Domain Model (Phase 1)

```
┌─────────────────────────────────────────────────────┐
│                    MOD / DE&S                        │
│              (Customer / demand signal)              │
└─────────────────────┬───────────────────────────────┘
                      │  delivery
┌─────────────────────▼───────────────────────────────┐
│              Albion Defence Systems                   │
│          (Prime Factory — capacity-constrained)      │
│   Produces: Munitions, Radar Modules, Comms, etc.   │
└──────┬──────────────┬───────────────────────────────┘
       │              │  component supply
┌──────▼──────┐ ┌─────▼───────┐
│ Tier-1      │ │ Tier-1      │
│ Supplier A  │ │ Supplier B  │
│ (UK-based,  │ │ (Allied,    │
│ reliable)   │ │ longer lead)│
└──────┬──────┘ └─────┬───────┘
       │              │
┌──────▼──────────────▼───────┐
│      Sub-tier Supplier C     │
│  (Sole-source, fragile,     │
│   long lead, disruption-    │
│   prone)                     │
└──────────────────────────────┘
```

## Module Design

### Selection Module
- Returns list of programme item IDs (e.g. `PGM-001`, `RADAR-002`)
- Maps to fictional defence product families

### Topology Module
- Creates NetworkX DiGraph with 5+ nodes
- Nodes: SubTierSupplierC, Tier1SupplierA, Tier1SupplierB, AlbionFactory, MODDepot
- Edges with mode-specific transit times
- Factory node has `capacity` attribute

### Customer Module
- Generates weekly demand per programme item
- Baseline rate configurable per item
- Surge multiplier activated at configurable trigger week
- Demand regime determined by scenario

### Vendor Module
- Processes purchase orders for each supplier
- Per-supplier attributes: base lead time, variability, capacity limit, disruption probability
- Disrupted suppliers have extended lead times or zero output
- Supports expedited orders at higher cost

### Buying Module
- Per-item safety stock target (weeks of cover)
- Reorder when inventory position drops below safety stock + pipeline
- Expedite flag when critically low
- Strategic reserve buffer for surge scenarios

### Fulfillment Module
- Production step: converts component inventory to finished goods (capacity-limited)
- Allocation: fulfils customer orders from finished goods inventory
- Priority: earlier orders first, with programme priority tiebreaker

### Metrics Module
- Tracks per-timestep: demand, fulfilled, backlog, inventory, production, expedite
- Computes: fill rate, backlog trend, utilisation, OTIF proxy, expedite cost
- Writes CSV and summary to output directory

## Scenario Configuration

Scenarios are JSON files in `src/scse/scenarios/` that override demand, disruption,
and logistics parameters without changing the module code.

| Scenario | Description |
|----------|-------------|
| `peacetime_baseline` | Normal MOD demand, no disruptions |
| `short_sharp_surge` | 3× demand spike for 12 weeks |
| `prolonged_attritional_conflict` | 2× demand sustained for 40+ weeks |
| `supplier_shock_during_surge` | Surge + sole-source supplier failure |
| `logistics_disruption_in_surge` | Surge + doubled transit times |
