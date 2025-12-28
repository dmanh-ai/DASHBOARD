#!/bin/bash
# ===================================================================
# AUTO DAILY UPDATE - Full Automation for Market Overview Dashboard
# ===================================================================
# Workflow:
# 1. Detect new .docx file in reports/word/
# 2. Parse to JavaScript
# 3. Validate output
# 4. Backup old data
# 5. Update full_data.js
# 6. Git commit & push
# 7. Deploy to GitHub Pages
# ===================================================================

set -e  # Exit on error

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WORKSPACE_ROOT="$(cd "$PROJECT_ROOT/.." && pwd)"
WORD_DIR="$PROJECT_ROOT/reports/word"
TXT_DIR="$PROJECT_ROOT/reports/txt"
DATA_DIR="$PROJECT_ROOT"
BACKUP_DIR="$PROJECT_ROOT/archive/data"
STATE_FILE="$PROJECT_ROOT/.last_parsed_doc"

# Input source
# - market (default): pull report from workspace `outputs/market/reports` (strict match `MARKET_REPORT_GLOB`, pick latest timestamp of latest day)
# - local: use files in `UI GLM/reports/word/` (manual copy)
WORD_SOURCE_MODE="${WORD_SOURCE_MODE:-market}"
MARKET_REPORTS_DIR="${MARKET_REPORTS_DIR:-$WORKSPACE_ROOT/outputs/market/reports}"
MARKET_REPORT_GLOB="${MARKET_REPORT_GLOB:-BaoCao_*.docx}"

# Files
MAIN_DATA_FILE="$DATA_DIR/full_data.js"
META_DATA_FILE="$DATA_DIR/ui_glm_meta.js"
META_JSON_FILE="$DATA_DIR/ui_glm_meta.json"
LOG_FILE="$PROJECT_ROOT/automation.log"

# Git config
GIT_EMAIL="automation@dashboard.local"
GIT_NAME="Dashboard Automation"

# ============================================================================
# LOGGING FUNCTIONS
# ============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    log "❌ ERROR: $*"
    exit 1
}

