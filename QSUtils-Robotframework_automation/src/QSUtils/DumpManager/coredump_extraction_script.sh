#!/bin/bash

# Coredump and Log Extraction Script for QSMonitor
# Enhanced version based on Windows batch file conversion

# Get current date and time
DATESTR=$(date +"%Y_%m_%d")
HMS=$(date +"%H%M%S")

# Get MAC address
MAC_ADDR=$(adb -s "$ADB_SERIAL" shell "cat /sys/class/net/wlan0/address" | sed 's/://g' | tr -d '\r')

# Get product name
PRODUCT_NAME=$(adb -s "$ADB_SERIAL" shell "cat /data/misc/device_name.txt" | sed 's/[^a-zA-Z0-9]//g' | tr -d '\r')

# Create directory name
DT="oneos_${PRODUCT_NAME}_log_${DATESTR}_${HMS}_${MAC_ADDR}"

# Remove any carriage return characters from the final directory name
DT=$(echo "$DT" | tr -d '\r')

# Create main directory
mkdir -p "$DT"

# Check if directory creation failed, use default name
if [ $? -ne 0 ]; then
  DT="oneos_product_log_${DATESTR}_${HMS}_${MAC_ADDR}"
  mkdir -p "$DT"
fi

# Define subdirectories
HARMAN_SDK_DIR="${PRODUCT_NAME}_log"
BT_DIR="bluetooth"
CD_DIR="coredump"
SYS_DIR="system"
AVS_DIR="avs_mrm"
OTA_DIR="ota_manager"
HC_DIR="harmancast"
LIGHTTPD_DIR="lighttpd"

# Create subdirectories
mkdir -p "$DT/$HARMAN_SDK_DIR"
mkdir -p "$DT/$BT_DIR"
mkdir -p "$DT/$CD_DIR"
mkdir -p "$DT/$SYS_DIR"
mkdir -p "$DT/$AVS_DIR"
mkdir -p "$DT/$OTA_DIR"
mkdir -p "$DT/$HC_DIR"
mkdir -p "$DT/$LIGHTTPD_DIR"

# Define config directories
CONFIG_DIR="$DT/config_files"
JSON_DIR="$CONFIG_DIR/json"
CONF_DIR="$CONFIG_DIR/conf"

# Create config directories
mkdir -p "$JSON_DIR"
mkdir -p "$CONF_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting log capture process${NC}"

# Capture basic files
echo -e "${GREEN}Capturing basic files${NC}"
adb -s "$ADB_SERIAL" shell sync
adb -s "$ADB_SERIAL" pull /sw_version.txt "./$DT/"
adb -s "$ADB_SERIAL" pull /data/misc/device_name.txt "./$DT/"
adb -s "$ADB_SERIAL" pull /proc/cmdline "./$DT/cmdline.txt"

# Dump for harmancast
echo -e "${GREEN}Dump for harmancast${NC}"
adb -s "$ADB_SERIAL" pull /data/etc/group.json "./$DT/$HC_DIR/"
adb -s "$ADB_SERIAL" pull /var/run/harmancast.state "./$DT/$HC_DIR/"
adb -s "$ADB_SERIAL" shell "dump_harmancast.sh"
adb -s "$ADB_SERIAL" pull /tmp/hcdump.tgz "./$DT/$HC_DIR/"

# Create dump flags to start dump immediately
echo -e "${GREEN}Starting audio dump processes${NC}"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/tutti_dump/"
adb -s "$ADB_SERIAL" shell "touch /tmp/dump_td"
adb -s "$ADB_SERIAL" shell "touch /tmp/dump_tc"

