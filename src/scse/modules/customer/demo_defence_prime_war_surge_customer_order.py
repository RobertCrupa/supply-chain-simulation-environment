"""
Customer demand generator for defence-prime war-surge simulations.
"""
from scse.api.module import Agent
import numpy as np

import logging
logger = logging.getLogger(__name__)


class DefencePrimeWarSurgeCustomerOrder(Agent):
    _DEFAULT_BASELINE_MEAN = 8
    _DEFAULT_WAR_SURGE_START = 20
    _DEFAULT_WAR_SURGE_DURATION = 20
    _DEFAULT_WAR_SURGE_MULTIPLIER = 3.5
    _DEFAULT_MIN_DEMAND = 1

    def __init__(self, run_parameters):
        simulation_seed = run_parameters['simulation_seed']
        self._rng = np.random.RandomState(simulation_seed)

        self._baseline_mean = run_parameters.get(
            'customer_baseline_mean', self._DEFAULT_BASELINE_MEAN)
        self._war_surge_start = run_parameters.get(
            'war_surge_start', self._DEFAULT_WAR_SURGE_START)
        self._war_surge_duration = run_parameters.get(
            'war_surge_duration', self._DEFAULT_WAR_SURGE_DURATION)
        self._war_surge_multiplier = run_parameters.get(
            'war_surge_multiplier', self._DEFAULT_WAR_SURGE_MULTIPLIER)
        self._min_demand = run_parameters.get(
            'customer_min_demand', self._DEFAULT_MIN_DEMAND)

        self._DEFAULT_DEFENCE_PRIME_CUSTOMER = 'Customer'

    def get_name(self):
        return 'order_generator'

    def reset(self, context, state):
        self._asin_list = context['asin_list']

    def _get_mean_demand(self, clock):
        if self._war_surge_start <= clock < (self._war_surge_start + self._war_surge_duration):
            return self._baseline_mean * self._war_surge_multiplier
        return self._baseline_mean

    def compute_actions(self, state):
        actions = []
        clock = state['clock']
        mean_demand = self._get_mean_demand(clock)

        for asin in self._asin_list:
            demand_realization = int(max(
                self._min_demand,
                self._rng.poisson(mean_demand)))
            action = {
                'type': 'customer_order',
                'asin': asin,
                'origin': None,
                'destination': self._DEFAULT_DEFENCE_PRIME_CUSTOMER,
                'quantity': demand_realization,
                'schedule': clock
            }
            logger.debug("{} bought {} units of {} at clock {}.".format(
                self._DEFAULT_DEFENCE_PRIME_CUSTOMER, demand_realization, asin, clock))
            actions.append(action)

        return actions
