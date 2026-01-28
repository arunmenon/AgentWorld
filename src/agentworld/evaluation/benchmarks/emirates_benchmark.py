"""Emirates pass^k targets and policy rules.

This module defines evaluation targets for Emirates tasks:
- Pass^k expected scores for each task
- Policy rules for compliance checking

Use with the existing TaskRunner for evaluation.
"""

from agentworld.tasks.definitions import PolicyRule


# =============================================================================
# Pass^k Targets
# =============================================================================

# Expected pass^k scores for each task
# Format: {task_id: {pass_1: float, pass_4: float, pass_8: float}}
EMIRATES_PASS_K_TARGETS = {
    # Easy tasks - higher expected success rates
    "emirates_chauffeur_001": {
        "pass_1": 0.90,
        "pass_4": 0.75,
        "pass_8": 0.60,
    },
    "emirates_lounge_001": {
        "pass_1": 0.95,
        "pass_4": 0.85,
        "pass_8": 0.70,
    },
    # Medium tasks - moderate success rates
    "emirates_skywards_redemption_001": {
        "pass_1": 0.80,
        "pass_4": 0.60,
        "pass_8": 0.45,
    },
    "emirates_icoupon_001": {
        "pass_1": 0.85,
        "pass_4": 0.65,
        "pass_8": 0.50,
    },
    # Hard tasks - lower success rates
    "emirates_baggage_claim_001": {
        "pass_1": 0.70,
        "pass_4": 0.45,
        "pass_8": 0.30,
    },
    "emirates_missed_connection_001": {
        "pass_1": 0.65,
        "pass_4": 0.40,
        "pass_8": 0.25,
    },
}


# =============================================================================
# Policy Rules for Emirates Domain
# =============================================================================

EMIRATES_POLICY_RULES = [
    PolicyRule(
        rule_id="emirates_chauffeur_eligibility",
        name="Chauffeur Service Eligibility",
        category="eligibility",
        domain="emirates",
        trigger_actions=["book_chauffeur"],
        conditions=[
            {"field": "booking.cabin_class", "operator": "in", "value": ["first", "business"]},
        ],
        requirements=[
            "Verify passenger is traveling First or Business class",
        ],
        severity="error",
    ),
    PolicyRule(
        rule_id="emirates_lounge_eligibility",
        name="Lounge Access Eligibility",
        category="eligibility",
        domain="emirates",
        trigger_actions=["issue_lounge_pass"],
        conditions=[
            {"field": "booking.cabin_class", "operator": "in", "value": ["first", "business"]},
        ],
        requirements=[
            "Verify Business or First class ticket",
            "Maximum 2 guest passes per passenger",
        ],
        severity="error",
    ),
    PolicyRule(
        rule_id="emirates_miles_redemption_balance",
        name="Miles Redemption Balance Check",
        category="limit",
        domain="emirates",
        trigger_actions=["process_miles_redemption"],
        requirements=[
            "Verify sufficient miles balance before redemption",
        ],
        severity="error",
    ),
    PolicyRule(
        rule_id="emirates_delay_compensation",
        name="Delay Compensation Thresholds",
        category="eligibility",
        domain="emirates",
        trigger_actions=["issue_icoupon"],
        conditions=[
            {"field": "flight.delay_hours", "operator": "gte", "value": 4},
        ],
        requirements=[
            "Delays over 4 hours: Meal voucher + lounge access",
        ],
        severity="warning",
    ),
    PolicyRule(
        rule_id="emirates_icoupon_limits",
        name="iCoupon Amount Limits",
        category="limit",
        domain="emirates",
        trigger_actions=["issue_icoupon"],
        conditions=[
            {"field": "params.amount", "operator": "lte", "value": 500},
        ],
        requirements=[
            "Maximum single iCoupon: $500 USD",
        ],
        severity="error",
    ),
    PolicyRule(
        rule_id="emirates_rebooking_cabin_retention",
        name="Rebooking Cabin Class Retention",
        category="confirmation",
        domain="emirates",
        trigger_actions=["rebook_passenger"],
        requirements=[
            "Maintain original cabin class when possible",
            "Confirm new itinerary with passenger",
        ],
        severity="warning",
    ),
]


def get_emirates_pass_k_targets() -> dict:
    """Get pass^k targets for Emirates tasks."""
    return EMIRATES_PASS_K_TARGETS.copy()


def get_emirates_policy_rules() -> list[PolicyRule]:
    """Get policy rules for Emirates domain."""
    return EMIRATES_POLICY_RULES.copy()
