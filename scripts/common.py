import os
"""Shared utilities for the FedSSI-Auth Revision-2 experiments (seed 42 throughout)."""
import json, os, time, numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier

ROOT = os.environ.get('FEDSSI_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RT_CSV = f'{ROOT}/data/rt/RT_IOT2022.csv'
RES = f'{ROOT}/results'
SEED = 42
NORMAL = ['MQTT_Publish', 'Thing_Speak', 'Wipro_bulb']          # Authorized (label 0)
CAT = ['proto', 'service']

def load_rt():
    df = pd.read_csv(RT_CSV)
    feat = [c for c in df.columns if c not in ('no', 'Attack_type')]
    const = [c for c in feat if df[c].nunique() <= 1]
    feat = [c for c in feat if c not in const]
    num = [c for c in feat if c not in CAT]
    y12 = df['Attack_type'].values
    y = (~df['Attack_type'].isin(NORMAL)).astype(int).values      # 1 = Unauthorized (attack) = positive class
    return df, feat, num, y12, y, const

def make_pre(num, scale):
    n = StandardScaler() if scale else 'passthrough'
    return ColumnTransformer([('num', n, num), ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CAT)])

MODEL_NAMES = ['LR', 'DT', 'kNN', 'SVM-RBF', 'GB', 'RF']
def make_model(name, num, seed=SEED, n_estimators=100):
    if name == 'LR':      clf, sc = LogisticRegression(max_iter=1000, class_weight='balanced'), True
    elif name == 'DT':    clf, sc = DecisionTreeClassifier(class_weight='balanced', random_state=seed), False
    elif name == 'kNN':   clf, sc = KNeighborsClassifier(n_neighbors=5, n_jobs=1), True
    elif name == 'SVM-RBF': clf, sc = SVC(kernel='rbf', class_weight='balanced', random_state=seed), True
    elif name == 'GB':    clf, sc = GradientBoostingClassifier(n_estimators=100, random_state=seed), False
    elif name == 'RF':    clf, sc = RandomForestClassifier(n_estimators=n_estimators, class_weight='balanced', n_jobs=1, random_state=seed), False
    return Pipeline([('pre', make_pre(num, sc)), ('clf', clf)])

def scores(pipe, X):
    """continuous attack score; probabilities where available, margin for SVM"""
    c = pipe.named_steps['clf']
    if hasattr(c, 'predict_proba'): return pipe.predict_proba(X)[:, 1]
    return pipe.decision_function(X)

def metrics(y, p):
    """positive class = 1 = Unauthorized (attack). macro-F1 = mean of the two per-class F1 values."""
    y = np.asarray(y); p = np.asarray(p)
    tp = int(((y == 1) & (p == 1)).sum()); tn = int(((y == 0) & (p == 0)).sum())
    fp = int(((y == 0) & (p == 1)).sum()); fn = int(((y == 1) & (p == 0)).sum())
    def f1(tp_, fp_, fn_):
        d = 2 * tp_ + fp_ + fn_
        return 2 * tp_ / d if d else 0.0
    f1_att = f1(tp, fp, fn); f1_ben = f1(tn, fn, fp)
    prec = tp / (tp + fp) if tp + fp else float('nan'); rec = tp / (tp + fn) if tp + fn else float('nan')
    fpr = fp / (fp + tn) if fp + tn else float('nan')
    return dict(tp=tp, tn=tn, fp=fp, fn=fn, precision=prec, recall=rec, fpr=fpr, f1_attack=f1_att,
                f1_benign=f1_ben, macro_f1=(f1_att + f1_ben) / 2, accuracy=(tp + tn) / len(y))

def save(obj, name):
    with open(f'{RES}/{name}', 'w') as f: json.dump(obj, f, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
def load(name):
    with open(f'{RES}/{name}') as f: return json.load(f)
