import sys, json, time; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import protocol as P
from common import save
NOW = int(time.time()); reg = P.MirrorRegistry(); docs = P.DocStore(); reg.register_domain('D_R', 'adminR')
iss = P.Issuer('did:ex:issuerA', 'D_I', reg, docs); reg.create_list('list-A', iss.admin); reg.add_assertion('D_R', 'D_I', iss.did, P.SCHEMA_HASH, NOW + 99, 'adminR', NOW)
h = P.Holder('did:ex:sensor1', reg, docs); h.request_credential(iss, dict(schema=P.SCHEMA, deviceClass='air-quality', maxBitrate='1kbps', validUntil=NOW + 999, listId='list-A', manufacturer='m', serial='s', postcode='p'))
gw = P.Gateway('gw-1', 'D_R', reg, docs); c = gw.challenge(NOW); vp = h.present(c, 'read:air', b'tls-exporter'); tok, why, T = gw.authenticate(vp, c['sid'], b'tls-exporter', 'read:air', now=NOW)
req = len(json.dumps(dict(did=h.did, scope='read:air', D_R='D_R')).encode()); ch = len(json.dumps(c).encode())
vpb = len(P.serialize_proof(vp['proof'])) + len(json.dumps(vp['revealed']).encode()) + len(vp['sigma']) + len(vp['issuer'].encode())
tk = len(json.dumps(tok['body'], sort_keys=True).encode()) + len(tok['sig'])
out = dict(request_bytes=req, challenge_bytes=ch, presentation_bytes=vpb, proof_bytes=len(P.serialize_proof(vp['proof'])), token_bytes=tk, auth_total_bytes=req + ch + vpb + tk, accept=why,
           calldata=dict(registerDID=4 + 2 * 32, revokeIndex=4 + 2 * 32, addTrustAssertion=4 + 5 * 32, createList=4 + 32))
save(out, 'message_sizes.json'); print(out)
