# Bash library containing functions for colored output and error handling.
#
# Library should follow style guide: https://google.github.io/styleguide/shellguide.html

# shellcheck shell=bash

#############
# Constants #
#############
# Note these are not defined as readonly so that the file can be sourced multiple times.
# shellcheck disable=2034 # allow unused variables

# ANSI escape codes for foreground coloring.
ANSI_BLACK="\033[0;30m"
ANSI_RED="\033[0;31m"
ANSI_GREEN="\033[0;32m"
ANSI_YELLOW="\033[0;33m"
ANSI_BLUE="\033[0;34m"
ANSI_MAGENTA="\033[0;35m"
ANSI_CYAN="\033[0;36m"
ANSI_WHITE="\033[0;37m"
ANSI_DEFAULT="\033[0;39m"
ANSI_RESET="\033[0;0m"

####################
# Helper Functions #
####################

# Function: color_print
# First argument is ANSI color escape code.
# Additional arguments represent text to display in color.
color_print() {
    local color_code=$1
    shift 1
    echo -e "${color_code}$*${ANSI_RESET}"
}

print_green() {
    color_print "${ANSI_GREEN}" "$@"
}

print_red() {
    color_print "${ANSI_RED}" "$@"
}

print_yellow() {
    color_print "${ANSI_YELLOW}" "$@"
}

print_error() {
  echo -e "${ANSI_RED}ERROR: $*${ANSI_RESET}" >&2
}

err_exit() {
  print_error "$*"
  echo "Exiting" >&2
  exit 1
}

makedirs_exit_on_fail() {
  if ! 2>/dev/null 1>/dev/null mkdir -p "$@" ; then
    err_exit "Failed to create directories: $*"
  fi
}

# Use first argument as a separator to join all remaining arguments.
# Based on: https://dev.to/meleu/how-to-join-array-elements-in-a-bash-script-303a
joinByStringSep() {
  local sep="$1"
  shift 1
  local first="$1"
  shift 1
  printf "%s" "${first}" "${@/#/${sep}}"
}
