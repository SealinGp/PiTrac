

# 测试步骤
> 确认Pi 1到Pi 2相机的触发信号路径工作正常，这个信号路径通过连接板传输。
## 第1步: 在Pi 2(Slave Pi)上
```bash
#先通过vnc viewer 连接 Pi 2

#初始化环境变量
source ~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/RunScripts/env.sh
cd $PITRAC_ROOT/ImageProcessing

#相机设置为外部触发模式
sudo ./CameraTools/setCameraTriggerExternal.sh

#在Slave Pi上执行 - 两个命令任选一个
rpicam-hello
# 或者
./RunScripts/runCam2Still.sh
# 期望现象: 相机程序会挂起等待，不会拍照，因为在等待来自Pi 1的触发信号
```

## 第2步: 在Master Pi (Pi 1)上执行
```bash
#在Pi 1上发送触发脉冲
cd $PITRAC_ROOT/ImageProcessing
./RunScripts/runPulseTest.sh
```

## 第3步: 观察结果
- ✅ 成功: Pi 1开始发送脉冲后，Pi 2的相机程序立即拍照
- ❌ 失败: Pi 2相机程序继续挂起，没有拍照反应


## 第4步: 恢复内部触发模式

## 测试完成后，在Slave Pi上执行
```bash
#恢复内部触发模式
sudo $PITRAC_ROOT/CameraTools/setCameraTriggerInternal.sh
```

# 当前问题:
Master Pi上执行runPulseTest.sh  报错:
```
root@golf1:~/Dev/PiTrac/Software/LMSourceCode/ImageProcessing# ./RunScripts/runPulseTest.sh 
PITRAC_ROOT set to: /root/Dev/PiTrac/Software/LMSourceCode
PITRAC_MSG_BROKER_FULL_ADDRESS set to: tcp://192.168.31.126:61616
PITRAC_WEBSERVER_SHARE_DIR set to: /home/golf/share/LM_Shares/WebShare
PITRAC_BASE_IMAGE_LOGGING_DIR set to: /home/golf/share/LM_Shares/Images

PITRAC_COMMON_CMD_LINE_ARGS =  --config_file /root/Dev/PiTrac/Software/LMSourceCode/ImageProcessing/golf_sim_config.json --msg_broker_address tcp://192.168.31.126:61616 --web_server_share_dir /home/golf/share/LM_Shares/WebShare --base_image_logging_dir /home/golf/share/LM_Shares/Images
[2025-08-24 18:56:35.862347] (0x00007fff21208040) [info] Golf Sim Launch Monitor Started
Options:
    system_mode: camera1
    logging_level: trace
    artifact_save_level: final_results_only
    shutdown: 0
    cam_still_mode: 0
    lm_comparison_mode: 0
    send_test_results: 0
    output_filename: out.png
    msg_broker_address_: tcp://192.168.31.126:61616
    configuration file: golf_sim_config.json
    pulse_test: 1
    golfer_orientation: right_handed
    practice_ball: 0
    wait_keys: 0
    run_single_pi: 0
    show_images: 0
    use_non_IR_camera: 0
    camera_gain (will override .json file settings): 1.000000
[2025-08-24 18:56:35.869326] (0x00007fff21208040) [info] Overriding camera gains with value: 1.000000.
[2025-08-24 18:56:35.869594] (0x00007fff21208040) [error] Exception occurred. ERROR: *** basic_string: construction from null is not valid ***
```