"""PayPal simulated application.

This module implements a simulated PayPal app for testing agent
interactions with payment functionality per ADR-017.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any

from agentworld.apps.base import (
    AppAction,
    AppResult,
    BaseSimulatedApp,
    ParamSpec,
    get_app_registry,
)


@dataclass
class Transaction:
    """A PayPal transaction."""

    id: str
    type: str  # "sent", "received"
    counterparty: str  # Agent ID
    counterparty_email: str
    amount: float
    note: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "counterparty": self.counterparty,
            "counterparty_email": self.counterparty_email,
            "amount": self.amount,
            "note": self.note,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        else:
            timestamp = datetime.now(UTC)

        return cls(
            id=data["id"],
            type=data["type"],
            counterparty=data["counterparty"],
            counterparty_email=data["counterparty_email"],
            amount=data["amount"],
            note=data.get("note", ""),
            timestamp=timestamp,
        )


@dataclass
class PaymentRequest:
    """A payment request."""

    id: str
    from_agent: str  # Requester agent ID
    from_email: str
    to_agent: str  # Target agent ID
    to_email: str
    amount: float
    note: str
    status: str = "pending"  # "pending", "paid", "declined"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "from_email": self.from_email,
            "to_agent": self.to_agent,
            "to_email": self.to_email,
            "amount": self.amount,
            "note": self.note,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaymentRequest":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now(UTC)

        resolved_at = data.get("resolved_at")
        if isinstance(resolved_at, str):
            resolved_at = datetime.fromisoformat(resolved_at)

        return cls(
            id=data["id"],
            from_agent=data["from_agent"],
            from_email=data["from_email"],
            to_agent=data["to_agent"],
            to_email=data["to_email"],
            amount=data["amount"],
            note=data.get("note", ""),
            status=data.get("status", "pending"),
            created_at=created_at,
            resolved_at=resolved_at,
        )


@dataclass
class PayPalAccount:
    """A PayPal account for an agent."""

    agent_id: str
    email: str
    balance: float
    transactions: list[Transaction] = field(default_factory=list)
    pending_requests_from: list[str] = field(default_factory=list)  # Request IDs where this agent requested
    pending_requests_to: list[str] = field(default_factory=list)  # Request IDs where this agent is target

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "email": self.email,
            "balance": self.balance,
            "transactions": [t.to_dict() for t in self.transactions],
            "pending_requests_from": self.pending_requests_from,
            "pending_requests_to": self.pending_requests_to,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PayPalAccount":
        """Create from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            email=data["email"],
            balance=data["balance"],
            transactions=[Transaction.from_dict(t) for t in data.get("transactions", [])],
            pending_requests_from=data.get("pending_requests_from", []),
            pending_requests_to=data.get("pending_requests_to", []),
        )


