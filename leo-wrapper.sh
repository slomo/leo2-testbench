#!/bin/bash

# only out put header
if [[ -z $1 ]]; then
    echo "problem, realtime, usertime, status, counter, timer"
    exit 0
fi

LEO_OPTS=${*:3}
FILE=$1
OUTFILE=$2

PROBLEM=$(basename $1)

STD_ERR_FILE=${OUTFILE}.stderr
STD_OUT_FILE=${OUTFILE}.stdout
TIME_STR=$({ TIMEFORMAT='%R, %U'; time timeout $((TIMELIMIT + 5)) leo ${LEO_OPTS} ${FILE} >${STD_OUT_FILE} 2>${STD_ERR_FILE}; } 2>&1)
TIMEOUT_RETURN=$?

echo "[cmd]: leo ${LEO_OPTS} ${FILE}"

# if error also output stdout
if [[ ${TIMEOUT_RETURN} -eq 255 ]]; then
    echo ">>> prover std_out for ${FILE} >>>"
    cat ${STD_OUT_FILE}
fi
echo ">>> prover std_err for ${FILE} >>>"
cat ${STD_ERR_FILE}
echo ">>>>>>"

# handle szs-status
SZS_STATUS=$(grep -m 1 -o "^% SZS status [[:alpha:]]*"  ${STD_OUT_FILE})
[[ -z ${SZS_STATUS} && ${TIMEOUT_RETURN} -eq 124 ]] && SZS_STATUS="Timeout"
[[ -z ${SZS_STATUS} ]] && SZS_STATUS="Error"

COUNTER=$(grep -m 1 "% LEO-II counters:"  ${STD_OUT_FILE})
COUNTER=${COUNTER#"% LEO-II counters:"}

TIMER=$(grep -m 1 "% LEO-II timers:"  ${STD_OUT_FILE})
TIMER=${TIMER#"% LEO-II timers:"}

SZS_STATUS=${SZS_STATUS#"% SZS status "}
echo "${PROBLEM}, ${TIME_STR}, ${SZS_STATUS}, ${COUNTER}, ${TIMER}" > ${OUTFILE}
