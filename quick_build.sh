#!/bin/sh

#
# Cliff Dong
# Quick build command generator
#
# 10/9/2016
#

LIB_DEF_FILES="build/products/SF-RP-P1S/Make.mk \
ipos/legacy/pkt/sw/se/xc/bsd/Dir.mk"

DBG=0
OUT_SCRIPT="quick_build_temp.sh"
STRIP="/proj/spr/toolchain/aarch64-mvista-linux/sysroots/x86_64-oesdk-linux/usr/bin/aarch64-mvista-linux/aarch64-mvista-linux-strip"

clear_file() {
    echo > ${OUT_SCRIPT}
}

append2file() {
    echo "$1" >> ${OUT_SCRIPT}
}

get_value() {
    str=$1
    VALUE=`awk -F'=' '{print $2}' ${str}`
}

is_CC_file() {
    echo "$1" | grep '\.cc$'
    if [ $? -eq 0 ]; then
        return 1
    else
        return 0
    fi
}

usage() {
    echo "quick_build.sh <source_file_path> [-D(debug on)]"
}

if [ $# -lt 1 ]; then
    usage
    exit 0
fi

# main starts here

SRC_PATH=$1
BUILD_LOG="/home/eaizhao/build_lc_log"

DIR=`dirname ${SRC_PATH}`
FILE=`basename ${SRC_PATH}`

MKFILE="${DIR}/Dir.mk"

TARGET=""
TARGET_TYPE=""
OBJ=""
OBJ_TYPE=""
NUM_LINES=0

is_CC_file ${FILE}
if [ $? -eq 1 ]; then
    OBJ=`echo ${FILE} | sed "s/\.cc/.o/g"`
else
    OBJ=`echo ${FILE} | sed "s/\.c/.o/g"`
fi

# Find lib target in Dir.mk
grep "LIB :=" ${MKFILE}
if [ $? -eq 0 ]; then
    LIB=`grep "LIB :=" ${MKFILE} | grep '\.a$'`
    if [ $? -eq 0 ]; then
        TARGET=`grep "LIB :=" ${MKFILE} | awk -F'=' '{print $2}'`
    else
        LIB=`grep "LIB :=" ${MKFILE} | awk -F'=' '{print $2}' | awk -F'(' '{print $2}' |awk -F')' '{print $1}'`
        TARGET=`cat ${LIB_DEF_FILES} | grep ${LIB} | awk -F'=' '{print $2}'`
    fi
    TARGET=`basename ${TARGET} | sed "s/\.a/.so.0.0/g"`
    TARGET_TYPE="Lib ("
    NUM_LINES=6
    is_CC_file ${FILE}
    if [ $? -eq 1 ]; then
        OBJ_TYPE="LibCCObj ("
    else
        OBJ_TYPE="LibCObj ("
    fi
fi

# Find bin target in Dir.mk
grep "BIN :=" ${MKFILE}
if [ $? -eq 0 ]; then
    BIN=`grep "BIN :=" ${MKFILE} | awk -F'=' '{print $2}'`
    TARGET=`echo "${BIN}" | sed 's/^[ \t]*//g'`
    TARGET_TYPE="Bin ("
    NUM_LINES=4
    is_CC_file ${FILE}
    if [ $? -eq 1 ]; then
        OBJ_TYPE="BinCCObj ("
    else
        OBJ_TYPE="BinCObj ("
    fi
fi

echo "==============================================================================="
echo "FILE: ${FILE}"
echo "MKFILE: ${MKFILE}"
echo "OBJ: ${OBJ}"
echo "OBJ_TYPE: ${OBJ_TYPE}"
echo "TARGET: ${TARGET}"
echo "TARGET_TYPE: ${TARGET_TYPE}"

# Grep make command from verbose build log
OBJ_CMD=`grep "${OBJ}" ${BUILD_LOG} | grep -A 1 "${OBJ_TYPE}" | grep -v "${OBJ_TYPE}"`
TARGET_CMD=`grep -A ${NUM_LINES} "${TARGET_TYPE}.*${TARGET}" ${BUILD_LOG} | grep -v "${TARGET_TYPE}" | grep -v "genver" | grep -v "mkdir"`

clear_file
chmod +x quick_build_temp.sh

append2file "cd ipos/legacy/pkt/"
append2file "${OBJ_CMD}"
append2file
append2file "${TARGET_CMD}"
append2file
append2file "cd -"
append2file

# Handle debug info strip

OUT_BASE_DIR=`cat .scratch | awk -F':=' '{print $2}'`

cd ${OUT_BASE_DIR}

PATHS=`find -type f -name "${TARGET}"`

for path in ${PATHS}
do
    echo ${path} | grep '\/stage\/' 1>/dev/null 2>&1
    if [ $? -eq 0 ]; then
        STAGE_PATH=${path}
    else
        ORIG_PATH=${path}
    fi
done

echo "STAGE_PATH: ${STAGE_PATH}"
echo "ORIG_PATH: ${ORIG_PATH}"
echo "==============================================================================="
cd -

append2file "cd ${OUT_BASE_DIR}"
append2file "cp ${ORIG_PATH} ${TARGET}"
if [ ${DBG} -eq 0 ]; then
    append2file "${STRIP} --strip-debug --strip-all ${TARGET}"
fi
if [ "${TARGET_TYPE}" == "Bin (" ]; then
    append2file "md5sum ${TARGET} | awk '{print \$1;}' >> ${TARGET}"
fi
append2file "mv ${TARGET} ${STAGE_PATH}"
append2file "cd -"

append2file "echo \"===============================================================================\""
append2file "echo \"Done! Build result - ${OUT_BASE_DIR}/${STAGE_PATH}\""
append2file "echo \"===============================================================================\""
