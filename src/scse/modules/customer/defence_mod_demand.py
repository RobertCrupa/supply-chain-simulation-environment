"""
MOD / DE&S demand generation module for defence surge simulation.

Generates weekly demand signals from the Ministry of Defence, with support
for baseline peacetime demand and wartime surge demand driven by scenario
configuration.

Demand is generated per programme item with configurable noise. The surge
multiplier is applied based on the current simulation week and the active
scenario's demand regime.

All demand parameters are fictional and for simulation purposes only.
"""

import logging
import numpy as np
from scse.api.module import Agent
from scse.modules.selection.defence_programme_selection import DEFENCE_PROGRAMME_ITEMS
from scse.scenarios.scenario_loader import load_scenario, get_demand_multiplier

logger = logging.getLogger(__name__)


class MODDemandGenerator(Agent):
    """Generates MOD demand orders based on scenario-driven demand regime.

    Each timestep (week), generates a customer_order for each programme item.
    The demand quantity is:
        demand = round(base_weekly_demand * demand_multiplier * noise)
    where noise ~ Uniform[0.8, 1.2] adds realistic variability.
    """

    _DEMAND_NOISE_LOW = 0.8
    _DEMAND_NOISE_HIGH = 1.2

    def __init__(self, run_parameters):
        self._rng = np.random.RandomState(run_parameters['simulation_seed'])
        self._scenario_name = run_parameters.get('scenario', 'peacetime_baseline')
        self._scenario = load_scenario(self._scenario_name)

    def get_name(self):
        return 'customer'

    def reset(self, context, state):
        self._asin_list = context.get('asin_list', [])

    def compute_actions(self, state):
        """Generate weekly MOD demand orders for all programme items."""
        current_week = state['clock']
        demand_multiplier = get_demand_multiplier(self._scenario, current_week)

        actions = []
        for asin in self._asin_list:
            item_config = DEFENCE_PROGRAMME_ITEMS.get(asin, {})
            base_demand = item_config.get('base_weekly_demand', 10)

            # Apply surge multiplier and add noise
            noise = self._rng.uniform(self._DEMAND_NOISE_LOW, self._DEMAND_NOISE_HIGH)
            demand_qty = max(1, round(base_demand * demand_multiplier * noise))

            action = {
                'type': 'customer_order',
                'asin': asin,
                'origin': None,
                'destination': 'MODDepot',
                'quantity': demand_qty,
                'schedule': current_week,
                'programme_priority': item_config.get('priority', 3),
            }
            actions.append(action)

            if demand_multiplier > 1.0:
                logger.debug(
                    f"Week {current_week}: SURGE demand for {asin} = {demand_qty} "
                    f"(base={base_demand}, mult={demand_multiplier:.1f})"
                )

        return actions
