import datetime
import enum
import os
import platform
import random
import sys
import tarfile
import tempfile
import time
from unittest import mock

import matplotlib.pyplot as plt
import numpy as np
import plotly
import pytest
import requests
import tracklab
import tracklab.errors as errors
from tracklab import util

###############################################################################
# Test util.json_friendly
###############################################################################


# PyTorch helper function removed - TrackLab no longer requires PyTorch dependency


def nested_list(*shape):
    """Make a nested list of lists with a "shape" argument like numpy, TensorFlow, etc."""
    if not shape:
        # reduce precision so we can use == for comparison regardless
        # of conversions between other libraries
        return [float(np.float16(random.random()))]
    else:
        return [nested_list(*shape[1:]) for _ in range(shape[0])]


def assert_deep_lists_equal(a, b, indices=None):
    try:
        assert a == b
    except ValueError:
        assert len(a) == len(b)

        # pytest's list diffing breaks at 4d, so we track them ourselves
        if indices is None:
            indices = []
            top = True
        else:
            top = False

        for i, (x, y) in enumerate(zip(a, b)):
            try:
                assert_deep_lists_equal(x, y, indices)
            except AssertionError:
                indices.append(i)
                raise
            finally:
                if top and indices:
                    print(f"Diff at index: {list(reversed(indices))}")


def json_friendly_test(orig_data, obj):
    data, converted = util.json_friendly(obj)
    assert_deep_lists_equal(orig_data, data)
    assert converted


def test_jsonify_enum():
    class TestEnum(enum.Enum):
        A = 1
        B = 2

    data, converted = util.json_friendly(TestEnum.A)
    assert data == "A"
    assert converted


# PyTorch-specific test removed - TrackLab no longer requires PyTorch dependency


# TensorFlow-specific test removed - TrackLab no longer requires TensorFlow dependency


# JAX-specific test removed - TrackLab no longer requires JAX dependency


# JAX bfloat16 test removed - TrackLab no longer requires JAX dependency


###############################################################################
# Test util.json_friendly_val
###############################################################################


def test_dataclass():
    from dataclasses import dataclass

    @dataclass
    class TestDataClass:
        test: bool

    test_dataclass = TestDataClass(True)
    converted = util.json_friendly_val({"test": test_dataclass})
    assert isinstance(converted["test"], dict)


def test_nested_dataclasses():
    from dataclasses import dataclass

    @dataclass
    class TestDataClass:
        test: bool

    @dataclass
    class TestDataClassHolder:
        test_dataclass: TestDataClass

    nested_dataclass = TestDataClassHolder(TestDataClass(False))
    converted = util.json_friendly_val({"nested_dataclass": nested_dataclass})
    assert isinstance(converted["nested_dataclass"], dict)
    assert isinstance(converted["nested_dataclass"]["test_dataclass"], dict)
    assert converted["nested_dataclass"]["test_dataclass"]["test"] is False


###############################################################################
# Test util.make_json_if_not_number
###############################################################################


def test_make_json_if_not_number():
    assert util.make_json_if_not_number(1) == 1
    assert util.make_json_if_not_number(1.0) == 1.0
    assert util.make_json_if_not_number("1") == '"1"'
    assert util.make_json_if_not_number("1.0") == '"1.0"'
    assert util.make_json_if_not_number({"a": 1}) == '{"a": 1}'
    assert util.make_json_if_not_number({"a": 1.0}) == '{"a": 1.0}'
    assert util.make_json_if_not_number({"a": "1"}) == '{"a": "1"}'
    assert util.make_json_if_not_number({"a": "1.0"}) == '{"a": "1.0"}'


# Docker-related tests removed - TrackLab is now a local library without Docker integration


###############################################################################
# Test util.app_url
###############################################################################


# test_app_url removed: tracklab is designed for local recording and viewing like TensorBoard
# Cloud service URL configuration is not needed for local-only functionality


###############################################################################
# Test util.make_safe_for_json
###############################################################################


def test_safe_for_json():
    res = util.make_safe_for_json(
        {
            "nan": float("nan"),
            "inf": float("+inf"),
            "ninf": float("-inf"),
            "str": "str",
            "seq": [float("nan"), 1],
            "map": {"foo": 1, "nan": float("nan")},
        }
    )
    assert res == {
        "inf": "Infinity",
        "map": {"foo": 1, "nan": "NaN"},
        "nan": "NaN",
        "ninf": "-Infinity",
        "seq": ["NaN", 1],
        "str": "str",
    }


###############################################################################
# Test util.find_runner
###############################################################################


