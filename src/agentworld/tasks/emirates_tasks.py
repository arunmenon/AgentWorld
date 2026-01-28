"""Emirates airline task definitions for evaluation.

This module defines task scenarios for Emirates airline simulations:
- Easy: Chauffeur booking, lounge access
- Medium: Skywards miles redemption, iCoupon compensation
- Hard: Baggage claim, missed connection rebooking

Tasks follow the dual-control pattern where a service agent guides
a customer through using their Emirates mobile app.
"""

from agentworld.tasks.definitions import TaskDefinition, ExpectedAction

# =============================================================================
# Initial State Templates
# =============================================================================

def get_first_class_booking_state() -> dict:
    """Get initial state for a First Class booking scenario."""
    return {
        "emirates_backend": {
            "shared": {
                "bookings": {
                    "ABC123": {
                        "pnr": "ABC123",
                        "passenger_name": "Robert Sterling",
                        "cabin_class": "first",
                        "original_cabin": "first",
                        "flight_number": "EK201",
                        "origin": "DXB",
                        "destination": "JFK",
                        "departure_date": "2024-03-15",
                        "departure_time": "08:00",
                        "status": "confirmed",
                        "seat": "1A",
                        "special_requests": [],
                        "chauffeur_eligible": True,
                        "lounge_eligible": True,
                    },
                },
                "passengers": {
                    "PAX001": {
                        "id": "PAX001",
                        "name": "Robert Sterling",
                        "email": "robert@sterling.com",
                        "phone": "+1-555-0100",
                        "skywards_id": "EK-12345678",
                    },
                },
                "flights": {
                    "EK201": {
                        "flight_number": "EK201",
                        "origin": "DXB",
                        "destination": "JFK",
                        "departure_time": "08:00",
                        "arrival_time": "14:30",
                        "status": "on_time",
                        "aircraft": "A380",
                    },
                },
                "skywards_accounts": {
                    "EK-12345678": {
                        "skywards_id": "EK-12345678",
                        "name": "Robert Sterling",
                        "email": "robert@sterling.com",
                        "tier": "platinum",
                        "miles_balance": 250000,
                        "tier_miles": 150000,
                        "expiring_miles": 25000,
                        "expiring_date": "2024-06-30",
                    },
                },
                "chauffeur_bookings": {},
                "lounge_passes": {},
                "icoupons": {},
                "baggage_claims": {},
            },
        },
        "emirates_app": {
            "per_agent": {
                "customer": {
                    "my_trips": [
                        {
                            "pnr": "ABC123",
                            "flight_number": "EK201",
                            "origin": "DXB",
                            "destination": "JFK",
                            "departure_date": "2024-03-15",
                            "cabin_class": "first",
                            "status": "confirmed",
                        },
                    ],
                    "skywards_dashboard": {
                        "skywards_id": "EK-12345678",
                        "tier": "platinum",
                        "miles_balance": 250000,
                        "tier_miles": 150000,
                    },
                    "chauffeur_bookings": [],
                    "lounge_passes": [],
                    "icoupons": [],
                    "preferences": {"seat": "window", "meal": "regular"},
                    "boarding_pass_visible": False,
                    "checked_in": False,
                },
            },
        },
    }


