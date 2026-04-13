"""
Defence inventory and buying policy module.

Implements a safety-stock-based reorder policy with strategic reserve
and expedite capability, suitable for a UK defence prime contractor
managing constrained components.

The buying policy:
- Maintains per-item safety stock (weeks-of-cover target)
- Reorders when inventory position falls below safety stock + pipeline
- Triggers expedited orders when critically low (below half safety stock)
- Adjusts safety stock targets upward during surge demand

All parameters are fictional and for simulation purposes only.
"""

import logging
import numpy as np
from scse.api.module import Agent
from scse.api.network import (
    get_asin_inventory_in_network,
    get_asin_inventory_on_all_inbound_arcs,
)
from scse.modules.selection.defence_programme_selection import DEFENCE_PROGRAMME_ITEMS
from scse.scenarios.scenario_loader import load_scenario, get_demand_multiplier

logger = logging.getLogger(__name__)


class DefenceInventoryPolicy(Agent):
    """Safety-stock buying policy with expedite capability.

    Reorder logic per item per week:
        target_position = safety_stock_weeks * current_demand_rate
        inventory_position = on_hand + in_transit
        order_qty = max(0, target_position - inventory_position)

    During surge (demand_multiplier > 1.5), safety stock target increases
    by 50% to provide additional buffer.
    """

    _DEFAULT_SAFETY_STOCK_WEEKS = 4
    _SURGE_SAFETY_STOCK_MULTIPLIER = 1.5
    _EXPEDITE_THRESHOLD_FRACTION = 0.5  # Expedite when below 50% of safety stock
    _SURGE_THRESHOLD = 1.5  # Demand multiplier above which surge buffer kicks in

    def __init__(self, run_parameters):
        self._rng = np.random.RandomState(run_parameters['simulation_seed'] + 2)
        self._scenario_name = run_parameters.get('scenario', 'peacetime_baseline')
        self._scenario = load_scenario(self._scenario_name)
        self._safety_stock_weeks = self._DEFAULT_SAFETY_STOCK_WEEKS

    def get_name(self):
        return 'buying'

    def reset(self, context, state):
        self._asin_list = context.get('asin_list', [])

    def compute_actions(self, state):
        """Generate purchase orders based on inventory position vs safety stock."""
        G = state['network']
        current_week = state['clock']
        demand_multiplier = get_demand_multiplier(self._scenario, current_week)

        actions = []
        for asin in self._asin_list:
            item_config = DEFENCE_PROGRAMME_ITEMS.get(asin, {})
            base_demand = item_config.get('base_weekly_demand', 10)

            # Current demand rate
            current_demand_rate = base_demand * demand_multiplier

            # Safety stock target (in units)
            ss_weeks = self._safety_stock_weeks
            if demand_multiplier > self._SURGE_THRESHOLD:
                ss_weeks *= self._SURGE_SAFETY_STOCK_MULTIPLIER
            target_position = ss_weeks * current_demand_rate

            # Inventory position = on-hand + in-transit
            on_hand = get_asin_inventory_in_network(G, asin)
            in_transit = get_asin_inventory_on_all_inbound_arcs(G, asin)
            inventory_position = on_hand + in_transit

            # Reorder quantity
            order_qty = max(0, round(target_position - inventory_position))

            if order_qty > 0:
                # Determine if expedite is needed
                expedite = inventory_position < (target_position * self._EXPEDITE_THRESHOLD_FRACTION)

                action = {
                    'type': 'purchase_order',
                    'asin': asin,
                    'quantity': order_qty,
                    'schedule': current_week,
                    'destination': 'AlbionFactory',
                    'expedite': expedite,
                }
                actions.append(action)

                if expedite:
                    logger.info(
                        f"Week {current_week}: EXPEDITE PO for {asin} x{order_qty} "
                        f"(inv_pos={inventory_position:.0f}, target={target_position:.0f})"
                    )
                else:
                    logger.debug(
                        f"Week {current_week}: PO for {asin} x{order_qty} "
                        f"(inv_pos={inventory_position:.0f}, target={target_position:.0f})"
                    )

        return actions
