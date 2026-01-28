"""Example dual-control tasks for τ²-bench evaluation.

Per ADR-020.1, these tasks demonstrate:
- Agent guides user who has device access
- Coordination handoffs between service_agent and customer
- Solo vs dual mode comparison

Domains: Airlines, PayPal
"""

from agentworld.tasks.dual_control import (
    DualControlTaskDefinition,
    CoordinationHandoff,
    InstructionTemplate,
)


# =============================================================================
# Instruction Templates (for handoff detection)
# =============================================================================

# Airlines Templates
SHOW_BOARDING_PASS_TEMPLATE = InstructionTemplate(
    template_id="show_boarding_pass",
    keywords=["show", "display", "open", "pull up"],
    target_keywords=["boarding pass", "boarding card", "ticket"],
    semantic_threshold=0.85,
)

CHECK_IN_TEMPLATE = InstructionTemplate(
    template_id="check_in_online",
    keywords=["check in", "check-in", "complete check-in"],
    target_keywords=["flight", "online"],
    semantic_threshold=0.85,
)

UPDATE_PREFERENCES_TEMPLATE = InstructionTemplate(
    template_id="update_preferences",
    keywords=["update", "change", "set", "modify"],
    target_keywords=["preferences", "settings", "seat preference", "meal"],
    semantic_threshold=0.80,
)

# PayPal Templates
TOGGLE_2FA_TEMPLATE = InstructionTemplate(
    template_id="toggle_two_factor",
    keywords=["enable", "disable", "turn on", "turn off", "toggle"],
    target_keywords=["two-factor", "2FA", "authentication", "security"],
    semantic_threshold=0.85,
)

SEND_MONEY_TEMPLATE = InstructionTemplate(
    template_id="send_money",
    keywords=["send", "transfer", "pay"],
    target_keywords=["money", "payment", "funds", "dollars"],
    semantic_threshold=0.85,
)

ADD_CARD_TEMPLATE = InstructionTemplate(
    template_id="add_card",
    keywords=["add", "link", "connect"],
    target_keywords=["card", "credit card", "debit card"],
    semantic_threshold=0.85,
)


# =============================================================================
# Airlines Domain Tasks
# =============================================================================

AIRLINES_SEAT_CHANGE_TASK = DualControlTaskDefinition(
    task_id="airlines_seat_change_001",
    name="Seat Change Request",
    description="Customer calls to request a seat change. Agent needs to change seat in backend while customer confirms on their app.",
    domain="airlines",
    difficulty="easy",
    simulation_config={
        "topology": "direct",
        "max_turns": 15,
    },
    agent_id="service_agent_1",
    agent_role="service_agent",
    agent_instruction="""You are an airline customer service agent. A customer is calling about their upcoming flight.

The customer wants to change their seat assignment. You have access to the backend CRM system.

Steps:
1. Look up the customer's booking using their confirmation code
2. Ask the customer what seat they would prefer
3. Change the seat in the backend system
4. Ask the customer to confirm the change shows on their mobile app
5. Verify the customer sees the updated seat assignment""",
    agent_apps=["airlines_backend"],
    agent_initial_state={
        "airlines_backend": {
            "shared": {
                "bookings": {
                    "ABC123": {
                        "passenger": "John Smith",
                        "flight": "AW789",
                        "seat": "22B",
                        "class": "economy",
                        "special_requests": [],
                    }
                },
                "flights": {
                    "AW789": {
                        "route": "SFO-JFK",
                        "departure": "2024-03-15T10:30:00",
                        "status": "on_time",
                    }
                },
            }
        }
    },
    agent_goal_state={
        "airlines_backend": {
            "shared": {
                "bookings": {
                    "ABC123": {
                        "seat": "12A",  # Changed to window seat
                    }
                }
            }
        }
    },
    user_id="customer_1",
    user_role="customer",
    user_instruction="""You are a customer with an upcoming flight. Your confirmation code is ABC123.

You want to change your seat from 22B (middle seat) to a window seat, preferably 12A.

When the service agent asks you to check your app:
1. Open your booking on the airlines app
2. Confirm whether you see the updated seat assignment
3. Report back to the agent""",
    user_apps=["airlines_app"],
    user_initial_state={
        "airlines_app": {
            "per_agent": {
                "customer_1": {
                    "my_bookings": [
                        {
                            "confirmation_code": "ABC123",
                            "flight": "AW789",
                            "seat": "22B",
                        }
                    ],
                    "preferences": {"seat": "window"},
                    "notifications": [],
                    "boarding_pass_visible": False,
                }
            }
        }
    },
    user_goal_state={
        "airlines_app": {
            "per_agent": {
                "customer_1": {
                    "my_bookings": [
                        {
                            "seat": "12A",  # Updated seat
                        }
                    ]
                }
            }
        }
    },
    required_handoffs=[
        CoordinationHandoff(
            handoff_id="confirm_seat_change",
            from_role="service_agent",
            to_role="customer",
            expected_action="view_my_trips",
            description="Agent asks customer to check their app for updated seat",
            instruction_template=InstructionTemplate(
                template_id="check_booking",
                keywords=["check", "look at", "open", "verify"],
                target_keywords=["app", "booking", "trip", "seat"],
            ),
        ),
    ],
    max_turns=15,
    expected_coordination_count=1,
    tags=["airlines", "seat_change", "easy"],
)

