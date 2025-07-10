"""Development automation for TrackLab using nox."""

from __future__ import annotations

import os
import pathlib
import platform
import re
import shutil
import time
from contextlib import contextmanager
from typing import Any, Callable

import nox

nox.options.default_venv_backend = "uv"

_SUPPORTED_PYTHONS = ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]

# Directories for test results and coverage
_NOX_PYTEST_COVERAGE_DIR = pathlib.Path(".nox-tracklab", "pytest-coverage")
_NOX_PYTEST_RESULTS_DIR = pathlib.Path(".nox-tracklab", "pytest-results")


@contextmanager
def report_time(session: nox.Session):
    """Context manager to report execution time."""
    t = time.time()
    yield
    session.log(f"Took {time.time() - t:.2f} seconds.")


def install_timed(session: nox.Session, *args, **kwargs):
    """Install packages with timing."""
    with report_time(session):
        session.install(*args, **kwargs)


def install_tracklab(session: nox.Session):
    """Builds and installs tracklab."""
    if session.venv_backend == "uv":
        install_timed(session, "--reinstall", "--refresh-package", "tracklab", ".")
    else:
        install_timed(session, "--force-reinstall", ".")


def get_session_file_name(session: nox.Session) -> str:
    """Returns the session name transformed to be usable in a file name."""
    return re.sub(r"[\(\)=\"\'\.]", "_", session.name)


def run_pytest(
    session: nox.Session,
    paths: list[str],
    opts: dict[str, str] | None = None,
) -> None:
    """Run pytest with common options."""
    session_file_name = get_session_file_name(session)

    opts = opts or {}
    pytest_opts = []
    pytest_env = {
        "PATH": session.env.get("PATH") or os.environ.get("PATH"),
        "USERNAME": os.environ.get("USERNAME"),
        "USERPROFILE": os.environ.get("USERPROFILE"),
        "HOME": os.environ.get("HOME"),
        "CI": os.environ.get("CI"),
    }

    # Print 20 slowest tests
    pytest_opts.append(f"--durations={opts.get('durations', 20)}")

    # Output test results for tooling
    junitxml = _NOX_PYTEST_RESULTS_DIR / session_file_name / "junit.xml"
    pytest_opts.append(f"--junitxml={junitxml}")
    session.notify("combine_test_results")

    # Per-test timeout
    pytest_opts.append(f"--timeout={opts.get('timeout', 300)}")

    # Run tests in parallel
    pytest_opts.append(f"-n={opts.get('n', 'auto')}")

    # Limit workers to prevent memory issues
    pytest_opts.append("--maxprocesses=8")

    # Enable Python code coverage collection
    pytest_opts.extend(["--cov-report=", "--cov", "--no-cov-on-fail"])

    pytest_env.update(python_coverage_env(session))
    session.notify("coverage")

    session.run(
        "pytest",
        *pytest_opts,
        *paths,
        env=pytest_env,
        include_outer_env=False,
    )


@nox.session(python=_SUPPORTED_PYTHONS)
def unit_tests(session: nox.Session) -> None:
    """Runs Python unit tests."""
    install_tracklab(session)
    install_timed(session, "-r", "requirements_test.txt")

    paths = session.posargs or ["tests/unit_tests"]
    run_pytest(session, paths=paths, opts={"n": "8"})


@nox.session(python=_SUPPORTED_PYTHONS)
def integration_tests(session: nox.Session) -> None:
    """Runs integration tests."""
    install_tracklab(session)
    install_timed(session, "-r", "requirements_test.txt")

    paths = session.posargs or ["tests/integration_tests"]
    run_pytest(session, paths=paths, opts={"n": "4"})


@nox.session(python=_SUPPORTED_PYTHONS)
def functional_tests(session: nox.Session) -> None:
    """Runs functional tests."""
    install_tracklab(session)
    install_timed(session, "-r", "requirements_test.txt")

    paths = session.posargs or ["tests/functional_tests"]
    run_pytest(session, paths=paths, opts={"n": "4"})


