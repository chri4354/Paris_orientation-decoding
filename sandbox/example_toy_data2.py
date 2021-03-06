import os.path as op
import numpy as np
import matplotlib.pyplot as plt

from sklearn.svm import SVR, SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from mne.io.meas_info import create_info
from mne.epochs import EpochsArray
from mne.decoding import GeneralizationAcrossTime

from postproc_functions import (compute_error_svr, compute_error_svc,
                                recombine_svr_prediction, plot_circ_hist)

# GENERATE SYNTHETIC DATA ======================================================
n_trial = 6 * 40
n_chan = 6 ** 2
n_time = 30
angles = np.linspace(15, 165, 6)
angle2circle = lambda angles: np.deg2rad(2 * (angles + 7.5))
circle2angle = lambda angles: np.rad2deg(2 * angles) / 2 - 7.5

# generate template topography for each angle
X0 = np.linspace(0, 2, np.sqrt(n_chan)) - 1
topos = list()
# fig, axs = plt.subplots(len(angles), sharex=False)
for a, angle in enumerate(angles):
    Xm, Ym = np.meshgrid(X0, X0)
    Xm += np.cos(np.deg2rad(2 * angle))
    Ym += np.sin(np.deg2rad(2 * angle))
    topos.append(np.exp(-((Xm ** 2) + (Ym ** 2))))
#     axs[a].matshow(topos[a], aspect='equal')
#     axs[a].set_axis_off()
#     axs[a].set_title('topo generated by angle %s' % angle)
# plt.show()

# Add new noisy topo to each trial at from half time
snr = 10
data = np.random.randn(n_trial, n_chan, n_time) / snr
y = np.arange(n_trial) % len(angles)
trial_angles = y * 30 + 15
for t in range(n_time / 2, n_time):
    for trial in range(n_trial):
        data[trial, :, t] += topos[y[trial]].flatten()

# export in mne structure
time = range(n_time)
chan_names = ['meg' + str(i) for i in range(n_chan)]
chan_types = ['grad'] * n_chan
info = create_info(chan_names, 1, chan_types)
events = np.c_[np.cumsum(np.ones(n_trial)), np.zeros(n_trial), np.zeros(n_trial)]
epochs = EpochsArray(data, info, events)

# RUN GAT ======================================================================

# SVR
# --- fit & predict separately
cos = lambda angles: np.cos(angle2circle(angles))
sin = lambda angles: np.sin(angle2circle(angles))
gats = list()
for transform in [cos, sin]:
    scaler = StandardScaler()
    svr = SVR(C=1, kernel='linear')
    clf = Pipeline([('scaler', scaler), ('svr', svr)])
    gat = GeneralizationAcrossTime(n_jobs=-1, clf=clf)
    gat.fit(epochs, y=transform(trial_angles))
    gat.predict(epochs)
    gats.append(gat)
# --- recombine
predict_angles, true_angles = recombine_svr_prediction(gats[0], gats[1])
# --- score
angle_errors_svr = compute_error_svr(predict_angles, true_angles)
plt.matshow(np.mean(angle_errors_svr,axis=2)), plt.colorbar(), plt.show()


# SVC Gat
scaler = StandardScaler()
svc = SVC(C=1, kernel='linear', probability=True)
clf = Pipeline([('scaler', scaler), ('svc', svc)])
gat = GeneralizationAcrossTime(n_jobs=-1, clf=clf, predict_type='predict_proba')
# --- fit & predict
gat.fit(epochs, y=trial_angles)
gat.predict(epochs)
# --- score
angle_errors_svc = compute_error_svc(gat, weighted_mean=False)
angle_errors_svc_w = compute_error_svc(gat, weighted_mean=True)

plt.matshow(angle_errors_svc[:,:,3]), plt.colorbar(), plt.show()


fig, ax = plt.subplots(3)
ax[0].matshow(np.mean(np.abs(angle_errors_svr), axis=2), vmin=0, vmax=np.pi)
ax[1].matshow(np.mean(np.abs(angle_errors_svc), axis=2), vmin=0, vmax=np.pi)
ax[2].matshow(np.mean(np.abs(angle_errors_svc_w), axis=2), vmin=0, vmax=np.pi)
plt.show()
