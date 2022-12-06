#!/bin/bash
#
# Bash script to install AzCopy into the specified directory. This does not ensure that azcopy is on the PATH.
#
# Usage: bash azcopy.sh -p <install path> [-c <cache path>]
#           -p: install path (required)
#           -c: cache path for downloads to be deleted by script, defaults to ".cache" directory within repo root
#
# Supports x86/x64 Linux only.
# For other versions see: https://docs.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10#download-azcopy
#
# Script should follow style guide: https://google.github.io/styleguide/shellguide.html

#############
# Constants #
#############

# Command line options.
readonly GETOPTS_STR="p:c:"

# Absolute path of the directory containing this file.
readonly FILE_DIR_PATH=$(dirname $(realpath $0))
# Root directory of repository (one level up from here).
readonly REPO_ROOT=$(realpath "${FILE_DIR_PATH}/..")

#################
# Main Function #
#################

main() {
  # Process options.
  while getopts "${GETOPTS_STR}" option; do
    case "${option}" in
      p) local install_path="${OPTARG}";;
      c) local cache_path="${OPTARG}";;
    esac
  done

  # Check required arguments are provided and assign defaults.
  if [[ ! ${install_path} ]]; then
    err_exit "Must specify the install directory with -p"
  fi
  local cache_path=${cache_path:-"${REPO_ROOT}/.cache"}

  # Download AzCopy.
  local azcopy_archive="${cache_path}/azcopy.tar"
  makedirs_exit_on_fail "${cache_path}"
  2>/dev/null 1>/dev/null curl -Lo "${azcopy_archive}" "https://aka.ms/downloadazcopy-v10-linux"
  if [[ $? -ne 0 ]]; then
    err_exit "Unable to download azcopy"
  fi

  # Extract azcopy executable into install directory.
  makedirs_exit_on_fail "${install_path}"
  local archive_exe_file=$(tar --list -f "${azcopy_archive}" | grep /azcopy$)
  2>/dev/null 1>/dev/null tar -xf "${azcopy_archive}" --strip-components=1 --directory "${install_path}" "${archive_exe_file}"
  if [[ $? -ne 0 ]]; then
    err_exit "Failed to extract azcopy executable from ${azcopy_archive}"
  fi

  # Make executable for all users.
  local azcopy_exe="${install_path}/azcopy"
  if [[ ! -f "${azcopy_exe}" ]]; then
    err_exit "AzCopy executable not found at ${azcopy_exe}"
  fi
  2>/dev/null 1>/dev/null chmod a+x "${azcopy_exe}"
  if [[ $? -ne 0 ]]; then
    err_exit "Failed to make ${azcopy_exe} executable for all users"
  fi

  print_green "Installed $(${azcopy_exe} --version) to ${azcopy_exe}"

  # Delete cache directory.
  2>/dev/null 1>/dev/null rm -r ${cache_path}
}

####################
# Top-Level Script #
####################

# Load colors library.
source "${REPO_ROOT}/.setup/lib-colors.sh"

# Run main.
main "$@"
