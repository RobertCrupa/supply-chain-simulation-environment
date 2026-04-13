"""
Scenario loader for defence surge simulation.

Loads named scenario configurations from JSON files in the scenarios directory.
Scenarios control demand regime, supplier disruption, and logistics parameters
without changing module code.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

_SCENARIO_DIR = os.path.dirname(os.path.abspath(__file__))


def load_scenario(scenario_name):
    """Load a scenario configuration by name.

    Args:
        scenario_name: Name of the scenario (e.g. 'peacetime_baseline').
            Must correspond to a JSON file in the scenarios directory.

    Returns:
        dict: Scenario configuration with keys: name, description,
            time_horizon, demand, suppliers, logistics.

    Raises:
        FileNotFoundError: If the scenario JSON file does not exist.
    """
    fpath = os.path.join(_SCENARIO_DIR, scenario_name + '.json')
    if not os.path.exists(fpath):
        available = list_scenarios()
        raise FileNotFoundError(
            f"Scenario '{scenario_name}' not found at {fpath}. "
            f"Available scenarios: {available}"
        )
    with open(fpath) as f:
        scenario = json.load(f)
    logger.info(f"Loaded scenario: {scenario['name']} — {scenario['description']}")
    return scenario


def list_scenarios():
    """Return a list of available scenario names."""
    scenarios = []
    for fname in sorted(os.listdir(_SCENARIO_DIR)):
        if fname.endswith('.json'):
            scenarios.append(fname.replace('.json', ''))
    return scenarios


def get_demand_multiplier(scenario, current_week):
    """Calculate the demand multiplier for the current week based on scenario config.

    Args:
        scenario: Scenario configuration dict.
        current_week: Current simulation week (0-indexed).

    Returns:
        float: Demand multiplier to apply to baseline demand rates.
    """
    demand_cfg = scenario['demand']
    trigger = demand_cfg.get('surge_trigger_week')
    duration = demand_cfg.get('surge_duration_weeks', 0)
    baseline_mult = demand_cfg.get('baseline_multiplier', 1.0)
    surge_mult = demand_cfg.get('surge_multiplier', 1.0)
    post_surge_mult = demand_cfg.get('post_surge_multiplier', 1.0)

    if trigger is None or current_week < trigger:
        return baseline_mult
    elif current_week < trigger + duration:
        return surge_mult
    else:
        return post_surge_mult


def is_supplier_disrupted(scenario, supplier_name, current_week, rng):
    """Determine if a supplier is disrupted this week.

    Checks both forced disruptions (scenario-scripted outages) and
    stochastic disruptions (random probability per week).

    Args:
        scenario: Scenario configuration dict.
        supplier_name: Name of the supplier node.
        current_week: Current simulation week.
        rng: numpy RandomState for stochastic draws.

    Returns:
        bool: True if the supplier is disrupted (cannot fulfil orders).
    """
    supplier_cfg = scenario['suppliers']

    # Check forced disruptions first
    forced = supplier_cfg.get('forced_disruptions', {})
    if supplier_name in forced:
        disruption = forced[supplier_name]
        if disruption['start_week'] <= current_week < disruption['end_week']:
            return True

    # Stochastic disruption
    prob = supplier_cfg.get('disruption_probability', 0.0)
    return rng.random() < prob


def get_transit_time_multiplier(scenario, current_week):
    """Calculate transit time multiplier for the current week.

    Args:
        scenario: Scenario configuration dict.
        current_week: Current simulation week.

    Returns:
        float: Multiplier to apply to base transit times.
    """
    logistics_cfg = scenario['logistics']
    base_mult = logistics_cfg.get('transit_time_multiplier', 1.0)
    start = logistics_cfg.get('transit_disruption_start_week')
    end = logistics_cfg.get('transit_disruption_end_week')

    if start is not None and end is not None:
        if start <= current_week < end:
            return base_mult
    return 1.0
