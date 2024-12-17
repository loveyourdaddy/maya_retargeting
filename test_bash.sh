#!/bin/bash

# logs 디렉토리 생성
LOGS_DIR="logs"
mkdir -p "$LOGS_DIR"

# 로그 파일 설정 - logs 디렉토리 안에 저장
LOG_FILE="$LOGS_DIR/retargeting_test_$(date +%Y%m%d_%H%M%S).log"
TEST_RESULTS="$LOGS_DIR/test_results_$(date +%Y%m%d_%H%M%S).txt"

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

    log "Running test case: $test_name"
    log "Source Character: $source_char"
    log "Source Motion: $source_motion"
    log "Target Character: $target_char"
    log "python retargeting_request.py "$source_char" "$source_motion" "$target_char""

    if python retargeting_request.py "$source_char" "$source_motion" "$target_char" 2>> "$LOG_FILE"; then
        log "✅ Test case $test_name successful"
        record_test_result "$test_name" "PASS"
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
)
    # "Metahuman"
    # "Minecraft"
    # "Readyplayerme"
    # "Roblox"
    # "UE"
    # "Zepeto"

# 테스트 시작
log "=== Starting Character Retargeting Tests ==="
log "Logs will be saved in: $LOGS_DIR/"

# 결과 카운터 초기화
total_tests=0
passed_tests=0

# 각 캐릭터 조합으로 테스트 실행
for source in "${characters[@]}"; do
    for target in "${characters[@]}"; do
        if [ "$source" != "$target" ]; then
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

# 에러 케이스 테스트
log "=== Testing Error Cases ==="

# 존재하지 않는 캐릭터 테스트
run_test_case "./models/NonExistent/NonExistent.fbx" "./models/Adori/Tpose.fbx" "./models/Adori/Adori.fbx" "NonExistent_Source_Character"
((total_tests++))

# 존재하지 않는 모션 테스트
# python retargeting_request.py ./models/Adori2.1/Adori2.1.fbx "./motions/Adori2.1/DumbellUpperBodyOverheadTricepPress.fbx" ./models/Asooni/Asooni.fbx 
run_test_case "./models/Adori/Adori.fbx" "./models/NonExistent/Tpose.fbx" "./models/Asooni/Asooni.fbx" "NonExistent_Motion"
((total_tests++))

# 결과 요약
log "=== Test Summary ==="
log "Total tests: $total_tests"
log "Passed tests: $passed_tests"
log "Failed tests: $((total_tests - passed_tests))"

# 결과 파일 위치 출력
echo ""
echo "Test completed. Logs are saved in:"
echo "Detailed log: $LOG_FILE"
echo "Test results: $TEST_RESULTS"

# 성공률 계산
success_rate=$(echo "scale=2; ($passed_tests * 100) / $total_tests" | bc)
log "Success rate: ${success_rate}%"

# 모든 테스트가 성공했는지 확인
if [ "$passed_tests" -eq "$total_tests" ]; then
    log "✅ All tests passed successfully"
    exit 0
else
    log "❌ Some tests failed"
    exit 1
fi