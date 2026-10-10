cd "$(dirname "$0")/.."
python3 scripts/s4_threshold_calib.py > logs/s4.log 2>&1
python3 scripts/s7b_cic_controls.py > logs/s7b.log 2>&1
echo done > logs/chain3.done
