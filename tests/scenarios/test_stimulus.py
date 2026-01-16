"""Tests for stimulus injection system."""

import pytest
from datetime import datetime

from agentworld.scenarios.stimulus import (
    StimulusType,
    Stimulus,
    create_question,
    create_announcement,
    create_topic_change,
    create_prompt,
    StimulusInjector,
)


class TestStimulusType:
    """Tests for StimulusType enum."""

    def test_types_exist(self):
        """Test that all types exist."""
        assert StimulusType.QUESTION.value == "question"
        assert StimulusType.ANNOUNCEMENT.value == "announcement"
        assert StimulusType.PROMPT.value == "prompt"
        assert StimulusType.TOPIC_CHANGE.value == "topic_change"
        assert StimulusType.INSTRUCTION.value == "instruction"
        assert StimulusType.ENVIRONMENT.value == "environment"


class TestStimulus:
    """Tests for Stimulus dataclass."""

    def test_creation_minimal(self):
        """Test creating stimulus with minimal params."""
        stimulus = Stimulus(
            content="Hello everyone",
            stimulus_type=StimulusType.ANNOUNCEMENT,
        )

        assert stimulus.content == "Hello everyone"
        assert stimulus.stimulus_type == StimulusType.ANNOUNCEMENT
        assert stimulus.source == "system"
        assert stimulus.target_agents is None
        assert stimulus.is_broadcast

    def test_creation_targeted(self):
        """Test creating targeted stimulus."""
        stimulus = Stimulus(
            content="Question for you",
            stimulus_type=StimulusType.QUESTION,
            target_agents=["agent1", "agent2"],
            source="moderator",
        )

        assert stimulus.target_agents == ["agent1", "agent2"]
        assert not stimulus.is_broadcast

    def test_is_broadcast_empty_list(self):
        """Test is_broadcast with empty target list."""
        stimulus = Stimulus(
            content="Test",
            stimulus_type=StimulusType.ANNOUNCEMENT,
            target_agents=[],
        )

        assert stimulus.is_broadcast

    def test_to_dict(self):
        """Test conversion to dictionary."""
        stimulus = Stimulus(
            content="Test",
            stimulus_type=StimulusType.QUESTION,
            source="test",
            priority=5,
        )
        data = stimulus.to_dict()

        assert data["content"] == "Test"
        assert data["stimulus_type"] == "question"
        assert data["source"] == "test"
        assert data["priority"] == 5
        assert "id" in data

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "id": "stim123",
            "content": "Test question",
            "stimulus_type": "question",
            "source": "moderator",
            "target_agents": ["a1"],
            "priority": 3,
        }
        stimulus = Stimulus.from_dict(data)

        assert stimulus.id == "stim123"
        assert stimulus.content == "Test question"
        assert stimulus.stimulus_type == StimulusType.QUESTION
        assert stimulus.target_agents == ["a1"]
        assert stimulus.priority == 3


class TestCreateQuestion:
    """Tests for create_question function."""

    def test_basic_question(self):
        """Test creating basic question."""
        stimulus = create_question("What do you think?")

        assert stimulus.content == "What do you think?"
        assert stimulus.stimulus_type == StimulusType.QUESTION
        assert stimulus.source == "moderator"
        assert stimulus.is_broadcast

    def test_targeted_question(self):
        """Test creating targeted question."""
        stimulus = create_question(
            content="What's your opinion?",
            target_agents=["agent1"],
        )

        assert stimulus.target_agents == ["agent1"]
        assert not stimulus.is_broadcast


class TestCreateAnnouncement:
    """Tests for create_announcement function."""

    def test_basic_announcement(self):
        """Test creating basic announcement."""
        stimulus = create_announcement("Welcome everyone!")

        assert stimulus.content == "Welcome everyone!"
        assert stimulus.stimulus_type == StimulusType.ANNOUNCEMENT
        assert stimulus.source == "system"
        assert stimulus.is_broadcast

    def test_custom_source(self):
        """Test announcement with custom source."""
        stimulus = create_announcement(
            content="Important update",
            source="admin",
        )

        assert stimulus.source == "admin"


class TestCreateTopicChange:
    """Tests for create_topic_change function."""

    def test_topic_change(self):
        """Test creating topic change."""
        stimulus = create_topic_change("AI Ethics")

        assert "AI Ethics" in stimulus.content
        assert stimulus.stimulus_type == StimulusType.TOPIC_CHANGE
        assert stimulus.metadata["topic"] == "AI Ethics"


class TestCreatePrompt:
    """Tests for create_prompt function."""

    def test_prompt(self):
        """Test creating prompt for specific agent."""
        stimulus = create_prompt(
            content="Please elaborate on your point",
            target_agent="agent1",
        )

        assert stimulus.content == "Please elaborate on your point"
        assert stimulus.stimulus_type == StimulusType.PROMPT
        assert stimulus.target_agents == ["agent1"]
        assert not stimulus.is_broadcast


