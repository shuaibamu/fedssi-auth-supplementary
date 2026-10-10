# FedSSI-Auth: supplementary material

Code, contracts, configuration, results and logs for the paper *FedSSI-Auth: Cross-Domain Federated Self-Sovereign Identity Authentication on Blockchain with Behavioural ML Defence for IoT*.



## Contents

| Path | Content |
|---|---|

| `scripts/bbs.py`, `scripts/protocol.py` | BBS+ prototype (BLS12-381; research code, not an audited library) and the 19-step protocol with the in-memory and on-chain registries |
| `contracts/` | `FedSSIContracts.sol` (DIDRegistry, RevocationList, TrustAnchorRegistry) and the compiled ABI/bytecode; one source is used for every measurement in the paper |
| `compile/` | Solidity compiler setup (solc 0.8.20, optimizer 200 runs, EVM version london) |
| `formal/` | Tamarin model of the protocol core (Algorithm 1, steps 1-15 and 17-18), five negative-control variants, run logs and `results_summary.csv` (Table 18); see `formal/README.md` |
| `config/` | Besu genesis and node configuration (QBFT, block period 2 s) used for the 1-, 4- and 7-validator networks; Algorithm 1 text |
| `results/` | All stored results: label map, split indices, fold scores, test scores and raw predicted probabilities (`*.npz`), threshold sweep (`threshold_sweep_oof.json`), trained Random Forest (`rf_binary_fulltrain.joblib`), statistics, hold-out, transfer, gas, benchmark and integrated-test outputs, 61-feature mapping |

|

## Environment

Python 3.12 (`pip install -r requirements.txt`), Java 21, Node.js, and a LaTeX installation with TikZ/pgfplots for the figures. The symbolic verification needs Tamarin 1.10.0 and Maude 3.3.1 (`formal/README.md`). Hyperledger Besu 24.12.2 and solc-js 0.8.20 are installed by `scripts/setup_environment.sh`. Paths are relative to the repository root; set `FEDSSI_ROOT` to override, and `BESU_BIN` to point to a different Besu binary.

The Besu experiments were run on a host with one virtual CPU and 4 GB of RAM (`results/host.json`); throughput and latency in `results/bench_live.json` depend on this host, whereas gas values are deterministic.






## License

MIT (see `LICENSE`).
