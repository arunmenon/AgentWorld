# ADR-015: Reasoning and Prompt Visibility Policy

## Status
Accepted

## Dependencies
- **[ADR-003](./ADR-003-llm-architecture.md)**: LLM calls and prompts
- **[ADR-006](./ADR-006-dual-memory.md)**: Agent internal state
- **[ADR-007](./ADR-007-visualization.md)**: Display in UI
- **[ADR-013](./ADR-013-security.md)**: Sensitive data handling

## Context

**Critical Gap Identified:**
No defined policy for:
- Whether LLM prompts are visible in logs/exports
- How agent "thinking" is captured and displayed
- What reasoning traces are stored vs ephemeral
- Privacy implications of exposing internal prompts

**Visibility Layers:**

| Layer | Content | Sensitivity |
|-------|---------|-------------|
| System prompts | Agent persona, instructions | Medium |
| User prompts | Step context, memory retrieval | Low |
| LLM responses | Full model output | Low-Medium |
| Reasoning traces | Chain-of-thought, tool use | Medium |
| Internal state | Memory embeddings, scores | Low |

**Use Cases for Visibility:**
1. **Debugging**: Why did agent X say Y?
2. **Research**: Analyze reasoning patterns
3. **Auditing**: Verify agent behavior
4. **Transparency**: Explain AI decisions to users
5. **Privacy**: Protect proprietary prompts

**Tension Points:**
- Researchers want full visibility for reproducibility
- Enterprises want to protect prompt engineering
- Users want to understand agent behavior
- Developers need debugging capabilities

## Decision

Implement **configurable visibility levels** with structured reasoning capture and export controls.

### Visibility Levels

```python
from enum import Enum

class VisibilityLevel(str, Enum):
    """Visibility levels for reasoning and prompts."""

    NONE = "none"           # No internal details exposed
    SUMMARY = "summary"     # High-level summaries only
    DETAILED = "detailed"   # Full reasoning, redacted prompts
    FULL = "full"           # Everything including raw prompts
    DEBUG = "debug"         # Full + internal scores, embeddings

@dataclass
class VisibilityConfig:
    """Configuration for reasoning visibility."""

    # Live display (CLI/Web)
    live_visibility: VisibilityLevel = VisibilityLevel.SUMMARY

    # Logging
    log_visibility: VisibilityLevel = VisibilityLevel.DETAILED

    # Export/persistence
    export_visibility: VisibilityLevel = VisibilityLevel.SUMMARY

    # What to capture
    capture_system_prompts: bool = True
    capture_chain_of_thought: bool = True
    capture_tool_calls: bool = True
    capture_memory_retrieval: bool = True

    # Redaction
    redact_api_keys: bool = True
    redact_custom_patterns: List[str] = field(default_factory=list)
```

### Reasoning Trace Structure

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class ReasoningStep:
    """Single step in agent reasoning."""
    step_type: str  # "prompt", "completion", "tool_call", "memory_retrieval"
    timestamp: datetime
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReasoningTrace:
    """Complete reasoning trace for an agent action."""
    agent_id: str
    simulation_step: int
    action_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Reasoning steps
    steps: List[ReasoningStep] = field(default_factory=list)

    # Summary (always available)
    summary: Optional[str] = None

    # Outcome
    final_action: Optional[str] = None
    tokens_used: int = 0
    latency_ms: int = 0

    def add_step(self, step: ReasoningStep) -> None:
        self.steps.append(step)

    def to_dict(self, visibility: VisibilityLevel) -> dict:
        """Export trace at specified visibility level."""
        base = {
            "agent_id": self.agent_id,
            "simulation_step": self.simulation_step,
            "action_id": self.action_id,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
        }

        if visibility == VisibilityLevel.NONE:
            return base

        if visibility in (VisibilityLevel.SUMMARY, VisibilityLevel.DETAILED,
                          VisibilityLevel.FULL, VisibilityLevel.DEBUG):
            base["summary"] = self.summary
            base["final_action"] = self.final_action

        if visibility in (VisibilityLevel.DETAILED, VisibilityLevel.FULL,
                          VisibilityLevel.DEBUG):
            base["steps"] = [
                self._format_step(s, visibility) for s in self.steps
            ]

        if visibility == VisibilityLevel.DEBUG:
            base["metadata"] = {
                "started_at": self.started_at.isoformat(),
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            }

        return base

    def _format_step(self, step: ReasoningStep, visibility: VisibilityLevel) -> dict:
        result = {
            "type": step.step_type,
            "timestamp": step.timestamp.isoformat(),
        }

        if visibility == VisibilityLevel.FULL or visibility == VisibilityLevel.DEBUG:
            result["content"] = step.content
            result["metadata"] = step.metadata
        elif visibility == VisibilityLevel.DETAILED:
            # Redact sensitive content
            result["content"] = self._redact_content(step.content)
            result["metadata"] = {
                k: v for k, v in step.metadata.items()
                if k not in ("raw_prompt", "api_key")
            }

        return result
