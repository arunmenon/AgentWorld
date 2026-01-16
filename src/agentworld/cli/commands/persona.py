"""Persona library commands - manage reusable personas."""

import json
import uuid
from pathlib import Path
from typing import Optional

import typer
from rich.prompt import Prompt, Confirm
from rich.table import Table

from agentworld.cli.output import console, print_error, print_success, print_info
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository


persona_app = typer.Typer(
    name="persona",
    help="Manage the persona library",
    no_args_is_help=True,
)


@persona_app.command(name="create")
def create_persona(
    name: str = typer.Option(
        None,
        "--name",
        "-n",
        help="Persona name",
    ),
    occupation: Optional[str] = typer.Option(
        None,
        "--occupation",
        "-o",
        help="Persona occupation",
    ),
    background: Optional[str] = typer.Option(
        None,
        "--background",
        "-b",
        help="Persona background description",
    ),
    age: Optional[int] = typer.Option(
        None,
        "--age",
        "-a",
        help="Persona age",
    ),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        "-t",
        help="Comma-separated tags",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive creation wizard",
    ),
) -> None:
    """Create a new persona in the library."""
    init_db()
    repo = Repository()

    if interactive:
        persona_data = _interactive_create_persona()
        if not persona_data:
            return
    else:
        if not name:
            name = Prompt.ask("Persona name")

        # Default traits
        traits = {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.3,
        }

        persona_data = {
            "id": str(uuid.uuid4()),
            "name": name,
            "occupation": occupation,
            "background": background or "",
            "age": age,
            "traits": traits,
            "tags": tags.split(",") if tags else [],
        }

    try:
        persona_id = repo.save_persona(persona_data)
        print_success(f"Created persona: {persona_data['name']}")
        print_info(f"ID: {persona_id}")
    except Exception as e:
        print_error(f"Failed to create persona: {e}")
        raise typer.Exit(1)


@persona_app.command(name="list")
def list_personas(
    occupation: Optional[str] = typer.Option(
        None,
        "--occupation",
        "-o",
        help="Filter by occupation",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum number of results",
    ),
) -> None:
    """List personas in the library."""
    init_db()
    repo = Repository()

    personas = repo.list_personas(occupation=occupation, limit=limit)

    if not personas:
        print_info("No personas found in library.")
        console.print("[dim]Create one with: agentworld persona create --interactive[/dim]")
        return

    table = Table(title="Persona Library")
    table.add_column("ID", style="dim", width=12)
    table.add_column("Name", style="bold")
    table.add_column("Occupation")
    table.add_column("Age")
    table.add_column("Tags")
    table.add_column("Uses", justify="right")

    for p in personas:
        tags_str = ", ".join(p.get("tags", [])[:3])
        if len(p.get("tags", [])) > 3:
            tags_str += "..."
        table.add_row(
            p["id"][:12],
            p["name"],
            p.get("occupation") or "-",
            str(p.get("age") or "-"),
            tags_str or "-",
            str(p.get("usage_count", 0)),
        )

    console.print(table)


@persona_app.command(name="show")
def show_persona(
    persona_id: str = typer.Argument(
        ...,
        help="Persona ID or name",
    ),
) -> None:
    """Show details of a persona."""
    init_db()
    repo = Repository()

    # Try by ID first
    persona = repo.get_persona(persona_id)
    if not persona:
        # Try by name
        persona = repo.get_persona_by_name(persona_id)

    if not persona:
        print_error(f"Persona not found: {persona_id}")
        raise typer.Exit(1)

    console.print(f"\n[bold]{persona['name']}[/bold]")
    console.print(f"[dim]ID: {persona['id']}[/dim]\n")

    if persona.get("occupation"):
        console.print(f"[bold]Occupation:[/bold] {persona['occupation']}")
    if persona.get("age"):
        console.print(f"[bold]Age:[/bold] {persona['age']}")
    if persona.get("background"):
        console.print(f"\n[bold]Background:[/bold]\n{persona['background']}")

    # Traits
    traits = persona.get("traits", {})
    if traits:
        console.print("\n[bold]Traits (Big Five):[/bold]")
        for trait, value in traits.items():
            bar = "=" * int(value * 20)
            console.print(f"  {trait:20s} [{bar:20s}] {value:.2f}")

    if persona.get("tags"):
        console.print(f"\n[bold]Tags:[/bold] {', '.join(persona['tags'])}")

    console.print(f"\n[dim]Used {persona.get('usage_count', 0)} times[/dim]")