success() {
    log "✅ SUCCESS: $*"
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

file_hash() {
    local file="$1"
    if command -v md5 >/dev/null 2>&1; then
        md5 -q "$file" 2>/dev/null || echo "unknown"
        return 0
    fi
    if command -v md5sum >/dev/null 2>&1; then
        md5sum "$file" 2>/dev/null | awk '{print $1}' || echo "unknown"
        return 0
    fi
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" 2>/dev/null | awk '{print $1}' || echo "unknown"
        return 0
    fi
    echo "unknown"
}

file_size_bytes() {
    local file="$1"
    if stat -f%z "$file" >/dev/null 2>&1; then
        stat -f%z "$file"
        return 0
    fi
    if stat -c%s "$file" >/dev/null 2>&1; then
        stat -c%s "$file"
        return 0
    fi
    wc -c <"$file" 2>/dev/null | tr -d ' ' || echo "0"
}

get_latest_docx() {
    # Find latest .docx file (excluding temp files starting with ~$)
    find "$WORD_DIR" -name "*.docx" -not -name "~*" -type f -print0 \
        | xargs -0 ls -t \
        | head -1
}

get_latest_daily_market_docx() {
    if [[ ! -d "$MARKET_REPORTS_DIR" ]]; then
        return 0
    fi

    local latest_date=""
    local best_file=""
    local find_pattern="$MARKET_REPORT_GLOB"

    # Strict rule: only ingest files matching MARKET_REPORT_GLOB (default: BaoCao_*.docx).
    # Choose the latest day (YYYYMMDD) and the latest timestamp (YYYYMMDD_HHMMSS).
    while IFS= read -r -d '' file; do
        local file_date stamp
        file_date="$(get_file_date "$file")"
        stamp="$(get_file_stamp_key "$file")"
        [[ -z "$file_date" || -z "$stamp" ]] && continue

        if [[ -z "$latest_date" || "$file_date" > "$latest_date" ]]; then
            latest_date="$file_date"
        fi
    done < <(find "$MARKET_REPORTS_DIR" -name "$find_pattern" -not -name "~*" -type f -print0 2>/dev/null)

    [[ -z "$latest_date" ]] && return 0

    while IFS= read -r -d '' file; do
        local file_date stamp best_stamp
        file_date="$(get_file_date "$file")"
        stamp="$(get_file_stamp_key "$file")"
        [[ "$file_date" != "$latest_date" ]] && continue
        [[ -z "$stamp" ]] && continue

        if [[ -z "$best_file" ]]; then
            best_file="$file"
            continue
        fi

        best_stamp="$(get_file_stamp_key "$best_file")"
        if [[ -n "$best_stamp" && "$stamp" > "$best_stamp" ]]; then
            best_file="$file"
        fi
    done < <(find "$MARKET_REPORTS_DIR" -name "$find_pattern" -not -name "~*" -type f -print0 2>/dev/null)

    [[ -n "$best_file" ]] && echo "$best_file"
    return 0
}

stage_market_docx_to_word_dir() {
    local market_docx="$1"
    mkdir -p "$WORD_DIR"

    local dest="$WORD_DIR/$(basename "$market_docx")"
    if [[ -f "$dest" ]]; then
        local src_hash dest_hash
        src_hash="$(file_hash "$market_docx")"
        dest_hash="$(file_hash "$dest")"
        if [[ "$src_hash" != "unknown" && "$src_hash" == "$dest_hash" ]]; then
            echo "$dest"
            return 0
        fi
    fi

    cp "$market_docx" "$dest"
    echo "$dest"
}

get_file_date() {
    local file="$1"
    # Extract date from filename like BaoCao_20251225_175640.docx
    basename "$file" | grep -oE '[0-9]{8}' | head -1
}

get_file_stamp_key() {
    local file="$1"
    # Extract stamp key from filename like BaoCao_20251225_175640.docx
    basename "$file" | grep -oE '[0-9]{8}_[0-9]{6}' | head -1
}

get_file_timestamp() {
    local file="$1"
    # Extract timestamp from filename
    basename "$file" | grep -oE '[0-9]{8}_[0-9]{6}' | head -1 | tr '_' ' '
}

is_already_parsed() {
    local docx_file="$1"
    local current_hash
    current_hash="$(file_hash "$docx_file")"

    if [[ -f "$STATE_FILE" ]]; then
        local last_hash=$(cat "$STATE_FILE" 2>/dev/null || echo "")
        if [[ "$current_hash" == "$last_hash" ]]; then
            return 0  # Already parsed
        fi
    fi
    return 1  # Not parsed yet
}

mark_as_parsed() {
    local docx_file="$1"
    local hash
    hash="$(file_hash "$docx_file")"
    echo "$hash" > "$STATE_FILE"
    log "📝 Marked as parsed: $(basename "$docx_file")"
}

# ============================================================================
# STEP 1: DETECT NEW FILE
# ============================================================================

step1_detect_new_file() {
    log "🔍 Step 1: Detecting new .docx file..."

    local latest_docx=""
    if [[ "$WORD_SOURCE_MODE" == "market" ]]; then
        local market_docx
        market_docx="$(get_latest_daily_market_docx)"
        if [[ -z "$market_docx" ]]; then
            log "⚠️  No matching .docx found in market reports dir: $MARKET_REPORTS_DIR"
            log "ℹ️  Expected pattern: $MARKET_REPORT_GLOB (default BaoCao_YYYYMMDD_HHMMSS.docx)"
            return 1
        fi
        latest_docx="$(stage_market_docx_to_word_dir "$market_docx")"
        log "📥 Pulled from market: $(basename "$market_docx") (staged at $(basename "$latest_docx"))"
    elif [[ "$WORD_SOURCE_MODE" == "local" ]]; then
        latest_docx="$(get_latest_docx)"
    else
        error "Invalid WORD_SOURCE_MODE=$WORD_SOURCE_MODE (expected: market|local)"
    fi

    if [[ -z "$latest_docx" ]]; then
        log "⚠️  No .docx files found in $WORD_DIR"
        return 1
    fi

    if is_already_parsed "$latest_docx"; then
        log "ℹ️  Latest file already processed: $(basename "$latest_docx")"
        return 1
    fi

    LATEST_DOCX="$latest_docx"
    log "📄 Found new file: $(basename "$LATEST_DOCX")"

    return 0
}

# ============================================================================
# STEP 2: CONVERT DOCX TO TXT
# ============================================================================

step2_convert_to_txt() {
    local docx_file="$1"
    local basename=$(basename "$docx_file" .docx)
    local txt_file="$TXT_DIR/${basename}.txt"

    log "🔄 Step 2: Converting to .txt..."

    if textutil -convert txt -stdout "$docx_file" > "$txt_file"; then
        log "✅ Converted: $txt_file"
        LATEST_TXT="$txt_file"
        return 0
    else
        error "Failed to convert $docx_file"
    fi
}

# ============================================================================
# STEP 3: PARSE TO JAVASCRIPT
# ============================================================================

step3_parse() {
    local txt_file="$1"
    local basename=$(basename "$txt_file" .txt)
    local js_file="$DATA_DIR/full_data_${basename}.js"

    log "🔄 Step 3: Parsing to JavaScript..."

    if python3 "$SCRIPT_DIR/auto_parse.py" "$txt_file" "$js_file"; then
        log "✅ Parsed: $js_file"
        LATEST_JS="$js_file"
        return 0
    else
        error "Failed to parse $txt_file"
    fi
}

# ============================================================================
# STEP 4: VALIDATE OUTPUT
# ============================================================================

step4_validate() {
    local js_file="$1"

    log "🔄 Step 4: Validating JavaScript..."

    if node --check "$js_file"; then
        log "✅ JavaScript syntax valid"

        # Extract stats (strict: must contain all 16 expected keys)
        local indices_count validator_out
        if ! validator_out="$(
            python3 - "$js_file" 2>>"$LOG_FILE" <<'PY'
import re
import sys

js_file = sys.argv[1]
content = open(js_file, "r", encoding="utf-8", errors="replace").read()

expected = [
    "overview",
    "vnindex",
    "vn30",
    "vn100",
    "vnmidcap",
    "vnreal",
    "vnit",
    "vnheal",
    "vnfin",
    "vnene",
    "vncons",
    "vnmat",
    "vncond",
    "vnsml",
    "vnfinselect",
    "vndiamond",
]

keys = set(re.findall(r"^ {4}([a-z0-9_]+):[ \t]*[{]", content, flags=re.M))
missing = [k for k in expected if k not in keys]

print(len(keys))
if missing:
    print("MISSING_KEYS=" + ",".join(missing), file=sys.stderr)
    sys.exit(2)
PY
        )"; then
            error "Validation failed: missing expected keys in FULL_DATA (see $LOG_FILE)"
        fi

        indices_count="$(echo "$validator_out" | head -n 1 | tr -d '[:space:]')"

        log "📊 Stats: ${indices_count} indices"
        if [[ "$indices_count" == "16" ]]; then
            log "✅ Validation passed (16/16 indices)"
            return 0
        fi

        error "Validation failed: expected 16 indices, got ${indices_count}"
    else
        error "JavaScript syntax validation failed"
    fi
}

