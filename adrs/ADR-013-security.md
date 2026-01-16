# ADR-013: Security and Secrets Management

## Status
Accepted

## Dependencies
- **[ADR-003](./ADR-003-llm-architecture.md)**: API keys for LLM providers
- **[ADR-008](./ADR-008-persistence.md)**: Data at rest protection
- **[ADR-012](./ADR-012-api-event-schema.md)**: API authentication

## Context

**Critical Gap Identified:**
Security concerns are scattered across ADRs without unified policy:
- ADR-003 mentions API keys but not secure storage
- ADR-007 mentions basic auth but no implementation detail
- ADR-008 stores potentially sensitive data without encryption
- No guidance on PII handling in simulation outputs

**Security Requirements:**

| Requirement | Rationale |
|-------------|-----------|
| Secret storage | Secure API keys, tokens |
| Authentication | Web dashboard, API access |
| Authorization | Role-based access control |
| Data protection | Encryption at rest |
| PII handling | Agent data may contain sensitive info |
| Audit logging | Track access and changes |

**Threat Model:**

| Threat | Risk | Mitigation |
|--------|------|------------|
| API key exposure in logs | High | Redaction, secure storage |
| Unauthorized API access | Medium | Authentication, RBAC |
| Data breach of SQLite file | Medium | Encryption at rest |
| PII in exported data | Medium | Redaction options |
| Injection via agent input | Low | Input validation |

## Decision

Implement **layered security model** with secure secret storage, token-based authentication, and optional encryption.

### Secret Storage

```python
from abc import ABC, abstractmethod
import os
import keyring
from cryptography.fernet import Fernet

class SecretProvider(ABC):
    """Abstract interface for secret retrieval."""

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Retrieve secret by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """Store secret (if supported)."""
        pass

class EnvironmentSecretProvider(SecretProvider):
    """Secrets from environment variables (default)."""

    def __init__(self, prefix: str = "AGENTWORLD_"):
        self.prefix = prefix

    def get(self, key: str) -> Optional[str]:
        env_key = f"{self.prefix}{key.upper()}"
        return os.environ.get(env_key)

    def set(self, key: str, value: str) -> None:
        raise NotImplementedError("Cannot set environment variables at runtime")

class KeyringSecretProvider(SecretProvider):
    """Secrets from system keyring (macOS Keychain, Windows Credential Manager)."""

    SERVICE_NAME = "agentworld"

    def get(self, key: str) -> Optional[str]:
        try:
            return keyring.get_password(self.SERVICE_NAME, key)
        except keyring.errors.KeyringError:
            return None

    def set(self, key: str, value: str) -> None:
        keyring.set_password(self.SERVICE_NAME, key, value)

class FileSecretProvider(SecretProvider):
    """Secrets from encrypted file."""

    def __init__(self, path: str, master_key: bytes):
        self.path = path
        self.fernet = Fernet(master_key)
        self._cache: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path, 'rb') as f:
                encrypted = f.read()
            decrypted = self.fernet.decrypt(encrypted)
            self._cache = json.loads(decrypted)

    def _save(self) -> None:
        data = json.dumps(self._cache).encode()
        encrypted = self.fernet.encrypt(data)
        with open(self.path, 'wb') as f:
            f.write(encrypted)
        os.chmod(self.path, 0o600)  # Owner read/write only

    def get(self, key: str) -> Optional[str]:
        return self._cache.get(key)

    def set(self, key: str, value: str) -> None:
        self._cache[key] = value
        self._save()

class ChainedSecretProvider(SecretProvider):
    """Try multiple providers in order."""

    def __init__(self, providers: List[SecretProvider]):
        self.providers = providers

    def get(self, key: str) -> Optional[str]:
        for provider in self.providers:
            value = provider.get(key)
            if value is not None:
                return value
        return None

    def set(self, key: str, value: str) -> None:
        # Set in first provider that supports it
        for provider in self.providers:
            try:
                provider.set(key, value)
                return
            except NotImplementedError:
                continue
        raise NotImplementedError("No provider supports setting secrets")

# Usage
secrets = ChainedSecretProvider([
    EnvironmentSecretProvider(),      # First: env vars
    KeyringSecretProvider(),          # Then: system keyring
    FileSecretProvider(               # Finally: encrypted file
        "~/.agentworld/secrets.enc",
        master_key=get_master_key()
    )
])

openai_key = secrets.get("OPENAI_API_KEY")
```

