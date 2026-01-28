"""Unit tests for dual-control task domain models (ADR-020.1).

Test Suites:
1. InstructionTemplate - Keyword matching and serialization
2. CoordinationHandoff - Handoff matching and serialization
3. DualControlTaskDefinition - Task structure and serialization
4. CoordinationEvent - Event tracking and serialization
5. CoordinationMetrics - Metrics computation
6. SoloDualComparison - Performance comparison
7. Example Tasks - Verify task examples are valid
"""

import pytest
from datetime import datetime

from agentworld.apps.definition import AgentRole
from agentworld.tasks.dual_control import (
    InstructionTemplate,
    CoordinationHandoff,
    DualControlTaskDefinition,
    CoordinationEvent,
    CoordinationMetrics,
    SoloDualComparison,
    TOGGLE_DATA_TEMPLATE,
    CHECK_STATUS_TEMPLATE,
    RESTART_DEVICE_TEMPLATE,
    TOGGLE_AIRPLANE_TEMPLATE,
)


# =============================================================================
# Test Suite 1: InstructionTemplate
# =============================================================================


class TestInstructionTemplate:
    """Tests for InstructionTemplate matching and serialization."""

    def test_matches_both_keywords(self):
        """Template matches when both action and target keywords are present."""
        template = InstructionTemplate(
            template_id="test_toggle",
            keywords=["toggle", "turn", "switch"],
            target_keywords=["data", "mobile data"],
        )

        matched, confidence = template.matches("Please toggle the mobile data setting")
        assert matched is True
        assert confidence == 0.95

    def test_matches_case_insensitive(self):
        """Matching is case-insensitive."""
        template = InstructionTemplate(
            template_id="test_toggle",
            keywords=["toggle"],
            target_keywords=["data"],
        )

        matched, confidence = template.matches("TOGGLE the DATA")
        assert matched is True

    def test_no_match_missing_action_keyword(self):
        """No match when action keyword is missing."""
        template = InstructionTemplate(
            template_id="test_toggle",
            keywords=["toggle"],
            target_keywords=["data"],
        )

        matched, confidence = template.matches("Please check the data setting")
        assert matched is False
        assert confidence == 0.0

    def test_no_match_missing_target_keyword(self):
        """No match when target keyword is missing."""
        template = InstructionTemplate(
            template_id="test_toggle",
            keywords=["toggle"],
            target_keywords=["data"],
        )

        matched, confidence = template.matches("Please toggle the setting")
        assert matched is False
        assert confidence == 0.0

    def test_to_dict_and_from_dict(self):
        """Template can be serialized and deserialized."""
        template = InstructionTemplate(
            template_id="test_template",
            keywords=["check", "view"],
            target_keywords=["status", "display"],
            semantic_threshold=0.9,
        )

        data = template.to_dict()
        restored = InstructionTemplate.from_dict(data)

        assert restored.template_id == template.template_id
        assert restored.keywords == template.keywords
        assert restored.target_keywords == template.target_keywords
        assert restored.semantic_threshold == template.semantic_threshold


class TestPredefinedTemplates:
    """Test the predefined instruction templates."""

    def test_toggle_data_template(self):
        """TOGGLE_DATA_TEMPLATE matches toggle data instructions."""
        matched, _ = TOGGLE_DATA_TEMPLATE.matches("Turn on mobile data please")
        assert matched is True

        matched, _ = TOGGLE_DATA_TEMPLATE.matches("Disable the cellular internet")
        assert matched is True

    def test_check_status_template(self):
        """CHECK_STATUS_TEMPLATE matches check status instructions."""
        matched, _ = CHECK_STATUS_TEMPLATE.matches("Check the signal status bar")
        assert matched is True

        matched, _ = CHECK_STATUS_TEMPLATE.matches("What does the screen display show?")
        assert matched is True

    def test_restart_device_template(self):
        """RESTART_DEVICE_TEMPLATE matches restart instructions."""
        matched, _ = RESTART_DEVICE_TEMPLATE.matches("Please restart your phone")
        assert matched is True

        matched, _ = RESTART_DEVICE_TEMPLATE.matches("Power cycle the device")
        assert matched is True

    def test_toggle_airplane_template(self):
        """TOGGLE_AIRPLANE_TEMPLATE matches airplane mode instructions."""
        matched, _ = TOGGLE_AIRPLANE_TEMPLATE.matches("Toggle airplane mode")
        assert matched is True

        matched, _ = TOGGLE_AIRPLANE_TEMPLATE.matches("Turn off flight mode")
        assert matched is True


