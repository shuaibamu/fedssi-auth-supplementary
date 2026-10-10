"""Generate the Tamarin model and the five negative-control variants from the template fedssi_auth.spthy.in.
Usage: python make_variants.py   (writes main.spthy and ctl_*.spthy next to this file)"""
import os
here = os.path.dirname(os.path.abspath(__file__))
tpl = open(os.path.join(here, 'fedssi_auth.spthy.in')).read()
base = dict(STV='St_V', PH_H="h(<n, Vid, sid, $S, $D, ch>)", PH_V="h(<n, $V, sid, $S, $D, ch>)", SIG_OUT='sg',
            HK_CHECK="Eq(hk, h(pkDoc)),", SIG_CHECK="Eq(verify(sg, h(<ph, pi, <'cred', hk, $C, $I>>), pkDoc), true),")
variants = {
    'main': {},                                                                                      # full protocol
    'ctl_no_holder_key_check': dict(HK_CHECK=''),                                                    # step 13 without holderKey = h(pk) check
    'ctl_no_holder_signature': dict(SIG_CHECK='', SIG_OUT="'none'"),                                 # step 15 removed
    'ctl_no_channel_binding': dict(PH_H="h(<n, Vid, sid, $S, $D>)", PH_V="h(<n, $V, sid, $S, $D>)"),  # ph without channel identifier
    'ctl_no_challenge_binding': dict(PH_H="'none'", PH_V="'none'"),                                  # ph constant
    'ctl_session_reusable': dict(STV='!St_V'),                                                       # challenge not consumed on acceptance
}
for name, over in variants.items():
    v = dict(base); v.update(over); t = tpl
    for k, val in v.items(): t = t.replace(f'@@{k}@@', val)
    if name != 'main': t = t.replace('theory FedSSI_Auth', 'theory FedSSI_Auth_' + name.replace('ctl_', 'Control_'))
    open(os.path.join(here, f'{name}.spthy'), 'w').write(t)
print('written:', ', '.join(f'{n}.spthy' for n in variants))
