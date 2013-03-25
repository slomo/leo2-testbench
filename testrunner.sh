#!/usr/bin/env bash

LOGLEVEL="INFO"

# helper
function log() {
    local LL_INFO=6
    local LL_WARN=3
    local LL_ERR=1

    local LL_MSG=$1
    local MSG=$2

    if [[ LL_${LOGLEVEL} -ge LL_${LL_MSG} ]]; then
        eval "tput setaf \$LL_${LL_MSG}"
        echo "[${LL_MSG}]: ${MSG}"
        tput sgr0 # reset
    fi
}

function exit_with_reason() {
    log "ERR" "$1"
    exit 1
}

function usage() {
    echo "Usage: $0 <config_file>"
    exit 1
}

# process steps

# sideeffect: sets NEED_BUILD
function fetch_leo_source() {
    local GIT_URL=$1
    local GIT_COMMIT=$2
    local LEO_LOCATION=$3

    NEEDS_BUILD=false

    if [[ -d ${LEO_LOCATION} ]]; then
        [[ -d "${LEO_LOCATION}/.git" ]] || exit_with_reason "${LEO_LOCATION} contains no git, but exits aborting"
    else
        git clone "${GIT_URL}" ${LEO_LOCATION} || exit_with_raeson "Failed to clone git repo ${GIT_URL}"
        NEEDS_BUILD=true
    fi

    pushd ${LEO_LOCATION} > /dev/null

    if [[  $(git rev-parse HEAD) != ${GIT_COMMIT} ]]; then
        git checkout -f ${GIT_COMMIT}
        NEEDS_BUILD=true
    fi

    popd > /dev/null
}

function build_leo() {
    local LEO_LOCATION=$1

    pushd "${LEO_LOCATION}/src" > /dev/null || exit_with_reason "Unable to find leo src dir in \"${LEO_LOCATION}\""
    
    make clean opt || exit_with_reason "Failed to build leo in \"${LEO_LOCATION}\""

    popd > /dev/null
} 

function execute_leo() {
    
    local FILE=$1
    local TIME_STR=""

    local STD_ERR_FILE=$(mktemp)
    local STD_OUT_FILE=$(mktemp)


    TIME_STR=$( { TIMEFORMAT='%R, %U'; time leo.opt -t 60 ${FILE} >${STD_OUT_FILE} 2>${STD_ERR_FILE}; } 2>&1 )

    local SZS_STATUS=$(grep -o "^% SZS status [[:alpha:]]*"  ${STD_OUT_FILE})
    
    local SZS_STATUS=${SZS_STATUS#"% SZS status "}


    [[ -z ${SZS_STATUS} ]] && SZS_STATUS="Invalid"


    rm -rf ${STD_ERR_FILE}. ${STD_OUT_FILE}
    
    echo -n "${TIME_STR}, ${SZS_STATUS}"


}


function setup_workingdir() {

    local CONFIG_FILE=$1
    local WORKING_DIR=$2


    log "INFO" "reading config file"

    # check input parameter
    [[ -n $1 ]] || usage 
    [[ -f $1 ]] || exit_with_reason "Config file \"$1\" unreadable"

    # load and check config
    source $1

    [[ -n ${GIT_URL} ]] || exit_with_reason "Need GIT_URL to checkout code"
    [[ -n ${GIT_COMMIT} ]] || exit_with_reason "Need GIT_COMMIT to checkout code"
    [[ -n ${TPTP} ]] || exit_with_reason "Need TPTP base to include axioms"
    [[ -n ${TPTP_PROBLEMS} ]] || exit_with_reason "Need FILES to contain at least one test file"
    [[ -n ${E_PATH} ]] && PATH="${PATH}:${E_PATH}"


    pushd ${WORKING_DIR} > /dev/null

    # get and build leo in specified version
    log "INFO" "installing leo, if needed"
    fetch_leo_source "${GIT_URL}" "${GIT_COMMIT}" "./leo2"

    if ${NEEDS_BUILD}; then build_leo "./leo2"; fi

    PATH="${PATH}:./leo2/bin"


    # check if all provers are ready
    which leo.opt > /dev/null || exit_with_reason "Leo binary not found"
    which eprover > /dev/null || exit_with_reason "E binary not found"

    popd > /dev/null

}

function testrunner() {

    local CONFIG_FILE=$1
    local SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

    setup_workingdir ${CONFIG_FILE} ${SCRIPT_DIR}

    pushd ${SCRIPT_DIR} > /dev/null

    local RESULT_DIR="${SCRIPT_DIR}/results/$(date +%Y%m%d_%H%M%S)"
    mkdir -p ${RESULT_DIR}

    # collect infos
    log "INFO" "checking evironment"

    cp ${CONFIG_FILE} ${RESULT_DIR}

    echo "EPROVER_VERSION=\"$(eprover --version)\"" > ${RESULT_DIR}/info.sh
    echo "LEO_VERSION=\"$(leo.opt --version)\"" >> ${RESULT_DIR}/info.sh
    
    # run leo on all files
    log "INFO" "executing tests"

    # write header for csv
    echo "problem, runtime, usertime, result, expectedResult" > ${RESULT_DIR}/data.cvs

    
    for FILE in ${TPTP_PROBLEMS}; do
        local FILEPATH="${TPTP}/Problems/${FILE}"
        export TPTP
        local RESULT=$(execute_leo ${FILEPATH})
        local EXPECTED=$(grep "^% Status   : [[:alpha:]]*$"  ${FILEPATH})
        echo "${FILE}, ${RESULT}, ${EXPECTED:13}" >> ${RESULT_DIR}/data.cvs
    done


    # create lastRun symlink
    LATEST_LINK=${SCRIPT_DIR}/results/lastRun
    [[ ! -a  ${LATEST_LINK} || -L ${LATEST_LINK} ]] && ln -sfT ${RESULT_DIR} ${LATEST_LINK}

    log "INFO" "Sucessfull terminating"
    popd > /dev/null
}


if [[  $2 = shell ]]; then 
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    setup_workingdir $1 ${SCRIPT_DIR}
    pushd ${SCRIPT_DIR}
    bash     
    popd
else
    testrunner $@
fi
