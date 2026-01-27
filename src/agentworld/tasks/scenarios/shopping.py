"""Shopping domain task scenarios.

This module provides pre-defined tasks for evaluating agents
in e-commerce/shopping contexts.

Scenarios cover:
- Product search and browsing
- Cart management
- Checkout and orders
- Returns and refunds
"""

from agentworld.tasks.definitions import ExpectedAction, TaskDefinition, TaskSet


def _make_shopping_task(
    task_id: str,
    name: str,
    description: str,
    difficulty: str,
    agent_instruction: str,
    expected_final_states: dict,
    expected_actions: list[dict],
    required_outputs: list[str],
    initial_cart: list[dict] | None = None,
    initial_balance: float = 500.0,
    estimated_steps: int = 5,
    tags: list[str] | None = None,
) -> TaskDefinition:
    """Helper to create shopping task definitions."""
    initial_cart = initial_cart or []

    return TaskDefinition(
        task_id=task_id,
        name=name,
        description=description,
        domain="shopping",
        difficulty=difficulty,
        simulation_config={
            "name": f"Task: {name}",
            "agents": [
                {
                    "name": "Shopper",
                    "agent_id": "shopper",
                    "traits": {"role": "customer"},
                    "background": f"A customer with ${initial_balance:.2f} to spend.",
                },
            ],
            "apps": [
                {
                    "id": "amazon",
                    "config": {
                        "initial_balance": initial_balance,
                        "initial_cart": initial_cart,
                    },
                }
            ],
            "steps": estimated_steps,
            "topology": {"type": "fully_connected"},
        },
        initial_app_states={
            "amazon": {
                "shopper": {
                    "balance": initial_balance,
                    "cart": initial_cart,
                    "orders": [],
                }
            }
        },
        agent_instruction=agent_instruction,
        expected_final_states=expected_final_states,
        expected_actions=[ExpectedAction.from_dict(a) for a in expected_actions],
        required_outputs=required_outputs,
        policy_rules=["confirm_large_purchase", "verify_stock"],
        estimated_steps=estimated_steps,
        tags=tags or ["shopping"],
    )


# =============================================================================
# Easy Tasks
# =============================================================================

SEARCH_PRODUCT = _make_shopping_task(
    task_id="shopping_search",
    name="Search for Product",
    description="Search for a specific product and report findings.",
    difficulty="easy",
    agent_instruction=(
        "Search for 'wireless headphones' on Amazon. "
        "Report the top result including name and price."
    ),
    expected_final_states={
        "amazon": {
            "shopper": {"balance": 500.0, "cart": [], "orders": []},
        }
    },
    expected_actions=[
        {
            "agent_id": "shopper",
            "app_id": "amazon",
            "action_name": "search_products",
            "params": {"query": "wireless headphones"},
        }
    ],
    required_outputs=["headphones", "price"],
    estimated_steps=2,
    tags=["shopping", "search", "easy"],
)

ADD_TO_CART = _make_shopping_task(
    task_id="shopping_add_cart",
    name="Add to Cart",
    description="Add a specific item to the shopping cart.",
    difficulty="easy",
    agent_instruction=(
        "Add the 'Sony WH-1000XM5' headphones (product_id: 'sony_wh1000xm5', price: $349.99) "
        "to the cart. Verify it was added successfully."
    ),
    expected_final_states={
        "amazon": {
            "shopper": {
                "balance": 500.0,
                "cart": [{"product_id": "sony_wh1000xm5", "quantity": 1, "price": 349.99}],
            },
        }
    },
    expected_actions=[
        {
            "agent_id": "shopper",
            "app_id": "amazon",
            "action_name": "add_to_cart",
            "params": {"product_id": "sony_wh1000xm5", "quantity": 1},
        }
    ],
    required_outputs=["added", "cart", "sony"],
    estimated_steps=2,
    tags=["shopping", "cart", "easy"],
)


# =============================================================================
# Medium Tasks
# =============================================================================

