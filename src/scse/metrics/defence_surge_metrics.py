"""
Defence surge simulation metrics module.

Tracks operational metrics relevant to a UK defence prime contractor
under surge conditions. Replaces the retail cash-accounting metrics
with defence-industrial KPIs.

Metrics tracked:
- Fill rate (units fulfilled / units demanded)
- Backlog (unfulfilled demand accumulation)
- Inventory position (on-hand finished goods and components)
- Production utilisation (actual output / capacity)
- Expedite cost proxy (count and cost of expedited orders)
- Service level (weekly fill rate)

Outputs CSV logs and a text summary to the output directory.

Interface note: The controller calls compute_reward(state, action) where
action is a single action dict. For 'advance_time', the method returns a
dict with 'total' and 'by_asin'. For shipments, it returns a scalar.
This matches the existing CashAccounting interface.
"""

import os
import csv
import logging
from scse.api.network import get_asin_inventory_in_node

logger = logging.getLogger(__name__)


class DefenceSurgeMetrics:
    """Collects and outputs defence-specific operational metrics.

    Follows the same compute_reward(state, action) interface as the
    existing CashAccounting metrics so the controller needs no changes
    to its reward-collection logic.
    """

    _EXPEDITE_COST_PREMIUM = 0.5  # 50% premium on expedited units
    _HOLDING_COST_PER_UNIT_WEEK = 100  # £ per unit per week
    _UNIT_COST = 5
    _UNIT_PRICE = 10

    def __init__(self, run_parameters):
        self._scenario_name = run_parameters.get('scenario', 'peacetime_baseline')
        self._output_dir = run_parameters.get('output_dir', 'output')
        self._time_horizon = run_parameters.get('time_horizon', 52)

        # Per-timestep accumulators (reset each advance_time)
        self._timestep_fulfilled = 0
        self._timestep_demanded = 0
        self._timestep_expedite_orders = 0
        self._timestep_expedite_units = 0
        self._timestep_inbound_cost = 0

        # Cumulative tracking
        self._total_demanded = 0
        self._total_fulfilled = 0
        self._total_expedite_orders = 0
        self._total_expedite_units = 0

        self._log = []

    def reset(self, context, state):
        """Reset metrics state for a new episode."""
        self._context = {}
        self._context['asin_list'] = context.get('asin_list', [])
        self._timestep_fulfilled = 0
        self._timestep_demanded = 0
        self._timestep_expedite_orders = 0
        self._timestep_expedite_units = 0
        self._timestep_inbound_cost = 0
        self._total_demanded = 0
        self._total_fulfilled = 0
        self._total_expedite_orders = 0
        self._total_expedite_units = 0
        self._log = []

    def compute_reward(self, state, action):
        """Compute reward for a single action. Interface matches CashAccounting.

        For outbound_shipment / inbound_shipment: returns scalar reward.
        For advance_time: returns dict with 'total' and 'by_asin'.
        """
        action_type = action['type']
        quantity = action.get('quantity') or 0
        asin = action.get('asin', '')

        if action_type == 'outbound_shipment':
            self._timestep_fulfilled += quantity
            self._total_fulfilled += quantity
            return self._UNIT_PRICE * quantity

        elif action_type == 'inbound_shipment':
            cost = self._UNIT_COST * quantity
            is_expedite = action.get('expedite', False)
            if is_expedite:
                cost *= (1 + self._EXPEDITE_COST_PREMIUM)
                self._timestep_expedite_orders += 1
                self._timestep_expedite_units += quantity
                self._total_expedite_orders += 1
                self._total_expedite_units += quantity
            self._timestep_inbound_cost += cost
            return -cost

        elif action_type == 'advance_time':
            return self._advance_time_reward(state)

        else:
            # Unknown action type — return 0 reward rather than raising
            return 0

    def _advance_time_reward(self, state):
        """Compute end-of-timestep reward and log metrics."""
        G = state['network']
        reward_by_asin = {k: 0 for k in self._context.get('asin_list', [])}
        total_reward = 0.0

        # Compute inventory and backlog
        factory_data = G.nodes.get('AlbionFactory', {})
        total_fg_inv = 0
        total_comp_inv = 0
        total_backlog = 0

        for asin in self._context.get('asin_list', []):
            fg = factory_data.get('inventory', {}).get(asin, 0)
            total_fg_inv += fg
            comp = factory_data.get('component_inventory', {}).get(asin, 0)
            total_comp_inv += comp

        # Current backlog = unfulfilled customer orders remaining in state
        for order in state.get('customer_orders', []):
            total_backlog += order.get('quantity', 0)

        # Total demand = everything fulfilled so far + current outstanding backlog
        # This is correct because fulfilled orders are removed from customer_orders
        # and partially fulfilled orders have their quantity reduced in-place.
        self._total_demanded = self._total_fulfilled + total_backlog

        # Holding cost
        holding_cost = (total_fg_inv + total_comp_inv) * self._HOLDING_COST_PER_UNIT_WEEK
        total_reward -= holding_cost

        # Production utilisation
        production = factory_data.get('production_this_week', 0)
        capacity = factory_data.get('weekly_capacity', 60)
        utilisation = production / capacity if capacity > 0 else 0

        # Cumulative fill rate
        fill_rate = (
            self._total_fulfilled / self._total_demanded
            if self._total_demanded > 0 else 1.0
        )

        # Log this timestep
        self._log.append({
            'week': state.get('clock', 0),
            'total_demanded': self._total_demanded,
            'total_fulfilled': self._total_fulfilled,
            'fill_rate': round(fill_rate, 4),
            'backlog': total_backlog,
            'fg_inventory': total_fg_inv,
            'component_inventory': total_comp_inv,
            'production': production,
            'utilisation': round(utilisation, 4),
            'expedite_orders_cumulative': self._total_expedite_orders,
            'expedite_units_cumulative': self._total_expedite_units,
            'holding_cost': round(holding_cost, 2),
        })

        # Reset per-timestep accumulators
        self._timestep_fulfilled = 0
        self._timestep_demanded = 0
        self._timestep_expedite_orders = 0
        self._timestep_expedite_units = 0
        self._timestep_inbound_cost = 0

        return {'total': total_reward, 'by_asin': reward_by_asin}

    def write_output(self):
        """Write metrics CSV and summary text to the output directory."""
        scenario_dir = os.path.join(self._output_dir, self._scenario_name)
        os.makedirs(scenario_dir, exist_ok=True)

        # Write detailed CSV log
        csv_path = os.path.join(scenario_dir, 'metrics_log.csv')
        if self._log:
            fieldnames = list(self._log[0].keys())
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self._log)
            logger.info(f"Metrics CSV written to {csv_path}")

        # Write summary
        summary_path = os.path.join(scenario_dir, 'summary.txt')
        with open(summary_path, 'w') as f:
            f.write(f"Defence Surge Simulation — {self._scenario_name}\n")
            f.write("=" * 60 + "\n\n")

            if self._log:
                last = self._log[-1]
                f.write(f"Simulation horizon:     {len(self._log)} weeks\n")
                f.write(f"Total demanded:         {last['total_demanded']} units\n")
                f.write(f"Total fulfilled:        {last['total_fulfilled']} units\n")
                f.write(f"Final fill rate:        {last['fill_rate']:.1%}\n")
                f.write(f"Final backlog:          {last['backlog']} units\n")
                f.write(f"Final FG inventory:     {last['fg_inventory']} units\n")
                f.write(f"Final component inv:    {last['component_inventory']} units\n")
                f.write(f"Expedite orders (cum):  {last['expedite_orders_cumulative']}\n")
                f.write(f"Expedite units (cum):   {last['expedite_units_cumulative']}\n\n")

                # Peak metrics
                peak_backlog = max(row['backlog'] for row in self._log)
                min_fill_rate = min(row['fill_rate'] for row in self._log)
                peak_utilisation = max(row['utilisation'] for row in self._log)
                f.write(f"Peak backlog:           {peak_backlog} units\n")
                f.write(f"Minimum fill rate:      {min_fill_rate:.1%}\n")
                f.write(f"Peak utilisation:       {peak_utilisation:.1%}\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("All values are from a fictional simulation. Not operational data.\n")

        logger.info(f"Summary written to {summary_path}")

        return scenario_dir