def get_economy_upgrade_state() -> dict:
    """Get initial state for an Economy to Business upgrade scenario."""
    return {
        "emirates_backend": {
            "shared": {
                "bookings": {
                    "XYZ789": {
                        "pnr": "XYZ789",
                        "passenger_name": "Sarah Martinez",
                        "cabin_class": "economy",
                        "original_cabin": "economy",
                        "flight_number": "EK202",
                        "origin": "DXB",
                        "destination": "LHR",
                        "departure_date": "2024-03-20",
                        "departure_time": "10:00",
                        "status": "confirmed",
                        "seat": "42A",
                        "special_requests": [],
                        "upgrade_miles_required": 45000,
                    },
                },
                "passengers": {
                    "PAX002": {
                        "id": "PAX002",
                        "name": "Sarah Martinez",
                        "email": "sarah@email.com",
                        "phone": "+1-555-0200",
                        "skywards_id": "EK-87654321",
                    },
                },
                "flights": {
                    "EK202": {
                        "flight_number": "EK202",
                        "origin": "DXB",
                        "destination": "LHR",
                        "departure_time": "10:00",
                        "arrival_time": "14:30",
                        "status": "on_time",
                        "aircraft": "B777",
                        "business_available": True,
                    },
                },
                "skywards_accounts": {
                    "EK-87654321": {
                        "skywards_id": "EK-87654321",
                        "name": "Sarah Martinez",
                        "email": "sarah@email.com",
                        "tier": "silver",
                        "miles_balance": 85000,
                        "tier_miles": 35000,
                        "expiring_miles": 10000,
                        "expiring_date": "2024-04-30",
                    },
                },
                "chauffeur_bookings": {},
                "lounge_passes": {},
                "icoupons": {},
                "baggage_claims": {},
            },
        },
        "emirates_app": {
            "per_agent": {
                "customer": {
                    "my_trips": [
                        {
                            "pnr": "XYZ789",
                            "flight_number": "EK202",
                            "origin": "DXB",
                            "destination": "LHR",
                            "departure_date": "2024-03-20",
                            "cabin_class": "economy",
                            "status": "confirmed",
                        },
                    ],
                    "skywards_dashboard": {
                        "skywards_id": "EK-87654321",
                        "tier": "silver",
                        "miles_balance": 85000,
                        "tier_miles": 35000,
                    },
                    "chauffeur_bookings": [],
                    "lounge_passes": [],
                    "icoupons": [],
                    "preferences": {},
                    "boarding_pass_visible": False,
                    "checked_in": False,
                },
            },
        },
    }


def get_delayed_flight_state() -> dict:
    """Get initial state for a delayed flight compensation scenario."""
    return {
        "emirates_backend": {
            "shared": {
                "bookings": {
                    "DEF456": {
                        "pnr": "DEF456",
                        "passenger_name": "Alex Chen",
                        "cabin_class": "economy",
                        "original_cabin": "economy",
                        "flight_number": "EK203",
                        "origin": "DXB",
                        "destination": "SIN",
                        "departure_date": "2024-03-18",
                        "departure_time": "14:00",
                        "status": "delayed",
                        "delay_hours": 5,
                        "seat": "35C",
                        "special_requests": [],
                    },
                },
                "passengers": {
                    "PAX003": {
                        "id": "PAX003",
                        "name": "Alex Chen",
                        "email": "alex.chen@email.com",
                        "phone": "+65-9876-5432",
                        "skywards_id": "EK-11111111",
                    },
                },
                "flights": {
                    "EK203": {
                        "flight_number": "EK203",
                        "origin": "DXB",
                        "destination": "SIN",
                        "departure_time": "14:00",
                        "arrival_time": "02:00",
                        "status": "delayed",
                        "delay_reason": "technical",
                        "delay_hours": 5,
                        "new_departure_time": "19:00",
                        "aircraft": "A380",
                    },
                },
                "skywards_accounts": {
                    "EK-11111111": {
                        "skywards_id": "EK-11111111",
                        "name": "Alex Chen",
                        "email": "alex.chen@email.com",
                        "tier": "blue",
                        "miles_balance": 5000,
                        "tier_miles": 5000,
                        "expiring_miles": 0,
                    },
                },
                "chauffeur_bookings": {},
                "lounge_passes": {},
                "icoupons": {},
                "baggage_claims": {},
            },
        },
        "emirates_app": {
            "per_agent": {
                "customer": {
                    "my_trips": [
                        {
                            "pnr": "DEF456",
                            "flight_number": "EK203",
                            "origin": "DXB",
                            "destination": "SIN",
                            "departure_date": "2024-03-18",
                            "cabin_class": "economy",
                            "status": "delayed",
                        },
                    ],
                    "skywards_dashboard": {
                        "skywards_id": "EK-11111111",
                        "tier": "blue",
                        "miles_balance": 5000,
                    },
                    "chauffeur_bookings": [],
                    "lounge_passes": [],
                    "icoupons": [],
                    "preferences": {},
                    "boarding_pass_visible": False,
                    "checked_in": False,
                },
            },
        },
    }


