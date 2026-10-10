import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from common import *
from sklearn.model_selection import train_test_split
df, feat, num, y12, y, const = load_rt()
idx = np.arange(len(df))
tr, te = train_test_split(idx, test_size=0.25, stratify=y12, random_state=SEED)
sub, _ = train_test_split(tr, train_size=30000, stratify=y12[tr], random_state=SEED)
np.save(f'{RES}/idx_train.npy', tr); np.save(f'{RES}/idx_test.npy', te); np.save(f'{RES}/idx_sub30k.npy', sub)
rows = []
for c in df['Attack_type'].value_counts().index:
    m = (y12 == c)
    rows.append(dict(original_class=c, binary_label='Authorized (0)' if c in NORMAL else 'Unauthorized (1)',
                     full=int(m.sum()), train=int(m[tr].sum()), test=int(m[te].sum()), sub30k=int(m[sub].sum())))
tab = pd.DataFrame(rows); tab.to_csv(f'{RES}/table_class_label_map.csv', index=False)
print(tab.to_string(index=False))
tot = dict(authorized=dict(full=int((y==0).sum()), train=int((y[tr]==0).sum()), test=int((y[te]==0).sum()), sub=int((y[sub]==0).sum())),
           unauthorized=dict(full=int((y==1).sum()), train=int((y[tr]==1).sum()), test=int((y[te]==1).sum()), sub=int((y[sub]==1).sum())))
print(tot)
save(dict(totals=tot, n_numeric=len(num), n_categorical=len(CAT), constant_dropped=const, features=feat, n_train=len(tr), n_test=len(te), n_sub=len(sub)), 'split_summary.json')
# feature-collection time: flow_duration (seconds) per binary class
q = df.assign(y=y).groupby('y')['flow_duration'].quantile([.5,.9,.99]).unstack()
print(q); save(q.round(6).to_dict(), 'flow_duration_quantiles.json')
