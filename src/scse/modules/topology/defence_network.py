"""
Defence supply chain network topology.

Creates a multi-tier supply chain network for a fictional UK defence prime
contractor (Albion Defence Systems). The network includes:

- Sub-tier supplier (sole-source, fragile)
- Two Tier-1 suppliers (UK-based and allied)
- Prime contractor factory (capacity-constrained)
- MOD depot (customer delivery point)

All names, locations, and parameters are fictional.
"""

import networkx as nx
from scse.api.module import Env


class DefenceNetwork(Env):
    """Multi-tier UK defence supply chain network.

    Network structure:
        SubTierSupplierC → Tier1SupplierA → AlbionFactory → MODDepot
        SubTierSupplierC → Tier1SupplierB → AlbionFactory
    """

    # Default parameters — can be overridden by scenario
    _DEFAULT_INITIAL_COMPONENT_INVENTORY = 100
    _DEFAULT_INITIAL_FINISHED_INVENTORY = 40

    # Weekly production capacity at the prime factory (units across all items)
    _DEFAULT_FACTORY_CAPACITY = 100

    _DEFAULT_FACTORY_NODE_ID = "AlbionFactory"
    _DEFAULT_CUSTOMER_NODE_ID = "MODDepot"

    def __init__(self, run_parameters):
        self._simulation_seed = run_parameters["simulation_seed"]
        self._initial_component_inv = self._DEFAULT_INITIAL_COMPONENT_INVENTORY
        self._initial_finished_inv = self._DEFAULT_INITIAL_FINISHED_INVENTORY
        self._factory_capacity = self._DEFAULT_FACTORY_CAPACITY
        self._runtime_context = run_parameters.get("runtime_context", {}) or {}
        self._factory_node_id = self._runtime_context.get(
            "factory_node_id", self._DEFAULT_FACTORY_NODE_ID
        )
        self._factory_label = self._runtime_context.get(
            "factory_label", self._factory_node_id
        )
        self._customer_node_id = self._runtime_context.get(
            "customer_node_id", self._DEFAULT_CUSTOMER_NODE_ID
        )
        self._customer_label = self._runtime_context.get(
            "customer_label", self._customer_node_id
        )
        self._runtime_suppliers = self._runtime_context.get("supplier_nodes", [])

    def get_name(self):
        return "network"

    def _has_runtime_suppliers(self):
        return isinstance(self._runtime_suppliers, list) and any(
            isinstance(s, dict) and s.get("id") for s in self._runtime_suppliers
        )

    @staticmethod
    def _to_location(value, fallback=(0.0, 0.0)):
        if isinstance(value, (tuple, list)) and len(value) == 2:
            try:
                return (float(value[0]), float(value[1]))
            except (TypeError, ValueError):
                return fallback
        return fallback

    def get_initial_state(self, context):
        """Build the defence supply chain network graph."""
        G = nx.DiGraph()
        asin_list = context.get("asin_list", [])

        if self._has_runtime_suppliers():
            supplier_ids = []

            for supplier in self._runtime_suppliers:
                if not isinstance(supplier, dict):
                    continue

                supplier_id = supplier.get("id")
                if not supplier_id:
                    continue

                supplier_ids.append(supplier_id)
                G.add_node(
                    supplier_id,
                    node_type="vendor",
                    label=supplier.get("label", supplier_id),
                    location=self._to_location(
                        supplier.get("location"), fallback=(54.0, -2.0)
                    ),
                    supplier_type=supplier.get("supplier_type", "tier_1"),
                    base_lead_time=max(1, int(supplier.get("base_lead_time", 3))),
                    lead_time_variability=max(
                        0, int(supplier.get("lead_time_variability", 1))
                    ),
                    weekly_capacity=max(1, int(supplier.get("weekly_capacity", 60))),
                    disruption_profile=supplier.get("disruption_profile", "moderate"),
                    country=supplier.get("country", "Unknown"),
                )

            factory_capacity = max(
                self._factory_capacity,
                sum(
                    max(1, int(s.get("weekly_capacity", 60)))
                    for s in self._runtime_suppliers
                    if isinstance(s, dict)
                )
                // 3,
            )

            G.add_node(
                self._factory_node_id,
                node_type="warehouse",
                label=self._factory_label,
                location=(51.45, -2.59),
                facility_type="prime_factory",
                weekly_capacity=factory_capacity,
                inventory={asin: self._initial_finished_inv for asin in asin_list},
                component_inventory={
                    asin: self._initial_component_inv for asin in asin_list
                },
                production_this_week=0,
                backlog={asin: 0 for asin in asin_list},
            )

            G.add_node(
                self._customer_node_id,
                node_type="customer",
                label=self._customer_label,
                location=(51.90, -1.15),
                delivered=0,
                delivered_by_item={asin: 0 for asin in asin_list},
            )

            for supplier in self._runtime_suppliers:
                if not isinstance(supplier, dict) or not supplier.get("id"):
                    continue
                supplier_id = supplier["id"]
                G.add_edge(
                    supplier_id,
                    self._factory_node_id,
                    transit_time=max(1, int(supplier.get("transit_time", 2))),
                    transport_mode=supplier.get("transport_mode", "road"),
                    shipments=[],
                )

            G.add_edge(
                self._factory_node_id,
                self._customer_node_id,
                transit_time=1,
                transport_mode="road_secure",
                shipments=[],
            )

            return G

        # --- Nodes ---

        # Sub-tier supplier: sole-source for critical raw materials / energetics
        # Fictional location: industrial site near Bridgwater, Somerset
        G.add_node(
            "SubTierSupplierC",
            node_type="vendor",
            label="Sub-Tier Supplier C",
            location=(51.13, -3.00),
            supplier_type="sub_tier",
            base_lead_time=6,
            lead_time_variability=3,
            weekly_capacity=80,
            disruption_profile="fragile",
        )

        # Tier-1 Supplier A: UK-based, reliable, moderate lead time
        # Fictional location: industrial site near Barrow-in-Furness, Cumbria
        G.add_node(
            "Tier1SupplierA",
            node_type="vendor",
            label="Tier-1 Supplier A",
            location=(54.11, -3.23),
            supplier_type="tier_1",
            base_lead_time=3,
            lead_time_variability=1,
            weekly_capacity=80,
            disruption_profile="reliable",
        )

        # Tier-1 Supplier B: Allied (European), longer lead time
        # Fictional location: allied supplier in northern France
        G.add_node(
            "Tier1SupplierB",
            node_type="vendor",
            label="Tier-1 Supplier B",
            location=(49.44, 1.09),
            supplier_type="tier_1",
            base_lead_time=5,
            lead_time_variability=2,
            weekly_capacity=60,
            disruption_profile="moderate",
        )

        # Prime contractor factory: Albion Defence Systems
        # Fictional location: industrial complex near Bristol
        G.add_node(
            "AlbionFactory",
            node_type="warehouse",
            label="Albion Factory",
            location=(51.45, -2.59),
            facility_type="prime_factory",
            weekly_capacity=self._factory_capacity,
            inventory={asin: self._initial_finished_inv for asin in asin_list},
            component_inventory={
                asin: self._initial_component_inv for asin in asin_list
            },
            production_this_week=0,
            backlog={asin: 0 for asin in asin_list},
        )

        # MOD depot: delivery point for the customer (Ministry of Defence)
        # Fictional location: logistics hub near Bicester, Oxfordshire
        G.add_node(
            "MODDepot",
            node_type="customer",
            label="MOD Depot",
            location=(51.90, -1.15),
            delivered=0,
            delivered_by_item={asin: 0 for asin in asin_list},
        )

        # --- Edges (supply lanes) ---

        # Sub-tier → Tier-1 suppliers (raw materials / sub-components)
        G.add_edge(
            "SubTierSupplierC",
            "Tier1SupplierA",
            transit_time=4,
            transport_mode="road",
            shipments=[],
        )
        G.add_edge(
            "SubTierSupplierC",
            "Tier1SupplierB",
            transit_time=5,
            transport_mode="sea_road",
            shipments=[],
        )

        # Tier-1 → Prime factory (components)
        G.add_edge(
            "Tier1SupplierA",
            "AlbionFactory",
            transit_time=2,
            transport_mode="road",
            shipments=[],
        )
        G.add_edge(
            "Tier1SupplierB",
            "AlbionFactory",
            transit_time=3,
            transport_mode="sea_road",
            shipments=[],
        )

        # Prime factory → MOD depot (finished goods)
        G.add_edge(
            "AlbionFactory",
            "MODDepot",
            transit_time=1,
            transport_mode="road_secure",
            shipments=[],
        )

        return G
