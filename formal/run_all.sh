#!/bin/bash
# Runs the full model and the five negative controls; needs tamarin-prover 1.10.0 and Maude 3.3.1 on PATH
# (see README.md). Results are written to <model>.out and summarised in results_summary.csv.
cd "$(dirname "$0")"
python3 make_variants.py
for m in main ctl_no_holder_key_check ctl_no_holder_signature ctl_no_channel_binding ctl_no_challenge_binding ctl_session_reusable; do
  echo "== $m"; ./run_tamarin.sh $m.spthy
done
python3 summarise.py
