#!/bin/sh
# Downloads Hyperledger Besu 24.12.2 and installs the Solidity compiler (solc-js 0.8.20). Requires Java 21 and Node.js.
set -e
cd "$(dirname "$0")/.."
curl -sSL -o besu.tar.gz https://github.com/besu-eth/besu/releases/download/24.12.2/besu-24.12.2.tar.gz
tar xzf besu.tar.gz -C "$HOME" && rm besu.tar.gz        # -> ~/besu-24.12.2/bin/besu (override with BESU_BIN)
(cd compile && npm install)                              # solc 0.8.20 as pinned in compile/package.json
node compile/compile.js                                  # writes contracts/compiled.json from contracts/FedSSIContracts.sol
