cd "$(dirname "$0")/.."
python3 scripts/s9_gas_and_tests.py > logs/s9.log 2>&1
python3 scripts/s11_integrated.py > logs/s11.log 2>&1
python3 scripts/s10_bench.py > logs/s10.log 2>&1
echo done > logs/chain4.done
