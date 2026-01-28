"""Dual-control example apps for τ²-bench evaluation.

Per ADR-020.1, these apps demonstrate role-restricted access:
- Service agents have backend/CRM access
- Customers have device/frontend access

Domains: Airlines, PayPal
"""

# =============================================================================
# Airlines Domain - Dual Control Apps
# =============================================================================

AIRLINES_BACKEND = {
    "app_id": "airlines_backend",
    "name": "Airlines Backend CRM",
    "description": "Backend system for airline agents to manage bookings, view passenger info, and process changes",
    "category": "custom",
    "icon": "🖥️",
    "access_type": "role_restricted",
    "allowed_roles": ["service_agent"],
    "state_type": "shared",
    "state_schema": [
        {"name": "bookings", "type": "object", "default": {}, "per_agent": False},
        {"name": "passengers", "type": "object", "default": {}, "per_agent": False},
        {"name": "flights", "type": "object", "default": {}, "per_agent": False},
    ],
    "initial_config": {
        "airline_code": "AW",
    },
    "actions": [
        {
            "name": "lookup_booking",
            "description": "Look up a booking by confirmation code",
            "toolType": "read",
            "parameters": {
                "confirmation_code": {
                    "type": "string",
                    "required": True,
                    "description": "6-character confirmation code",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "len(params.confirmation_code) == 6",
                    "error_message": "Confirmation code must be 6 characters",
                },
                {
                    "type": "branch",
                    "condition": "shared.bookings[params.confirmation_code] != null",
                    "then": [
                        {
                            "type": "return",
                            "value": {
                                "booking": "shared.bookings[params.confirmation_code]",
                                "found": True,
                            },
                        },
                    ],
                    "else": [
                        {
                            "type": "return",
                            "value": {"found": False, "message": "Booking not found"},
                        },
                    ],
                },
            ],
        },
        {
            "name": "lookup_passenger",
            "description": "Look up passenger details by ID or name",
            "toolType": "read",
            "parameters": {
                "passenger_id": {
                    "type": "string",
                    "required": False,
                    "description": "Passenger ID",
                },
                "last_name": {
                    "type": "string",
                    "required": False,
                    "description": "Passenger last name",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.passenger_id != null || params.last_name != null",
                    "error_message": "Provide passenger_id or last_name",
                },
                {
                    "type": "return",
                    "value": {"passengers": "shared.passengers"},
                },
            ],
        },
        {
            "name": "check_flight_status",
            "description": "Check status of a flight",
            "toolType": "read",
            "parameters": {
                "flight_number": {
                    "type": "string",
                    "required": True,
                    "description": "Flight number (e.g., AW123)",
                },
            },
            "logic": [
                {
                    "type": "branch",
                    "condition": "shared.flights[params.flight_number] != null",
                    "then": [
                        {
                            "type": "return",
                            "value": {"flight": "shared.flights[params.flight_number]"},
                        },
                    ],
                    "else": [
                        {
                            "type": "return",
                            "value": {"found": False},
                        },
                    ],
                },
            ],
        },
        {
            "name": "change_seat",
            "description": "Change seat assignment for a booking",
            "toolType": "write",
            "parameters": {
                "confirmation_code": {
                    "type": "string",
                    "required": True,
                    "description": "Booking confirmation code",
                },
                "new_seat": {
                    "type": "string",
                    "required": True,
                    "description": "New seat number (e.g., 12A)",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.bookings[params.confirmation_code] != null",
                    "error_message": "Booking not found",
                },
                {
                    "type": "update",
                    "target": "shared.bookings[params.confirmation_code].seat",
                    "operation": "set",
                    "value": "params.new_seat",
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "new_seat": "params.new_seat",
                        "message": "Seat changed successfully",
                    },
                },
            ],
        },
        {
            "name": "add_special_request",
            "description": "Add special assistance or meal request",
            "toolType": "write",
            "parameters": {
                "confirmation_code": {
                    "type": "string",
                    "required": True,
                    "description": "Booking confirmation code",
                },
                "request_type": {
                    "type": "string",
                    "required": True,
                    "description": "Type: wheelchair, meal, bassinet, etc.",
                },
                "details": {
                    "type": "string",
                    "required": False,
                    "description": "Additional details",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.bookings[params.confirmation_code] != null",
                    "error_message": "Booking not found",
                },
                {
                    "type": "update",
                    "target": "shared.bookings[params.confirmation_code].special_requests",
                    "operation": "append",
                    "value": {
                        "type": "params.request_type",
                        "details": "params.details",
                        "added_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {"success": True, "message": "Special request added"},
                },
            ],
        },
        {
            "name": "process_refund",
            "description": "Process refund for a cancelled booking",
            "toolType": "write",
            "parameters": {
                "confirmation_code": {
                    "type": "string",
                    "required": True,
                    "description": "Booking confirmation code",
                },
                "refund_amount": {
                    "type": "number",
                    "required": True,
                    "description": "Amount to refund",
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Refund reason",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.bookings[params.confirmation_code] != null",
                    "error_message": "Booking not found",
                },
                {
                    "type": "validate",
                    "condition": "params.refund_amount > 0",
                    "error_message": "Refund amount must be positive",
                },
                {
                    "type": "update",
                    "target": "shared.bookings[params.confirmation_code].status",
                    "operation": "set",
                    "value": "refunded",
                },
                {
                    "type": "update",
                    "target": "shared.bookings[params.confirmation_code].refund",
                    "operation": "set",
                    "value": {
                        "amount": "params.refund_amount",
                        "reason": "params.reason",
                        "processed_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "refund_id": "generate_id()",
                        "amount": "params.refund_amount",
                    },
                },
            ],
        },
    ],
}

