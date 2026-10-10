"""FedSSI-Auth revised protocol (Revision 2): holder-key binding, challenge/verifier/channel binding,
gateway-measured traffic features, short-lived bound tokens.  Real BBS+ (bbs.py) + Ed25519 (cryptography)."""
import hashlib, json, os, time, secrets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from py_arkworks_bls12381 import G2Point
import bbs

def H(*parts):
    h = hashlib.sha256()
    for p in parts:
        b = p if isinstance(p, bytes) else str(p).encode(); h.update(len(b).to_bytes(4, 'big') + b)
    return h.digest()
def raw_pk(sk): return sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
def ed_verify(pk_bytes, sig, msg):
    try: Ed25519PublicKey.from_public_bytes(pk_bytes).verify(sig, msg); return True
    except (InvalidSignature, ValueError): return False

SCHEMA = 'AirQualitySensorCredential-v1'
SCHEMA_HASH = H(SCHEMA)
ATTR_ORDER = ['schema', 'deviceClass', 'maxBitrate', 'validUntil', 'listId', 'revIdx', 'holderKey', 'manufacturer', 'serial', 'postcode']
REVEAL_NAMES = ['schema', 'deviceClass', 'maxBitrate', 'validUntil', 'listId', 'revIdx', 'holderKey']
REVEAL_IDX = [ATTR_ORDER.index(n) + 1 for n in REVEAL_NAMES]
def attr_scalars(attrs): return [bbs.msg_scalar(n, attrs[n]) for n in ATTR_ORDER]
def key_binding(pk_bytes): return H(b'holderKey', pk_bytes).hex()

# ------------------------------------------------------------------ registry interfaces
class MirrorRegistry:
    """Python mirror of DIDRegistry / TrustAnchorRegistry / RevocationList read+write semantics (same logic as the Solidity sources)."""
    def __init__(self): self.dids, self.domains, self.assertions, self.revoked, self.listowner = {}, {}, {}, {}, {}
    def register_did(self, did, doc_hash, controller): assert did not in self.dids; self.dids[did] = dict(hash=doc_hash, controller=controller, active=True)
    def deactivate_did(self, did, sender): assert self.dids[did]['controller'] == sender; self.dids[did]['active'] = False
    def register_domain(self, dom, admin): self.domains[dom] = admin
    def add_assertion(self, verifier_dom, issuer_dom, issuer_did, schema_hash, exp, sender, now):
        if self.domains.get(verifier_dom) != sender: raise PermissionError('not domain admin')
        aid = H(verifier_dom, issuer_dom, issuer_did, schema_hash); assert aid not in self.assertions
        self.assertions[aid] = dict(valid_from=now, exp=exp, revoked=False); return aid
    def revoke_assertion(self, verifier_dom, issuer_dom, issuer_did, schema_hash, sender):
        if self.domains.get(verifier_dom) != sender: raise PermissionError('not domain admin')
        self.assertions[H(verifier_dom, issuer_dom, issuer_did, schema_hash)]['revoked'] = True
    def create_list(self, lid, owner): self.listowner[lid] = owner; self.revoked[lid] = set()
    def revoke_index(self, lid, idx, sender):
        if self.listowner[lid] != sender: raise PermissionError('not list owner')
        self.revoked[lid].add(int(idx))
    # --- read path used by the gateway (steps 7-12 of Algorithm 1)
    def resolve_dids(self, did_h, did_i):
        a, b = self.dids.get(did_h), self.dids.get(did_i)
        return ((a['hash'], a['active']) if a else (b'\0' * 32, False)), ((b['hash'], b['active']) if b else (b'\0' * 32, False))
    def is_trusted(self, verifier_dom, issuer_dom, issuer_did, schema_hash, now):
        a = self.assertions.get(H(verifier_dom, issuer_dom, issuer_did, schema_hash))
        return bool(a and not a['revoked'] and a['valid_from'] <= now < a['exp'])
    def is_revoked(self, lid, idx): return int(idx) in self.revoked.get(lid, set())

class DocStore:
    """off-chain DID-document store (wallet / IPFS stand-in); integrity is anchored by documentHash on chain"""
    def __init__(self): self.docs = {}
    def put(self, did, doc): self.docs[did] = doc
    def get(self, did): return self.docs.get(did)
