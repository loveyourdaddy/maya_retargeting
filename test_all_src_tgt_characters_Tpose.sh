#!/bin/bash

# logs 디렉토리 생성
LOGS_DIR="logs"
mkdir -p "$LOGS_DIR"

TEST_DATE=$(date +%Y%m%d_%H%M%S)
BASE_TEST_DIR="./test_results/${TEST_DATE}"
mkdir -p "$BASE_TEST_DIR"


# 로그 파일 설정 - logs 디렉토리 안에 저장
LOG_FILE="$LOGS_DIR/retargeting_test_$(date +%Y%m%d_%H%M%S).log"
TEST_RESULTS="$LOGS_DIR/test_results_$(date +%Y%m%d_%H%M%S).txt"

# 로그 함수
log() {
    local message="$1" # "[$(date +'%Y-%m-%d %H:%M:%S')] 
    echo "$message" | tee -a "$LOG_FILE"
    # echo  -a "$LOG_FILE"
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
    
    log "python retargeting_request.py "$source_char" "$source_motion" "$target_char""
    if python retargeting_request.py "$source_char" "$source_motion" "$target_char" 2>> "$LOG_FILE"; then
        log "✅ Test case $test_name successful"
        # record_test_result "$test_name" "PASS"
        
        # 결과 FBX 파일 이동
        # 예상되는 결과 파일명 패턴에 따라 수정 필요
        source_name=$(basename "$source_char" .fbx)
        target_name=$(basename "$target_char" .fbx)
        motion_name=$(basename "$source_motion" .fbx)
        result_file="${motion_name}.fbx"
        result_dir="$BASE_TEST_DIR/${source_name}/${target_name}"
        
        echo mv "$result_file" "$result_dir/"
        if [ -f "$result_file" ]; then
            # 결과 파일이 존재하면 해당 디렉토리로 이동
            mv "$result_file" "$result_dir/"
            log "Moved result file to $result_dir/"
        else
            log "Warning: Result file not found: $result_file"
        fi
        
        return 0
    else
        log "❌ Test case $test_name failed"
        record_test_result "$test_name" "FAIL"
        return 1
    fi
}


# 캐릭터 폴더 리스트
characters=(
    "Adori"
    "Adori2.0"
    "Asooni"
    "Adori2.1"
    "Asooni2.1"

    "Metahuman"
    "Minecraft"
    "Readyplayerme"
    "Roblox"
    "UE"
    "Zepeto"
)


# 결과 카운터 초기화
total_tests=0
passed_tests=0

# 각 캐릭터 조합으로 테스트 실행
for source in "${characters[@]}"; do
    # 소스 캐릭터별 디렉토리 생성
    SOURCE_DIR="$BASE_TEST_DIR/${source}"
    mkdir -p "$SOURCE_DIR"

    for target in "${characters[@]}"; do
        if [ "$source" != "$target" ]; then
            # 결과 파일을 저장할 타겟 디렉토리 생성
            TARGET_DIR="$SOURCE_DIR/${target}"
            mkdir -p "$TARGET_DIR"
            
            # 테스트 케이스 구성
            source_char="./models/${source}/${source}.fbx"
            source_motion="./motions/${source}/Tpose.fbx"
            target_char="./models/${target}/${target}.fbx"
            test_name="${source}_to_${target}_Tpose"
            
            ((total_tests++))
            if run_test_case "$source_char" "$source_motion" "$target_char" "$test_name"; then
                ((passed_tests++))
            fi
            
            # 테스트 간 간격
            sleep 2
        fi
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
echo "Detailed log: $LOG_FILE"
echo "Test results: $TEST_RESULTS"
