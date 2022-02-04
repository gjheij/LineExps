import argparse
from datetime import datetime
import os
from psychopy import logging
from session import pRFSession
opj = os.path.join
opd = os.path.dirname

#---------------------------------------------------------------------------------------------------
# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('subject', default=None, nargs='?')
parser.add_argument('session', default=None, nargs='?')
parser.add_argument('run', default=None, nargs='?')
parser.add_argument('hemi', default=None, nargs='?')
parser.add_argument('eyelink', default=None, nargs='?')
parser.add_argument('screenshots', default=None, nargs='?')
parser.add_argument('simulate', default=None, nargs='?')

cmd_args = parser.parse_args()
subject, session, run, hemi, eyelink, screenshots, simulate = cmd_args.subject, cmd_args.session, cmd_args.run, cmd_args.hemi, cmd_args.eyelink, cmd_args.screenshots, cmd_args.simulate

#---------------------------------------------------------------------------------------------------
# Request manual input if cmd-line wasn't used
if subject is None:
    subject = input('Subject? (999): ')
    subject = 999 if subject == '' else subject

if session is None:
    session = input('Session? (0): ')
    session = 0 if session == '' else session

if run is None:
    run = input('Run? (0): ')
    run = 0 if run == '' else run

if hemi is None:
    hemi = input('Hemisphere? (L): ')
    hemi = "L" if hemi == '' else hemi

if eyelink is None:
    eyelink = input('Eyetracker? (False): ')
    eyelink = False if eyelink == '' else eyelink

if screenshots is None:
    screenshots = input('Screenshots? (False): ')
    screenshots = False if screenshots == '' else screenshots

if simulate is None:
    simulate = input('simulate? (False): ')
    simulate = False if simulate == '' else simulate    

#---------------------------------------------------------------------------------------------------
# Throw warnings if eyetracker was disabled or if we're taking screenshots!
if not eyelink:
    logging.warn("Using NO eyetracker")

if screenshots:
    logging.warn("Saving screenshots; make sure you're doing this offline!")

#---------------------------------------------------------------------------------------------------
# settings
if simulate:
    settings_fn = opj(opd(__file__), 'simulate.yml')
else:
    settings_fn = opj(opd(__file__), 'settings.yml')

# output
output_str = f'sub-{subject}_ses-{session}_task-pRF_run-{run}'
output_dir = './logs/'+output_str

if os.path.exists(output_dir):
    print("Warning: output directory already exists. Renaming to avoid overwriting.")
    output_dir = output_dir + datetime.now().strftime('%Y%m%d%H%M%S')

cmd=f"python main.py {subject} {session} {run} {hemi} {eyelink} {screenshots} {simulate}"
print(cmd)
print("---------------------------------------------------------------------------------------------------")
params_file = opj(os.path.realpath('..'), 'data', f"sub-{subject}_model-norm_desc-best_vertices.csv")
session_object = pRFSession(output_str=output_str,
                            output_dir=output_dir,
                            settings_file=settings_fn,
                            eyetracker_on=eyelink,
                            params_file=params_file,
                            hemi=hemi,
                            screenshots=screenshots)

# creates the design
session_object.create_design()

# create the trials
session_object.create_trials()
logging.warn(f'Writing results to: {opj(session_object.output_dir, session_object.output_str)}')

# run
session_object.run()
session_object.close()
