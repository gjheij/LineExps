import os.path as op
import argparse
import sys
import numpy as np
import scipy.stats as ss
import pandas as pd
from psychopy import logging
from itertools import product
import yaml
from session import TwoSidedSession
from datetime import datetime

# deal with arguments
parser = argparse.ArgumentParser()
parser.add_argument('subject', default=None, nargs='?')
parser.add_argument('condition', default=None, nargs='?')
parser.add_argument('ses', default=None, nargs='?')
parser.add_argument('run', default=None, nargs='?')

cmd_args = parser.parse_args()
subject, condition, ses, run, = cmd_args.subject, cmd_args.condition, cmd_args.ses, cmd_args.run

if subject is None:
    subject = input('Subject? (999): ')
    subject = 999 if subject == '' else subject

if condition is None:
    condition = input('Condition? (HC): ')
    condition = "HC" if condition == '' else condition

if run is None:
    run = input('Run? (None): ')
    run = 0 if run == '' else run
elif run == '0':
    run = 0

if ses is None:
    ses = input('Session? (None): ')
    ses = 0 if ses == '' else ses
elif ses == '0':
    ses = 0

output_str = f'sub-{subject}_ses-{ses}_task-scenes_run-{run}'
output_dir = './logs/'+output_str

if op.exists(output_dir):
    print("Warning: output directory already exists. Renaming to avoid overwriting.")
    output_dir = output_dir + datetime.now().strftime('%Y%m%d%H%M%S')

settings_fn = op.join(op.dirname(__file__), 'settings.yml')
session_object = TwoSidedSession(output_str=output_str,
                                 output_dir=output_dir,
                                 settings_file=settings_fn,
                                 eyetracker_on=False,
                                 condition=condition)

session_object.create_trials()
logging.warn(f'Writing results to: {op.join(session_object.output_dir, session_object.output_str)}')
session_object.run()
session_object.close()