AIRLINES_APP = {
    "app_id": "airlines_app",
    "name": "Airlines Mobile App",
    "description": "Customer-facing mobile app for checking flights, viewing boarding pass, and managing preferences",
    "category": "custom",
    "icon": "✈️",
    "access_type": "role_restricted",
    "allowed_roles": ["customer"],
    "state_type": "per_agent",
    "state_schema": [
        {"name": "my_bookings", "type": "array", "default": [], "per_agent": True},
        {"name": "preferences", "type": "object", "default": {}, "per_agent": True},
        {"name": "notifications", "type": "array", "default": [], "per_agent": True},
        {"name": "boarding_pass_visible", "type": "boolean", "default": False, "per_agent": True},
    ],
    "actions": [
        {
            "name": "view_my_trips",
            "description": "View my upcoming trips",
            "toolType": "read",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {"bookings": "agent.my_bookings"},
                },
            ],
        },
        {
            "name": "show_boarding_pass",
            "description": "Display boarding pass on screen",
            "toolType": "read",
            "parameters": {
                "confirmation_code": {
                    "type": "string",
                    "required": True,
                    "description": "Booking confirmation code",
                },
            },
            "logic": [
                {
                    "type": "update",
                    "target": "agent.boarding_pass_visible",
                    "operation": "set",
                    "value": True,
                },
                {
                    "type": "return",
                    "value": {
                        "displayed": True,
                        "confirmation_code": "params.confirmation_code",
                        "message": "Boarding pass is now displayed",
                    },
                },
            ],
        },
        {
            "name": "hide_boarding_pass",
            "description": "Hide boarding pass from screen",
            "toolType": "write",
            "parameters": {},
            "logic": [
                {
                    "type": "update",
                    "target": "agent.boarding_pass_visible",
                    "operation": "set",
                    "value": False,
                },
                {
                    "type": "return",
                    "value": {"hidden": True},
                },
            ],
        },
        {
            "name": "update_preferences",
            "description": "Update travel preferences",
            "toolType": "write",
            "parameters": {
                "seat_preference": {
                    "type": "string",
                    "required": False,
                    "description": "window, aisle, or middle",
                },
                "meal_preference": {
                    "type": "string",
                    "required": False,
                    "description": "regular, vegetarian, vegan, kosher, halal",
                },
                "notifications_enabled": {
                    "type": "boolean",
                    "required": False,
                    "description": "Enable flight notifications",
                },
            },
            "logic": [
                {
                    "type": "branch",
                    "condition": "params.seat_preference != null",
                    "then": [
                        {
                            "type": "update",
                            "target": "agent.preferences.seat",
                            "operation": "set",
                            "value": "params.seat_preference",
                        },
                    ],
                },
                {
                    "type": "branch",
                    "condition": "params.meal_preference != null",
                    "then": [
                        {
                            "type": "update",
                            "target": "agent.preferences.meal",
                            "operation": "set",
                            "value": "params.meal_preference",
                        },
                    ],
                },
                {
                    "type": "return",
                    "value": {"preferences": "agent.preferences"},
                },
            ],
        },
        {
            "name": "check_in_online",
            "description": "Check in for a flight online",
            "toolType": "write",
            "parameters": {
                "confirmation_code": {
                    "type": "string",
                    "required": True,
                    "description": "Booking confirmation code",
                },
            },
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "checked_in": True,
                        "confirmation_code": "params.confirmation_code",
                        "message": "You are now checked in. Boarding pass available.",
                    },
                },
            ],
        },
        {
            "name": "view_notifications",
            "description": "View flight notifications and alerts",
            "toolType": "read",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {"notifications": "agent.notifications"},
                },
            ],
        },
    ],
}


