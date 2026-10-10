import sys, json, time, secrets; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import protocol as P, bbs
from common import RES, save
NOW = int(time.time())
def build(reg=None):
    reg = reg or P.MirrorRegistry(); docs = P.DocStore()
    reg.register_domain('D_R', 'adminR'); reg.register_domain('D_I', 'adminI')
    issuer = P.Issuer('did:ex:issuerA', 'D_I', reg, docs)
    reg.create_list('list-A', issuer.admin)
    reg.add_assertion('D_R', 'D_I', issuer.did, P.SCHEMA_HASH, NOW + 3600, 'adminR', NOW - 10)
    base = dict(schema=P.SCHEMA, deviceClass='air-quality', maxBitrate='1kbps', validUntil=NOW + 86400, listId='list-A',
                manufacturer='Helsinki Sensors Oy', serial='AQ-2024-04188', postcode='00100')
    holder = P.Holder('did:ex:sensor1', reg, docs); holder.request_credential(issuer, base)
    gw = P.Gateway('gw-1', 'D_R', reg, docs, scorer=None)
    return reg, docs, issuer, holder, gw, base
def session(gw, holder, ch_id=b'tls-exporter-1', scope='read:air', vc=None, signer=None, now=None, present_challenge=None, auth_challenge_sid=None, channel_for_gw=None):
    c = gw.challenge(now or NOW)
    vp = holder.present(present_challenge or c, scope, ch_id, vc=vc, signer=signer)
    return gw.authenticate(vp, auth_challenge_sid or c['sid'], channel_for_gw or ch_id, scope, now=now or NOW), vp, c
results = []
def case(name, kind, expect, fn):
    t = time.time(); got = fn(); ok = (got == expect)
    results.append(dict(test=name, kind=kind, expected=expect, observed=got, passed=ok, ms=round((time.time() - t) * 1000, 1)))
    print(('PASS ' if ok else 'FAIL ') + f'{name:62s} expected={expect:28s} observed={got}')