AIRLINES_SPECIAL_ASSISTANCE_TASK = DualControlTaskDefinition(
    task_id="airlines_special_assistance_002",
    name="Special Assistance Request",
    description="Customer needs to add wheelchair assistance. Agent adds request in backend and guides customer to update preferences.",
    domain="airlines",
    difficulty="medium",
    simulation_config={
        "topology": "direct",
        "max_turns": 20,
    },
    agent_id="service_agent_1",
    agent_role="service_agent",
    agent_instruction="""You are an airline customer service agent. A customer needs wheelchair assistance for their upcoming flight.

Steps:
1. Look up the customer's booking
2. Add the wheelchair assistance request in the backend
3. Guide the customer to update their preferences in their app
4. Ask them to enable notifications so they receive gate assistance info
5. Confirm the special request is properly recorded""",
    agent_apps=["airlines_backend"],
    agent_initial_state={
        "airlines_backend": {
            "shared": {
                "bookings": {
                    "XYZ789": {
                        "passenger": "Mary Johnson",
                        "flight": "AW456",
                        "seat": "1A",
                        "class": "first",
                        "special_requests": [],
                    }
                }
            }
        }
    },
    agent_goal_state={
        "airlines_backend": {
            "shared": {
                "bookings": {
                    "XYZ789": {
                        "special_requests": [
                            {"type": "wheelchair"}
                        ]
                    }
                }
            }
        }
    },
    user_id="customer_1",
    user_role="customer",
    user_instruction="""You are a customer who needs wheelchair assistance for your upcoming flight. Your confirmation code is XYZ789.

When the agent asks you to update your preferences:
1. Open your airline app settings
2. Update your preferences as instructed
3. Enable notifications if asked
4. Confirm the changes back to the agent""",
    user_apps=["airlines_app"],
    user_initial_state={
        "airlines_app": {
            "per_agent": {
                "customer_1": {
                    "my_bookings": [
                        {
                            "confirmation_code": "XYZ789",
                            "flight": "AW456",
                        }
                    ],
                    "preferences": {},
                    "notifications": [],
                }
            }
        }
    },
    user_goal_state={
        "airlines_app": {
            "per_agent": {
                "customer_1": {
                    "preferences": {
                        "notifications_enabled": True,
                    }
                }
            }
        }
    },
    required_handoffs=[
        CoordinationHandoff(
            handoff_id="update_preferences",
            from_role="service_agent",
            to_role="customer",
            expected_action="update_preferences",
            description="Agent guides customer to update app preferences",
            instruction_template=UPDATE_PREFERENCES_TEMPLATE,
        ),
    ],
    max_turns=20,
    expected_coordination_count=2,
    tags=["airlines", "special_assistance", "medium"],
)


# =============================================================================
# PayPal Domain Tasks
# =============================================================================

