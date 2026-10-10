"""One-validator QBFT network: (1) gas of EVERY function of the released contracts, (2) protocol tests on the live contracts."""
import sys, time, json, statistics; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
from besu_net import Net
from chain_registry import ChainRegistry, K
from web3 import Web3
t0 = time.time()
def log(m): print(f'[{time.time()-t0:6.0f}s] {m}', flush=True)
net = Net(1, period=1); w3 = net.start(); log('1-validator QBFT network up, block ' + str(w3.eth.block_number))
try:
    reg = ChainRegistry(w3); log(f'deployed: {reg.deploy_gas}')
    G = {}
    def rec(label, r): G.setdefault(label, []).append(r)
    reg.register_domain('D_R', 'adminR'); reg.register_domain('D_I', 'adminI')
    # registerDID x20 (distinct DIDs): constant cost?
    for i in range(20): reg.register_did(f'did:ex:gas{i}', Web3.keccak(text=f'doc{i}'), 'ctrl', wait=False)
    reg.flush()
    # gas log by label
    for lab, g in reg.gas_log: rec(lab, g)
    reg.gas_log.clear()
    dc = reg.c['DIDRegistry']; ctrl = reg.acct('ctrl')
    r = reg._send(ctrl, dc.functions.updateDIDDocument(K('did:ex:gas0'), Web3.keccak(text='new')), label='updateDIDDocument'); 
    r = reg._send(ctrl, dc.functions.deactivateDID(K('did:ex:gas1')), label='deactivateDID')
    reg.create_list('list-A', 'iss')
    reg.revoke_index('list-A', 5, 'iss'); reg.revoke_index('list-A', 6, 'iss'); reg.revoke_index('list-A', 1000, 'iss')
    reg.add_assertion('D_R', 'D_I', 'did:ex:issuerA', Web3.keccak(text='schema'), int(time.time()) + 3600, 'adminR', 0)
    reg.revoke_assertion('D_R', 'D_I', 'did:ex:issuerA', Web3.keccak(text='schema'), 'adminR')
    for lab, g in reg.gas_log: rec(lab, g)
    # label revokeIndex variants explicitly: 1st (new word, zero->nonzero), 2nd (same word), 3rd (new word)
    rv = [g for lab, g in reg.gas_log if lab == 'revokeIndex']; G.pop('revokeIndex'); G['revokeIndex_first_bit_in_word'] = [rv[0], rv[2]]; G['revokeIndex_bit_in_populated_word'] = [rv[1]]
    # views: execution gas via estimateGas (as if sent in a tx) and call latency
    views = {'resolveDID': dc.functions.resolveDID(K('did:ex:gas0')), 'resolveDIDs': dc.functions.resolveDIDs(K('did:ex:gas0'), K('did:ex:gas1')),
             'isRevoked': reg.c['RevocationList'].functions.isRevoked(K('list-A'), 5),
             'isTrusted': reg.c['TrustAnchorRegistry'].functions.isTrusted(K('D_R'), K('D_I'), K('did:ex:issuerA'), Web3.keccak(text='schema'))}
    V = {}
    for nme, fn in views.items():
        eg = fn.estimate_gas({'from': ctrl.address}); ts = []
        for _ in range(100): t = time.perf_counter(); fn.call(); ts.append((time.perf_counter() - t) * 1000)
        V[nme] = dict(estimate_gas_if_sent=eg, call_ms_median=statistics.median(ts), call_ms_p95=sorted(ts)[94])
    out = dict(deploy_gas=reg.deploy_gas, tx_gas={k: dict(n=len(v), min=min(v), max=max(v), median=statistics.median(v)) for k, v in G.items()}, views=V,
               solc='0.8.20 optimizer 200 runs, evmVersion london', evm='Hyperledger Besu 24.12.2 (QBFT, 1 validator)')
    save(out, 'gas_table.json'); log('gas: ' + json.dumps({k: v['median'] for k, v in out['tx_gas'].items()})); log('views: ' + json.dumps({k: (v['estimate_gas_if_sent'], round(v['call_ms_median'], 1)) for k, v in V.items()}))
    # ---- protocol tests against the live contracts (fresh deployment)
    import s8_protocol_tests as T
    reg2 = ChainRegistry(w3); res = T.run(lambda: reg2, label='chain'); log(f'chain protocol tests: {sum(r["passed"] for r in res)}/{len(res)}')
finally:
    net.stop()
log('DONE')