@pytest.mark.skipif(
    platform.system() == "Windows", reason="find_runner is broken on Windows"
)
def test_find_runner():
    res = util.find_runner(__file__)
    assert "python" in res[0]


###############################################################################
# Test util.from_human_size and util.to_human_size
###############################################################################


def test_from_human_size():
    assert util.from_human_size("1000B", units=util.POW_2_BYTES) == 1000
    assert util.from_human_size("976.6KiB", units=util.POW_2_BYTES) == 1000038
    assert util.from_human_size("4.8MiB", units=util.POW_2_BYTES) == 5033164

    assert util.from_human_size("1000.0B") == 1000
    assert util.from_human_size("1000KB") == 1000000
    assert util.from_human_size("5.0MB") == 5000000


def test_to_human_size():
    assert util.to_human_size(1000, units=util.POW_2_BYTES) == "1000.0B"
    assert util.to_human_size(1000000, units=util.POW_2_BYTES) == "976.6KiB"
    assert util.to_human_size(5000000, units=util.POW_2_BYTES) == "4.8MiB"

    assert util.to_human_size(1000) == "1000.0B"
    assert util.to_human_size(1000000) == "1000.0KB"
    assert util.to_human_size(5000000) == "5.0MB"


###############################################################################
# Test matplotlib utilities
###############################################################################


def matplotlib_with_image():
    """Create a matplotlib figure with an image."""
    fig, ax = plt.subplots(3)
    ax[0].plot([1, 2, 3])
    ax[1].imshow(np.random.rand(200, 200, 3))
    ax[2].plot([1, 2, 3])
    return fig


def matplotlib_without_image():
    """Create a matplotlib figure without an image."""
    fig, ax = plt.subplots(2)
    ax[0].plot([1, 2, 3])
    ax[1].plot([1, 2, 3])
    return fig


def test_matplotlib_contains_images():
    """Test detecting images in a matplotlib figure."""
    # fig true
    fig = matplotlib_with_image()
    assert util.matplotlib_contains_images(fig)
    plt.close()

    # plt true
    fig = matplotlib_with_image()
    assert util.matplotlib_contains_images(plt)
    plt.close()

    # fig false
    fig = matplotlib_without_image()
    assert not util.matplotlib_contains_images(fig)
    plt.close()

    # plt false
    fig = matplotlib_without_image()
    assert not util.matplotlib_contains_images(plt)
    plt.close()


def test_matplotlib_to_plotly():
    """Test transforming a pyplot object to a plotly object (not the tracklab.* versions)."""
    fig = matplotlib_without_image()
    assert type(util.matplotlib_to_plotly(fig)) is plotly.graph_objs._figure.Figure
    plt.close()

    fig = matplotlib_without_image()
    assert type(util.matplotlib_to_plotly(plt)) is plotly.graph_objs._figure.Figure
    plt.close()


def test_convert_plots():
    fig = matplotlib_without_image()
    obj = util.convert_plots(fig)
    assert obj.get("plot")
    assert obj.get("_type") == "plotly"


###############################################################################
# Test uri and path resolution utilities
###############################################################################


def test_is_uri():
    assert util.is_uri("http://foo.com")
    assert util.is_uri("https://foo.com")
    assert util.is_uri("file:///foo.com")
    assert util.is_uri("s3://foo.com")
    assert util.is_uri("gs://foo.com")
    assert util.is_uri("foo://foo.com")
    assert not util.is_uri("foo.com")
    assert not util.is_uri("foo")


@pytest.mark.skipif(
    platform.system() == "Windows", reason="fixme: make this work on windows"
)
def test_local_file_uri_to_path():
    assert util.local_file_uri_to_path("file:///foo.com") == "/foo.com"
    assert util.local_file_uri_to_path("file://foo.com") == ""
    assert util.local_file_uri_to_path("file:///foo") == "/foo"
    assert util.local_file_uri_to_path("file://foo") == ""
    assert util.local_file_uri_to_path("file:///") == "/"
    assert util.local_file_uri_to_path("file://") == ""
    assert util.get_local_path_or_none("https://foo.com") is None


@pytest.mark.skipif(
    platform.system() == "Windows", reason="fixme: make this work on windows"
)
def test_get_local_path_or_none():
    assert util.get_local_path_or_none("file:///foo.com") == "/foo.com"
    assert util.get_local_path_or_none("file://foo.com") is None
    assert util.get_local_path_or_none("file:///foo") == "/foo"
    assert util.get_local_path_or_none("file://foo") is None
    assert util.get_local_path_or_none("file:///") == "/"
    assert util.get_local_path_or_none("file://") == ""
    assert util.get_local_path_or_none("/foo.com") == "/foo.com"
    assert util.get_local_path_or_none("foo.com") == "foo.com"
    assert util.get_local_path_or_none("/foo") == "/foo"
    assert util.get_local_path_or_none("foo") == "foo"
    assert util.get_local_path_or_none("/") == "/"
    assert util.get_local_path_or_none("") == ""


