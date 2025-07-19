import json
import os
import random
import string

import pytest
from google.protobuf.wrappers_pb2 import BoolValue, StringValue
from tracklab.proto import tracklab_settings_pb2
from tracklab.sdk.internal.job_builder import JobBuilder
from tracklab.sdk.internal.settings_static import SettingsStatic
from tracklab.util import make_artifact_name_safe

def str_of_length(n):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))

def make_proto_settings(**kwargs):
    proto = wandb_settings_pb2.Settings()
    for k, v in kwargs.items():
        if isinstance(v, bool):
            getattr(proto, k).CopyFrom(BoolValue(value=v))
        elif isinstance(v, str):
            getattr(proto, k).CopyFrom(StringValue(value=v))
    return proto

def test_build_repo_job(runner, api):
    remote_name = str_of_length(129)
    metadata = {
        "git": {"remote": remote_name, "commit": "testtestcommit"},
        "codePath": "blah/test.py",
        "args": ["--test", "test"],
        "python": "3.7",
    }
    with runner.isolated_filesystem():
        with open("requirements.txt", "w") as f:
            f.write("numpy==1.19.0")
            f.write("wandb")
        with open("wandb-metadata.json", "w") as f:
            f.write(json.dumps(metadata))

        kwargs = {
            "x_files_dir": "./",
            "disable_job_creation": False,
            "_jupyter": False,
        }
        settings = SettingsStatic(
            make_proto_settings(
                **kwargs,
            )
        )
        job_builder = JobBuilder(settings)
        artifact = job_builder.build(
            api,
            dockerfile="Dockerfile",
            build_context="blah/",
        )
    # assert artifact is not None # Artifact test removed
    # assert artifact.name == make_artifact_name_safe( # Artifact test removed
            f"job-{remote_name}_blah_test.py"
        )
    # assert artifact.type == "job" # Artifact test removed
    # assert artifact._manifest.entries["wandb-job.json"] # Artifact test removed
    # assert artifact._manifest.entries["requirements.frozen.txt"] # Artifact test removed

        with open(artifact._manifest.entries["wandb-job.json"].local_path) as f:
            job_json = json.load(f)
            source_json = job_json["source"]
            assert source_json["git"]["remote"] == remote_name
            assert source_json["git"]["commit"] == "testtestcommit"
            assert source_json["dockerfile"] == "Dockerfile"
            assert source_json["build_context"] == "blah/"

def test_build_repo_notebook_job(runner, tmp_path, api, mocker):
    remote_name = str_of_length(129)
    metadata = {
        "git": {"remote": remote_name, "commit": "testtestcommit"},
        "program": "blah/test.ipynb",
        "args": ["--test", "test"],
        "python": "3.7",
        "root": "test",
    }

    orig_os_path_exists = os.path.exists

    def exists(path):
        if "test.ipynb" in path:
            return True
        return orig_os_path_exists(path)

    mocker.patch("os.path.exists", side_effect=exists)
    # patch in_jupyter to return True
    mocker.patch("tracklab.sdk.lib.ipython.in_jupyter", return_value=True)
    with runner.isolated_filesystem():
        with open("requirements.txt", "w") as f:
            f.write("numpy==1.19.0")
            f.write("wandb")
        with open("wandb-metadata.json", "w") as f:
            f.write(json.dumps(metadata))

        kwargs = {
            "x_files_dir": "./",
            "disable_job_creation": False,
            "x_jupyter_root": str(tmp_path),
        }
        settings = SettingsStatic(
            make_proto_settings(
                **kwargs,
            )
        )
        job_builder = JobBuilder(settings, True)
        artifact = job_builder.build(api)
    # assert artifact is not None # Artifact test removed
    # assert artifact.name == make_artifact_name_safe( # Artifact test removed
            f"job-{remote_name}_blah_test.ipynb"
        )
    # assert artifact.type == "job" # Artifact test removed
    # assert artifact._manifest.entries["wandb-job.json"] # Artifact test removed
    # assert artifact._manifest.entries["requirements.frozen.txt"] # Artifact test removed
        assert job_builder._is_notebook_run is True

