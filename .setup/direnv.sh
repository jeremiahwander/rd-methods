#!/bin/bash
#
# Bash script to configure direnv to automatically activate the environment when in the repo.
#
# Usage: bash direnv.sh
#
# Script should follow style guide: https://google.github.io/styleguide/shellguide.html

#############
# Constants #
#############

# Absolute path of the directory containing this file.
FILE_DIR_PATH=$(dirname "$(realpath "$0")")
readonly FILE_DIR_PATH
# Root directory of repository (one level up from here).
REPO_ROOT=$(realpath "${FILE_DIR_PATH}/..")
readonly REPO_ROOT

#################
# Main Function #
#################

main() {
  # Check that direnv is found.
  if ! 2>/dev/null 1>/dev/null direnv version ; then
    err_exit "direnv executable not found on PATH"
  fi

  # Check that shell setup file is found.
  local setup_script="${REPO_ROOT}/setup-shell"
  if [[ ! -f "${setup_script}" ]]; then
    err_exit "setup-shell script not found at ${setup_script}"
  fi

  # Create .envrc file to activate environment.
  local envrc_file="${REPO_ROOT}/.envrc"
  echo "source \"${setup_script}\"" > "${envrc_file}"

  # Tell direnv that the .envrc file is trusted.
  direnv allow "${REPO_ROOT}"

  # Reload the environment using the new .envrc file.
  direnv reload
}

####################
# Top-Level Script #
####################

# Load colors library.
source "${REPO_ROOT}/.setup/lib-colors.sh"

# Run main.
main "$@"
