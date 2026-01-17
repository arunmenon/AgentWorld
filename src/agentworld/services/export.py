"""Export service for simulation data.

Provides export functionality for various fine-tuning and training data formats.
Supports: JSONL, OpenAI, Anthropic, ShareGPT, Alpaca, DPO pairs.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from agentworld.persistence.repository import Repository


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSONL = "jsonl"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    SHAREGPT = "sharegpt"
    ALPACA = "alpaca"
    DPO = "dpo"


class RedactionProfile(str, Enum):
    """Redaction profiles for privacy control."""
    NONE = "none"       # Nothing redacted (internal use only)
    BASIC = "basic"     # Debug traces, internal IDs, system prompts
    STRICT = "strict"   # + Persona background, agent names anonymized, PII patterns


@dataclass
class ExportManifest:
    """Export manifest for dataset integrity tracking."""
    manifest_version: str = "1.0"
    simulation_ids: list[str] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)
    config_hash: str = ""
    persona_panel_hash: str = ""
    seed: int | None = None
    exporter_version: str = "1.0.0"
    format_version: str = ""
    filters_applied: dict[str, Any] = field(default_factory=dict)
    record_count: int = 0
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "manifest_version": self.manifest_version,
            "simulation_ids": self.simulation_ids,
            "run_ids": self.run_ids,
            "config_hash": self.config_hash,
            "persona_panel_hash": self.persona_panel_hash,
            "seed": self.seed,
            "exporter_version": self.exporter_version,
            "format_version": self.format_version,
            "filters_applied": self.filters_applied,
            "record_count": self.record_count,
            "created_at": self.created_at,
        }


@dataclass
class DPOConfig:
    """Configuration for DPO pair generation."""
    source: str = "score_ranking"  # "score_ranking" | "ab_preference" | "multi_response"
    chosen_threshold: float = 0.75
    rejected_threshold: float = 0.25
    min_score_gap: float = 0.2


@dataclass
class ExportOptions:
    """Options for export operations."""
    redaction_profile: RedactionProfile = RedactionProfile.BASIC
    anonymize: bool = False
    min_score: float | None = None
    excluded_agents: list[str] = field(default_factory=list)
    include_manifest: bool = True
    dpo_config: DPOConfig | None = None


class ExportService:
    """Service for exporting simulation data to various formats."""

    # PII patterns for strict redaction
    PII_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
        (r'\b\d{3}[-]?\d{2}[-]?\d{4}\b', '[SSN]'),
        (r'\b(?:sk-|api[_-]?key[_-]?)[a-zA-Z0-9]{20,}\b', '[API_KEY]'),
    ]

    def __init__(self, repository: Repository | None = None):
        """Initialize export service.

        Args:
            repository: Repository for database access. If None, creates new one.
        """
        self._repo = repository

    @property
    def repo(self) -> Repository:
        """Get repository instance, creating if needed."""
        if self._repo is None:
            self._repo = Repository()
        return self._repo

    def _compute_hash(self, data: Any) -> str:
        """Compute SHA256 hash of data."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return f"sha256:{hashlib.sha256(json_str.encode()).hexdigest()[:16]}"

    def _redact_pii(self, text: str) -> str:
        """Redact PII patterns from text."""
        for pattern, replacement in self.PII_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def _apply_redaction(
        self,
        data: dict[str, Any],
        profile: RedactionProfile,
        anon_map: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Apply redaction profile to data.

        Args:
            data: Data to redact
            profile: Redaction profile to apply
            anon_map: Optional anonymization mapping for agent names

        Returns:
            Redacted data copy
        """
        if profile == RedactionProfile.NONE:
            return data

        result = dict(data)

        # Basic redaction: remove debug traces, internal IDs, system prompts
        if profile in (RedactionProfile.BASIC, RedactionProfile.STRICT):
            keys_to_remove = ['system_prompt', 'debug', 'internal_id', 'trace']
            for key in keys_to_remove:
                result.pop(key, None)

        # Strict redaction: anonymize names, redact background, PII
        if profile == RedactionProfile.STRICT:
            # Anonymize sender/receiver
            if anon_map:
                if 'sender_id' in result:
                    result['sender_id'] = anon_map.get(result['sender_id'], result['sender_id'])
                if 'receiver_id' in result:
                    result['receiver_id'] = anon_map.get(result['receiver_id'], result['receiver_id'])
                if 'name' in result:
                    result['name'] = anon_map.get(result['name'], result['name'])

            # Remove background
            result.pop('background', None)

            # Redact PII from content
            if 'content' in result and isinstance(result['content'], str):
                result['content'] = self._redact_pii(result['content'])

        return result

    def _get_simulation_data(
        self,
        simulation_id: str,
        options: ExportOptions
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict], dict[str, str]]:
        """Get simulation data with optional processing.

        Returns:
            Tuple of (simulation, agent_map, messages, anon_map)
        """
        sim = self.repo.get_simulation(simulation_id)
        if not sim:
            raise ValueError(f"Simulation not found: {simulation_id}")

        agents = self.repo.get_agents_for_simulation(simulation_id)
        agent_map = {a["id"]: a for a in agents}

        # Create anonymization mapping
        anon_map = {}
        if options.anonymize or options.redaction_profile == RedactionProfile.STRICT:
            for i, agent in enumerate(agents, 1):
                anon_map[agent["id"]] = f"Agent_{i}"
                anon_map[agent.get("name", "")] = f"Agent_{i}"

        messages = self.repo.get_messages_for_simulation(simulation_id)

        # Filter out excluded agents
        if options.excluded_agents:
            messages = [
                m for m in messages
                if m.get("sender_id") not in options.excluded_agents
            ]

        return sim, agent_map, messages, anon_map

    def _create_manifest(
        self,
        simulation_ids: list[str],
        format_name: str,
        record_count: int,
        options: ExportOptions
    ) -> ExportManifest:
        """Create export manifest."""
        # Gather config data for hashing
        configs = []
        personas = []
        for sim_id in simulation_ids:
            sim = self.repo.get_simulation(sim_id)
            if sim:
                configs.append(sim.get("config", {}))
                agents = self.repo.get_agents_for_simulation(sim_id)
                personas.extend([
                    {"name": a.get("name"), "traits": a.get("traits")}
                    for a in agents
                ])

        return ExportManifest(
            simulation_ids=simulation_ids,
            config_hash=self._compute_hash(configs),
            persona_panel_hash=self._compute_hash(personas),
            format_version=f"{format_name}-1.0",
            filters_applied={
                "min_score": options.min_score,
                "redaction_profile": options.redaction_profile.value,
                "excluded_agents": options.excluded_agents,
            },
            record_count=record_count,
            created_at=datetime.now(UTC).isoformat(),
        )

    def export_jsonl(
        self,
        simulation_id: str,
        options: ExportOptions | None = None
    ) -> list[dict[str, Any]]:
        """Export messages as JSONL format.

        Args:
            simulation_id: Simulation to export
            options: Export options

        Returns:
            List of message dictionaries
        """
        options = options or ExportOptions()
        sim, agent_map, messages, anon_map = self._get_simulation_data(simulation_id, options)

        result = []
        for msg in messages:
            record = {
                "sender": agent_map.get(msg["sender_id"], {}).get("name", msg["sender_id"]),
                "content": msg["content"],
                "step": msg.get("step", 0),
                "timestamp": msg.get("timestamp"),
            }
            if msg.get("receiver_id"):
                record["receiver"] = agent_map.get(msg["receiver_id"], {}).get("name", msg["receiver_id"])

            record = self._apply_redaction(record, options.redaction_profile, anon_map)
            result.append(record)

        return result

    def export_openai_format(
        self,
        simulation_id: str,
        options: ExportOptions | None = None
    ) -> list[dict[str, Any]]:
        """Export as OpenAI fine-tuning format.

        Format: {"messages": [{"role": "user"|"assistant", "content": "..."}]}

        Args:
            simulation_id: Simulation to export
            options: Export options

        Returns:
            List of conversation records in OpenAI format
        """
        options = options or ExportOptions()
        sim, agent_map, messages, anon_map = self._get_simulation_data(simulation_id, options)

        # Group messages into conversations by step
        conversations = []
        current_messages = []

        for msg in messages:
            sender_name = agent_map.get(msg["sender_id"], {}).get("name", msg["sender_id"])
            if anon_map:
                sender_name = anon_map.get(sender_name, sender_name)

            content = msg["content"]
            if options.redaction_profile == RedactionProfile.STRICT:
                content = self._redact_pii(content)

            # Alternate between user/assistant roles based on agent order
            role = "user" if len(current_messages) % 2 == 0 else "assistant"

            current_messages.append({
                "role": role,
                "content": f"[{sender_name}]: {content}" if role == "user" else content
            })

        if current_messages:
            conversations.append({"messages": current_messages})

        return conversations

    def export_anthropic_format(
        self,
        simulation_id: str,
        options: ExportOptions | None = None
    ) -> list[dict[str, Any]]:
        """Export as Anthropic fine-tuning format.

        Format: {"prompt": "Human: ...\n\nAssistant:", "completion": "..."}

        Args:
            simulation_id: Simulation to export
            options: Export options

        Returns:
            List of prompt/completion pairs
        """
        options = options or ExportOptions()
        sim, agent_map, messages, anon_map = self._get_simulation_data(simulation_id, options)

        result = []

        # Create prompt/completion pairs from sequential messages
        for i in range(0, len(messages) - 1, 2):
            prompt_msg = messages[i]
            completion_msg = messages[i + 1] if i + 1 < len(messages) else None

            if not completion_msg:
                continue

            prompt_sender = agent_map.get(prompt_msg["sender_id"], {}).get("name", prompt_msg["sender_id"])
            if anon_map:
                prompt_sender = anon_map.get(prompt_sender, prompt_sender)

            prompt_content = prompt_msg["content"]
            completion_content = completion_msg["content"]

            if options.redaction_profile == RedactionProfile.STRICT:
                prompt_content = self._redact_pii(prompt_content)
                completion_content = self._redact_pii(completion_content)

            result.append({
                "prompt": f"Human: [{prompt_sender}]: {prompt_content}\n\nAssistant:",
                "completion": f" {completion_content}"
            })

        return result

    def export_sharegpt_format(
        self,
        simulation_id: str,
        options: ExportOptions | None = None
    ) -> list[dict[str, Any]]:
        """Export as ShareGPT format for open-source models.

        Format: {"conversations": [{"from": "human"|"gpt", "value": "..."}]}

        Args:
            simulation_id: Simulation to export
            options: Export options

        Returns:
            List of conversations in ShareGPT format
        """
        options = options or ExportOptions()
        sim, agent_map, messages, anon_map = self._get_simulation_data(simulation_id, options)

        conversations = []
        current_conv = []

        for i, msg in enumerate(messages):
            sender_name = agent_map.get(msg["sender_id"], {}).get("name", msg["sender_id"])
            if anon_map:
                sender_name = anon_map.get(sender_name, sender_name)

            content = msg["content"]
            if options.redaction_profile == RedactionProfile.STRICT:
                content = self._redact_pii(content)

            # Alternate human/gpt based on position
            role = "human" if i % 2 == 0 else "gpt"

            current_conv.append({
                "from": role,
                "value": f"[{sender_name}]: {content}" if role == "human" else content
            })

        if current_conv:
            conversations.append({"conversations": current_conv})

        return conversations

    def export_alpaca_format(
        self,
        simulation_id: str,
        options: ExportOptions | None = None
    ) -> list[dict[str, Any]]:
        """Export as Alpaca instruction tuning format.

        Format: {"instruction": "...", "input": "...", "output": "..."}

        Args:
            simulation_id: Simulation to export
            options: Export options

        Returns:
            List of instruction/input/output records
        """
        options = options or ExportOptions()
        sim, agent_map, messages, anon_map = self._get_simulation_data(simulation_id, options)

        result = []

        # Create instruction pairs from sequential messages
        for i in range(0, len(messages) - 1, 2):
            input_msg = messages[i]
            output_msg = messages[i + 1] if i + 1 < len(messages) else None

            if not output_msg:
                continue

            input_sender = agent_map.get(input_msg["sender_id"], {}).get("name", input_msg["sender_id"])
            output_sender = agent_map.get(output_msg["sender_id"], {}).get("name", output_msg["sender_id"])

            if anon_map:
                input_sender = anon_map.get(input_sender, input_sender)
                output_sender = anon_map.get(output_sender, output_sender)

            input_content = input_msg["content"]
            output_content = output_msg["content"]

            if options.redaction_profile == RedactionProfile.STRICT:
                input_content = self._redact_pii(input_content)
                output_content = self._redact_pii(output_content)

            result.append({
                "instruction": f"Respond as {output_sender} to the following message from {input_sender}.",
                "input": input_content,
                "output": output_content
            })

        return result

    def export_dpo_pairs(
        self,
        simulation_id: str,
        evaluations: list[dict[str, Any]],
        options: ExportOptions | None = None
    ) -> list[dict[str, Any]]:
        """Export as DPO preference pairs format.

        Format: {"prompt": "...", "chosen": "...", "rejected": "..."}

        Requires evaluation scores to determine chosen/rejected responses.

        Args:
            simulation_id: Simulation to export
            evaluations: List of message evaluations with scores
            options: Export options

        Returns:
            List of DPO preference pairs
        """
        options = options or ExportOptions()
        dpo_config = options.dpo_config or DPOConfig()

        sim, agent_map, messages, anon_map = self._get_simulation_data(simulation_id, options)

        # Build evaluation score map
        eval_map: dict[str, float] = {}
        for e in evaluations:
            msg_id = e.get("message_id")
            score = e.get("score", 0.5)
            if msg_id:
                eval_map[msg_id] = score

        result = []

        if dpo_config.source == "score_ranking":
            # Group messages by prompt (previous message)
            prompt_responses: dict[str, list[dict]] = {}

            for i, msg in enumerate(messages):
                if i == 0:
                    continue

                prompt_msg = messages[i - 1]
                prompt_key = prompt_msg.get("id", str(i - 1))

                if prompt_key not in prompt_responses:
                    prompt_responses[prompt_key] = []

                score = eval_map.get(msg.get("id", ""), 0.5)
                prompt_responses[prompt_key].append({
                    "message": msg,
                    "score": score,
                    "prompt_msg": prompt_msg
                })

            # Generate DPO pairs from ranked responses
            for prompt_key, responses in prompt_responses.items():
                if len(responses) < 2:
                    continue

                # Sort by score
                responses.sort(key=lambda x: x["score"], reverse=True)

                chosen_candidates = [r for r in responses if r["score"] >= dpo_config.chosen_threshold]
                rejected_candidates = [r for r in responses if r["score"] <= dpo_config.rejected_threshold]

                if not chosen_candidates or not rejected_candidates:
                    continue

                for chosen in chosen_candidates:
                    for rejected in rejected_candidates:
                        score_gap = chosen["score"] - rejected["score"]
                        if score_gap < dpo_config.min_score_gap:
                            continue

                        prompt_content = chosen["prompt_msg"]["content"]
                        chosen_content = chosen["message"]["content"]
                        rejected_content = rejected["message"]["content"]

                        if options.redaction_profile == RedactionProfile.STRICT:
                            prompt_content = self._redact_pii(prompt_content)
                            chosen_content = self._redact_pii(chosen_content)
                            rejected_content = self._redact_pii(rejected_content)

                        result.append({
                            "prompt": prompt_content,
                            "chosen": chosen_content,
                            "rejected": rejected_content,
                            "chosen_score": chosen["score"],
                            "rejected_score": rejected["score"],
                        })

        return result

    def export_conversations(
        self,
        simulation_id: str,
        options: ExportOptions | None = None
    ) -> list[dict[str, Any]]:
        """Export messages grouped by conversation thread.

        Args:
            simulation_id: Simulation to export
            options: Export options

        Returns:
            List of conversation thread dictionaries
        """
        options = options or ExportOptions()
        sim, agent_map, messages, anon_map = self._get_simulation_data(simulation_id, options)

        # Group by step (treating each step as a conversation unit)
        conversations: dict[int, list[dict]] = {}

        for msg in messages:
            step = msg.get("step", 0)
            if step not in conversations:
                conversations[step] = []

            sender_name = agent_map.get(msg["sender_id"], {}).get("name", msg["sender_id"])
            if anon_map:
                sender_name = anon_map.get(sender_name, sender_name)

            content = msg["content"]
            if options.redaction_profile == RedactionProfile.STRICT:
                content = self._redact_pii(content)

            conversations[step].append({
                "sender": sender_name,
                "content": content,
                "timestamp": msg.get("timestamp"),
            })

        return [
            {"step": step, "messages": msgs}
            for step, msgs in sorted(conversations.items())
        ]

    def export_to_file(
        self,
        simulation_id: str,
        output_path: Path,
        format: ExportFormat,
        options: ExportOptions | None = None
    ) -> ExportManifest:
        """Export simulation data to file.

        Args:
            simulation_id: Simulation to export
            output_path: Output file path
            format: Export format
            options: Export options

        Returns:
            Export manifest
        """
        options = options or ExportOptions()

        # Get data based on format
        if format == ExportFormat.JSONL:
            data = self.export_jsonl(simulation_id, options)
        elif format == ExportFormat.OPENAI:
            data = self.export_openai_format(simulation_id, options)
        elif format == ExportFormat.ANTHROPIC:
            data = self.export_anthropic_format(simulation_id, options)
        elif format == ExportFormat.SHAREGPT:
            data = self.export_sharegpt_format(simulation_id, options)
        elif format == ExportFormat.ALPACA:
            data = self.export_alpaca_format(simulation_id, options)
        elif format == ExportFormat.DPO:
            # DPO requires evaluations - get from database if available
            evaluations = self.repo.get_evaluations_for_simulation(simulation_id)
            data = self.export_dpo_pairs(simulation_id, evaluations, options)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write data
        with open(output_path, "w") as f:
            for record in data:
                f.write(json.dumps(record, default=str) + "\n")

        # Create and write manifest
        manifest = self._create_manifest(
            simulation_ids=[simulation_id],
            format_name=format.value,
            record_count=len(data),
            options=options
        )

        if options.include_manifest:
            manifest_path = output_path.with_suffix(".manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(manifest.to_dict(), f, indent=2)

        return manifest

    def export_multi_simulation(
        self,
        simulation_ids: list[str],
        output_path: Path,
        format: ExportFormat,
        options: ExportOptions | None = None
    ) -> ExportManifest:
        """Export multiple simulations to a single file.

        Args:
            simulation_ids: List of simulation IDs to export
            output_path: Output file path
            format: Export format
            options: Export options

        Returns:
            Export manifest
        """
        options = options or ExportOptions()
        all_data = []

        for sim_id in simulation_ids:
            if format == ExportFormat.JSONL:
                data = self.export_jsonl(sim_id, options)
            elif format == ExportFormat.OPENAI:
                data = self.export_openai_format(sim_id, options)
            elif format == ExportFormat.ANTHROPIC:
                data = self.export_anthropic_format(sim_id, options)
            elif format == ExportFormat.SHAREGPT:
                data = self.export_sharegpt_format(sim_id, options)
            elif format == ExportFormat.ALPACA:
                data = self.export_alpaca_format(sim_id, options)
            elif format == ExportFormat.DPO:
                evaluations = self.repo.get_evaluations_for_simulation(sim_id)
                data = self.export_dpo_pairs(sim_id, evaluations, options)
            else:
                raise ValueError(f"Unsupported format: {format}")

            all_data.extend(data)

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write data
        with open(output_path, "w") as f:
            for record in all_data:
                f.write(json.dumps(record, default=str) + "\n")

        # Create and write manifest
        manifest = self._create_manifest(
            simulation_ids=simulation_ids,
            format_name=format.value,
            record_count=len(all_data),
            options=options
        )

        if options.include_manifest:
            manifest_path = output_path.with_suffix(".manifest.json")
            with open(manifest_path, "w") as f:
                json.dump(manifest.to_dict(), f, indent=2)

        return manifest
