from scse.modules.customer.demo_defence_prime_war_surge_customer_order import DefencePrimeWarSurgeCustomerOrder
from scse.profiles.profile import load_profile


def test_defence_prime_profile_loads():
    profile = load_profile('defence_prime_war_surge_profile')
    assert profile['name'] == 'defence_prime_war_surge_profile'
    assert "scse.modules.customer.demo_defence_prime_war_surge_customer_order.DefencePrimeWarSurgeCustomerOrder" in profile['modules']


def test_war_surge_mean_demand_window():
    module = DefencePrimeWarSurgeCustomerOrder({
        'simulation_seed': 7,
        'customer_baseline_mean': 4,
        'war_surge_start': 3,
        'war_surge_duration': 2,
        'war_surge_multiplier': 5,
    })
    module.reset({'asin_list': ['asin-1']}, {})

    assert module._get_mean_demand(2) == 4
    assert module._get_mean_demand(3) == 20
    assert module._get_mean_demand(4) == 20
    assert module._get_mean_demand(5) == 4


def test_war_surge_customer_actions_shape():
    module = DefencePrimeWarSurgeCustomerOrder({
        'simulation_seed': 11,
        'customer_baseline_mean': 2,
        'war_surge_start': 1,
        'war_surge_duration': 2,
        'war_surge_multiplier': 6,
        'customer_min_demand': 1,
    })
    module.reset({'asin_list': ['asin-1', 'asin-2']}, {})

    actions = module.compute_actions({'clock': 1})

    assert len(actions) == 2
    for action in actions:
        assert action['type'] == 'customer_order'
        assert action['destination'] == 'Customer'
        assert action['schedule'] == 1
        assert isinstance(action['quantity'], int)
        assert action['quantity'] >= 1