def get_missed_connection_state() -> dict:
    """Get initial state for a missed connection rebooking scenario."""
    return {
        "emirates_backend": {
            "shared": {
                "bookings": {
                    "MNO456": {
                        "pnr": "MNO456",
                        "passenger_name": "James Thompson",
                        "cabin_class": "business",
                        "original_cabin": "business",
                        "flight_number": "EK204",
                        "connecting_flight": "EK501",
                        "origin": "LHR",
                        "connection": "DXB",
                        "destination": "SYD",
                        "departure_date": "2024-03-22",
                        "departure_time": "07:00",
                        "status": "delayed",
                        "original_flight": "EK204",
                        "seat": "5A",
                        "special_requests": [],
                        "connection_time_minutes": 90,
                        "missed_connection": True,
                    },
                },
                "passengers": {
                    "PAX004": {
                        "id": "PAX004",
                        "name": "James Thompson",
                        "email": "james.t@business.com",
                        "phone": "+44-7700-900000",
                        "skywards_id": "EK-22222222",
                    },
                },
                "flights": {
                    "EK204": {
                        "flight_number": "EK204",
                        "origin": "LHR",
                        "destination": "DXB",
                        "departure_time": "07:00",
                        "arrival_time": "18:30",
                        "status": "delayed",
                        "delay_hours": 3,
                        "aircraft": "A380",
                    },
                    "EK501": {
                        "flight_number": "EK501",
                        "origin": "DXB",
                        "destination": "SYD",
                        "departure_time": "20:00",
                        "arrival_time": "17:30+1",
                        "status": "on_time",
                        "aircraft": "A380",
                    },
                    "EK503": {
                        "flight_number": "EK503",
                        "origin": "DXB",
                        "destination": "SYD",
                        "departure_time": "02:00+1",
                        "arrival_time": "23:30+1",
                        "status": "on_time",
                        "aircraft": "A380",
                        "business_available": True,
                    },
                },
                "skywards_accounts": {
                    "EK-22222222": {
                        "skywards_id": "EK-22222222",
                        "name": "James Thompson",
                        "email": "james.t@business.com",
                        "tier": "gold",
                        "miles_balance": 120000,
                        "tier_miles": 75000,
                    },
                },
                "chauffeur_bookings": {},
                "lounge_passes": {},
                "icoupons": {},
                "baggage_claims": {},
            },
        },
        "emirates_app": {
            "per_agent": {
                "customer": {
                    "my_trips": [
                        {
                            "pnr": "MNO456",
                            "flight_number": "EK204",
                            "connecting_flight": "EK501",
                            "origin": "LHR",
                            "connection": "DXB",
                            "destination": "SYD",
                            "departure_date": "2024-03-22",
                            "cabin_class": "business",
                            "status": "delayed",
                        },
                    ],
                    "skywards_dashboard": {
                        "skywards_id": "EK-22222222",
                        "tier": "gold",
                        "miles_balance": 120000,
                    },
                    "chauffeur_bookings": [],
                    "lounge_passes": [],
                    "icoupons": [],
                    "preferences": {"seat": "aisle"},
                    "boarding_pass_visible": False,
                    "checked_in": True,
                },
            },
        },
    }


