#!/usr/bin/env python
"""
CLI runner for the UK Defence Prime Supply Chain Surge Simulation.

Usage:
    python run_defence_sim.py --scenario peacetime_baseline
    python run_defence_sim.py --scenario short_sharp_surge --seed 42
    python run_defence_sim.py --list-scenarios

Scenarios:
    peacetime_baseline              Normal MOD demand, no disruptions
    short_sharp_surge               3x demand spike for 12 weeks
    prolonged_attritional_conflict  2x demand sustained for 44 weeks
    supplier_shock_during_surge     Surge + sole-source supplier failure
    logistics_disruption_in_surge   Surge + doubled transit times

All names, data, and outputs are fictional and for simulation purposes only.
"""

import argparse
import logging
import sys
import os

# Ensure the src directory is on the path for direct execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scse.controller.miniscot import SupplyChainEnvironment
from scse.scenarios.scenario_loader import load_scenario, list_scenarios

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='UK Defence Prime Supply Chain Surge Simulation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--scenario', '-s',
        default='peacetime_baseline',
        help='Scenario name (default: peacetime_baseline)'
    )
    parser.add_argument(
        '--seed', type=int, default=12345,
        help='Random seed for reproducibility (default: 12345)'
    )
    parser.add_argument(
        '--output-dir', '-o', default='output',
        help='Output directory for results (default: output)'
    )
    parser.add_argument(
        '--list-scenarios', action='store_true',
        help='List available scenarios and exit'
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help='Suppress debug logging'
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s'
    )
    # Suppress verbose debug from the controller
    logging.getLogger('scse.controller.miniscot').setLevel(logging.WARNING)

    if args.list_scenarios:
        print("Available scenarios:")
        for name in list_scenarios():
            scenario = load_scenario(name)
            print(f"  {name:40s} {scenario.get('description', '')}")
        return

    # Load scenario to get time horizon
    scenario = load_scenario(args.scenario)
    time_horizon = scenario.get('time_horizon', 52)

    print(f"\n{'='*60}")
    print(f"  Defence Prime Supply Chain Surge Simulation")
    print(f"  Scenario: {args.scenario}")
    print(f"  Description: {scenario.get('description', 'N/A')}")
    print(f"  Horizon: {time_horizon} weeks")
    print(f"  Seed: {args.seed}")
    print(f"{'='*60}\n")

    # Create and run the simulation
    env = SupplyChainEnvironment(
        profile='defence_surge_profile',
        simulation_seed=args.seed,
        start_date='2025-01-06',  # A Monday
        time_increment='weekly',
        time_horizon=time_horizon,
        asin_selection='all',
        scenario=args.scenario,
        output_dir=args.output_dir,
    )

    final_state = env.run()

    # Write metrics output
    metrics = env._metrics
    if hasattr(metrics, 'write_output'):
        output_path = metrics.write_output()
        print(f"\nResults written to: {output_path}/")

    # Print summary to console
    if hasattr(metrics, '_log') and metrics._log:
        last = metrics._log[-1]
        print(f"\n{'='*60}")
        print(f"  SIMULATION RESULTS — {args.scenario}")
        print(f"{'='*60}")
        print(f"  Total demanded:       {last['total_demanded']:>8} units")
        print(f"  Total fulfilled:      {last['total_fulfilled']:>8} units")
        print(f"  Final fill rate:      {last['fill_rate']:>8.1%}")
        print(f"  Final backlog:        {last['backlog']:>8} units")
        print(f"  Final FG inventory:   {last['fg_inventory']:>8} units")
        print(f"  Expedite orders:      {last['expedite_orders_cumulative']:>8}")
        print(f"  Peak backlog:         {max(r['backlog'] for r in metrics._log):>8} units")
        print(f"  Min fill rate:        {min(r['fill_rate'] for r in metrics._log):>8.1%}")
        print(f"  Peak utilisation:     {max(r['utilisation'] for r in metrics._log):>8.1%}")
        print(f"{'='*60}")
        print(f"\n  All values are fictional simulation outputs.")
        print(f"  See {output_path}/ for detailed CSV and summary.\n")


if __name__ == '__main__':
    main()
