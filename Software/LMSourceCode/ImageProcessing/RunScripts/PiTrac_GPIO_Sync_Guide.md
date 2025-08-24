# PiTrac Dual Camera GPIO Synchronization Test Guide

## Overview

This document provides a detailed testing guide for the dual-camera GPIO synchronization functionality in the PiTrac system. The system uses Master Pi5 to control the Connect Board via GPIO Pin 22, which then triggers the Slave Pi5 camera for synchronized photography.

## Hardware Connection Verification

### Connection Diagram
Based on project documentation and PCB design, the correct hardware connections are:

```
Master Pi5 Pin 22 (BCM GPIO25) → Connect Board Shr Pin (Sys1_Conn1 Pin 3)
                                        ↓
                              Connect Board Internal Processing
                                        ↓
Connect Board XTrg Pin (Sys2_Conn1 Pin 2) → Slave Pi5 Camera Module XTR Pin
```

### Complete GPIO Connection Table
**Master Pi (192.168.31.122) - Sys1_Conn1 Connection:**
- Vcc (Red) → Master Pi Pin 1 (3.3V)
- Strb (White) → Master Pi Pin 19 (BCM GPIO10)
- Shr (Yellow) → Master Pi Pin 22 (BCM GPIO25) **[Key Trigger Signal]**
- Gnd (Black) → Master Pi Pin 9 (GND) [Pin 6 used by fan]

**Slave Pi (192.168.31.126) - Sys2_Conn1 Connection:**
- Vcc (Red) → Slave Pi Pin 17 (3.3V)  
- XTrg (Yellow) → Slave Camera XTR Pin **[External Trigger Input]**
- Gnd (Black) → Slave Pi Pin 9 (GND)

### Pin Function Description
- **Shr Pin**: Shutter trigger signal input, controls camera external shutter (XTRG)
- **XTrg Pin**: Shutter trigger signal output, connects to slave camera external trigger pin
- **Pin 22**: Master Pi5 BCM GPIO25, used to output trigger pulse

## Synchronization Mechanism

### Trigger Flow
1. Master Pi5 detects ball motion
2. Calls `SendExternalTrigger()` function
3. GPIO25 (Pin 22) outputs high-level pulse signal to Connect Board Shr pin
4. Simultaneously sends LED strobe pulse sequence via SPI
5. Connect Board processes Shr signal and outputs to XTrg pin
6. Slave Pi5 camera receives XTrg trigger signal and immediately captures
7. GPIO25 returns to low level, completing one synchronized capture

### Key Code Locations
- **GPIO Control**: `pulse_strobe.cpp` - `SendExternalTrigger()` function
- **Motion Detection Trigger**: `motion_detect_stage.cpp`
- **Camera Configuration**: `libcamera_interface.cpp:1364-1381`
- **Trigger Mode Setting**: 
  - Camera1 (Master): `setCameraTriggerInternal.sh`
  - Camera2 (Slave): `setCameraTriggerExternal.sh`

## Environment Configuration

