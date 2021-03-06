# Decoding parameters
import copy
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVR
from utils import clf_2class_proba, SVR_angle
from base import (scorer_angle, scorer_auc, scorer_spearman, scorer_circLinear)


def analysis(name, typ, condition=None, query=None):
    single_trial = False
    erf_function = None
    if typ == 'categorize':
        clf = Pipeline([('scaler', StandardScaler()),
                        ('svc', clf_2class_proba(C=1, class_weight='auto'))])
        scorer = scorer_auc
        chance = .5
    elif typ == 'regress':
        clf = Pipeline([('scaler', StandardScaler()), ('svr', LinearSVR(C=1))])
        scorer = scorer_spearman
        single_trial = True  # with non param need single trial here
        chance = 0.
    elif typ == 'circ_regress':
        clf = SVR_angle()
        scorer = scorer_angle
        chance = 1. / 6.
        single_trial = True
        erf_function = scorer_circLinear
    if condition is None:
        condition = name
    return dict(name=name, condition=condition, query=query, clf=clf,
                scorer=scorer, chance=chance, erf_function=erf_function,
                single_trial=single_trial, cv=8)

analyses = (
    analysis('target_present',      'categorize'),
    analysis('target_contrast',     'regress'),
    analysis('target_contrast_pst', 'regress', condition='target_contrast',
             query='target_present == True'),
    analysis('target_spatialFreq',  'categorize'),
    analysis('target_circAngle',    'circ_regress'),
    analysis('probe_circAngle',     'circ_regress'),
    analysis('probe_tilt',          'categorize'),
    analysis('discrim_button',      'categorize'),
    analysis('discrim_correct',     'categorize'),
    analysis('detect_button',       'regress'),
    analysis('detect_button_pst',   'regress', condition='detect_button',
             query='target_present == True'),
    analysis('detect_seen',         'categorize'),
    analysis('detect_seen_pst',     'categorize', condition='detect_seen',
             query='target_present == True')
)

# ###################### Define subscores #####################################

subscores = []
for analysis in analyses:
    analysis['contrast'] = analysis['name']
    subscores.append(analysis)
    # subdivide by visibility
    query = '(%s) and ' % analysis['query'] if analysis['query'] else ''
    if analysis['name'] not in ['m_visibilities', 'm_seen']:
        # Seen
        analysis_ = copy.deepcopy(analysis)
        analysis_['name'] += '-seen'
        analysis_['query'] = query + 'detect_seen == True'
        subscores.append(analysis_)
        # Unseen
        analysis_ = copy.deepcopy(analysis)
        analysis_['query'] = query + 'detect_seen == False'
        subscores.append(analysis_)


# ############# Define second-order subscores #################################
subscores2 = []

for analysis in analyses:
    if analysis['name'] not in ['m_visibilities', 'm_seen']:
        analysis_ = copy.deepcopy(analysis)
        analysis_['contrast1'] = analysis_['name'] + '-seen'
        analysis_['contrast2'] = analysis_['name'] + '-unseen'
        analysis_['chance'] = 0
        subscores2.append(analysis)
