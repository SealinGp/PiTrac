# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PiTrac is an open-source golf launch monitor that uses Raspberry Pi computers and cameras to analyze golf ball launch speed, angles, and spin in three dimensions. The system interfaces with golf simulators (GSPro, E6/TruGolf) and provides a web-based standalone interface. This is a dual-Pi system with complex hardware/software integration.

## System Architecture

### Hardware Components
- **Two Raspberry Pi Systems**: Main Pi (usually Pi 5) for Camera 1 and secondary Pi (Pi 4/5) for Camera 2
- **Camera System**: Two Raspberry Pi HQ cameras for stereo vision
- **Strobe System**: LED strobing for ball capture with custom PCB connector board
- **Web Interface**: Tomcat/TomEE server running on Camera 2 Pi

### Software Architecture
The main application is written in C++20 and consists of several key subsystems:

#### Core Components (`Software/LMSourceCode/ImageProcessing/`)
- **Main Application**: `lm_main.cpp` - Entry point and main processing loop
- **Image Processing**: Ball detection using OpenCV, Hough circles, ellipse detection
- **Camera Interface**: `libcamera_interface.cpp` - Handles camera operations
- **Ball Analysis**: `ball_image_proc.cpp`, `golf_ball.cpp` - Ball tracking and spin analysis
- **State Machine**: `gs_fsm.cpp` - Manages system states and shot processing
- **IPC System**: Message passing between Pi systems using ActiveMQ
- **Simulator Interfaces**: `gs_gspro_interface.cpp`, `gs_e6_interface.cpp`

#### Build System
- **Primary**: Meson build system (`meson.build`)
- **Dependencies**: OpenCV 4.9+, libcamera, boost, ActiveMQ C++, lgpio
- **Cross-compilation**: Supports Pi 4 and Pi 5 architectures

## Common Development Commands

### Building the Main Application
```bash
# Set up build environment (run once)
cd Software/LMSourceCode/ImageProcessing
meson setup build --buildtype=release

# Build the application
cd build
ninja

# The executable will be at: build/pitrac_lm
```

### Build Options
```bash
# Enable recompiling closed source components (if you have access)
meson setup build -Denable_recompile_closed_source=true

# For Pi 4 compilation (mostly deprecated)
meson setup build -Denable_compile_on_pi4=true
```

### Environment Setup
PiTrac requires several environment variables before running:
```bash
# Required environment variables (from RunScripts/runPiTracCommon.sh)
export PITRAC_ROOT="/path/to/pitrac/root"
export PITRAC_MSG_BROKER_FULL_ADDRESS="tcp://broker_address:61616"
export PITRAC_WEBSERVER_SHARE_DIR="/path/to/web/share"
export PITRAC_BASE_IMAGE_LOGGING_DIR="/path/to/image/logs"

# Optional simulator addresses
export PITRAC_E6_HOST_ADDRESS="simulator_ip"
export PITRAC_GSPRO_HOST_ADDRESS="simulator_ip"
```

### Running the System
```bash
# Camera 1 (main Pi)
cd Software/LMSourceCode/ImageProcessing/RunScripts
./runCam1.sh

# Camera 2 (secondary Pi)
./runCam2.sh

# Single Pi mode (for development)
./runCam1SinglePi.sh
```

### Testing and Calibration
```bash
# Camera calibration
./runCam1Calibration.sh
./runCam2Calibration.sh

# Automated testing suite
./runAutomatedTesting.sh

# Take test shots for calibration
cd ../CameraTools
./take_calibration_shots.sh
```

### Web Application
The web interface is a Java/Jakarta EE application in `golfsim_tomee_webapp/`:
```bash
# Build web application
cd Software/LMSourceCode/ImageProcessing/golfsim_tomee_webapp
mvn clean package

# Deploy to TomEE (usually on Camera 2 Pi)
# Copy target/*.war to TomEE webapps directory
```

## Configuration

### Primary Configuration File
`Software/LMSourceCode/ImageProcessing/golf_sim_config.json` contains all system parameters:
- Camera calibration matrices and distortion coefficients
- Ball detection parameters (Hough circles, Canny edge detection)
- Strobe timing and pulse configurations
- Simulator interface settings
- Physical constants and positioning

### Camera Configuration
- Camera calibration data is stored in the config JSON
- Motion detection settings in `assets/motion_detect.json`
- Camera-specific JSON files for different Pi models (`imx296_noir.json`)

## Key Development Areas

### Image Processing Pipeline
1. **Motion Detection**: Uses libcamera motion detection stage
2. **Ball Detection**: Multi-stage Hough circle detection with fallback algorithms
3. **Spin Analysis**: Gabor filter-based pattern matching with 3D rotation estimation
4. **Trajectory Calculation**: Stereo vision mathematics for 3D ball tracking

### Inter-Pi Communication
- ActiveMQ message broker for IPC between Pi systems
- Message types: control, image data, results
- Located in `gs_ipc_*.cpp` files

### Hardware Integration
- GPIO control for strobe timing (`pulse_strobe.cpp`)
- Camera hardware abstraction (`camera_hardware.cpp`)
- Trigger synchronization between cameras

## Important File Structure

### Source Code
- `Software/LMSourceCode/ImageProcessing/` - Main C++ application
- `Software/CalibrateCameraDistortions/` - Python camera calibration tools
- `Hardware/Connector Board/` - KiCad PCB designs for custom hardware

### 3D Printed Parts
- `3D Printed Parts/` - FreeCAD models for enclosures and mounts
- Multiple enclosure versions and component variations

### Documentation
- `Documentation/` - Comprehensive setup and usage guides
- Assembly instructions, troubleshooting, configuration guides

## Dependencies and Prerequisites

### System Dependencies
```bash
# Core libraries needed for compilation
libcamera-dev libopencv-dev libboost-all-dev
libactivemq-cpp-dev libssl-dev libapr1-dev
libfmt-dev liblgpio-dev libmsgpack-cxx-dev
```

### Hardware Requirements
- Requires specific Raspberry Pi camera modules
- Custom strobe hardware with GPIO control
- Precise physical positioning and calibration

## Development Notes

- The system uses some closed-source components (`gs_e6_response.cpp.o`)
- Camera calibration is critical for accurate measurements
- Timing synchronization between cameras is essential
- The system requires careful physical setup and calibration
- Configuration parameters are highly sensitive to hardware setup

## Testing

- Automated test suite in `Software/LMSourceCode/Testing/`
- Manual calibration tools and scripts
- Comparison testing against commercial launch monitors
- Shot injection system for repeatable testing