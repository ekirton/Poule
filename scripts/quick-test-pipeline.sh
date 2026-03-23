#!/usr/bin/env bash
set -euo pipefail

# Quick-test the indexing and extraction pipelines.
#
# Usage:
#   ./scripts/quick-test-pipeline.sh                                    # all libraries, smoke (4 files each)
#   ./scripts/quick-test-pipeline.sh --tier debug                       # all libraries, debug (14 files each)
#   ./scripts/quick-test-pipeline.sh --libraries coquelicot             # full coquelicot
#   ./scripts/quick-test-pipeline.sh --libraries flocq,coquelicot       # full flocq + coquelicot
#   ./scripts/quick-test-pipeline.sh --libraries flocq --tier smoke     # flocq, 4 files
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
    echo "Tiers (limit .vo file count per library, default: smoke):" >&2
    echo "  smoke   4 .vo files   (~30 seconds per library)" >&2
    echo "  debug   14 .vo files  (~1-2 minutes per library)" >&2
    echo "" >&2
    echo "Options:" >&2
    echo "  --libraries     Comma-separated list of libraries (default: all 6)" >&2
    echo "  --tier          Limit to N .vo files per library (default: smoke). Omit for full." >&2
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
TIER_DIR=""

# Clean up temp dir on exit if created
cleanup() { [[ -n "$TIER_DIR" ]] && rm -rf "$TIER_DIR"; }
trap cleanup EXIT

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

    # Determine index target (full library or tier-limited temp dir)
    if [[ -n "$TIER" ]]; then
        TIER_LIMIT="${TIER_LIMITS[$TIER]}"
        TIER_DIR=$(mktemp -d)

        while IFS= read -r vo; do
            rel="${vo#"$PROJECT_DIR"/}"
            mkdir -p "$TIER_DIR/$(dirname "$rel")"
            ln -s "$vo" "$TIER_DIR/$rel"
        done < <(find "$PROJECT_DIR" -name "*.vo" | sort | head -n "$TIER_LIMIT")

        VO_COUNT=$(find "$TIER_DIR" -name "*.vo" | wc -l)
        INDEX_TARGET="$TIER_DIR"
        DB_SUFFIX="${lib}-${TIER}"
    else
        VO_COUNT=$(find "$PROJECT_DIR" -name "*.vo" | wc -l)
        INDEX_TARGET="$lib"
        DB_SUFFIX="$lib"
    fi

    DB_PATH="${OUTPUT_DIR}/index-${DB_SUFFIX}.db"
    JSONL_PATH="${OUTPUT_DIR}/${DB_SUFFIX}.jsonl"

    echo "=== ${lib} (${VO_COUNT} .vo files) ==="

    # --- Indexing phase ---

    if [[ "$EXTRACT_ONLY" != true ]]; then
        echo "--- Indexing ---" >&2
        rm -f "$DB_PATH"
        INDEX_START=$(date +%s)

        if ! python -m Poule.extraction --target "$INDEX_TARGET" --db "$DB_PATH" --progress; then
            echo "  ERROR: Indexing failed for ${lib}" >&2
            RESULTS[$lib]="FAILED (index)"
            [[ -n "$TIER" ]] && rm -rf "$TIER_DIR" && TIER_DIR=""
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
            [[ -n "$TIER" ]] && rm -rf "$TIER_DIR" && TIER_DIR=""
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
            [[ -n "$TIER" ]] && rm -rf "$TIER_DIR" && TIER_DIR=""
            continue
        fi

        EXTRACT_END=$(date +%s)
        echo "  Extraction completed in $((EXTRACT_END - EXTRACT_START))s"
        echo ""
    fi

    RESULTS[$lib]="ok"

    # Clean up tier temp dir between libraries
    if [[ -n "$TIER" ]]; then
        rm -rf "$TIER_DIR"
        TIER_DIR=""
    fi
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
