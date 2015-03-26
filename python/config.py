import os
import os.path as op

import numpy as np

import matplotlib.pyplot as plt
import pandas as pd

# Experiment parameters
open_browser = True
base_path = op.dirname(op.dirname(__file__))
data_path = '/media/Paris/data/'
script_path = '/home/niccolo/Dropbox/DOCUP/scripts/python/'
results_dir = op.join(base_path, 'results')
if not op.exists(results_dir):
    os.mkdir(results_dir)

subjects = ['ak130184', 'el130086', 'ga130053', 'gm130176', 'hn120493',
    'ia130315', 'jd110235', 'jm120476', 'ma130185', 'mc130295',
    'mj130216', 'mr080072', 'oa130317', 'rg110386', 'sb120316',
    'tc120199', 'ts130283', 'yp130276', 'av130322', 'ps120458']

# Define contrasts
absent = dict(cond='present', values=[0])

contrasts_svc = (
    dict(name='targetAngle',
         include=dict(cond='orientation_target', values=[15, 45, 75, 105, 135, 165]),
         exclude=[absent]),
    dict(name='probeAngle',
         include=dict(cond='orientation_probe', values=[15, 45, 75, 105, 135, 165]),
         exclude=[]),
    dict(name='4visibilitiesPresent',
         include=dict(cond='response_visibilityCode', values=[1, 2, 3, 4]),
         exclude=[absent]),
    dict(name='visibilityPresent',
         include=dict(cond='seen_unseen', values=[0, 1]),
         exclude=[absent]),
    dict(name='presentAbsent',
         include=dict(cond='present', values=[0, 1]),
         exclude=[]),
    dict(name='accuracy',
         include=dict(cond='correct', values=[0, 1]),
         exclude=[dict(cond='correct', values=[float('NaN')])]),
    dict(name='lambda',
         include=dict(cond='lambda', values=[1, 2]),
         exclude=[absent]),
    dict(name='tilt',
         include=dict(cond='tilt', values=[-1, 1]),
         exclude=[absent]),
    dict(name='responseButton',
         include=dict(cond='response_tilt', values=[-1, 1]),
         exclude=[dict(cond='response_tilt', values=[0])]),

)

contrasts_svr = (
    dict(name='targetAngle_cos', # values likely to be changed
         include=dict(cond='orientation_target_cos',
                        values=np.cos(2*np.deg2rad([x+7.5 for x in [15, 45, 75, 105, 135, 165]]))),
         exclude=[absent]),
    dict(name='targetAngle_sin',
         include=dict(cond='orientation_target_sin',
                        values=np.sin(2*np.deg2rad([x+7.5 for x in [15, 45, 75, 105, 135, 165]]))),
         exclude=[absent]),
    dict(name='probeAngle_cos', # values likely to be changed
         include=dict(cond='orientation_probe_cos',
                        values=np.cos(2*np.deg2rad([x+7.5 for x in [15, 45, 75, 105, 135, 165]]))),
         exclude=[absent]),
    dict(name='probeAngle_sin',
         include=dict(cond='orientation_probe_sin',
                        values=np.sin(2*np.deg2rad([x+7.5 for x in [15, 45, 75, 105, 135, 165]]))),
         exclude=[absent]),
    dict(name='4visibilitiesPresent',
         include=dict(cond='response_visibilityCode', values=[1, 2, 3, 4]),
         exclude=[absent]),
    dict(name='targetContrast',
         include=dict(cond='contrast', values=[0, .5, .75, 1]),#revise target contrast
         exclude=[]),

)

clf_types = (
    dict(name='SVC',values=contrasts_svc),
    dict(name='SVR',values=contrasts_svr)
)

# Define frequencies of interest for power decoding
freqs = [7, 10, 12, 18, 29, 70, 105]

# Define type of input (erf,power etc...)
inputTypes = (
    dict(name='erf',values=[float('NaN')],clf=clf_types),
    dict(name='power',values=freqs,clf=clf_types)
)

# Decoding preprocessing steps
preproc = dict(decim=4, crop=dict(tmin=0., tmax=0.700))

# Decoding parameters
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
scaler = StandardScaler()
svc = SVC(C=1, kernel='linear', probability=True, class_weight='auto')
clf = Pipeline([('scaler', scaler), ('svc', svc)])
decoding_params = dict(n_jobs=-1, clf=clf, predict_type='predict_proba')