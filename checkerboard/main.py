import os.path as op
import argparse
from psychopy import logging
import yaml
from session import CheckerSession
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('subject', default=None, nargs='?')
parser.add_argument('ses', default=None, nargs='?')
parser.add_argument('run', default=None, nargs='?')
parser.add_argument('eyelink', default=False, nargs='?')

cmd_args = parser.parse_args()
subject, ses, run, eyelink = cmd_args.subject, cmd_args.ses, cmd_args.run, cmd_args.eyelink

if subject is None:
    subject = input('Subject? (999): ')
    subject = 999 if subject == '' else subject

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

if eyelink is None:
    eyelink = input('Eyetracker? (None): ')
    eyelink = 0 if eyelink == '' else eyelink
elif eyelink == '0':
    eyelink = 0    

eyetracker_on = False
if eyelink == 1:
    eyetracker_on = True
    logging.warn("Using eyetracker")


output_str = f'sub-{subject}_ses-{ses}_run-{run}_task-checkerboard'
output_dir = './logs/'+output_str

if op.exists(output_dir):
    print("Warning: output directory already exists. Renaming to avoid overwriting.")
    output_dir = output_dir + datetime.now().strftime('%Y%m%d%H%M%S')

settings_fn = op.join(op.dirname(__file__), 'settings.yml')

session_object = CheckerSession(
    output_str=output_str,
    output_dir=output_dir,
    settings_file=settings_fn,
    eyetracker_on=eyetracker_on)

session_object.create_trials()
logging.warn(f'Writing results to: {op.join(session_object.output_dir, session_object.output_str)}')
session_object.run()
session_object.close()
