"""Tests for Persona Library functionality (Phase 4)."""

import pytest
import uuid
from agentworld.persistence.database import init_db
from agentworld.persistence.repository import Repository


@pytest.fixture
def repo():
    """Create repository with in-memory database."""
    init_db(in_memory=True)
    return Repository()


class TestPersonaMethods:
    """Tests for persona CRUD operations."""

    def test_save_persona(self, repo):
        """Test saving a persona."""
        persona_data = {
            "id": str(uuid.uuid4()),
            "name": "Test Persona",
            "occupation": "Engineer",
            "traits": {"openness": 0.8, "conscientiousness": 0.7},
            "tags": ["tech", "analytical"],
        }
        persona_id = repo.save_persona(persona_data)
        assert persona_id == persona_data["id"]

    def test_get_persona(self, repo):
        """Test retrieving a persona by ID."""
        persona_id = str(uuid.uuid4())
        repo.save_persona({
            "id": persona_id,
            "name": "Get Test",
            "occupation": "Designer",
            "traits": {"openness": 0.9},
        })

        result = repo.get_persona(persona_id)
        assert result is not None
        assert result["name"] == "Get Test"
        assert result["occupation"] == "Designer"

    def test_get_persona_by_name(self, repo):
        """Test retrieving a persona by name."""
        repo.save_persona({
            "id": str(uuid.uuid4()),
            "name": "Unique Name",
            "traits": {},
        })

        result = repo.get_persona_by_name("Unique Name")
        assert result is not None
        assert result["name"] == "Unique Name"

    def test_get_persona_not_found(self, repo):
        """Test getting non-existent persona."""
        result = repo.get_persona("nonexistent")
        assert result is None

    def test_list_personas(self, repo):
        """Test listing personas."""
        repo.save_persona({"id": str(uuid.uuid4()), "name": "Persona 1", "traits": {}})
        repo.save_persona({"id": str(uuid.uuid4()), "name": "Persona 2", "traits": {}})

        results = repo.list_personas()
        assert len(results) >= 2

    def test_list_personas_by_occupation(self, repo):
        """Test filtering personas by occupation."""
        repo.save_persona({
            "id": str(uuid.uuid4()),
            "name": "Engineer 1",
            "occupation": "Engineer",
            "traits": {},
        })
        repo.save_persona({
            "id": str(uuid.uuid4()),
            "name": "Designer 1",
            "occupation": "Designer",
            "traits": {},
        })

        engineers = repo.list_personas(occupation="Engineer")
        assert all(p["occupation"] == "Engineer" for p in engineers)

    def test_delete_persona(self, repo):
        """Test deleting a persona."""
        persona_id = str(uuid.uuid4())
        repo.save_persona({"id": persona_id, "name": "To Delete", "traits": {}})

        deleted = repo.delete_persona(persona_id)
        assert deleted is True

        result = repo.get_persona(persona_id)
        assert result is None

    def test_search_personas(self, repo):
        """Test searching personas."""
        repo.save_persona({
            "id": str(uuid.uuid4()),
            "name": "Alice Engineer",
            "occupation": "Software Engineer",
            "description": "Loves coding",
            "traits": {},
        })

        results = repo.search_personas("Alice")
        assert len(results) >= 1
        assert any("Alice" in p["name"] for p in results)

    def test_increment_persona_usage(self, repo):
        """Test incrementing persona usage count."""
        persona_id = str(uuid.uuid4())
        repo.save_persona({"id": persona_id, "name": "Usage Test", "traits": {}})

        repo.increment_persona_usage(persona_id)
        repo.increment_persona_usage(persona_id)

        result = repo.get_persona(persona_id)
        assert result["usage_count"] == 2


class TestCollectionMethods:
    """Tests for persona collection operations."""

    def test_save_collection(self, repo):
        """Test saving a collection."""
        collection_data = {
            "id": str(uuid.uuid4()),
            "name": "Test Collection",
            "description": "A test collection",
        }
        collection_id = repo.save_collection(collection_data)
        assert collection_id == collection_data["id"]

    def test_get_collection(self, repo):
        """Test retrieving a collection by ID."""
        collection_id = str(uuid.uuid4())
        repo.save_collection({
            "id": collection_id,
            "name": "Get Test Collection",
            "description": "Description",
        })

        result = repo.get_collection(collection_id)
        assert result is not None
        assert result["name"] == "Get Test Collection"

    def test_get_collection_by_name(self, repo):
        """Test retrieving a collection by name."""
        repo.save_collection({
            "id": str(uuid.uuid4()),
            "name": "Named Collection",
        })

        result = repo.get_collection_by_name("Named Collection")
        assert result is not None
        assert result["name"] == "Named Collection"

    def test_list_collections(self, repo):
        """Test listing collections."""
        repo.save_collection({"id": str(uuid.uuid4()), "name": "Collection A"})
        repo.save_collection({"id": str(uuid.uuid4()), "name": "Collection B"})

        results = repo.list_collections()
        assert len(results) >= 2

    def test_delete_collection(self, repo):
        """Test deleting a collection."""
        collection_id = str(uuid.uuid4())
        repo.save_collection({"id": collection_id, "name": "To Delete"})

        deleted = repo.delete_collection(collection_id)
        assert deleted is True

        result = repo.get_collection(collection_id)
        assert result is None