# ============================================================================
# STEP 5: BACKUP OLD DATA
# ============================================================================

step5_backup() {
    local new_js_file="$1"
    local file_date=$(get_file_date "$LATEST_DOCX")

    log "🔄 Step 5: Backing up old data..."

    # Create backup dir if not exists
    mkdir -p "$BACKUP_DIR"

    # Backup current full_data.js if exists
    if [[ -f "$MAIN_DATA_FILE" ]]; then
        local backup_file="$BACKUP_DIR/full_data_${file_date}.js"
        cp "$MAIN_DATA_FILE" "$backup_file"
        log "✅ Backed up to: $backup_file"
    else
        log "ℹ️  No existing full_data.js to backup"
    fi

    return 0
}

# ============================================================================
# STEP 6: UPDATE MAIN DATA FILE
# ============================================================================

step6_update_main() {
    local new_js_file="$1"

    log "🔄 Step 6: Updating $MAIN_DATA_FILE..."

    if cp "$new_js_file" "$MAIN_DATA_FILE"; then
        log "✅ Updated: $MAIN_DATA_FILE"

        # Show preview
        local date_info=$(get_file_timestamp "$LATEST_DOCX")
        log "📅 Data date: $date_info"

        # Write small meta file so dashboard header reflects latest report timestamp.
        local stamp date_part time_part asof_iso human_date human_updated_at
        stamp="$(get_file_stamp_key "$LATEST_DOCX")"
        date_part="${stamp%_*}"
        time_part="${stamp#*_}"
        asof_iso="${date_part:0:4}-${date_part:4:2}-${date_part:6:2}"
        human_date="${date_part:6:2}/${date_part:4:2}/${date_part:0:4}"
        human_updated_at="${human_date} ${time_part:0:2}:${time_part:2:2}"

        cat >"$META_DATA_FILE" <<EOF
// AUTO-GENERATED by UI GLM/tools/auto_daily_update.sh
window.UI_GLM_REPORT_META = {
  stamp: "${stamp}",
  asof_iso: "${asof_iso}",
  human_date: "${human_date}",
  human_updated_at: "${human_updated_at}",
  source_docx: "$(basename "$LATEST_DOCX")"
};
EOF
        log "🧷 Wrote meta: $META_DATA_FILE"

        cat >"$META_JSON_FILE" <<EOF
{
  "stamp": "${stamp}",
  "asof_iso": "${asof_iso}",
  "human_date": "${human_date}",
  "human_updated_at": "${human_updated_at}",
  "source_docx": "$(basename "$LATEST_DOCX")"
}
EOF
        log "🧷 Wrote meta: $META_JSON_FILE"

        return 0
    else
        error "Failed to update $MAIN_DATA_FILE"
    fi
}

