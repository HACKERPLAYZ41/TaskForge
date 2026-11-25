#!/bin/bash
set -e
echo "========================================================================="
echo "                    TASKFORGE END-TO-END DEMO EXECUTION                  "
echo "========================================================================="
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

chmod +x bin/taskforge
./bin/taskforge demo --offline