@persona_app.command(name="delete")
def delete_persona(
    persona_id: str = typer.Argument(
        ...,
        help="Persona ID",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation",
    ),
) -> None:
    """Delete a persona from the library."""
    init_db()
    repo = Repository()

    persona = repo.get_persona(persona_id)
    if not persona:
        print_error(f"Persona not found: {persona_id}")
        raise typer.Exit(1)

    if not force:
        if not Confirm.ask(f"Delete persona '{persona['name']}'?"):
            return

    if repo.delete_persona(persona_id):
        print_success(f"Deleted persona: {persona['name']}")
    else:
        print_error("Failed to delete persona")


@persona_app.command(name="search")
def search_personas(
    query: str = typer.Argument(
        ...,
        help="Search query",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of results",
    ),
) -> None:
    """Search personas by name, description, or occupation."""
    init_db()
    repo = Repository()

    personas = repo.search_personas(query, limit=limit)

    if not personas:
        print_info(f"No personas found matching '{query}'")
        return

    table = Table(title=f"Search Results: '{query}'")
    table.add_column("ID", style="dim", width=12)
    table.add_column("Name", style="bold")
    table.add_column("Occupation")
    table.add_column("Description")

    for p in personas:
        desc = (p.get("description") or "")[:40]
        if len(p.get("description") or "") > 40:
            desc += "..."
        table.add_row(
            p["id"][:12],
            p["name"],
            p.get("occupation") or "-",
            desc or "-",
        )

    console.print(table)


@persona_app.command(name="import")
def import_personas(
    file_path: Path = typer.Argument(
        ...,
        help="JSON file to import",
        exists=True,
    ),
) -> None:
    """Import personas from a JSON file."""
    init_db()
    repo = Repository()

    try:
        content = file_path.read_text()
        data = json.loads(content)
    except Exception as e:
        print_error(f"Failed to read file: {e}")
        raise typer.Exit(1)

    # Handle both single persona and list
    if isinstance(data, dict):
        personas = [data]
    else:
        personas = data

    imported = 0
    for p in personas:
        if "id" not in p:
            p["id"] = str(uuid.uuid4())
        try:
            repo.save_persona(p)
            imported += 1
        except Exception as e:
            print_error(f"Failed to import '{p.get('name', 'unknown')}': {e}")

    print_success(f"Imported {imported} persona(s)")


@persona_app.command(name="export")
def export_personas(
    output: Path = typer.Option(
        Path("personas.json"),
        "--output",
        "-o",
        help="Output file path",
    ),
    persona_id: Optional[str] = typer.Option(
        None,
        "--id",
        help="Export specific persona by ID",
    ),
) -> None:
    """Export personas to a JSON file."""
    init_db()
    repo = Repository()

    if persona_id:
        persona = repo.get_persona(persona_id)
        if not persona:
            print_error(f"Persona not found: {persona_id}")
            raise typer.Exit(1)
        data = persona
    else:
        data = repo.list_personas(limit=1000)

    try:
        output.write_text(json.dumps(data, indent=2))
        print_success(f"Exported to {output}")
    except Exception as e:
        print_error(f"Failed to export: {e}")
        raise typer.Exit(1)


def _interactive_create_persona() -> Optional[dict]:
    """Interactive persona creation wizard."""
    console.print("[bold]Persona Creation Wizard[/bold]\n")

    name = Prompt.ask("Persona name")

    # Check if name exists
    init_db()
    repo = Repository()
    existing = repo.get_persona_by_name(name)
    if existing:
        print_error(f"A persona named '{name}' already exists")
        return None

    occupation = Prompt.ask("Occupation", default="")
    age_str = Prompt.ask("Age (or press Enter to skip)", default="")
    age = int(age_str) if age_str else None

    background = Prompt.ask("Background description", default="")

    console.print("\n[bold]Big Five Personality Traits[/bold]")
    console.print("[dim]Enter values from 0.0 (low) to 1.0 (high)[/dim]\n")

    traits = {}
    trait_descriptions = {
        "openness": "Creativity, curiosity, openness to new experiences",
        "conscientiousness": "Organization, dependability, self-discipline",
        "extraversion": "Sociability, assertiveness, positive emotions",
        "agreeableness": "Cooperation, trust, helpfulness",
        "neuroticism": "Anxiety, emotional instability, moodiness",
    }

    for trait, desc in trait_descriptions.items():
        console.print(f"[dim]{desc}[/dim]")
        value = float(Prompt.ask(f"{trait.capitalize()}", default="0.5"))
        traits[trait] = max(0.0, min(1.0, value))

    tags_str = Prompt.ask("\nTags (comma-separated)", default="")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

    # Preview
    console.print("\n[bold]Preview:[/bold]")
    console.print(f"  Name: {name}")
    console.print(f"  Occupation: {occupation or '-'}")
    console.print(f"  Age: {age or '-'}")
    console.print(f"  Tags: {', '.join(tags) if tags else '-'}")

    if not Confirm.ask("\nCreate this persona?"):
        return None

    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "occupation": occupation or None,
        "age": age,
        "background": background,
        "traits": traits,
        "tags": tags,
    }


