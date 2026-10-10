import os
"""ChainRegistry: same interface as protocol.MirrorRegistry but backed by the deployed Solidity contracts (web3)."""
import json, time
from web3 import Web3
from eth_account import Account
COMPILED = json.load(open(os.path.join(os.environ.get('FEDSSI_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'contracts', 'compiled.json')))
K = lambda s: Web3.keccak(text=s)
class ChainRegistry:
    def __init__(self, w3, owner='owner'):
        self.w3 = w3; self.cid = w3.eth.chain_id; self._acct = {}; self.pending = []; self.gas_log = []; self.owner = owner; self.deploy_gas = {}
        self.c = {}
        for name in ('DIDRegistry', 'RevocationList', 'TrustAnchorRegistry'):
            C = w3.eth.contract(abi=COMPILED[name]['abi'], bytecode=COMPILED[name]['evm']['bytecode']['object'])
            r = self._send(self.acct(owner), C.constructor(), wait=True); self.deploy_gas[name] = r.gasUsed
            self.c[name] = w3.eth.contract(address=r.contractAddress, abi=COMPILED[name]['abi'])
    def acct(self, name):
        if name not in self._acct: self._acct[name] = Account.from_key(Web3.keccak(text='fedssi-acct-' + name))
        return self._acct[name]
    def _send(self, acct, fn, wait=True, label=None):
        nonce = self.w3.eth.get_transaction_count(acct.address, 'pending')
        try: gas = int(fn.estimate_gas({'from': acct.address}) * 1.3) + 5000
        except Exception as e: raise PermissionError(str(e)[:120])
        tx = fn.build_transaction({'from': acct.address, 'nonce': nonce, 'gas': gas, 'gasPrice': 0, 'chainId': self.cid})
        h = self.w3.eth.send_raw_transaction(acct.sign_transaction(tx).raw_transaction)
        if not wait: self.pending.append((h, label)); return h
        r = self.w3.eth.wait_for_transaction_receipt(h, timeout=120)
        if r.status != 1: raise PermissionError('reverted')
        if label: self.gas_log.append((label, r.gasUsed))
        return r
    def flush(self):
        for h, label in self.pending:
            r = self.w3.eth.wait_for_transaction_receipt(h, timeout=180)
            if r.status != 1: raise PermissionError('reverted')
            if label: self.gas_log.append((label, r.gasUsed))
        self.pending = []
    # --- writes (names as in MirrorRegistry)
    def register_did(self, did, doc_hash, controller, wait=False): self._send(self.acct(controller), self.c['DIDRegistry'].functions.registerDID(K(did), doc_hash), wait=wait, label='registerDID')
    def deactivate_did(self, did, sender): self.flush(); self._send(self.acct(sender), self.c['DIDRegistry'].functions.deactivateDID(K(did)), wait=True, label='deactivateDID')
    def register_domain(self, dom, admin): self._send(self.acct(self.owner), self.c['TrustAnchorRegistry'].functions.registerDomain(K(dom), self.acct(admin).address), wait=True, label='registerDomain')
    def add_assertion(self, vdom, idom, issuer_did, schema_hash, exp, sender, now):
        self._send(self.acct(sender), self.c['TrustAnchorRegistry'].functions.addTrustAssertion(K(vdom), K(idom), K(issuer_did), schema_hash, int(exp)), wait=True, label='addTrustAssertion')
    def _aid(self, vdom, idom, issuer_did, schema_hash): return Web3.solidity_keccak(['bytes32'] * 4, [K(vdom), K(idom), K(issuer_did), schema_hash])
    def revoke_assertion(self, vdom, idom, issuer_did, schema_hash, sender):
        self._send(self.acct(sender), self.c['TrustAnchorRegistry'].functions.revokeTrustAssertion(self._aid(vdom, idom, issuer_did, schema_hash)), wait=True, label='revokeTrustAssertion')
    def create_list(self, lid, owner): self._send(self.acct(owner), self.c['RevocationList'].functions.createList(K(lid)), wait=True, label='createList')
    def revoke_index(self, lid, idx, sender): self._send(self.acct(sender), self.c['RevocationList'].functions.revokeIndex(K(lid), int(idx)), wait=True, label='revokeIndex')
    # --- reads used by the gateway (eth_call)
    def resolve_dids(self, did_h, did_i):
        self.flush()
        a, b, c, d = self.c['DIDRegistry'].functions.resolveDIDs(K(did_h), K(did_i)).call(); return (bytes(a), bool(b)), (bytes(c), bool(d))
    def is_trusted(self, vdom, idom, issuer_did, schema_hash, now):
        self.flush(); return bool(self.c['TrustAnchorRegistry'].functions.isTrusted(K(vdom), K(idom), K(issuer_did), schema_hash).call())
    def is_revoked(self, lid, idx):
        self.flush(); return bool(self.c['RevocationList'].functions.isRevoked(K(lid), int(idx)).call())