# =============================================================================
# Test Suite 2: CoordinationHandoff
# =============================================================================


class TestCoordinationHandoff:
    """Tests for CoordinationHandoff matching and serialization."""

    def test_matches_with_template(self):
        """Handoff matches instruction using template."""
        handoff = CoordinationHandoff(
            handoff_id="toggle_data_handoff",
            from_role=AgentRole.SERVICE_AGENT,
            to_role=AgentRole.CUSTOMER,
            expected_action="toggle_data",
            instruction_template=InstructionTemplate(
                template_id="toggle_data",
                keywords=["toggle"],
                target_keywords=["data"],
            ),
        )

        matched, confidence = handoff.matches_instruction("Please toggle mobile data")
        assert matched is True
        assert confidence == 0.95

    def test_matches_with_regex_pattern(self):
        """Handoff matches instruction using regex pattern."""
        handoff = CoordinationHandoff(
            handoff_id="check_booking_handoff",
            from_role=AgentRole.SERVICE_AGENT,
            to_role=AgentRole.CUSTOMER,
            expected_action="view_my_trips",
            instruction_pattern=r"check.*booking|verify.*reservation",
        )

        matched, confidence = handoff.matches_instruction("Please check your booking")
        assert matched is True
        assert confidence == 0.90

    def test_no_match_wrong_instruction(self):
        """Handoff doesn't match unrelated instruction."""
        handoff = CoordinationHandoff(
            handoff_id="toggle_data_handoff",
            from_role=AgentRole.SERVICE_AGENT,
            to_role=AgentRole.CUSTOMER,
            expected_action="toggle_data",
            instruction_template=TOGGLE_DATA_TEMPLATE,
        )

        matched, confidence = handoff.matches_instruction("How are you today?")
        assert matched is False

    def test_to_dict_and_from_dict(self):
        """Handoff can be serialized and deserialized."""
        handoff = CoordinationHandoff(
            handoff_id="test_handoff",
            from_role=AgentRole.SERVICE_AGENT,
            to_role=AgentRole.CUSTOMER,
            expected_action="test_action",
            description="Test handoff description",
            instruction_pattern=r"test.*pattern",
            instruction_template=InstructionTemplate(
                template_id="test",
                keywords=["test"],
                target_keywords=["action"],
            ),
        )

        data = handoff.to_dict()
        restored = CoordinationHandoff.from_dict(data)

        assert restored.handoff_id == handoff.handoff_id
        assert restored.from_role == handoff.from_role
        assert restored.to_role == handoff.to_role
        assert restored.expected_action == handoff.expected_action
        assert restored.instruction_pattern == handoff.instruction_pattern
        assert restored.instruction_template.template_id == handoff.instruction_template.template_id


# =============================================================================
# Test Suite 3: DualControlTaskDefinition
# =============================================================================


