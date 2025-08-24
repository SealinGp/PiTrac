#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only */
#
# Copyright (C) 2022-2025, Verdant Consultants, LLC.
#
# Fixed version of runPulseTest.sh with proper environment variable handling

# Ensure PITRAC_ROOT is set
if [ -z "$PITRAC_ROOT" ]; then
    export PITRAC_ROOT=/root/Dev/PiTrac/Software/LMSourceCode
    echo "PITRAC_ROOT was not set, using default: $PITRAC_ROOT"
fi

# Source the common script to set other environment variables
. $PITRAC_ROOT/ImageProcessing/RunScripts/runPiTracCommon.sh

# Display environment variables for debugging
echo "PITRAC_ROOT set to: $PITRAC_ROOT"
echo "PITRAC_MSG_BROKER_FULL_ADDRESS set to: $PITRAC_MSG_BROKER_FULL_ADDRESS"
echo "PITRAC_WEBSERVER_SHARE_DIR set to: $PITRAC_WEBSERVER_SHARE_DIR"
echo "PITRAC_BASE_IMAGE_LOGGING_DIR set to: $PITRAC_BASE_IMAGE_LOGGING_DIR"
echo ""
echo ""
echo "PITRAC_COMMON_CMD_LINE_ARGS = $PITRAC_COMMON_CMD_LINE_ARGS"

# Run the pulse test with explicitly set environment
cd $PITRAC_ROOT/ImageProcessing
$PITRAC_ROOT/ImageProcessing/build/pitrac_lm --pulse_test --system_mode camera1 --logging_level trace