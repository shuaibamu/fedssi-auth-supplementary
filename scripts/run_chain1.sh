cd "$(dirname "$0")/.."
python3 scripts/s2b_models_cv_full.py > logs/s2b.log 2>&1
python3 scripts/s3_stats.py _full > logs/s3_full.log 2>&1
python3 scripts/s4_threshold_calib.py > logs/s4.log 2>&1
python3 scripts/s5_multiclass.py > logs/s5.log 2>&1
python3 scripts/s6_harder.py > logs/s6.log 2>&1
echo done > logs/chain1.done
