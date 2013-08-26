#!/bin/bash
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
    [[ -n ${FO_PROVERS} ]] || FO_PROVERS="E-1.8"
    [[ -n ${TIMELIMIT} ]] || TIMELIMIT=30
    [[ -n ${LEO_OPTS} ]] || LEO_OPTS="-f e"
    [[ -n ${LEO_VERSION} ]] || exit_with_reason "Need LEO_VERSION to test"
    [[ -n ${TPTP_PROBLEMS} ]] || exit_with_reason "Need TPTP_PROBLEMS to contain at least one test file"
    [[ -n ${APPEND_OPTS} ]] || APPEND_OPTS=""
}

function generate_opts() {
    LEO_OPTS=""
    CSV="${LEO_VERSION},${TPTP_VERSION}"
    PROVERS=()
    for prover in "${FO_PROVERS[@]}"; do
        CSV="${CSV},${prover}"
        case ${prover} in
            E-*)
                PROVERS+=("e")
                LEO_OPTS="${LEO_OPTS} --atp e=${prover}/PROVER/eprover"
                ;;
            SPASS-*)
                PROVERS+=("spass")
                LEO_OPTS=" ${LEO_OPTS} --atp spass=${prover}/SPASS"
                ;;
        esac
    done
    SAVE_IFS=$IFS
    IFS=","
    PROVERS="${PROVERS[*]}"
    IFS=$SAVE_IFS
    LEO_OPTS="${LEO_OPTS} -f ${PROVERS} -t ${TIMELIMIT} ${APPEND_OPTS}"
}

# continue if last run not done
if [[ -L ${CURRENT_LINK} ]]; then
    log_info "Continue last run"
    make PROFILE="${CURRENT_LINK}/profile"
    exit 1

fi

load_config $1
generate_opts

RESULT_PREFIX="run/$(date +%Y%m%d_%H%M%S)"
RESULT_DIR="${PWD}/${RESULT_PREFIX}"
PROFILE="${RESULT_DIR}/profile"

mkdir -p ${RESULT_DIR}
ln ${RESULT_DIR} -s ${CURRENT_LINK}
ln ${RESULT_DIR} -sf ${LAST_LINK}
cp ${CONFIG_FILE} ${RESULT_DIR}/config.sh
echo ${CSV} > ${RESULT_DIR}/config.csv

# generate problem list
TARGETS=""
for FILE in ${TPTP_PROBLEMS}; do
    TARGETS="${RESULT_PREFIX}/${FILE}.csv ${TARGETS}"
done

cat > ${PROFILE} <<EOF
export PATH := leo-${LEO_VERSION}/bin:\$(PATH)
export TPTP := TPTP-v${TPTP_VERSION}

${RESULT_PREFIX}/summary.csv: ${TARGETS}
	./leo-wrapper.sh > \$@
	cat \$^ >> \$@
	rm ${CURRENT_LINK}


${RESULT_PREFIX}/%.p.csv: TPTP-v${TPTP_VERSION} ${FO_PROVERS} leo-${LEO_VERSION}
	mkdir -p \$(dir \$@)
	./leo-wrapper.sh \$(TPTP)/Problems/\$*.p ${LEO_OPTS} > \$@
EOF

make PROFILE="${PROFILE}"