```

### Reasoning Capture

```python
class ReasoningCapture:
    """Captures reasoning traces during agent execution."""

    def __init__(self, config: VisibilityConfig):
        self.config = config
        self._current_trace: Optional[ReasoningTrace] = None

    @contextmanager
    def trace(self, agent_id: str, simulation_step: int) -> Generator[ReasoningTrace, None, None]:
        """Context manager for capturing a reasoning trace."""
        self._current_trace = ReasoningTrace(
            agent_id=agent_id,
            simulation_step=simulation_step,
            action_id=str(uuid.uuid4()),
            started_at=datetime.utcnow()
        )

        try:
            yield self._current_trace
        finally:
            self._current_trace.completed_at = datetime.utcnow()
            self._emit_trace(self._current_trace)
            self._current_trace = None

    def log_prompt(self, prompt: str, prompt_type: str = "user") -> None:
        """Log a prompt being sent to LLM."""
        if not self._current_trace:
            return

        if not self.config.capture_system_prompts and prompt_type == "system":
            return

        self._current_trace.add_step(ReasoningStep(
            step_type="prompt",
            timestamp=datetime.utcnow(),
            content=prompt,
            metadata={"prompt_type": prompt_type}
        ))

    def log_completion(self, completion: str, tokens: int) -> None:
        """Log LLM completion."""
        if not self._current_trace:
            return

        self._current_trace.tokens_used += tokens
        self._current_trace.add_step(ReasoningStep(
            step_type="completion",
            timestamp=datetime.utcnow(),
            content=completion,
            metadata={"tokens": tokens}
        ))

    def log_tool_call(self, tool_name: str, input: dict, output: str) -> None:
        """Log agent tool usage."""
        if not self._current_trace or not self.config.capture_tool_calls:
            return

        self._current_trace.add_step(ReasoningStep(
            step_type="tool_call",
            timestamp=datetime.utcnow(),
            content=f"Tool: {tool_name}\nInput: {json.dumps(input)}\nOutput: {output}",
            metadata={"tool": tool_name, "input": input}
        ))

    def log_memory_retrieval(
        self,
        query: str,
        retrieved: List[Memory],
        scores: List[float]
    ) -> None:
        """Log memory retrieval for context."""
        if not self._current_trace or not self.config.capture_memory_retrieval:
            return

        self._current_trace.add_step(ReasoningStep(
            step_type="memory_retrieval",
            timestamp=datetime.utcnow(),
            content=f"Query: {query}\nRetrieved {len(retrieved)} memories",
            metadata={
                "query": query,
                "memory_ids": [m.id for m in retrieved],
                "scores": scores
            }
        ))

    def log_chain_of_thought(self, thought: str) -> None:
        """Log intermediate reasoning."""
        if not self._current_trace or not self.config.capture_chain_of_thought:
            return

        self._current_trace.add_step(ReasoningStep(
            step_type="chain_of_thought",
            timestamp=datetime.utcnow(),
            content=thought,
            metadata={}
        ))

    def set_summary(self, summary: str) -> None:
        """Set human-readable summary of reasoning."""
        if self._current_trace:
            self._current_trace.summary = summary

    def set_final_action(self, action: str) -> None:
        """Set the final action taken."""
        if self._current_trace:
            self._current_trace.final_action = action
