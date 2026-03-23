#!/usr/bin/env bash
set -euo pipefail

# Quick-test the indexing and extraction pipelines.
#
# Usage:
#   ./scripts/quick-test-pipeline.sh                                    # all libraries, smoke tier
#   ./scripts/quick-test-pipeline.sh --tier debug                       # all libraries, debug tier
#   ./scripts/quick-test-pipeline.sh --libraries coquelicot             # full coquelicot
#   ./scripts/quick-test-pipeline.sh --libraries flocq,coquelicot       # full flocq + coquelicot
#   ./scripts/quick-test-pipeline.sh --libraries flocq --tier smoke     # flocq, ~4 files
#   ./scripts/quick-test-pipeline.sh --index-only                       # index only
#   ./scripts/quick-test-pipeline.sh --extract-only                     # extract only (needs prior index)

export ROCQLIB="${ROCQLIB:-${COQLIB:-}}"

ALL_LIBRARIES="stdlib,mathcomp,stdpp,flocq,coquelicot,coqinterval"
LIBRARIES=""
TIER=""
OUTPUT_DIR="/data/quick-test"
INDEX_ONLY=false
EXTRACT_ONLY=false
WATCHDOG_TIMEOUT=120

usage() {
    echo "Usage: $(basename "$0") [--libraries lib1,lib2,...] [--tier smoke|debug]" >&2
    echo "                        [--output-dir DIR] [--index-only] [--extract-only]" >&2
    echo "" >&2
    echo "Run indexing and extraction for fast pipeline testing." >&2
    echo "" >&2
    echo "Libraries (default: all 6):" >&2
    echo "  stdlib, mathcomp, stdpp, flocq, coquelicot, coqinterval" >&2
    echo "" >&2
    echo "Tiers (pick a small subdirectory per library, default: smoke):" >&2
    echo "  smoke   ~4 .vo files   (~30 seconds per library)" >&2
    echo "  debug   ~14 .vo files  (~1-2 minutes per library)" >&2
    echo "" >&2
    echo "Options:" >&2
    echo "  --libraries     Comma-separated list of libraries (default: all 6)" >&2
    echo "  --tier          Limit scope per library (default: smoke). Omit for full." >&2
    echo "  --output-dir    Output directory (default: /data/quick-test)" >&2
    echo "  --index-only    Run only the indexing phase" >&2
    echo "  --extract-only  Run only the extraction phase (requires prior index)" >&2
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --tier)
            TIER="$2"
            shift 2
            ;;
        --libraries)
            LIBRARIES="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --index-only)
            INDEX_ONLY=true
            shift
            ;;
        --extract-only)
            EXTRACT_ONLY=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            ;;
    esac
done

# --- Defaults ---
# No args → all libraries, smoke tier.  --libraries alone → full libraries.

if [[ -z "$LIBRARIES" && -z "$TIER" ]]; then
    LIBRARIES="$ALL_LIBRARIES"
    TIER="smoke"
elif [[ -z "$LIBRARIES" ]]; then
    LIBRARIES="$ALL_LIBRARIES"
fi

# --- Resolve Coq library path ---

COQ_LIB="$(coqc -where 2>/dev/null)"

# --- Library contrib directory and module prefix mappings ---
# (mirrors _LIBRARY_CONTRIB_DIRS and module conventions in pipeline.py)

declare -A LIB_CONTRIB_DIRS=(
    [mathcomp]=mathcomp
    [stdpp]=stdpp
    [flocq]=Flocq
    [coquelicot]=Coquelicot
    [coqinterval]=Interval
)

declare -A LIB_MODULE_PREFIXES=(
    [stdlib]="Coq."
    [mathcomp]="mathcomp."
    [stdpp]="stdpp."
    [flocq]="Flocq."
    [coquelicot]="Coquelicot."
    [coqinterval]="Interval."
)

# --- Tier file limits ---

declare -A TIER_LIMITS=(
    [smoke]=4
    [debug]=14
)

if [[ -n "$TIER" && -z "${TIER_LIMITS[$TIER]+x}" ]]; then
    echo "Unknown tier: $TIER (expected smoke or debug)" >&2
    exit 1
