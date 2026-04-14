"""
Defence programme item selection module.

Replaces the retail ASIN selection with fictional UK defence programme items.
Each item represents a product family produced by the prime contractor.

All names are fictional and for simulation purposes only.
"""

from scse.api.module import Env


# Fictional defence programme items produced by the prime contractor.
# Each item has a base weekly demand rate and a programme priority (1=highest).
DEFENCE_PROGRAMME_ITEMS = {
    "PGM-001": {
        "name": "Precision-Guided Munition Mk4",
        "family": "Munitions",
        "base_weekly_demand": 40,
        "priority": 1,
        "unit_cost": 15000,
        "critical_component": "COMP-ENG-01",
    },
    "RADAR-002": {
        "name": "Sentinel Radar Module",
        "family": "Sensors",
        "base_weekly_demand": 8,
        "priority": 2,
        "unit_cost": 85000,
        "critical_component": "COMP-SEMI-01",
    },
    "COMMS-003": {
        "name": "Secure Comms Assembly Type-7",
        "family": "Communications",
        "base_weekly_demand": 15,
        "priority": 2,
        "unit_cost": 32000,
        "critical_component": "COMP-SEMI-01",
    },
    "AVS-004": {
        "name": "Armoured Vehicle Subsystem Pack",
        "family": "Vehicle Systems",
        "base_weekly_demand": 5,
        "priority": 3,
        "unit_cost": 120000,
        "critical_component": "COMP-ARMR-01",
    },
    "MRO-005": {
        "name": "Depot Maintenance & Spares Kit",
        "family": "MRO / Sustainment",
        "base_weekly_demand": 25,
        "priority": 3,
        "unit_cost": 8000,
        "critical_component": "COMP-ENG-01",
    },
}


class DefenceProgrammeSelection(Env):
    """Provides the list of defence programme items to the simulation.

    This replaces the retail ASIN selection module. Instead of ISBNs,
    the simulation operates over fictional UK defence programme items.
    """

    def __init__(self, run_parameters):
        self._asin_selection = run_parameters.get('asin_selection', 'all')

    def get_name(self):
        return 'asin_list'

    def get_context(self):
        """Return the list of programme item IDs as the 'asin_list' context.

        The existing framework uses 'asin' terminology throughout — we reuse
        this to maintain compatibility with the controller and network utilities.
        """
        if self._asin_selection == 'all' or self._asin_selection is None:
            return list(DEFENCE_PROGRAMME_ITEMS.keys())
        elif isinstance(self._asin_selection, list):
            return self._asin_selection
        elif isinstance(self._asin_selection, int):
            items = list(DEFENCE_PROGRAMME_ITEMS.keys())
            return items[:self._asin_selection]
        else:
            return list(DEFENCE_PROGRAMME_ITEMS.keys())