# =============================================================================
# PayPal Domain - Dual Control Apps
# =============================================================================

PAYPAL_BACKEND = {
    "app_id": "paypal_backend",
    "name": "PayPal Support Console",
    "description": "Backend console for PayPal support agents to view accounts, transactions, and resolve disputes",
    "category": "payment",
    "icon": "🏦",
    "access_type": "role_restricted",
    "allowed_roles": ["service_agent"],
    "state_type": "shared",
    "state_schema": [
        {"name": "accounts", "type": "object", "default": {}, "per_agent": False},
        {"name": "transactions", "type": "array", "default": [], "per_agent": False},
        {"name": "disputes", "type": "object", "default": {}, "per_agent": False},
        {"name": "holds", "type": "object", "default": {}, "per_agent": False},
    ],
    "actions": [
        {
            "name": "lookup_account",
            "description": "Look up account by email or account ID",
            "toolType": "read",
            "parameters": {
                "email": {
                    "type": "string",
                    "required": False,
                    "description": "Account email",
                },
                "account_id": {
                    "type": "string",
                    "required": False,
                    "description": "Account ID",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.email != null || params.account_id != null",
                    "error_message": "Provide email or account_id",
                },
                {
                    "type": "return",
                    "value": {"accounts": "shared.accounts"},
                },
            ],
        },
        {
            "name": "view_transaction_history",
            "description": "View transaction history for an account",
            "toolType": "read",
            "parameters": {
                "account_id": {
                    "type": "string",
                    "required": True,
                    "description": "Account ID",
                },
                "limit": {
                    "type": "number",
                    "required": False,
                    "default": 10,
                    "description": "Number of transactions to return",
                },
            },
            "logic": [
                {
                    "type": "return",
                    "value": {"transactions": "shared.transactions"},
                },
            ],
        },
        {
            "name": "check_account_status",
            "description": "Check if account has any holds or limitations",
            "toolType": "read",
            "parameters": {
                "account_id": {
                    "type": "string",
                    "required": True,
                    "description": "Account ID",
                },
            },
            "logic": [
                {
                    "type": "branch",
                    "condition": "shared.accounts[params.account_id] != null",
                    "then": [
                        {
                            "type": "return",
                            "value": {
                                "status": "shared.accounts[params.account_id].status",
                                "holds": "shared.holds[params.account_id]",
                                "limitations": "shared.accounts[params.account_id].limitations",
                            },
                        },
                    ],
                    "else": [
                        {
                            "type": "return",
                            "value": {"found": False},
                        },
                    ],
                },
            ],
        },
        {
            "name": "release_hold",
            "description": "Release a payment hold",
            "toolType": "write",
            "parameters": {
                "hold_id": {
                    "type": "string",
                    "required": True,
                    "description": "Hold ID to release",
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Reason for releasing hold",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.holds[params.hold_id] != null",
                    "error_message": "Hold not found",
                },
                {
                    "type": "update",
                    "target": "shared.holds[params.hold_id].status",
                    "operation": "set",
                    "value": "released",
                },
                {
                    "type": "update",
                    "target": "shared.holds[params.hold_id].released_at",
                    "operation": "set",
                    "value": "timestamp()",
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "message": "Hold released successfully",
                    },
                },
            ],
        },
        {
            "name": "create_dispute",
            "description": "Create a dispute case for a transaction",
            "toolType": "write",
            "parameters": {
                "transaction_id": {
                    "type": "string",
                    "required": True,
                    "description": "Transaction ID",
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Dispute reason",
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Disputed amount",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.amount > 0",
                    "error_message": "Amount must be positive",
                },
                {
                    "type": "update",
                    "target": "shared.disputes[generate_id()]",
                    "operation": "set",
                    "value": {
                        "transaction_id": "params.transaction_id",
                        "reason": "params.reason",
                        "amount": "params.amount",
                        "status": "open",
                        "created_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "dispute_id": "generate_id()",
                        "message": "Dispute created",
                    },
                },
            ],
        },
        {
            "name": "resolve_dispute",
            "description": "Resolve a dispute case",
            "toolType": "write",
            "parameters": {
                "dispute_id": {
                    "type": "string",
                    "required": True,
                    "description": "Dispute ID",
                },
                "resolution": {
                    "type": "string",
                    "required": True,
                    "description": "Resolution: refund, denied, partial_refund",
                },
                "refund_amount": {
                    "type": "number",
                    "required": False,
                    "description": "Refund amount if applicable",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.disputes[params.dispute_id] != null",
                    "error_message": "Dispute not found",
                },
                {
                    "type": "update",
                    "target": "shared.disputes[params.dispute_id].status",
                    "operation": "set",
                    "value": "resolved",
                },
                {
                    "type": "update",
                    "target": "shared.disputes[params.dispute_id].resolution",
                    "operation": "set",
                    "value": "params.resolution",
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "resolution": "params.resolution",
                    },
                },
            ],
        },
        {
            "name": "issue_refund",
            "description": "Issue a refund for a transaction",
            "toolType": "write",
            "parameters": {
                "transaction_id": {
                    "type": "string",
                    "required": True,
                    "description": "Original transaction ID",
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Refund amount",
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Refund reason",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.amount > 0",
                    "error_message": "Amount must be positive",
                },
                {
                    "type": "update",
                    "target": "shared.transactions",
                    "operation": "append",
                    "value": {
                        "id": "generate_id()",
                        "type": "refund",
                        "original_transaction": "params.transaction_id",
                        "amount": "params.amount",
                        "reason": "params.reason",
                        "timestamp": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "refund_id": "generate_id()",
                        "amount": "params.amount",
                    },
                },
            ],
        },
    ],
}

