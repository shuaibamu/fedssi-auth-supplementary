"""Summarise the Tamarin outputs (*.out) as results_summary.csv (Table 18 of the paper)."""
import csv, os, re
here = os.path.dirname(os.path.abspath(__file__))
P = ['P1_agreement_with_honest_holder', 'P2_injective_agreement', 'P3_credential_issued_to_presenter', 'P4_issuer_trusted_by_administrator', 'P5_token_origin']
LAB = [('main', 'Full protocol (Algorithm 1)'), ('ctl_no_holder_key_check', 'Without the holderKey check (step 13)'), ('ctl_no_holder_signature', 'Without the holder signature (step 15)'),
       ('ctl_no_channel_binding', 'Without the channel identifier in ph'), ('ctl_no_challenge_binding', 'Without any challenge binding (ph constant)'), ('ctl_session_reusable', 'Challenge not consumed on acceptance')]
rows = []
for k, lab in LAB:
    txt = open(os.path.join(here, f'{k}.out')).read()
    res = {m.group(1): m.group(2) for m in re.finditer(r'^\s*((?:executable_|P\d_)[A-Za-z_]*) \((?:exists-trace|all-traces)\): (verified|falsified)', txt, re.M)}
    sec = re.search(r'processing time: ([\d.]+)s', txt).group(1)
    rows.append([lab] + ['proved' if res[p] == 'verified' else 'attack' for p in P] + [sec])
with open(os.path.join(here, 'results_summary.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['model', 'P1', 'P2', 'P3', 'P4', 'P5', 'seconds']); w.writerows(rows)
print(open(os.path.join(here, 'results_summary.csv')).read())
