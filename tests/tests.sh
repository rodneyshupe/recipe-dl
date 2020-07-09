#!/usr/bin/env bash
trap 'rc=$?; echo "ERR at line ${LINENO} (rc: $rc)"; exit $rc' ERR
#trap 'rc=$?; echo "EXIT (rc: $rc)"; exit $rc' EXIT
set -u

### Script Constant
declare -r SCRIPT_NAME=$0

### Exit Constants
declare -r -i EX_OK=0            # successful termination
declare -r -i EX_USAGE=64        # command line usage error
declare -r -i EX_NOINPUT=66      # cannot open input
declare -r -i EX_OSFILE=72       # critical OS file missing
declare -r -i EX_IOERR=74        # input/output error

### Forground Color Constants
declare -A -x COLORS=(
  ['normal']="$(tput sgr0)"
  ['red']="$(tput setaf 1)"
  ['green']="$(tput setaf 2)"
  ['yellow']="$(tput setaf 3)"
  ['blue']="$(tput setaf 4)"
  ['magenta']="$(tput setaf 5)"
  ['cyan']="$(tput setaf 6)"
  ['white']="$(tput setaf 7)"
  ['bold']="$(tput bold)"
)
COLORS+=( ['debug']="${COLORS['blue']}${COLORS['bold']}")
COLORS+=( ['warning']="${COLORS['yellow']}")
COLORS+=( ['error']="${COLORS['red']}" )

COLORS+=( ['highlight']="${COLORS['cyan']}" )

COLORS+=( ['pass']="${COLORS['green']}${COLORS['bold']}")
COLORS+=( ['fail']="${COLORS['red']}${COLORS['bold']}")
COLORS+=( ['missing']="${COLORS['yellow']}${COLORS['bold']}")

### Flags
declare -i FLAG_DEBUG=0
declare -i FLAG_APPEND_LOG=0
declare -i FLAG_SILENT=0
declare -i FLAG_LOADTESTS=0
declare -i FLAG_APPENDTESTS=0

### Global Variables
declare -a TESTS=()
declare FAILURE_LOG_FILE=""

declare SCRIPT_PATH=$(dirname $(readlink $0) 2>/dev/null || dirname $0)           # relative
SCRIPT_PATH="`( cd \"${SCRIPT_PATH}\" && pwd )`"  # absolutized and normalized
if [ -z "${SCRIPT_PATH}" ] ; then
  echo_error "For some reason, the path is not accessible to the script (e.g. permissions re-evaled after suid)"
  exit ${EX_IOERR}  # fail
fi

declare -r PROJECT_PATH="`( cd \"${SCRIPT_PATH}/..\" && pwd )`"  # absolutized and normalized
if [ -z "${PROJECT_PATH}" ] ; then
  echo_error "For some reason, the path is not accessible to the script (e.g. permissions re-evaled after suid)"
  exit ${EX_IOERR}  # fail
fi

declare -r REFERENCE_FILE_PATH="${SCRIPT_PATH}/reference-files"
declare -r DEFAULT_TESTS_FILE="$SCRIPT_PATH/recipe-dl.tests"
declare -r DEFAULT_FAILURE_LOG_FILE="${SCRIPT_PATH}/test.failures.log"

declare -i COUNT_PASS=0
declare -i COUNT_FAIL=0
declare -i COUNT_SKIP=0