SEARCH_AND_ADD = _make_shopping_task(
    task_id="shopping_search_add",
    name="Search and Add to Cart",
    description="Search for a product and add it to cart.",
    difficulty="medium",
    agent_instruction=(
        "Search for 'laptop stand' on Amazon. "
        "Find a product under $50 and add it to the cart. "
        "Report what you added and the cart total."
    ),
    expected_final_states={
        "amazon": {
            "shopper": {
                "balance": 500.0,
                # Cart will have one item under $50
            },
        }
    },
    expected_actions=[
        {
            "agent_id": "shopper",
            "app_id": "amazon",
            "action_name": "search_products",
            "params": {"query": "laptop stand"},
            "order": 1,
        },
        {
            "agent_id": "shopper",
            "app_id": "amazon",
            "action_name": "add_to_cart",
            "params": {},
            "order": 2,
        },
    ],
    required_outputs=["added", "cart", "stand"],
    estimated_steps=4,
    tags=["shopping", "search", "cart", "medium"],
)

MODIFY_CART = _make_shopping_task(
    task_id="shopping_modify_cart",
    name="Modify Cart Quantity",
    description="Update quantity of items in cart.",
    difficulty="medium",
    agent_instruction=(
        "The cart has 1 'USB-C Hub' (product_id: 'usbc_hub', $29.99). "
        "Increase the quantity to 3 and report the new cart total."
    ),
    initial_cart=[{"product_id": "usbc_hub", "quantity": 1, "price": 29.99}],
    expected_final_states={
        "amazon": {
            "shopper": {
                "balance": 500.0,
                "cart": [{"product_id": "usbc_hub", "quantity": 3, "price": 29.99}],
            },
        }
    },
    expected_actions=[
        {
            "agent_id": "shopper",
            "app_id": "amazon",
            "action_name": "update_cart",
            "params": {"product_id": "usbc_hub", "quantity": 3},
        }
    ],
    required_outputs=["quantity", "3", "89.97"],  # 3 * 29.99
    estimated_steps=3,
    tags=["shopping", "cart", "quantity", "medium"],
)

SIMPLE_CHECKOUT = _make_shopping_task(
    task_id="shopping_checkout",
    name="Simple Checkout",
    description="Complete checkout with items in cart.",
    difficulty="medium",
    agent_instruction=(
        "The cart has a 'Mechanical Keyboard' ($89.99). "
        "Complete the checkout process and confirm the order. "
        "Report the order confirmation and remaining balance."
    ),
    initial_cart=[{"product_id": "mech_keyboard", "quantity": 1, "price": 89.99}],
    expected_final_states={
        "amazon": {
            "shopper": {
                "balance": 410.01,  # 500 - 89.99
                "cart": [],
                # orders will have 1 item
            },
        }
    },
    expected_actions=[
        {
            "agent_id": "shopper",
            "app_id": "amazon",
            "action_name": "checkout",
            "params": {},
        }
    ],
    required_outputs=["order", "confirmed", "410"],
    estimated_steps=3,
    tags=["shopping", "checkout", "medium"],
)


# =============================================================================
# Hard Tasks
# =============================================================================

FULL_SHOPPING_FLOW = _make_shopping_task(
    task_id="shopping_full_flow",
    name="Full Shopping Flow",
    description="Complete end-to-end shopping: search, add, checkout.",
    difficulty="hard",
    agent_instruction=(
        "Complete a full shopping flow: "
        "1. Search for 'wireless mouse' "
        "2. Find one under $40 "
        "3. Add 2 units to cart "
        "4. Review the cart total "
        "5. Complete checkout "
        "Report the order confirmation and remaining balance."
    ),
    expected_final_states={
        "amazon": {
            "shopper": {
                # Balance will be reduced by ~$80 (2x ~$40)
                "cart": [],
            },
        }
    },
    expected_actions=[
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "search_products", "order": 1},
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "add_to_cart", "params": {"quantity": 2}, "order": 2},
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "view_cart", "order": 3, "required": False},
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "checkout", "order": 4},
    ],
    required_outputs=["order", "confirmed", "mouse"],
    estimated_steps=8,
    tags=["shopping", "full-flow", "hard"],
)

