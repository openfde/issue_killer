#!/bin/bash
set -uo pipefail

TREE="$1"
PROJECT="$2"
TARGET="$3"
MODULE="$4"
JOBS="$5"
PATCH="$6"
ARTIFACT_REL="$7"
PRODUCT="$8"
LOG="$9"
EXIT_FILE="${10}"

cd "$TREE" || { echo "tree not found: $TREE"; echo 2 > "$EXIT_FILE"; exit 2; }

branch=$(git -C "$PROJECT" branch --show-current 2>/dev/null)
head=$(git -C "$PROJECT" rev-parse HEAD 2>/dev/null)
dirty=$(git -C "$PROJECT" status --porcelain 2>/dev/null)
echo "branch=$branch"
echo "head=$head"
echo "dirty_lines=$(printf '%s' "$dirty" | wc -l)"
if [ -n "$dirty" ]; then
    echo "dirty worktree"
    echo 7 > "$EXIT_FILE"
    exit 7
fi

APPLIED=0
cleanup() {
    if [ "$APPLIED" = "1" ] && [ -n "$PATCH" ]; then
        git -C "$PROJECT" apply -R "$PATCH" || true
    fi
}
trap cleanup EXIT

if [ -n "$PATCH" ]; then
    if git -C "$PROJECT" apply --reverse --check "$PATCH" >/dev/null 2>&1; then
        echo "patch already applied; building current branch"
    else
        git -C "$PROJECT" apply --check "$PATCH" || { echo "patch does not apply"; echo 11 > "$EXIT_FILE"; exit 11; }
        git -C "$PROJECT" apply "$PATCH" || { echo "patch apply failed"; echo 12 > "$EXIT_FILE"; exit 12; }
        APPLIED=1
        echo "patch applied temporarily"
    fi
fi

source build/envsetup.sh
lunch "$TARGET" || { echo 4 > "$EXIT_FILE"; exit 4; }
make "$MODULE" -j"$JOBS"
rc=$?
if [ "$rc" -ne 0 ]; then
    echo "make failed: $rc"
    echo "$rc" > "$EXIT_FILE"
    exit "$rc"
fi

ARTIFACT="$TREE/out/target/product/$PRODUCT/$ARTIFACT_REL"
if [ ! -f "$ARTIFACT" ]; then
    echo "artifact missing: $ARTIFACT"
    echo 13 > "$EXIT_FILE"
    exit 13
fi

sha256sum "$ARTIFACT"
echo "artifact=$ARTIFACT"
echo 0 > "$EXIT_FILE"