# Start dump mas data
echo -e "${GREEN}Start dump mas data${NC}"
rm -rf mas_dump
adb -s "$ADB_SERIAL" shell "touch /tmp/log_all"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/mas_dump/"
adb -s "$ADB_SERIAL" shell "mkdir /tmp/mas_dump/"
adb -s "$ADB_SERIAL" shell "mas_dbg dumpst 0"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 5 1 /tmp/mas_dump/mas_input_main.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 6 1 /tmp/mas_dump/mas_input_sub0.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 7 1 /tmp/mas_dump/mas_input_sub1.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 8 1 /tmp/mas_dump/mas_input_track_3.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 9 1 /tmp/mas_dump/mas_input_track_4.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 10 1 /tmp/mas_dump/mas_input_track_5.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 11 1 /tmp/mas_dump/mas_input_track_6.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 12 1 /tmp/mas_dump/mas_input_track_7.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 13 1 /tmp/mas_dump/mas_input_track_8.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 14 1 /tmp/mas_dump/mas_input_track_9.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 15 1 /tmp/mas_dump/mas_input_track_10.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 16 1 /tmp/mas_dump/mas_input_track_11.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 21 1 /tmp/mas_dump/mas_input_track_16.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 25 1 /tmp/mas_dump/mas_input_track_20.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 0 1 /tmp/mas_dump/mas_ppcin.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 1 1 /tmp/mas_dump/mas_ppcout.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 2 1 /tmp/mas_dump/mas_halout.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dumpst 0"

# Start dump hmpp
echo -e "${GREEN}Start dump hmpp${NC}"
rm -rf hmpp_dump_data
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/hmpp_dump_data"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/hmpp_input*.pcm"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/hmpp_output*.pcm"
adb -s "$ADB_SERIAL" shell "mkdir -p /tmp/hmpp_dump_data"
adb -s "$ADB_SERIAL" shell "printf /tmp/hmpp_dump_data | tee /tmp/hmpp_dump_path"
adb -s "$ADB_SERIAL" shell "touch /tmp/dump_hmpp"
adb -s "$ADB_SERIAL" shell "amixer cset name='HM DUMP ALL' 1"

# Dump gst decoder
echo -e "${GREEN}Start dump gst decoder${NC}"
adb -s "$ADB_SERIAL" shell "touch /tmp/dataparse_in.conf"
adb -s "$ADB_SERIAL" shell "touch /tmp/dataparse_out.conf"
adb -s "$ADB_SERIAL" shell "touch /tmp/dec_done.conf"
adb -s "$ADB_SERIAL" shell sync

# Dump gst mtk src/sink
echo -e "${GREEN}Dump gst mtk src/sink${NC}"
adb -s "$ADB_SERIAL" shell "touch /tmp/mtkalsasrc_out.conf"
rm -f mtkalsasrc_out.raw
adb -s "$ADB_SERIAL" shell sync
adb -s "$ADB_SERIAL" shell "touch /tmp/sinkoutput.conf"
rm -f sinkoutput.pcm
adb -s "$ADB_SERIAL" shell sync

# Dump prepp
echo -e "${GREEN}Dump prepp${NC}"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/prepp_*"
adb -s "$ADB_SERIAL" shell "touch /tmp/dump_prepp"
adb -s "$ADB_SERIAL" shell sync

# Record few seconds audio
sleep 1

# Remove dump flags to stop dump immediately
echo -e "${GREEN}Stopping audio dump processes${NC}"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/dump_td"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/dump_tc"
adb -s "$ADB_SERIAL" shell sync

# Stop hmpp dump
echo -e "${GREEN}Stop hmpp dump${NC}"
adb -s "$ADB_SERIAL" shell "amixer cset name='HM DUMP ALL' 0"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/dump_hmpp"

# Stop gst decoder
echo -e "${GREEN}Stop gst decoder${NC}"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/dataparse_in.conf"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/dataparse_out.conf"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/dec_done.conf"

# Stop gst mtksrc/sink
echo -e "${GREEN}Stop gst mtksrc/sink${NC}"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/mtkalsasrc_out.conf"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/sinkoutput.conf"

# Stop prepp dump
echo -e "${GREEN}Stop prepp dump${NC}"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/dump_prepp"
adb -s "$ADB_SERIAL" shell sync