def doc_hash(doc): return H(json.dumps(doc, sort_keys=True))

# ------------------------------------------------------------------ parties
class Issuer:
    def __init__(self, did, domain, registry, docs, admin='0xissuer'):
        self.did, self.domain = did, domain; self.sk, self.pk = bbs.keygen(); self.admin = admin
        self.doc = dict(id=did, domain=domain, bbsPublicKey=self.pk.to_compressed_bytes().hex()); docs.put(did, self.doc)
        registry.register_did(did, doc_hash(self.doc), admin); self.next_idx = 0
    def issue(self, holder_pk, pop_sig, pop_msg, attrs):
        """issuance requires proof-of-possession of the holder key over (issuer DID || nonce || key): binds the credential to pk_H"""
        if not ed_verify(holder_pk, pop_sig, pop_msg): raise PermissionError('holder proof-of-possession failed')
        if pop_msg != H(b'issue-pop', self.did, attrs['nonce'].encode(), holder_pk): raise PermissionError('PoP message mismatch')
        a = {k: v for k, v in attrs.items() if k != 'nonce'}; a['holderKey'] = key_binding(holder_pk)
        a['revIdx'] = self.next_idx; self.next_idx += 1
        return dict(attrs=a, sig=bbs.sign(self.sk, attr_scalars(a)), issuer=self.did)

class Holder:
    def __init__(self, did, registry, docs, admin='0xholder', register=True):
        self.did = did; self.sk = Ed25519PrivateKey.generate(); self.pk = raw_pk(self.sk); self.vc = None
        self.doc = dict(id=did, ed25519PublicKey=self.pk.hex())
        if register: docs.put(did, self.doc); registry.register_did(did, doc_hash(self.doc), admin)
    def request_credential(self, issuer, base_attrs):
        nonce = secrets.token_hex(8); msg = H(b'issue-pop', issuer.did, nonce.encode(), self.pk)
        self.vc = issuer.issue(self.pk, self.sk.sign(msg), msg, dict(base_attrs, nonce=nonce)); return self.vc
    def present(self, challenge, scope, channel_id, vc=None, signer=None):
        vc = vc or self.vc; ph = H(b'FedSSI-ph', challenge['n'], challenge['V_id'], challenge['sid'], str(challenge['ts']), channel_id, scope, challenge['D_R'])
        msgs = attr_scalars(vc['attrs']); proof = bbs.proof_gen(vc['sig'], msgs, REVEAL_IDX, ph)
        revealed = {n: vc['attrs'][n] for n in REVEAL_NAMES}
        transcript = H(ph, serialize_proof(proof), json.dumps(revealed, sort_keys=True))
        return dict(did=self.did, issuer=vc['issuer'], revealed=revealed, proof=proof, sigma=(signer or self.sk).sign(transcript), scope=scope)
def serialize_proof(p):
    return b''.join([x.to_compressed_bytes() for x in (p['Ap'], p['Abar'], p['d'])] + [int(p[k]).to_bytes(32, 'big') for k in ('c', 'e_hat', 'r2_hat', 'r3_hat', 'sp_hat')])

