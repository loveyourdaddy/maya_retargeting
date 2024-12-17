#!/bin/bash

# logs 디렉토리 생성
LOGS_DIR="logs"
mkdir -p "$LOGS_DIR"

# 로그 파일 설정 - logs 디렉토리 안에 저장
LOG_FILE="$LOGS_DIR/motion_test_$(date +%Y%m%d_%H%M%S).log"
TEST_RESULTS="$LOGS_DIR/test_results_$(date +%Y%m%d_%H%M%S).txt"

# 로그 함수
log() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}


# ''' functions '''
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

    # log "Running test case: $test_name"
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


# ''' list '''
# 소스 캐릭터 설정 (테스트할 캐릭터)
SOURCE_CHARACTER="Adori" # Adori2.0
SOURCE_CHAR_PATH="./models/${SOURCE_CHARACTER}/${SOURCE_CHARACTER}.fbx"

# 타겟 캐릭터 리스트
target_characters=(
    # "Adori"
    "Adori2.0"
    # "Asooni"
    # "Adori2.1"
    # "Asooni2.1"
)

# 결과 카운터 초기화
total_tests=0
passed_tests=0

# IFS 백업
OLDIFS="$IFS"
IFS=$'\n'

# 모든 모션 파일 찾기
motion_files=($(find "./motions/${SOURCE_CHARACTER}" -type f -name "*.fbx"))
echo "Found motion files:"
for motion in "${motion_files[@]}"; do
    echo "  $motion"
done


# ''' retarget '''
# 각 타겟 캐릭터에 대해 모든 모션 테스트
for target in "${target_characters[@]}"; do
    if [ "$SOURCE_CHARACTER" != "$target" ]; then
        target_char="./models/${target}/${target}.fbx"
        
        for motion in "${motion_files[@]}"; do
            motion_name=$(basename "$motion" .fbx)
            test_name="${SOURCE_CHARACTER}_to_${target}_${motion_name}"
            
            ((total_tests++))
            if run_test_case "$SOURCE_CHAR_PATH" "$motion" "$target_char" "$test_name"; then
                ((passed_tests++))
            fi
            
            # 테스트 간 간격
            sleep 2
        done
    fi
done

# 에러 케이스 테스트
log "=== Testing Error Cases ==="

# 성공률 계산
success_rate=$(echo "scale=2; ($passed_tests * 100) / $total_tests" | bc)
log "Success rate: ${success_rate}%"
