from textwrap import dedent

import pytest
from tracklab.apis.public.utils import (
    fetch_org_from_settings_or_entity,
    parse_org_from_registry_path,
)
from tracklab.sdk.internal.internal_api import _OrgNames

@pytest.mark.parametrize(
    "path, path_type, expected",
    [
        # Valid cases
        ("my-org/wandb-registry-model", "project", "my-org"),
        ("my-org/wandb-registry-model/model:v1", "artifact", "my-org"),
        # Invalid cases
        ("", "project", ""),  # empty path
        ("wandb-registry-model", "project", ""),  # no org (project)
        ("wandb-registry-model/model:v1", "artifact", ""),  # no org (artifact)
        ("my-org/wandb-registry-model/extra/path", "project", ""),  # too many parts
        ("my-org", "project", ""),  # only org
        # None/empty type
        ("my-org/wandb-registry-model", "", ""),  # empty type
        ("my-org/wandb-registry-model", None, ""),  # None type
    ],
)
def test_parse_org_from_registry_path(path, path_type, expected):
    """Test parse_org_from_registry_path with various input combinations."""
    result = parse_org_from_registry_path(path, path_type)
    assert result == expected

@pytest.fixture
def mock_fetch_orgs_and_org_entities_from_entity(monkeypatch):
    def mock_fetch_orgs(self, entity_name):
        responses = {
            "team-entity": [
                _OrgNames(entity_name="team-entity", display_name="team-org")
            ],
            "default-entity": [
                _OrgNames(entity_name="default-entity", display_name="default-org")
            ],
            "multi-org-user-entity": [
                _OrgNames(entity_name="org1", display_name="Org 1"),
                _OrgNames(entity_name="org2", display_name="Org 2"),
            ],
        }
        return responses.get(entity_name, [])

    monkeypatch.setattr(
        "tracklab.sdk.internal.internal_api.Api._fetch_orgs_and_org_entities_from_entity",
        mock_fetch_orgs,
    )

def test_fetch_org_from_settings_direct(mock_fetch_orgs_and_org_entities_from_entity):
    """Test when organization is directly specified in settings"""
    settings = {"organization": "org-display", "entity": "default-entity"}
    result = fetch_org_from_settings_or_entity(settings)
    assert result == "org-display"

def test_fetch_org_from_entity(mock_fetch_orgs_and_org_entities_from_entity):
    """Test fetching org when only entity is available"""
    settings = {"organization": None, "entity": "team-entity"}
    result = fetch_org_from_settings_or_entity(settings)
    assert result == "team-org"

def test_fetch_org_from_default_entity(mock_fetch_orgs_and_org_entities_from_entity):
    """Test fetching org using default entity when settings entity is None"""
    settings = {"organization": None, "entity": None}
    result = fetch_org_from_settings_or_entity(
        settings, default_entity="default-entity"
    )
    assert result == "default-org"

def test_no_entity_raises_error(mock_fetch_orgs_and_org_entities_from_entity):
    """Test that error is raised when no entity is available"""
    settings = {"organization": None, "entity": None}
    with pytest.raises(ValueError, match="No entity specified"):
        fetch_org_from_settings_or_entity(settings)

def test_no_orgs_found_raises_error(mock_fetch_orgs_and_org_entities_from_entity):
    """Test that error is raised when no orgs are found for entity"""
    settings = {"organization": None, "entity": "unknown-entity"}
    with pytest.raises(ValueError, match="No organizations found for entity"):
        fetch_org_from_settings_or_entity(settings)

def test_multiple_orgs_raises_error(mock_fetch_orgs_and_org_entities_from_entity):
    """Test that error is raised when multiple orgs are found for entity"""
    settings = {"organization": None, "entity": "multi-org-user-entity"}
    with pytest.raises(ValueError, match="Multiple organizations found for entity"):
        fetch_org_from_settings_or_entity(settings)

# GraphQL tests removed since GraphQL functionality was removed