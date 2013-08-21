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

function load_config() {
    source $1 || exit_with_reason "Unable to find config file '$1'"
    CONFIG_FILE=$1

    [[ -n ${TPTP_VERSION} ]] || TPTP_VERSION="5.5.0"
    [[ -n ${FO_PROVERS} ]] || FO_PROVERS="E-1.8"
    [[ -n ${TIMELIMIT} ]] || TIMELIMIT=30
    [[ -n ${LEO_OPTS} ]] || LEO_OPTS="-f e"
    [[ -n ${GIT_COMMIT} ]] || exit_with_reason "Need GIT_COMMIT to checkout code"
    [[ -n ${TPTP_PROBLEMS} ]] || exit_with_reason "Need FILES to contain at least one test file"
    [[ -n ${APPEND_OPTS} ]] || APPEND_OPTS=""
}

function generate_opts() {
    LEO_OPTS=""
    for prover in "${FO_PROVERS[@]}"; do
        case ${prover} in
            E-*)
                LEO_OPTS="${LEO_OPTS} -f e --atp e=${prover}/PROVER/eprover"
                ;;
            SPASS-*)
                LEO_OPTS=" ${LEO_OPTS} -f spass --atp spass=${prover}/SPASS"
                ;;
        esac
    done
    LEO_OPTS="${LEO_OPTS} -t ${TIMELIMIT} ${APPEND_OPTS}"
}

# continue if last run not done
if [[ -L ${CURRENT_LINK} ]]; then
    log_info "Continue last run"
    make PROFILE="${CURRENT_LINK}/profile"
    exit 1

fi

load_config $1
generate_opts

RESULT_PREFIX="results/$(date +%Y%m%d_%H%M%S)"
RESULT_DIR="${PWD}/${RESULT_PREFIX}"
PROFILE="${RESULT_DIR}/profile"

mkdir -p ${RESULT_DIR}
ln ${RESULT_DIR} -s ${CURRENT_LINK}
ln ${RESULT_DIR} -sf ${LAST_LINK}
cp ${CONFIG_FILE} ${RESULT_DIR}/config

# generate problem list
TARGETS=""
for FILE in ${TPTP_PROBLEMS}; do
    TARGETS="${RESULT_PREFIX}/${FILE}.csv ${TARGETS}"
done

cat > ${PROFILE} <<EOF
export PATH := leo-git-${GIT_COMMIT}/bin:\$(PATH)
export TPTP := TPTP-v${TPTP_VERSION}

${RESULT_PREFIX}/summary.csv: ${TARGETS}
	./leo-wrapper.sh > \$@
	cat \$^ >> \$@
	rm ${CURRENT_LINK}


${RESULT_PREFIX}/%.p.csv: TPTP-v${TPTP_VERSION} ${FO_PROVERS}
	mkdir -p \$(dir \$@)
	./leo-wrapper.sh \$(TPTP)/Problems/\$*.p ${LEO_OPTS} > \$@
EOF

make PROFILE="${PROFILE}"
