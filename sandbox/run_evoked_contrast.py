import os.path as op
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress

import mne
from mne.io import Raw
from mne.io.pick import _picks_by_type as picks_by_type
from mne.preprocessing import read_ica
from mne.viz import plot_drop_log

from meeg_preprocessing.utils import setup_provenance, set_eog_ecg_channels

from toolbox.utils import find_in_df, build_contrast, save_to_dict

from utils import get_data

from config import (
    data_path,
    pyoutput_path,
    subjects,
    paths('report'),
    contrasts,
    open_browser,
    chan_types,
)

report, run_id, _, logger = setup_provenance(script=__file__,
                                                       results_dir=paths('report'))

mne.set_log_level('INFO')

# force separation of magnetometers and gradiometers
if 'meg' in [i['name'] for i in chan_types]:
    chan_types = [dict(name='mag'), dict(name='grad')] + \
                 [dict(name=i['name']) for i in chan_types
                                           if i['name'] != 'meg']
for subject in subjects:

    # Extract events from mat file
    meg_fname = op.join(data_path, subject, 'preprocessed', subject + '_preprocessed')
    bhv_fname = op.join(data_path, subject, 'behavior', subject + '_fixed.mat')
    epochs, events = get_data(meg_fname, bhv_fname)

    # Apply each contrast
    all_epochs = [[]] * len(contrasts)
    for contrast in contrasts:
        # XXX try:
        delta, evokeds = build_contrast(contrast['conditions'], epochs, events)
        # except RuntimeError:
        #     warnings.warn('{}: no epochs in {} for {}' % (subject, ep_name,
        #                                                   contrast['name']))
        #     continue

        # Prepare plot delta (subtraction, or regression)
        fig1, ax1 = plt.subplots(1, len(chan_types))
        if type(ax1) not in [list, np.ndarray]:
            ax1 = [ax1]
        # Prepare plot all conditions at top level of contrast
        fig2, ax2 = plt.subplots(len(evokeds), len(chan_types))
        ax2 = np.reshape(ax2, len(evokeds) * len(chan_types))

        # Loop across channels
        for ch, chan_type in enumerate(chan_types):
            # Select specific types of sensor
            info = delta.info
            picks = [i for k, p in picks_by_type(info)
                          for i in p if k in chan_type['name']]
            # --------------------------------------------------------------
            # Plot delta (subtraction, or regression)
            # adjust color scale
            mM = np.percentile(np.abs(delta.data[picks,:]), 99.)

            # plot mean sensors x time
            ax1[ch].imshow(delta.data[picks,:], vmin=-mM, vmax=mM,
                              interpolation='none', aspect='auto',
                              cmap='RdBu_r', extent=[min(delta.times),
                                  max(delta.times), 0, len(picks)])
            # add t0
            ax1[ch].plot([0, 0], [0, len(picks)], color='black')
            ax1[ch].set_title(chan_type['name'] + ': ' + delta.comment)
            ax1[ch].set_xlabel('Time')
            ax1[ch].set_adjustable('box-forced')

            # --------------------------------------------------------------
            # Plot all conditions at top level of contrast
            # XXX only works for +:- data
            mM = np.mean([np.percentile(abs(e.data[picks,:]), 99.)
                                               for e in evokeds['current']])

            for e, evoked in enumerate(evokeds['current']):
                ax_ind = e * len(chan_types) + ch
                ax2[ax_ind].imshow(evoked.data[picks,:], vmin=-mM, vmax=mM,
                                  interpolation='none', aspect='auto',
                                  cmap='RdBu_r', extent=[min(delta.times),
                                      max(evoked.times), 0, len(picks)])
                ax2[ax_ind].plot([0, 0], [0, len(picks)], color='black')
                ax2[ax_ind].set_title(chan_type['name'] + ': ' +
                                     evoked.comment)
                ax2[ax_ind].set_xlabel('Time')
                ax2[ax_ind].set_adjustable('box-forced')

        # Save figure
        report.add_figs_to_section(fig1, ('%s %s: DELTA'
            % (subject, contrast['name'])), contrast['name'])

        report.add_figs_to_section(fig2, ('%s %s: CONDITIONS'
            % (subject, contrast['name'])), contrast['name'])


    # Save all_evokeds
    ave_fname = op.join(pyoutput_path, subject,
                      '{}-contrasts-ave.pickle'.format(subject))
    save_dict = dict()
    save_dict[contrast['name']] = dict(delta=delta, evokeds=evokeds,
                                       contrast=contrast, events=events)
    save_to_dict(ave_fname, save_dict)

report.save(open_browser=open_browser)
