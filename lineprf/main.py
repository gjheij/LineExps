import argparse
from datetime import datetime
import os
from psychopy import logging
from session import pRFSession
opj = os.path.join
opd = os.path.dirname

# stupid function to deal with string-representations of boolean..
def str2bool(v):
  return str(v).lower() in ("yes", "true", "t", "1")

#---------------------------------------------------------------------------------------------------
# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument('subject', default=None, nargs='?')
parser.add_argument('session', default=None, nargs='?')
parser.add_argument('run', default=None, nargs='?')
parser.add_argument('hemi', default=None, nargs='?')
parser.add_argument('eyetracker', default=None, nargs='?')
parser.add_argument('screenshots', default=None, nargs='?')
parser.add_argument('simulate', default=None, nargs='?')

cmd_args = parser.parse_args()
subject, session, run, hemi, eyetracker, screenshots, simulate = cmd_args.subject, cmd_args.session, cmd_args.run, cmd_args.hemi, cmd_args.eyetracker, cmd_args.screenshots, cmd_args.simulate

#---------------------------------------------------------------------------------------------------
# Request manual input if cmd-line wasn't used
if subject is None:
    subject = input('Subject? (999): ')
    subject = 999 if subject == '' else subject

if session is None:
    session = input('Session? (0): ')
    session = 0 if session == '' else session

if run is None:
    run = input('Run ID? (0): ')
    run = 0 if run == '' else run

if hemi is None:
    hemi = input('Hemisphere? (L): ')
    hemi = "L" if hemi == '' else hemi

if eyetracker is None:
    eyetracker = bool(input('Eyetracker? (False): '))
    if eyetracker == '':
        eyetracker = False
    else:
        eyetracker = str2bool(eyetracker)
else:
    eyetracker = str2bool(eyetracker)        

if screenshots is None:
    if screenshots == '':
        screenshots = False
    else:
        screenshots = str2bool(screenshots)
else:
    screenshots = str2bool(screenshots)        
    
if simulate is None:
    if simulate == '':
        simulate = False
    else:
        simulate = str2bool(simulate)
else:
    simulate = str2bool(simulate)        

print(f"Subject: \t{subject}")
print(f"Session: \t{session}")
print(f"Run ID: \t{run}")
print(f"Hemisphere: \t{hemi}")
print(f"Eyetracker: \t{eyetracker}")
print(f"Screenshots: \t{screenshots}")
print(f"Simulate: \t{simulate}")

#---------------------------------------------------------------------------------------------------
# Throw warnings if eyetracker was disabled or if we're taking screenshots!
if eyetracker == False:
    logging.warn("Eyetracker DISABLED")
elif eyetracker == True:
    logging.warn("Eyetracker ENABLED")
else:
    raise ValueError(f"Unknown input {eyetracker} of type {type(eyetracker)} for eyetracker-option. Must be 'True' or 'False'")

if screenshots == True:
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

cmd=f"python main.py {subject} {session} {run} {hemi} {eyetracker} {screenshots} {simulate}"
print(cmd)
print("---------------------------------------------------------------------------------------------------")
params_file = opj(os.path.realpath('..'), 'data', f"sub-{subject}_model-norm_desc-best_vertices.csv")
session_object = pRFSession(output_str=output_str,
                            output_dir=output_dir,
                            settings_file=settings_fn,
                            eyetracker_on=eyetracker,
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
