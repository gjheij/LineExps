import argparse
from datetime import datetime
from itertools import product
import numpy as np
import os
from psychopy import logging
from session import SizeResponseSession
import sys
import yaml
opj = os.path.join
opd = os.path.dirname

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('subject', default=None, nargs='?')
parser.add_argument('ses', default=None, nargs='?')
parser.add_argument('run', default=None, nargs='?')
parser.add_argument('hemi', default='L', nargs='?')
parser.add_argument('eyelink', default=False, nargs='?')

cmd_args = parser.parse_args()
subject, ses, run, hemi, eyelink = cmd_args.subject, cmd_args.ses, cmd_args.run, cmd_args.hemi, cmd_args.eyelink

if subject is None:
    subject = input('Subject? (999): ')
    subject = 999 if subject == '' else subject

if ses is None:
    ses = input('Session? (None): ')
    ses = 0 if ses == '' else ses
elif ses == '0':
    ses = 0

if run is None:
    run = input('Run? (None): ')
    run = 0 if run == '' else run
elif run == '0':
    run = 0

if eyelink:
    eyetracker_on = True
else:
    eyetracker_on = False
    logging.warn("Using NO eyetracker")


output_str = f'sub-{subject}_ses-{ses}_run-{run}_task-SR'
settings_fn = opj(opd(__file__), 'settings.yml')

output_dir = './logs/'+output_str

if os.path.exists(output_dir):
    logging.warn("Warning: output directory already exists. Renaming to avoid overwriting.")
    output_dir = output_dir + datetime.now().strftime('%Y%m%d%H%M%S')


params_file = opj(os.path.realpath('..'), 'data', f"sub-{subject}_model-norm_desc-best_vertices.csv")
stim_size_file = opj(opd(params_file), f"sub-{subject}_hemi-{hemi}_desc-prf_sizeresponse.npy")
session_object = SizeResponseSession(output_str=output_str,
                                     output_dir=output_dir,
                                     settings_file=settings_fn,
                                     eyetracker_on=eyetracker_on,
                                     params_file=params_file,
                                     size_file=stim_size_file,
                                     hemi=hemi)

session_object.create_trials()
logging.warn(f'Writing results to: {opj(session_object.output_dir, session_object.output_str)}')
session_object.run()
session_object.close()
