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

**#Supporting files**
| Paper item | File |
|---|---|
| Table 5 (class to binary label) | `tables/table05_class_label_map.csv` |
| Tables 6-8 (performance, cross-validation, paired tests) | `tables/table06-08*.csv`, `results/test_results_full.json`, `cv_fold_scores_full.json`, `stats_tests_full.json` |
| Table 9, Figure 11 (per class, confusion matrices) | `tables/table09_per_class.csv`, `results/multiclass_and_family_results.json` |
| Table 10, Figure 12 (ablation) | `tables/table10_ablation.csv`, `results/ablation.json` |
| Table 11 (gas) | `tables/table11_gas.csv`, `results/gas_table.json` |
| Table 12, Figure 13 (live benchmark) | `tables/table12_live_benchmark.csv`, `results/bench_live.json` |
| Tables 13-15 (hold-out and transfer) | `tables/table13-15*.csv`, `results/harder_validation.json`, `cic_transfer.json`, `cic_controls.json` |
| Tables 16-17 (protocol and integrated tests) | `tables/table16-17*.csv`, `results/protocol_tests_*.json`, `integrated_*.json` |
| Table 18 (Tamarin results) | `formal/results_summary.csv`, `formal/*.out`, `formal/*.spthy` |
| 61-feature mapping between RT-IoT2022 and CIC-IDS2017 | `results/table_feature_mapping_61.csv` |
| Figure 8 (threshold sweep, calibration, scores) | `results/threshold_sweep_oof.json`, `threshold_calibration_seeds.json`, `test_scores_full.npz` ||

## Environment

Python 3.12 (`pip install -r requirements.txt`), Java 21, Node.js, and a LaTeX installation with TikZ/pgfplots for the figures. The symbolic verification needs Tamarin 1.10.0 and Maude 3.3.1 (`formal/README.md`). Hyperledger Besu 24.12.2 and solc-js 0.8.20 are installed by `scripts/setup_environment.sh`. Paths are relative to the repository root; set `FEDSSI_ROOT` to override, and `BESU_BIN` to point to a different Besu binary.

The Besu experiments were run on a host with one virtual CPU and 4 GB of RAM (`results/host.json`); throughput and latency in `results/bench_live.json` depend on this host, whereas gas values are deterministic.






## License

MIT (see `LICENSE`).