PAYPAL_APP = {
    "app_id": "paypal_app",
    "name": "PayPal Mobile App",
    "description": "Customer-facing PayPal app for payments, balance, and settings",
    "category": "payment",
    "icon": "💳",
    "access_type": "role_restricted",
    "allowed_roles": ["customer"],
    "state_type": "per_agent",
    "state_schema": [
        {"name": "balance", "type": "number", "default": 0, "per_agent": True},
        {"name": "recent_transactions", "type": "array", "default": [], "per_agent": True},
        {"name": "linked_cards", "type": "array", "default": [], "per_agent": True},
        {"name": "notifications", "type": "array", "default": [], "per_agent": True},
        {"name": "two_factor_enabled", "type": "boolean", "default": False, "per_agent": True},
    ],
    "actions": [
        {
            "name": "check_balance",
            "description": "View current PayPal balance",
            "toolType": "read",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {"balance": "agent.balance"},
                },
            ],
        },
        {
            "name": "view_recent_activity",
            "description": "View recent transactions",
            "toolType": "read",
            "parameters": {
                "limit": {
                    "type": "number",
                    "required": False,
                    "default": 10,
                    "description": "Number of transactions",
                },
            },
            "logic": [
                {
                    "type": "return",
                    "value": {"transactions": "agent.recent_transactions"},
                },
            ],
        },
        {
            "name": "send_money",
            "description": "Send money to another user",
            "toolType": "write",
            "parameters": {
                "recipient": {
                    "type": "string",
                    "required": True,
                    "description": "Recipient email or phone",
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "min_value": 0.01,
                    "description": "Amount to send",
                },
                "note": {
                    "type": "string",
                    "required": False,
                    "description": "Payment note",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.amount > 0",
                    "error_message": "Amount must be positive",
                },
                {
                    "type": "validate",
                    "condition": "agent.balance >= params.amount",
                    "error_message": "Insufficient balance",
                },
                {
                    "type": "update",
                    "target": "agent.balance",
                    "operation": "subtract",
                    "value": "params.amount",
                },
                {
                    "type": "update",
                    "target": "agent.recent_transactions",
                    "operation": "append",
                    "value": {
                        "type": "sent",
                        "to": "params.recipient",
                        "amount": "params.amount",
                        "note": "params.note",
                        "timestamp": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "transaction_id": "generate_id()",
                        "new_balance": "agent.balance",
                    },
                },
            ],
        },
        {
            "name": "request_money",
            "description": "Request money from another user",
            "toolType": "write",
            "parameters": {
                "from_user": {
                    "type": "string",
                    "required": True,
                    "description": "User to request from",
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "min_value": 0.01,
                    "description": "Amount to request",
                },
                "note": {
                    "type": "string",
                    "required": False,
                    "description": "Request note",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.amount > 0",
                    "error_message": "Amount must be positive",
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "request_id": "generate_id()",
                        "message": "Request sent",
                    },
                },
            ],
        },
        {
            "name": "toggle_two_factor",
            "description": "Enable or disable two-factor authentication",
            "toolType": "write",
            "parameters": {
                "enable": {
                    "type": "boolean",
                    "required": True,
                    "description": "Enable (true) or disable (false)",
                },
            },
            "logic": [
                {
                    "type": "update",
                    "target": "agent.two_factor_enabled",
                    "operation": "set",
                    "value": "params.enable",
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "two_factor_enabled": "params.enable",
                    },
                },
            ],
        },
        {
            "name": "view_linked_cards",
            "description": "View linked debit/credit cards",
            "toolType": "read",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {"cards": "agent.linked_cards"},
                },
            ],
        },
        {
            "name": "add_card",
            "description": "Link a new card to the account",
            "toolType": "write",
            "parameters": {
                "card_number_last4": {
                    "type": "string",
                    "required": True,
                    "description": "Last 4 digits of card",
                },
                "card_type": {
                    "type": "string",
                    "required": True,
                    "description": "visa, mastercard, amex, discover",
                },
                "expiry": {
                    "type": "string",
                    "required": True,
                    "description": "Expiry date MM/YY",
                },
            },
            "logic": [
                {
                    "type": "update",
                    "target": "agent.linked_cards",
                    "operation": "append",
                    "value": {
                        "id": "generate_id()",
                        "last4": "params.card_number_last4",
                        "type": "params.card_type",
                        "expiry": "params.expiry",
                        "added_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {"success": True, "message": "Card added"},
                },
            ],
        },
        {
            "name": "remove_card",
            "description": "Remove a linked card",
            "toolType": "write",
            "parameters": {
                "card_id": {
                    "type": "string",
                    "required": True,
                    "description": "Card ID to remove",
                },
            },
            "logic": [
                {
                    "type": "return",
                    "value": {"success": True, "message": "Card removed"},
                },
            ],
        },
        {
            "name": "view_notifications",
            "description": "View account notifications",
            "toolType": "read",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {"notifications": "agent.notifications"},
                },
            ],
        },
    ],
}


