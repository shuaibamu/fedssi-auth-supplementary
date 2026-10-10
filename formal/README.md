# Symbolic verification of the protocol core (Tamarin)

`fedssi_auth.spthy.in` is the model of Algorithm 1 (steps 1-15 and 17-18) under a Dolev-Yao adversary; `make_variants.py` generates `main.spthy` (full protocol) and five negative controls that each remove one element. The five properties P1-P5 and two executability lemmas are stated at the end of the model.

| Variant | Removed element | Expected result |
|---|---|---|
| `main` | none | all lemmas verified |
| `ctl_no_holder_key_check` | `holderKey = h(pk)` check (step 13) | P3 falsified |
| `ctl_no_holder_signature` | holder signature (step 15) | P1, P2 falsified |
| `ctl_no_channel_binding` | channel identifier in the presentation header | P1, P2 falsified |
| `ctl_no_challenge_binding` | all challenge binding (constant header) | P1, P2 falsified |
| `ctl_session_reusable` | consumption of the challenge on acceptance | P2 falsified |

## Tools

Tamarin prover 1.10.0 (https://github.com/tamarin-prover/tamarin-prover/releases/tag/1.10.0, Linux x86-64 archive) and Maude 3.3.1 (https://github.com/maude-lang/Maude/releases/tag/Maude3.3.1). Put both on `PATH` (the `maude` binary must be named `maude`, and `MAUDE_LIB` must point to its directory). Set `TAMARIN=/path/to/tamarin-prover` if the binary is not on `PATH`.

## Run

`sh run_all.sh` regenerates the variants, runs Tamarin on each (6-13 s per model on one virtual CPU), and writes `results_summary.csv`. The committed `*.out` files are the logs of the runs reported in the paper.

## Scope

Symbolic model, perfect cryptography; BBS+ is abstracted (proofs need the issuer's signature, are bound to the presentation header, and verify only against the issuer key). Timing (expiry, revocation freshness), compromised device software that signs on request, issuer and administrator key compromise, zero-knowledge and unlinkability of the proofs, and the traffic gate are outside the model.