### Authentication

```python
from datetime import datetime, timedelta
import jwt
from passlib.hash import bcrypt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class AuthConfig:
    """Authentication configuration."""
    jwt_secret: str              # From secrets provider
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    require_auth: bool = True    # Can disable for local dev

class TokenPayload:
    """JWT token payload."""
    sub: str                     # User ID
    roles: List[str]             # User roles
    exp: datetime                # Expiration
    iat: datetime                # Issued at
    type: str                    # "access" or "refresh"

class AuthService:
    """Authentication service."""

    def __init__(self, config: AuthConfig, secrets: SecretProvider):
        self.config = config
        self.jwt_secret = secrets.get("JWT_SECRET")
        if not self.jwt_secret:
            self.jwt_secret = self._generate_jwt_secret()

    def create_access_token(self, user_id: str, roles: List[str]) -> str:
        """Create JWT access token."""
        payload = {
            "sub": user_id,
            "roles": roles,
            "exp": datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.config.jwt_algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token."""
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days),
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.config.jwt_algorithm)

    def verify_token(self, token: str, expected_type: str = "access") -> TokenPayload:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )
            if payload.get("type") != expected_type:
                raise InvalidTokenError(f"Expected {expected_type} token")
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(str(e))

# FastAPI dependency
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """FastAPI dependency for authenticated user."""
    if not auth_service.config.require_auth:
        return None  # Auth disabled

    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = auth_service.verify_token(credentials.credentials)
        return await get_user_by_id(payload.sub)
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Role-Based Access Control (RBAC)

```python
from enum import Enum
from functools import wraps

class Role(str, Enum):
    ADMIN = "admin"           # Full access
    OPERATOR = "operator"     # Run simulations, view all
    VIEWER = "viewer"         # View only
    API_USER = "api_user"     # Programmatic access

class Permission(str, Enum):
    # Simulation permissions
    SIMULATION_CREATE = "simulation:create"
    SIMULATION_READ = "simulation:read"
    SIMULATION_UPDATE = "simulation:update"
    SIMULATION_DELETE = "simulation:delete"
    SIMULATION_CONTROL = "simulation:control"  # start/stop/pause

    # Agent permissions
    AGENT_READ = "agent:read"
    AGENT_INJECT = "agent:inject"  # Inject stimuli

    # System permissions
    CONFIG_READ = "config:read"
    CONFIG_UPDATE = "config:update"
    SECRETS_MANAGE = "secrets:manage"
    USERS_MANAGE = "users:manage"

# Role -> Permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions

    Role.OPERATOR: {
        Permission.SIMULATION_CREATE,
        Permission.SIMULATION_READ,
        Permission.SIMULATION_UPDATE,
        Permission.SIMULATION_CONTROL,
        Permission.AGENT_READ,
        Permission.AGENT_INJECT,
        Permission.CONFIG_READ,
    },

    Role.VIEWER: {
        Permission.SIMULATION_READ,
        Permission.AGENT_READ,
        Permission.CONFIG_READ,
    },

    Role.API_USER: {
        Permission.SIMULATION_CREATE,
        Permission.SIMULATION_READ,
        Permission.SIMULATION_CONTROL,
        Permission.AGENT_READ,
    },
}