# =============================================================================
# Dual Control App Collections
# =============================================================================

# Import Emirates apps
from agentworld.apps.evaluation.emirates_apps import EMIRATES_BACKEND, EMIRATES_APP

DUAL_CONTROL_APPS = {
    # Airlines
    "airlines_backend": AIRLINES_BACKEND,
    "airlines_app": AIRLINES_APP,
    # PayPal
    "paypal_backend": PAYPAL_BACKEND,
    "paypal_app": PAYPAL_APP,
    # Emirates
    "emirates_backend": EMIRATES_BACKEND,
    "emirates_app": EMIRATES_APP,
}


def get_dual_control_apps() -> dict[str, dict]:
    """Get all dual-control app definitions.

    Returns:
        Dictionary of dual-control app definitions
    """
    return DUAL_CONTROL_APPS.copy()


def get_dual_control_app(app_id: str) -> dict | None:
    """Get a specific dual-control app definition.

    Args:
        app_id: App ID

    Returns:
        App definition or None
    """
    return DUAL_CONTROL_APPS.get(app_id)


def get_apps_by_domain(domain: str) -> list[dict]:
    """Get all apps for a specific domain.

    Args:
        domain: Domain name (airlines, paypal)

    Returns:
        List of app definitions for that domain
    """
    domain_prefixes = {
        "airlines": ["airlines_backend", "airlines_app"],
        "paypal": ["paypal_backend", "paypal_app"],
    }

    app_ids = domain_prefixes.get(domain.lower(), [])
    return [DUAL_CONTROL_APPS[app_id] for app_id in app_ids if app_id in DUAL_CONTROL_APPS]


def get_service_agent_apps() -> list[dict]:
    """Get all apps accessible by service agents.

    Returns:
        List of backend/CRM apps
    """
    return [
        app for app in DUAL_CONTROL_APPS.values()
        if "service_agent" in app.get("allowed_roles", [])
    ]


def get_customer_apps() -> list[dict]:
    """Get all apps accessible by customers.

    Returns:
        List of customer-facing apps
    """
    return [
        app for app in DUAL_CONTROL_APPS.values()
        if "customer" in app.get("allowed_roles", [])
    ]