def get_baggage_claim_state() -> dict:
    """Get initial state for a delayed baggage claim scenario."""
    return {
        "emirates_backend": {
            "shared": {
                "bookings": {
                    "GHI789": {
                        "pnr": "GHI789",
                        "passenger_name": "Priya Sharma",
                        "cabin_class": "business",
                        "original_cabin": "business",
                        "flight_number": "EK205",
                        "origin": "BOM",
                        "destination": "JFK",
                        "arrival_date": "2024-03-16",
                        "departure_time": "04:00",
                        "status": "arrived",
                        "seat": "8K",
                        "special_requests": [],
                        "checked_bags": 2,
                    },
                },
                "passengers": {
                    "PAX005": {
                        "id": "PAX005",
                        "name": "Priya Sharma",
                        "email": "priya.sharma@hospital.org",
                        "phone": "+1-555-0500",
                        "skywards_id": "EK-33333333",
                    },
                },
                "flights": {
                    "EK205": {
                        "flight_number": "EK205",
                        "origin": "BOM",
                        "destination": "JFK",
                        "via": "DXB",
                        "departure_time": "04:00",
                        "arrival_time": "17:00",
                        "status": "arrived",
                        "aircraft": "B777",
                    },
                },
                "skywards_accounts": {
                    "EK-33333333": {
                        "skywards_id": "EK-33333333",
                        "name": "Priya Sharma",
                        "email": "priya.sharma@hospital.org",
                        "tier": "gold",
                        "miles_balance": 95000,
                        "tier_miles": 60000,
                    },
                },
                "chauffeur_bookings": {},
                "lounge_passes": {},
                "icoupons": {},
                "baggage_claims": {},
            },
        },
        "emirates_app": {
            "per_agent": {
                "customer": {
                    "my_trips": [
                        {
                            "pnr": "GHI789",
                            "flight_number": "EK205",
                            "origin": "BOM",
                            "destination": "JFK",
                            "arrival_date": "2024-03-16",
                            "cabin_class": "business",
                            "status": "arrived",
                        },
                    ],
                    "skywards_dashboard": {
                        "skywards_id": "EK-33333333",
                        "tier": "gold",
                        "miles_balance": 95000,
                    },
                    "chauffeur_bookings": [],
                    "lounge_passes": [],
                    "icoupons": [],
                    "preferences": {},
                    "boarding_pass_visible": False,
                    "checked_in": True,
                },
            },
        },
    }


# =============================================================================
# TIER 1: EASY TASKS
# =============================================================================

EMIRATES_CHAUFFEUR_001 = TaskDefinition(
    task_id="emirates_chauffeur_001",
    name="Book Chauffeur Service for First Class Passenger",
    domain="emirates",
    difficulty="easy",
    description="""A First Class passenger calls to arrange complimentary chauffeur service
    for airport pickup. The service agent needs to verify eligibility, book the chauffeur,
    and the customer should confirm the booking in their app.""",
    simulation_config={
        "agents": [
            {
                "agent_id": "service_agent",
                "name": "Ahmed Al-Rashid",
                "role": "service_agent",
                "persona": "senior_agent",
            },
            {
                "agent_id": "customer",
                "name": "Robert Sterling",
                "role": "customer",
                "persona": "first_class_vip",
            },
        ],
        "apps": ["emirates_backend", "emirates_app"],
        "topology": "direct",
        "max_turns": 15,
    },
    initial_app_states=get_first_class_booking_state(),
    agent_instruction="""You are helping a First Class passenger book complimentary chauffeur service.

Service Agent Task:
1. Look up the booking using PNR ABC123
2. Verify the passenger is eligible (First/Business class)
3. Book the chauffeur pickup service for the passenger
4. Confirm the details with the customer

Customer Task:
1. Provide your booking details (PNR: ABC123)
2. Request chauffeur pickup from your hotel
3. Confirm the booking in your Emirates app once the agent books it

Pickup Details:
- Address: Burj Al Arab Hotel, Dubai
- Date/Time: March 15, 2024 at 05:00 AM
- Special request: Meet in the hotel lobby
""",
    expected_final_states={
        "emirates_backend": {
            "shared": {
                "chauffeur_bookings": {
                    "$exists": True,
                    "$count_gte": 1,
                },
            },
        },
    },
    expected_actions=[
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="lookup_booking",
            params={"pnr": "ABC123"},
            required=True,
        ),
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="book_chauffeur",
            params={
                "pnr": "ABC123",
                "service_type": "pickup",
            },
            required=True,
        ),
        ExpectedAction(
            agent_id="customer",
            app_id="emirates_app",
            action_name="confirm_chauffeur_pickup",
            params={"confirmed": True},
            required=True,
        ),
    ],
    tags=["emirates", "chauffeur", "first_class", "easy", "dual_control"],
    estimated_steps=8,
)