fi

# --- Resolve project directory for a library ---

resolve_project_dir() {
    local lib="$1"
    if [[ "$lib" == "stdlib" ]]; then
        local root="${COQ_LIB}/user-contrib/Stdlib"
        if [[ ! -d "$root" ]]; then
            root="${COQ_LIB}/theories"
        fi
        echo "$root"
    else
        echo "${COQ_LIB}/user-contrib/${LIB_CONTRIB_DIRS[$lib]}"
    fi
}

# --- Find a subdirectory with at most N .vo files for tier-limited indexing ---
# The subdirectory must be within the real Coq lib tree so that the backend's
# _vo_to_canonical_module path heuristic (which looks for user-contrib/ or
# theories/ markers) works correctly.

find_tier_target() {
    local project_dir="$1" tier_limit="$2"

    local best_dir="" best_count=0
    while IFS= read -r subdir; do
        local count
        count=$(find "$subdir" -name "*.vo" | wc -l)
        if [[ $count -le $tier_limit && $count -gt $best_count ]]; then
            best_dir="$subdir"
            best_count=$count
        fi
    done < <(find "$project_dir" -mindepth 1 -maxdepth 1 -type d 2>/dev/null)

    # Fall back to full directory for flat libraries (e.g. stdpp, coquelicot)
    if [[ -n "$best_dir" ]]; then
        echo "$best_dir"
    else
        echo "$project_dir"
    fi
}

# --- Parse library list ---

IFS=',' read -ra LIB_ARRAY <<< "$LIBRARIES"

for lib in "${LIB_ARRAY[@]}"; do
    if [[ -z "${LIB_MODULE_PREFIXES[$lib]+x}" ]]; then
        echo "Unknown library: $lib" >&2
        echo "Valid libraries: ${ALL_LIBRARIES//,/, }" >&2
        exit 1
    fi
done

mkdir -p "$OUTPUT_DIR"

if [[ -n "$TIER" ]]; then
    echo "Quick test pipeline — ${#LIB_ARRAY[@]} libraries, ${TIER} tier"
else
    echo "Quick test pipeline — ${#LIB_ARRAY[@]} libraries, full"
fi
echo "  Libraries:  ${LIBRARIES}"
echo "  Output dir: ${OUTPUT_DIR}"
echo ""

OVERALL_START=$(date +%s)

# --- Per-library loop ---

declare -A RESULTS