def run(reg_factory=None, label='mirror'):
    reg, docs, issuer, holder, gw, base = build(reg_factory() if reg_factory else None)
    # --- positive
    def p1(): (tok, why, T), vp, c = session(gw, holder); ok, w = P.rp_verify_token(tok, gw.pk, 'D_R', 'read:air', NOW + 1) if tok else (False, why); return 'accept' if ok else why
    case('P1 valid credential, honest holder, fresh challenge', 'positive', 'accept', p1)
    def p2():  # selective disclosure: hidden attributes are not in the presentation
        (tok, why, T), vp, c = session(gw, holder); return 'hidden_not_sent' if all(k not in vp['revealed'] for k in ('manufacturer', 'serial', 'postcode')) else 'leak'
    case('P2 undisclosed attributes absent from presentation', 'positive', 'hidden_not_sent', p2)
    # --- holder binding
    atk = P.Holder('did:ex:attacker', reg, docs)              # attacker registers a DID with its own key
    def n1():  # victim's full credential used with the attacker's registered DID/key
        (tok, why, T), vp, c = session(gw, atk, vc=holder.vc); return why
    case('N1 victim credential + attacker-registered DID/key (holder binding)', 'negative', 'holder_binding_mismatch', n1)
    def n1b():  # attacker claims victim DID but signs with its own key
        (tok, why, T), vp, c = session(gw, holder, signer=atk.sk); return why
    case('N1b victim DID + credential, attacker signature key', 'negative', 'holder_signature_invalid', n1b)
    def n1c():  # issuance without proof of possession
        try: issuer.issue(atk.pk, b'\0' * 64, P.H(b'issue-pop', issuer.did, b'n', atk.pk), dict(base, nonce='n')); return 'issued'
        except PermissionError as e: return 'pop_refused'
    case('N1c issuance without holder proof-of-possession', 'negative', 'pop_refused', n1c)
    # --- freshness / replay / relay
    def n2():  # replay a previously used presentation under a new challenge
        c1 = gw.challenge(NOW); vp = holder.present(c1, 'read:air', b'tls-exporter-1'); gw.authenticate(vp, c1['sid'], b'tls-exporter-1', 'read:air', now=NOW)
        c2 = gw.challenge(NOW); return gw.authenticate(vp, c2['sid'], b'tls-exporter-1', 'read:air', now=NOW)[1]
    case('N2 replay of earlier presentation in a new session', 'negative', 'bbs_proof_invalid', n2)
    def n2b():  # same session id used twice
        c = gw.challenge(NOW); vp = holder.present(c, 'read:air', b'ch'); gw.authenticate(vp, c['sid'], b'ch', 'read:air', now=NOW); return gw.authenticate(vp, c['sid'], b'ch', 'read:air', now=NOW)[1]
    case('N2b second use of a consumed session challenge', 'negative', 'sid_unknown_or_reused', n2b)
    def n3():  # presentation relayed to a different gateway
        gw2 = P.Gateway('gw-2', 'D_R', reg, docs); c1 = gw.challenge(NOW); vp = holder.present(c1, 'read:air', b'ch'); c2 = gw2.challenge(NOW)
        return gw2.authenticate(vp, c2['sid'], b'ch', 'read:air', now=NOW)[1]
    case('N3 relay to a different verifier gateway', 'negative', 'bbs_proof_invalid', n3)
    def n4():  # relay over a different transport channel
        c = gw.challenge(NOW); vp = holder.present(c, 'read:air', b'channel-A'); return gw.authenticate(vp, c['sid'], b'channel-B', 'read:air', now=NOW)[1]
    case('N4 relay over a different channel (channel binding)', 'negative', 'bbs_proof_invalid', n4)
    def n4b():  # scope escalation: presentation made for one scope, gateway session for another
        c = gw.challenge(NOW); vp = holder.present(c, 'read:air', b'ch'); return gw.authenticate(vp, c['sid'], b'ch', 'admin:all', now=NOW)[1]
    case('N4b scope substitution', 'negative', 'bbs_proof_invalid', n4b)
    def n5():  # tampered disclosed claim
        c = gw.challenge(NOW); vp = holder.present(c, 'read:air', b'ch'); vp['revealed'] = dict(vp['revealed'], deviceClass='medical-pump'); return gw.authenticate(vp, c['sid'], b'ch', 'read:air', now=NOW)[1]
    case('N5 tampered disclosed claim', 'negative', 'bbs_proof_invalid', n5)
    h5 = P.Holder('did:ex:sensor5', reg, docs); h5.request_credential(issuer, dict(base, validUntil=NOW - 5))   # issuer still trusted, credential already past validUntil
    def n6(): (tok, why, T), vp, c = session(gw, h5); return why
    case('N6 expired credential', 'negative', 'credential_expired', n6)
    def n6b(): (tok, why, T), vp, c = session(gw, holder, now=NOW + 40); return why
    case('N6b stale challenge (older than permitted skew)', 'negative', 'stale_challenge', lambda: (lambda c: (lambda vp: gw.authenticate(vp, c['sid'], b'ch', 'read:air', now=NOW + 40))(holder.present(c, 'read:air', b'ch')))(gw.challenge(NOW))[1])
    # --- status & trust
    h2 = P.Holder('did:ex:sensor2', reg, docs); h2.request_credential(issuer, base)
    def n7(): reg.revoke_index('list-A', h2.vc['attrs']['revIdx'], issuer.admin); (tok, why, T), vp, c = session(gw, h2); return why
    case('N7 revoked credential (status list bit set)', 'negative', 'revoked', n7)
    other = P.Issuer('did:ex:issuerB', 'D_I', reg, docs, admin='0xissuerB'); reg.create_list('list-B', '0xissuerB')
    h3 = P.Holder('did:ex:sensor3', reg, docs); h3.request_credential(other, dict(base, listId='list-B'))
    case('N8 issuer without trust assertion', 'negative', 'untrusted_issuer', lambda: session(gw, h3)[0][1])
    def n8b():
        reg.add_assertion('D_R', 'D_I', other.did, P.SCHEMA_HASH, NOW - 1, 'adminR', NOW - 100); return session(gw, h3, now=NOW)[0][1]
    case('N8b expired trust assertion', 'negative', 'untrusted_issuer', n8b)
    def n8c():
        iss = P.Issuer('did:ex:issuerC', 'D_I', reg, docs, admin='0xissuerC'); reg.create_list('list-C', '0xissuerC')
        reg.add_assertion('D_R', 'D_I', iss.did, P.SCHEMA_HASH, NOW + 3600, 'adminR', NOW - 10)
        hh = P.Holder('did:ex:sensorC', reg, docs); hh.request_credential(iss, dict(base, listId='list-C'))
        reg.revoke_assertion('D_R', 'D_I', iss.did, P.SCHEMA_HASH, 'adminR'); return session(gw, hh)[0][1]
    case('N8c revoked trust assertion', 'negative', 'untrusted_issuer', n8c)
    def n8d():
        try: reg.add_assertion('D_R', 'D_I', 'did:ex:evil', P.SCHEMA_HASH, NOW + 99, 'attacker', NOW); return 'written'
        except PermissionError: return 'write_refused'
    case('N8d trust assertion written by non-admin (T4)', 'negative', 'write_refused', n8d)
    h4 = P.Holder('did:ex:sensor4', reg, docs); h4.request_credential(issuer, base)
    def n9(): reg.deactivate_did('did:ex:sensor4', '0xholder'); return session(gw, h4)[0][1]
    case('N9 deactivated holder DID', 'negative', 'holder_inactive_or_unknown', n9)
    def n10():
        docs.docs['did:ex:sensor1'] = dict(holder.doc, ed25519PublicKey=atk.pk.hex()); r = session(gw, holder)[0][1]; docs.docs['did:ex:sensor1'] = holder.doc; return r
    case('N10 DID document altered off-chain (hash mismatch)', 'negative', 'doc_hash_mismatch', n10)
    def n11():  # credential forged by a key that is not the registered issuer key
        fsk, fpk = bbs.keygen(); a = dict(holder.vc['attrs']); forged = dict(attrs=a, sig=bbs.sign(fsk, P.attr_scalars(a)), issuer=issuer.did)
        return session(gw, holder, vc=forged)[0][1]
    case('N11 credential forged under an unregistered issuer key', 'negative', 'bbs_proof_invalid', n11)
    # --- relying-party token checks
    (tok, why, T), vp, c = session(gw, holder); 
    case('N12 token presented to a different audience', 'negative', 'wrong_audience', lambda: P.rp_verify_token(tok, gw.pk, 'D_OTHER', 'read:air', NOW + 1)[1])
    case('N12b expired token', 'negative', 'token_expired', lambda: P.rp_verify_token(tok, gw.pk, 'D_R', 'read:air', NOW + 600)[1])
    case('N12c token with altered scope', 'negative', 'bad_signature', lambda: P.rp_verify_token(dict(tok, body=dict(tok['body'], scope='admin:all')), gw.pk, 'D_R', 'admin:all', NOW + 1)[1])
    case('N12d token for a different scope than the resource requires', 'negative', 'scope_mismatch', lambda: P.rp_verify_token(tok, gw.pk, 'D_R', 'write:air', NOW + 1)[1])
    case('N12e token of a revoked (behaviourally flagged) session', 'negative', 'session_revoked', lambda: P.rp_verify_token(tok, gw.pk, 'D_R', 'read:air', NOW + 1, revoked_sids={tok['body']['sid']})[1])
    npass = sum(r['passed'] for r in results); print(f'{label}: {npass}/{len(results)} passed')
    save(dict(label=label, results=results), f'protocol_tests_{label}.json'); return results
if __name__ == '__main__': run()