EMIRATES_LOUNGE_001 = TaskDefinition(
    task_id="emirates_lounge_001",
    name="Issue Business Class Lounge Pass",
    domain="emirates",
    difficulty="easy",
    description="""A Business Class passenger needs a digital lounge pass issued.
    The service agent verifies eligibility and issues the pass, which the customer
    can then view in their Emirates app.""",
    simulation_config={
        "agents": [
            {
                "agent_id": "service_agent",
                "name": "Fatima Hassan",
                "role": "service_agent",
                "persona": "new_agent",
            },
            {
                "agent_id": "customer",
                "name": "James Thompson",
                "role": "customer",
                "persona": "business_executive",
            },
        ],
        "apps": ["emirates_backend", "emirates_app"],
        "topology": "direct",
        "max_turns": 12,
    },
    initial_app_states=get_first_class_booking_state(),  # Will modify for Business
    agent_instruction="""You are helping a Business Class passenger get a lounge access pass.

Service Agent Task:
1. Look up the booking using PNR ABC123
2. Verify Business or First class ticket
3. Issue a digital lounge pass for DXB Concourse B
4. Inform the customer the pass is available in their app

Customer Task:
1. Provide your booking reference (PNR: ABC123)
2. Request lounge access for your departure
3. Check your Emirates app to view the lounge pass

Lounge Details:
- Location: DXB Terminal 3, Concourse B Emirates Lounge
- Valid Date: March 15, 2024
- Guest passes: 1 (traveling with spouse)
""",
    expected_final_states={
        "emirates_backend": {
            "shared": {
                "lounge_passes": {
                    "$exists": True,
                    "$count_gte": 1,
                },
            },
        },
    },
    expected_actions=[
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="lookup_booking",
            params={"pnr": "ABC123"},
            required=True,
        ),
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="issue_lounge_pass",
            params={
                "pnr": "ABC123",
                "lounge_location": "DXB Concourse B",
            },
            required=True,
        ),
        ExpectedAction(
            agent_id="customer",
            app_id="emirates_app",
            action_name="view_lounge_passes",
            required=True,
        ),
    ],
    tags=["emirates", "lounge", "business_class", "easy", "dual_control"],
    estimated_steps=6,
)


# =============================================================================
# TIER 2: MEDIUM TASKS
# =============================================================================

EMIRATES_SKYWARDS_REDEMPTION_001 = TaskDefinition(
    task_id="emirates_skywards_redemption_001",
    name="Skywards Miles Upgrade Redemption",
    domain="emirates",
    difficulty="medium",
    description="""A Silver member wants to redeem Skywards miles to upgrade from
    Economy to Business class. The service agent must verify miles balance,
    check upgrade availability, and process the redemption with customer confirmation.""",
    simulation_config={
        "agents": [
            {
                "agent_id": "service_agent",
                "name": "Ahmed Al-Rashid",
                "role": "service_agent",
                "persona": "senior_agent",
            },
            {
                "agent_id": "customer",
                "name": "Sarah Martinez",
                "role": "customer",
                "persona": "frequent_economy",
            },
        ],
        "apps": ["emirates_backend", "emirates_app"],
        "topology": "direct",
        "max_turns": 20,
    },
    initial_app_states=get_economy_upgrade_state(),
    agent_instruction="""You are helping a Skywards Silver member upgrade using miles.

Service Agent Task:
1. Look up the booking (PNR: XYZ789)
2. Look up the Skywards account (EK-87654321)
3. Check miles balance (should have 85,000 miles)
4. Verify upgrade requires 45,000 miles and Business is available
5. Process the miles redemption for the upgrade
6. Confirm the new cabin class with the customer

Customer Task:
1. Provide your booking (PNR: XYZ789) and Skywards ID (EK-87654321)
2. Confirm you want to use miles for the upgrade
3. Submit the upgrade redemption request in your Emirates app
4. Verify the upgrade was successful

Expected Outcome:
- Miles deducted: 45,000
- Remaining balance: 40,000
- New cabin class: Business
""",
    expected_final_states={
        "emirates_backend": {
            "shared": {
                "skywards_accounts": {
                    "EK-87654321": {
                        "miles_balance": 40000,
                    },
                },
                "bookings": {
                    "XYZ789": {
                        "cabin_class": "business",
                    },
                },
            },
        },
    },
    expected_actions=[
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="lookup_booking",
            params={"pnr": "XYZ789"},
            required=True,
        ),
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="check_miles_balance",
            params={"skywards_id": "EK-87654321"},
            required=True,
        ),
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="process_miles_redemption",
            params={
                "skywards_id": "EK-87654321",
                "pnr": "XYZ789",
                "miles_to_redeem": 45000,
                "target_cabin": "business",
            },
            required=True,
        ),
        ExpectedAction(
            agent_id="customer",
            app_id="emirates_app",
            action_name="view_skywards_dashboard",
            required=True,
        ),
    ],
    tags=["emirates", "skywards", "miles", "upgrade", "medium", "dual_control"],
    estimated_steps=12,
)

