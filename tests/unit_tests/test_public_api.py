import json
import sys
from unittest import mock
from unittest.mock import MagicMock

import pytest
import tracklab
from tracklab import Api
from tracklab.apis import internal
from tracklab.sdk.artifacts.artifact_download_logger import ArtifactDownloadLogger
from tracklab.sdk.internal.thread_local_settings import _thread_local_api_settings

def test_api_auto_login_no_tty():
    with mock.patch.object(sys, "stdin", None):
        with pytest.raises(tracklab.UsageError):
            Api()

def test_thread_local_cookies():
    try:
        _thread_local_api_settings.cookies = {"foo": "bar"}
        api = Api()
        assert api._base_client.transport.cookies == {"foo": "bar"}
    finally:
        _thread_local_api_settings.cookies = None

def test_thread_local_api_key():
    try:
        _thread_local_api_settings.api_key = "XXXX"
        api = Api()
        assert api.api_key == "XXXX"
    finally:
        _thread_local_api_settings.api_key = None

@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_base_url_sanitization():
    with mock.patch.object(wandb, "login", mock.MagicMock()):
        api = Api({"base_url": "https://tracklab.corp.net///"})
        assert api.settings["base_url"] == "https://tracklab.corp.net"

@pytest.mark.parametrize(
    "path",
    [
        "user/proj/run",  # simple
        "/user/proj/run",  # leading slash
        "user/proj:run",  # docker
        "user/proj/runs/run",  # path_url
    ],
)
@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_parse_path(path):
    with mock.patch.object(wandb, "login", mock.MagicMock()):
        user, project, run = Api()._parse_path(path)
        assert user == "user"
        assert project == "proj"
        assert run == "run"

@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_parse_project_path():
    with mock.patch.object(wandb, "login", mock.MagicMock()):
        entity, project = Api()._parse_project_path("user/proj")
        assert entity == "user"
        assert project == "proj"

@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_parse_project_path_proj():
    with mock.patch.dict("os.environ", {"TRACKLAB_ENTITY": "mock_entity"}):
        entity, project = Api()._parse_project_path("proj")
        assert entity == "mock_entity"
        assert project == "proj"

@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_parse_path_docker_proj():
    with mock.patch.dict("os.environ", {"TRACKLAB_ENTITY": "mock_entity"}):
        user, project, run = Api()._parse_path("proj:run")
        assert user == "mock_entity"
        assert project == "proj"
        assert run == "run"

@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_parse_path_user_proj():
    with mock.patch.dict("os.environ", {"TRACKLAB_ENTITY": "mock_entity"}):
        user, project, run = Api()._parse_path("proj/run")
        assert user == "mock_entity"
        assert project == "proj"
        assert run == "run"

@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_parse_path_proj():
    with mock.patch.dict("os.environ", {"TRACKLAB_ENTITY": "mock_entity"}):
        user, project, run = Api()._parse_path("proj")
        assert user == "mock_entity"
        assert project == "proj"
        assert run == "proj"

@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_parse_path_id():
    with mock.patch.dict(
        "os.environ", {"TRACKLAB_ENTITY": "mock_entity", "TRACKLAB_PROJECT": "proj"}
    ):
        user, project, run = Api()._parse_path("run")
        assert user == "mock_entity"
        assert project == "proj"
        assert run == "run"

@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_direct_specification_of_api_key():
    # test_settings has a different API key
    api = Api(api_key="abcd" * 10)
    assert api.api_key == "abcd" * 10

@pytest.mark.parametrize(
    "path",
    [
        "test",
        "test/test",
    ],
)
@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_from_path_project_type(path):
    with mock.patch.object(wandb, "login", mock.MagicMock()):
        project = Api().from_path(path)
        assert isinstance(project, tracklab.apis.public.Project)

@pytest.mark.usefixtures("patch_apikey", "patch_prompt")
def test_report_to_html():
    path = "test/test/reports/My-Report--XYZ"
    report = Api().from_path(path)
    report_html = report.to_html(hidden=True)
    assert "test/test/reports/My-Report--XYZ" in report_html
    assert "<button" in report_html

def test_override_base_url_passed_to_login():
    base_url = "https://tracklab.space"
    with mock.patch.object(wandb, "login", mock.MagicMock()) as mock_login:
        api = tracklab.Api(api_key=None, overrides={"base_url": base_url})
        assert mock_login.call_args[1]["host"] == base_url
        assert api.settings["base_url"] == base_url

# def test_artifact_download_logger(): # Artifact test removed
#     now = 0 # Artifact test removed
#     termlog = mock.Mock() # Artifact test removed
#  # Artifact test removed
#     nfiles = 10 # Artifact test removed
#     logger = ArtifactDownloadLogger( # Artifact test removed
#         nfiles=nfiles, # Artifact test removed
#         clock_for_testing=lambda: now, # Artifact test removed
#         termlog_for_testing=termlog, # Artifact test removed
#     ) # Artifact test removed
#  # Artifact test removed
#     times_calls = [ # Artifact test removed
#         (0, None), # Artifact test removed
#         (0.001, None), # Artifact test removed
#         (1, mock.call("\\ 3 of 10 files downloaded...\r", newline=False)), # Artifact test removed
#         (1.001, None), # Artifact test removed
#         (2, mock.call("| 5 of 10 files downloaded...\r", newline=False)), # Artifact test removed
#         (2.001, None), # Artifact test removed
#         (3, mock.call("/ 7 of 10 files downloaded...\r", newline=False)), # Artifact test removed
#         (4, mock.call("- 8 of 10 files downloaded...\r", newline=False)), # Artifact test removed
#         (5, mock.call("\\ 9 of 10 files downloaded...\r", newline=False)), # Artifact test removed
#         (6, mock.call("  10 of 10 files downloaded.  ", newline=True)), # Artifact test removed
#     ] # Artifact test removed
#     assert len(times_calls) == nfiles # Artifact test removed
#  # Artifact test removed
#     for t, call in times_calls: # Artifact test removed
#         now = t # Artifact test removed
#         termlog.reset_mock() # Artifact test removed
#         logger.notify_downloaded() # Artifact test removed
#         if call: # Artifact test removed
#             termlog.assert_called_once() # Artifact test removed
#             assert termlog.call_args == call # Artifact test removed
#         else: # Artifact test removed
#             termlog.assert_not_called() # Artifact test removed
#  # Artifact test removed
#  # Artifact test removed
def test_create_custom_chart(monkeypatch):
    _api = internal.Api()
    _api.api.gql = MagicMock(return_value={"createCustomChart": {"chart": {"id": "1"}}})
    mock_gql = MagicMock(return_value="test-gql-resp")
    monkeypatch.setattr(tracklab.sdk.internal.internal_api, "gql", mock_gql)

    # Test with uppercase access (as would be passed from public API)
    kwargs = {
        "entity": "test-entity",
        "name": "chart",
        "display_name": "Chart",
        "spec_type": "vega2",
        "access": "PRIVATE",  # Uppercase as converted by public API
        "spec": {},
    }

    resp = _api.create_custom_chart(**kwargs)
    assert resp == {"chart": {"id": "1"}}
    _api.api.gql.assert_called_once_with(
        "test-gql-resp",
        {
            "entity": "test-entity",
            "name": "chart",
            "displayName": "Chart",
            "type": "vega2",
            "access": "PRIVATE",
            "spec": json.dumps({}),
        },
    )