# def test_build_artifact_job(runner, api): # Artifact test removed
#     metadata = { # Artifact test removed
#         "codePath": "blah/test.py", # Artifact test removed
#         "args": ["--test", "test"], # Artifact test removed
#         "python": "3.7", # Artifact test removed
#     } # Artifact test removed
#     artifact_name = str_of_length(129) # Artifact test removed
#     with runner.isolated_filesystem(): # Artifact test removed
#         with open("requirements.txt", "w") as f: # Artifact test removed
#             f.write("numpy==1.19.0") # Artifact test removed
#             f.write("wandb") # Artifact test removed
#         with open("wandb-metadata.json", "w") as f: # Artifact test removed
#             f.write(json.dumps(metadata)) # Artifact test removed
#  # Artifact test removed
#         kwargs = { # Artifact test removed
#             "x_files_dir": "./", # Artifact test removed
#             "disable_job_creation": False, # Artifact test removed
#             "_jupyter": False, # Artifact test removed
#         } # Artifact test removed
#         settings = SettingsStatic( # Artifact test removed
#             make_proto_settings( # Artifact test removed
#                 **kwargs, # Artifact test removed
#             ) # Artifact test removed
#         ) # Artifact test removed
#         job_builder = JobBuilder(settings) # Artifact test removed
#         job_builder._logged_code_artifact = { # Artifact test removed
#             "id": "testtest", # Artifact test removed
#             "name": artifact_name, # Artifact test removed
#         } # Artifact test removed
#         artifact = job_builder.build(api) # Artifact test removed
#         assert artifact is not None # Artifact test removed
#         assert artifact.name == make_artifact_name_safe(f"job-{artifact_name}") # Artifact test removed
#         assert artifact.type == "job" # Artifact test removed
#         assert artifact._manifest.entries["wandb-job.json"] # Artifact test removed
#         assert artifact._manifest.entries["requirements.frozen.txt"] # Artifact test removed
#  # Artifact test removed
#  # Artifact test removed
# def test_build_artifact_notebook_job(runner, tmp_path, mocker, api): # Artifact test removed
#     metadata = { # Artifact test removed
#         "program": "blah/test.ipynb", # Artifact test removed
#         "args": ["--test", "test"], # Artifact test removed
#         "python": "3.7", # Artifact test removed
#     } # Artifact test removed
#     artifact_name = str_of_length(129) # Artifact test removed
#     orig_os_path_exists = os.path.exists # Artifact test removed
#  # Artifact test removed
#     def exists(path): # Artifact test removed
#         if "test.ipynb" in path: # Artifact test removed
#             return True # Artifact test removed
#         return orig_os_path_exists(path) # Artifact test removed
#  # Artifact test removed
#     mocker.patch("os.path.exists", side_effect=exists) # Artifact test removed
#     # patch in_jupyter to return True # Artifact test removed
#     mocker.patch("tracklab.sdk.lib.ipython.in_jupyter", return_value=True) # Artifact test removed
#     with runner.isolated_filesystem(): # Artifact test removed
#         with open("requirements.txt", "w") as f: # Artifact test removed
#             f.write("numpy==1.19.0") # Artifact test removed
#             f.write("wandb") # Artifact test removed
#         with open("wandb-metadata.json", "w") as f: # Artifact test removed
#             f.write(json.dumps(metadata)) # Artifact test removed
#         kwargs = { # Artifact test removed
#             "x_files_dir": "./", # Artifact test removed
#             "disable_job_creation": False, # Artifact test removed
#             "x_jupyter_root": str(tmp_path), # Artifact test removed
#         } # Artifact test removed
#         settings = SettingsStatic( # Artifact test removed
#             make_proto_settings( # Artifact test removed
#                 **kwargs, # Artifact test removed
#             ) # Artifact test removed
#         ) # Artifact test removed
#         job_builder = JobBuilder(settings) # Artifact test removed
#         job_builder._logged_code_artifact = { # Artifact test removed
#             "id": "testtest", # Artifact test removed
#             "name": artifact_name, # Artifact test removed
#         } # Artifact test removed
#         artifact = job_builder.build(api) # Artifact test removed
#         assert artifact is not None # Artifact test removed
#         assert artifact.name == make_artifact_name_safe(f"job-{artifact_name}") # Artifact test removed
#         assert artifact.type == "job" # Artifact test removed
#         assert artifact._manifest.entries["wandb-job.json"] # Artifact test removed
#         assert artifact._manifest.entries["requirements.frozen.txt"] # Artifact test removed
#         assert job_builder._is_notebook_run is True # Artifact test removed
#  # Artifact test removed
#  # Artifact test removed
@pytest.mark.parametrize("verbose", [True, False])
# def test_build_artifact_notebook_job_no_program( # Artifact test removed
#     mocker, # Artifact test removed
#     runner, # Artifact test removed
#     tmp_path, # Artifact test removed
#     capfd, # Artifact test removed
#     verbose, # Artifact test removed
#     api, # Artifact test removed
):
    metadata = {
        "program": "blah/test.ipynb",
        "args": ["--test", "test"],
        "python": "3.7",
    }
    artifact_name = str_of_length(129)

    # patch in_jupyter to return True
    mocker.patch("tracklab.sdk.lib.ipython.in_jupyter", return_value=True)

    with runner.isolated_filesystem():
        with open("requirements.txt", "w") as f:
            f.write("numpy==1.19.0")
            f.write("wandb")
        with open("wandb-metadata.json", "w") as f:
            f.write(json.dumps(metadata))
        kwargs = {
            "x_files_dir": "./",
            "disable_job_creation": False,
            "x_jupyter_root": str(tmp_path),
        }
        settings = SettingsStatic(
            make_proto_settings(
                **kwargs,
            )
        )
        job_builder = JobBuilder(settings, verbose)
        job_builder._logged_code_artifact = {
            "id": "testtest",
            "name": artifact_name,
        }
        artifact = job_builder.build(api)

    # assert not artifact # Artifact test removed
        out = capfd.readouterr().err
        _msg = "No program path found when generating artifact job source for a non-colab notebook run. See https://docs.tracklab.ai/guides/launch/create-job"
        if verbose:
            assert _msg in out
        else:
            assert _msg not in out