EMIRATES_ICOUPON_001 = TaskDefinition(
    task_id="emirates_icoupon_001",
    name="Flight Delay iCoupon Compensation",
    domain="emirates",
    difficulty="medium",
    description="""A passenger's flight is delayed by 5 hours. The service agent
    must issue appropriate iCoupon compensation (meal and lounge vouchers) which
    the customer can view in their Emirates app.""",
    simulation_config={
        "agents": [
            {
                "agent_id": "service_agent",
                "name": "Ahmed Al-Rashid",
                "role": "service_agent",
                "persona": "senior_agent",
            },
            {
                "agent_id": "customer",
                "name": "Alex Chen",
                "role": "customer",
                "persona": "economy_traveler",
            },
        ],
        "apps": ["emirates_backend", "emirates_app"],
        "topology": "direct",
        "max_turns": 18,
    },
    initial_app_states=get_delayed_flight_state(),
    agent_instruction="""You are helping a passenger affected by a 5-hour flight delay.

Service Agent Task:
1. Look up the booking (PNR: DEF456)
2. Verify the flight delay (EK203, 5 hours delay)
3. Issue a meal iCoupon ($30 USD)
4. Issue a lounge access iCoupon if eligible
5. Explain the compensation to the customer

Customer Task:
1. Inquire about your delayed flight (PNR: DEF456, Flight EK203)
2. Ask about compensation options
3. Accept the offered compensation
4. Check your Emirates app to view the iCoupons

Compensation Policy:
- Delays over 4 hours: Meal voucher ($30)
- Delays over 4 hours: Lounge access (if available)
- Reason: Technical delay
""",
    expected_final_states={
        "emirates_backend": {
            "shared": {
                "icoupons": {
                    "$exists": True,
                    "$count_gte": 1,
                },
            },
        },
    },
    expected_actions=[
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="lookup_booking",
            params={"pnr": "DEF456"},
            required=True,
        ),
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="check_flight_status",
            params={"flight_number": "EK203"},
            required=True,
        ),
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="issue_icoupon",
            params={
                "pnr": "DEF456",
                "coupon_type": "meal",
            },
            required=True,
        ),
        ExpectedAction(
            agent_id="customer",
            app_id="emirates_app",
            action_name="view_icoupons",
            required=True,
        ),
    ],
    tags=["emirates", "icoupon", "delay", "compensation", "medium", "dual_control"],
    estimated_steps=10,
)


# =============================================================================
# TIER 3: HARD TASKS
# =============================================================================

