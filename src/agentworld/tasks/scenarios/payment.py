"""Payment domain task scenarios.

This module provides pre-defined tasks for evaluating agents
in payment/financial transaction contexts.

Scenarios cover:
- Simple transfers
- Balance verification
- Multi-step transactions
- Error handling
- Policy compliance
"""

from agentworld.tasks.definitions import ExpectedAction, TaskDefinition, TaskSet


def _make_payment_task(
    task_id: str,
    name: str,
    description: str,
    difficulty: str,
    agent_instruction: str,
    expected_final_states: dict,
    expected_actions: list[dict],
    required_outputs: list[str],
    initial_balances: dict[str, float] | None = None,
    estimated_steps: int = 5,
    tags: list[str] | None = None,
) -> TaskDefinition:
    """Helper to create payment task definitions."""
    initial_balances = initial_balances or {"alice": 1000.0, "bob": 500.0}

    return TaskDefinition(
        task_id=task_id,
        name=name,
        description=description,
        domain="payment",
        difficulty=difficulty,
        simulation_config={
            "name": f"Task: {name}",
            "agents": [
                {
                    "name": "Alice",
                    "agent_id": "alice",
                    "traits": {"role": "user"},
                    "background": f"A PayPal user with ${initial_balances.get('alice', 1000):.2f} balance.",
                },
                {
                    "name": "Bob",
                    "agent_id": "bob",
                    "traits": {"role": "user"},
                    "background": f"A PayPal user with ${initial_balances.get('bob', 500):.2f} balance.",
                },
            ],
            "apps": [
                {
                    "id": "paypal",
                    "config": {"initial_balance": initial_balances},
                }
            ],
            "steps": estimated_steps,
            "topology": {"type": "fully_connected"},
        },
        initial_app_states={
            "paypal": {
                agent_id: {"balance": balance, "transactions": []}
                for agent_id, balance in initial_balances.items()
            }
        },
        agent_instruction=agent_instruction,
        expected_final_states=expected_final_states,
        expected_actions=[ExpectedAction.from_dict(a) for a in expected_actions],
        required_outputs=required_outputs,
        policy_rules=["confirm_large_transfer", "verify_recipient"],
        estimated_steps=estimated_steps,
        tags=tags or ["payment"],
    )


# =============================================================================
# Easy Tasks
# =============================================================================

SIMPLE_TRANSFER = _make_payment_task(
    task_id="payment_simple_transfer",
    name="Simple Transfer",
    description="Alice transfers $50 to Bob. Basic happy-path transfer.",
    difficulty="easy",
    agent_instruction=(
        "Transfer $50 from Alice to Bob using PayPal. "
        "Confirm the transfer was successful and report the new balance."
    ),
    expected_final_states={
        "paypal": {
            "alice": {"balance": 950.0},
            "bob": {"balance": 550.0},
        }
    },
    expected_actions=[
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "transfer",
            "params": {"to": "bob", "amount": 50},
        }
    ],
    required_outputs=["transfer", "successful", "balance"],
    estimated_steps=3,
    tags=["payment", "transfer", "easy"],
)

CHECK_BALANCE = _make_payment_task(
    task_id="payment_check_balance",
    name="Check Balance",
    description="Alice checks her current balance.",
    difficulty="easy",
    agent_instruction=(
        "Check Alice's PayPal balance and report the amount."
    ),
    expected_final_states={
        "paypal": {
            "alice": {"balance": 1000.0},
            "bob": {"balance": 500.0},
        }
    },
    expected_actions=[
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "check_balance",
            "params": {},
        }
    ],
    required_outputs=["balance", "1000"],
    estimated_steps=2,
    tags=["payment", "balance", "easy"],
)


# =============================================================================
# Medium Tasks
# =============================================================================