# ============================================================================
# STEP 6.5: EXPORT INDEX OHLCV (FROM MARKET DB)
# ============================================================================

step6_5_export_index_ohlcv() {
    log "🔄 Step 6.5: Exporting index OHLCV from market monthly DB..."

    local exporter="$SCRIPT_DIR/export_index_ohlcv_from_market_db.py"
    local db_path="$WORKSPACE_ROOT/market_cache/hose_monthly/latest.sqlite"
    local out_path="$DATA_DIR/index_ohlcv.js"

    if [[ ! -f "$exporter" ]]; then
        log "⚠️  Exporter missing: $exporter (skip)"
        return 0
    fi
    if [[ ! -f "$db_path" ]]; then
        log "⚠️  Market DB missing: $db_path (skip)"
        return 0
    fi

    if python3 "$exporter" --db "$db_path" --out "$out_path" >>"$LOG_FILE" 2>&1; then
        log "✅ Exported: $out_path"
        return 0
    fi

    log "⚠️  Export index OHLCV failed (continue). See $LOG_FILE"
    return 0
}

# ============================================================================
# STEP 7: GIT OPERATIONS
# ============================================================================

step7_git_commit() {
    log "🔄 Step 7: Git operations..."

    cd "$PROJECT_ROOT"

    # Check if git repo
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log "⚠️  Not a git repository, skipping git operations"
        return 0
    fi

    # Configure git if needed
    git config user.email "$GIT_EMAIL" 2>/dev/null || true
    git config user.name "$GIT_NAME" 2>/dev/null || true

    # Check for changes (data + meta + dashboard + OHLCV export)
    if git diff --quiet -- "$MAIN_DATA_FILE" "$META_DATA_FILE" "$META_JSON_FILE" "$DATA_DIR/DASHBOARD_V3.html" "$DATA_DIR/index_ohlcv.js"; then
        log "ℹ️  No changes to commit"
        return 0
    fi

    # Add files (full_data + meta; dashboard html may change occasionally)
    git add "$MAIN_DATA_FILE" "$META_DATA_FILE" "$META_JSON_FILE" "$DATA_DIR/DASHBOARD_V3.html" "$DATA_DIR/index_ohlcv.js" 2>/dev/null || true

    # Commit
    local file_date
    file_date="$(get_file_date "$LATEST_DOCX")"
    local commit_msg="🤖 Auto: Update market data for ${file_date}

📊 Source: $(basename "$LATEST_DOCX")
📅 Generated: $(date '+%Y-%m-%d %H:%M:%S')
✅ 16/16 indices parsed

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

    if git commit -m "$commit_msg"; then
        log "✅ Git commit successful"
        return 0
    else
        log "⚠️  Git commit failed (nothing to commit?)"
        return 0
    fi
}

step8_git_push() {
    log "🔄 Step 8: Pushing to remote..."

    cd "$PROJECT_ROOT"

    # Check if remote exists
    if ! git remote get-url origin > /dev/null 2>&1; then
        log "⚠️  No git remote, skipping push"
        return 0
    fi

    # Push
    if git push origin main; then
        log "✅ Pushed to remote"
        return 0
    else
        log "⚠️  Git push failed (check network/permissions)"
        return 1
    fi
}

# ============================================================================
# MAIN WORKFLOW
# ============================================================================

main() {
    log "═══════════════════════════════════════════════════════════════"
    log "🚀 AUTO DAILY UPDATE STARTED"
    log "═══════════════════════════════════════════════════════════════"

    # Step 1: Detect new file
    if ! step1_detect_new_file; then
        log "ℹ️  No new files to process"
        exit 0
    fi

    # Step 2: Convert to txt
    step2_convert_to_txt "$LATEST_DOCX"

    # Step 3: Parse
    step3_parse "$LATEST_TXT"

    # Step 4: Validate
    step4_validate "$LATEST_JS"

    # Step 5: Backup
    step5_backup "$LATEST_JS"

    # Step 6: Update main
    step6_update_main "$LATEST_JS"

    # Step 6.5: Export index OHLCV (market DB)
    step6_5_export_index_ohlcv

    # Step 7: Git commit
    step7_git_commit

    # Step 8: Git push (optional, may fail)
    step8_git_push || true

    # Mark as parsed
    mark_as_parsed "$LATEST_DOCX"

    # Done
    log "═══════════════════════════════════════════════════════════════"
    success "DAILY UPDATE COMPLETED!"
    log "📄 Source: $(basename "$LATEST_DOCX")"
    log "📊 Output: $MAIN_DATA_FILE"
    log "═══════════════════════════════════════════════════════════════"
}

# Run main
main "$@"
