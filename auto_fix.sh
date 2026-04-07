#!/bin/bash
echo "🚀 [AUTO_FIX] Starting Autonomous Recovery Sequence..." > /home/aqtobe-hub/ProtoQol/api/final_report.log
pkill -9 -f python3 || true
pkill -9 -f uvicorn || true
sleep 2

# Start the Engine
nohup python3 /home/aqtobe-hub/ProtoQol/api/main.py >> /home/aqtobe-hub/ProtoQol/api/final_report.log 2>&1 &
sleep 5

# Trigger the Sanity Trial
echo "🧪 [AUTO_FIX] Launching AI Council Sanity Audit..." >> /home/aqtobe-hub/ProtoQol/api/final_report.log
python3 /home/aqtobe-hub/ProtoQol/final_sanity_test.py >> /home/aqtobe-hub/ProtoQol/api/final_report.log 2>&1

echo "🏁 [AUTO_FIX] FINISHED. Result is ready for Alikhan." >> /home/aqtobe-hub/ProtoQol/api/final_report.log
