# Defence Prime Supply Chain Simulation — Gap Analysis

## Overview

This document compares the existing miniSCOT supply chain simulation
(designed for a retail / e-commerce newsvendor problem) with the target
UK defence-prime surge scenario. It identifies domain mismatches and
outlines what must change.

## Current Architecture Summary

| Aspect | Current (Newsvendor Demo) |
|--------|--------------------------|
| **Products** | Single ASIN (ISBN) — consumer good |
| **Demand** | Stochastic Poisson, stationary, i.i.d. |
| **Network** | 3 nodes: Manufacturer → Warehouse → Customer |
| **Suppliers** | Single vendor, infinite inventory, deterministic lead time |
| **Buying Policy** | Order-up-to, service-level (P90) targeting |
| **Fulfillment** | Closest-warehouse, single allocation |
| **Metrics** | Cash accounting (revenue, cost, holding cost) |
| **Scenarios** | None — single hard-coded profile |
| **Time** | Daily steps, 100-day horizon |

## Target: UK Defence Prime Surge Model

| Aspect | Target |
|--------|--------|
| **Products** | Multiple programme items (munitions, radar modules, comms assemblies, etc.) |
| **Demand** | MOD/DE&S demand signals — baseline peacetime plus wartime surge |
| **Network** | Multi-tier: Sub-tier suppliers → Tier-1 suppliers → Prime factory → MOD depots |
| **Suppliers** | Constrained, sole-source, variable lead times, disruption-prone |
| **Buying Policy** | Safety-stock + strategic reserve, expedite capability, priority allocation |
| **Fulfillment** | Programme-priority-based allocation under constrained output |
| **Metrics** | Fill rate, backlog, OTIF, production utilisation, expedite cost, inventory position |
| **Scenarios** | Peacetime, short surge, prolonged conflict, supplier shock, logistics disruption |
| **Time** | Weekly steps, 52–104 week horizon |

## Key Domain Mismatches

### 1. Demand Model
- **Current**: Stationary Poisson — no concept of surge, regime change, or programme priority.
- **Target**: Baseline demand that shifts to a surge multiplier on a trigger date. Multiple demand streams (new-build vs MRO/sustainment). Demand can be programme-specific.

### 2. Supplier Model
- **Current**: Single infinite-inventory vendor with deterministic transit time.
- **Target**: Multiple suppliers with finite capacity, stochastic lead times, disruption probability, and ramp-up constraints. Some components are sole-source.

### 3. Network Topology
- **Current**: Simple 3-node chain with uniform transit times.
- **Target**: Multi-tier directed graph with UK prime factory, multiple supplier tiers, and MOD delivery points. Edges have variable transit times, potential disruption, and mode-specific characteristics.

### 4. Inventory Policy
- **Current**: Network-level order-up-to with P90 target.
- **Target**: Per-item safety stock + strategic buffer. Expediting as a policy lever. Allocation priority across programmes.

### 5. Production Constraints
- **Current**: None — warehouse is just a pass-through inventory node.
- **Target**: Prime factory has finite weekly throughput (capacity pool). Production consumes components from inventory. Ramp-up delay when adding shifts.

### 6. Metrics
- **Current**: Cash accounting only (revenue, cost, holding).
- **Target**: Operational metrics — fill rate, backlog, OTIF, utilisation, expedite cost, inventory days-of-supply.

### 7. Scenario System
- **Current**: None — single hard-coded profile.
- **Target**: Named, configurable scenarios that modify demand, disruption, and logistics parameters.

## Components to Reuse vs Replace

### Reuse (with adaptation)
- **Controller/Simulation Loop** (`miniscot.py`): Core step logic, action processing, shipment transfer — all reusable. Just needs new modules plugged in.
- **Module API** (`api/module.py`): Agent/Env/Service abstractions are sound.
- **Network Utilities** (`api/network.py`): Inventory helpers, shipment tracking — reusable.
- **Profile System** (`profiles/profile.py`): JSON profile loading and class instantiation — reusable as-is.
- **Service Registry**: Cross-module service sharing — reusable.
- **Test Harness**: pytest structure — reusable, add new tests.

### Replace (new defence modules)
- Selection module → defence programme items
- Topology module → multi-tier defence network
- Customer module → MOD demand with surge
- Vendor module → constrained supplier with disruption
- Buying module → defence inventory policy with expediting
- Fulfillment module → priority-based allocation with production constraints
- Metrics module → defence operational metrics

## Risks and Unknowns

1. The existing controller assumes a simple action model (purchase_order, inbound/outbound_shipment). Adding production constraints may require extending the action vocabulary.
2. The metrics module is tightly coupled to cash accounting. A new metrics module is needed.
3. The existing CLI (`cmd2`-based) has a pre-existing compatibility issue with cmd2 v2+.
4. No existing scenario/configuration system beyond profiles — needs to be built.

## Recommendation

Create new defence modules alongside the existing newsvendor modules. Use the existing profile system to switch between demo and defence configurations. This preserves backward compatibility and allows incremental development.