TRANSFER_WITH_VERIFICATION = _make_payment_task(
    task_id="payment_transfer_verify",
    name="Transfer with Verification",
    description="Alice verifies balance, transfers $100 to Bob, then verifies again.",
    difficulty="medium",
    agent_instruction=(
        "First check Alice's balance to verify she has enough funds. "
        "Then transfer $100 from Alice to Bob. "
        "Finally, verify the transfer by checking both balances."
    ),
    expected_final_states={
        "paypal": {
            "alice": {"balance": 900.0},
            "bob": {"balance": 600.0},
        }
    },
    expected_actions=[
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "check_balance",
            "params": {},
            "order": 1,
        },
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "transfer",
            "params": {"to": "bob", "amount": 100},
            "order": 2,
        },
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "check_balance",
            "params": {},
            "order": 3,
            "required": False,  # Optional final verification
        },
    ],
    required_outputs=["transfer", "successful", "900"],
    estimated_steps=5,
    tags=["payment", "transfer", "verification", "medium"],
)

MULTI_PARTY_TRANSFER = _make_payment_task(
    task_id="payment_multi_party",
    name="Multi-Party Transfer",
    description="Alice sends money to Bob, then Bob sends some to Charlie.",
    difficulty="medium",
    agent_instruction=(
        "Execute two sequential transfers: "
        "1. Alice sends $200 to Bob "
        "2. Bob sends $100 to Charlie "
        "Report the final balances of all parties."
    ),
    initial_balances={"alice": 1000.0, "bob": 500.0, "charlie": 200.0},
    expected_final_states={
        "paypal": {
            "alice": {"balance": 800.0},
            "bob": {"balance": 600.0},
            "charlie": {"balance": 300.0},
        }
    },
    expected_actions=[
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "transfer",
            "params": {"to": "bob", "amount": 200},
            "order": 1,
        },
        {
            "agent_id": "bob",
            "app_id": "paypal",
            "action_name": "transfer",
            "params": {"to": "charlie", "amount": 100},
            "order": 2,
        },
    ],
    required_outputs=["alice", "800", "bob", "600", "charlie", "300"],
    estimated_steps=6,
    tags=["payment", "transfer", "multi-party", "medium"],
)

REQUEST_AND_PAY = _make_payment_task(
    task_id="payment_request_pay",
    name="Request and Pay",
    description="Bob requests money from Alice, Alice pays the request.",
    difficulty="medium",
    agent_instruction=(
        "Bob requests $75 from Alice with note 'Lunch money'. "
        "Alice then pays the request. "
        "Verify the final balances."
    ),
    expected_final_states={
        "paypal": {
            "alice": {"balance": 925.0},
            "bob": {"balance": 575.0},
        }
    },
    expected_actions=[
        {
            "agent_id": "bob",
            "app_id": "paypal",
            "action_name": "request_money",
            "params": {"from": "alice", "amount": 75},
            "order": 1,
        },
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "pay_request",
            "params": {},
            "order": 2,
        },
    ],
    required_outputs=["request", "paid", "925", "575"],
    estimated_steps=5,
    tags=["payment", "request", "medium"],
)


# =============================================================================
# Hard Tasks
# =============================================================================

INSUFFICIENT_FUNDS_HANDLING = _make_payment_task(
    task_id="payment_insufficient_funds",
    name="Insufficient Funds Handling",
    description="Alice tries to transfer more than her balance, must handle error.",
    difficulty="hard",
    agent_instruction=(
        "Alice attempts to transfer $1500 to Bob. "
        "Since Alice only has $1000, handle the insufficient funds error gracefully. "
        "Then transfer the maximum possible amount ($1000) instead. "
        "Report the outcome."
    ),
    expected_final_states={
        "paypal": {
            "alice": {"balance": 0.0},
            "bob": {"balance": 1500.0},
        }
    },
    expected_actions=[
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "transfer",
            "params": {"to": "bob", "amount": 1500},
            "order": 1,
            "required": False,  # May fail
        },
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "transfer",
            "params": {"to": "bob", "amount": 1000},
            "order": 2,
        },
    ],
    required_outputs=["insufficient", "transfer", "1000"],
    estimated_steps=6,
    tags=["payment", "error-handling", "hard"],
)

