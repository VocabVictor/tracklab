import re
from enum import Enum
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Union
from urllib.parse import urlparse

from tracklab.sdk.internal.internal_api import gql

from tracklab._iterutils import one
from tracklab.sdk.internal.internal_api import Api as InternalApi


def is_artifact_registry_project(project: str) -> bool:
    """Check if a project name is an artifact registry project.
    
    In TrackLab, registry projects follow a specific naming pattern.
    Since we removed the server dependency, we'll use a simple heuristic.
    """
    # Simple heuristic: registry projects contain "registry" in the name
    return "registry" in project.lower()


def parse_s3_url_to_s3_uri(url) -> str:
    """Convert an S3 HTTP(S) URL to an S3 URI.

    Arguments:
        url (str): The S3 URL to convert, in the format
                   'http(s)://<bucket>.s3.<region>.amazonaws.com/<key>'.
                   or 'http(s)://<bucket>.s3.amazonaws.com/<key>'

    Returns:
        str: The corresponding S3 URI in the format 's3://<bucket>/<key>'.

    Raises:
        ValueError: If the provided URL is not a valid S3 URL.
    """
    # Regular expression to match S3 URL pattern
    s3_pattern = r"^https?://.*s3.*amazonaws\.com.*"
    parsed_url = urlparse(url)

    # Check if it's an S3 URL
    match = re.match(s3_pattern, parsed_url.geturl())
    if not match:
        raise ValueError("Invalid S3 URL")

    # Extract bucket name and key
    bucket_name, *_ = parsed_url.netloc.split(".")
    key = parsed_url.path.lstrip("/")

    # Construct the S3 URI
    s3_uri = f"s3://{bucket_name}/{key}"

    return s3_uri


class PathType(Enum):
    """We have lots of different paths users pass in to fetch artifacts, projects, etc.

    This enum is used for specifying what format the path is in given a string path.
    """

    PROJECT = "PROJECT"
    ARTIFACT = "ARTIFACT"


def parse_org_from_registry_path(path: str, path_type: Union[PathType, str, None]) -> str:
    """Parse the org from a registry path.

    Essentially fetching the "entity" from the path but for Registries the entity is actually the org.

    Args:
        path (str): The path to parse. Can be a project path <entity>/<project> or <project> or an
        artifact path like <entity>/<project>/<artifact> or <project>/<artifact> or <artifact>
        path_type (PathType): The type of path to parse.
    """
    # Handle None or empty path_type
    if not path_type or not path:
        return ""
    
    # Convert string to PathType if needed
    if isinstance(path_type, str):
        path_type = path_type.upper()
        if path_type not in ["PROJECT", "ARTIFACT"]:
            return ""
    else:
        path_type = path_type.value if hasattr(path_type, 'value') else str(path_type)
        
    parts = path.split("/")
    
    # For project paths, we expect exactly 2 parts
    # For artifact paths, we expect exactly 3 parts
    if path_type == "PROJECT":
        if len(parts) != 2:
            return ""
        org, project = parts
        if is_artifact_registry_project(project):
            return org
    elif path_type == "ARTIFACT":
        if len(parts) != 3:
            return ""
        org, project = parts[:2]
        if is_artifact_registry_project(project):
            return org
    
    return ""


def fetch_org_from_settings_or_entity(
    settings: dict, default_entity: Optional[str] = None
) -> str:
    """Fetch the org from either the settings or deriving it from the entity.

    Returns the org from the settings if available. If no org is passed in or set, the entity is used to fetch the org.

    Args:
        organization (str | None): The organization to fetch the org for.
        settings (dict): The settings to fetch the org for.
        default_entity (str | None): The default entity to fetch the org for.
    """
    if (organization := settings.get("organization")) is None:
        # Fetch the org via the Entity. Won't work if default entity is a personal entity and belongs to multiple orgs
        entity = settings.get("entity") or default_entity
        if entity is None:
            raise ValueError(
                "No entity specified and can't fetch organization from the entity"
            )
        entity_orgs = InternalApi()._fetch_orgs_and_org_entities_from_entity(entity)
        entity_org = one(
            entity_orgs,
            too_short=ValueError(
                "No organizations found for entity. Please specify an organization in the settings."
            ),
            too_long=ValueError(
                "Multiple organizations found for entity. Please specify an organization in the settings."
            ),
        )
        organization = entity_org.display_name
    return organization


