#!/bin/bash
#
# Bash script to install all prerequisites into the base conda environment.
#
# Usage: bash base.sh -p <conda root path>
#           -p: conda root path (required)
#
# Script should follow style guide: https://google.github.io/styleguide/shellguide.html

#############
# Constants #
#############

# Command line options.
readonly GETOPTS_STR="p:"

# Absolute path of the directory containing this file.
FILE_DIR_PATH=$(dirname "$(realpath "$0")")
readonly FILE_DIR_PATH
# Root directory of repository (one level up from here).
REPO_ROOT=$(realpath "${FILE_DIR_PATH}/..")
readonly REPO_ROOT

# Exact versions of dependencies to install.
readonly DEPENDENCIES_SPEC=( \
  "conda-forge::mamba=0.25.0" \
  "conda-forge::conda-lock=1.1.1" \
  "semantic_version=2.8.5" \
  "colorama=0.4.4" \
)

#################
# Main Function #
#################

main() {
  # Process options.
  while getopts "${GETOPTS_STR}" option; do
    case "${option}" in
      p) local conda_root="${OPTARG}";;
    esac
  done

  # Check that conda root is provided.
  if [[ ! ${conda_root} ]]; then
    err_exit "Must specify conda root directory with -p"
  fi

  # Check that conda is found.
  local conda_exe_path="${conda_root}/bin/conda"
  if [[ ! -e ${conda_exe_path} ]]; then
    err_exit "Conda executable not found: ${conda_exe_path}"
  fi

  # Install dependencies.
  echo "Installing conda dependencies into base environment (takes several seconds)..."
  # shellcheck disable=2046 # word splitting is desired.
  if ! "${conda_exe_path}" install --yes -n base $(joinByStringSep " " "${DEPENDENCIES_SPEC[@]}") ; then
    err_exit "Failed to install conda dependencies into base environment"
  fi
  print_green "Installed conda dependencies into base environment"
}

####################
# Top-Level Script #
####################

# Load colors library.
source "${REPO_ROOT}/.setup/lib-colors.sh"

# Run main.
main "$@"
