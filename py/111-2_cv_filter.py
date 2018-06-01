#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 01:53:33 2018

@author: Kazuki
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 30 08:33:16 2018

@author: Kazuki
"""


from glob import glob
from os import system
import pandas as pd
import sys
sys.path.append('/home/kazuki_onodera/Python')
import lgbmextension as ex
import lightgbm as lgb
import multiprocessing
import utils
utils.start(__file__)
#==============================================================================

SEED = 71

folders  = glob('../data/106*_train')
folders += glob('../data/107*_train')
folders += glob('../data/108*_train')
folders += glob('../data/109*_train')
folders += glob('../data/110*_train')

X = pd.concat([
               utils.read_pickles(f) for f in (folders)
               ], axis=1)
y = utils.read_pickles('../data/label').TARGET


#utils.reduce_memory(X)
print(f'X.shape {X.shape}')


param = {
         'objective': 'binary',
         'metric': 'auc',
         'learning_rate': 0.01,
         'max_depth': -1,
         'num_leaves': 511,
         'max_bin': 255,
         'colsample_bytree': 0.1,
         'subsample': 0.5,
#         'nthread': int(multiprocessing.cpu_count()/2),
         'nthread': multiprocessing.cpu_count(),
         'bagging_freq': 1,
         
         'seed': SEED
         }


categorical_feature = ['NAME_CONTRACT_TYPE',
                     'CODE_GENDER',
                     'FLAG_OWN_CAR',
                     'FLAG_OWN_REALTY',
                     'NAME_TYPE_SUITE',
                     'NAME_INCOME_TYPE',
                     'NAME_EDUCATION_TYPE',
                     'NAME_FAMILY_STATUS',
                     'NAME_HOUSING_TYPE',
                     'OCCUPATION_TYPE',
                     'WEEKDAY_APPR_PROCESS_START',
                     'ORGANIZATION_TYPE',
                     'FONDKAPREMONT_MODE',
                     'HOUSETYPE_MODE',
                     'WALLSMATERIAL_MODE',
                     'EMERGENCYSTATE_MODE']

dtrain = lgb.Dataset(X, y, categorical_feature=list( set(X.columns)&set(categorical_feature)) )
dtrain.construct()

ret = lgb.cv(param, dtrain, 9999, nfold=5,
             early_stopping_rounds=50, verbose_eval=10,
             categorical_feature=list( set(X.columns)&set(categorical_feature)),
             seed=SEED)
print(f"CV auc-mean {ret['auc-mean'][-1]}")

dtrain = lgb.Dataset(X, y, categorical_feature=list( set(X.columns)&set(categorical_feature)) )
model = lgb.train(param, dtrain, len(ret['auc-mean']))
#model = lgb.train(param, dtrain, 300, valid_sets=[dtrain], valid_names=['train'])

imp = ex.getImp(model)


imp.to_csv(f'LOG/imp_{__file__}.csv', index=False)

# =============================================================================
# 
# =============================================================================
imp = imp.set_index('index')
feature_all = imp[imp['split'] != 0].index.tolist()

import gc

def read_pickle(folder, usecols):
    df = pd.read_pickle(folder+'/000.p')
    col = list( set(usecols) & set(df.columns))
    if len(col)>0:
        df = utils.read_pickles(folder, col)
        utils.to_pickles(df, folder+'_filtered', utils.SPLIT_SIZE)
        del df; gc.collect()
        
        folder = folder.replace('_train', '_test')
        df = utils.read_pickles(folder, col)
        utils.to_pickles(df, folder+'_filtered', utils.SPLIT_SIZE)
        
    else:
        print(f'{folder} doesnt have valid features')
        pass
    

[read_pickle(f, feature_all) for f in folders]

#==============================================================================
utils.end(__file__)



