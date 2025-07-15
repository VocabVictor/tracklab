import os
from unittest import mock

import pytest
import tracklab


@pytest.fixture
def sample_data():
    artifact = tracklab.Artifact("boom-data", type="dataset")
    artifact.save()
    artifact.wait()
    yield artifact


def test_artifacts_in_config(user, sample_data, test_settings):
    with tracklab.init(settings=test_settings()) as run:
        artifact = run.use_artifact("boom-data:v0")
        logged_artifact = tracklab.Artifact("my-arti", type="dataset")
        run.log_artifact(logged_artifact)
        logged_artifact.wait()
        run.config.dataset = artifact
        run.config.logged_artifact = logged_artifact
        run.config.update({"myarti": artifact})
        with pytest.raises(ValueError) as e_info:
            run.config.nested_dataset = {"nested": artifact}
        assert str(e_info.value) == (
            "Instances of tracklab.Artifact can only be top level keys in a run's config"
        )

        with pytest.raises(ValueError) as e_info:
            run.config.dict_nested = {"one_nest": {"two_nest": artifact}}
        assert str(e_info.value) == (
            "Instances of tracklab.Artifact can only be top level keys in a run's config"
        )

        with pytest.raises(ValueError) as e_info:
            run.config.update({"one_nest": {"two_nest": artifact}})
        assert str(e_info.value) == (
            "Instances of tracklab.Artifact can only be top level keys in a run's config"
        )

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["dataset"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": artifact.id,
        "version": "v0",
        "sequenceName": artifact.source_name.split(":")[0],
        "usedAs": None,
    }

    assert run.config["myarti"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": artifact.id,
        "version": "v0",
        "sequenceName": artifact.source_name.split(":")[0],
        "usedAs": None,
    }

    assert run.config["logged_artifact"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": logged_artifact.id,
        "version": "v0",
        "sequenceName": logged_artifact.name.split(":")[0],
        "usedAs": None,
    }


def test_artifact_string_run_config_init(user, sample_data, test_settings):
    config = {"dataset": f"wandb-artifact://{user}/uncategorized/boom-data:v0"}
    with tracklab.init(settings=test_settings(), config=config) as run:
        dataset = run.config.dataset

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["dataset"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": dataset.id,
        "version": "v0",
        "sequenceName": dataset.source_name.split(":")[0],
        "usedAs": None,
    }


def test_artifact_string_run_config_set_item(user, sample_data, test_settings):
    with tracklab.init(settings=test_settings()) as run:
        run.config.dataset = f"wandb-artifact://{run.settings.base_url}/{user}/uncategorized/boom-data:v0"
        dataset = run.config.dataset

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["dataset"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": dataset.id,
        "version": "v0",
        "sequenceName": dataset.source_name.split(":")[0],
        "usedAs": None,
    }


def test_artifact_string_digest_run_config_update(user, sample_data, test_settings):
    with tracklab.init(settings=test_settings()) as run:
        run.config.update({"dataset": f"wandb-artifact://_id/{sample_data.id}"})
        dataset = run.config.dataset

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["dataset"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": dataset.id,
        "version": "v0",
        "sequenceName": dataset.source_name.split(":")[0],
        "usedAs": None,
    }


def test_artifact_string_digest_run_config_init(user, sample_data, test_settings):
    config = {"dataset": f"wandb-artifact://_id/{sample_data.id}"}
    with tracklab.init(settings=test_settings(), config=config) as run:
        dataset = run.config.dataset

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["dataset"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": dataset.id,
        "version": "v0",
        "sequenceName": dataset.source_name.split(":")[0],
        "usedAs": None,
    }


def test_artifact_string_digest_run_config_set_item(user, sample_data, test_settings):
    with tracklab.init(settings=test_settings()) as run:
        run.config.dataset = (
            f"wandb-artifact://{run.settings.base_url}/_id/{sample_data.id}"
        )
        dataset = run.config.dataset

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["dataset"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": dataset.id,
        "version": "v0",
        "sequenceName": dataset.source_name.split(":")[0],
        "usedAs": None,
    }


def test_artifact_string_run_config_update(user, sample_data, test_settings):
    with tracklab.init(settings=test_settings()) as run:
        run.config.update(
            {"dataset": f"wandb-artifact://{user}/uncategorized/boom-data:v0"}
        )
        dataset = run.config.dataset

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["dataset"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": dataset.id,
        "version": "v0",
        "sequenceName": dataset.source_name.split(":")[0],
        "usedAs": None,
    }


def test_wandb_artifact_config_update(user, test_settings):
    open("file1.txt", "w").write("hello")
    artifact = tracklab.Artifact("test_reference_download", "dataset")
    artifact.add_file("file1.txt")
    artifact.add_reference(
        "https://wandb-artifacts-refs-public-test.s3-us-west-2.amazonaws.com/StarWars3.wav"
    )
    with tracklab.init(settings=test_settings()) as run:
        run.config.update({"test_reference_download": artifact})
        assert run.config.test_reference_download == artifact

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    config_art = {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": artifact.id,
        "version": "v0",
        "sequenceName": artifact.name.split(":")[0],
        "usedAs": None,
    }
    assert run.config["test_reference_download"] == config_art

    with tracklab.init(settings=test_settings()) as run:
        run.config.update({"test_reference_download": config_art})
        assert run.config.test_reference_download.id == artifact.id


