cd "$(dirname "$0")/.."
while [ ! -f logs/chain1.done ]; do sleep 5; done
python3 scripts/s7_cic.py > logs/s7.log 2>&1
echo done > logs/chain2.done