MULTI_ITEM_PURCHASE = _make_shopping_task(
    task_id="shopping_multi_item",
    name="Multi-Item Purchase",
    description="Add multiple different items and checkout.",
    difficulty="hard",
    agent_instruction=(
        "Create a home office setup order: "
        "1. Add 'Desk Lamp' (product_id: 'desk_lamp', $34.99) "
        "2. Add 'Mouse Pad XL' (product_id: 'mousepad_xl', $19.99) "
        "3. Add 'Monitor Stand' (product_id: 'monitor_stand', $45.99) "
        "4. Review cart to verify all items "
        "5. Complete checkout "
        "Report total cost and order confirmation."
    ),
    expected_final_states={
        "amazon": {
            "shopper": {
                "balance": 399.03,  # 500 - (34.99 + 19.99 + 45.99)
                "cart": [],
            },
        }
    },
    expected_actions=[
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "add_to_cart", "params": {"product_id": "desk_lamp"}},
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "add_to_cart", "params": {"product_id": "mousepad_xl"}},
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "add_to_cart", "params": {"product_id": "monitor_stand"}},
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "checkout"},
    ],
    required_outputs=["order", "lamp", "mousepad", "monitor", "100.97"],
    estimated_steps=8,
    tags=["shopping", "multi-item", "hard"],
)

REMOVE_AND_REPLACE = _make_shopping_task(
    task_id="shopping_remove_replace",
    name="Remove and Replace Item",
    description="Remove item from cart and add a different one.",
    difficulty="hard",
    agent_instruction=(
        "The cart has 'Basic Mouse' ($19.99). "
        "The customer changed their mind and wants 'Gaming Mouse' ($59.99) instead. "
        "1. Remove 'Basic Mouse' (product_id: 'basic_mouse') from cart "
        "2. Add 'Gaming Mouse' (product_id: 'gaming_mouse') to cart "
        "3. Complete checkout "
        "Report the final order."
    ),
    initial_cart=[{"product_id": "basic_mouse", "quantity": 1, "price": 19.99}],
    expected_final_states={
        "amazon": {
            "shopper": {
                "balance": 440.01,  # 500 - 59.99
                "cart": [],
            },
        }
    },
    expected_actions=[
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "remove_from_cart", "params": {"product_id": "basic_mouse"}, "order": 1},
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "add_to_cart", "params": {"product_id": "gaming_mouse"}, "order": 2},
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "checkout", "order": 3},
    ],
    required_outputs=["gaming", "mouse", "order", "440"],
    estimated_steps=6,
    tags=["shopping", "cart-modify", "hard"],
)

BUDGET_CONSTRAINT = _make_shopping_task(
    task_id="shopping_budget",
    name="Budget-Constrained Shopping",
    description="Shop within a specific budget limit.",
    difficulty="hard",
    agent_instruction=(
        "You have a budget of $100. "
        "Create the best home office setup possible within this budget. "
        "Search for items, compare prices, and add items to cart. "
        "Do not exceed the $100 budget. "
        "Complete checkout and report what you purchased and total spent."
    ),
    initial_balance=100.0,
    expected_final_states={
        "amazon": {
            "shopper": {
                # Balance should be > 0 (didn't exceed budget)
                "cart": [],
            },
        }
    },
    expected_actions=[
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "search_products"},
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "add_to_cart"},
        {"agent_id": "shopper", "app_id": "amazon", "action_name": "checkout"},
    ],
    required_outputs=["budget", "total", "order"],
    estimated_steps=10,
    tags=["shopping", "budget", "constraint", "hard"],
)


# =============================================================================
# Scenario Collections
# =============================================================================

SHOPPING_SCENARIOS: list[TaskDefinition] = [
    # Easy
    SEARCH_PRODUCT,
    ADD_TO_CART,
    # Medium
    SEARCH_AND_ADD,
    MODIFY_CART,
    SIMPLE_CHECKOUT,
    # Hard
    FULL_SHOPPING_FLOW,
    MULTI_ITEM_PURCHASE,
    REMOVE_AND_REPLACE,
    BUDGET_CONSTRAINT,
]

SHOPPING_BENCHMARK = TaskSet(
    name="shopping_benchmark",
    description="Comprehensive shopping domain benchmark covering easy, medium, and hard tasks",
    domain="shopping",
    task_ids=[t.task_id for t in SHOPPING_SCENARIOS],
)


def get_shopping_scenarios() -> list[TaskDefinition]:
    """Get all shopping task scenarios.

    Returns:
        List of shopping TaskDefinitions
    """
    return SHOPPING_SCENARIOS.copy()


def get_shopping_scenarios_by_difficulty(difficulty: str) -> list[TaskDefinition]:
    """Get shopping scenarios filtered by difficulty.

    Args:
        difficulty: 'easy', 'medium', or 'hard'

    Returns:
        Filtered list of TaskDefinitions
    """
    return [t for t in SHOPPING_SCENARIOS if t.difficulty == difficulty]
