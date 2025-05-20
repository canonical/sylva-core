#!/bin/bash

# This script runs a command, checks its exit code, and validates whether it
# matches the expected outcome ("success" or "reject"). It is intended to automate test result validation and log failures.
# Usage: ./validate-test-result.sh <description> <expected_outcome> <command>

set +e

# Use a temp file for accumulating failed test descriptions.
FAILED_TESTS_FILE="/tmp/test-failures.log"

if [ "$0" = "$BASH_SOURCE" ]; then
  if [ $# -lt 3 ]; then
    echo "Usage: ./validate-test-result.sh <description> <expected_outcome (success|reject)> <command> [args...]"
    exit 1
  fi

  description="$1"
  expected_outcome="$2"
  shift 2
  cmd_and_args=("$@")

  echo "----------------------------------------------------"
  echo "Running: $description (expect $expected_outcome)"

  "${cmd_and_args[@]}"
  exit_code=$?

  if [ "$expected_outcome" = "reject" ]; then
    if [ $exit_code -ne 0 ]; then
      echo "✅ PASSED: Command was rejected as expected (exit code: $exit_code)."
      exit 0
    else
      echo "❌ FAILED: Command succeeded but was expected to be rejected (exit code: $exit_code)."
      echo "FAILED: $description (expected rejection, got success)" >> "$FAILED_TESTS_FILE"
      exit 1
    fi
  elif [ "$expected_outcome" = "success" ]; then
    if [ $exit_code -eq 0 ]; then
      echo "✅ PASSED: Command succeeded as expected."
      exit 0
    else
      echo "❌ FAILED: Command failed but was expected to succeed (exit code: $exit_code)."
      echo "FAILED: $description (expected success, got failure)" >> "$FAILED_TESTS_FILE"
      exit 1
    fi
  else
    echo "⚠️ WARNING: Unknown expected outcome '$expected_outcome' for test '$description'."
    echo "FAILED: $description (invalid expected outcome: $expected_outcome)" >> "$FAILED_TESTS_FILE"
    exit 1
  fi
fi