class PayPalApp(BaseSimulatedApp):
    """Simulated PayPal application.

    Provides digital payment functionality including:
    - Checking balance
    - Sending money (transfers)
    - Requesting money
    - Paying/declining requests
    - Viewing transaction history
    """

    def __init__(self):
        """Initialize PayPal app."""
        super().__init__()
        self._accounts: dict[str, PayPalAccount] = {}
        self._requests: dict[str, PaymentRequest] = {}
        self._email_to_agent: dict[str, str] = {}  # email -> agent_id

    @property
    def app_id(self) -> str:
        """Unique ID for this app."""
        return "paypal"

    @property
    def name(self) -> str:
        """Display name for this app."""
        return "PayPal"

    @property
    def description(self) -> str:
        """Description for agent context."""
        return (
            "Digital payment platform for sending and receiving money. "
            "You can check your balance, transfer money to other users, "
            "request money from others, and view your transaction history."
        )

    def get_actions(self) -> list[AppAction]:
        """Get available actions."""
        return [
            AppAction(
                name="check_balance",
                description="View your current PayPal balance",
                parameters={},
                returns={"balance": "number"},
            ),
            AppAction(
                name="transfer",
                description="Send money to another user",
                parameters={
                    "to": ParamSpec(
                        name="to",
                        type="string",
                        description="Email address or agent ID of the recipient",
                        required=True,
                    ),
                    "amount": ParamSpec(
                        name="amount",
                        type="number",
                        description="Amount to send (must be positive)",
                        required=True,
                        min_value=0.01,
                    ),
                    "note": ParamSpec(
                        name="note",
                        type="string",
                        description="Optional note for the transfer",
                        required=False,
                        default="",
                        max_length=500,
                    ),
                },
                returns={"transaction_id": "string", "new_balance": "number"},
            ),
            AppAction(
                name="request_money",
                description="Request payment from another user",
                parameters={
                    "from": ParamSpec(
                        name="from",
                        type="string",
                        description="Email address or agent ID to request from",
                        required=True,
                    ),
                    "amount": ParamSpec(
                        name="amount",
                        type="number",
                        description="Amount to request (must be positive)",
                        required=True,
                        min_value=0.01,
                    ),
                    "note": ParamSpec(
                        name="note",
                        type="string",
                        description="Optional note explaining the request",
                        required=False,
                        default="",
                        max_length=500,
                    ),
                },
                returns={"request_id": "string"},
            ),
            AppAction(
                name="view_transactions",
                description="View recent transaction history",
                parameters={
                    "limit": ParamSpec(
                        name="limit",
                        type="number",
                        description="Maximum number of transactions to return",
                        required=False,
                        default=10,
                        min_value=1,
                        max_value=100,
                    ),
                },
                returns={"transactions": "array"},
            ),
            AppAction(
                name="pay_request",
                description="Pay a pending payment request",
                parameters={
                    "request_id": ParamSpec(
                        name="request_id",
                        type="string",
                        description="ID of the request to pay",
                        required=True,
                    ),
                },
                returns={"transaction_id": "string", "new_balance": "number"},
            ),
            AppAction(
                name="decline_request",
                description="Decline a pending payment request",
                parameters={
                    "request_id": ParamSpec(
                        name="request_id",
                        type="string",
                        description="ID of the request to decline",
                        required=True,
                    ),
                },
                returns={"success": "boolean"},
            ),
        ]

    async def _initialize_state(
        self,
        agents: list[str],
        config: dict[str, Any],
    ) -> None:
        """Initialize PayPal accounts for all agents."""
        initial_balance = config.get("initial_balance", 1000.0)

        self._accounts.clear()
        self._requests.clear()
        self._email_to_agent.clear()

        for agent_id in agents:
            # Generate email from agent ID
            email = f"{agent_id}@paypal-sim.example.com"

            account = PayPalAccount(
                agent_id=agent_id,
                email=email,
                balance=initial_balance,
            )
            self._accounts[agent_id] = account
            self._email_to_agent[email] = agent_id
            self._email_to_agent[agent_id] = agent_id  # Allow lookup by ID too

    def _resolve_recipient(self, identifier: str) -> str | None:
        """Resolve email or agent ID to agent ID.

        Args:
            identifier: Email address or agent ID

        Returns:
            Agent ID or None if not found
        """
        # Direct agent ID lookup
        if identifier in self._accounts:
            return identifier

        # Email lookup
        return self._email_to_agent.get(identifier)

    async def _execute_action(
        self,
        agent_id: str,
        action: str,
        params: dict[str, Any],
    ) -> AppResult:
        """Execute a PayPal action."""
        # Verify agent has an account
        if agent_id not in self._accounts:
            return AppResult.fail(f"No PayPal account found for agent {agent_id}")

        account = self._accounts[agent_id]

        if action == "check_balance":
            return await self._check_balance(account)
        elif action == "transfer":
            return await self._transfer(account, params)
        elif action == "request_money":
            return await self._request_money(account, params)
        elif action == "view_transactions":
            return await self._view_transactions(account, params)
        elif action == "pay_request":
            return await self._pay_request(account, params)
        elif action == "decline_request":
            return await self._decline_request(account, params)
        else:
            return AppResult.fail(f"Unknown action: {action}")

    async def _check_balance(self, account: PayPalAccount) -> AppResult:
        """Check account balance."""
        return AppResult.ok({
            "balance": round(account.balance, 2),
            "email": account.email,
        })

    async def _transfer(
        self,
        account: PayPalAccount,
        params: dict[str, Any],
    ) -> AppResult:
        """Transfer money to another user."""
        recipient_id = params.get("to", "")
        amount = params.get("amount", 0)
        note = params.get("note", "")

        # Resolve recipient
        resolved_recipient = self._resolve_recipient(recipient_id)
        if resolved_recipient is None:
            return AppResult.fail(f"User not found: {recipient_id}")

        if resolved_recipient == account.agent_id:
            return AppResult.fail("Cannot transfer money to yourself")

        recipient_account = self._accounts[resolved_recipient]

        # Check balance
        if amount > account.balance:
            return AppResult.fail(
                f"Insufficient funds. Your balance is ${account.balance:.2f}, "
                f"but you tried to send ${amount:.2f}"
            )

        # Execute transfer
        transaction_id = f"tx-{uuid.uuid4().hex[:8]}"

        # Deduct from sender
        account.balance -= amount
        sender_transaction = Transaction(
            id=transaction_id,
            type="sent",
            counterparty=resolved_recipient,
            counterparty_email=recipient_account.email,
            amount=amount,
            note=note,
        )
        account.transactions.append(sender_transaction)

        # Add to recipient
        recipient_account.balance += amount
        recipient_transaction = Transaction(
            id=transaction_id,
            type="received",
            counterparty=account.agent_id,
            counterparty_email=account.email,
            amount=amount,
            note=note,
        )
        recipient_account.transactions.append(recipient_transaction)

        # Send observation to recipient
        self.add_observation(
            agent_id=resolved_recipient,
            message=f"You received ${amount:.2f} from {account.email}" + (f": '{note}'" if note else ""),
            data={
                "type": "received",
                "amount": amount,
                "from": account.agent_id,
                "from_email": account.email,
                "transaction_id": transaction_id,
                "note": note,
            },
            priority=10,
        )

        return AppResult.ok({
            "transaction_id": transaction_id,
            "new_balance": round(account.balance, 2),
            "amount_sent": amount,
            "recipient": recipient_account.email,
        })

    async def _request_money(
        self,
        account: PayPalAccount,
        params: dict[str, Any],
    ) -> AppResult:
        """Request money from another user."""
        target_id = params.get("from", "")
        amount = params.get("amount", 0)
        note = params.get("note", "")

        # Resolve target
        resolved_target = self._resolve_recipient(target_id)
        if resolved_target is None:
            return AppResult.fail(f"User not found: {target_id}")

        if resolved_target == account.agent_id:
            return AppResult.fail("Cannot request money from yourself")

        target_account = self._accounts[resolved_target]

        # Create request
        request_id = f"req-{uuid.uuid4().hex[:8]}"
        request = PaymentRequest(
            id=request_id,
            from_agent=account.agent_id,
            from_email=account.email,
            to_agent=resolved_target,
            to_email=target_account.email,
            amount=amount,
            note=note,
        )
        self._requests[request_id] = request

        # Track in accounts
        account.pending_requests_from.append(request_id)
        target_account.pending_requests_to.append(request_id)

        # Send observation to target
        note_text = f" for '{note}'" if note else ""
        self.add_observation(
            agent_id=resolved_target,
            message=f"{account.email} requested ${amount:.2f} from you{note_text}",
            data={
                "type": "request",
                "request_id": request_id,
                "amount": amount,
                "from": account.agent_id,
                "from_email": account.email,
                "note": note,
            },
            priority=8,
        )

        return AppResult.ok({
            "request_id": request_id,
            "amount": amount,
            "to": target_account.email,
        })

    async def _view_transactions(
        self,
        account: PayPalAccount,
        params: dict[str, Any],
    ) -> AppResult:
        """View transaction history."""
        limit = params.get("limit", 10)

        # Get most recent transactions
        transactions = sorted(
            account.transactions,
            key=lambda t: t.timestamp,
            reverse=True,
        )[:limit]

        return AppResult.ok({
            "transactions": [t.to_dict() for t in transactions],
            "total_count": len(account.transactions),
        })

    async def _pay_request(
        self,
        account: PayPalAccount,
        params: dict[str, Any],
    ) -> AppResult:
        """Pay a pending request."""
        request_id = params.get("request_id", "")

        # Find request
        request = self._requests.get(request_id)
        if request is None:
            return AppResult.fail(f"Request not found: {request_id}")

        # Verify this agent is the target of the request
        if request.to_agent != account.agent_id:
            return AppResult.fail("This request is not addressed to you")

        # Check status
        if request.status != "pending":
            return AppResult.fail(f"Request already {request.status}")

        # Check balance
        if request.amount > account.balance:
            return AppResult.fail(
                f"Insufficient funds. Your balance is ${account.balance:.2f}, "
                f"but the request is for ${request.amount:.2f}"
            )

        requester_account = self._accounts[request.from_agent]

        # Execute payment
        transaction_id = f"tx-{uuid.uuid4().hex[:8]}"

        # Deduct from payer
        account.balance -= request.amount
        payer_transaction = Transaction(
            id=transaction_id,
            type="sent",
            counterparty=request.from_agent,
            counterparty_email=requester_account.email,
            amount=request.amount,
            note=f"Payment for request: {request.note}" if request.note else "Payment for request",
        )
        account.transactions.append(payer_transaction)

        # Add to requester
        requester_account.balance += request.amount
        requester_transaction = Transaction(
            id=transaction_id,
            type="received",
            counterparty=account.agent_id,
            counterparty_email=account.email,
            amount=request.amount,
            note=f"Request paid: {request.note}" if request.note else "Request paid",
        )
        requester_account.transactions.append(requester_transaction)

        # Update request status
        request.status = "paid"
        request.resolved_at = datetime.now(UTC)

        # Remove from pending lists
        if request_id in account.pending_requests_to:
            account.pending_requests_to.remove(request_id)
        if request_id in requester_account.pending_requests_from:
            requester_account.pending_requests_from.remove(request_id)

        # Send observation to requester
        self.add_observation(
            agent_id=request.from_agent,
            message=f"{account.email} paid your ${request.amount:.2f} request",
            data={
                "type": "request_paid",
                "request_id": request_id,
                "amount": request.amount,
                "from": account.agent_id,
                "from_email": account.email,
                "transaction_id": transaction_id,
            },
            priority=10,
        )

        return AppResult.ok({
            "transaction_id": transaction_id,
            "new_balance": round(account.balance, 2),
            "amount_paid": request.amount,
            "paid_to": requester_account.email,
        })

    async def _decline_request(
        self,
        account: PayPalAccount,
        params: dict[str, Any],
    ) -> AppResult:
        """Decline a pending request."""
        request_id = params.get("request_id", "")

        # Find request
        request = self._requests.get(request_id)
        if request is None:
            return AppResult.fail(f"Request not found: {request_id}")

        # Verify this agent is the target of the request
        if request.to_agent != account.agent_id:
            return AppResult.fail("This request is not addressed to you")

        # Check status
        if request.status != "pending":
            return AppResult.fail(f"Request already {request.status}")

        requester_account = self._accounts[request.from_agent]

        # Update request status
        request.status = "declined"
        request.resolved_at = datetime.now(UTC)

        # Remove from pending lists
        if request_id in account.pending_requests_to:
            account.pending_requests_to.remove(request_id)
        if request_id in requester_account.pending_requests_from:
            requester_account.pending_requests_from.remove(request_id)

        # Send observation to requester
        self.add_observation(
            agent_id=request.from_agent,
            message=f"{account.email} declined your ${request.amount:.2f} request",
            data={
                "type": "request_declined",
                "request_id": request_id,
                "amount": request.amount,
                "declined_by": account.agent_id,
                "declined_by_email": account.email,
            },
            priority=5,
        )

        return AppResult.ok({
            "success": True,
            "request_id": request_id,
        })

    async def get_agent_state(self, agent_id: str) -> dict[str, Any]:
        """Get the agent's view of PayPal state."""
        if agent_id not in self._accounts:
            return {"error": "No account found"}

        account = self._accounts[agent_id]

        # Get pending requests info
        pending_to_pay = []
        for req_id in account.pending_requests_to:
            req = self._requests.get(req_id)
            if req:
                pending_to_pay.append({
                    "request_id": req.id,
                    "from": req.from_email,
                    "amount": req.amount,
                    "note": req.note,
                    "created_at": req.created_at.isoformat(),
                })

        pending_from_others = []
        for req_id in account.pending_requests_from:
            req = self._requests.get(req_id)
            if req:
                pending_from_others.append({
                    "request_id": req.id,
                    "to": req.to_email,
                    "amount": req.amount,
                    "note": req.note,
                    "status": req.status,
                    "created_at": req.created_at.isoformat(),
                })

        return {
            "email": account.email,
            "balance": round(account.balance, 2),
            "transaction_count": len(account.transactions),
            "recent_transactions": [t.to_dict() for t in account.transactions[-5:]],
            "pending_requests_to_pay": pending_to_pay,
            "pending_requests_from_others": pending_from_others,
        }

    def _get_state_dict(self) -> dict[str, Any]:
        """Get app state as dictionary for serialization."""
        return {
            "accounts": {
                agent_id: account.to_dict()
                for agent_id, account in self._accounts.items()
            },
            "requests": {
                req_id: req.to_dict()
                for req_id, req in self._requests.items()
            },
            "email_to_agent": self._email_to_agent,
        }

    def _restore_state_dict(self, state: dict[str, Any]) -> None:
        """Restore app state from dictionary."""
        self._accounts = {
            agent_id: PayPalAccount.from_dict(data)
            for agent_id, data in state.get("accounts", {}).items()
        }
        self._requests = {
            req_id: PaymentRequest.from_dict(data)
            for req_id, data in state.get("requests", {}).items()
        }
        self._email_to_agent = state.get("email_to_agent", {})


# Register with the app registry
def register_paypal_app() -> None:
    """Register PayPal app with the registry."""
    registry = get_app_registry()
    registry.register(PayPalApp)