class Gateway:
    def __init__(self, V_id, domain_R, registry, docs, scorer=None, tau=0.5, window=3, token_ttl=60, skew=30, channel_secret=None):
        self.V_id, self.D_R, self.reg, self.docs, self.scorer, self.tau = V_id, domain_R, registry, docs, scorer, tau
        self.sk = Ed25519PrivateKey.generate(); self.pk = raw_pk(self.sk); self.challenges = {}; self.ttl = token_ttl; self.skew = skew
        self.sessions = {}; self.window = window; self.t = {}
    def challenge(self, now=None):
        now = now or int(time.time()); c = dict(n=secrets.token_hex(32), V_id=self.V_id, sid=secrets.token_hex(8), ts=now, D_R=self.D_R)
        self.challenges[c['sid']] = dict(c, used=False); return c
    def authenticate(self, vp, sid, channel_id, scope, flows=None, now=None, max_deviceclass=None):
        """returns (token|None, reason, timing dict).  flows: gateway-measured feature rows for H's recent completed flows (observation window)."""
        T = {}; now = now or int(time.time()); tt = time.perf_counter()
        def mark(k):
            nonlocal tt; T[k] = (time.perf_counter() - tt) * 1000; tt = time.perf_counter()
        ch = self.challenges.get(sid)
        if ch is None or ch['used']: return None, 'sid_unknown_or_reused', T
        ch['used'] = True                                           # single-use challenge
        if abs(now - ch['ts']) > self.skew: return None, 'stale_challenge', T
        ph = H(b'FedSSI-ph', ch['n'], ch['V_id'], ch['sid'], str(ch['ts']), channel_id, scope, ch['D_R'])   # recomputed by V, never taken from H
        rev = vp['revealed']; did_h, did_i = vp['did'], vp['issuer']; mark('prep')
        (h_hash, h_act), (i_hash, i_act) = self.reg.resolve_dids(did_h, did_i); mark('chain_resolveDIDs')
        if not h_act: return None, 'holder_inactive_or_unknown', T
        if not i_act: return None, 'issuer_inactive_or_unknown', T
        dh, di = self.docs.get(did_h), self.docs.get(did_i)
        if dh is None or di is None or doc_hash(dh) != h_hash or doc_hash(di) != i_hash: return None, 'doc_hash_mismatch', T
        pk_h = bytes.fromhex(dh['ed25519PublicKey']); pk_i = G2Point.from_compressed_bytes(bytes.fromhex(di['bbsPublicKey'])); mark('doc_check')
        if rev.get('schema') != SCHEMA: return None, 'schema', T
        trusted = self.reg.is_trusted(self.D_R, di['domain'], did_i, H(rev['schema']), now); mark('chain_isTrusted')
        if not trusted: return None, 'untrusted_issuer', T
        if self.reg.is_revoked(rev['listId'], rev['revIdx']): return None, 'revoked', T
        mark('chain_isRevoked')
        if int(rev['validUntil']) <= now: return None, 'credential_expired', T
        if max_deviceclass and rev['deviceClass'] not in max_deviceclass: return None, 'policy_deviceClass', T
        if rev['holderKey'] != key_binding(pk_h): return None, 'holder_binding_mismatch', T   # credential <-> holder key link
        mark('claims')
        scal = {ATTR_ORDER.index(n) + 1: bbs.msg_scalar(n, rev[n]) for n in REVEAL_NAMES}
        if not bbs.proof_verify(pk_i, vp['proof'], scal, ph): return None, 'bbs_proof_invalid', T
        mark('bbs_verify')
        transcript = H(ph, serialize_proof(vp['proof']), json.dumps(rev, sort_keys=True))
        if not ed_verify(pk_h, vp['sigma'], transcript): return None, 'holder_signature_invalid', T
        mark('holder_sig_verify')
        score = None
        if self.scorer is not None:
            if flows is None or len(flows) == 0:
                score = None                                          # no completed flow yet -> provisional (restricted) token
            else:
                score = float(max(self.scorer(flows))); 
                if score > self.tau: mark('classifier'); return None, 'behavioural_reject', T
        mark('classifier')
        exp = now + (self.ttl if score is not None else min(self.ttl, 15))
        body = dict(sub=did_h, aud=self.D_R, scope=scope, exp=exp, sid=sid, cnf=key_binding(pk_h), prov=score is None)
        tok = dict(body=body, sig=self.sk.sign(json.dumps(body, sort_keys=True).encode())); mark('token_sign')
        self.sessions[sid] = dict(did=did_h, token=tok, revoked=False, ch=channel_id)
        return tok, 'accept', T
    def monitor(self, sid, new_flows):
        """post-issuance re-check: score newly completed flows of the session; revoke the session on score >= tau"""
        s = self.sessions[sid]; 
        if s['revoked']: return 'already_revoked', None
        sc = float(max(self.scorer(new_flows))); 
        if sc > self.tau: s['revoked'] = True; return 'revoked', sc
        return 'ok', sc

def rp_verify_token(tok, gw_pk, aud, scope_needed, now, revoked_sids=()):
    b = tok['body']
    if not ed_verify(gw_pk, tok['sig'], json.dumps(b, sort_keys=True).encode()): return False, 'bad_signature'
    if b['aud'] != aud: return False, 'wrong_audience'
    if b['exp'] <= now: return False, 'token_expired'
    if b['scope'] != scope_needed: return False, 'scope_mismatch'
    if b['sid'] in revoked_sids: return False, 'session_revoked'
    return True, 'ok'
