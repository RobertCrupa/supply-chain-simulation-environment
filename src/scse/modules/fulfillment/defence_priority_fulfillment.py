"""
Defence priority fulfillment module with production constraints.

Combines two functions:
1. Production: converts component inventory to finished goods (capacity-limited)
2. Fulfillment: allocates finished goods to MOD orders by programme priority

The prime factory (AlbionFactory) has a weekly production capacity.
Customer orders are fulfilled in priority order from finished-goods inventory.
Unfulfilled orders accumulate as backlog.

All parameters are fictional and for simulation purposes only.
"""

import logging
from scse.api.module import Agent
from scse.api.network import get_asin_inventory_in_node, set_asin_inventory_in_node
from scse.modules.selection.defence_programme_selection import DEFENCE_PROGRAMME_ITEMS

logger = logging.getLogger(__name__)


class DefencePriorityFulfillment(Agent):
    """Priority-based fulfillment with production capacity constraint.

    Each timestep:
    1. Production step — produce up to factory capacity from component inventory
    2. Fulfillment step — allocate finished goods to customer orders by priority

    Orders that cannot be fulfilled are left in the customer_orders list
    and become backlog for the next timestep.
    """

    # Production capacity: limit per item to 2x the fair share.
    # This allows some items to use more than their equal share of capacity
    # while preventing any single item from monopolising the factory.
    _PRODUCTION_HEADROOM_FACTOR = 2

    def __init__(self, run_parameters):
        pass

    def get_name(self):
        return 'fulfillment'

    def reset(self, context, state):
        self._asin_list = context.get('asin_list', [])

    def compute_actions(self, state):
        """Produce goods and fulfil customer orders."""
        G = state['network']
        current_week = state['clock']

        # --- Step 1: Production ---
        factory_data = G.nodes['AlbionFactory']
        weekly_capacity = factory_data.get('weekly_capacity', 60)
        produced_this_week = 0

        for asin in self._asin_list:
            if produced_this_week >= weekly_capacity:
                break

            # Check component inventory available for production
            component_inv = factory_data.get('component_inventory', {}).get(asin, 0)
            if component_inv <= 0:
                continue

            # Produce as many as capacity and components allow
            can_produce = min(component_inv, weekly_capacity - produced_this_week)
            max_per_item = max(1, weekly_capacity // max(1, len(self._asin_list)))
            produce_qty = min(can_produce, max_per_item * self._PRODUCTION_HEADROOM_FACTOR)

            if produce_qty > 0:
                # Consume components
                factory_data['component_inventory'][asin] = component_inv - produce_qty
                # Add to finished goods inventory
                current_fg = factory_data.get('inventory', {}).get(asin, 0)
                if 'inventory' not in factory_data:
                    factory_data['inventory'] = {}
                factory_data['inventory'][asin] = current_fg + produce_qty
                produced_this_week += produce_qty

                logger.debug(
                    f"Week {current_week}: Produced {asin} x{produce_qty} "
                    f"(components used={produce_qty}, FG now={factory_data['inventory'][asin]})"
                )

        factory_data['production_this_week'] = produced_this_week

        # --- Step 2: Fulfillment ---
        customer_orders = state.get('customer_orders', [])

        # Sort by programme priority (lower number = higher priority)
        customer_orders.sort(
            key=lambda o: (
                DEFENCE_PROGRAMME_ITEMS.get(o.get('asin', ''), {}).get('priority', 99),
                o.get('schedule', 0)  # FIFO within same priority
            )
        )

        actions = []

        # Track virtual inventory to avoid over-committing across multiple orders
        virtual_inventory = {}
        for asin in self._asin_list:
            virtual_inventory[asin] = get_asin_inventory_in_node(factory_data, asin)

        for order in customer_orders:
            asin = order['asin']
            quantity = order['quantity']
            destination = order.get('destination', 'MODDepot')

            available = virtual_inventory.get(asin, 0)

            if available >= quantity:
                # Full fulfillment
                action = {
                    'type': 'outbound_shipment',
                    'asin': asin,
                    'quantity': quantity,
                    'origin': 'AlbionFactory',
                    'destination': destination,
                    'schedule': current_week,
                    'uuid': order.get('uuid', ''),
                }
                actions.append(action)
                virtual_inventory[asin] = available - quantity

                logger.debug(
                    f"Week {current_week}: Fulfilled {asin} x{quantity} → {destination}"
                )
            elif available > 0:
                # Partial fulfillment — ship what's available
                action = {
                    'type': 'outbound_shipment',
                    'asin': asin,
                    'quantity': available,
                    'origin': 'AlbionFactory',
                    'destination': destination,
                    'schedule': current_week,
                    'uuid': order.get('uuid', ''),
                }
                actions.append(action)
                virtual_inventory[asin] = 0

                # Reduce order quantity by amount shipped (remainder stays as backlog)
                order['quantity'] = quantity - available

                logger.debug(
                    f"Week {current_week}: Partial fulfillment {asin} "
                    f"x{available}/{quantity} → {destination} (backlog={order['quantity']})"
                )
            else:
                # No inventory — order remains as backlog
                logger.debug(
                    f"Week {current_week}: BACKLOG {asin} x{quantity} — no FG inventory"
                )

        return actions
