"""Emirates airline dual-control apps for evaluation.

Per ADR-020.1, these apps demonstrate role-restricted access for Emirates:
- Service agents have backend CRM access
- Customers have Emirates mobile app access

Domain: Emirates Airline
Features: Skywards loyalty, chauffeur service, lounge access, iCoupon compensation
"""

# =============================================================================
# Emirates Backend CRM - Service Agent Only
# =============================================================================

EMIRATES_BACKEND = {
    "app_id": "emirates_backend",
    "name": "Emirates Backend CRM",
    "description": "Backend CRM system for Emirates service agents to manage bookings, Skywards accounts, chauffeur services, lounge passes, and compensation",
    "category": "custom",
    "icon": "🖥️",
    "access_type": "role_restricted",
    "allowed_roles": ["service_agent"],
    "state_type": "shared",
    "state_schema": [
        {"name": "bookings", "type": "object", "default": {}, "perAgent": False, "description": "PNR -> booking details"},
        {"name": "passengers", "type": "object", "default": {}, "perAgent": False, "description": "Passenger ID -> passenger info"},
        {"name": "flights", "type": "object", "default": {}, "perAgent": False, "description": "Flight number -> flight info"},
        {"name": "skywards_accounts", "type": "object", "default": {}, "perAgent": False, "description": "Skywards ID -> account details"},
        {"name": "chauffeur_bookings", "type": "object", "default": {}, "perAgent": False, "description": "Booking ID -> chauffeur service details"},
        {"name": "lounge_passes", "type": "object", "default": {}, "perAgent": False, "description": "Pass ID -> lounge pass details"},
        {"name": "icoupons", "type": "object", "default": {}, "perAgent": False, "description": "Coupon ID -> iCoupon voucher details"},
        {"name": "baggage_claims", "type": "object", "default": {}, "perAgent": False, "description": "PIR number -> baggage claim details"},
    ],
    "initial_config": {
        "airline_code": "EK",
    },
    "actions": [
        # ==== READ ACTIONS ====
        {
            "name": "lookup_booking",
            "description": "Look up a booking by PNR confirmation code or ticket number",
            "toolType": "read",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": False,
                    "description": "6-character PNR confirmation code (e.g., ABC123)",
                },
                "ticket_number": {
                    "type": "string",
                    "required": False,
                    "description": "13-digit ticket number (e.g., 1762345678901)",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.pnr != null || params.ticket_number != null",
                    "errorMessage": "Provide either pnr or ticket_number",
                },
                {
                    "type": "branch",
                    "condition": "params.pnr != null && shared.bookings[params.pnr] != null",
                    "then": [
                        {
                            "type": "return",
                            "value": {
                                "found": True,
                                "booking": "shared.bookings[params.pnr]",
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
            "name": "lookup_skywards_member",
            "description": "Look up Skywards loyalty member by ID or email",
            "toolType": "read",
            "parameters": {
                "skywards_id": {
                    "type": "string",
                    "required": False,
                    "description": "Skywards membership ID (e.g., EK-12345678)",
                },
                "email": {
                    "type": "string",
                    "required": False,
                    "description": "Member email address",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.skywards_id != null || params.email != null",
                    "errorMessage": "Provide skywards_id or email",
                },
                {
                    "type": "branch",
                    "condition": "params.skywards_id != null && shared.skywards_accounts[params.skywards_id] != null",
                    "then": [
                        {
                            "type": "return",
                            "value": {
                                "found": True,
                                "member": "shared.skywards_accounts[params.skywards_id]",
                            },
                        },
                    ],
                    "else": [
                        {
                            "type": "return",
                            "value": {"found": False, "message": "Skywards member not found"},
                        },
                    ],
                },
            ],
        },
        {
            "name": "check_miles_balance",
            "description": "Check Skywards miles balance and tier status",
            "toolType": "read",
            "parameters": {
                "skywards_id": {
                    "type": "string",
                    "required": True,
                    "description": "Skywards membership ID",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.skywards_accounts[params.skywards_id] != null",
                    "errorMessage": "Skywards account not found",
                },
                {
                    "type": "return",
                    "value": {
                        "skywards_id": "params.skywards_id",
                        "miles_balance": "shared.skywards_accounts[params.skywards_id].miles_balance",
                        "tier": "shared.skywards_accounts[params.skywards_id].tier",
                        "tier_miles": "shared.skywards_accounts[params.skywards_id].tier_miles",
                        "expiring_miles": "shared.skywards_accounts[params.skywards_id].expiring_miles",
                    },
                },
            ],
        },
        {
            "name": "check_flight_status",
            "description": "Check real-time status of a flight",
            "toolType": "read",
            "parameters": {
                "flight_number": {
                    "type": "string",
                    "required": True,
                    "description": "Flight number (e.g., EK123)",
                },
                "date": {
                    "type": "string",
                    "required": False,
                    "description": "Flight date (YYYY-MM-DD)",
                },
            },
            "logic": [
                {
                    "type": "branch",
                    "condition": "shared.flights[params.flight_number] != null",
                    "then": [
                        {
                            "type": "return",
                            "value": {
                                "found": True,
                                "flight": "shared.flights[params.flight_number]",
                            },
                        },
                    ],
                    "else": [
                        {
                            "type": "return",
                            "value": {"found": False, "message": "Flight not found"},
                        },
                    ],
                },
            ],
        },
        {
            "name": "track_baggage",
            "description": "Track baggage claim status",
            "toolType": "read",
            "parameters": {
                "pir_number": {
                    "type": "string",
                    "required": True,
                    "description": "Property Irregularity Report number",
                },
            },
            "logic": [
                {
                    "type": "branch",
                    "condition": "shared.baggage_claims[params.pir_number] != null",
                    "then": [
                        {
                            "type": "return",
                            "value": {
                                "found": True,
                                "claim": "shared.baggage_claims[params.pir_number]",
                            },
                        },
                    ],
                    "else": [
                        {
                            "type": "return",
                            "value": {"found": False, "message": "Baggage claim not found"},
                        },
                    ],
                },
            ],
        },
        # ==== WRITE ACTIONS ====
        {
            "name": "book_chauffeur",
            "description": "Book complimentary chauffeur service for First/Business class passengers",
            "toolType": "write",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR",
                },
                "passenger_name": {
                    "type": "string",
                    "required": True,
                    "description": "Passenger name",
                },
                "service_type": {
                    "type": "string",
                    "required": True,
                    "description": "pickup or dropoff",
                    "enum": ["pickup", "dropoff"],
                },
                "pickup_address": {
                    "type": "string",
                    "required": True,
                    "description": "Pickup/dropoff address",
                },
                "pickup_datetime": {
                    "type": "string",
                    "required": True,
                    "description": "Pickup date and time (ISO format)",
                },
                "special_instructions": {
                    "type": "string",
                    "required": False,
                    "description": "Special instructions for driver",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.bookings[params.pnr] != null",
                    "errorMessage": "Booking not found",
                },
                {
                    "type": "validate",
                    "condition": "shared.bookings[params.pnr].cabin_class == 'first' || shared.bookings[params.pnr].cabin_class == 'business'",
                    "errorMessage": "Chauffeur service only available for First and Business class",
                },
                {
                    "type": "update",
                    "target": "shared.chauffeur_bookings[generate_id()]",
                    "operation": "set",
                    "value": {
                        "booking_id": "generate_id()",
                        "pnr": "params.pnr",
                        "passenger_name": "params.passenger_name",
                        "service_type": "params.service_type",
                        "pickup_address": "params.pickup_address",
                        "pickup_datetime": "params.pickup_datetime",
                        "special_instructions": "params.special_instructions",
                        "status": "confirmed",
                        "created_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "chauffeur_booking_id": "generate_id()",
                        "message": "Chauffeur service booked successfully",
                    },
                },
            ],
        },
        {
            "name": "issue_lounge_pass",
            "description": "Issue digital lounge access pass",
            "toolType": "write",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR",
                },
                "passenger_name": {
                    "type": "string",
                    "required": True,
                    "description": "Passenger name",
                },
                "lounge_location": {
                    "type": "string",
                    "required": True,
                    "description": "Lounge location (e.g., DXB Concourse B)",
                },
                "valid_date": {
                    "type": "string",
                    "required": True,
                    "description": "Date pass is valid for (YYYY-MM-DD)",
                },
                "guest_passes": {
                    "type": "number",
                    "required": False,
                    "default": 0,
                    "description": "Number of guest passes (max 2)",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.bookings[params.pnr] != null",
                    "errorMessage": "Booking not found",
                },
                {
                    "type": "validate",
                    "condition": "params.guest_passes == null || params.guest_passes <= 2",
                    "errorMessage": "Maximum 2 guest passes allowed",
                },
                {
                    "type": "update",
                    "target": "shared.lounge_passes[generate_id()]",
                    "operation": "set",
                    "value": {
                        "pass_id": "generate_id()",
                        "pnr": "params.pnr",
                        "passenger_name": "params.passenger_name",
                        "lounge_location": "params.lounge_location",
                        "valid_date": "params.valid_date",
                        "guest_passes": "params.guest_passes",
                        "status": "active",
                        "qr_code": "generate_id()",
                        "issued_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "pass_id": "generate_id()",
                        "message": "Lounge pass issued successfully",
                    },
                },
            ],
        },
        {
            "name": "process_miles_redemption",
            "description": "Process Skywards miles redemption for upgrade",
            "toolType": "write",
            "parameters": {
                "skywards_id": {
                    "type": "string",
                    "required": True,
                    "description": "Skywards membership ID",
                },
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR to upgrade",
                },
                "miles_to_redeem": {
                    "type": "number",
                    "required": True,
                    "description": "Number of miles to redeem",
                },
                "target_cabin": {
                    "type": "string",
                    "required": True,
                    "description": "Target cabin class (business or first)",
                    "enum": ["business", "first"],
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.skywards_accounts[params.skywards_id] != null",
                    "errorMessage": "Skywards account not found",
                },
                {
                    "type": "validate",
                    "condition": "shared.bookings[params.pnr] != null",
                    "errorMessage": "Booking not found",
                },
                {
                    "type": "validate",
                    "condition": "shared.skywards_accounts[params.skywards_id].miles_balance >= params.miles_to_redeem",
                    "errorMessage": "Insufficient miles balance",
                },
                {
                    "type": "update",
                    "target": "shared.skywards_accounts[params.skywards_id].miles_balance",
                    "operation": "subtract",
                    "value": "params.miles_to_redeem",
                },
                {
                    "type": "update",
                    "target": "shared.bookings[params.pnr].cabin_class",
                    "operation": "set",
                    "value": "params.target_cabin",
                },
                {
                    "type": "update",
                    "target": "shared.bookings[params.pnr].upgrade_history",
                    "operation": "append",
                    "value": {
                        "type": "miles_redemption",
                        "miles_used": "params.miles_to_redeem",
                        "from_cabin": "shared.bookings[params.pnr].original_cabin",
                        "to_cabin": "params.target_cabin",
                        "processed_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "new_cabin": "params.target_cabin",
                        "miles_deducted": "params.miles_to_redeem",
                        "remaining_balance": "shared.skywards_accounts[params.skywards_id].miles_balance",
                    },
                },
            ],
        },
        {
            "name": "issue_icoupon",
            "description": "Issue iCoupon compensation voucher for delays or inconvenience",
            "toolType": "write",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR",
                },
                "passenger_name": {
                    "type": "string",
                    "required": True,
                    "description": "Passenger name",
                },
                "coupon_type": {
                    "type": "string",
                    "required": True,
                    "description": "Type of iCoupon",
                    "enum": ["meal", "lounge", "hotel", "transport", "general"],
                },
                "amount": {
                    "type": "number",
                    "required": True,
                    "description": "Voucher amount in USD",
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Reason for compensation (e.g., flight_delay, baggage_delay)",
                },
                "valid_until": {
                    "type": "string",
                    "required": False,
                    "description": "Expiry date (YYYY-MM-DD), defaults to 24 hours",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.bookings[params.pnr] != null",
                    "errorMessage": "Booking not found",
                },
                {
                    "type": "validate",
                    "condition": "params.amount > 0 && params.amount <= 500",
                    "errorMessage": "Amount must be between 1 and 500 USD",
                },
                {
                    "type": "update",
                    "target": "shared.icoupons[generate_id()]",
                    "operation": "set",
                    "value": {
                        "coupon_id": "generate_id()",
                        "pnr": "params.pnr",
                        "passenger_name": "params.passenger_name",
                        "coupon_type": "params.coupon_type",
                        "amount": "params.amount",
                        "currency": "USD",
                        "reason": "params.reason",
                        "valid_until": "params.valid_until",
                        "status": "active",
                        "qr_code": "generate_id()",
                        "issued_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "coupon_id": "generate_id()",
                        "amount": "params.amount",
                        "message": "iCoupon issued successfully",
                    },
                },
            ],
        },
        {
            "name": "create_baggage_claim",
            "description": "Create Property Irregularity Report (PIR) for delayed or lost baggage",
            "toolType": "write",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR",
                },
                "passenger_name": {
                    "type": "string",
                    "required": True,
                    "description": "Passenger name",
                },
                "flight_number": {
                    "type": "string",
                    "required": True,
                    "description": "Flight number",
                },
                "bag_tag_number": {
                    "type": "string",
                    "required": True,
                    "description": "Bag tag number",
                },
                "bag_description": {
                    "type": "string",
                    "required": True,
                    "description": "Bag description (color, brand, size)",
                },
                "delivery_address": {
                    "type": "string",
                    "required": False,
                    "description": "Address for bag delivery once found",
                },
                "contact_phone": {
                    "type": "string",
                    "required": True,
                    "description": "Contact phone number",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.bookings[params.pnr] != null",
                    "errorMessage": "Booking not found",
                },
                {
                    "type": "update",
                    "target": "shared.baggage_claims[generate_id()]",
                    "operation": "set",
                    "value": {
                        "pir_number": "generate_id()",
                        "pnr": "params.pnr",
                        "passenger_name": "params.passenger_name",
                        "flight_number": "params.flight_number",
                        "bag_tag_number": "params.bag_tag_number",
                        "bag_description": "params.bag_description",
                        "delivery_address": "params.delivery_address",
                        "contact_phone": "params.contact_phone",
                        "status": "searching",
                        "created_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "pir_number": "generate_id()",
                        "message": "Baggage claim created. We will notify you once the bag is located.",
                    },
                },
            ],
        },
        {
            "name": "change_seat",
            "description": "Change seat assignment for a booking",
            "toolType": "write",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR",
                },
                "passenger_name": {
                    "type": "string",
                    "required": True,
                    "description": "Passenger name",
                },
                "flight_segment": {
                    "type": "number",
                    "required": False,
                    "default": 1,
                    "description": "Flight segment number (1 for first flight)",
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
                    "condition": "shared.bookings[params.pnr] != null",
                    "errorMessage": "Booking not found",
                },
                {
                    "type": "update",
                    "target": "shared.bookings[params.pnr].seat",
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
            "name": "rebook_passenger",
            "description": "Rebook passenger on alternative flight",
            "toolType": "write",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Original booking PNR",
                },
                "passenger_name": {
                    "type": "string",
                    "required": True,
                    "description": "Passenger name",
                },
                "new_flight_number": {
                    "type": "string",
                    "required": True,
                    "description": "New flight number",
                },
                "reason": {
                    "type": "string",
                    "required": True,
                    "description": "Reason for rebooking",
                    "enum": ["missed_connection", "flight_cancelled", "schedule_change", "passenger_request", "overbooking"],
                },
                "retain_cabin": {
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "Maintain same cabin class",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "shared.bookings[params.pnr] != null",
                    "errorMessage": "Booking not found",
                },
                {
                    "type": "validate",
                    "condition": "shared.flights[params.new_flight_number] != null",
                    "errorMessage": "New flight not found",
                },
                {
                    "type": "update",
                    "target": "shared.bookings[params.pnr].flight_number",
                    "operation": "set",
                    "value": "params.new_flight_number",
                },
                {
                    "type": "update",
                    "target": "shared.bookings[params.pnr].rebooking_history",
                    "operation": "append",
                    "value": {
                        "original_flight": "shared.bookings[params.pnr].original_flight",
                        "new_flight": "params.new_flight_number",
                        "reason": "params.reason",
                        "rebooked_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "new_flight": "params.new_flight_number",
                        "message": "Passenger rebooked successfully",
                    },
                },
            ],
        },
        {
            "name": "add_special_request",
            "description": "Add Special Service Request (SSR) to booking",
            "toolType": "write",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR",
                },
                "passenger_name": {
                    "type": "string",
                    "required": True,
                    "description": "Passenger name",
                },
                "request_type": {
                    "type": "string",
                    "required": True,
                    "description": "Type of special request",
                    "enum": ["wheelchair", "meal_vegetarian", "meal_vegan", "meal_halal", "meal_kosher", "meal_gluten_free", "bassinet", "unaccompanied_minor", "pet_in_cabin", "medical_oxygen"],
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
                    "condition": "shared.bookings[params.pnr] != null",
                    "errorMessage": "Booking not found",
                },
                {
                    "type": "update",
                    "target": "shared.bookings[params.pnr].special_requests",
                    "operation": "append",
                    "value": {
                        "type": "params.request_type",
                        "details": "params.details",
                        "passenger_name": "params.passenger_name",
                        "status": "confirmed",
                        "added_at": "timestamp()",
                    },
                },
                {
                    "type": "return",
                    "value": {
                        "success": True,
                        "request_type": "params.request_type",
                        "message": "Special request added successfully",
                    },
                },
            ],
        },
    ],
}

