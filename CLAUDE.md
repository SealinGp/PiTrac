# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PiTrac is the world's first open-source DIY golf launch monitor that uses photometric analysis to measure golf ball launch parameters (speed, angles, spin) using dual Raspberry Pi computers with high-speed cameras. It interfaces with golf simulators like GSPro and E6/TruGolf.

## Architecture

PiTrac uses a **dual-Pi distributed system**:
- **Camera 1 Pi**: Primary ball detection and motion tracking
- **Camera 2 Pi**: Secondary trajectory analysis + web UI (Tomee server)
- **Communication**: ActiveMQ message broker for inter-Pi communication
- **Languages**: C++20 core application, Java web interface
- **Computer Vision**: OpenCV 4.9+ with custom ball detection algorithms

## Build System

**Primary build system is Meson** (not CMake):

```bash
# Standard build process
cd Software/LMSourceCode/ImageProcessing/
meson setup build/
ninja -C build/

# Build options
meson setup build/ -Denable_compile_on_pi4=true  # For Pi 4 compatibility
meson setup build/ -Denable_recompile_closed_source=false  # Use pre-compiled objects
```

**Important**: The project uses pre-compiled closed-source object files by default. CMakeLists.txt files exist but are for individual modules only.

## Environment Setup

PiTrac requires extensive environment variables - **always source the common script first**:

```bash
export PITRAC_ROOT=/path/to/PiTrac/Software/LMSourceCode
export PITRAC_MSG_BROKER_FULL_ADDRESS="tcp://192.168.1.x:61616"
export PITRAC_WEBSERVER_SHARE_DIR="/path/to/shared/images"
export PITRAC_BASE_IMAGE_LOGGING_DIR="/path/to/logs"
export PITRAC_GSPRO_HOST_ADDRESS="192.168.1.x"  # Optional
export PITRAC_E6_HOST_ADDRESS="192.168.1.x"     # Optional

# Then source common settings
source $PITRAC_ROOT/ImageProcessing/RunScripts/runPiTracCommon.sh
```

## Running PiTrac

**Use the provided run scripts** - don't run the binary directly:

```bash
# Camera 1 (primary ball detection)
./RunScripts/runCam1.sh

# Camera 2 (trajectory analysis)
./RunScripts/runCam2.sh

# Single Pi mode (development/testing)
./RunScripts/runCam1SinglePi.sh

# Calibration modes
./RunScripts/runCam1Calibration.sh
./RunScripts/runCam2Calibration.sh

# Testing and diagnostics
./RunScripts/runAutomatedTesting.sh
./RunScripts/runTestGsProServer.sh
```

## Key Configuration

**Main config**: `golf_sim_config.json` (490+ lines)
- Ball detection parameters (Hough circles, Canny edge detection)
- Camera calibration matrices and distortion coefficients
- Strobe timing sequences
- Algorithm parameters (CLAHE processing, motion detection thresholds)

**Camera settings**: Motion detection thresholds, exposure, gain
**Build options**: `meson_options.txt` for compile-time features

## Core Components

### Ball Detection Pipeline
- **Motion Detection**: Background subtraction for ball presence
- **Hough Circle Detection**: Primary ball identification algorithm
- **Alternative Ellipse Detection**: YAED (Yet Another Ellipse Detector) fallback
- **CLAHE Processing**: Contrast enhancement for better detection

### State Machine (`gs_fsm.cpp`)
States: Initializing → WaitingForBall → WaitingForSimulatorArmed → WaitingForBallStabilization → WaitingForBallHit → CalculatingResults

### IPC System (`gs_ipc_*.cpp`)
- **ActiveMQ messaging** between Pi systems
- **Message types**: Control messages, image data, results
- **Synchronization**: Coordinated capture timing between cameras

### Simulator Interfaces
- **GSPro**: Socket-based JSON communication (`gs_gspro_*.cpp`)
- **E6/TruGolf**: HTTP-based communication (`gs_e6_*.cpp`)
- **Results formatting**: Club data, ball parameters, spin calculations

## Development Dependencies

**System packages required**:
```bash
# Core vision/math libraries
libopencv-dev (>=4.9.0), libboost-all-dev (>=1.74.0)

# Camera/hardware
libcamera-dev, liblgpio-dev, libbcm-host-dev

# Messaging/networking
libactivemq-cpp-dev, libapr1-dev, libssl-dev

# Build tools
meson, ninja-build, pkg-config

# Web interface (Camera 2 Pi only)
openjdk-17-jdk, maven, apache-tomee
```

**Build from source** (see Documentation/Raspberry Pi Setup and Configuration.md):
- OpenCV (with specific Pi optimizations)
- libcamera (latest from RPi foundation)
- ActiveMQ C++ library

## Testing

**No standard test framework** - uses custom scripts:
```bash
# Run automated test suite
./RunScripts/runAutomatedTesting.sh

# Test individual components
./RunScripts/runTestGsProServer.sh  # Simulator interface
./RunScripts/runTestResults.sh      # Results calculation
./RunScripts/runPulseTest.sh        # Strobe timing
```

## Hardware-Specific Notes

- **Right-handed golfers only** (current limitation)
- **Requires dual Pi setup** for full functionality
- **Camera calibration required** before use (see Documentation/PiTrac - Camera Calibration.md)
- **Strobe timing critical** - uses hardware PWM for microsecond precision
- **Custom PCB required** for power/strobe control (designs in Hardware/ directory)

## Web Interface

**Tomee-based monitoring interface** (Camera 2 Pi only):
```bash
# Build web app
cd golfsim_tomee_webapp/
mvn clean package

# Deploy to Tomee (automatic via scripts)
```
Provides real-time monitoring, configuration, and image display at http://pi-ip:8080

## Important Constraints

- **Closed-source components**: Some E6 interface code uses pre-compiled objects
- **Pi-specific**: Designed for Raspberry Pi hardware (GPIO, camera interface)
- **Network dependent**: Requires ActiveMQ broker for dual-Pi operation
- **Calibration required**: Extensive camera calibration needed for accuracy
- **Right-hand only**: Current algorithms assume right-handed golfer orientation
