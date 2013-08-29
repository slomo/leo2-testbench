#!/bin/bash
# seems to have implication on computation
export LC_ALL=C

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CURRENT_LINK=${SCRIPT_DIR}/run/current
LAST_LINK=${SCRIPT_DIR}/run/last


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
    [[ -n ${FO_PROVERS} ]] || FO_PROVERS=("E-1.8")
    [[ -n ${TIMELIMIT} ]] || TIMELIMIT=30
    [[ -n ${LEO_VERSION} ]] || exit_with_reason "Need LEO_VERSION to test"
    [[ -n ${TPTP_PATTERN} ]] || exit_with_reason "Need TPTP_PROBLEMS to contain a pattern"
    [[ -n ${APPEND_OPTS} ]] || APPEND_OPTS=""

    # generate list of tptp problems
    TPTP_PROBLEMS=$(find TPTP-v${TPTP_VERSION}/Problems -iname "${TPTP_PATTERN}" |
        sed 's/.*\b\([A-Z]\{3\}\)\b/\1/')
}

function generate_opts() {
    # values returned from that function
    LEO_OPTS=""
    FO_BINARIES=""

    local PROVERS=()
    local BINARY
    local PROVER

    for PROVER_NAME in "${FO_PROVERS[@]}"; do
        BINARY="${PROVER_NAME}/"
        case ${PROVER_NAME} in
            E-*)
                PROVER="e"
                BINARY="${BINARY}/PROVER/eprover"
                ;;
            SPASS-*)
                BINARY="${BINARY}/SPASS"
                PROVER="spass"
                ;;
        esac
        LEO_OPTS=" ${LEO_OPTS} --atp ${PROVER}=${BINARY}"
        PROVERS+=(${PROVER})
        FO_BINARIES="${FO_BINARIES} ${BINARY}"
    done

    # join provers with comma
    local SAVE_IFS=${IFS}
    IFS=","
    PROVERS="${PROVERS[*]}"
    IFS=${SAVE_IFS}

    LEO_OPTS="${LEO_OPTS} -f ${PROVERS} -t ${TIMELIMIT} ${APPEND_OPTS}"
}

function next_run() {
    local LAST=$(pushd run > /dev/null ; ls | sort -n | tail -1 ; popd > /dev/null)
    printf "%.2d" $((LAST + 1))
}

# continue if last run not done
if [[ -L ${CURRENT_LINK} ]]; then
    log_info "Continue last run"
    make PROFILE="${CURRENT_LINK}/profile"
    exit 1

fi

load_config $1
generate_opts

RESULT_PREFIX="run/$(next_run)"
RESULT_DIR="${PWD}/${RESULT_PREFIX}"
PROFILE="${RESULT_DIR}/profile"

mkdir -p ${RESULT_DIR}
ln ${RESULT_DIR} -s ${CURRENT_LINK}
ln ${RESULT_DIR} -sf ${LAST_LINK}
cp ${CONFIG_FILE} ${RESULT_DIR}/config.sh
echo $(date) >  ${RESULT_DIR}/time
# generate problem list
TARGETS=""
for FILE in ${TPTP_PROBLEMS}; do
    TARGETS="${RESULT_PREFIX}/${FILE}.csv ${TARGETS}"
done

cat > ${PROFILE} <<EOF
export PATH := leo-${LEO_VERSION}/bin:\$(PATH)
export TPTP := TPTP-v${TPTP_VERSION}
export TIMEOUT := ${TIMELIMIT}

${RESULT_PREFIX}/summary.csv: ${TARGETS}
	./leo-wrapper.sh > \$@
	cat \$^ >> \$@
	rm ${CURRENT_LINK}


${RESULT_PREFIX}/%.p.csv: TPTP-v${TPTP_VERSION} ${FO_BINARIES} leo-${LEO_VERSION}/bin/leo
	mkdir -p \$(dir \$@)
	./leo-wrapper.sh \$(TPTP)/Problems/\$*.p ${LEO_OPTS} > \$@
EOF

make PROFILE="${PROFILE}"