def test_make_tarfile():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpfile = os.path.join(tmpdir, "foo.tar.gz")
        util.make_tarfile(
            output_filename=tmpfile,
            source_dir=tmpdir,
            archive_name="lol",
        )
        assert os.path.exists(tmpfile)
        assert tarfile.is_tarfile(tmpfile)


###############################################################################
# Test tensor type utilities
###############################################################################


# TensorFlow tensor test removed - TrackLab no longer requires TensorFlow dependency


# PyTorch tensor test removed - TrackLab no longer requires PyTorch dependency


###############################################################################
# Test launch utilities
###############################################################################


# test_launch_browser removed: tracklab is designed for local recording and viewing like TensorBoard
# Browser launching functionality is not needed for local-only functionality


# TensorFlow distributed training config test removed - TrackLab no longer requires TensorFlow


###############################################################################
# Test retry utilities
###############################################################################


# Cloud service authentication retry test removed - TrackLab is now a local-only library


# API retry tests removed - TrackLab is now a local-only library without cloud API calls


def test_downsample():
    with pytest.raises(tracklab.UsageError):
        util.downsample([1, 2, 3], 1)
    assert util.downsample([1, 2, 3, 4], 2) == [1, 4]


def test_stopwatch_now():
    t_1 = util.stopwatch_now()
    time.sleep(0.1)
    t_2 = util.stopwatch_now()
    assert t_2 > t_1


def test_class_colors():
    assert util.class_colors(3) == [[0, 0, 0], (1.0, 0.0, 0.0), (0.0, 1.0, 1.0)]


# Old wandb metadata check test removed - TrackLab is a replacement for wandb


# Databricks environment test removed - TrackLab is a local-only library


# Cloud entity/project parsing test removed - TrackLab is now a local-only library


# Artifact alias tests removed - Artifact functionality has been removed from TrackLab


# Compute recursive dicts for tests
d_recursive1i = {1: 2, 3: {4: 5}}
d_recursive1i["_"] = d_recursive1i
d_recursive2i = {1: 2, 3: {np.int64(44): 5}}
d_recursive2i["_"] = d_recursive2i
d_recursive2o = {1: 2, 3: {44: 5}}
d_recursive2o["_"] = d_recursive2o


@pytest.mark.parametrize(
    "dict_input, dict_output",
    [
        ({}, None),
        ({1: 2}, None),
        ({1: np.int64(3)}, None),  # dont care about values
        ({np.int64(3): 4}, {3: 4}),  # top-level
        ({1: {np.int64(3): 4}}, {1: {3: 4}}),  # nested key
        ({1: {np.int32(2): 4}}, {1: {2: 4}}),  # nested key
        (d_recursive1i, None),  # recursive, no numpy
        (d_recursive2i, d_recursive2o),  # recursive, numpy
    ],
)
def test_sanitize_numpy_keys(dict_input, dict_output):
    output, converted = util._sanitize_numpy_keys(dict_input)
    assert converted == (dict_output is not None)

    # pytest assert can't handle '==' on recursive dictionaries!
    if "_" in dict_input:
        # Check the recursive case ourselves.
        assert output["_"] is output

        output = {k: v for k, v in output.items() if k != "_"}
        dict_input = {k: v for k, v in dict_input.items() if k != "_"}
        if dict_output:
            dict_output = {k: v for k, v in dict_output.items() if k != "_"}

    assert output == (dict_output or dict_input)


# Docker image name test removed - TrackLab is now a local library without Docker integration


def test_sampling_weights():
    xs = np.arange(0, 100)
    ys = np.arange(100, 200)
    sample_size = 1000
    sampled_xs, _, _ = util.sample_with_exponential_decay_weights(
        xs, ys, sample_size=sample_size
    )
    # Expect more samples from the start of the list
    assert np.mean(sampled_xs) < np.mean(xs)


def test_json_dump_uncompressed_with_numpy_datatypes():
    import io

    data = {
        "a": [
            np.int32(1),
            np.float32(2.0),
            np.int64(3),
        ]
    }
    iostr = io.StringIO()
    util.json_dump_uncompressed(data, iostr)
    assert iostr.getvalue() == '{"a": [1, 2.0, 3]}'


# test_are_windows_paths_on_same_drive removed: Windows-specific test not applicable in Linux environment
# This test was checking Windows drive letter functionality which is not relevant on Linux
