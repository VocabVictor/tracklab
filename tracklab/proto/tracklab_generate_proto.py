#!/usr/bin/env python

import importlib.metadata
import os
import pathlib

import grpc_tools  # type: ignore
from grpc_tools import protoc  # type: ignore
from packaging import version


def get_pip_package_version(package_name: str) -> str:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        raise ValueError(f"Package `{package_name}` not found")

protobuf_version = version.Version(get_pip_package_version("protobuf"))

proto_root = os.path.join(os.path.dirname(grpc_tools.__file__), "_proto")
tmp_out: pathlib.Path = pathlib.Path(f"v{protobuf_version.major}/")

# Stay in current directory
for proto_file in [
    "tracklab_base.proto",
    "tracklab_internal.proto",
    "tracklab_settings.proto",
    "tracklab_telemetry.proto",
    "tracklab_server.proto",
]:
    ret = protoc.main(
        (
            "",
            "-I",
            proto_root,
            "-I",
            ".",
            f"--python_out={tmp_out}",
            f"{proto_file}",
        )
    )
    assert not ret

# clean up tmp dirs if they exist
import shutil
if (tmp_out / "tracklab").exists():
    for p in (tmp_out / "tracklab" / "proto").glob("*pb2*"):
        p.rename(tmp_out / p.name)
    shutil.rmtree(tmp_out / "tracklab")