PAYPAL_ENABLE_2FA_TASK = DualControlTaskDefinition(
    task_id="paypal_enable_2fa_001",
    name="Enable Two-Factor Authentication",
    description="Customer calls support to enable 2FA. Agent verifies identity and guides customer through enabling 2FA on their app.",
    domain="paypal",
    difficulty="easy",
    simulation_config={
        "topology": "direct",
        "max_turns": 15,
    },
    agent_id="service_agent_1",
    agent_role="service_agent",
    agent_instruction="""You are a PayPal customer support agent. A customer wants to enable two-factor authentication for security.

Steps:
1. Look up the customer's account to verify their identity
2. Check if they have any account limitations
3. Guide them to enable 2FA in their PayPal app
4. Ask them to confirm 2FA is now enabled
5. Verify the change in the backend""",
    agent_apps=["paypal_backend"],
    agent_initial_state={
        "paypal_backend": {
            "shared": {
                "accounts": {
                    "user_12345": {
                        "email": "customer@example.com",
                        "status": "active",
                        "limitations": [],
                        "two_factor_enabled": False,
                    }
                },
                "holds": {},
                "disputes": {},
            }
        }
    },
    agent_goal_state={},  # Agent's backend view doesn't change
    user_id="customer_1",
    user_role="customer",
    user_instruction="""You are a PayPal customer who wants to enable two-factor authentication for better security.

Your account email is customer@example.com.

When the support agent guides you:
1. Open your PayPal app
2. Navigate to security settings
3. Enable two-factor authentication
4. Confirm the change to the agent""",
    user_apps=["paypal_app"],
    user_initial_state={
        "paypal_app": {
            "per_agent": {
                "customer_1": {
                    "balance": 250.00,
                    "recent_transactions": [],
                    "linked_cards": [],
                    "notifications": [],
                    "two_factor_enabled": False,
                }
            }
        }
    },
    user_goal_state={
        "paypal_app": {
            "per_agent": {
                "customer_1": {
                    "two_factor_enabled": True,
                }
            }
        }
    },
    required_handoffs=[
        CoordinationHandoff(
            handoff_id="enable_2fa",
            from_role="service_agent",
            to_role="customer",
            expected_action="toggle_two_factor",
            description="Agent guides customer to enable 2FA in their app",
            instruction_template=TOGGLE_2FA_TEMPLATE,
        ),
    ],
    max_turns=15,
    expected_coordination_count=1,
    tags=["paypal", "security", "2fa", "easy"],
)

PAYPAL_DISPUTE_RESOLUTION_TASK = DualControlTaskDefinition(
    task_id="paypal_dispute_001",
    name="Transaction Dispute Resolution",
    description="Customer disputes a transaction. Agent investigates and may issue refund while guiding customer through their app.",
    domain="paypal",
    difficulty="hard",
    simulation_config={
        "topology": "direct",
        "max_turns": 25,
    },
    agent_id="service_agent_1",
    agent_role="service_agent",
    agent_instruction="""You are a PayPal dispute resolution specialist. A customer is disputing a transaction they don't recognize.

Steps:
1. Look up the customer's account and transaction history
2. Find the disputed transaction (transaction ID: TXN_98765)
3. Create a dispute case in the system
4. Ask the customer to check their recent activity in their app to verify they don't recognize it
5. Based on the investigation, issue a refund if warranted
6. Ask the customer to verify the refund appears in their account""",
    agent_apps=["paypal_backend"],
    agent_initial_state={
        "paypal_backend": {
            "shared": {
                "accounts": {
                    "user_12345": {
                        "email": "customer@example.com",
                        "status": "active",
                        "balance": 500.00,
                    }
                },
                "transactions": [
                    {
                        "id": "TXN_98765",
                        "type": "payment",
                        "amount": 149.99,
                        "merchant": "Unknown Merchant",
                        "timestamp": "2024-03-10T14:22:00",
                    }
                ],
                "disputes": {},
                "holds": {},
            }
        }
    },
    agent_goal_state={
        "paypal_backend": {
            "shared": {
                "disputes": {
                    # A dispute should be created and resolved
                }
            }
        }
    },
    user_id="customer_1",
    user_role="customer",
    user_instruction="""You are a PayPal customer who noticed a suspicious transaction of $149.99 from "Unknown Merchant" that you don't recognize.

Transaction ID is TXN_98765.

When the support agent asks:
1. Check your recent activity in your PayPal app
2. Confirm you don't recognize this transaction
3. Verify when refund is processed""",
    user_apps=["paypal_app"],
    user_initial_state={
        "paypal_app": {
            "per_agent": {
                "customer_1": {
                    "balance": 350.01,  # After the suspicious charge
                    "recent_transactions": [
                        {
                            "id": "TXN_98765",
                            "type": "payment",
                            "amount": -149.99,
                            "merchant": "Unknown Merchant",
                        }
                    ],
                    "linked_cards": [
                        {"last4": "4567", "type": "visa"}
                    ],
                    "notifications": [],
                    "two_factor_enabled": True,
                }
            }
        }
    },
    user_goal_state={
        "paypal_app": {
            "per_agent": {
                "customer_1": {
                    "balance": 500.00,  # Refunded
                }
            }
        }
    },
    required_handoffs=[
        CoordinationHandoff(
            handoff_id="verify_transaction",
            from_role="service_agent",
            to_role="customer",
            expected_action="view_recent_activity",
            description="Agent asks customer to verify transaction in their app",
            instruction_template=InstructionTemplate(
                template_id="check_activity",
                keywords=["check", "look at", "review", "verify"],
                target_keywords=["activity", "transactions", "recent", "history"],
            ),
        ),
        CoordinationHandoff(
            handoff_id="confirm_refund",
            from_role="service_agent",
            to_role="customer",
            expected_action="check_balance",
            description="Agent asks customer to verify refund appeared",
            instruction_template=InstructionTemplate(
                template_id="check_balance",
                keywords=["check", "verify", "confirm"],
                target_keywords=["balance", "refund", "account"],
            ),
        ),
    ],
    max_turns=25,
    expected_coordination_count=2,
    tags=["paypal", "dispute", "refund", "hard"],
)

