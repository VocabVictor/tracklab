"""Compatibility module for old internal_api imports.

This module provides backward compatibility for code that imports from
tracklab.sdk.internal.internal_api. All functionality has been moved to
the tracklab.sdk.internal.api module with a cleaner, modular design.
"""

from typing import NamedTuple

# Re-export everything from the new API module
from tracklab.sdk.internal.api import Api

# Mock functions that were in the old internal_api
def gql(x):
    """Mock GraphQL query function for local TrackLab."""
    return x

# Legacy types
class _OrgNames(NamedTuple):
    entity_name: str
    display_name: str

def _match_org_with_fetched_org_entities(
    organization: str, orgs: list[_OrgNames]
) -> str:
    """Match the organization provided with the org entity or org name.
    
    Args:
        organization: Organization name to match
        orgs: List of _OrgNames to search through
        
    Returns:
        str: Matched organization entity name
        
    Raises:
        ValueError: If no match is found
    """
    # Check for exact entity name match
    for org in orgs:
        if org.entity_name == organization:
            return org.entity_name
            
    # Check for display name match
    for org in orgs:
        if org.display_name == organization:
            return org.entity_name
            
    # No match found
    raise ValueError(f"Organization '{organization}' not found in available organizations")

# Re-export commonly used items
__all__ = ["Api", "gql", "_OrgNames", "_match_org_with_fetched_org_entities"]