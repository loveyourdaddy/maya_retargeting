#!/bin/bash

# IFS 백업
OLDIFS="$IFS"
IFS=$'\n'

# logs 디렉토리 생성
LOGS_DIR="logs"
mkdir -p "$LOGS_DIR"

TEST_DATE=$(date +%Y%m%d_%H%M%S)
BASE_TEST_DIR="./test_results/${TEST_DATE}"
mkdir -p "$BASE_TEST_DIR"
echo "Results in: $BASE_TEST_DIR"

# 로그 파일 설정 - logs 디렉토리 안에 저장
LOG_FILE="$LOGS_DIR/retargeting_test_$(date +%Y%m%d_%H%M%S).log"
TEST_RESULTS="$LOGS_DIR/test_results_$(date +%Y%m%d_%H%M%S).txt" # failed test list

# 변수 
GENERATE_VIDEO=false # true

# 캐릭터 폴더 리스트
src_characters=(
    "Adori"
    "Adori2.0"
    "Adori2.1"
    "Asooni"
    "Asooni2.0"

    # "Adori_qc"
    # "Adori2.0_qc"
    # "Asooni_qc"
)

tgt_characters=(
    "Adori"
    "Adori2.0"
    "Asooni"
    "Adori2.1"
    "Asooni2.0"

    "Metahuman_woMesh"
    # "Metahuman"
    "Minecraft"
    "Readyplayerme"
    "Roblox"
    "UE"
    "Zepeto"
)

# 로그 함수
log() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

# 테스트 결과 기록 함수
record_test_result() {
    local test_name="$1"
    local result="$2"
    echo "Test: $test_name - Result: $result" >> "$TEST_RESULTS"
}

# 테스트 케이스 실행 함수
run_test_case() {
    local source_char="$1"
    local source_motion="$2"
    local target_char="$3"
    local test_name="$4"
    
    log ">> COMMAND: python retargeting_request.py "$source_char" "$source_motion" "$target_char""
    output=$(python retargeting_request.py "$source_char" "$source_motion" "$target_char" 2>> "$LOG_FILE")
    
    if [[ $output == *"Download failed"* ]]; then
        log "❌" #  Test case $test_name failed
        log "Try mayapy retargeting_different_axis.py --sourceChar "$source_char" --sourceMotion "$source_motion" --targetChar "$target_char""
        record_test_result "$test_name" "FAIL" 
        return 1
    elif python retargeting_request.py "$source_char" "$source_motion" "$target_char" 2>> "$LOG_FILE"; then
        # success
        log "✅ \n" # Test case $test_name successful
        
        # 결과 FBX 파일 이동
        source_name=$(basename "$source_char" .fbx)
        target_name=$(basename "$target_char" .fbx)
        motion_name=$(basename "$source_motion" .fbx)
        result_file="${motion_name}.fbx"

        # dir
        result_dir="$BASE_TEST_DIR/${source_name}/${target_name}"

        # video path
        result_full_dir="/Users/inseo/2024_KAI_Retargeting/test_videos/${TEST_DATE}/${source_name}/${target_name}"

        if [ -f "$result_file" ]; then
            # 결과 fbx 파일이 존재하면 해당 디렉토리로 이동
            mv "$result_file" "$result_dir/"

            if [ "$GENERATE_VIDEO" = true ]; then
                # MP4 변환
                log "Converting FBX to MP4 using Maya..."
                mkdir -p "$result_full_dir"
                if [ $3 = "./models/UE/UE.fbx" ]; then
                    # maya
                    echo "mayapy render_fbx_maya.py "$result_dir/$result_file" "$result_full_dir""
                    mayapy render_fbx_maya.py "$result_dir/$result_file" "$result_full_dir"
                else
                    # blender
                    echo "/Applications/Blender.app/Contents/MacOS/Blender -b -P render_fbx_blender.py -- "$result_dir/$result_file" "$result_full_dir""
                    /Applications/Blender.app/Contents/MacOS/Blender -b -P render_fbx_blender.py -- "$result_dir/$result_file" "$result_full_dir"
                fi
            fi
        else
            log "Warning: Result file not found: $result_file \n"
        fi
        
        return 0
    else
        log "❌ Test case $test_name failed"
        record_test_result "$test_name" "FAIL"
        return 1
    fi
}

get_first_motion() {
    local character="$1"
    local motion_dir="./motions/${character}"
    
    # local first_motion=$(find "$motion_dir" -name "*.fbx" | sort | head -n 5 | tail -n 1)
    local first_motion=$(find "$motion_dir" -name "*.fbx" | grep -iv "Tpose\|t-pose\|t_pose" | sort | head -n 5 | tail -n 1)

    if [ -n "$first_motion" ]; then
        echo "$first_motion"
    else
        echo "No motion found for $character"
        echo "./motions/${character}/Tpose.fbx"  # 기본값
    fi
}

# 모든 모션 파일을 가져오는 함수
get_all_motions() {
    local character="$1"
    local motion_dir="./motions/${character}"
    
    # T-pose 관련 파일을 제외한 모든 FBX 파일 찾기
    local motions=($(find "$motion_dir" -name "*.fbx" | grep -iv "Tpose\|t-pose\|t_pose" | sort))
    
    if [ ${#motions[@]} -eq 0 ]; then
        log "Warning: No motions found for $character in $motion_dir"
        echo "./motions/${character}/Tpose.fbx"  # 기본값 반환
    else
        printf "%s\n" "${motions[@]}"
    fi
}

# 결과 카운터 초기화
total_tests=0
passed_tests=0

# 각 캐릭터 조합으로 테스트 실행
for source in "${src_characters[@]}"; do
    # 소스 캐릭터별 디렉토리 생성
    SOURCE_DIR="$BASE_TEST_DIR/${source}"
    mkdir -p "$SOURCE_DIR"

    # 소스 캐릭터의 첫 번째 모션 / 모든 모션 가져오기
    motion_files=($(get_first_motion "$source")) # get_all_motions
    log "Found ${#motion_files[@]} motion files for $source"
    
    # 각 모션 파일에 대해 테스트
    for motion_file in "${motion_files[@]}"; do
        motion_name=$(basename "$motion_file" .fbx)
        log "Processing motion: $motion_name"

        # target
        for target in "${tgt_characters[@]}"; do
            if [ "$source" != "$target" ]; then
                # 결과 파일을 저장할 타겟 디렉토리 생성
                TARGET_DIR="$SOURCE_DIR/${target}"
                mkdir -p "$TARGET_DIR"
                
                # 테스트 케이스 구성
                source_char="./models/${source}/${source}.fbx"
                source_motion="$motion_file"
                target_char="./models/${target}/${target}.fbx"
                test_name="${source}_to_${target}_${motion_name}"
                
                ((total_tests++))
                if run_test_case "$source_char" "$source_motion" "$target_char" "$test_name"; then
                    ((passed_tests++))
                fi
                
                # 테스트 간 간격
                sleep 2
            fi
        done
    done
done

# 결과 요약
log "=== Test Summary ==="
log "Total tests: $total_tests"
log "Passed tests: $passed_tests"
log "Failed tests: $((total_tests - passed_tests))"

# 성공률 계산
success_rate=$(echo "scale=2; ($passed_tests * 100) / $total_tests" | bc)
log "Success rate: ${success_rate}%"

# 결과 파일 위치 출력
echo ""
echo "Test completed. Logs are saved in:"
echo "Test results: $TEST_RESULTS"