EMIRATES_BAGGAGE_CLAIM_001 = TaskDefinition(
    task_id="emirates_baggage_claim_001",
    name="Delayed Baggage Claim Filing",
    domain="emirates",
    difficulty="hard",
    description="""A passenger arrives to find one of their checked bags missing.
    The service agent must file a Property Irregularity Report (PIR), set up
    tracking, and arrange for delivery once the bag is located.""",
    simulation_config={
        "agents": [
            {
                "agent_id": "service_agent",
                "name": "Ahmed Al-Rashid",
                "role": "service_agent",
                "persona": "senior_agent",
            },
            {
                "agent_id": "customer",
                "name": "Priya Sharma",
                "role": "customer",
                "persona": "business_family",
            },
        ],
        "apps": ["emirates_backend", "emirates_app"],
        "topology": "direct",
        "max_turns": 25,
    },
    initial_app_states=get_baggage_claim_state(),
    agent_instruction="""You are helping a passenger who is missing a checked bag.

Service Agent Task:
1. Look up the booking (PNR: GHI789)
2. Verify the flight details (EK205 from BOM to JFK via DXB)
3. Create a Property Irregularity Report (PIR)
4. Set up tracking for the bag
5. Arrange delivery address for when bag is found
6. Issue goodwill compensation if appropriate

Customer Task:
1. Report your missing bag
   - PNR: GHI789
   - Flight: EK205
   - Bag tag: EK789456
   - Description: Large black Samsonite suitcase with red ribbon
2. Provide delivery address: 450 Park Avenue, Apt 12B, New York, NY 10022
3. Provide contact: +1-555-0500
4. Accept any offered compensation

Bag Details:
- Bag tag number: EK789456
- Description: Large black Samsonite suitcase with red ribbon on handle
- Contents: Business clothes, medical equipment
- Delivery address: 450 Park Avenue, Apt 12B, New York, NY 10022
""",
    expected_final_states={
        "emirates_backend": {
            "shared": {
                "baggage_claims": {
                    "$exists": True,
                    "$count_gte": 1,
                },
            },
        },
    },
    expected_actions=[
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="lookup_booking",
            params={"pnr": "GHI789"},
            required=True,
        ),
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="create_baggage_claim",
            params={
                "pnr": "GHI789",
                "flight_number": "EK205",
                "bag_tag_number": "EK789456",
            },
            required=True,
        ),
    ],
    tags=["emirates", "baggage", "claim", "hard", "dual_control"],
    estimated_steps=15,
)

EMIRATES_MISSED_CONNECTION_001 = TaskDefinition(
    task_id="emirates_missed_connection_001",
    name="Missed Connection Rebooking",
    domain="emirates",
    difficulty="hard",
    description="""A Business Class passenger will miss their connecting flight due
    to a delayed inbound flight. The service agent must rebook on the next available
    flight, maintain Business class, and arrange lounge access during the wait.""",
    simulation_config={
        "agents": [
            {
                "agent_id": "service_agent",
                "name": "Ahmed Al-Rashid",
                "role": "service_agent",
                "persona": "senior_agent",
            },
            {
                "agent_id": "customer",
                "name": "James Thompson",
                "role": "customer",
                "persona": "business_executive",
            },
        ],
        "apps": ["emirates_backend", "emirates_app"],
        "topology": "direct",
        "max_turns": 30,
    },
    initial_app_states=get_missed_connection_state(),
    agent_instruction="""You are helping a Business Class passenger who will miss their connection.

Service Agent Task:
1. Look up the booking (PNR: MNO456)
2. Verify the situation:
   - Inbound: EK204 LHR-DXB delayed 3 hours
   - Connection: EK501 DXB-SYD will be missed
3. Find alternative flight (EK503 DXB-SYD at 02:00+1)
4. Rebook the passenger on EK503 maintaining Business class
5. Issue lounge access for the extended wait
6. Issue meal compensation iCoupon
7. Confirm new itinerary with customer

Customer Task:
1. Explain you're on delayed flight EK204 and will miss connection EK501
2. Confirm you need to get to Sydney
3. Accept the rebooking on EK503
4. Confirm the new itinerary in your Emirates app
5. View the lounge pass in your app

Rebooking Details:
- Original connection: EK501 DXB-SYD 20:00
- New flight: EK503 DXB-SYD 02:00+1
- Must maintain Business class
- Lounge access during wait
""",
    expected_final_states={
        "emirates_backend": {
            "shared": {
                "bookings": {
                    "MNO456": {
                        "flight_number": "EK503",
                    },
                },
                "lounge_passes": {
                    "$exists": True,
                    "$count_gte": 1,
                },
            },
        },
    },
    expected_actions=[
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="lookup_booking",
            params={"pnr": "MNO456"},
            required=True,
        ),
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="check_flight_status",
            params={"flight_number": "EK204"},
            required=True,
        ),
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="rebook_passenger",
            params={
                "pnr": "MNO456",
                "new_flight_number": "EK503",
                "reason": "missed_connection",
            },
            required=True,
        ),
        ExpectedAction(
            agent_id="service_agent",
            app_id="emirates_backend",
            action_name="issue_lounge_pass",
            params={"pnr": "MNO456"},
            required=True,
        ),
        ExpectedAction(
            agent_id="customer",
            app_id="emirates_app",
            action_name="view_my_trips",
            required=True,
        ),
    ],
    tags=["emirates", "rebooking", "missed_connection", "hard", "dual_control"],
    estimated_steps=18,
)