```

### Integration with Agent

```python
class Agent:
    def __init__(self, ..., reasoning_capture: ReasoningCapture):
        self.reasoning = reasoning_capture

    async def act(self, step: int) -> AgentAction:
        """Execute agent action with reasoning capture."""
        with self.reasoning.trace(self.id, step) as trace:
            # Retrieve relevant memories
            query = self._get_context_query()
            memories, scores = await self.memory.retrieve(query, k=10)
            self.reasoning.log_memory_retrieval(query, memories, scores)

            # Build prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(memories)
            self.reasoning.log_prompt(system_prompt, "system")
            self.reasoning.log_prompt(user_prompt, "user")

            # Call LLM
            response = await self.llm.complete(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            self.reasoning.log_completion(response.content, response.tokens)

            # Parse and potentially use tools
            action = self._parse_action(response.content)
            if action.tool_call:
                tool_result = await self._execute_tool(action.tool_call)
                self.reasoning.log_tool_call(
                    action.tool_call.name,
                    action.tool_call.input,
                    tool_result
                )

            # Set summary for display
            self.reasoning.set_summary(
                f"{self.name} decided to: {action.summary}"
            )
            self.reasoning.set_final_action(action.content)

            return action
```

### Display in CLI (ADR-007)

```python
class CLIReasoningDisplay:
    """Display reasoning in CLI based on visibility level."""

    def __init__(self, console: Console, visibility: VisibilityLevel):
        self.console = console
        self.visibility = visibility

    def display_trace(self, trace: ReasoningTrace) -> None:
        """Display reasoning trace in CLI."""
        if self.visibility == VisibilityLevel.NONE:
            return

        # Always show summary
        self.console.print(
            f"[dim]{trace.agent_id}[/dim] {trace.summary or trace.final_action}"
        )

        if self.visibility == VisibilityLevel.SUMMARY:
            return

        # Show thinking indicator
        if self.visibility in (VisibilityLevel.DETAILED, VisibilityLevel.FULL):
            with self.console.status(f"[dim]{trace.agent_id} thinking...[/dim]"):
                for step in trace.steps:
                    self._display_step(step)

    def _display_step(self, step: ReasoningStep) -> None:
        """Display individual reasoning step."""
        if step.step_type == "chain_of_thought":
            self.console.print(f"  [italic dim]💭 {step.content[:100]}...[/italic dim]")

        elif step.step_type == "tool_call":
            tool = step.metadata.get("tool", "unknown")
            self.console.print(f"  [cyan]🔧 Using tool: {tool}[/cyan]")

        elif step.step_type == "memory_retrieval":
            count = len(step.metadata.get("memory_ids", []))
            self.console.print(f"  [dim]📚 Retrieved {count} memories[/dim]")

        elif step.step_type == "prompt" and self.visibility == VisibilityLevel.FULL:
            self.console.print(Panel(
                step.content[:500] + "..." if len(step.content) > 500 else step.content,
                title=f"Prompt ({step.metadata.get('prompt_type', 'user')})",
                border_style="dim"
            ))
```

### WebSocket Events for Reasoning

```python
# Extend ADR-012 event schema
class ReasoningEventType(str, Enum):
    THINKING_START = "reasoning.thinking_start"
    THINKING_STEP = "reasoning.thinking_step"
    THINKING_END = "reasoning.thinking_end"
    TOOL_CALL = "reasoning.tool_call"
    MEMORY_ACCESS = "reasoning.memory_access"

# Event payloads
{
    "type": "reasoning.thinking_start",
    "payload": {
        "agent_id": "lisa",
        "agent_name": "Lisa",
        "simulation_step": 15
    }
}

{
    "type": "reasoning.thinking_step",
    "payload": {
        "agent_id": "lisa",
        "step_type": "chain_of_thought",
        "content": "Considering the user's question about pricing..."  # Redacted based on visibility
    }
}

{
    "type": "reasoning.thinking_end",
    "payload": {
        "agent_id": "lisa",
        "summary": "Lisa decided to express concern about the price point",
        "tokens_used": 234,
        "latency_ms": 1250
    }
}
```

### Storage and Export

```python
class ReasoningStorage:
    """Store and export reasoning traces."""

    def __init__(self, db_session, config: VisibilityConfig):
        self.db = db_session
        self.config = config

    async def store(self, trace: ReasoningTrace) -> None:
        """Store reasoning trace to database."""
        # Store at configured export visibility level
        trace_dict = trace.to_dict(self.config.export_visibility)

        await self.db.execute(
            insert(ReasoningTraceModel).values(
                id=trace.action_id,
                agent_id=trace.agent_id,
                simulation_step=trace.simulation_step,
                trace_data=json.dumps(trace_dict),
                visibility_level=self.config.export_visibility.value,
                created_at=trace.started_at
            )
        )
        await self.db.commit()

    async def export(
        self,
        simulation_id: str,
        visibility: VisibilityLevel,
        format: str = "jsonl"
    ) -> str:
        """Export reasoning traces for simulation."""
        traces = await self.db.execute(
            select(ReasoningTraceModel)
            .where(ReasoningTraceModel.simulation_id == simulation_id)
            .order_by(ReasoningTraceModel.created_at)
        )

        # Re-filter based on requested visibility
        # (can only reduce visibility from stored level)
        output = []
        for trace_model in traces:
            stored_level = VisibilityLevel(trace_model.visibility_level)
            effective_level = min(visibility, stored_level, key=lambda l: list(VisibilityLevel).index(l))

            if effective_level != VisibilityLevel.NONE:
                trace_dict = json.loads(trace_model.trace_data)
                # Re-apply visibility filter
                filtered = self._filter_to_visibility(trace_dict, effective_level)
                output.append(filtered)

        if format == "jsonl":
            return "\n".join(json.dumps(t) for t in output)
        elif format == "json":
            return json.dumps(output, indent=2)

    def _filter_to_visibility(self, trace: dict, visibility: VisibilityLevel) -> dict:
        """Filter trace data to visibility level."""
        if visibility == VisibilityLevel.SUMMARY:
            return {
                "agent_id": trace["agent_id"],
                "simulation_step": trace["simulation_step"],
                "summary": trace.get("summary"),
                "final_action": trace.get("final_action")
            }
        # Additional filtering logic...
        return trace
```

### YAML Configuration

```yaml
visibility:
  # Display levels
  live:
    level: summary          # What to show in CLI/Web during execution
    show_thinking: true     # Show "agent thinking..." indicator
    show_tool_calls: true   # Show tool usage

  logging:
    level: detailed         # What to write to logs
    include_prompts: true   # Include prompts (will be redacted)
    include_completions: true

  export:
    level: summary          # What to include in exports
    include_reasoning_traces: false  # Store traces to DB

  # Capture configuration
  capture:
    system_prompts: true
    chain_of_thought: true
    tool_calls: true
    memory_retrieval: true

  # Redaction
  redaction:
    api_keys: true
    custom_patterns:
      - '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Emails
```

### Privacy Considerations

```python
class PrivacyManager:
    """Manage privacy aspects of reasoning visibility."""

    def __init__(self, config: VisibilityConfig):
        self.config = config
        self._redaction_patterns = self._compile_patterns()

    def _compile_patterns(self) -> List[re.Pattern]:
        """Compile redaction patterns."""
        patterns = []

        if self.config.redact_api_keys:
            patterns.append(re.compile(r'(sk-[a-zA-Z0-9]{20,})'))
            patterns.append(re.compile(r'(Bearer\s+[a-zA-Z0-9\-_.]+)'))

        for custom in self.config.redact_custom_patterns:
            patterns.append(re.compile(custom))

        return patterns

    def redact(self, text: str) -> str:
        """Redact sensitive information from text."""
        for pattern in self._redaction_patterns:
            text = pattern.sub("[REDACTED]", text)
        return text

    def should_capture(self, content_type: str) -> bool:
        """Check if content type should be captured."""
        mapping = {
            "system_prompt": self.config.capture_system_prompts,
            "chain_of_thought": self.config.capture_chain_of_thought,
            "tool_call": self.config.capture_tool_calls,
            "memory_retrieval": self.config.capture_memory_retrieval,
        }
        return mapping.get(content_type, True)

    def filter_for_export(self, trace: ReasoningTrace) -> ReasoningTrace:
        """Filter trace for export based on privacy settings."""
        # Apply redaction to all text content
        for step in trace.steps:
            step.content = self.redact(step.content)

        return trace
```

## Consequences

**Positive:**
- Clear policy for what's visible at each layer
- Configurable for different use cases (research vs production)
- Structured traces enable analysis
- Privacy protection via redaction
- Debug capability when needed

**Negative:**
- Performance overhead from trace capture
- Storage requirements for full traces
- Complexity in visibility filtering

**Tradeoffs:**
- Transparency vs privacy
- Debug capability vs storage costs
- Real-time display vs performance

## Related ADRs
- [ADR-003](./ADR-003-llm-architecture.md): LLM calls
- [ADR-006](./ADR-006-dual-memory.md): Memory access
- [ADR-007](./ADR-007-visualization.md): Display
- [ADR-013](./ADR-013-security.md): Redaction
