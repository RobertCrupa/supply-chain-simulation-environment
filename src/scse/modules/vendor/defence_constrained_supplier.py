"""
Defence constrained supplier module.

Models suppliers with finite capacity, stochastic lead times, and disruption
risk. Replaces the infinite-inventory vendor with realistic defence-industrial
supplier behaviour.

Suppliers:
- Have finite weekly dispatch capacity
- May be disrupted (forced or stochastic) based on scenario configuration
- Have variable lead times (base + random variability)
- Can receive expedited orders at premium cost

All supplier parameters are fictional and for simulation purposes only.
"""

import logging
import math
import numpy as np
from scse.api.module import Agent
from scse.scenarios.scenario_loader import (
    load_scenario, is_supplier_disrupted, get_transit_time_multiplier
)

logger = logging.getLogger(__name__)


class DefenceConstrainedSupplier(Agent):
    """Processes purchase orders through capacity-constrained, disruption-prone suppliers.

    For each pending purchase order:
    1. Identify which supplier node should fulfil it
    2. Check if supplier is disrupted this week
    3. If not disrupted, fulfil up to weekly capacity with variable lead time
    4. Remaining unfulfilled POs carry over to next week
    """

    def __init__(self, run_parameters):
        self._rng = np.random.RandomState(run_parameters['simulation_seed'] + 1)
        self._scenario_name = run_parameters.get('scenario', 'peacetime_baseline')
        self._scenario = load_scenario(self._scenario_name)
        self._supplier_capacity_used = {}

    def get_name(self):
        return 'vendor'

    def reset(self, context, state):
        self._asin_list = context.get('asin_list', [])
        self._supplier_capacity_used = {}

    def compute_actions(self, state):
        """Process purchase orders through constrained suppliers."""
        G = state['network']
        current_week = state['clock']
        purchase_orders = state.get('purchase_orders', [])
        transit_mult = get_transit_time_multiplier(self._scenario, current_week)

        # Reset capacity tracking for this week
        self._supplier_capacity_used = {}

        actions = []
        unfulfilled_pos = []

        # Identify supplier nodes
        supplier_nodes = [
            n for n, d in G.nodes(data=True)
            if d.get('node_type') == 'vendor'
        ]

        for po in purchase_orders:
            asin = po['asin']
            quantity = po['quantity']
            is_expedite = po.get('expedite', False)

            # Route PO to appropriate supplier
            # Tier-1 suppliers feed the factory; sub-tier feeds tier-1
            supplier = self._select_supplier(G, supplier_nodes, asin, po)
            if supplier is None:
                unfulfilled_pos.append(po)
                continue

            node_data = G.nodes[supplier]

            # Check disruption
            if is_supplier_disrupted(self._scenario, supplier, current_week, self._rng):
                logger.info(f"Week {current_week}: {supplier} DISRUPTED — PO for {asin} x{quantity} delayed")
                unfulfilled_pos.append(po)
                continue

            # Check capacity
            weekly_cap = node_data.get('weekly_capacity', 50)
            used = self._supplier_capacity_used.get(supplier, 0)
            available = max(0, weekly_cap - used)

            if available <= 0:
                unfulfilled_pos.append(po)
                continue

            dispatch_qty = min(quantity, available)
            self._supplier_capacity_used[supplier] = used + dispatch_qty

            # Calculate lead time with variability
            base_lt = node_data.get('base_lead_time', 3)
            lt_var = node_data.get('lead_time_variability', 1)
            lead_time = max(1, base_lt + self._rng.randint(-lt_var, lt_var + 1))

            # Expedite reduces lead time by ~40% at premium cost
            if is_expedite:
                lead_time = max(1, math.ceil(lead_time * 0.6))

            # Apply transit time multiplier from logistics disruption
            effective_lead_time = max(1, round(lead_time * transit_mult))

            # Determine destination (factory for tier-1, tier-1 for sub-tier)
            destination = self._get_destination(G, supplier)

            action = {
                'type': 'inbound_shipment',
                'asin': asin,
                'quantity': dispatch_qty,
                'origin': supplier,
                'destination': destination,
                'schedule': current_week,
                'uuid': po.get('uuid', ''),
                'lead_time_override': effective_lead_time,
                'expedite': is_expedite,
            }
            actions.append(action)

            # If partially fulfilled, keep remainder as pending PO
            remainder = quantity - dispatch_qty
            if remainder > 0:
                remaining_po = dict(po)
                remaining_po['quantity'] = remainder
                unfulfilled_pos.append(remaining_po)

            logger.debug(
                f"Week {current_week}: {supplier} dispatches {asin} x{dispatch_qty} "
                f"(LT={effective_lead_time}w, expedite={is_expedite})"
            )

        return actions

    def _select_supplier(self, G, supplier_nodes, asin, po):
        """Select the most appropriate supplier for a purchase order.

        Routes to the first available tier-1 supplier that has an edge
        to AlbionFactory. Falls back to any supplier.
        """
        destination = po.get('destination', 'AlbionFactory')

        # Prefer suppliers that directly feed the destination
        for supplier in supplier_nodes:
            if G.has_edge(supplier, destination):
                return supplier

        # Fallback: any vendor node
        if supplier_nodes:
            return supplier_nodes[0]
        return None

    def _get_destination(self, G, supplier):
        """Determine where a supplier ships to based on network edges."""
        successors = list(G.successors(supplier))
        if successors:
            return successors[0]
        return 'AlbionFactory'