@nox.session(python=_SUPPORTED_PYTHONS)
def system_tests(session: nox.Session) -> None:
    """Runs system tests."""
    install_tracklab(session)
    install_timed(session, "-r", "requirements_test.txt")

    paths = session.posargs or ["tests/system_tests"]
    run_pytest(session, paths=paths, opts={"n": "2"})


@nox.session(python=_SUPPORTED_PYTHONS)
def tests(session: nox.Session) -> None:
    """Runs all tests."""
    install_tracklab(session)
    install_timed(session, "-r", "requirements_test.txt")

    paths = session.posargs or ["tests/"]
    run_pytest(session, paths=paths, opts={"n": "8"})


@nox.session(name="lint")
def lint(session: nox.Session) -> None:
    """Lint code using ruff."""
    session.install("ruff")
    session.run("ruff", "check", "tracklab")
    session.run("ruff", "format", "--check", "tracklab")


@nox.session(name="format")
def format_code(session: nox.Session) -> None:
    """Format code using ruff."""
    session.install("ruff")
    session.run("ruff", "format", "tracklab")
    session.run("ruff", "check", "--fix", "tracklab")


@nox.session(name="mypy")
def mypy(session: nox.Session) -> None:
    """Type-check the code with mypy."""
    session.install("mypy", "pydantic")
    session.install(".")
    session.run("mypy", "tracklab")


def python_coverage_env(session: nox.Session) -> dict[str, str]:
    """Returns environment variables configuring Python coverage output."""
    _NOX_PYTEST_COVERAGE_DIR.mkdir(exist_ok=True, parents=True)
    pycovfile = _NOX_PYTEST_COVERAGE_DIR / (
        ".coverage-" + get_session_file_name(session)
    )
    return {"COVERAGE_FILE": str(pycovfile.absolute())}


@nox.session(default=False)
def coverage(session: nox.Session) -> None:
    """Combines coverage outputs from test sessions."""
    install_timed(session, "coverage[toml]")

    py_directories = list(_NOX_PYTEST_COVERAGE_DIR.iterdir())
    if len(py_directories) > 0:
        session.run("coverage", "combine", *py_directories)
        session.run("coverage", "xml")
        session.run("coverage", "report")
    else:
        session.warn("No Python coverage found.")
    shutil.rmtree(_NOX_PYTEST_COVERAGE_DIR, ignore_errors=True)


@nox.session(default=False)
def combine_test_results(session: nox.Session) -> None:
    """Merges Python test results into a test-results/junit.xml file."""
    install_timed(session, "junitparser")

    pathlib.Path("test-results").mkdir(exist_ok=True)
    xml_paths = list(_NOX_PYTEST_RESULTS_DIR.glob("*/junit.xml"))
    if xml_paths:
        session.run(
            "junitparser",
            "merge",
            *xml_paths,
            "test-results/junit.xml",
        )

    shutil.rmtree(_NOX_PYTEST_RESULTS_DIR, ignore_errors=True)


@nox.session(name="build")
def build(session: nox.Session) -> None:
    """Build the package."""
    session.install("build")
    session.run("python", "-m", "build")


@nox.session(name="serve")
def serve(session: nox.Session) -> None:
    """Start the TrackLab development server."""
    install_tracklab(session)
    session.run("python", "-m", "tracklab.backend.server", "--dev")


@nox.session(name="clean")
def clean(session: nox.Session) -> None:
    """Clean build artifacts."""
    directories = [
        ".nox-tracklab",
        "build",
        "dist",
        "*.egg-info",
        "__pycache__",
        ".pytest_cache",
        ".coverage",
        "coverage.xml",
        "test-results",
    ]
    
    for directory in directories:
        session.run("rm", "-rf", directory, external=True)
    
    session.run("find", ".", "-name", "*.pyc", "-delete", external=True)
    session.run("find", ".", "-name", "__pycache__", "-exec", "rm", "-rf", "{}", "+", external=True)