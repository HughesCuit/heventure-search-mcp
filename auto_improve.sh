#!/bin/bash
#===============================================================================
# heventure-search-mcp 自动改进循环
# 每天北京时间 00:00 执行
# 
# 改进流程:
#   1. 依赖检查 (outdated + security)
#   2. 代码质量 (ruff check + format)
#   3. 测试 (pytest)
#   4. 性能基准测试 (记录 + 对比)
#   5. 自动更新 CHANGELOG
#   6. Git commit + tag (有改动时)
#   7. 生成改进报告
#===============================================================================

set -e

PROJECT_DIR="/home/huanghe/heventure-search-mcp"
cd "$PROJECT_DIR"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S CST')
LOG_FILE="$PROJECT_DIR/improve_log_$(date '+%Y%m%d').txt"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%H:%M:%S')] $1"
    echo "[$(date '+%H:%M:%S')] $1" >> "$LOG_FILE"
}

report() {
    echo -e "${BLUE}[REPORT]${NC} $1"
    echo "[REPORT] $1" >> "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    echo "[WARN] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $1" >> "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
    echo "[OK] $1" >> "$LOG_FILE"
}

#-------------------------------------------------------------------------------
# 开始
#-------------------------------------------------------------------------------
log "=========================================="
log "heventure-search-mcp 自动改进循环"
log "时间: $TIMESTAMP"
log "=========================================="

# 激活虚拟环境
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
fi

PYTHON="$PROJECT_DIR/.venv/bin/python"

CHANGES_MADE=""
CHANGELOG_UPDATED=""
PERF_REGRESSION=""
TEST_FAILED=""
DEPS_UPDATED=""

#-------------------------------------------------------------------------------
# Step 1: 依赖检查
#-------------------------------------------------------------------------------
log ""
log "--- Step 1: 依赖检查 ---"

# 检查过时包（使用 uv pip）
if [ -f "$PROJECT_DIR/pyproject.toml" ]; then
    # 用 uv pip list 检查过时包
    uv pip list --outdated 2>/dev/null > /tmp/outdated.txt || true
    if [ -s /tmp/outdated.txt ]; then
        OUTDATED_COUNT=$(wc -l < /tmp/outdated.txt)
        warn "发现 $OUTDATED_COUNT 个过时包"
        head -20 /tmp/outdated.txt >> "$LOG_FILE"
        
        # 尝试安全升级
        log "尝试安全升级..."
        uv pip install -r "$PROJECT_DIR/requirements.txt" --upgrade 2>&1 >> "$LOG_FILE" || true
        
        # 检查是否真的升级了
        NEW_OUTDATED=$(uv pip list --outdated 2>/dev/null | wc -l)
        if [ "$NEW_OUTDATED" -lt "$OUTDATED_COUNT" ]; then
            DEPS_UPDATED="✅ 依赖升级完成 ($OUTDATED_COUNT → $NEW_OUTDATED 个过时包)"
            success "$DEPS_UPDATED"
            CHANGES_MADE="yes"
        fi
    else
        success "所有依赖已是最新"
    fi
fi

#-------------------------------------------------------------------------------
# Step 2: 代码质量检查
#-------------------------------------------------------------------------------
log ""
log "--- Step 2: 代码质量检查 ---"

# ruff check
if command -v ruff &> /dev/null; then
    RUFF_OUTPUT=$(ruff check "$PROJECT_DIR" 2>&1) || true
    if [ -n "$RUFF_OUTPUT" ]; then
        warn "ruff 发现问题:"
        echo "$RUFF_OUTPUT" >> "$LOG_FILE"
        # 自动修复（允许失败，用 || true 避免 set -e 退出）
        ruff check --fix "$PROJECT_DIR" 2>&1 >> "$LOG_FILE" || true
        RUFF_AFTER=$(ruff check "$PROJECT_DIR" 2>&1) || true
        if [ -n "$RUFF_AFTER" ]; then
            warn "自动修复后仍有问题，需人工处理"
        else
            success "ruff 自动修复完成"
            CHANGES_MADE="yes"
        fi
    else
        success "ruff 检查通过"
    fi
fi

# ruff format check
if command -v ruff &> /dev/null; then
    RUFF_FORMAT=$(ruff format --check "$PROJECT_DIR" 2>&1) || true
    if [ -n "$RUFF_FORMAT" ]; then
        warn "代码格式不符合规范，自动格式化..."
        ruff format "$PROJECT_DIR" 2>&1 >> "$LOG_FILE" || true
        success "ruff format 完成"
        CHANGES_MADE="yes"
    else
        success "ruff format 检查通过"
    fi
fi

#-------------------------------------------------------------------------------
# Step 3: 运行测试
#-------------------------------------------------------------------------------
log ""
log "--- Step 3: 运行测试 ---"

