import os
from pathlib import Path
import shutil

import nox

try:
    import tomllib
except ModuleNotFoundError or ImportError:
    import tomli as tomllib


def get_python_version():
    """Get the python version from .python-version file unless it is github actions."""
    if "GITHUB_ACTIONS" in os.environ:
        return Path(os.environ["Python_ROOT_DIR"]).parent.name
    return Path(".python-version").read_text().strip()


def get_package_name():
    """Get the package name from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    pyproject_data = tomllib.loads(pyproject_path.read_text())
    return pyproject_data["project"]["name"].replace("-", "_")


PYTHON_VERSION = get_python_version()
PACKAGE_NAME = get_package_name()
PACKAGE_DIR_PATH = Path(PACKAGE_NAME).resolve()

nox.options.reuse_existing_virtualenvs = True
nox.options.default_venv_backend = "uv"


def uv(session, *args):
    """Run uv commands inside a nox session."""
    session.run("uv", *args, "--active", external=True)


@nox.session(python=PYTHON_VERSION)
def install(session):
    """
    Equivalent of:
      make install
    """
    uv(session, "sync", "--group", "dev")


@nox.session(python=PYTHON_VERSION)
def lock(session):
    """
    Equivalent of:
      make lock
    """
    uv(session, "lock", "--upgrade")


@nox.session(python=PYTHON_VERSION)
def lock_check(session):
    """
    Equivalent of:
      make lock-check
    """
    uv(session, "lock", "--check")


#
# Formatting / chores
#


@nox.session(python=PYTHON_VERSION)
def ruff_fixes(session):
    uv(session, "sync", "--group", "dev")
    session.run("ruff", "check", ".", "--fix")


@nox.session(python=PYTHON_VERSION)
def black_fixes(session):
    uv(session, "sync", "--group", "dev")
    session.run("ruff", "format", ".")


@nox.session(python=PYTHON_VERSION)
def tomlsort_fixes(session):
    uv(session, "sync", "--group", "dev")
    session.run(
        "tombi",
        "format",
        # Only format toml files that are not in .venv directories
        *[str(p) for p in Path(".").rglob("*.toml") if ".venv" not in p.parts and ".nox" not in p.parts],
        external=True,
    )


@nox.session(python=PYTHON_VERSION)
def isort_fixes(session):
    uv(session, "sync", "--group", "dev")
    session.run("isort", PACKAGE_NAME, "tests")


@nox.session(python=PYTHON_VERSION)
def chores(session):
    """
    Equivalent of:
      make chores

    This runs all formatting and linting fixes but also mypy checks.
    """
    session.notify("isort_fixes")
    session.notify("ruff_fixes")
    session.notify("black_fixes")
    session.notify("tomlsort_fixes")
    session.notify("mypy_check")
    session.notify("nextflow_check")


@nox.session(python=PYTHON_VERSION)
def github_actions_chores(session):
    """
    Same as chores but with more verbose pytest output for better debugging in CI.

    and no cloud nextflow check as this repo relies on non-downloaded modules.

    """

    session.notify("isort_fixes")
    session.notify("ruff_fixes")
    session.notify("black_fixes")
    session.notify("tomlsort_fixes")
    session.notify("mypy_check")


#
# Checks / linting
#


@nox.session(python=PYTHON_VERSION)
def ruff_check(session):
    uv(session, "sync", "--group", "dev")
    session.run("ruff", "check")


@nox.session(python=PYTHON_VERSION)
def black_check(session):
    uv(session, "sync", "--group", "dev")
    session.run("ruff", "format", ".", "--check")


@nox.session(python=PYTHON_VERSION)
def mypy_check(session):
    uv(session, "sync", "--group", "dev")
    session.run("mypy", PACKAGE_NAME)


@nox.session(python=PYTHON_VERSION)
def tomlsort_check(session):
    uv(session, "sync", "--group", "dev")
    tomls = [str(p) for p in Path(".").rglob("*.toml") if ".venv" not in p.parts and ".nox" not in p.parts]
    session.run("tombi", "lint", *tomls, external=True)
    session.run("tombi", "format", *tomls, "--check", external=True)


@nox.session(python=PYTHON_VERSION)
def isort_check(session):
    uv(session, "sync", "--group", "dev")
    session.run("isort", PACKAGE_NAME, "tests", "--check-only")


@nox.session(python=PYTHON_VERSION)
def nextflow_check(session):
    """
    Lint Nextflow files using built in Nextflow linting.
    """
    session.run(
        "nextflow",
        "lint",
        *[str(p) for p in PACKAGE_DIR_PATH.rglob("*.nf") if "external" not in p.parts]
        + [str(p) for p in PACKAGE_DIR_PATH.rglob("*.config") if "external" not in p.parts],
        "-tabs",
        "-sort-declarations",
        "-harshil-alignment",
        external=True,
    )


#
# Testing
#


@nox.session(python=PYTHON_VERSION)
def tests(session):
    """
    Equivalent of:
      make tests
    """

    session.notify("ruff_check")
    session.notify("black_check")
    session.notify("mypy_check")
    session.notify("tomlsort_check")
    session.notify("isort_check")
    session.notify("nextflow_check")
    session.notify("pytest")


@nox.session(python=PYTHON_VERSION)
def github_actions_tests(session):
    """
    Same as tests but with more verbose pytest output for better debugging in CI.

    and no cloud nextflow check as this repo relies on non-downloaded modules.

    """

    session.notify("ruff_check")
    session.notify("black_check")
    session.notify("mypy_check")
    session.notify("tomlsort_check")
    session.notify("isort_check")
    session.notify("pytest_loud")


@nox.session(python=PYTHON_VERSION)
def precommit(session):
    """
    Equivalent of:
      make precommit
    """

    session.notify("ruff_check")
    session.notify("black_check")
    session.notify("mypy_check")
    session.notify("tomlsort_check")
    session.notify("isort_check")


@nox.session(python=PYTHON_VERSION)
def pytest(session):
    uv(session, "sync", "--group", "dev")
    session.run(
        "pytest",
        f"--cov={PACKAGE_NAME}",
        "--cov-report=term-missing",
        "tests",
    )


@nox.session(python=PYTHON_VERSION)
def pytest_loud(session):
    uv(session, "sync", "--group", "dev")
    session.run(
        "pytest",
        "--log-cli-level=DEBUG",
        "-log_cli=true",
        f"--cov=./{PACKAGE_NAME}",
        "--cov-report=term-missing",
        "tests",
    )


#
# Packaging
#


@nox.session(python=PYTHON_VERSION)
def build_singularity(session):
    """
    Build the Singularity containers for this project.
    """
    uv(session, "sync", "--group", "dev")
    session.install("pip==24.0", "pip-tools==7.5.2")
    session.run("pip", "--version")
    session.run("pip-compile", "--version")

    # existing commands below…
    # use uv to turn pyproject.toml into requirements.txt
    session.run("pip-compile", "--output-file", "requirements.txt", "pyproject.toml")
    args = list(session.posargs)
    if args:
        singularity_images_dir = Path(args[0]).resolve()
    else:
        singularity_images_dir = Path("/mnt/sdd1/luc/singularity_images").resolve()
    print("Singularity_dir:", singularity_images_dir)
    singularity_container_dir = Path("containers").resolve()

    for definition_file in singularity_container_dir.rglob("*.def"):
        print(f"Building Singularity image for {definition_file.name}...")
        try:
            session.run(
                "singularity",
                "build",
                str(singularity_images_dir.joinpath(definition_file.with_suffix(".sif").name)),
                str(definition_file),
                external=True,
            )
        # Offers to rebuild, if user says no, it will skip to the next one instead of erroring out.
        except Exception as e:
            print(f"Error building {definition_file.name}: {e}")
            continue

@nox.session(python=PYTHON_VERSION)
def build(session):
    """
    Equivalent of:
      make build
    """
    uv(session, "sync", "--group", "dev")
    session.run("python", "-m", "build")


#
# Nextflow
#


@nox.session()
def nextflow(session):
    """
    Run Nextflow pipeline with a specified profile (default: local).
    Usage:
      nox -s nextflow -- [profile] [nextflow args...]
      e.g. nox -s nextflow -- slurm --input_dir /path/to/inputs
    """
    args = list(session.posargs)
    profile = "local"
    if args and "--profile" not in args:
        args.extend(["--profile", profile])
    if args and "--input_dir" not in args:
        args.extend(["--input_dir", str(PACKAGE_DIR_PATH.joinpath("..", "inputs", "test"))])

    session.run(
        "nextflow",
        "run",
        PACKAGE_DIR_PATH.joinpath("main.nf"),
        *args,
        external=True,
        env={
            "NXF_LOG_FILE": str(PACKAGE_DIR_PATH.joinpath("work", ".nextflow.log")),
            **os.environ,
        },
    )


@nox.session()
def nextflow_clean(session):
    """
    Clean all Nextflow work directories for this project.
    """

    session.run(
        "nextflow",
        "clean",
        "-f",
        external=True,
    )


@nox.session()
def nextflow_obliterate(session):
    """
    Obliterate all Nextflow work directories for this project.
    WARNING: This will delete all work directories and cannot be undone.
    """
    session.chdir(PACKAGE_DIR_PATH)

    shutil.rmtree(PACKAGE_DIR_PATH.joinpath("work"), ignore_errors=True)