# Collection subcommands
collection_app = typer.Typer(
    name="collection",
    help="Manage persona collections",
    no_args_is_help=True,
)


@collection_app.command(name="create")
def create_collection(
    name: str = typer.Argument(..., help="Collection name"),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Collection description",
    ),
) -> None:
    """Create a new persona collection."""
    init_db()
    repo = Repository()

    collection_data = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
    }

    try:
        collection_id = repo.save_collection(collection_data)
        print_success(f"Created collection: {name}")
        print_info(f"ID: {collection_id}")
    except Exception as e:
        print_error(f"Failed to create collection: {e}")
        raise typer.Exit(1)


@collection_app.command(name="list")
def list_collections() -> None:
    """List all persona collections."""
    init_db()
    repo = Repository()

    collections = repo.list_collections()

    if not collections:
        print_info("No collections found.")
        return

    table = Table(title="Persona Collections")
    table.add_column("ID", style="dim", width=12)
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Members", justify="right")

    for c in collections:
        table.add_row(
            c["id"][:12],
            c["name"],
            (c.get("description") or "-")[:40],
            str(c.get("member_count", 0)),
        )

    console.print(table)


@collection_app.command(name="add")
def add_to_collection(
    collection: str = typer.Argument(..., help="Collection ID or name"),
    persona: str = typer.Argument(..., help="Persona ID or name"),
) -> None:
    """Add a persona to a collection."""
    init_db()
    repo = Repository()

    # Resolve collection
    coll = repo.get_collection(collection) or repo.get_collection_by_name(collection)
    if not coll:
        print_error(f"Collection not found: {collection}")
        raise typer.Exit(1)

    # Resolve persona
    pers = repo.get_persona(persona) or repo.get_persona_by_name(persona)
    if not pers:
        print_error(f"Persona not found: {persona}")
        raise typer.Exit(1)

    repo.add_persona_to_collection(coll["id"], pers["id"])
    print_success(f"Added '{pers['name']}' to collection '{coll['name']}'")


@collection_app.command(name="remove")
def remove_from_collection(
    collection: str = typer.Argument(..., help="Collection ID or name"),
    persona: str = typer.Argument(..., help="Persona ID or name"),
) -> None:
    """Remove a persona from a collection."""
    init_db()
    repo = Repository()

    # Resolve collection
    coll = repo.get_collection(collection) or repo.get_collection_by_name(collection)
    if not coll:
        print_error(f"Collection not found: {collection}")
        raise typer.Exit(1)

    # Resolve persona
    pers = repo.get_persona(persona) or repo.get_persona_by_name(persona)
    if not pers:
        print_error(f"Persona not found: {persona}")
        raise typer.Exit(1)

    if repo.remove_persona_from_collection(coll["id"], pers["id"]):
        print_success(f"Removed '{pers['name']}' from collection '{coll['name']}'")
    else:
        print_error("Persona not in collection")


@collection_app.command(name="show")
def show_collection(
    collection: str = typer.Argument(..., help="Collection ID or name"),
) -> None:
    """Show personas in a collection."""
    init_db()
    repo = Repository()

    coll = repo.get_collection(collection) or repo.get_collection_by_name(collection)
    if not coll:
        print_error(f"Collection not found: {collection}")
        raise typer.Exit(1)

    console.print(f"\n[bold]{coll['name']}[/bold]")
    if coll.get("description"):
        console.print(f"[dim]{coll['description']}[/dim]")
    console.print()

    personas = repo.get_personas_in_collection(coll["id"])

    if not personas:
        print_info("No personas in this collection.")
        return

    table = Table()
    table.add_column("ID", style="dim", width=12)
    table.add_column("Name", style="bold")
    table.add_column("Occupation")

    for p in personas:
        table.add_row(
            p["id"][:12],
            p["name"],
            p.get("occupation") or "-",
        )

    console.print(table)


# Add collection subcommands to persona app
persona_app.add_typer(collection_app, name="collection")