# =============================================================================
# Emirates Customer Mobile App - Customer Only
# =============================================================================

EMIRATES_APP = {
    "app_id": "emirates_app",
    "name": "Emirates Mobile App",
    "description": "Customer-facing Emirates mobile app for managing trips, boarding passes, Skywards miles, and preferences",
    "category": "custom",
    "icon": "✈️",
    "access_type": "role_restricted",
    "allowed_roles": ["customer"],
    "state_type": "per_agent",
    "state_schema": [
        {"name": "my_trips", "type": "array", "default": [], "perAgent": True, "description": "Customer's upcoming and past trips"},
        {"name": "skywards_dashboard", "type": "object", "default": {}, "perAgent": True, "description": "Skywards account dashboard"},
        {"name": "chauffeur_bookings", "type": "array", "default": [], "perAgent": True, "description": "Customer's chauffeur service bookings"},
        {"name": "lounge_passes", "type": "array", "default": [], "perAgent": True, "description": "Customer's lounge access passes"},
        {"name": "icoupons", "type": "array", "default": [], "perAgent": True, "description": "Customer's iCoupon vouchers"},
        {"name": "preferences", "type": "object", "default": {}, "perAgent": True, "description": "Customer preferences"},
        {"name": "boarding_pass_visible", "type": "boolean", "default": False, "perAgent": True, "description": "Is boarding pass displayed"},
        {"name": "checked_in", "type": "boolean", "default": False, "perAgent": True, "description": "Online check-in completed"},
    ],
    "actions": [
        # ==== READ ACTIONS ====
        {
            "name": "view_my_trips",
            "description": "View upcoming and past trips",
            "toolType": "read",
            "parameters": {
                "filter": {
                    "type": "string",
                    "required": False,
                    "default": "upcoming",
                    "description": "Filter: upcoming, past, or all",
                    "enum": ["upcoming", "past", "all"],
                },
            },
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "trips": "agent.my_trips",
                        "filter": "params.filter",
                    },
                },
            ],
        },
        {
            "name": "show_boarding_pass",
            "description": "Display mobile boarding pass for a trip",
            "toolType": "read",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR",
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "agent.checked_in == true",
                    "errorMessage": "Please check in first to view boarding pass",
                },
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
                        "pnr": "params.pnr",
                        "message": "Boarding pass is now displayed on screen",
                    },
                },
            ],
        },
        {
            "name": "view_skywards_dashboard",
            "description": "View Skywards miles balance, tier status, and benefits",
            "toolType": "read",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "dashboard": "agent.skywards_dashboard",
                    },
                },
            ],
        },
        {
            "name": "view_chauffeur_bookings",
            "description": "View chauffeur service bookings",
            "toolType": "read",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "bookings": "agent.chauffeur_bookings",
                    },
                },
            ],
        },
        {
            "name": "view_lounge_passes",
            "description": "View active lounge access passes",
            "toolType": "read",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "passes": "agent.lounge_passes",
                    },
                },
            ],
        },
        {
            "name": "view_icoupons",
            "description": "View iCoupon compensation vouchers",
            "toolType": "read",
            "parameters": {},
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "coupons": "agent.icoupons",
                    },
                },
            ],
        },
        # ==== WRITE ACTIONS ====
        {
            "name": "redeem_miles_upgrade",
            "description": "Submit request to redeem Skywards miles for cabin upgrade",
            "toolType": "write",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR",
                },
                "target_cabin": {
                    "type": "string",
                    "required": True,
                    "description": "Target cabin class",
                    "enum": ["business", "first"],
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "agent.skywards_dashboard.miles_balance != null",
                    "errorMessage": "Skywards account not linked",
                },
                {
                    "type": "return",
                    "value": {
                        "submitted": True,
                        "pnr": "params.pnr",
                        "target_cabin": "params.target_cabin",
                        "message": "Upgrade request submitted. Please wait for confirmation.",
                    },
                },
            ],
        },
        {
            "name": "submit_upgrade_bid",
            "description": "Submit Emirates Plus upgrade bid",
            "toolType": "write",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR",
                },
                "bid_amount": {
                    "type": "number",
                    "required": True,
                    "description": "Bid amount in USD",
                },
                "target_cabin": {
                    "type": "string",
                    "required": True,
                    "description": "Target cabin class",
                    "enum": ["business", "first"],
                },
            },
            "logic": [
                {
                    "type": "validate",
                    "condition": "params.bid_amount >= 100",
                    "errorMessage": "Minimum bid amount is $100",
                },
                {
                    "type": "return",
                    "value": {
                        "submitted": True,
                        "pnr": "params.pnr",
                        "bid_amount": "params.bid_amount",
                        "target_cabin": "params.target_cabin",
                        "message": "Upgrade bid submitted. You will be notified of the outcome 24-48 hours before departure.",
                    },
                },
            ],
        },
        {
            "name": "confirm_chauffeur_pickup",
            "description": "Confirm chauffeur pickup details",
            "toolType": "write",
            "parameters": {
                "booking_id": {
                    "type": "string",
                    "required": True,
                    "description": "Chauffeur booking ID",
                },
                "confirmed": {
                    "type": "boolean",
                    "required": True,
                    "description": "Confirm the booking",
                },
                "updated_address": {
                    "type": "string",
                    "required": False,
                    "description": "Updated pickup address if needed",
                },
            },
            "logic": [
                {
                    "type": "return",
                    "value": {
                        "confirmed": "params.confirmed",
                        "booking_id": "params.booking_id",
                        "message": "Chauffeur booking confirmed",
                    },
                },
            ],
        },
        {
            "name": "online_checkin",
            "description": "Complete online check-in for flight",
            "toolType": "write",
            "parameters": {
                "pnr": {
                    "type": "string",
                    "required": True,
                    "description": "Booking PNR",
                },
                "seat_preference": {
                    "type": "string",
                    "required": False,
                    "description": "Seat preference: window, aisle, middle",
                    "enum": ["window", "aisle", "middle"],
                },
            },
            "logic": [
                {
                    "type": "update",
                    "target": "agent.checked_in",
                    "operation": "set",
                    "value": True,
                },
                {
                    "type": "return",
                    "value": {
                        "checked_in": True,
                        "pnr": "params.pnr",
                        "message": "Check-in complete. Your boarding pass is now available.",
                    },
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
                    "description": "Preferred seat type",
                    "enum": ["window", "aisle", "middle"],
                },
                "meal_preference": {
                    "type": "string",
                    "required": False,
                    "description": "Preferred meal type",
                    "enum": ["regular", "vegetarian", "vegan", "halal", "kosher", "gluten_free"],
                },
                "communication_language": {
                    "type": "string",
                    "required": False,
                    "description": "Preferred language",
                },
                "notification_email": {
                    "type": "boolean",
                    "required": False,
                    "description": "Receive email notifications",
                },
                "notification_sms": {
                    "type": "boolean",
                    "required": False,
                    "description": "Receive SMS notifications",
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
                    "type": "branch",
                    "condition": "params.communication_language != null",
                    "then": [
                        {
                            "type": "update",
                            "target": "agent.preferences.language",
                            "operation": "set",
                            "value": "params.communication_language",
                        },
                    ],
                },
                {
                    "type": "return",
                    "value": {
                        "updated": True,
                        "preferences": "agent.preferences",
                    },
                },
            ],
        },
    ],
}


# =============================================================================
# Emirates App Collections
# =============================================================================

EMIRATES_APPS = {
    "emirates_backend": EMIRATES_BACKEND,
    "emirates_app": EMIRATES_APP,
}


def get_emirates_apps() -> dict[str, dict]:
    """Get all Emirates app definitions.

    Returns:
        Dictionary of Emirates app definitions
    """
    return EMIRATES_APPS.copy()


def get_emirates_app(app_id: str) -> dict | None:
    """Get a specific Emirates app definition.

    Args:
        app_id: App ID

    Returns:
        App definition or None
    """
    return EMIRATES_APPS.get(app_id)


def get_emirates_backend_app() -> dict:
    """Get the Emirates backend CRM app definition.

    Returns:
        Emirates backend app definition
    """
    return EMIRATES_BACKEND


def get_emirates_customer_app() -> dict:
    """Get the Emirates customer mobile app definition.

    Returns:
        Emirates customer app definition
    """
    return EMIRATES_APP
