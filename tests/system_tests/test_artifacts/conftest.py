import pytest
import tracklab
from tracklab.sdk.artifacts.artifact import Artifact


@pytest.fixture
def logged_artifact(user, example_files) -> Artifact:
    with tracklab.init(entity=user, project="project") as run:
        artifact = tracklab.Artifact("test-artifact", "dataset")
        artifact.add_dir(example_files)
        run.log_artifact(artifact)
    artifact.wait()
    return tracklab.Api().artifact(f"{user}/project/test-artifact:v0")


@pytest.fixture
def linked_artifact(user, logged_artifact) -> Artifact:
    with tracklab.init(entity=user, project="other-project") as run:
        run.link_artifact(logged_artifact, "linked-from-portfolio")

    return tracklab.Api().artifact(f"{user}/other-project/linked-from-portfolio:v0")