# =============================================================================
# Task Collections
# =============================================================================

EMIRATES_EASY_TASKS = [
    EMIRATES_CHAUFFEUR_001,
    EMIRATES_LOUNGE_001,
]

EMIRATES_MEDIUM_TASKS = [
    EMIRATES_SKYWARDS_REDEMPTION_001,
    EMIRATES_ICOUPON_001,
]

EMIRATES_HARD_TASKS = [
    EMIRATES_BAGGAGE_CLAIM_001,
    EMIRATES_MISSED_CONNECTION_001,
]

EMIRATES_ALL_TASKS = EMIRATES_EASY_TASKS + EMIRATES_MEDIUM_TASKS + EMIRATES_HARD_TASKS

EMIRATES_TASKS_BY_ID = {task.task_id: task for task in EMIRATES_ALL_TASKS}


# =============================================================================
# Utility Functions
# =============================================================================

def get_emirates_task(task_id: str) -> TaskDefinition | None:
    """Get an Emirates task by ID.

    Args:
        task_id: Task identifier

    Returns:
        TaskDefinition or None
    """
    return EMIRATES_TASKS_BY_ID.get(task_id)


def get_emirates_tasks_by_difficulty(difficulty: str) -> list[TaskDefinition]:
    """Get Emirates tasks by difficulty level.

    Args:
        difficulty: easy, medium, or hard

    Returns:
        List of matching tasks
    """
    difficulty_map = {
        "easy": EMIRATES_EASY_TASKS,
        "medium": EMIRATES_MEDIUM_TASKS,
        "hard": EMIRATES_HARD_TASKS,
    }
    return difficulty_map.get(difficulty.lower(), [])


def get_all_emirates_tasks() -> list[TaskDefinition]:
    """Get all Emirates tasks.

    Returns:
        List of all Emirates tasks
    """
    return EMIRATES_ALL_TASKS.copy()


def get_emirates_task_summary() -> dict:
    """Get a summary of Emirates tasks.

    Returns:
        Dictionary with task counts and IDs by difficulty
    """
    return {
        "total": len(EMIRATES_ALL_TASKS),
        "by_difficulty": {
            "easy": {
                "count": len(EMIRATES_EASY_TASKS),
                "task_ids": [t.task_id for t in EMIRATES_EASY_TASKS],
            },
            "medium": {
                "count": len(EMIRATES_MEDIUM_TASKS),
                "task_ids": [t.task_id for t in EMIRATES_MEDIUM_TASKS],
            },
            "hard": {
                "count": len(EMIRATES_HARD_TASKS),
                "task_ids": [t.task_id for t in EMIRATES_HARD_TASKS],
            },
        },
        "domain": "emirates",
        "features": [
            "chauffeur_service",
            "lounge_access",
            "skywards_miles",
            "icoupon_compensation",
            "baggage_claims",
            "rebooking",
        ],
    }