function usage {
  echo "Usage: ${SCRIPT_NAME} [-d] [-h] [-r] [-t <URL> <ReferenceFile>] [-t <URL> <ReferenceFile>] ..."
  if [ $# -eq 0 ] || [ -z "$1" ]; then
    echo "  -d|--debug                      Add additional Output"
    echo "  -h|--help                       Display help"
    echo "  -l|--log-file <FILE>            Specifiy Log File (Default: $DEFAULT_FAILURE_LOG_FILE) "
    echo "  -a|--append-log                 Append to existing log."
    echo "  -r|--reset-references           Instead of tests resets the reference files"
    echo "  -t|--test <URL> <ReferenceFile> URL to test. Overrides default tests."
    echo "     --load-tests <FILE>          load tests from file"
    echo "     --append-tests               Append manual tests to test file."
  fi
}

function parse_arguments () {
  TESTS=()
  FAILURE_LOG_FILE=""
  while (( "$#" )); do
    case "$1" in
      -d|--debug)
        FLAG_DEBUG=1
        shift
        ;;
      -h|--help)
        echo_info "$(usage)"
        exit 0
        ;;
      -r|--reset-references)
        reset_references
        shift
        exit 0
        ;;
      -l|--log-file)
        shift
        FAILURE_LOG_FILE="$1"
        shift
        ;;
      -a|--append-log)
        FLAG_APPEND_LOG=1
        shift
        ;;
      -t|--test)
        shift
        TESTS+=("$1|$2")
        shift
        shift
        ;;
      --load-tests)
        shift
        FLAG_LOADTESTS=1
        TESTS_FILE="${1}"
        load_tests "${TESTS_FILE}"
        shift
        ;;
      --append-tests)
        shift
        FLAG_APPENDTESTS=1
        ;;
      -*|--*=) # unsupported flags
        echo_error "ERROR: Unsupported flag $1"
        echo_error "$(usage)"
        exit ${EX_USAGE}
        ;;
      *) # preserve positional arguments
        echo_error "ERROR: Unsupported argument $1"
        echo_error "$(usage)"
        exit ${EX_USAGE}
        ;;
    esac
  done
  if [[ "${FAILURE_LOG_FILE}" == "" ]]; then
    FAILURE_LOG_FILE="${DEFAULT_FAILURE_LOG_FILE}"
  fi
  if [ ${#TESTS[@]} -eq 0 ]; then
    TESTS_FILE="${DEFAULT_TESTS_FILE}"
    load_tests "${TESTS_FILE}"
  fi
}

function command_exists() {
  command -v "$@" > /dev/null 2>&1
}

function echo_info() {
  echo "$@" >$(tty)
}

function echo_debug() {
  if [[ $FLAG_DEBUG -ne 0 ]]; then
    local _BREADCRUMB=$(basename ${SCRIPT_NAME})
    for (( idx=${#FUNCNAME[@]}-2 ; idx>=1 ; idx-- )) ; do
      _BREADCRUMB="${_BREADCRUMB}:${FUNCNAME[idx]}"
    done
    echo_info "[${COLORS['debug']} DEBUG: ${_BREADCRUMB} ${COLORS['normal']}] $@"
  fi
}

function echo_warning() {
  if [[ $FLAG_SILENT -eq 0 ]]; then
    local _BREADCRUMB=""
    if [[ $FLAG_DEBUG -ne 0 ]]; then
      _BREADCRUMB=$(basename ${SCRIPT_NAME})
      for (( idx=${#FUNCNAME[@]}-1 ; idx>=1 ; idx-- )) ; do
        _BREADCRUMB="${_BREADCRUMB}:${FUNCNAME[idx]}"
      done
      _BREADCRUMB=": ${_BREADCRUMB}"
    fi
    echo_info "[${COLORS['warning']} WARNING${_BREADCRUMB} ${COLORS['normal']}] $@"
  fi
}

function echo_error() {
  local _BREADCRUMB=""
  if [[ $FLAG_DEBUG -ne 0 ]]; then
    _BREADCRUMB=$(basename ${SCRIPT_NAME})
    for (( idx=${#FUNCNAME[@]}-1 ; idx>=1 ; idx-- )) ; do
      _BREADCRUMB="${_BREADCRUMB}:${FUNCNAME[idx]}"
    done
    _BREADCRUMB=": ${_BREADCRUMB}"
  fi
  echo_info "[${COLORS['error']} ERROR${_BREADCRUMB} ${COLORS['normal']}] $@" >&2
}

function check_requirements() {
  local MISSING=""

  command_exists cmp || MISSING="${MISSING}$(echo '  cmp')"
  command_exists diff || MISSING="${MISSING}$(echo '  diff')"

  if [[ -n "${MISSING}" ]]; then
    echo_error "Script requires the following commands which are not installed."
    echo_error "${MISSING}"
    echo_error "Aborting."

    exit ${EX_OSFILE}
  fi
}

function option_from_file() {
  local _REFERENCE_FILE="${1}"

  echo_debug "Param: _REFERENCE_FILE=$_REFERENCE_FILE"
  local FILENAME=$(basename -- "$_REFERENCE_FILE")
  local EXTENTION="${FILENAME##*.}"
  #echo_debug "FILENAME=${FILENAME}"
  echo_debug "EXTENTION=${EXTENTION}"

  case "${EXTENTION}" in
    rst)
      OPTION="-r"
      ;;
    md)
      OPTION="-m"
      ;;
    json)
      OPTION="-j"
      ;;
  esac
  echo_debug "OPTION=${OPTION}"
  echo ${OPTION}
}

function load_tests() {
  local _TESTS_FILE=${1:-}

  if [ -s "${_TESTS_FILE}" ]; then
    echo_info "Loading tests from file: ${_TESTS_FILE}"
    TESTS=()
    IFS=
    while read -r TEST_LINE; do
      TEST_LINE="$(echo "${TEST_LINE}" | sed 's/\#.*$//g' | sed 's/^[[:space:]]*//g' | sed 's/[[:space:]]*$//g')"
      if [[ "${TEST_LINE}" != "" ]] ; then
        #echo_debug "Adding Test: \"${TEST_LINE}\"" # Not sure why this is not working but is being added to the file 'not a tty'
        TESTS+=("${TEST_LINE}")
      fi
    done < "${_TESTS_FILE}"
    unset IFS
    echo_debug "Loaded ${#TESTS[@]} tests."
  else
    echo_error "Tests File (${_TESTS_FILE}) is missing."
    exit ${EX_NOINPUT}
  fi
  unset _TESTS_FILE
}

function append_tests() {
  if [ $FLAG_APPENDTESTS -ne 0 ] && [ ${#TESTS[@]} -gt 0 ]; then
    if [ $FLAG_LOADTESTS -ne 0 ]; then
      rm "${TESTS_FILE}" >/dev/null 2>&1
    fi
    for TEST in "${TESTS[@]}"; do
      echo "${TEST}" >> "${TESTS_FILE}"
    done
  fi
}

function log_failure() {
  local _OPTIONS="${1:-}"
  local _URL="${2}"
  local _REFERENCE_FILE="${3}"
  local _TMP_OUTPUT_FILE="${4}"

  local PRINT_WIDTH=80
  echo "$(head -c $[PRINT_WIDTH] < /dev/zero | tr '\0' '=')" >> "${FAILURE_LOG_FILE}"
  echo "Reference File: \"${REFERENCE_FILE_PATH}/${_REFERENCE_FILE}\"" >> "${FAILURE_LOG_FILE}"
  echo "URL:            \"${_URL}\"" >> "${FAILURE_LOG_FILE}"
  if [ $FLAG_DEBUG -ne 0 ]; then
    echo "Option used:    \"${_OPTIONS}\"" >> "${FAILURE_LOG_FILE}"
    echo "Temp Compare File: ${_TMP_OUTPUT_FILE}" >> "${FAILURE_LOG_FILE}"
  fi
  echo "" >> "${FAILURE_LOG_FILE}"
  echo "Differences detailed below" >> "${FAILURE_LOG_FILE}"
  echo "$(head -c $[PRINT_WIDTH] < /dev/zero | tr '\0' '=')" >> "${FAILURE_LOG_FILE}"
  echo "" >> "${FAILURE_LOG_FILE}"
  diff --ignore-trailing-space --ignore-blank-lines "${REFERENCE_FILE_PATH}/${_REFERENCE_FILE}" "${_TMP_OUTPUT_FILE}" >> "${FAILURE_LOG_FILE}" 2>&1
  echo "" >> "${FAILURE_LOG_FILE}"
  echo "$(head -c $[PRINT_WIDTH] < /dev/zero | tr '\0' '=')" >> "${FAILURE_LOG_FILE}"
}

function reset_references {
  # Lopp through the tests
  for TEST in "${TESTS[@]}"; do
    local URL=$(cut -d'|' -f1 <<< "${TEST}")
    local REFERENCE_FILE=$(cut -d'|' -f2 <<< "${TEST}")

    local OPTION=$(option_from_file "${REFERENCE_FILE}")
    echo_info "  Resetting ${REFERENCE_FILE}"
    ${PROJECT_PATH}/recipe-dl/recipe-dl.py ${OPTION} -q -s -o "${REFERENCE_FILE_PATH}/${REFERENCE_FILE}" "${URL}" > /dev/null 2>/dev/null
    unset URL REFERENCE_FILE OPTION
  done
  unset TEST
}

function run_test() {
  local _URL="${1}"
  local _REFERENCE_FILE="${2:-}"

  local OPTION=$(option_from_file "${_REFERENCE_FILE}")
  local TMP_OUTPUT_FILE="$(mktemp ./test.output.XXXXXX)"
  rm "${TMP_OUTPUT_FILE}"

  echo_debug "Param: _URL=${_URL}"
  echo_debug "Param: _REFERENCE_FILE=${_REFERENCE_FILE}"
  echo_debug "Value: OPTION=${OPTION}"
  echo_debug "Value: TMP_OUTPUT_FILE=${TMP_OUTPUT_FILE}"

  local PRINT_WIDTH=$(tput cols)
  ((PRINT_WIDTH-=10))
  local PRINT_PARAM_WIDTH=$(($PRINT_WIDTH-13))
  local PRINT_OPTIONS=""
  PRINT_OPTIONS=$([ "${OPTION}" != "" ] && [ "${OPTION}" != " " ] && echo " (${OPTION})")
  local PRINT_URL=$(printf '%-'$(($PRINT_PARAM_WIDTH))'s' "${_URL}$PRINT_OPTIONS")
  if [ "${PRINT_URL:$(($PRINT_PARAM_WIDTH-1)):1}" == " " ]; then
    local PRINT_URL=$(printf '%.'$PRINT_PARAM_WIDTH's' "${_URL}${PRINT_OPTIONS}")
  else
    if [ "${PRINT_OPTIONS}" == "" ]; then
      PRINT_URL=$(printf '%.'$(($PRINT_PARAM_WIDTH-3))'s...' "${_URL}")
    else
      PRINT_URL=$(printf '%.'$(($PRINT_PARAM_WIDTH-8))'s...%s' "${_URL}" "${PRINT_OPTIONS}")
    fi
  fi
  printf 'Test: %-'$PRINT_PARAM_WIDTH's ' "${PRINT_URL}"

  if [ -s "${REFERENCE_FILE_PATH}/${_REFERENCE_FILE}" ]; then
    ${PROJECT_PATH}/recipe-dl/recipe-dl.py ${OPTION} -q -s -o "${TMP_OUTPUT_FILE}" "${_URL}" > /dev/null 2>/dev/null

    local TMP_OUTPUT_FILE_EXT="$(set -- $TMP_OUTPUT_FILE.*; echo "$1")"
    echo_debug "Compare File: \"$TMP_OUTPUT_FILE_EXT\""

    if diff --brief --ignore-trailing-space --ignore-blank-lines "${REFERENCE_FILE_PATH}/${_REFERENCE_FILE}" "${TMP_OUTPUT_FILE_EXT}" >/dev/null 2>&1 ; then
      ((COUNT_PASS++))
      echo "[${COLORS['pass']}PASS${COLORS['normal']}]"
    else
      ((COUNT_FAIL++))
      echo "[${COLORS['fail']}FAIL${COLORS['normal']}] see log"
      log_failure "${OPTION}" "${_URL}" "${_REFERENCE_FILE}" "${TMP_OUTPUT_FILE_EXT}"
    fi
    rm "${TMP_OUTPUT_FILE_EXT}" 2>/dev/null
  else
    ((COUNT_SKIP++))
    echo "[${COLORS['missing']}MISSING${COLORS['normal']}]"
    ${PROJECT_PATH}/recipe-dl/recipe-dl.py ${OPTION} -q -s -o "${REFERENCE_FILE_PATH}/${_REFERENCE_FILE}" "${_URL}" > /dev/null 2>/dev/null
  fi
}

function run_tests() {
  echo_info "Using reference file: ${REFERENCE_FILE_PATH}"
  if [ $FLAG_APPEND_LOG -eq 0 ] && [ ! -s $FLAG_APPEND_LOG ]; then
    echo_info "Failues will be logged to $FAILURE_LOG_FILE"
    rm "$FAILURE_LOG_FILE" 2>/dev/null
  else
    echo_info "Failues will be appended to $FAILURE_LOG_FILE"
  fi
  echo_info ""
  echo_info "Running Tests..."
  echo_info ""
  echo_info "$(head -c $(tput cols) < /dev/zero | tr '\0' '=')"
  echo_info ""

  COUNT_PASS=0
  COUNT_FAIL=0
  COUNT_SKIP=0

  # Loop through the tests
  for TEST in "${TESTS[@]}"; do
    local URL=$(cut -d'|' -f1 <<< "${TEST}")
    local REFERENCE_FILE=$(cut -d'|' -f2 <<< "${TEST}")
    run_test "${URL}" "${REFERENCE_FILE}"
    unset URL REFERENCE_FILE
  done
  unset TEST
  echo_info ""
  echo_info "$(head -c $(tput cols) < /dev/zero | tr '\0' '=')"
  echo_info ""
  echo_info "Results: ${COUNT_PASS} Passed  ${COUNT_FAIL} Failed  ${COUNT_SKIP} Skipped  "
}

check_requirements
parse_arguments "$@"
run_tests
append_tests
