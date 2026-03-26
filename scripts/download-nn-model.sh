#!/usr/bin/env bash
#
# Download the neural premise selector ONNX model from the index-merged
# GitHub Release into the data directory.
#
# Usage:
#   ./scripts/download-nn-model.sh [--output-dir DIR] [--force]
#
# Prerequisites: gh (authenticated)

set -euo pipefail

OUTPUT_DIR="/data"
FORCE=false
TAG="index-merged"
ASSET_NAME="neural-premise-selector.onnx"

usage() {
    echo "Usage: $(basename "$0") [--output-dir DIR] [--force]"
    echo
    echo "Download ${ASSET_NAME} from the ${TAG} GitHub Release."
    echo
    echo "Options:"
    echo "  --output-dir DIR   Destination directory (default: /data)"
    echo "  --force            Overwrite existing model file"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output-dir)
            if [[ $# -lt 2 ]]; then
                echo "Error: --output-dir requires a path argument." >&2
                usage
            fi
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help|-h)
            usage
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            ;;
    esac
done

# --- Validate prerequisites ---

if ! command -v gh &>/dev/null; then
    echo "Error: gh not found." >&2
    exit 1
fi

if ! gh auth status &>/dev/null; then
    echo "Error: gh not authenticated. Run 'gh auth login' first." >&2
    exit 1
fi

# --- Check existing file ---

dest="${OUTPUT_DIR}/${ASSET_NAME}"

if [[ -f "$dest" && "$FORCE" != true ]]; then
    echo "Error: ${dest} already exists. Use --force to overwrite." >&2
    exit 1
fi

# --- Verify release exists ---

if ! gh release view "$TAG" &>/dev/null; then
    echo "Error: no ${TAG} release found." >&2
    exit 1
fi

# --- Download ---

mkdir -p "$OUTPUT_DIR"

echo "Downloading ${ASSET_NAME} from release ${TAG}..."
if ! gh release download "$TAG" -p "$ASSET_NAME" -D "$OUTPUT_DIR" --clobber; then
    echo "Error: failed to download ${ASSET_NAME}. The release may not include a model." >&2
    exit 1
fi

size=$(du -h "$dest" | cut -f1)
echo "Done: ${dest} (${size})"
