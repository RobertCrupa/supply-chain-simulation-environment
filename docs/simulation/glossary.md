# Glossary

This glossary defines the main domain and engine terms used by the simulation.

## Domain Terms

- **Scenario**: named configuration that controls demand, disruption,
  logistics, and horizon for a run.
- **Peacetime baseline**: scenario with baseline demand and low disruption,
  used as reference case.
- **Surge**: period where demand multiplier rises above baseline.
- **Post-surge**: period after surge window with recovery or elevated residual
  demand depending on scenario.
- **Programme item**: defence product family simulated as an item ID (e.g.
  `PGM-001`).
- **Programme priority**: rank used by fulfillment; lower number means higher
  service priority.
- **Backlog**: unfulfilled customer order quantity carried across weeks.
- **Fill rate**: cumulative fulfilled units divided by cumulative demanded units.
- **Safety stock**: target inventory coverage used to trigger replenishment.
- **Inventory position**: on-hand inventory plus in-transit inventory.
- **Expedite**: replenishment mode that shortens lead time with added cost.
- **Supplier disruption**: a supplier week where orders cannot be fulfilled due
  to forced or stochastic outage.
- **Lead time**: elapsed timesteps between shipment dispatch and arrival.
- **Transit time multiplier**: scenario factor that scales lead times during
  logistics disruption windows.
- **Utilization**: production output divided by weekly factory capacity.

## Engine Terms

- **miniSCOT**: the simulation framework used by this submodule.
- **Profile**: JSON module wiring that defines which modules and metrics run.
- **Module**: pluggable unit implementing an interface.
- **Env module**: module type that contributes static context and initial state.
- **Agent module**: module type that reads state and emits actions each step.
- **Metrics module**: module that computes reward and writes output artifacts.
- **Service module**: optional shared service loaded through service registry.
- **Context**: run-static values assembled from Env modules.
- **State**: run-dynamic mutable structure advanced each timestep.
- **Action**: event emitted by agents and executed by controller.
- **Order action**: action persisted as pending demand/supply intent
  (`customer_order`, `purchase_order`).
- **Shipment action**: action persisted on network edges with arrival countdown
  (`inbound_shipment`, `outbound_shipment`).
- **Clock**: integer timestep counter.
- **Time horizon**: number of timesteps to execute.
- **Run parameters**: configuration dict passed to all modules at
  instantiation.

## Legacy Compatibility Terms

- **ASIN**: legacy item identifier name from original newsvendor model. In
  defence mode it refers to programme item IDs.
- **asin_list**: context key containing active item IDs for the run.
- **Warehouse node type**: framework label used for inventory-holding nodes;
  `AlbionFactory` uses this node type.
