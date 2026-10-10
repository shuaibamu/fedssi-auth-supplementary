cd "$(dirname "$0")/.."
while [ ! -f logs/chain4.done ]; do sleep 5; done
python3 scripts/s9_gas_and_tests.py > logs/s9.log 2>&1
echo done > logs/chain5.done
