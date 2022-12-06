#!/bin/bash
#
# Bash script to install the conda environment for the project.
#
# Usage: bash env.sh -p <conda root path> -n <env name>
#           -p: conda root path (required)
#           -n: environment name (required)
#
# Script should follow style guide: https://google.github.io/styleguide/shellguide.html

#############
# Constants #
#############

# Command line options.
readonly GETOPTS_STR="p:n:"

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
  # Process options.
  while getopts "${GETOPTS_STR}" option; do
    case "${option}" in
      p) local conda_root="${OPTARG}";;
      n) local env_name="${OPTARG}";;
    esac
  done

  # Check required arguments are provided.
  if [[ ! ${conda_root} ]]; then
    err_exit "Must specify conda root directory with -p"
  fi
  if [[ ! ${env_name} ]]; then
    err_exit "Must specify environment name with -n"
  fi

  # Check that conda-lock is found.
  local conda_lock_exe_path="${conda_root}/bin/conda-lock"
  if [[ ! -e ${conda_lock_exe_path} ]]; then
    err_exit "conda-lock executable not found: ${conda_lock_exe_path}"
  fi

  # Check that mamba is found.
  local mamba_exe_path="${conda_root}/bin/mamba"
  if [[ ! -e ${mamba_exe_path} ]]; then
    err_exit "mamaba executable not found: ${mamba_exe_path}"
  fi

  # Check if environment already exists.
  local env_path="${conda_root}/envs/${env_name}"
  if [[ -d ${env_path} ]]; then
    print_yellow "Conda environment ${env_name} already exists at ${env_path}"
    echo "No changes made"
    exit 0
  fi

  # Check that lock file exists.
  local lock_file="${REPO_ROOT}/conda-lock.yml"
  if [[ ! -f "${lock_file}" ]]; then
    err_exit "Conda lock file not found: ${lock_file}"
  fi

  # Create environment from lock file using conda-lock.
  echo "Creating ${env_name} conda environment (takes several minutes)..."
  if ! "${conda_lock_exe_path}" install --conda "${mamba_exe_path}" --name "${env_name}" "${lock_file}" ; then
    err_exit "Failed to create ${env_name} conda environment"
  fi
  print_green "Created ${env_name} conda environment"
}

####################
# Top-Level Script #
####################

# Load colors library.
source "${REPO_ROOT}/.setup/lib-colors.sh"

# Run main.
main "$@"
