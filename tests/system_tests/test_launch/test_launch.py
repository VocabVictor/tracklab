from unittest import mock
from unittest.mock import MagicMock

import pytest
import tracklab
from tracklab.errors import CommError
from tracklab.sdk.internal.internal_api import Api as InternalApi
from tracklab.sdk.launch._launch import _launch
from tracklab.sdk.launch.errors import LaunchError


class MockBuilder:
    def __init__(self, *args, **kwargs):
        pass

    async def verify(self):
        pass

    async def build_image(self, *args, **kwargs):
        pass


@pytest.mark.asyncio
async def test_launch_incorrect_backend(runner, user, monkeypatch):
    proj = "test1"
    entry_point = ["python", "/examples/examples/launch/launch-quickstart/train.py"]
    settings = tracklab.Settings(project=proj)
    api = InternalApi()

    monkeypatch.setattr(
        tracklab.sdk.launch.builder.build,
        "LaunchProject",
        lambda *args, **kwargs: MagicMock(),
    )

    monkeypatch.setattr(
        tracklab.sdk.launch.builder.build,
        "validate_docker_installation",
        lambda: None,
    )

    monkeypatch.setattr(
        "tracklab.docker",
        lambda: None,
    )
    monkeypatch.setattr(
        "tracklab.sdk.launch.loader.environment_from_config",
        lambda *args, **kawrgs: None,
    )
    (
        monkeypatch.setattr(
            "tracklab.sdk.launch.loader.registry_from_config", lambda *args, **kawrgs: None
        ),
    )

    monkeypatch.setattr(
        "tracklab.sdk.launch.loader.builder_from_config",
        lambda *args, **kawrgs: MockBuilder(),
    )
    r = tracklab.init(settings=settings)
    r.finish()
    with pytest.raises(
        LaunchError,
        match="Could not create runner from config. Invalid runner name: testing123",
    ):
        await _launch(
            api,
            docker_image="testimage",
            entity=user,
            project=proj,
            entry_point=entry_point,
            resource="testing123",
        )


def test_launch_multi_run(runner, user):
    with runner.isolated_filesystem(), mock.patch.dict(
        "os.environ", {"TRACKLAB_RUN_ID": "test", "TRACKLAB_LAUNCH": "true"}
    ):
        with tracklab.init() as run1:
            pass

        with tracklab.init() as run2:
            pass

        assert run1.id == "test"
        assert run2.id == "test"


def test_launch_get_project_queue_error(user):
    proj = "projectq32e"
    api = InternalApi()
    with pytest.raises(
        CommError,
        match=f"Error fetching run queues for {user}/{proj} check that you have access to this entity and project",
    ):
        api.get_project_run_queues(user, proj)


def test_launch_wandb_init_launch_envs(
    wandb_backend_spy,
    runner,
    user,
):
    queue = "test-queue-name"
    with runner.isolated_filesystem(), mock.patch.dict(
        "os.environ",
        {
            "TRACKLAB_LAUNCH_QUEUE_NAME": queue,
            "TRACKLAB_LAUNCH_QUEUE_ENTITY": user,
            "TRACKLAB_LAUNCH_TRACE_ID": "test123",
        },
    ):
        with tracklab.init() as run:
            run.log({"test": 1})

        with wandb_backend_spy.freeze() as snapshot:
            config = snapshot.config(run_id=run.id)

            assert config["_wandb"]["value"]["launch_trace_id"] == "test123"
            assert config["_wandb"]["value"]["launch_queue_entity"] == user
            assert config["_wandb"]["value"]["launch_queue_name"] == queue
