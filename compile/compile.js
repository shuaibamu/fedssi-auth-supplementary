const solc = require('solc'); const fs = require('fs');
const src = fs.readFileSync(require('path').join(__dirname, '..', 'contracts', 'FedSSIContracts.sol'), 'utf8');
const input = { language: 'Solidity', sources: { 'FedSSIContracts.sol': { content: src } },
  settings: { optimizer: { enabled: true, runs: 200 }, evmVersion: 'london', outputSelection: { '*': { '*': ['abi', 'evm.bytecode.object'] } } } };
const out = JSON.parse(solc.compile(JSON.stringify(input)));
let bad = false; (out.errors || []).forEach(e => { console.error(e.formattedMessage); if (e.severity === 'error') bad = true; });
if (bad) process.exit(1);
fs.writeFileSync(require('path').join(__dirname, '..', 'contracts', 'compiled.json'), JSON.stringify(out.contracts['FedSSIContracts.sol'], null, 1));
console.log('compiled:', Object.keys(out.contracts['FedSSIContracts.sol']).join(', '), 'solc', solc.version());
