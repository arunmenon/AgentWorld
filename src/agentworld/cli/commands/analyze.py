"""Analyze command - analyze simulation results and generate insights."""

import json
from pathlib import Path
from typing import Optional
from collections import Counter

import typer
from rich.table import Table
from rich.panel import Panel

from agentworld.cli.output import console, print_error, print_success, print_info
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository


def analyze(
    simulation_id: str = typer.Argument(..., help="Simulation ID to analyze"),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save analysis to file",
    ),
    metrics: bool = typer.Option(
        False,
        "--metrics",
        "-m",
        help="Show detailed metrics",
    ),
    sentiment: bool = typer.Option(
        False,
        "--sentiment",
        "-s",
        help="Analyze message sentiment (requires textblob)",
    ),
    topics: bool = typer.Option(
        False,
        "--topics",
        "-t",
        help="Extract key topics from messages",
    ),
    format: str = typer.Option(
        "rich",
        "--format",
        "-f",
        help="Output format: rich, json",
    ),
) -> None:
    """Analyze simulation results and generate insights.

    Provides statistics, sentiment analysis, and topic extraction.
    """
    init_db()
    repo = Repository()

    # Get simulation
    sim = repo.get_simulation(simulation_id)
    if not sim:
        print_error(f"Simulation not found: {simulation_id}")
        raise typer.Exit(1)

    # Get data
    agents = repo.get_agents_for_simulation(simulation_id)
    messages = repo.get_messages_for_simulation(simulation_id)

    # Basic statistics
    stats = {
        "simulation_id": simulation_id,
        "simulation_name": sim.get("name", ""),
        "status": sim.get("status", ""),
        "total_steps": sim.get("total_steps", 0),
        "current_step": sim.get("current_step", 0),
        "agent_count": len(agents),
        "message_count": len(messages),
        "total_tokens": sim.get("total_tokens", 0),
        "total_cost": sim.get("total_cost", 0.0),
    }

    # Message statistics
    if messages:
        msg_lengths = [len(m.get("content", "")) for m in messages]
        stats["avg_message_length"] = sum(msg_lengths) / len(msg_lengths)
        stats["min_message_length"] = min(msg_lengths)
        stats["max_message_length"] = max(msg_lengths)

        # Messages per agent
        sender_counts = Counter(m.get("sender_id") for m in messages)
        stats["messages_per_agent"] = dict(sender_counts)

        # Messages per step
        step_counts = Counter(m.get("step") for m in messages)
        stats["messages_per_step"] = dict(sorted(step_counts.items()))

    # Detailed metrics
    if metrics:
        stats["metrics"] = _calculate_metrics(agents, messages)

    # Sentiment analysis
    if sentiment:
        stats["sentiment"] = _analyze_sentiment(messages)

    # Topic extraction
    if topics:
        stats["topics"] = _extract_topics(messages)

    # Output
    if format == "json":
        output_str = json.dumps(stats, indent=2, default=str)
        if output:
            output.write_text(output_str)
            print_success(f"Analysis saved to {output}")
        else:
            console.print(output_str)
    else:
        _display_rich_analysis(stats, agents)
        if output:
            # Also save JSON version
            output.write_text(json.dumps(stats, indent=2, default=str))
            print_success(f"Analysis saved to {output}")


def _calculate_metrics(agents: list, messages: list) -> dict:
    """Calculate detailed metrics."""
    metrics = {}

    if messages:
        # Response time simulation (based on step ordering)
        steps = sorted(set(m.get("step", 0) for m in messages))
        metrics["step_distribution"] = {
            "total_steps": len(steps),
            "first_step": min(steps) if steps else 0,
            "last_step": max(steps) if steps else 0,
        }

        # Conversation flow
        flows = []
        prev_sender = None
        for m in sorted(messages, key=lambda x: (x.get("step", 0), x.get("timestamp", ""))):
            sender = m.get("sender_id")
            if prev_sender and prev_sender != sender:
                flows.append(f"{prev_sender[:4]}->{sender[:4]}")
            prev_sender = sender
        flow_counts = Counter(flows)
        metrics["conversation_flows"] = dict(flow_counts.most_common(10))

    # Agent engagement
    if agents:
        metrics["agent_engagement"] = {}
        for agent in agents:
            agent_id = agent.get("id", "")
            agent_msgs = [m for m in messages if m.get("sender_id") == agent_id]
            metrics["agent_engagement"][agent.get("name", agent_id)] = {
                "message_count": len(agent_msgs),
                "avg_length": (
                    sum(len(m.get("content", "")) for m in agent_msgs) / len(agent_msgs)
                    if agent_msgs else 0
                ),
            }

    return metrics