SPLIT_PAYMENT = _make_payment_task(
    task_id="payment_split",
    name="Split Payment",
    description="Alice splits a $300 payment evenly between Bob and Charlie.",
    difficulty="hard",
    agent_instruction=(
        "Alice needs to split a $300 payment evenly between Bob and Charlie. "
        "Calculate the split amount ($150 each) and execute both transfers. "
        "Verify all balances after completion."
    ),
    initial_balances={"alice": 1000.0, "bob": 200.0, "charlie": 200.0},
    expected_final_states={
        "paypal": {
            "alice": {"balance": 700.0},
            "bob": {"balance": 350.0},
            "charlie": {"balance": 350.0},
        }
    },
    expected_actions=[
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "transfer",
            "params": {"to": "bob", "amount": 150},
        },
        {
            "agent_id": "alice",
            "app_id": "paypal",
            "action_name": "transfer",
            "params": {"to": "charlie", "amount": 150},
        },
    ],
    required_outputs=["split", "150", "bob", "charlie", "700", "350"],
    estimated_steps=6,
    tags=["payment", "split", "calculation", "hard"],
)

COMPLEX_WORKFLOW = _make_payment_task(
    task_id="payment_complex_workflow",
    name="Complex Payment Workflow",
    description="Multi-step workflow: check, transfer, request, decline, transfer.",
    difficulty="hard",
    agent_instruction=(
        "Execute the following complex payment workflow: "
        "1. Alice checks her balance "
        "2. Alice transfers $100 to Bob "
        "3. Bob requests $50 from Alice "
        "4. Alice declines the request "
        "5. Alice transfers $25 to Bob as a compromise "
        "Report the final state and all actions taken."
    ),
    expected_final_states={
        "paypal": {
            "alice": {"balance": 875.0},
            "bob": {"balance": 625.0},
        }
    },
    expected_actions=[
        {"agent_id": "alice", "app_id": "paypal", "action_name": "check_balance", "order": 1},
        {"agent_id": "alice", "app_id": "paypal", "action_name": "transfer", "params": {"to": "bob", "amount": 100}, "order": 2},
        {"agent_id": "bob", "app_id": "paypal", "action_name": "request_money", "params": {"from": "alice", "amount": 50}, "order": 3},
        {"agent_id": "alice", "app_id": "paypal", "action_name": "decline_request", "order": 4},
        {"agent_id": "alice", "app_id": "paypal", "action_name": "transfer", "params": {"to": "bob", "amount": 25}, "order": 5},
    ],
    required_outputs=["declined", "compromise", "875", "625"],
    estimated_steps=10,
    tags=["payment", "workflow", "multi-step", "hard"],
)


# =============================================================================
# Scenario Collections
# =============================================================================

PAYMENT_SCENARIOS: list[TaskDefinition] = [
    # Easy
    SIMPLE_TRANSFER,
    CHECK_BALANCE,
    # Medium
    TRANSFER_WITH_VERIFICATION,
    MULTI_PARTY_TRANSFER,
    REQUEST_AND_PAY,
    # Hard
    INSUFFICIENT_FUNDS_HANDLING,
    SPLIT_PAYMENT,
    COMPLEX_WORKFLOW,
]

PAYMENT_BENCHMARK = TaskSet(
    name="payment_benchmark",
    description="Comprehensive payment domain benchmark covering easy, medium, and hard tasks",
    domain="payment",
    task_ids=[t.task_id for t in PAYMENT_SCENARIOS],
)


def get_payment_scenarios() -> list[TaskDefinition]:
    """Get all payment task scenarios.

    Returns:
        List of payment TaskDefinitions
    """
    return PAYMENT_SCENARIOS.copy()


def get_payment_scenarios_by_difficulty(difficulty: str) -> list[TaskDefinition]:
    """Get payment scenarios filtered by difficulty.

    Args:
        difficulty: 'easy', 'medium', or 'hard'

    Returns:
        Filtered list of TaskDefinitions
    """
    return [t for t in PAYMENT_SCENARIOS if t.difficulty == difficulty]