# Stop mas dump
echo -e "${GREEN}Stop mas dump${NC}"
adb -s "$ADB_SERIAL" shell "mas_dbg dumpst 0"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 5 0 /tmp/mas_dump/mas_input_main.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 6 0 /tmp/mas_dump/mas_input_sub0.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 7 0 /tmp/mas_dump/mas_input_sub1.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 8 0 /tmp/mas_dump/mas_input_track_3.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 9 0 /tmp/mas_dump/mas_input_track_4.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 10 0 /tmp/mas_dump/mas_input_track_5.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 11 0 /tmp/mas_dump/mas_input_track_6.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 12 0 /tmp/mas_dump/mas_input_track_7.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 13 0 /tmp/mas_dump/mas_input_track_8.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 14 0 /tmp/mas_dump/mas_input_track_9.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 15 0 /tmp/mas_dump/mas_input_track_10.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 16 0 /tmp/mas_dump/mas_input_track_11.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 21 0 /tmp/mas_dump/mas_input_track_16.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 25 0 /tmp/mas_dump/mas_input_track_20.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 0 0 /tmp/mas_dump/mas_ppcin.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 1 0 /tmp/mas_dump/mas_ppcout.pcm"
adb -s "$ADB_SERIAL" shell "mas_dbg dump 2 0 /tmp/mas_dump/mas_halout.pcm"

# Start pull all dump
echo -e "${GREEN}Pulling all audio dump data${NC}"
adb -s "$ADB_SERIAL" pull "/tmp/tutti_dump/" "./$DT/"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/tutti_dump/"

# Pull mas dump
echo -e "${GREEN}Pull mas dump${NC}"
adb -s "$ADB_SERIAL" pull /tmp/mas_dump/ "./$DT/"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/mas_dump/"

# Pull hmpp dump
echo -e "${GREEN}Pull hmpp dump${NC}"
adb -s "$ADB_SERIAL" pull /tmp/hmpp_dump_data "./$DT/"
adb -s "$ADB_SERIAL" pull /data/misc/cal_setting.bin "./$DT/hmpp_dump_data/"
adb -s "$ADB_SERIAL" pull /data/misc/cal_setting.bin.crash "./$DT/hmpp_dump_data/"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/hmpp_dump_data"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/hmpp_dump_path"
adb -s "$ADB_SERIAL" pull /tmp/hmpp_input_6ch.pcm "./$DT/"
adb -s "$ADB_SERIAL" pull /tmp/hmpp_output_16ch.pcm "./$DT/"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/hmpp_input*.pcm"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/hmpp_output*.pcm"

# Pull gst dump
echo -e "${GREEN}Pull gst dump${NC}"
adb -s "$ADB_SERIAL" pull /tmp/dataparse_in.raw "./$DT/"
adb -s "$ADB_SERIAL" pull /tmp/dataparse_out.raw "./$DT/"
adb -s "$ADB_SERIAL" pull /tmp/dec_done.pcm "./$DT/"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/dataparse_in.raw"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/dataparse_out.raw"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/dec_done.pcm"

# Pull gst mtksrc/sink
echo -e "${GREEN}Pull gst mtksrc/sink${NC}"
adb -s "$ADB_SERIAL" pull /tmp/mtkalsasrc_out.raw "./$DT/"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/mtkalsasrc_out.raw"
adb -s "$ADB_SERIAL" pull /tmp/sinkoutput.pcm "./$DT/"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/sinkoutput.pcm"

# Pull prepp
echo -e "${GREEN}Pull prepp${NC}"
adb -s "$ADB_SERIAL" pull /tmp/prepp_input_12ch.pcm "./$DT/"
adb -s "$ADB_SERIAL" pull /tmp/prepp_output_12ch.pcm "./$DT/"
adb -s "$ADB_SERIAL" shell "rm -rf /tmp/prepp_*"

# Capture harman sdk log
echo -e "${GREEN}Capture harman sdk log${NC}"
adb -s "$ADB_SERIAL" shell "dump_log.sh"
adb -s "$ADB_SERIAL" pull /data/tmp/dump_log "./$DT/$HARMAN_SDK_DIR/"
adb -s "$ADB_SERIAL" pull /data/tmp/system_bootup.log "./$DT/$HARMAN_SDK_DIR/"
adb -s "$ADB_SERIAL" pull /run/dhcpcd/hooks.log "./$DT/$HARMAN_SDK_DIR/dhcp_hooks.log"
adb -s "$ADB_SERIAL" shell "/system/workdir/bin/localSendSocket 4 a01_thread_dump"
adb -s "$ADB_SERIAL" pull /tmp/a01_thread_dump "./$DT/$HARMAN_SDK_DIR/a01_thread_dump"
adb -s "$ADB_SERIAL" shell "wpa_cli -iwlan0 log_level DEBUG"
adb -s "$ADB_SERIAL" shell "rm -rf /data/tmp/dump_log"