def _analyze_sentiment(messages: list) -> dict:
    """Analyze sentiment of messages."""
    try:
        from textblob import TextBlob
    except ImportError:
        return {"error": "textblob not installed. Run: pip install textblob"}

    sentiments = []
    for msg in messages:
        content = msg.get("content", "")
        if content:
            blob = TextBlob(content)
            sentiments.append({
                "step": msg.get("step"),
                "sender_id": msg.get("sender_id"),
                "polarity": blob.sentiment.polarity,
                "subjectivity": blob.sentiment.subjectivity,
            })

    if sentiments:
        avg_polarity = sum(s["polarity"] for s in sentiments) / len(sentiments)
        avg_subjectivity = sum(s["subjectivity"] for s in sentiments) / len(sentiments)
        return {
            "avg_polarity": avg_polarity,
            "avg_subjectivity": avg_subjectivity,
            "sentiment_trend": sentiments[-5:],  # Last 5 messages
            "overall": "positive" if avg_polarity > 0.1 else "negative" if avg_polarity < -0.1 else "neutral",
        }

    return {"error": "No messages to analyze"}


def _extract_topics(messages: list) -> dict:
    """Extract key topics from messages."""
    # Simple keyword extraction without external dependencies
    all_text = " ".join(m.get("content", "") for m in messages)
    words = all_text.lower().split()

    # Filter common words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "again", "further", "then", "once", "and",
        "but", "or", "nor", "so", "yet", "both", "either", "neither", "not",
        "only", "own", "same", "than", "too", "very", "just", "also", "now",
        "i", "you", "he", "she", "it", "we", "they", "what", "which", "who",
        "this", "that", "these", "those", "am", "your", "my", "our", "their",
    }

    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
    word_counts = Counter(filtered_words)

    return {
        "top_words": dict(word_counts.most_common(20)),
        "unique_words": len(set(filtered_words)),
        "total_words": len(filtered_words),
    }


def _display_rich_analysis(stats: dict, agents: list) -> None:
    """Display analysis in rich format."""
    # Header
    console.print(Panel(
        f"[bold]{stats.get('simulation_name', 'Simulation')}[/bold]\n"
        f"ID: {stats.get('simulation_id')}\n"
        f"Status: {stats.get('status')}",
        title="Simulation Analysis",
    ))

    # Basic stats table
    stats_table = Table(title="Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")

    stats_table.add_row("Steps", f"{stats.get('current_step', 0)}/{stats.get('total_steps', 0)}")
    stats_table.add_row("Agents", str(stats.get('agent_count', 0)))
    stats_table.add_row("Messages", str(stats.get('message_count', 0)))
    stats_table.add_row("Total Tokens", str(stats.get('total_tokens', 0)))
    stats_table.add_row("Total Cost", f"${stats.get('total_cost', 0):.4f}")

    if "avg_message_length" in stats:
        stats_table.add_row("Avg Message Length", f"{stats.get('avg_message_length', 0):.1f} chars")

    console.print(stats_table)

    # Agent table
    if agents:
        agent_table = Table(title="Agent Activity")
        agent_table.add_column("Agent", style="cyan")
        agent_table.add_column("Messages", style="green")

        msgs_per_agent = stats.get("messages_per_agent", {})
        for agent in agents:
            agent_id = agent.get("id", "")
            count = msgs_per_agent.get(agent_id, 0)
            agent_table.add_row(agent.get("name", agent_id), str(count))

        console.print(agent_table)

    # Sentiment if available
    if "sentiment" in stats and "error" not in stats["sentiment"]:
        sent = stats["sentiment"]
        console.print(Panel(
            f"Overall: [bold]{sent.get('overall', 'unknown')}[/bold]\n"
            f"Polarity: {sent.get('avg_polarity', 0):.3f}\n"
            f"Subjectivity: {sent.get('avg_subjectivity', 0):.3f}",
            title="Sentiment Analysis",
        ))

    # Topics if available
    if "topics" in stats:
        topics = stats["topics"]
        top_words = topics.get("top_words", {})
        if top_words:
            words_str = ", ".join(f"{w}({c})" for w, c in list(top_words.items())[:10])
            console.print(Panel(
                f"Top words: {words_str}\n"
                f"Unique words: {topics.get('unique_words', 0)}",
                title="Topic Analysis",
            ))
