import sys
import getopt
from datetime import datetime
import os
from psychopy import logging
from session import SizeResponseSession
opj = os.path.join
opd = os.path.dirname

def main(argv):

    """main.py

    Run a pRF experiment consisting of 8 bar sweeps (per iteration) in the 4 cardinal directions. Bar width is alternated between sweeps (e.g., first 2 thin bars, then 2 thick bars, etc.). Between each sweep, there's a rest period of equal length.

    Parameters
    ----------
    -s|--sub <subject ID>   subject ID (in digits; 'sub-' is appended) [default = '999']
    -n|--ses <session ID>   session ID (in digits; 'ses-' is appended) [default = 0]
    -r|--run <run ID>       run ID (in digits; 'run-' is appended) [default = 0]
    -t|--task <task ID>     task ID (e.g., 'SRFi')
    --lh|--left             target left hemisphere
    --rh|--right            target right hemisphere
    -e|--eye                turn on eyetracker
    --fix_task              task on the stimulus ('contrast' for attention task [default], 'fix' for changing fixation dot)
    --fix                   set task on stimulus to 'fix'
    --type <stim type>      stimulus type (e.g., 'annulus' [default], 'larger', 'orig')
    --design <stim design>  stimulus design ('radial' for radial stim [default], 'checker' for checkerboard stimulus)
    -q|--help               bring up this help text

    Example
    ----------
    >>> python main.py # defaults to python main.py 999 -n 0 -r 0 -h L 
    >>> python main.py -s 001 -n 2 -r 1 --eye
    >>> python main.py --help
    """

    subject     = "999"
    session     = 0
    run         = 0
    task        = "SR"
    hemi        = "L"
    eyetracker  = False
    fix_task    = "contrast"
    stim_type   = "annulus"
    stim_design = "radial"
    demo        = False
    eye_flag    = ""

    #---------------------------------------------------------------------------------------------------
    # parse arguments
    try:
        opts = getopt.getopt(argv,"eptdqs:n:r:h:",["sub=", "ses=", "run=", "hemi=", "eye", "task=", "fix_task=", "help", "demo","lh","rh","type=","design=","annulus","larger","orig","checker","radial","left","right","fix"])[0]
    except getopt.GetoptError:
        print("ERROR while handling arguments.. Did you specify an 'illegal' argument..?")
        print(main.__doc__)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-q', '--help'):
            print(main.__doc__)
            sys.exit()
        elif opt in ("-s", "--sub"):
            subject = arg
        elif opt in ("-n", "--ses"):
            session = arg         
        elif opt in ("--demo"):
            run = "demo"
        elif opt in ("-r", "--run"):
            run = arg            
        elif opt in ("--lh", "--left"):
            hemi = "L"
        elif opt in ("--rh", "--right"):
            hemi = "R"
        elif opt in ("--h", "--hemi"):
            hemi = arg
        elif opt in ("-e", "--eye"):
            eyetracker = True
            eye_flag = "--eye"
        elif opt in ("t","--task"):
            task = arg
        elif opt in ("--fix_task"):
            fix_task = arg
        elif opt in ("--fix"):
            fix_task = "fix"                                
        elif opt in ("--type"):
            stim_type = arg
        elif opt in ("--annulus"):
            stim_type = "annulus"
        elif opt in ("--larger"):
            stim_type = "larger"        
        elif opt in ("--orig"):
            stim_type = "orig"        
        elif opt in ("--design"):
            stim_design = arg  
        elif opt in ("--checker"):
            stim_design = "checker"
        elif opt in ("--radial"):
            stim_design = "radial"     
            
    if run == "demo":
        demo = True

    print(f"Subject: \t{subject}")
    print(f"Session: \t{session}")
    print(f"Run ID: \t{run}")
    print(f"Task ID: \t{task}")
    print(f"Hemisphere: \t{hemi}")
    print(f"Eyetracker: \t{eyetracker}")
    print(f"Fix task: \t{fix_task}")
    print(f"Stim type: \t{stim_type}")
    print(f"Stim design: \t{stim_design}")

    # construct command so we can copy that
    cmd=f"""python main.py -s {subject} -n {session} -r {run} -t {task} -h {hemi} {eye_flag} --fix_task {fix_task} --type {stim_type} --design {stim_design}"""
    
    print(cmd)
    if not eyetracker:
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
        eyetracker_on=eyetracker,
        params_file=params_file,
        hemi=hemi,
        task=task,
        fix_task=fix_task,
        stim_type=stim_type,
        stim_design=stim_design,
        demo=demo)

    session_object.create_trials()
    logging.warn(f'Writing results to: {opj(session_object.output_dir, session_object.output_str)}')
    session_object.run()
    session_object.close()

if __name__ == "__main__":
    main(sys.argv[1:])    