TEST_LOG="$PROJECT_DIR/test_results_$(date '+%Y%m%d').json"
if [ -d "$PROJECT_DIR/tests" ]; then
    PYTEST_EXIT=0
    PYTEST_OUTPUT=$($PYTHON -m pytest tests/ -v --tb=short 2>&1) || PYTEST_EXIT=$?
    if [ $PYTEST_EXIT -eq 0 ]; then
        success "所有测试通过 ✅"
    else
        warn "测试失败 (exit $PYTEST_EXIT)"
        echo "$PYTEST_OUTPUT" >> "$LOG_FILE"
        TEST_FAILED="⚠️ 测试失败，需人工检查"
        echo "$PYTEST_OUTPUT" | grep -E "ERROR|FAILED" | head -10 >> "$LOG_FILE"
    fi
else
    report "无测试目录，跳过"
fi

#-------------------------------------------------------------------------------
# Step 4: 性能基准测试
#-------------------------------------------------------------------------------
log ""
log "--- Step 4: 性能基准测试 ---"

BENCHMARK_LOG="$PROJECT_DIR/benchmark_history.json"

# 运行快速基准测试
BENCHMARK_OUTPUT=$($PYTHON quick_benchmark.py 2>&1 || true)

# 提取关键指标
AVG_SEARCH_TIME=$(echo "$BENCHMARK_OUTPUT" | grep -oE '[0-9]+ms' | head -1 | tr -d 'ms' || echo "0")
SEARCH_SUCCESS_RATE=$(echo "$BENCHMARK_OUTPUT" | grep -oE '✅|❌' | grep -c "✅" || echo "0")

# 与历史对比
if [ -f "$BENCHMARK_LOG" ]; then
    LAST_AVG=$(tail -1 "$BENCHMARK_LOG" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('avg_search_time',0))" 2>/dev/null || echo "0")
    
    if [ "$LAST_AVG" != "0" ] && [ "$AVG_SEARCH_TIME" != "0" ]; then
        CHANGE=$(python3 -c "print(round(($AVG_SEARCH_TIME - $LAST_AVG) / $LAST_AVG * 100, 1))" 2>/dev/null || echo "0")
        if (( $(echo "$CHANGE > 10" | bc -l 2>/dev/null || echo "0") )); then
            PERF_REGRESSION="⚠️ 性能下降 ${CHANGE}%"
            warn "$PERF_REGRESSION (上次: ${LAST_AVG}ms, 本次: ${AVG_SEARCH_TIME}ms)"
            CHANGES_MADE="yes"  # 可能需要回滚或优化
        else
            success "性能稳定 (变化: ${CHANGE}%)"
        fi
    fi
fi

# 记录本次结果
RESULT_JSON=$(python3 -c "
import json, datetime
entry = {
    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'avg_search_time_ms': $AVG_SEARCH_TIME,
    'search_success_count': $SEARCH_SUCCESS_RATE,
    'exit_code': 0
}
print(json.dumps(entry))
" 2>/dev/null || echo "{}")

if [ -f "$BENCHMARK_LOG" ]; then
    # 追加到历史（保留最近30条）
    tail -29 "$BENCHMARK_LOG" > /tmp/bm_temp.json || true
    echo "$RESULT_JSON" >> /tmp/bm_temp.json
    mv /tmp/bm_temp.json "$BENCHMARK_LOG"
else
    echo "[$RESULT_JSON]" > "$BENCHMARK_LOG"
fi

success "基准测试完成 - 平均搜索时间: ${AVG_SEARCH_TIME}ms"

#-------------------------------------------------------------------------------
# Step 5: 检查 Git 状态
#-------------------------------------------------------------------------------
log ""
log "--- Step 5: Git 状态检查 ---"

cd "$PROJECT_DIR"
git fetch origin 2>/dev/null || true

# 检查是否有未提交的改动
if git diff --quiet 2>/dev/null && [ -z "$CHANGES_MADE" ]; then
    report "无代码改动，跳过提交"
else
    log "发现代码改动，准备提交..."
    CHANGES_MADE="yes"
fi

#-------------------------------------------------------------------------------
# Step 6: 自动生成 CHANGELOG
#-------------------------------------------------------------------------------
if [ -n "$CHANGES_MADE" ] || [ -n "$DEPS_UPDATED" ]; then
    log ""
    log "--- Step 6: 更新 CHANGELOG ---"
    
    # 获取上次 tag 之后的 commit
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -n "$LAST_TAG" ]; then
        COMMITS=$(git log "$LAST_TAG"..HEAD --oneline 2>/dev/null | wc -l)
        if [ "$COMMITS" -gt 0 ]; then
            # 生成 changelog 条目
            CHANGELOG_ENTRY="## [Unreleased] - $(date '+%Y-%m-%d')

