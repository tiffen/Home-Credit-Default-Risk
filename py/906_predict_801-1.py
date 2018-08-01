#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug  1 20:04:21 2018

@author: Kazuki
"""


import gc, os
from tqdm import tqdm
import pandas as pd
import numpy as np
import sys
sys.path.append(f'/home/{os.environ.get("USER")}/PythonLibrary')
import lgbextension as ex
import lightgbm as lgb
from multiprocessing import cpu_count
from glob import glob
from collections import defaultdict
import utils, utils_cat, utils_best
utils.start(__file__)
#==============================================================================

LOOP = 3

SEED = 71

NROUND = 5040


SUBMIT_FILE_PATH = '../output/801-1.csv.gz'

COMMENT = f'CV auc-mean(7-fold):  0.80510 + 0.00325 all(804+CV805=1144)'

EXE_SUBMIT = True

param = {
         'objective': 'binary',
         'metric': 'auc',
         'learning_rate': 0.01,
         'max_depth': 6,
         'num_leaves': 63,
         'max_bin': 255,
         
         'min_child_weight': 10,
         'min_data_in_leaf': 150,
         'reg_lambda': 0.5,  # L2 regularization term on weights.
         'reg_alpha': 0.5,  # L1 regularization term on weights.
         
         'colsample_bytree': 0.9,
         'subsample': 0.9,
#         'nthread': 32,
         'nthread': cpu_count(),
         'bagging_freq': 1,
         'verbose':-1,
         'seed': SEED
         }

np.random.seed(SEED)
# =============================================================================
# feature
# =============================================================================

loader805 = utils_best.Loader('CV805_LB803')
loader804 = utils_best.Loader('LB804')

X_805 = loader805.train().head()
X_804 = loader804.train().head()

col = X_804.columns.difference(X_805.columns)
feature = pd.concat([X_805, X_804[col]], axis=1).columns

file_tr = ('../feature/train_' + feature + '.f').tolist()
file_te = ('../feature/test_'  + feature + '.f').tolist()

# =============================================================================
# load data
# =============================================================================
X_train = pd.concat([
                    pd.read_feather(f) for f in tqdm(file_tr, mininterval=60)
                   ], axis=1)

X_test = pd.concat([
                    pd.read_feather(f) for f in tqdm(file_te, mininterval=60)
                   ], axis=1)[X_train.columns]

y = utils.read_pickles('../data/label').TARGET

X_train['nejumi'] = np.load('../feature_someone/train_nejumi.npy')
X_test['nejumi'] = np.load('../feature_someone/test_nejumi.npy')

if X_train.columns.duplicated().sum()>0:
    raise Exception(f'duplicated!: { X_train.columns[ X_train.columns.duplicated() ] }')
print('no dup :) ')
print(f'X_train.shape {X_train.shape}')

gc.collect()

CAT = list( set(X_train.columns)&set(utils_cat.ALL))

print(f'category: {CAT}')

keys = sorted([c.split('_')[0][:2] for c in X_train.columns])
di = defaultdict(int)
for k in keys:
    di[k] += 1
for k,v in di.items():
    print(f'{k}: {v}')

X_train.head().to_csv(SUBMIT_FILE_PATH.replace('.csv', '_X.csv'),
       index=False, compression='gzip')

# =============================================================================
# training
# =============================================================================
dtrain = lgb.Dataset(X_train, y, categorical_feature=CAT )

models = []
for i in range(LOOP):
    print(f'LOOP: {i}')
    gc.collect()
    param.update({'seed':np.random.randint(9999)})
    model = lgb.train(param, dtrain, NROUND,
                      categorical_feature=CAT)
#    model.save_model(f'lgb{i}.model')
    models.append(model)

imp = ex.getImp(models)
imp.to_csv(f'LOG/imp_{__file__}.csv', index=False)

# =============================================================================
# predict
# =============================================================================
sub = pd.read_pickle('../data/sub.p')

gc.collect()

label_name = 'TARGET'

sub[label_name] = 0
for model in models:
    y_pred = model.predict(X_test)
    sub[label_name] += pd.Series(y_pred).rank()
sub[label_name] /= LOOP
sub[label_name] /= sub[label_name].max()
sub['SK_ID_CURR'] = sub['SK_ID_CURR'].map(int)

sub.to_csv(SUBMIT_FILE_PATH, index=False, compression='gzip')

# =============================================================================
# submission
# =============================================================================
if EXE_SUBMIT:
    print('submit')
    utils.submit(SUBMIT_FILE_PATH, COMMENT)

#==============================================================================
utils.end(__file__)



