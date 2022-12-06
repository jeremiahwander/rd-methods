#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Checks versions of system dependencies."""

import json
import subprocess  # nosec
import sys
from typing import Any, Optional

from colorama import Fore, Style, init
from semantic_version import Version

# Version requirements.
AZ_CLI_VERSION_MIN = Version("2.30.0")
AZ_CLI_VERSION_MAX = None


class PrintErrorMessage(Exception):  # noqa: D101
    pass


def styled(style: Any, message: str) -> str:
    """Apply specified console `style` to `message` and returned styled string for printing."""
    return str(style) + message + str(Style.RESET_ALL)


def check_version(
    used_version: Version, min_version: Optional[Version] = None, max_version: Optional[Version] = None
) -> bool:
    """Raise PrintErrorMessage exception if `used_version` is not between `min_version` and `max_version`."""
    if min_version and used_version < min_version:
        raise PrintErrorMessage(f"az version is {used_version}, must be >= {min_version}")
    if max_version and used_version > max_version:
        raise PrintErrorMessage(f"az version is {used_version}, must be <= {max_version}")
    return True


def main() -> None:
    """Main script rountine."""
    # Get Azure CLI version.
    try:
        az_version_call = subprocess.run(["az", "version"], capture_output=True, text=True)  # nosec
    except FileNotFoundError:
        raise PrintErrorMessage("'az' command not found")
    if az_version_call.returncode:
        raise PrintErrorMessage(f"'az version' command failed with exit code {az_version_call.returncode}")
    # Check Azure CLI version.
    check_version(Version(json.loads(az_version_call.stdout)["azure-cli"]), AZ_CLI_VERSION_MIN, AZ_CLI_VERSION_MAX)


if __name__ == "__main__":
    init()  # Initialize colorama console styling.
    try:
        main()
    except PrintErrorMessage as err:
        print(styled(Fore.RED, f"ERROR: {str(err)}"), file=sys.stderr)
        print("Exiting", file=sys.stderr)
        sys.exit(1)
