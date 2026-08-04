"""Compatibility shim. The installer lives in harness_setup.py.

This repo is a workspace, not a Python package, but a file named setup.py at
the root is a contract with pip: `pip install .` executes it with setuptools
command arguments, which here used to mean an *interactive installer* running
inside a package build. The installer was renamed to end that collision.

This shim keeps the old habit working — `python setup.py` still runs the real
installer — while refusing the packaging invocations pip makes.
"""
import sys

SETUPTOOLS_COMMANDS = {
    "egg_info", "dist_info", "sdist", "bdist_wheel", "bdist", "build",
    "install", "develop", "editable_wheel",
}

if SETUPTOOLS_COMMANDS.intersection(sys.argv[1:]):
    sys.stderr.write(
        "This repository is not a pip-installable package.\n"
        "To set up the Job Search Agent Harness, run:  python harness_setup.py\n"
    )
    sys.exit(1)

from harness_setup import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
