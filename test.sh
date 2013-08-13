#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CURRENT_LINK=${SCRIPT_DIR}/results/current
LAST_LINK=${SCRIPT_DIR}/results/last


function exit_with_reason() {
    tput setaf 1
    echo -n "ERR: "
    tput sgr0
    echo $1
    exit 1
}

function log_info() {
    tput setaf 6
    echo -n "INFO: "
    tput sgr0
    echo $1
}

# continue if last run not done
if [[ -L ${CURRENT_LINK} ]]; then
    log_info "Continue last run"
    make PROFILE="${CURRENT_LINK}/profile"
    exit 1

fi


# load and check config
source $1 || exit_with_reason "Unable to find config file '$1'"
CONFIG_FILE=$1

RESULT_PREFIX="results/$(date +%Y%m%d_%H%M%S)"
RESULT_DIR="${PWD}/${RESULT_PREFIX}"
mkdir -p ${RESULT_DIR}
ln ${RESULT_DIR} -s ${CURRENT_LINK}
ln ${RESULT_DIR} -sf ${LAST_LINK}


[[ -n ${E_VERSION} ]] || E_VERSION=1.8
[[ -n ${TPTP_VERSION} ]] || TPTP_VERSION=5.5.0
[[ -n ${GIT_COMMIT} ]] || exit_with_reason "Need GIT_COMMIT to checkout code"
[[ -n ${TPTP_PROBLEMS} ]] || exit_with_reason "Need FILES to contain at least one test file"
[[ -n ${TIMELIMIT} ]] || TIMELIMIT=30
[[ -n ${LEO_OPTS} ]] || LEO_OPTS="-f e"


LEO_OPTS="${LEO_OPTS} -t ${TIMELIMIT} --atp e=E-${E_VERSION}/PROVER/eprover"

PROFILE="${RESULT_DIR}/profile"
cp ${CONFIG_FILE} ${RESULT_DIR}/config

TARGETS=""

for FILE in ${TPTP_PROBLEMS}; do
    TARGETS="${RESULT_PREFIX}/${FILE}.cvs ${TARGETS}"
done

cat > ${PROFILE} <<EOF
export PATH := leo-git-${GIT_COMMIT}/bin:\$(PATH)
export TPTP := TPTP-v${TPTP_VERSION}

${RESULT_PREFIX}/summery.cvs: ${TARGETS}
	cat \$^ > \$@
	rm ${CURRENT_LINK}

${RESULT_PREFIX}/%.p.cvs: TPTP-v${TPTP_VERSION} leo-git-${GIT_COMMIT} E-${E_VERSION}
	mkdir -p \$(dir \$@)
	./leo-wrapper.sh \$(TPTP)/Problems/\$*.p ${LEO_OPTS} > \$@
EOF

make PROFILE="${PROFILE}"