for lib in "${LIB_ARRAY[@]}"; do
    MODULE_PREFIX="${LIB_MODULE_PREFIXES[$lib]}"
    PROJECT_DIR="$(resolve_project_dir "$lib")"

    if [[ ! -d "$PROJECT_DIR" ]]; then
        echo "WARNING: ${lib} not found at ${PROJECT_DIR}, skipping" >&2
        RESULTS[$lib]="skipped"
        continue
    fi

    # Determine index target
    if [[ -n "$TIER" ]]; then
        TIER_LIMIT="${TIER_LIMITS[$TIER]}"
        INDEX_TARGET="$(find_tier_target "$PROJECT_DIR" "$TIER_LIMIT")"
        DB_SUFFIX="${lib}-${TIER}"
    else
        # Full library: use library name so pipeline applies library-specific logic
        INDEX_TARGET="$lib"
        DB_SUFFIX="$lib"
    fi

    VO_COUNT=$(find "$INDEX_TARGET" -name "*.vo" 2>/dev/null | wc -l)
    DB_PATH="${OUTPUT_DIR}/index-${DB_SUFFIX}.db"
    JSONL_PATH="${OUTPUT_DIR}/${DB_SUFFIX}.jsonl"

    echo "=== ${lib} (${VO_COUNT} .vo files) ==="
    if [[ -n "$TIER" ]]; then
        echo "  Index target: ${INDEX_TARGET}"
    fi

    # --- Indexing phase ---

    if [[ "$EXTRACT_ONLY" != true ]]; then
        echo "--- Indexing ---" >&2
        rm -f "$DB_PATH"
        INDEX_START=$(date +%s)

        if ! python -m Poule.extraction --target "$INDEX_TARGET" --db "$DB_PATH" --progress; then
            echo "  ERROR: Indexing failed for ${lib}" >&2
            RESULTS[$lib]="FAILED (index)"
            continue
        fi

        INDEX_END=$(date +%s)
        DECL_COUNT=$(sqlite3 "$DB_PATH" "SELECT value FROM index_meta WHERE key = 'declarations'" 2>/dev/null || echo "?")
        echo "  Indexed ${DECL_COUNT} declarations in $((INDEX_END - INDEX_START))s"
        echo ""
    fi

    # --- Extraction phase ---

    if [[ "$INDEX_ONLY" != true ]]; then
        if [[ ! -f "$DB_PATH" ]]; then
            echo "  ERROR: Index database not found at ${DB_PATH}" >&2
            echo "  Run without --extract-only first." >&2
            RESULTS[$lib]="FAILED (no index)"
            continue
        fi

        echo "--- Extraction ---" >&2
        rm -f "$JSONL_PATH"
        EXTRACT_START=$(date +%s)

        if ! poule extract "$PROJECT_DIR" \
            --output "$JSONL_PATH" \
            --index-db "$DB_PATH" \
            --module-prefix "$MODULE_PREFIX" \
            --watchdog-timeout "$WATCHDOG_TIMEOUT"; then
            echo "  ERROR: Extraction failed for ${lib}" >&2
            RESULTS[$lib]="FAILED (extract)"
            continue
        fi

        EXTRACT_END=$(date +%s)
        echo "  Extraction completed in $((EXTRACT_END - EXTRACT_START))s"
        echo ""
    fi

    RESULTS[$lib]="ok"
done

# --- Summary ---

OVERALL_END=$(date +%s)
OVERALL_ELAPSED=$((OVERALL_END - OVERALL_START))

echo "=== Summary ==="
echo "  Total time: ${OVERALL_ELAPSED}s"
echo ""

for lib in "${LIB_ARRAY[@]}"; do
    DB_SUFFIX="${lib}"
    [[ -n "$TIER" ]] && DB_SUFFIX="${lib}-${TIER}"
    DB_PATH="${OUTPUT_DIR}/index-${DB_SUFFIX}.db"
    JSONL_PATH="${OUTPUT_DIR}/${DB_SUFFIX}.jsonl"

    STATUS="${RESULTS[$lib]:-unknown}"

    if [[ "$STATUS" != "ok" ]]; then
        printf "  %-15s %s\n" "$lib" "$STATUS"
        continue
    fi

    DETAILS=""
    if [[ -f "$DB_PATH" ]]; then
        DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
        DECL_COUNT=$(sqlite3 "$DB_PATH" "SELECT value FROM index_meta WHERE key = 'declarations'" 2>/dev/null || echo "?")
        DETAILS="index: ${DB_SIZE}, ${DECL_COUNT} decls"
    fi

    if [[ -f "$JSONL_PATH" ]]; then
        JSONL_SIZE=$(du -h "$JSONL_PATH" | cut -f1)
        PROOF_COUNTS=$(tail -1 "$JSONL_PATH" 2>/dev/null | python3 -c "
import json, sys
try:
    s = json.loads(sys.stdin.readline())
    if s.get('record_type') == 'extraction_summary':
        print(f\"{s['total_extracted']} extracted, {s['total_failed']} failed\")
except Exception:
    pass
" 2>/dev/null || true)
        [[ -n "$DETAILS" ]] && DETAILS="${DETAILS}; "
        DETAILS="${DETAILS}output: ${JSONL_SIZE}${PROOF_COUNTS:+, ${PROOF_COUNTS}}"
    fi

    printf "  %-15s %s\n" "$lib" "${DETAILS:-ok}"
done

# Exit non-zero if any library failed
for lib in "${LIB_ARRAY[@]}"; do
    if [[ "${RESULTS[$lib]}" == FAILED* ]]; then
        exit 1
    fi
done