### 自动化改进
- 🆕 自动改进循环执行"
            
            [ -n "$DEPS_UPDATED" ] && CHANGELOG_ENTRY="$CHANGELOG_ENTRY"$'\n'"- $DEPS_UPDATED"
            [ -n "$TEST_FAILED" ] && CHANGELOG_ENTRY="$CHANGELOG_ENTRY"$'\n'"- $TEST_FAILED"
            [ -n "$PERF_REGRESSION" ] && CHANGELOG_ENTRY="$CHANGELOG_ENTRY"$'\n'"- $PERF_REGRESSION"
            [ -z "$DEPS_UPDATED" ] && [ -z "$TEST_FAILED" ] && [ -z "$PERF_REGRESSION" ] && CHANGELOG_ENTRY="$CHANGELOG_ENTRY"$'\n'"- ✅ 日常维护，所有检查通过"
            
            # 追加到 CHANGELOG.md
            {
                echo ""
                echo "$CHANGELOG_ENTRY"
            } >> "$PROJECT_DIR/CHANGELOG.md"
            
            CHANGELOG_UPDATED="✅ CHANGELOG 已更新 ($COMMITS commits since $LAST_TAG)"
            success "$CHANGELOG_UPDATED"
        fi
    fi
fi

#-------------------------------------------------------------------------------
# Step 7: Git commit + tag
#-------------------------------------------------------------------------------
if [ -n "$CHANGES_MADE" ]; then
    log ""
    log "--- Step 7: Git 提交 ---"
    
    # 添加所有改动
    git add -A 2>/dev/null
    
    # 检查是否有实际的改动
    if git diff --cached --quiet 2>/dev/null; then
        report "无有效改动需要提交"
    else
        # 生成 commit message
        COMMIT_MSG="🤖 自动改进 - $(date '+%Y-%m-%d %H:%M')"
        
        [ -n "$DEPS_UPDATED" ] && COMMIT_MSG="$COMMIT_MSG"$'\n\n'"- $DEPS_UPDATED"
        [ -n "$TEST_FAILED" ] && COMMIT_MSG="$COMMIT_MSG"$'\n'"- $TEST_FAILED"
        [ -n "$PERF_REGRESSION" ] && COMMIT_MSG="$COMMIT_MSG"$'\n'"- $PERF_REGRESSION"
        [ -z "$DEPS_UPDATED" ] && [ -z "$TEST_FAILED" ] && [ -z "$PERF_REGRESSION" ] && COMMIT_MSG="$COMMIT_MSG"$'\n\n'"- ✅ 日常维护"
        
        # Commit
        git commit -m "$COMMIT_MSG" 2>&1 >> "$LOG_FILE" || warn "Git commit 失败"
        
        # 创建 tag
        NEW_TAG="v1.5.0-auto-$(date '+%Y%m%d')"
        git tag -a "$NEW_TAG" -m "自动改进 $(date '+%Y-%m-%d %H:%M')" 2>&1 >> "$LOG_FILE" || warn "Git tag 失败"
        
        success "已提交并打标签: $NEW_TAG"
        
        # 推送到远程
        git push origin main 2>&1 >> "$LOG_FILE" || warn "git push 失败"
        git push origin "$NEW_TAG" 2>&1 >> "$LOG_FILE" || warn "git push tag 失败"
        
        CHANGES_MADE="✅ 已提交: $NEW_TAG"
    fi
fi

#-------------------------------------------------------------------------------
# 生成报告
#-------------------------------------------------------------------------------
log ""
log "=========================================="
log "改进循环完成"
log "时间: $(date '+%Y-%m-%d %H:%M:%S')"
log "=========================================="

REPORT_SUMMARY="
🌙 heventure-search-mcp 自动改进报告
==========================================
时间: $TIMESTAMP

📦 依赖状态:    $([ -n "$DEPS_UPDATED" ] && echo "$DEPS_UPDATED" || echo "✅ 已是最新")
🔍 代码质量:    $([ -n "$RUFF_OUTPUT" ] && echo "已自动修复" || echo "✅ 通过")
🧪 测试状态:    $([ -n "$TEST_FAILED" ] && echo "$TEST_FAILED" || echo "✅ 通过")
⚡ 性能状态:    $([ -n "$PERF_REGRESSION" ] && echo "$PERF_REGRESSION" || echo "✅ 稳定")
📝 CHANGELOG:  $([ -n "$CHANGELOG_UPDATED" ] && echo "$CHANGELOG_UPDATED" || echo "无更新")
🐙 Git:        $([ -n "$CHANGES_MADE" ] && echo "$CHANGES_MADE" || echo "无改动")
==========================================
详细日志: $LOG_FILE
"

echo "$REPORT_SUMMARY"

# 保存报告
echo "$REPORT_SUMMARY" >> "$LOG_FILE"
echo "$REPORT_SUMMARY" > "$PROJECT_DIR/latest_improve_report.txt"

exit 0