### Network Configuration
- Master Pi: 192.168.31.122 (connects to Slave's ActiveMQ broker)
- Slave Pi: 192.168.31.126 (runs ActiveMQ broker on port 61616)
- Samba Shared Directory: /home/golf/share/LM_Shares

### Required Service Status
**Master Pi:**
- ActiveMQ: Not needed (acts as client)
- Shared Directory: `/home/golf/share/LM_Shares` (Samba server)

**Slave Pi:**
- ActiveMQ: Running on port 61616 ✅
- TomEE: Running on port 8080 ✅  
- Mount: Master Pi shared directory to `/home/golf/share/LM_Shares` ✅

### Environment Variables Setup
Use `env.sh` script to set environment variables:

```bash
# Master Pi
source ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/RunScripts/env.sh master 192.168.31.126

# Slave Pi  
source ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/RunScripts/env.sh slave
```

Key Environment Variables:
- `PITRAC_ROOT`: `/root/Dev/PiTrac/Software/LMSourceCode`
- `PITRAC_MSG_BROKER_FULL_ADDRESS`: ActiveMQ connection address
- `PITRAC_BASE_IMAGE_LOGGING_DIR`: `/home/golf/share/LM_Shares/Images`
- `PITRAC_WEBSERVER_SHARE_DIR`: `/home/golf/share/LM_Shares/WebShare`

## Testing Methods

### Method 1: PiTrac Code-Level Trigger Mode Setting

PiTrac automatically sets trigger mode based on `--system_mode` parameter:

**libcamera_interface.cpp:1341-1381 Logic:**
```cpp
case SystemMode::kCamera1: {
    // Set to internal trigger mode
    std::string trigger_mode_command = "sudo $PITRAC_ROOT/ImageProcessing/CameraTools/setCameraTriggerInternal.sh";
    system(trigger_mode_command.c_str());
}

case SystemMode::kCamera2: {
    // Set to external trigger mode  
    std::string trigger_mode_command = "sudo $PITRAC_ROOT/ImageProcessing/CameraTools/setCameraTriggerExternal.sh";
    system(trigger_mode_command.c_str());
}
```

**Camera2 External Trigger Configuration:**
```cpp
options->timeout.set("0ms");  // Wait forever for external trigger
options->shutter.set("11111us"); // Not actually used for external triggering
```

### Method 2: Test Script Approach

#### Step 1: Run Listener Script on Slave Pi
```bash
source ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/RunScripts/env.sh slave
sudo python3 ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/RunScripts/test_slave_external_trigger.py
```

#### Step 2: Run Trigger Script on Master Pi
```bash
source ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/RunScripts/env.sh master 192.168.31.126
python3 ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/RunScripts/test_pin22_trigger.py
```

### Method 3: Official PiTrac Application Test

#### On Slave Pi (Camera2):
```bash
source ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/RunScripts/env.sh slave
cd ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing
./build/pitrac_lm --system_mode camera2 --msg_broker_address tcp://localhost:61616
```

#### On Master Pi (Camera1):
```bash
source ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/RunScripts/env.sh master 192.168.31.126
cd ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing  
./build/pitrac_lm --system_mode camera1 --msg_broker_address tcp://192.168.31.126:61616
```

## Manual Trigger Mode Setting

### Set External Trigger Mode (Slave Pi)
```bash
# Using script
sudo $PITRAC_ROOT/ImageProcessing/CameraTools/setCameraTriggerExternal.sh

# Or directly set
sudo bash -c 'echo 1 > /sys/module/imx296/parameters/trigger_mode'

# Verify setting
cat /sys/module/imx296/parameters/trigger_mode  # Should display: 1
```

### Set Internal Trigger Mode (Master Pi)
```bash
# Using script
sudo $PITRAC_ROOT/ImageProcessing/CameraTools/setCameraTriggerInternal.sh

# Or directly set
sudo bash -c 'echo 0 > /sys/module/imx296/parameters/trigger_mode'

# Verify setting
cat /sys/module/imx296/parameters/trigger_mode  # Should display: 0
```

## Expected Results

### Success Indicators
- ✅ Master Pi can start camera1 mode normally
- ✅ Slave Pi can start camera2 mode normally (external trigger)
- ✅ GPIO25 can output pulse signal correctly
- ✅ Slave camera can be successfully triggered externally
- ✅ Images saved to shared directory: `/home/golf/share/LM_Shares/Images/`
- ✅ ActiveMQ message passing works normally
- ✅ Image timestamp difference < 10ms
- ✅ Logs show "SendExternalTrigger" messages

### Image Quality Check
- **Camera1 (Master)**: Resolution 1456x1088, normal color
- **Camera2 (Slave)**: Resolution 1456x1088, infrared imaging
- Both images should be clear without blur
- Exposure time and gain settings should be reasonable

## Troubleshooting

### Common Issues

#### 1. Configuration File Issues
```bash
# Error: golf_sim_config.json: cannot open file
# Solution: Ensure running from ImageProcessing directory, or copy config file to build directory
cp ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/golf_sim_config.json ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/build/
```

#### 2. basic_string null Error
```bash
# Possible cause: Some fields in configuration file are empty strings
# Needs further debugging to determine which field causes the problem
```

#### 3. Camera Initialization Timeout
```bash
# External trigger mode requires trigger signal to complete initialization
# Solution: Initialize in internal mode first, then switch to external trigger mode
```

#### 4. GPIO Permission Issues
```bash
sudo usermod -a -G gpio $USER
sudo usermod -a -G spi $USER
# Re-login for permissions to take effect
```

#### 5. ActiveMQ Connection Issues
```bash
# Check ActiveMQ status
systemctl status activemq

# Check port listening
netstat -tlnp | grep 61616

# Check firewall
sudo ufw status
```

### Debug Commands

#### GPIO Status Monitoring
```bash
# Monitor GPIO25 status changes
gpionotify 25

# View GPIO status
gpio readall | grep -E "(GPIO|25)"
```

#### Real-time Log Monitoring
```bash
# Monitor PiTrac logs
tail -f /home/golf/share/LM_Shares/Images/*.log

# Monitor system logs
journalctl -f | grep -i camera
```

#### Camera Status Check
```bash
# Check if camera is recognized
libcamera-hello --list-cameras

# Check trigger mode
cat /sys/module/imx296/parameters/trigger_mode

# Test basic camera functionality
libcamera-still -o test.jpg --timeout 2000
```

## Test Script Description

### test_pin22_trigger.py (Master Pi)
- Function: Send GPIO trigger signals
- Location: Master Pi GPIO Pin 22 (BCM GPIO25)
- Modes: Single trigger, continuous trigger, interactive trigger
- Trigger Signal: 100ms high-level pulse

### test_slave_external_trigger.py (Slave Pi)  
- Function: Listen for external trigger signals and capture
- Trigger Mode: External trigger (trigger_mode=1)
- Timeout Mechanism: 30 second timeout, supports Ctrl+C exit
- Image Save: `/home/golf/share/LM_Shares/Images/`
- Initialization Strategy: Initialize in internal mode first, then switch to external trigger

### test_dual_camera_sync.py (Complete Test)
- Function: Complete dual-camera synchronization test
- Test Content: Trigger delay, synchronization accuracy, image quality
- Statistical Analysis: Average delay, standard deviation, success rate

## Configuration File Reference

### golf_sim_config.json Key Configuration
```json
{
    "strobing": {
        "kStrobePulseVectorDriver": ["0.175", "0.7", "1.4", ...],
        "kBaudRateForFastPulses": "115200"
    },
    "cameras": {
        "kCamera1Gain": "1.0",
        "kCamera2Gain": "4.0", 
        "kNumInitialCamera2PrimingPulses": "12",
        "kPauseBeforeCamera2PrimingPulsesMs": "2000"
    },
    "ipc_interface": {
        "kWebActiveMQHostAddress": "PITRAC_MSG_BROKER_FULL_ADDRESS",
        "kMaxCam2ImageReceivedTimeMs": "40000"
    }
}
```

## Maintenance Recommendations

1. **Regular Calibration**: Run complete synchronization test monthly
2. **Connection Check**: Regularly check hardware connection stability  
3. **Log Cleanup**: Regularly clean up test log files
4. **Configuration Backup**: Save configuration files when working normally
5. **Environment Monitoring**: Monitor ActiveMQ and TomEE service status

## Technical Summary

### PiTrac Trigger Mode Auto-Setting Mechanism
- Automatically calls corresponding setup script based on `--system_mode` parameter
- Camera1 mode: Automatically set internal trigger (trigger_mode=0)
- Camera2 mode: Automatically set external trigger (trigger_mode=1)
- Single Pi mode: No automatic setting, requires manual dtoverlay configuration

### GPIO Hardware Synchronization Chain
- Master Pi GPIO25 → Connect Board Shr → Connect Board XTrg → Slave Camera XTR
- Trigger Signal: 100ms high-level pulse 
- Synchronization Accuracy: < 10ms delay
- Electrical Isolation: Achieved through Connect Board optoisolators

### Key Success Factors
1. **Correct Hardware Connection**: GPIO pins, Connect Board wiring correct
2. **Complete Environment Variables**: All PITRAC_* variables set correctly
3. **Normal Service Status**: ActiveMQ, TomEE, Samba services running
4. **Trigger Mode Setting**: Camera1 internal, Camera2 external
5. **Valid Configuration File**: golf_sim_config.json no null fields
6. **Correct Permissions**: GPIO, sudo permissions configured properly

---
**Document Version**: v2.0  
**Last Updated**: 2025-08-24  
**Applicable Version**: PiTrac v0.1+  
**Test Status**: Hardware Connection✅ Environment Configuration✅ Trigger Mode Setting✅ GPIO Test Scripts✅ PiTrac Application Debugging🔄