class TestDualControlTaskDefinition:
    """Tests for DualControlTaskDefinition structure and serialization."""

    def create_sample_task(self) -> DualControlTaskDefinition:
        """Create a sample task for testing."""
        return DualControlTaskDefinition(
            task_id="test_task_001",
            name="Test Task",
            description="A test dual-control task",
            domain="airlines",
            difficulty="easy",
            simulation_config={"topology": "direct", "max_turns": 15},
            agent_id="service_agent_1",
            agent_role=AgentRole.SERVICE_AGENT,
            agent_instruction="Help the customer",
            agent_apps=["airlines_backend"],
            user_id="customer_1",
            user_role=AgentRole.CUSTOMER,
            user_instruction="Get help from agent",
            user_apps=["airlines_app"],
            agent_initial_state={"airlines_backend": {"shared": {}}},
            agent_goal_state={},
            user_initial_state={"airlines_app": {"per_agent": {}}},
            user_goal_state={},
            required_handoffs=[
                CoordinationHandoff(
                    handoff_id="handoff_1",
                    from_role=AgentRole.SERVICE_AGENT,
                    to_role=AgentRole.CUSTOMER,
                    expected_action="view_my_trips",
                )
            ],
            max_turns=15,
            expected_coordination_count=1,
            tags=["test", "airlines"],
        )

    def test_task_creation(self):
        """Task can be created with all fields."""
        task = self.create_sample_task()

        assert task.task_id == "test_task_001"
        assert task.domain == "airlines"
        assert task.difficulty == "easy"
        assert len(task.required_handoffs) == 1
        assert task.is_active is True

    def test_task_roles(self):
        """Task roles are correctly set."""
        task = self.create_sample_task()

        assert task.agent_role == AgentRole.SERVICE_AGENT
        assert task.user_role == AgentRole.CUSTOMER

    def test_task_apps(self):
        """Task apps are correctly set."""
        task = self.create_sample_task()

        assert "airlines_backend" in task.agent_apps
        assert "airlines_app" in task.user_apps

    def test_to_dict_and_from_dict(self):
        """Task can be serialized and deserialized."""
        task = self.create_sample_task()
        task.created_at = datetime.now()
        task.updated_at = datetime.now()

        data = task.to_dict()
        restored = DualControlTaskDefinition.from_dict(data)

        assert restored.task_id == task.task_id
        assert restored.name == task.name
        assert restored.domain == task.domain
        assert restored.agent_role == task.agent_role
        assert restored.user_role == task.user_role
        assert len(restored.required_handoffs) == len(task.required_handoffs)
        assert restored.tags == task.tags


# =============================================================================
# Test Suite 4: CoordinationEvent
# =============================================================================


class TestCoordinationEvent:
    """Tests for CoordinationEvent tracking and serialization."""

    def test_event_creation(self):
        """Event can be created with all fields."""
        event = CoordinationEvent(
            event_id="evt_001",
            trial_id="trial_001",
            task_id="task_001",
            instructor_id="agent_1",
            instructor_role=AgentRole.SERVICE_AGENT,
            instruction_text="Please check your booking",
            actor_id="customer_1",
            actor_role=AgentRole.CUSTOMER,
            action_taken="view_my_trips",
            action_params={"confirmation_code": "ABC123"},
            matched_handoff_id="handoff_1",
            match_confidence=0.95,
            handoff_successful=True,
            latency_turns=2,
            timestamp=datetime.now(),
        )

        assert event.event_id == "evt_001"
        assert event.handoff_successful is True
        assert event.latency_turns == 2

    def test_event_without_action(self):
        """Event can be created without action (user didn't act)."""
        event = CoordinationEvent(
            event_id="evt_002",
            trial_id="trial_001",
            task_id="task_001",
            instructor_id="agent_1",
            instructor_role=AgentRole.SERVICE_AGENT,
            instruction_text="Please toggle the data",
        )

        assert event.actor_id is None
        assert event.action_taken is None
        assert event.handoff_successful is False

    def test_to_dict_and_from_dict(self):
        """Event can be serialized and deserialized."""
        event = CoordinationEvent(
            event_id="evt_003",
            trial_id="trial_001",
            task_id="task_001",
            instructor_id="agent_1",
            instructor_role=AgentRole.SERVICE_AGENT,
            instruction_text="Test instruction",
            actor_id="customer_1",
            actor_role=AgentRole.CUSTOMER,
            action_taken="test_action",
            handoff_successful=True,
            latency_turns=3,
            timestamp=datetime.now(),
        )

        data = event.to_dict()
        restored = CoordinationEvent.from_dict(data)

        assert restored.event_id == event.event_id
        assert restored.instructor_role == event.instructor_role
        assert restored.handoff_successful == event.handoff_successful
        assert restored.latency_turns == event.latency_turns


# =============================================================================
# Test Suite 5: CoordinationMetrics
# =============================================================================


