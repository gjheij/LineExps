import argparse
from datetime import datetime
import os
from psychopy import logging
from session import SizeResponseSession
opj = os.path.join
opd = os.path.dirname

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('subject', default=None, nargs='?')
parser.add_argument('session', default=None, nargs='?')
parser.add_argument('task', default=None, nargs='?')
parser.add_argument('run', default=None, nargs='?')
parser.add_argument('hemi', default=None, nargs='?')
parser.add_argument('eyelink', default=None, nargs='?')

cmd_args = parser.parse_args()
subject, session, task, run, hemi, eyelink = cmd_args.subject, cmd_args.session, cmd_args.task, cmd_args.run, cmd_args.hemi, cmd_args.eyelink

if subject is None:
    subject = input('Subject? (999): ')
    subject = 999 if subject == '' else subject

if session is None:
    session = input('Session? (0): ')
    session = 0 if session == '' else session

if task is None:
    task = input('task? (SR): ')
    task = "SR" if task == '' else task

if run is None:
    run = input('Run? (0): ')
    run = 0 if run == '' else run

if run == "demo":
    demo = True
else:
    demo = False

if hemi is None:
    hemi = input('Hemisphere? (L): ')
    hemi = "L" if hemi == '' else hemi

if eyelink is None:
    eyelink = input('Eyetracker? (False): ')
    eyelink = False if eyelink == '' else eyelink

if not eyelink:
    logging.warn("Using NO eyetracker")


output_str = f'sub-{subject}_ses-{session}_task-{task}_run-{run}'
settings_fn = opj(opd(__file__), 'settings.yml')

output_dir = './logs/'+output_str

if os.path.exists(output_dir):
    logging.warn("Warning: output directory already exists. Renaming to avoid overwriting.")
    output_dir = output_dir + datetime.now().strftime('%Y%m%d%H%M%S')


params_file = opj(os.getcwd(), 'data', f"sub-{subject}_model-norm_desc-best_vertices.csv")
session_object = SizeResponseSession(
    output_str=output_str,
    output_dir=output_dir,
    settings_file=settings_fn,
    eyetracker_on=eyelink,
    params_file=params_file,
    hemi=hemi,
    demo=demo)

session_object.create_trials()
logging.warn(f'Writing results to: {opj(session_object.output_dir, session_object.output_str)}')
session_object.run()
session_object.close()