class TestCollectionMembership:
    """Tests for adding/removing personas from collections."""

    def test_add_persona_to_collection(self, repo):
        """Test adding a persona to a collection."""
        # Create persona and collection
        persona_id = str(uuid.uuid4())
        collection_id = str(uuid.uuid4())

        repo.save_persona({"id": persona_id, "name": "Member Persona", "traits": {}})
        repo.save_collection({"id": collection_id, "name": "Member Collection"})

        # Add persona to collection
        member_id = repo.add_persona_to_collection(collection_id, persona_id)
        assert member_id is not None

    def test_get_personas_in_collection(self, repo):
        """Test getting all personas in a collection."""
        # Create personas and collection
        persona1_id = str(uuid.uuid4())
        persona2_id = str(uuid.uuid4())
        collection_id = str(uuid.uuid4())

        repo.save_persona({"id": persona1_id, "name": "Persona One", "traits": {}})
        repo.save_persona({"id": persona2_id, "name": "Persona Two", "traits": {}})
        repo.save_collection({"id": collection_id, "name": "Two Member Collection"})

        repo.add_persona_to_collection(collection_id, persona1_id)
        repo.add_persona_to_collection(collection_id, persona2_id)

        personas = repo.get_personas_in_collection(collection_id)
        assert len(personas) == 2

    def test_remove_persona_from_collection(self, repo):
        """Test removing a persona from a collection."""
        persona_id = str(uuid.uuid4())
        collection_id = str(uuid.uuid4())

        repo.save_persona({"id": persona_id, "name": "Remove Test", "traits": {}})
        repo.save_collection({"id": collection_id, "name": "Remove Collection"})
        repo.add_persona_to_collection(collection_id, persona_id)

        removed = repo.remove_persona_from_collection(collection_id, persona_id)
        assert removed is True

        personas = repo.get_personas_in_collection(collection_id)
        assert len(personas) == 0

    def test_get_collections_for_persona(self, repo):
        """Test getting all collections containing a persona."""
        persona_id = str(uuid.uuid4())
        coll1_id = str(uuid.uuid4())
        coll2_id = str(uuid.uuid4())

        repo.save_persona({"id": persona_id, "name": "Multi Collection Persona", "traits": {}})
        repo.save_collection({"id": coll1_id, "name": "Collection One"})
        repo.save_collection({"id": coll2_id, "name": "Collection Two"})

        repo.add_persona_to_collection(coll1_id, persona_id)
        repo.add_persona_to_collection(coll2_id, persona_id)

        collections = repo.get_collections_for_persona(persona_id)
        assert len(collections) == 2

    def test_duplicate_membership_prevented(self, repo):
        """Test that duplicate memberships return existing ID."""
        persona_id = str(uuid.uuid4())
        collection_id = str(uuid.uuid4())

        repo.save_persona({"id": persona_id, "name": "Dupe Test", "traits": {}})
        repo.save_collection({"id": collection_id, "name": "Dupe Collection"})

        id1 = repo.add_persona_to_collection(collection_id, persona_id)
        id2 = repo.add_persona_to_collection(collection_id, persona_id)

        # Should return same ID, not create duplicate
        assert id1 == id2


class TestPopulationTemplateMethods:
    """Tests for population template operations."""

    def test_save_population_template(self, repo):
        """Test saving a population template."""
        template_data = {
            "id": str(uuid.uuid4()),
            "name": "Test Template",
            "description": "A test template",
            "demographic_config": {
                "age": {"min": 18, "max": 65},
                "occupations": ["engineer", "designer"],
            },
            "trait_distributions": {
                "openness": {"mean": 0.6, "std": 0.2},
            },
            "default_count": 10,
        }
        template_id = repo.save_population_template(template_data)
        assert template_id == template_data["id"]

    def test_get_population_template(self, repo):
        """Test retrieving a population template by ID."""
        template_id = str(uuid.uuid4())
        repo.save_population_template({
            "id": template_id,
            "name": "Get Test Template",
            "demographic_config": {},
            "trait_distributions": {},
        })

        result = repo.get_population_template(template_id)
        assert result is not None
        assert result["name"] == "Get Test Template"

    def test_get_population_template_by_name(self, repo):
        """Test retrieving a template by name."""
        repo.save_population_template({
            "id": str(uuid.uuid4()),
            "name": "Named Template",
            "demographic_config": {},
            "trait_distributions": {},
        })

        result = repo.get_population_template_by_name("Named Template")
        assert result is not None
        assert result["name"] == "Named Template"

    def test_list_population_templates(self, repo):
        """Test listing population templates."""
        repo.save_population_template({
            "id": str(uuid.uuid4()),
            "name": "Template A",
            "demographic_config": {},
            "trait_distributions": {},
        })
        repo.save_population_template({
            "id": str(uuid.uuid4()),
            "name": "Template B",
            "demographic_config": {},
            "trait_distributions": {},
        })

        results = repo.list_population_templates()
        assert len(results) >= 2

    def test_delete_population_template(self, repo):
        """Test deleting a population template."""
        template_id = str(uuid.uuid4())
        repo.save_population_template({
            "id": template_id,
            "name": "To Delete",
            "demographic_config": {},
            "trait_distributions": {},
        })

        deleted = repo.delete_population_template(template_id)
        assert deleted is True

        result = repo.get_population_template(template_id)
        assert result is None

    def test_increment_template_usage(self, repo):
        """Test incrementing template usage count."""
        template_id = str(uuid.uuid4())
        repo.save_population_template({
            "id": template_id,
            "name": "Usage Template",
            "demographic_config": {},
            "trait_distributions": {},
        })

        repo.increment_template_usage(template_id)
        repo.increment_template_usage(template_id)

        result = repo.get_population_template(template_id)
        assert result["usage_count"] == 2