class TestCoordinationMetrics:
    """Tests for CoordinationMetrics computation."""

    def test_from_events_success_rate(self):
        """Metrics correctly calculate success rate."""
        events = [
            CoordinationEvent(
                event_id="evt_1",
                trial_id="t1",
                task_id="task_1",
                instructor_id="a1",
                instructor_role=AgentRole.SERVICE_AGENT,
                instruction_text="Instruction 1",
                handoff_successful=True,
                latency_turns=2,
            ),
            CoordinationEvent(
                event_id="evt_2",
                trial_id="t1",
                task_id="task_1",
                instructor_id="a1",
                instructor_role=AgentRole.SERVICE_AGENT,
                instruction_text="Instruction 2",
                handoff_successful=False,
            ),
        ]

        metrics = CoordinationMetrics.from_events(
            task_id="task_1",
            events=events,
            required_handoffs=2,
        )

        assert metrics.total_handoffs_required == 2
        assert metrics.handoffs_completed == 1
        assert metrics.coordination_success_rate == 0.5

    def test_from_events_avg_latency(self):
        """Metrics correctly calculate average latency."""
        events = [
            CoordinationEvent(
                event_id="evt_1",
                trial_id="t1",
                task_id="task_1",
                instructor_id="a1",
                instructor_role=AgentRole.SERVICE_AGENT,
                instruction_text="Instruction 1",
                handoff_successful=True,
                latency_turns=2,
            ),
            CoordinationEvent(
                event_id="evt_2",
                trial_id="t1",
                task_id="task_1",
                instructor_id="a1",
                instructor_role=AgentRole.SERVICE_AGENT,
                instruction_text="Instruction 2",
                handoff_successful=True,
                latency_turns=4,
            ),
        ]

        metrics = CoordinationMetrics.from_events(
            task_id="task_1",
            events=events,
            required_handoffs=2,
        )

        assert metrics.avg_instruction_to_action_turns == 3.0  # (2 + 4) / 2

    def test_from_events_empty(self):
        """Metrics handle empty event list."""
        metrics = CoordinationMetrics.from_events(
            task_id="task_1",
            events=[],
            required_handoffs=2,
        )

        assert metrics.handoffs_completed == 0
        assert metrics.coordination_success_rate == 0.0
        assert metrics.avg_instruction_to_action_turns == 0.0

    def test_to_dict(self):
        """Metrics can be serialized."""
        metrics = CoordinationMetrics(
            task_id="task_1",
            total_handoffs_required=5,
            handoffs_completed=4,
            coordination_success_rate=0.8,
            avg_instruction_to_action_turns=2.5,
            computed_at=datetime.now(),
        )

        data = metrics.to_dict()

        assert data["task_id"] == "task_1"
        assert data["coordination_success_rate"] == 0.8


# =============================================================================
# Test Suite 6: SoloDualComparison
# =============================================================================


class TestSoloDualComparison:
    """Tests for SoloDualComparison."""

    def test_compute_gaps(self):
        """Comparison correctly computes performance gap."""
        comparison = SoloDualComparison(
            task_id="task_1",
            solo_trials=10,
            solo_successes=6,
            solo_pass_1=0.6,
            solo_avg_steps=5.0,
            dual_trials=10,
            dual_successes=4,
            dual_pass_1=0.4,
            dual_avg_steps=8.0,
        )

        comparison.compute_gaps()

        assert abs(comparison.performance_drop - 0.2) < 0.0001  # 0.6 - 0.4
        assert comparison.step_increase == 3.0  # 8.0 - 5.0

    def test_to_dict_and_from_dict(self):
        """Comparison can be serialized and deserialized."""
        comparison = SoloDualComparison(
            task_id="task_1",
            solo_trials=10,
            solo_successes=6,
            solo_pass_1=0.6,
            solo_avg_steps=5.0,
            dual_trials=10,
            dual_successes=4,
            dual_pass_1=0.4,
            dual_avg_steps=8.0,
            performance_drop=0.2,
            step_increase=3.0,
            computed_at=datetime.now(),
        )

        data = comparison.to_dict()
        restored = SoloDualComparison.from_dict(data)

        assert restored.task_id == comparison.task_id
        assert restored.solo_pass_1 == comparison.solo_pass_1
        assert restored.dual_pass_1 == comparison.dual_pass_1
        assert restored.performance_drop == comparison.performance_drop


# =============================================================================
# Test Suite 7: Example Tasks
# =============================================================================