def require_permission(permission: Permission):
    """Decorator to require specific permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: User = None, **kwargs):
            if user is None:
                raise HTTPException(status_code=401)

            user_permissions = set()
            for role in user.roles:
                user_permissions |= ROLE_PERMISSIONS.get(Role(role), set())

            if permission not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission.value}"
                )

            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator

# Usage
@app.post("/api/v1/simulations")
@require_permission(Permission.SIMULATION_CREATE)
async def create_simulation(request: CreateSimulationRequest, user: User = Depends(get_current_user)):
    ...
```

### Data Protection

```python
from cryptography.fernet import Fernet
from sqlalchemy import TypeDecorator, LargeBinary

class EncryptedString(TypeDecorator):
    """SQLAlchemy type for encrypted string storage."""

    impl = LargeBinary
    cache_ok = True

    def __init__(self, key: bytes):
        super().__init__()
        self.fernet = Fernet(key)

    def process_bind_param(self, value: str, dialect) -> bytes:
        if value is None:
            return None
        return self.fernet.encrypt(value.encode())

    def process_result_value(self, value: bytes, dialect) -> str:
        if value is None:
            return None
        return self.fernet.decrypt(value).decode()

# Database encryption key management
class DatabaseEncryption:
    """Manage database encryption."""

    def __init__(self, secrets: SecretProvider):
        self.secrets = secrets
        self._key: Optional[bytes] = None

    @property
    def key(self) -> bytes:
        if self._key is None:
            key_b64 = self.secrets.get("DATABASE_ENCRYPTION_KEY")
            if key_b64:
                self._key = base64.b64decode(key_b64)
            else:
                # Generate and store new key
                self._key = Fernet.generate_key()
                self.secrets.set(
                    "DATABASE_ENCRYPTION_KEY",
                    base64.b64encode(self._key).decode()
                )
        return self._key

    def get_encrypted_type(self) -> EncryptedString:
        return EncryptedString(self.key)

# Usage in models (ADR-008)
class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    # Persona may contain PII - encrypt if configured
    persona_profile = Column(
        db_encryption.get_encrypted_type() if ENCRYPT_PII else JSON,
        nullable=False
    )
```

### Secret Redaction in Logs

```python
import re
import logging
from typing import Pattern

class SecretRedactingFilter(logging.Filter):
    """Logging filter that redacts secrets."""

    # Patterns to redact
    PATTERNS: List[tuple[str, Pattern]] = [
        ("API key", re.compile(r'(sk-[a-zA-Z0-9]{20,})')),
        ("Bearer token", re.compile(r'(Bearer\s+[a-zA-Z0-9\-_.]+)')),
        ("Password", re.compile(r'(password["\s:=]+)[^\s"]+', re.I)),
        ("Secret", re.compile(r'(secret["\s:=]+)[^\s"]+', re.I)),
    ]

    REDACTED = "[REDACTED]"

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._redact(str(record.msg))
        if record.args:
            record.args = tuple(
                self._redact(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True

    def _redact(self, text: str) -> str:
        for name, pattern in self.PATTERNS:
            text = pattern.sub(f"\\1{self.REDACTED}", text)
        return text

# Apply to all loggers
def setup_secure_logging():
    """Configure logging with secret redaction."""
    redact_filter = SecretRedactingFilter()

    for handler in logging.root.handlers:
        handler.addFilter(redact_filter)

    # Also add to new handlers
    logging.getLogger().addFilter(redact_filter)
```

### PII Handling in Exports

```python
from enum import Enum
from dataclasses import dataclass

class PIILevel(Enum):
    """PII handling levels for exports."""
    NONE = "none"           # No redaction
    MINIMAL = "minimal"     # Redact obvious PII (emails, phones)
    STANDARD = "standard"   # Redact names, locations
    STRICT = "strict"       # Anonymize all agent identifiers

@dataclass
class ExportConfig:
    """Configuration for data export."""
    pii_level: PIILevel = PIILevel.MINIMAL
    include_embeddings: bool = False
    include_llm_cache: bool = False

class DataExporter:
    """Export simulation data with PII handling."""

    def __init__(self, config: ExportConfig):
        self.config = config
        self._agent_map: Dict[str, str] = {}  # Original -> Anonymized

    def export_simulation(self, sim_id: str) -> dict:
        """Export simulation data with PII handling."""
        data = self._fetch_simulation_data(sim_id)

        if self.config.pii_level != PIILevel.NONE:
            data = self._apply_pii_redaction(data)

        return data

    def _apply_pii_redaction(self, data: dict) -> dict:
        """Apply PII redaction based on level."""
        if self.config.pii_level == PIILevel.MINIMAL:
            return self._redact_minimal(data)
        elif self.config.pii_level == PIILevel.STANDARD:
            return self._redact_standard(data)
        elif self.config.pii_level == PIILevel.STRICT:
            return self._anonymize_strict(data)
        return data

    def _redact_minimal(self, data: dict) -> dict:
        """Redact emails, phone numbers, SSN patterns."""
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        }

        def redact_text(text: str) -> str:
            for name, pattern in patterns.items():
                text = re.sub(pattern, f"[REDACTED_{name.upper()}]", text)
            return text

        return self._apply_to_strings(data, redact_text)

    def _anonymize_strict(self, data: dict) -> dict:
        """Full anonymization - replace agent IDs/names."""
        # Create anonymous mapping
        for agent in data.get("agents", []):
            original_id = agent["id"]
            if original_id not in self._agent_map:
                self._agent_map[original_id] = f"agent_{len(self._agent_map) + 1}"

            agent["id"] = self._agent_map[original_id]
            agent["name"] = f"Agent {self._agent_map[original_id].split('_')[1]}"

        # Apply to messages
        for message in data.get("messages", []):
            if message.get("sender_id") in self._agent_map:
                message["sender_id"] = self._agent_map[message["sender_id"]]
            if message.get("receiver_id") in self._agent_map:
                message["receiver_id"] = self._agent_map[message["receiver_id"]]

        return self._redact_minimal(data)  # Also apply minimal
```

### Audit Logging

```python
from datetime import datetime
from enum import Enum

class AuditAction(str, Enum):
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"

    # Simulations
    SIMULATION_CREATE = "simulation_create"
    SIMULATION_START = "simulation_start"
    SIMULATION_STOP = "simulation_stop"
    SIMULATION_DELETE = "simulation_delete"

    # Configuration
    CONFIG_UPDATE = "config_update"
    SECRET_ACCESS = "secret_access"
    SECRET_UPDATE = "secret_update"

    # Data
    EXPORT = "export"
    CHECKPOINT_RESTORE = "checkpoint_restore"

@dataclass
class AuditEntry:
    timestamp: datetime
    action: AuditAction
    user_id: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: dict
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool

class AuditLogger:
    """Audit logging service."""

    def __init__(self, db_session):
        self.db = db_session

    async def log(
        self,
        action: AuditAction,
        user: Optional[User],
        resource: Optional[tuple[str, str]] = None,
        details: dict = None,
        request: Optional[Request] = None,
        success: bool = True
    ) -> None:
        """Log an audit event."""
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            action=action,
            user_id=user.id if user else None,
            resource_type=resource[0] if resource else None,
            resource_id=resource[1] if resource else None,
            details=details or {},
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            success=success
        )

        # Persist to database
        await self.db.execute(
            insert(AuditLogModel).values(
                **asdict(entry)
            )
        )
        await self.db.commit()

        # Also log to file/stdout for immediate visibility
        logger.info(
            f"AUDIT: {action.value} by {entry.user_id or 'anonymous'} "
            f"on {entry.resource_type}/{entry.resource_id} "
            f"- {'SUCCESS' if success else 'FAILED'}"
        )

# Usage in endpoints
@app.post("/api/v1/simulations/{sim_id}/start")
async def start_simulation(
    sim_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    audit: AuditLogger = Depends(get_audit_logger)
):
    try:
        result = await simulation_service.start(sim_id)
        await audit.log(
            AuditAction.SIMULATION_START,
            user,
            resource=("simulation", sim_id),
            request=request
        )
        return result
    except Exception as e:
        await audit.log(
            AuditAction.SIMULATION_START,
            user,
            resource=("simulation", sim_id),
            details={"error": str(e)},
            request=request,
            success=False
        )
        raise
```

### YAML Configuration

```yaml
security:
  # Authentication
  auth:
    enabled: true
    jwt_expire_minutes: 60
    require_https: true  # Enforce HTTPS in production

  # Secret providers (tried in order)
  secrets:
    providers:
      - type: environment
        prefix: "AGENTWORLD_"
      - type: keyring
        service: "agentworld"
      - type: file
        path: "~/.agentworld/secrets.enc"

  # Data protection
  encryption:
    encrypt_pii: true
    encrypt_embeddings: false

  # PII handling
  pii:
    default_export_level: minimal  # none, minimal, standard, strict

  # Audit
  audit:
    enabled: true
    log_to_database: true
    log_to_file: true
    retention_days: 90

  # RBAC
  rbac:
    default_role: viewer
    # Users configured via environment or secrets
```

## Consequences

**Positive:**
- Secrets never in code or plain config files
- Flexible provider chain supports various deployment scenarios
- RBAC enables multi-user deployments
- Audit trail for compliance
- PII handling enables safer data sharing

**Negative:**
- Additional complexity for single-user local deployments
- Performance overhead from encryption
- Key management responsibility

**Tradeoffs:**
- Security vs convenience (can disable auth for local dev)
- Encryption overhead vs data protection
- Audit verbosity vs storage costs

## Related ADRs
- [ADR-003](./ADR-003-llm-architecture.md): API key usage
- [ADR-008](./ADR-008-persistence.md): Data storage
- [ADR-012](./ADR-012-api-event-schema.md): API authentication
