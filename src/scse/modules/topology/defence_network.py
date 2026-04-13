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

    def __init__(self, run_parameters):
        self._simulation_seed = run_parameters['simulation_seed']
        self._initial_component_inv = self._DEFAULT_INITIAL_COMPONENT_INVENTORY
        self._initial_finished_inv = self._DEFAULT_INITIAL_FINISHED_INVENTORY
        self._factory_capacity = self._DEFAULT_FACTORY_CAPACITY

    def get_name(self):
        return 'network'

    def get_initial_state(self, context):
        """Build the defence supply chain network graph."""
        G = nx.DiGraph()
        asin_list = context.get('asin_list', [])

        # --- Nodes ---

        # Sub-tier supplier: sole-source for critical raw materials / energetics
        # Fictional location: industrial site near Bridgwater, Somerset
        G.add_node('SubTierSupplierC',
                    node_type='vendor',
                    location=(51.13, -3.00),
                    supplier_type='sub_tier',
                    base_lead_time=6,
                    lead_time_variability=3,
                    weekly_capacity=80,
                    disruption_profile='fragile')

        # Tier-1 Supplier A: UK-based, reliable, moderate lead time
        # Fictional location: industrial site near Barrow-in-Furness, Cumbria
        G.add_node('Tier1SupplierA',
                    node_type='vendor',
                    location=(54.11, -3.23),
                    supplier_type='tier_1',
                    base_lead_time=3,
                    lead_time_variability=1,
                    weekly_capacity=80,
                    disruption_profile='reliable')

        # Tier-1 Supplier B: Allied (European), longer lead time
        # Fictional location: allied supplier in northern France
        G.add_node('Tier1SupplierB',
                    node_type='vendor',
                    location=(49.44, 1.09),
                    supplier_type='tier_1',
                    base_lead_time=5,
                    lead_time_variability=2,
                    weekly_capacity=60,
                    disruption_profile='moderate')

        # Prime contractor factory: Albion Defence Systems
        # Fictional location: industrial complex near Bristol
        G.add_node('AlbionFactory',
                    node_type='warehouse',
                    location=(51.45, -2.59),
                    facility_type='prime_factory',
                    weekly_capacity=self._factory_capacity,
                    inventory={asin: self._initial_finished_inv for asin in asin_list},
                    component_inventory={asin: self._initial_component_inv for asin in asin_list},
                    production_this_week=0,
                    backlog={asin: 0 for asin in asin_list})

        # MOD depot: delivery point for the customer (Ministry of Defence)
        # Fictional location: logistics hub near Bicester, Oxfordshire
        G.add_node('MODDepot',
                    node_type='customer',
                    location=(51.90, -1.15),
                    delivered=0,
                    delivered_by_item={asin: 0 for asin in asin_list})

        # --- Edges (supply lanes) ---

        # Sub-tier → Tier-1 suppliers (raw materials / sub-components)
        G.add_edge('SubTierSupplierC', 'Tier1SupplierA',
                    transit_time=4, transport_mode='road',
                    shipments=[])
        G.add_edge('SubTierSupplierC', 'Tier1SupplierB',
                    transit_time=5, transport_mode='sea_road',
                    shipments=[])

        # Tier-1 → Prime factory (components)
        G.add_edge('Tier1SupplierA', 'AlbionFactory',
                    transit_time=2, transport_mode='road',
                    shipments=[])
        G.add_edge('Tier1SupplierB', 'AlbionFactory',
                    transit_time=3, transport_mode='sea_road',
                    shipments=[])

        # Prime factory → MOD depot (finished goods)
        G.add_edge('AlbionFactory', 'MODDepot',
                    transit_time=1, transport_mode='road_secure',
                    shipments=[])

        return G