class TestExampleTasks:
    """Tests for the example dual-control tasks."""

    def test_airlines_tasks_exist(self):
        """Airlines example tasks are properly defined."""
        from agentworld.tasks.dual_control_examples import (
            AIRLINES_SEAT_CHANGE_TASK,
            AIRLINES_SPECIAL_ASSISTANCE_TASK,
        )

        assert AIRLINES_SEAT_CHANGE_TASK.task_id == "airlines_seat_change_001"
        assert AIRLINES_SEAT_CHANGE_TASK.domain == "airlines"
        assert AIRLINES_SEAT_CHANGE_TASK.difficulty == "easy"
        assert len(AIRLINES_SEAT_CHANGE_TASK.required_handoffs) == 1

        assert AIRLINES_SPECIAL_ASSISTANCE_TASK.task_id == "airlines_special_assistance_002"
        assert AIRLINES_SPECIAL_ASSISTANCE_TASK.difficulty == "medium"

    def test_paypal_tasks_exist(self):
        """PayPal example tasks are properly defined."""
        from agentworld.tasks.dual_control_examples import (
            PAYPAL_ENABLE_2FA_TASK,
            PAYPAL_DISPUTE_RESOLUTION_TASK,
            PAYPAL_ADD_CARD_TASK,
        )

        assert PAYPAL_ENABLE_2FA_TASK.task_id == "paypal_enable_2fa_001"
        assert PAYPAL_ENABLE_2FA_TASK.domain == "paypal"
        assert PAYPAL_ENABLE_2FA_TASK.difficulty == "easy"

        assert PAYPAL_DISPUTE_RESOLUTION_TASK.difficulty == "hard"
        assert len(PAYPAL_DISPUTE_RESOLUTION_TASK.required_handoffs) == 2

        assert PAYPAL_ADD_CARD_TASK.difficulty == "easy"

    def test_tasks_have_correct_roles(self):
        """Tasks have correct agent/user roles."""
        from agentworld.tasks.dual_control_examples import ALL_DUAL_CONTROL_TASKS

        for task in ALL_DUAL_CONTROL_TASKS:
            assert task.agent_role == AgentRole.SERVICE_AGENT
            assert task.user_role == AgentRole.CUSTOMER

    def test_tasks_have_correct_apps(self):
        """Tasks reference correct apps for each role."""
        from agentworld.tasks.dual_control_examples import (
            AIRLINES_SEAT_CHANGE_TASK,
            PAYPAL_ENABLE_2FA_TASK,
        )

        # Airlines task: agent uses backend, customer uses app
        assert "airlines_backend" in AIRLINES_SEAT_CHANGE_TASK.agent_apps
        assert "airlines_app" in AIRLINES_SEAT_CHANGE_TASK.user_apps

        # PayPal task: agent uses backend, customer uses app
        assert "paypal_backend" in PAYPAL_ENABLE_2FA_TASK.agent_apps
        assert "paypal_app" in PAYPAL_ENABLE_2FA_TASK.user_apps

    def test_get_tasks_by_domain(self):
        """get_tasks_by_domain returns correct tasks."""
        from agentworld.tasks.dual_control_examples import get_tasks_by_domain

        airlines_tasks = get_tasks_by_domain("airlines")
        assert len(airlines_tasks) == 2
        assert all(t.domain == "airlines" for t in airlines_tasks)

        paypal_tasks = get_tasks_by_domain("paypal")
        assert len(paypal_tasks) == 3
        assert all(t.domain == "paypal" for t in paypal_tasks)

    def test_get_tasks_by_difficulty(self):
        """get_tasks_by_difficulty returns correct tasks."""
        from agentworld.tasks.dual_control_examples import get_tasks_by_difficulty

        easy_tasks = get_tasks_by_difficulty("easy")
        assert len(easy_tasks) >= 3
        assert all(t.difficulty == "easy" for t in easy_tasks)

        hard_tasks = get_tasks_by_difficulty("hard")
        assert len(hard_tasks) >= 1
        assert all(t.difficulty == "hard" for t in hard_tasks)

    def test_get_task_by_id(self):
        """get_task_by_id returns correct task or None."""
        from agentworld.tasks.dual_control_examples import get_task_by_id

        task = get_task_by_id("airlines_seat_change_001")
        assert task is not None
        assert task.name == "Seat Change Request"

        task = get_task_by_id("nonexistent_task")
        assert task is None
