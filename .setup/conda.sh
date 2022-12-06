#!/bin/bash
#
# Bash script to install conda to the specified path unless it's already present.
#
# Usage: bash conda.sh [-p <install path>] [-c <cache path>] [-v <conda version>] [-i <python version>]
#           -p: install path, defaults to ".conda" directory within repo root.
#           -v: conda version (e.g., "4.10.3"), defaults to latest
#           -i: python interpreter version (e.g, "py39"), defaults to latest
#
# Supports x86/x64 Mac OSX and Linux.
#
# Script should follow style guide: https://google.github.io/styleguide/shellguide.html

#############
# Constants #
#############

# Command line options.
readonly GETOPTS_STR="p:v:i:"

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
      p) local install_path="${OPTARG}";;
      v) local conda_version="${OPTARG}";;
      i) local py_version="${OPTARG}";;
    esac
  done

  # Set defaults.
  local install_path=${install_path:-"${REPO_ROOT}/.conda"}
  local conda_version=${conda_version:-"latest"}

  # Check if correct version of conda is already installed.
  local conda_exe_path="${install_path}/bin/conda"
  if [[ -e ${conda_exe_path} && ${conda_version} != "latest" && $(${conda_exe_path} -V) == "conda ${conda_version}" ]]; then
    print_green "conda ${conda_version} already installed"
    exit 0
  fi

  # Error if install directory already exists.
  if [[ -d ${install_path} ]]; then
    err_exit "Install directory already exists: ${install_path}"
  fi

  # Create dirs.
  local cache_path
  cache_path=$(mktemp --directory --tmpdir)
  
  # Determine OS.
  if [[ "${OSTYPE}" == "linux-gnu"* ]]; then # Linux
    local os_name="Linux"
  elif [[ "${OSTYPE}" == "darwin"* ]]; then # Mac OSX
    local os_name="Linux"
  else
    err_exit "Failed to determine OS"
  fi

  # Download a Miniconda installer to cache.
  local conda_download_url="https://repo.anaconda.com/miniconda/Miniconda3-${py_version}${py_version:+_}${conda_version}-${os_name}-x86_64.sh"
  local conda_installer_path="${cache_path}/install_miniconda.sh"
  echo "Downloading Miniconda ${conda_version} for ${os_name}..."
  if ! 2>/dev/null 1>/dev/null curl --max-time 30 -o "${conda_installer_path}" "${conda_download_url}" ; then
    err_exit "Failed to download ${conda_download_url}"
  fi

  # Run Miniconda installer.
  echo "Installing Miniconda to ${install_path} (takes a few seconds)..."
  if ! 2>/dev/null 1>/dev/null bash "${conda_installer_path}" -b -p "${install_path}" ; then
    err_exit "Failed to install Miniconda"
  fi

  # Delete cache directory.
  2>/dev/null 1>/dev/null rm -r "${cache_path}"

  # Report success.
  print_green "Installed $(${conda_exe_path} -V)"
}

####################
# Top-Level Script #
####################

# Load colors library.
source "${REPO_ROOT}/.setup/lib-colors.sh"

# Run main.
main "$@"
