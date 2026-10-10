"""Regenerate the result tables of the paper (Tables 5-19) as CSV files from the stored results.
Usage: python scripts/make_tables.py   (writes to tables/)"""
import json, os, csv
import numpy as np, pandas as pd
ROOT = os.environ.get('FEDSSI_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES, OUT = os.path.join(ROOT, 'results'), os.path.join(ROOT, 'tables'); os.makedirs(OUT, exist_ok=True)
L = lambda n: json.load(open(os.path.join(RES, n)))
def w(name, header, rows):
    with open(os.path.join(OUT, name), 'w', newline='') as f: c = csv.writer(f); c.writerow(header); c.writerows(rows)
    print('wrote', name, len(rows), 'rows')
ORDER = ['LR', 'DT', 'kNN', 'SVM-RBF', 'GB', 'RF']
NM = {'LR': 'Logistic Regression', 'DT': 'Decision Tree', 'kNN': 'k-NN', 'SVM-RBF': 'SVM (RBF)', 'GB': 'Gradient Boosting', 'RF': 'Random Forest'}
T, S, MC, AB, GAS, BN = (L(n) for n in ('test_results_full.json', 'stats_tests_full.json', 'multiclass_and_family_results.json', 'ablation.json', 'gas_table.json', 'bench_live.json'))
HV, CT, CC, IM, SP = (L(n) for n in ('harder_validation.json', 'cic_transfer.json', 'cic_controls.json', 'integrated_matrix.json', 'split_summary.json'))
PTc, PTm = L('protocol_tests_chain.json'), L('protocol_tests_mirror.json')
# Table 5: class -> binary label with counts
t5 = pd.read_csv(os.path.join(RES, 'table_class_label_map.csv')); tt = SP['totals']
rows = [list(r) for r in t5.itertuples(index=False)] + [['Total Authorized', 'Authorized (0)', tt['authorized']['full'], tt['authorized']['train'], tt['authorized']['test']], ['Total Unauthorized', 'Unauthorized (1)', tt['unauthorized']['full'], tt['unauthorized']['train'], tt['unauthorized']['test']], ['All flows', '', tt['authorized']['full'] + tt['unauthorized']['full'], SP['n_train'], SP['n_test']]]
w('table05_class_label_map.csv', ['original_class', 'binary_label', 'full', 'train', 'test'], rows)
# Tables 6-8
w('table06_test_performance.csv', ['classifier', 'precision', 'recall', 'f1_unauthorized', 'macro_f1', 'fpr', 'roc_auc'], [[NM[k]] + [round(T[k][m], 4) for m in ('precision', 'recall', 'f1_attack', 'macro_f1', 'fpr', 'roc_auc')] for k in ORDER])
cv = S['cv_summary']; w('table07_cv_macro_f1.csv', ['classifier', 'mean_macro_f1', 'ci95_half_width', 'fold_scores'], [[NM[k], round(cv[k]['mean'], 4), round(cv[k]['ci95_half'], 4), ' / '.join(f'{x:.4f}' for x in cv[k]['folds_macro_f1'])] for k in ORDER])
pw = S['pairwise']; w('table08_paired_tests.csv', ['comparison', 'other_wrong_rf_right', 'rf_wrong_other_right', 'mcnemar_exact_p', 'mcnemar_holm_p', 'paired_t_p', 'paired_t_holm_p', 'corrected_t_p', 'corrected_t_holm_p'], [[f'RF vs {NM[k]}', pw[k]['other_wrong_rf_right'], pw[k]['rf_wrong_other_right'], pw[k]['mcnemar_exact_p'], pw[k]['mcnemar_exact_holm'], pw[k]['p_naive'], pw[k]['p_naive_holm'], pw[k]['p_corrected'], pw[k]['p_corrected_holm']] for k in ORDER[:-1]])
# Table 9
pc, bg = MC['per_class_multiclass'], MC['binary_gateway_by_class']
w('table09_per_class.csv', ['class', 'kind', 'precision', 'recall', 'f1', 'support', 'binary_gate_flagged', 'binary_gate_n', 'binary_gate_rate'], [[l, bg[l]['kind'], round(pc[l]['precision'], 4), round(pc[l]['recall'], 4), round(pc[l]['f1'], 4), pc[l]['support'], bg[l]['flagged'], bg[l]['n'], round(bg[l]['rate'], 4)] for l in MC['labels']])
# Table 10
w('table10_ablation.csv', ['configuration', 'n_features', 'macro_f1', 'f1_unauthorized', 'recall', 'fpr'], [[k, a.get('n_features', ''), round(a['macro_f1'], 4), round(a['f1_attack'], 4), round(a['recall'], 4), round(a['fpr'], 4)] for k, a in AB.items()])
# Table 11
g, vw, dg = GAS['tx_gas'], GAS['views'], GAS['deploy_gas']
rows = [[f'{k} (deployment)', v, '', ''] for k, v in dg.items()] + [[k, g[k]['median'], g[k]['min'], g[k]['max']] for k in g] + [[k + ' (read-only; gas if sent as transaction)', vw[k]['estimate_gas_if_sent'], '', f"call median {vw[k]['call_ms_median']:.1f} ms"] for k in vw]
w('table11_gas.csv', ['function', 'gas_median', 'min', 'max_or_note'], rows)
# Table 12
rows = []
for n_, key in ((4, 'n4'), (7, 'n7')):
    runs = BN[key]['runs']
    for Ld in (10, 50, 100):
        r = [x for x in runs if x['load'] == Ld]; f = lambda k: (round(float(np.mean([x[k] for x in r])), 3), round(float(np.std([x[k] for x in r], ddof=1)), 3))
        rows.append([n_, Ld, len(r), *f('throughput_tps'), *f('latency_median_s'), round(float(np.mean([x['latency_p95_s'] for x in r])), 2), sum(x['failed'] for x in r), round(float(np.mean([x['host_cpu_busy_fraction'] for x in r])), 2)])
w('table12_live_benchmark.csv', ['validators', 'devices', 'runs', 'throughput_tps_mean', 'throughput_tps_sd', 'latency_median_s_mean', 'latency_median_s_sd', 'latency_p95_s_mean', 'failures', 'host_cpu_busy'], rows)
# Table 13-14
OB, WS, LF = HV['ordered_block_70_30'], HV['within_session_ordered'], HV['lofo']
cic = CT['files']; ptp = sum(v['harmonized']['tp'] for v in cic.values()); pfn = sum(v['harmonized']['fn'] for v in cic.values()); pfp = sum(v['harmonized']['fp'] for v in cic.values()); ptn = sum(v['harmonized']['tn'] for v in cic.values())
rf = T['RF']
w('table13_validation_summary.csv', ['setting', 'test_population', 'recall', 'fpr'], [
 ['Random stratified split (reference)', SP['n_test'], round(rf['recall'], 4), round(rf['fpr'], 4)],
 ['Within-session ordered hold-out', WS['n_test'], round(WS['metrics']['recall'], 4), round(WS['metrics']['fpr'], 4)],
 ['Ordered-block hold-out (first 70% train, last 30% test)', OB['n_test'], round(OB['attack_recall'], 4), 'undefined (no benign flows)'],
 ['Leave-one-attack-family-out (range over nine families)', 'family + benign test flows', f"{min(v['recall_heldout'] for v in LF.values()):.3f}-{max(v['recall_heldout'] for v in LF.values()):.3f}", f"{min(v['fpr_benign'] for v in LF.values()):.4f}-{max(v['fpr_benign'] for v in LF.values()):.4f}"],
 ['Transfer RT-IoT2022 -> CIC-IDS2017 (pooled)', ptp + pfn + pfp + ptn, round(ptp / (ptp + pfn), 3), round(pfp / (pfp + ptn), 3)],
 ['Reverse transfer CIC-IDS2017 -> RT-IoT2022', SP['n_test'], round(CC['reverse_cic_to_rt']['recall'], 4), round(CC['reverse_cic_to_rt']['fpr'], 4)]])
w('table14_leave_one_family_out.csv', ['held_out_family', 'flows', 'recall', 'missed', 'benign_rejected', 'benign_tested'], [[f, v['n_heldout'], round(v['recall_heldout'], 3), v['missed'], v['benign_blocked'], v['benign_test_n']] for f, v in sorted(LF.items(), key=lambda kv: -kv[1]['recall_heldout'])])
# Table 15
rows = []
for n_, v in cic.items():
    h = v['harmonized']; au = CC['auc'].get(n_, {})
    rows.append([n_, h['benign_total'], h['tp'] + h['fn'], h['tp'], h['fn'], h['fp'], h['tn'], round(h['recall'], 3) if h['recall'] == h['recall'] else '', round(h['fpr'], 3), round(au['auc61'], 2) if au else ''])
rows.append(['Pooled', pfp + ptn, ptp + pfn, ptp, pfn, pfp, ptn, round(ptp / (ptp + pfn), 3), round(pfp / (pfp + ptn), 3), round(CC['auc']['pooled_61'], 2)])
w('table15_cic_transfer.csv', ['file', 'benign', 'attack', 'tp', 'fn', 'fp', 'tn', 'recall', 'fpr', 'auc'], rows)
# Tables 16-17
w('table16_protocol_tests.csv', ['id', 'case', 'expected_outcome', 'in_memory_run', 'live_contract_run'], [[a['test'].split(' ', 1)[0], a['test'].split(' ', 1)[1], a['expected'], 'pass' if a['passed'] else 'FAIL', 'pass' if b['passed'] else 'FAIL'] for a, b in zip(PTc['results'], PTm['results'])])
w('table17_integrated_test.csv', ['credential_state|traffic', 'outcomes (count of ' + str(IM['trials_per_cell']) + ' sessions)'], [[k, '; '.join(f'{r}={c}' for r, c in v.items())] for k, v in IM['cells'].items()])
# Table 18 (symbolic verification, from the Tamarin runs) and Table 19 (61-feature mapping)
import shutil
fsum = os.path.join(ROOT, 'formal', 'results_summary.csv')
if os.path.exists(fsum): shutil.copy(fsum, os.path.join(OUT, 'table18_symbolic_verification.csv')); print('copied table18')
shutil.copy(os.path.join(RES, 'table_feature_mapping_61.csv'), os.path.join(OUT, 'table19_feature_mapping_61.csv')); print('copied table19')
