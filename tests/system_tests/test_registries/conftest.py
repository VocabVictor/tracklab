from __future__ import annotations

from typing import TYPE_CHECKING

import tracklab
from pytest import fixture, skip
from tracklab import Api, Artifact
from tracklab.apis.public.registries._utils import fetch_org_entity_from_organization
from tracklab.apis.public.registries.registry import Registry
from tracklab.proto.tracklab_internal_pb2 import ServerFeature
from tracklab.sdk.internal.internal_api import Api as InternalApi
from tracklab.util import random_string

if TYPE_CHECKING:
    from ..backend_fixtures import BackendFixtureFactory, TeamAndOrgNames


@fixture
def team_and_org(
    backend_fixture_factory: BackendFixtureFactory, user: str
) -> TeamAndOrgNames:
    return backend_fixture_factory.make_team(username=user)


@fixture
def team(team_and_org: TeamAndOrgNames) -> str:
    return team_and_org.team


@fixture
def org(team_and_org: TeamAndOrgNames) -> str:
    """Set up backend resources for testing link_artifact within a registry."""
    return team_and_org.org


@fixture
def org_entity(org: str, api: Api) -> str:
    if not InternalApi()._server_supports(ServerFeature.ARTIFACT_REGISTRY_SEARCH):
        skip("Cannot fetch org entity on this server version.")

    return fetch_org_entity_from_organization(api.client, org)


@fixture
def registry(org: str, api: Api, worker_id: str) -> Registry:
    # Full name will be "wandb-registry-model"
    if not InternalApi()._server_supports(
        ServerFeature.INCLUDE_ARTIFACT_TYPES_IN_REGISTRY_CREATION
    ):
        skip("Cannot create a test registry on this server version.")

    return api.create_registry(
        name="model", visibility="organization", organization=org
    )


@fixture
def source_artifact(team: str, worker_id: str) -> Artifact:
    # In order to link to an org registry, the source artifact must be logged
    # within a TEAM entity, NOT the user's personal entity.
    with tracklab.init(entity=team) as run:
        artifact = Artifact(name="test-artifact", type="dataset")
        return run.log_artifact(artifact)


@fixture
def target_collection_name(worker_id: str) -> str:
    """The name of the target collection to link to."""
    return f"collection-{worker_id}-{random_string(8)}"


@fixture
def other_team_and_org(
    backend_fixture_factory: BackendFixtureFactory, user: str
) -> TeamAndOrgNames:
    return backend_fixture_factory.make_team(username=user)


@fixture
def other_team(other_team_and_org: TeamAndOrgNames) -> str:
    return other_team_and_org.team


@fixture
def other_org(other_team_and_org: TeamAndOrgNames) -> str:
    """Set up backend resources for testing link_artifact within a registry."""
    return other_team_and_org.org