PAYPAL_ADD_CARD_TASK = DualControlTaskDefinition(
    task_id="paypal_add_card_001",
    name="Link New Payment Card",
    description="Customer wants to add a new card. Agent verifies account and guides customer through adding card in their app.",
    domain="paypal",
    difficulty="easy",
    simulation_config={
        "topology": "direct",
        "max_turns": 15,
    },
    agent_id="service_agent_1",
    agent_role="service_agent",
    agent_instruction="""You are a PayPal support agent. A customer wants to add a new credit card to their account.

Steps:
1. Verify the customer's account
2. Check for any account limitations that might prevent adding a card
3. Guide the customer to add the card through their PayPal app
4. Ask them to confirm the card was added successfully""",
    agent_apps=["paypal_backend"],
    agent_initial_state={
        "paypal_backend": {
            "shared": {
                "accounts": {
                    "user_67890": {
                        "email": "newuser@example.com",
                        "status": "active",
                        "limitations": [],
                    }
                }
            }
        }
    },
    agent_goal_state={},
    user_id="customer_1",
    user_role="customer",
    user_instruction="""You are a PayPal customer who wants to add a new Visa credit card ending in 1234 to your account.

When the support agent guides you:
1. Open your PayPal app
2. Go to linked cards section
3. Add your new card with expiry 12/26
4. Confirm the card was added successfully""",
    user_apps=["paypal_app"],
    user_initial_state={
        "paypal_app": {
            "per_agent": {
                "customer_1": {
                    "balance": 100.00,
                    "linked_cards": [],
                    "notifications": [],
                }
            }
        }
    },
    user_goal_state={
        "paypal_app": {
            "per_agent": {
                "customer_1": {
                    "linked_cards": [
                        {"last4": "1234", "type": "visa", "expiry": "12/26"}
                    ]
                }
            }
        }
    },
    required_handoffs=[
        CoordinationHandoff(
            handoff_id="add_new_card",
            from_role="service_agent",
            to_role="customer",
            expected_action="add_card",
            description="Agent guides customer to add card in app",
            instruction_template=ADD_CARD_TEMPLATE,
        ),
    ],
    max_turns=15,
    expected_coordination_count=1,
    tags=["paypal", "card", "easy"],
)


# =============================================================================
# Task Collections
# =============================================================================

AIRLINES_TASKS = [
    AIRLINES_SEAT_CHANGE_TASK,
    AIRLINES_SPECIAL_ASSISTANCE_TASK,
]

PAYPAL_TASKS = [
    PAYPAL_ENABLE_2FA_TASK,
    PAYPAL_DISPUTE_RESOLUTION_TASK,
    PAYPAL_ADD_CARD_TASK,
]

ALL_DUAL_CONTROL_TASKS = AIRLINES_TASKS + PAYPAL_TASKS


def get_tasks_by_domain(domain: str) -> list[DualControlTaskDefinition]:
    """Get all tasks for a specific domain.

    Args:
        domain: Domain name (airlines, paypal)

    Returns:
        List of task definitions
    """
    domain_tasks = {
        "airlines": AIRLINES_TASKS,
        "paypal": PAYPAL_TASKS,
    }
    return domain_tasks.get(domain.lower(), [])


def get_tasks_by_difficulty(difficulty: str) -> list[DualControlTaskDefinition]:
    """Get all tasks of a specific difficulty.

    Args:
        difficulty: easy, medium, or hard

    Returns:
        List of task definitions
    """
    return [t for t in ALL_DUAL_CONTROL_TASKS if t.difficulty == difficulty]


def get_task_by_id(task_id: str) -> DualControlTaskDefinition | None:
    """Get a specific task by ID.

    Args:
        task_id: Task ID

    Returns:
        Task definition or None
    """
    for task in ALL_DUAL_CONTROL_TASKS:
        if task.task_id == task_id:
            return task
    return None
