#!/bin/bash
LEO_OPTS=${*:2}
FILE=$1
PROBLEM=$(basename $1)

STD_ERR_FILE=$(mktemp)
STD_OUT_FILE=$(mktemp)
TIME_STR=$({ TIMEFORMAT='%R, %U'; time timeout $((TIMELIMIT + 5)) leo ${LEO_OPTS} ${FILE} >${STD_OUT_FILE} 2>${STD_ERR_FILE}; } 2>&1)
cat ${STD_ERR_FILE} 1>&2


# handle szs-status
SZS_STATUS=$(grep -m 1 -o "^% SZS status [[:alpha:]]*"  ${STD_OUT_FILE})
[[ -z ${SZS_STATUS} ]] && SZS_STATUS="Error"

SZS_STATUS=${SZS_STATUS#"% SZS status "}
rm -rf ${STD_ERR_FILE}. ${STD_OUT_FILE}
echo "${PROBLEM}, ${TIME_STR}, ${SZS_STATUS}"
