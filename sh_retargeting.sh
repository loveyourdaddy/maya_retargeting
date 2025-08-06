#!/bin/bash

# FBX to BVH Batch Converter
# Usage: ./fbx2bvh.sh

SOURCE_CHAR="./models/SMPL/SMPL.fbx"
SOURCE_DIR="./motions/SMPL/"
TARGET_CHAR="./models/SMPL/SMPL.fbx"

# Default paths
INPUT_FOLDER="./motions/SMPL/" # folder 
FILES=("IAM.bvh" "Siren.bvh" "Sticky.bvh" "Summer.bvh" "Way4Love.bvh")
# FILES=[IAM.bvh, Siren.bvh, Sticky.bvh, Summer.bvh, Way4Love.bvh]

# Conversion counters
SUCCESS_COUNT=0
FAILED_COUNT=0
FAILED_FILES=()

# Convert each FBX file
for file in "${FILES[@]}"; do    
    SOURCE_MOTION="$SOURCE_DIR$file"
    echo "Processing file: $SOURCE_MOTION"

    # Run the conversion
    if mayapy run_retargeting.py  --sourceChar "$SOURCE_CHAR" --sourceMotion "$SOURCE_MOTION" --targetChar "$TARGET_CHAR" ; then
        echo "✓ Successfully : $file"
        ((SUCCESS_COUNT++))
    else
        echo "✗ Failed: $file"
        ((FAILED_COUNT++))
        FAILED_FILES+=("$file")
    fi
done

if [[ $FAILED_COUNT -gt 0 ]]; then
    echo ""
    echo "Failed files:"
    for failed_file in "${FAILED_FILES[@]}"; do
        echo "  - $failed_file"
    done
fi
