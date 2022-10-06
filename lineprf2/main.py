import sys
import getopt
from datetime import datetime
import os
from psychopy import logging
from session import pRFSession
opj = os.path.join
opd = os.path.dirname

def main(argv):

    """
---------------------------------------------------------------------------------------------------
main.py

Run a pRF experiment consisting of 8 bar sweeps (per iteration) in the 4 cardinal directions. Bar 
width is alternated between sweeps (e.g., first 2 thin bars, then 2 thick bars, etc.). Between each 
sweep, there's a rest period of equal length.

Parameters
----------
-s|--sub <sub ID>   subject ID (in digits; 'sub-' is appended) [default = '999']
-n|--ses <ses ID>   session ID (in digits; 'ses-' is appended) [default = 0]
-r|--run <run ID>   run ID (in digits; 'run-' is appended) [default = 0]
--lh|--rh           which hemisphere to use [default = "--lh"]
-e|--eye            turn on eyetracker
-p|--png            make screenshots (only do this adhoc; costs too much memory to do it *during* 
                    the experiment)
-t|--sim            use `simulate.yml`-settings, rather than `settings.yml`
-q|--help           bring up this help text
-d|--delim          Have the participant delineate the FOV; saves out a json-file with pixels to be 
                    removed from the design matrix (info will also be saved to the yml-file). Gene-
                    rally only needed once, unless you have multiple designs in your experiment 
                    (might interfere otherwise with finding the json-file in `spinoza_fitprfs`). 
                    Information will also be written to the yml-file, `spinoza_fitprfs` will accept 
                    both if one doesn't exist.

Examples
----------
>>> python main.py # defaults to python main.py 999 -n 0 -r 0 --lh
>>> python main.py -s 001 -n 2 -r 1 --eye
>>> python main.py --help
---------------------------------------------------------------------------------------------------
    """

    subject     = "999"
    session     = 0
    run         = 0
    hemi        = "L"
    eyetracker  = False
    screenshots = False
    simulate    = False
    delim       = False

    #---------------------------------------------------------------------------------------------------
    # parse arguments
    try:
        opts = getopt.getopt(argv,"heptqs:n:r:",["sub=", "ses=", "run=", "hemi=", "eye", "png", "sim", "help", "delim", "lh", "rh"])[0]
    except getopt.GetoptError:
        print("ERROR while handling arguments.. Did you specify an 'illegal' argument..?")
        print(main.__doc__)
        sys.exit(2)

    cmd = f"python main.py"
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(main.__doc__)
            sys.exit()
        elif opt in ("-s", "--sub"):
            subject = arg
        elif opt in ("-n", "--ses"):
            session = arg            
        elif opt in ("-r", "--run"):
            run = arg          
        elif opt in ("-e", "--eye"):
            eyetracker = True
        elif opt in ("-p", "--png"):
            screenshots = True
        elif opt in ("-t", "--sim"):
            simulate = True
        elif opt in ("-d", "--delim"):
            delim = True
        elif opt in ("lh"):
            hemi = "L"
        elif opt in ("rh"):
            hemi = "R"            

    print(f"Subject: \t{subject}")
    print(f"Session: \t{session}")
    print(f"Run ID: \t{run}")
    print(f"Hemisphere: \t{hemi}")
    print(f"Eyetracker: \t{eyetracker}")
    print(f"Screenshots: \t{screenshots}")
    print(f"Simulate: \t{simulate}")
    print(f"Delimiter: \t{delim}")

    # construct command so we can copy that
    cmd += f" -s {subject} -n {session} -r {run}"
    if eyetracker:
        cmd += " --eye"
    
    if screenshots:
        cmd += " --png"

    if simulate:
        cmd += " --sim"

    if delim:
        cmd += " --delim"

    if hemi == "L":
        cmd += " --lh"
    
    if hemi == "R":
        cmd += " --rh"      

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

    print("\nCopy command below for easy re-running of this experiment:")
    print(cmd)
    print("---------------------------------------------------------------------------------------------------")
    params_file = opj(os.path.realpath('..'), 'data', f"sub-{subject}_model-norm_desc-best_vertices.csv")
    session_object = pRFSession(
        output_str=output_str,
        output_dir=output_dir,
        settings_file=settings_fn,
        eyetracker_on=eyetracker,
        params_file=params_file,
        hemi=hemi,
        screenshots=screenshots,
        delimit_screen=delim)

    # not really a warning, but still..
    logging.warn(f'Writing results to: {opj(session_object.output_dir, session_object.output_str)}')

    # run
    session_object.run()

    # if something fails in the experiment, close() will not be called, causing missed outputs.
    session_object.close()

if __name__ == "__main__":
    main(sys.argv[1:])    