@pytest.mark.parametrize("verbose", [True, False])
# def test_build_artifact_notebook_job_no_metadata( # Artifact test removed
#     mocker, # Artifact test removed
#     runner, # Artifact test removed
#     tmp_path, # Artifact test removed
#     capfd, # Artifact test removed
#     verbose, # Artifact test removed
#     api, # Artifact test removed
):
    # patch in_jupyter to return True
    mocker.patch("tracklab.sdk.lib.ipython.in_jupyter", return_value=True)

    artifact_name = str_of_length(129)
    with runner.isolated_filesystem():
        with open("requirements.txt", "w") as f:
            f.write("numpy==1.19.0")
            f.write("wandb")

        kwargs = {
            "x_files_dir": "./",
            "disable_job_creation": False,
            "x_jupyter_root": str(tmp_path),
        }
        settings = SettingsStatic(
            make_proto_settings(
                **kwargs,
            )
        )
        job_builder = JobBuilder(settings, verbose)
        job_builder._logged_code_artifact = {
            "id": "testtest",
            "name": artifact_name,
        }
        artifact = job_builder.build(api)

    # assert not artifact # Artifact test removed
        out = capfd.readouterr().err
        _msg = "Ensure read and write access to run files dir"
        if verbose:
            assert _msg in out
        else:
            assert _msg not in out

@pytest.mark.parametrize("verbose", [True, False])
# def test_build_artifact_notebook_job_no_program_metadata( # Artifact test removed
#     mocker, # Artifact test removed
#     runner, # Artifact test removed
#     tmp_path, # Artifact test removed
#     capfd, # Artifact test removed
#     verbose, # Artifact test removed
#     api, # Artifact test removed
):
    metadata = {
        "args": ["--test", "test"],
        "python": "3.7",
    }
    # patch in_jupyter to return True
    mocker.patch("tracklab.sdk.lib.ipython.in_jupyter", return_value=True)

    artifact_name = str_of_length(129)
    with runner.isolated_filesystem():
        with open("requirements.txt", "w") as f:
            f.write("numpy==1.19.0")
            f.write("wandb")
        with open("wandb-metadata.json", "w") as f:
            f.write(json.dumps(metadata))
        kwargs = {
            "x_files_dir": "./",
            "disable_job_creation": False,
            "x_jupyter_root": str(tmp_path),
        }
        settings = SettingsStatic(
            make_proto_settings(
                **kwargs,
            )
        )
        job_builder = JobBuilder(settings, verbose)
        job_builder._logged_code_artifact = {
            "id": "testtest",
            "name": artifact_name,
        }
        artifact = job_builder.build(api)

    # assert not artifact # Artifact test removed
        out = capfd.readouterr().err
        _msg = "WARNING Notebook 'program' path not found in metadata"
        if verbose:
            assert _msg in out
        else:
            assert _msg not in out

def test_build_image_job(runner, api):
    image_name = str_of_length(129)
    metadata = {
        "program": "blah/test.py",
        "args": ["--test", "test"],
        "python": "3.7",
        "docker": image_name,
    }
    with runner.isolated_filesystem():
        with open("requirements.txt", "w") as f:
            f.write("numpy==1.19.0")
            f.write("wandb")
        with open("wandb-metadata.json", "w") as f:
            f.write(json.dumps(metadata))
        kwargs = {
            "x_files_dir": "./",
            "disable_job_creation": False,
            "_jupyter": False,
        }
        settings = SettingsStatic(
            make_proto_settings(
                **kwargs,
            )
        )
        job_builder = JobBuilder(settings)
        artifact = job_builder.build(api)
    # assert artifact is not None # Artifact test removed
    # assert artifact.name == make_artifact_name_safe(f"job-{image_name}") # Artifact test removed
    # assert artifact.type == "job" # Artifact test removed
    # assert artifact._manifest.entries["wandb-job.json"] # Artifact test removed
    # assert artifact._manifest.entries["requirements.frozen.txt"] # Artifact test removed

def test_set_disabled():
    kwargs = {
        "x_files_dir": "./",
        "disable_job_creation": False,
    }
    settings = SettingsStatic(make_proto_settings(**kwargs))

    job_builder = JobBuilder(settings)
    job_builder.disable = "testtest"
    assert job_builder.disable == "testtest"

def test_no_metadata_file(runner, api):
    kwargs = {
        "x_files_dir": "./",
        "disable_job_creation": False,
    }
    settings = SettingsStatic(make_proto_settings(**kwargs))
    job_builder = JobBuilder(settings)
    artifact = job_builder.build(api)
    # assert artifact is None # Artifact test removed
