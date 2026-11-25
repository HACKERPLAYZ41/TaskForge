#!/bin/bash
mkdir -p /logs/verifier
REWARD_FILE="/logs/verifier/reward.txt"

# Default to 0 so reward file is always present even if test crashes
echo 0 > "$REWARD_FILE"

TEST_FEATURE="/tests/test_feature.py"
if [ ! -f "$TEST_FEATURE" ]; then
    TEST_FEATURE="tests/test_feature.py"
fi

cd /workspace/repo
export PYTHONPATH="src:${PYTHONPATH:-}"

# Run feature tests and regression tests
if pytest -q "$TEST_FEATURE" tests/test_basic.py tests/test_commands.py; then
    echo 1 > "$REWARD_FILE"
    echo "=== TaskForge Verifier: SUCCESS (Reward: 1) ==="
    exit 0
else
    echo 0 > "$REWARD_FILE"
    echo "=== TaskForge Verifier: FAILURE (Reward: 0) ==="
    exit 0
fi