# Capture log for BT
echo -e "${GREEN}Capture log for BT${NC}"
adb -s "$ADB_SERIAL" pull /data/misc/bluedroid/bt_config.conf "./$DT/$BT_DIR/bt_config.conf"
adb -s "$ADB_SERIAL" pull /data/misc/bluedroid/bt_config.bak "./$DT/$BT_DIR/bt_config.bak"
adb -s "$ADB_SERIAL" pull /data/misc/bluedroid/bt_did.conf "./$DT/$BT_DIR/bt_did.conf"
adb -s "$ADB_SERIAL" pull /data/misc/bluedroid/bt_stack.conf "./$DT/$BT_DIR/bt_stack.conf"
adb -s "$ADB_SERIAL" shell "ps | grep blu" >"./$DT/$BT_DIR/bt_process.log"

# Capture log for whole system
echo -e "${RED}Capture log for whole system${NC}"
adb -s "$ADB_SERIAL" shell "cat /sys/class/power_supply/BQ25601_CHARGER/capacity" >"./$DT/$SYS_DIR/power.log"
adb -s "$ADB_SERIAL" shell "ps" >"./$DT/$SYS_DIR/process.log"
adb -s "$ADB_SERIAL" shell "df -h" >"./$DT/$SYS_DIR/disk.log"
adb -s "$ADB_SERIAL" shell "du /tmp/* -sh ; du /run/* -sh; du /var/* -sh; du /data/var/lib/systemd/systemd-coredump/ -sh; du /data/tmp/crash-alarm/ -sh;" >>"./$DT/$SYS_DIR/disk.log"
adb -s "$ADB_SERIAL" shell "du /ota/* -h" >>"./$DT/$SYS_DIR/disk.log"
adb -s "$ADB_SERIAL" pull /ota/misc/hm-ota.txt "./$DT/$SYS_DIR/"
adb -s "$ADB_SERIAL" shell "export TERM=xterm; /usr/bin/top -n 5 -d 1" >"./$DT/$SYS_DIR/top.log"
adb -s "$ADB_SERIAL" shell "procrank" >"./$DT/$SYS_DIR/procrank.log"
adb -s "$ADB_SERIAL" shell "echo 'cpu_temp:'; cat /proc/mtktz/mtktscpu; echo 'pcb_temp:'; cat /proc/mtktz/mtktsAP; echo 'cpu_freq:'; cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq; echo 'cpu_on:'; cat /sys/devices/system/cpu/online; cat /proc/thermlmt" >"./$DT/$SYS_DIR/cpu.log"
adb -s "$ADB_SERIAL" pull /data/asound.state "./$DT/$SYS_DIR/"
adb -s "$ADB_SERIAL" pull /data/audio-ui/volume/music "./$DT/$SYS_DIR/music_vol"
adb -s "$ADB_SERIAL" shell "echo '================free=================='; free -m; echo '================meminfo=================='; cat /proc/meminfo; echo '==================ps========================='; ps -aux -t; echo '======================tmpfs======================'; du /tmp/* -sh; du /run/* -sh; du /var/* -sh; echo '==================top========================'; TERM=xterm top -n 1 -H -d 1; TERM=xterm top -n 1 -H -d 1; echo '=====================dump lsof====================='; lsof" >"./$DT/$SYS_DIR/system_log.txt"

# Capture coredump for the system crash
echo -e "${RED}Capture coredump for the system crash${NC}"
adb -s "$ADB_SERIAL" shell "ls -all /data/var/lib/systemd/systemd-coredump" >"./$DT/$CD_DIR/coredump.log"
adb -s "$ADB_SERIAL" pull /data/var/lib/systemd/systemd-coredump "./$DT/$CD_DIR/coredump"
adb -s "$ADB_SERIAL" pull /data/tmp/crash-alarm "./$DT/$CD_DIR/"
adb -s "$ADB_SERIAL" pull /sys/fs/pstore/ "./$DT/$CD_DIR/"
adb -s "$ADB_SERIAL" shell "cat /proc/*/maps" >"./$DT/$CD_DIR/proc_maps.log"
adb -s "$ADB_SERIAL" shell "free -k" >"./$DT/$CD_DIR/free_mem.log"
adb -s "$ADB_SERIAL" shell "cat /proc/meminfo" >>"./$DT/$CD_DIR/free_mem.log"

