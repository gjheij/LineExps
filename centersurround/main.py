import os.path as op
import argparse
import sys
import numpy as np
import scipy.stats as ss
from datetime import datetime
from psychopy import logging
from itertools import product
import yaml
from session import TwoSidedSession

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
logging.warn(f"Targeting following hemisphere: {hemi}")

if eyelink:
    eyetracker_on = True
    logging.warn("Using eyetracker")
else:
    eyetracker_on = False
    logging.warn("Using NO eyetracker")


output_str = f'sub-{subject}_ses-{ses}_run-{run}_task-PRF'
settings_fn = op.join(op.dirname(__file__), 'settings.yml')

output_dir = './logs/'+output_str

if op.exists(output_dir):
    print("Warning: output directory already exists. Renaming to avoid overwriting.")
    output_dir = output_dir + datetime.now().strftime('%Y%m%d%H%M%S')

params_file = op.join(op.dirname(__file__), 'prf_params', f"sub-{subject}_desc-prf_params_best_vertices.csv")

session_object = TwoSidedSession(output_str=output_str,
                                 output_dir=None,
                                 settings_file=settings_fn,
                                 eyetracker_on=eyetracker_on,
                                 params_file=params_file,
                                 hemi=hemi)

session_object.create_trials()
logging.warn(f'Writing results to: {op.join(session_object.output_dir, session_object.output_str)}')
session_object.run()
session_object.close()