def test_wandb_artifact_config_set_item(user, test_settings):
    open("file1.txt", "w").write("hello")
    artifact = tracklab.Artifact("test_reference_download", "dataset")
    artifact.add_file("file1.txt")
    artifact.add_reference(
        "https://wandb-artifacts-refs-public-test.s3-us-west-2.amazonaws.com/StarWars3.wav"
    )
    with tracklab.init(settings=test_settings()) as run:
        run.config.test_reference_download = artifact
        assert run.config.test_reference_download == artifact

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["test_reference_download"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": artifact.id,
        "version": "v0",
        "sequenceName": artifact.name.split(":")[0],
        "usedAs": None,
    }


def test_use_artifact(user, test_settings):
    with tracklab.init(settings=test_settings()) as run:
        artifact = tracklab.Artifact("arti", type="dataset")
        run.use_artifact(artifact)
        artifact.wait()
        assert artifact.digest == "64e7c61456b10382e2f3b571ac24b659"


def test_public_artifact_run_config_init(user, sample_data, test_settings):
    art = tracklab.Api().artifact("boom-data:v0", type="dataset")
    config = {"dataset": art}
    with tracklab.init(settings=test_settings(), config=config) as run:
        assert run.config.dataset == art

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["dataset"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": art.id,
        "version": "v0",
        "sequenceName": art.source_name.split(":")[0],
        "usedAs": None,
    }


def test_public_artifact_run_config_set_item(user, sample_data, test_settings):
    art = tracklab.Api().artifact("boom-data:v0", type="dataset")
    with tracklab.init(settings=test_settings()) as run:
        run.config.dataset = art
        assert run.config.dataset == art

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["dataset"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": art.id,
        "version": "v0",
        "sequenceName": art.source_name.split(":")[0],
        "usedAs": None,
    }


def test_public_artifact_run_config_update(user, sample_data, test_settings):
    art = tracklab.Api().artifact("boom-data:v0", type="dataset")
    config = {"dataset": art}
    with tracklab.init(settings=test_settings()) as run:
        run.config.update(config)
        assert run.config.dataset == art

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["dataset"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": art.id,
        "version": "v0",
        "sequenceName": art.source_name.split(":")[0],
        "usedAs": None,
    }


def test_wandb_artifact_init_config(user, test_settings):
    open("file1.txt", "w").write("hello")
    artifact = tracklab.Artifact("test_reference_download", "dataset")
    artifact.add_file("file1.txt")
    artifact.add_reference(
        "https://wandb-artifacts-refs-public-test.s3-us-west-2.amazonaws.com/StarWars3.wav"
    )
    config = {"test_reference_download": artifact}
    with tracklab.init(settings=test_settings(), config=config) as run:
        assert run.config.test_reference_download == artifact

    run = tracklab.Api().run(f"uncategorized/{run.id}")
    assert run.config["test_reference_download"] == {
        "_type": "artifactVersion",
        "_version": "v0",
        "id": artifact.id,
        "version": "v0",
        "sequenceName": artifact.name.split(":")[0],
        "usedAs": None,
    }


def test_log_code_settings(user):
    with open("test.py", "w") as f:
        f.write('print("test")')
    settings = tracklab.Settings(save_code=True, code_dir=".")
    with tracklab.init(settings=settings) as run:
        pass

    artifact_name = tracklab.util.make_artifact_name_safe(
        f"source-{run.project}-{run._settings.program_relpath}"
    )
    tracklab.Api().artifact(f"{artifact_name}:v0")


@pytest.mark.parametrize("save_code", [True, False])
def test_log_code_env(wandb_backend_spy, save_code):
    # test for WB-7468
    with mock.patch.dict("os.environ", TRACKLAB_SAVE_CODE=str(save_code).lower()):
        with open("test.py", "w") as f:
            f.write('print("test")')

        # simulate user turning on code saving in UI
        gql = wandb_backend_spy.gql
        wandb_backend_spy.stub_gql(
            gql.Matcher(operation="Viewer"),
            gql.once(
                content={
                    "data": {"viewer": {"flags": """{"code_saving_enabled": true}"""}}
                },
                status=200,
            ),
        )
        settings = tracklab.Settings(save_code=None, code_dir=".")
        with tracklab.init(settings=settings) as run:
            assert run._settings.save_code is save_code

        artifact_name = tracklab.util.make_artifact_name_safe(
            f"source-{run.project}-{run._settings.program_relpath}"
        )
        if save_code:
            tracklab.Api().artifact(f"{artifact_name}:v0")
        else:
            with pytest.raises(tracklab.errors.CommError):
                tracklab.Api().artifact(f"{artifact_name}:v0")


@pytest.mark.xfail(reason="Backend race condition")
def test_anonymous_mode_artifact(user, capsys, local_settings):
    copied_env = os.environ.copy()
    copied_env.pop("TRACKLAB_API_KEY")
    copied_env.pop("TRACKLAB_USERNAME")
    copied_env.pop("TRACKLAB_ENTITY")
    with mock.patch.dict("os.environ", copied_env, clear=True):
        run = tracklab.init(anonymous="must")
        run.log_artifact(tracklab.Artifact("my-arti", type="dataset"))
        run.finish()

    _, err = capsys.readouterr()

    assert (
        "Artifacts logged anonymously cannot be claimed and expire after 7 days." in err
    )