# IMPORTANT: Delete coredump files after successful extraction
echo -e "${RED}Deleting coredump files from device after extraction${NC}"
adb -s "$ADB_SERIAL" shell "rm -rf /data/var/lib/systemd/systemd-coredump/*"
adb -s "$ADB_SERIAL" shell "rm -rf /data/tmp/crash-alarm/*"
echo -e "${GREEN}Coredump files deleted successfully${NC}"

# Airplay corrupt token
adb -s "$ADB_SERIAL" pull /data/.airplay/license.plist.corrupt "./$DT/$CD_DIR/airplay.license.plist.corrupt"

# Dump avs related log
echo -e "${GREEN}Dump avs related log${NC}"
LOGFILE="./$DT/$AVS_DIR/avs_offline.log"

echo "starting test at $(date)" >"$LOGFILE"
adb -s "$ADB_SERIAL" shell "ping -c5 www.amazon.com" >>"$LOGFILE"
adb -s "$ADB_SERIAL" shell "ping -c5 www.google.com" >>"$LOGFILE"
adb -s "$ADB_SERIAL" shell "ping -c5 8.8.8.8" >>"$LOGFILE"
adb -s "$ADB_SERIAL" shell "netcfg|grep wlan0" >>"$LOGFILE"
adb -s "$ADB_SERIAL" shell "ifconfig -a" >>"$LOGFILE"
adb -s "$ADB_SERIAL" shell "ps |grep AlexaApp" >>"$LOGFILE"

# Capture ota log
adb -s "$ADB_SERIAL" pull /ota/log/installer.log "$DT/$OTA_DIR/install.log"

# Capture lighttpd log
echo -e "${GREEN}Capture lighttpd log${NC}"
adb -s "$ADB_SERIAL" pull /tmp/access.log "$DT/$LIGHTTPD_DIR/access.log"
adb -s "$ADB_SERIAL" pull /tmp/lighttpd.error.log "$DT/$LIGHTTPD_DIR/lighttpd.error.log"
adb -s "$ADB_SERIAL" shell "systemctl status lighttpd.service" >"./$DT/$LIGHTTPD_DIR/lighttpd.service.log"

# Capture avs config files
adb -s "$ADB_SERIAL" pull /data/AlexaClientSDKConfig.json "./$DT/$AVS_DIR/AlexaClientSDKConfig.json"
adb -s "$ADB_SERIAL" pull /data/MRMConfig.json "./$DT/$AVS_DIR/MRMConfig.json"
adb -s "$ADB_SERIAL" pull /data/ReggaeMediaPlayer.json "./$DT/$AVS_DIR/ReggaeMediaPlayer.json"

# Capture all .json and .conf files
echo -e "${GREEN}Capture all .json and .conf files${NC}"
# Find and pull .json files
while IFS= read -r -d '' file; do
  echo "Attempting to pull file: $file to $JSON_DIR"
  adb -s "$ADB_SERIAL" pull "$file" "$JSON_DIR/"
done < <(adb -s "$ADB_SERIAL" exec-out "find / -maxdepth 4 -name '*.json' -print0")

# Find and pull .conf files
while IFS= read -r -d '' file; do
  echo "Attempting to pull file: $file to $CONF_DIR"
  adb -s "$ADB_SERIAL" pull "$file" "$CONF_DIR/"
done < <(adb -s "$ADB_SERIAL" exec-out "find / -maxdepth 4 -name '*.conf' -print0")

# List the contents of the json and conf directories
ls -la "$JSON_DIR"
ls -la "$CONF_DIR"

# Compression log archive
echo -e "${GREEN}Compression log archive to ${DT}.zip${NC}"
if command -v zip &>/dev/null; then
  zip -r "${DT}.zip" "$DT"
elif command -v 7z &>/dev/null; then
  7z a "${DT}.zip" "$DT"
else
  echo -e "${YELLOW}Neither zip nor 7z found. Skipping compression.${NC}"
fi

echo -e "${GREEN}Log capture is DONE!!${NC}"
