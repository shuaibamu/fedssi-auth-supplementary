#!/bin/bash
# usage: run_tamarin.sh model.spthy   (needs tamarin-prover 1.10.0 and Maude 3.3.1 on PATH)
export LANG=C.UTF-8 LC_ALL=C.UTF-8
TAM=${TAMARIN:-tamarin-prover}
$TAM --prove "$1" > "${1%.spthy}.out" 2>&1
grep -E "^(  )?(executable_|P[0-9]_)[A-Za-z_]* \((exists-trace|all-traces)\): (verified|falsified|analysis incomplete)" "${1%.spthy}.out"
grep -E "processing time" "${1%.spthy}.out"