class TestStimulusInjector:
    """Tests for StimulusInjector class."""

    @pytest.fixture
    def injector(self):
        """Create injector instance."""
        return StimulusInjector()

    def test_initial_state(self, injector):
        """Test initial state."""
        assert len(injector.pending) == 0
        assert len(injector.history) == 0

    def test_queue_stimulus(self, injector):
        """Test queuing stimulus."""
        stimulus = Stimulus(
            content="Test",
            stimulus_type=StimulusType.ANNOUNCEMENT,
        )
        injector.queue(stimulus)

        assert len(injector.pending) == 1
        assert injector.pending[0].content == "Test"

    def test_queue_by_priority(self, injector):
        """Test that stimuli are sorted by priority."""
        low = Stimulus(content="Low", stimulus_type=StimulusType.ANNOUNCEMENT, priority=1)
        high = Stimulus(content="High", stimulus_type=StimulusType.ANNOUNCEMENT, priority=10)
        mid = Stimulus(content="Mid", stimulus_type=StimulusType.ANNOUNCEMENT, priority=5)

        injector.queue(low)
        injector.queue(high)
        injector.queue(mid)

        pending = injector.pending
        assert pending[0].priority == 10
        assert pending[1].priority == 5
        assert pending[2].priority == 1

    def test_queue_question(self, injector):
        """Test queue_question convenience method."""
        stimulus = injector.queue_question("What do you think?")

        assert stimulus.stimulus_type == StimulusType.QUESTION
        assert len(injector.pending) == 1

    def test_queue_announcement(self, injector):
        """Test queue_announcement convenience method."""
        stimulus = injector.queue_announcement("Welcome!")

        assert stimulus.stimulus_type == StimulusType.ANNOUNCEMENT
        assert len(injector.pending) == 1

    def test_pop_next(self, injector):
        """Test popping next stimulus."""
        s1 = Stimulus(content="First", stimulus_type=StimulusType.ANNOUNCEMENT)
        s2 = Stimulus(content="Second", stimulus_type=StimulusType.ANNOUNCEMENT)

        injector.queue(s1)
        injector.queue(s2)

        popped = injector.pop_next()

        assert popped.content == "First"
        assert len(injector.pending) == 1

    def test_pop_next_empty(self, injector):
        """Test popping from empty queue."""
        result = injector.pop_next()
        assert result is None

    def test_peek_next(self, injector):
        """Test peeking at next stimulus."""
        stimulus = Stimulus(content="Test", stimulus_type=StimulusType.ANNOUNCEMENT)
        injector.queue(stimulus)

        peeked = injector.peek_next()

        assert peeked.content == "Test"
        assert len(injector.pending) == 1  # Still there

    def test_peek_next_empty(self, injector):
        """Test peeking at empty queue."""
        result = injector.peek_next()
        assert result is None

    @pytest.mark.asyncio
    async def test_inject(self, injector):
        """Test injecting stimulus."""
        stimulus = Stimulus(content="Test", stimulus_type=StimulusType.ANNOUNCEMENT)

        await injector.inject(stimulus, step=5)

        assert stimulus.injected_at is not None
        assert stimulus.injected_at_step == 5
        assert len(injector.history) == 1

    @pytest.mark.asyncio
    async def test_inject_next(self, injector):
        """Test inject_next convenience method."""
        stimulus = Stimulus(content="Test", stimulus_type=StimulusType.ANNOUNCEMENT)
        injector.queue(stimulus)

        injected = await injector.inject_next(step=3)

        assert injected is not None
        assert injected.injected_at_step == 3
        assert len(injector.pending) == 0
        assert len(injector.history) == 1

    @pytest.mark.asyncio
    async def test_inject_next_empty(self, injector):
        """Test inject_next with empty queue."""
        result = await injector.inject_next(step=1)
        assert result is None

    def test_clear_pending(self, injector):
        """Test clearing pending stimuli."""
        injector.queue(Stimulus(content="1", stimulus_type=StimulusType.ANNOUNCEMENT))
        injector.queue(Stimulus(content="2", stimulus_type=StimulusType.ANNOUNCEMENT))

        cleared = injector.clear_pending()

        assert cleared == 2
        assert len(injector.pending) == 0

    @pytest.mark.asyncio
    async def test_get_history_for_step(self, injector):
        """Test getting history for specific step."""
        s1 = Stimulus(content="Step 1", stimulus_type=StimulusType.ANNOUNCEMENT)
        s2 = Stimulus(content="Step 2", stimulus_type=StimulusType.ANNOUNCEMENT)
        s3 = Stimulus(content="Step 3", stimulus_type=StimulusType.ANNOUNCEMENT)

        await injector.inject(s1, step=1)
        await injector.inject(s2, step=2)
        await injector.inject(s3, step=2)

        step2_history = injector.get_history_for_step(2)

        assert len(step2_history) == 2

    @pytest.mark.asyncio
    async def test_get_history_for_agent(self, injector):
        """Test getting history for specific agent."""
        broadcast = Stimulus(
            content="For all",
            stimulus_type=StimulusType.ANNOUNCEMENT,
        )
        targeted = Stimulus(
            content="For agent1",
            stimulus_type=StimulusType.PROMPT,
            target_agents=["agent1"],
        )
        other = Stimulus(
            content="For agent2",
            stimulus_type=StimulusType.PROMPT,
            target_agents=["agent2"],
        )

        await injector.inject(broadcast, step=1)
        await injector.inject(targeted, step=1)
        await injector.inject(other, step=1)

        agent1_history = injector.get_history_for_agent("agent1")

        # Should include broadcast and targeted
        assert len(agent1_history) == 2

    @pytest.mark.asyncio
    async def test_on_inject_callback(self, injector):
        """Test on_inject callback."""
        injected_stimuli = []

        def callback(stimulus):
            injected_stimuli.append(stimulus)

        injector.on_inject(callback)

        stimulus = Stimulus(content="Test", stimulus_type=StimulusType.ANNOUNCEMENT)
        await injector.inject(stimulus, step=1)

        assert len(injected_stimuli) == 1
        assert injected_stimuli[0].content == "Test"
