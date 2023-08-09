from exptools2.core import Session, PylinkEyetrackerSession
import numpy as np
import pandas as pd
from psychopy import tools, logging
from psychopy.visual import Circle
import scipy.stats as ss
from stimuli import FixationLines, SizeResponseStim, pRFCue, FixationCross
from trial import SizeResponseTrial, InstructionTrial, DummyWaiterTrial, OutroTrial
import os
opj = os.path.join
opd = os.path.dirname

class SizeResponseSession(PylinkEyetrackerSession):
    def __init__(
        self, 
        output_str, 
        output_dir, 
        settings_file, 
        eyetracker_on=True, 
        subject=None, 
        hemi="L", 
        fix_task="fix",
        task="SRFa",
        demo=False):

        """ Initializes StroopSession object.

        Parameters
        ----------
        output_str : str
            Basename for all output-files (like logs), e.g., "sub-01_task-stroop_run-1"
        output_dir : str
            Path to desired output-directory (default: None, which results in $pwd/logs)
        settings_file : str
            Path to yaml-file with settings (default: None, which results in the package's
            default settings file (in data/default_settings.yml)
        eyetracker_on: bool, optional
            Make link with eyetracker during experiment, default is True
        params_file: str, optional
            File containing the pRF-parameters used as target site for the stimuli
        size_file: str, optional
            Path to a numpy array containing the stimulus sizes to be used as per the output of `call_sizeresponse`
        """
        super().__init__(
            output_str, 
            output_dir=output_dir, 
            settings_file=settings_file, 
            eyetracker_on=eyetracker_on)  # initialize parent class!
        
        self.demo = demo
        self.task = task
        self.fix_task = fix_task
        self.fixation_width = self.settings['various'].get('fixation_width')
        self.fixation_color = self.settings['various'].get('fixation_color')
        self.data_dir = opj(opd(__file__), "data",subject)
        self.pars_file = opj(self.data_dir, f"{subject}_model-norm_desc-best_vertices.csv")
        self.size_file = opj(self.data_dir, f"{subject}_task-{self.task}_hemi-{hemi}_desc-sizes.txt")
        self.order_file = opj(self.data_dir, f"{subject}_task-{self.task}_hemi-{hemi}_desc-order.txt")
        self.iti_file = opj(self.data_dir, f"{subject}_task-{self.task}_hemi-{hemi}_desc-itis.txt")

        # convert target site to pixels
        self.hemi = hemi
        for ff,tag in zip(
            [self.pars_file,self.size_file,self.order_file,self.iti_file],
            ["pars","sizes","order","itis"]):
            if not os.path.exists(ff):
                raise FileNotFoundError(f"Could not find '{tag}'-file: '{ff}'")
            print(f"{tag}:\t{ff}")

        if os.path.exists(self.pars_file):
            self.prf_parameters = pd.read_csv(self.pars_file).set_index('hemi')
            self.x_loc          = self.prf_parameters['x'][self.hemi] 
            self.y_loc          = self.prf_parameters['y'][self.hemi]   
            self.x_loc_pix      = tools.monitorunittools.deg2pix(self.x_loc, self.monitor)
            self.y_loc_pix      = tools.monitorunittools.deg2pix(self.y_loc, self.monitor) 
            self.stim_sizes     = np.loadtxt(self.size_file)
        else:
            # center stuff if not parameter file is
            self.x_loc, self.y_loc, self.x_loc_pix, self.y_loc_pix = 0,0,0,0            
            self.stim_sizes = self.settings['stimuli'].get('stim_sizes')
            
        # set position
        self.pos = (self.x_loc, self.y_loc)
        print(f"Target position: {self.pos}")
        print(f"Stimulus sizes: {self.stim_sizes}")

        self.repetitions = self.settings['design'].get('stim_repetitions')
        self.duration = self.settings['design'].get('stim_duration')
        self.n_trials = self.repetitions * len(self.stim_sizes)
        self.outro_trial_time = self.settings['design'].get('end_duration')
        self.static_isi = self.settings['design'].get('static_isi')
        self.custom_isi = self.settings['design'].get('custom_isi')
        if self.demo:
            self.n_trials = 5
            self.end_duration = 2
            self.start_duration = 2
            self.repetitions = 1
            self.custom_isi = True

        # make activation stimulus
        self.ActStims = {}
        for ix,ss in enumerate(self.stim_sizes):
            self.ActStims[f"stim_{ix}"] = SizeResponseStim(
                self,
                pos=self.pos,
                radialCycles=self.settings['stimuli'].get('radial_cycles'),
                angularCycles=self.settings['stimuli'].get('angular_cycles'),
                size=ss
                )
            
            self.ActStims[f"stim_{ix}"].draw(contrast="high")

    def create_trials(self):
        """ Creates trials (ideally before running your session!) """

        # set stuff for performance split on stimulus type
        for ii in ["hits","fa","miss","cr"]:
            setattr(self,ii,0)

        fixation_radius_deg = self.settings['stimuli']['Size_fixation_dot_in_degrees']
            
        if self.fix_task == "fix":
            #two colors of the fixation circle for the task
            self.fixation_disk_0 = Circle(
                self.win, 
                units='deg', 
                radius=fixation_radius_deg, 
                fillColor=[1,-1,-1], 
                lineColor=[1,-1,-1])
            
            self.fixation_disk_1 = Circle(
                self.win, 
                units='deg', 
                radius=fixation_radius_deg, 
                fillColor=[-1,1,-1], 
                lineColor=[-1,1,-1])
            
            self.contrast = np.ones((self.n_trials), dtype=int)
        else:

            # define crossing fixation lines
            self.fixation = FixationCross(
                win=self.win, 
                lineWidth=self.fixation_width, 
                color=self.fixation_color)
            
            # set half of stims to start with low contrast, other half to start with high contrast
            self.contrast = np.r_[np.ones(self.n_trials//2, dtype=int), np.zeros(self.n_trials//2, dtype=int)]        

            np.random.shuffle(self.contrast)    
            
        # ITI stuff
        if not self.custom_isi:
            itis = iterative_itis(
                mean_duration=self.settings['design'].get('mean_iti_duration'),
                minimal_duration=self.settings['design'].get('minimal_iti_duration'),
                maximal_duration=self.settings['design'].get('maximal_iti_duration'),
                n_trials=self.n_trials,
                leeway=self.settings['design'].get('total_iti_duration_leeway'),
                verbose=True)
        else:
            # read in pre-specified isi-file
            if not self.demo:
                if os.path.exists(self.iti_file):
                    print(f'Using ITI-file {self.iti_file}')
                    itis = np.loadtxt(self.iti_file)
                else:
                    raise ValueError(f"Invalid option.. Create a file called '{self.iti_file}' with {self.n_trials} ISIs, use 'run = demo', or set 'custom_isi' to 'False' in 'settings.yml'")
            else:
                itis = np.full(self.n_trials, self.static_isi)

        self.total_experiment_time = itis.sum() + self.start_duration + self.end_duration + (self.n_trials*self.duration)
        print(f"Total experiment time: {round(self.total_experiment_time,2)}s")

        dummy_trial = DummyWaiterTrial(
            session=self,
            trial_nr=0,
            phase_durations=[np.inf, self.start_duration],
            txt='waiting for scanner trigger')

        # parameters
        if self.custom_isi:
            if self.demo:
                self.presented_stims = np.hstack([np.full(self.repetitions,ii) for ii in range(len(self.stim_sizes))])
                np.random.shuffle(self.presented_stims)
            else:
                if not os.path.exists(self.order_file):
                    self.presented_stims = np.hstack([np.full(self.repetitions,ii) for ii in range(len(self.stim_sizes))])
                    np.random.shuffle(self.presented_stims)
                else:
                    print(f'Using order-file {self.order_file}')
                    self.presented_stims = list(np.loadtxt(self.order_file, dtype=int))
        else:
            self.presented_stims = np.hstack([np.full(self.repetitions,ii) for ii in range(len(self.stim_sizes))])
            np.random.shuffle(self.presented_stims)

        if len(self.presented_stims) != len(itis):
            raise ValueError(f"Number of stimulus presentations ({len(self.presented_stims)}) does not match the number of ISIs ({len(itis)})")
        
        if isinstance(self.presented_stims, list):
            self.presented_stims = np.array(self.presented_stims)

        self.trials = [dummy_trial]
        if len(self.contrast) != self.n_trials:
            self.contrast = np.append(self.contrast,1)

        for i in range(self.n_trials):

            # get the stim size for this trial and set the size
            self.stim_size_this_trial = self.stim_sizes[self.presented_stims[i]]
            
            # append trial
            self.trials.append(SizeResponseTrial(
                session=self,
                trial_nr=1+i,
                phase_durations=[itis[i], self.settings['design'].get ('stim_duration')],
                phase_names=['iti', 'stim'],
                parameters={
                    'condition': self.stim_size_this_trial,
                    'stimulus': self.presented_stims[i],
                    'contrast': ['high', 'low'][self.contrast[i]],
                    'fix_color_changetime': np.random.rand()*self.settings['design'].get('mean_iti_duration')},
                timing='seconds',
                verbose=True)
            )
            
        # create list of times at which to switch the fixation color; make a bunch more that total_experiment_time so it continues in the outro_trial
        self.dot_switch_color_times = np.arange(3, self.total_experiment_time*1.5, float(self.settings['Task_settings']['color_switch_interval']))
        self.dot_switch_color_times += (2*np.random.rand(len(self.dot_switch_color_times))-1)

        # needed to keep track of which dot to print
        self.current_dot_time = 0
        self.next_dot_time = 1

        outro_trial = OutroTrial(
            session=self,
            trial_nr=self.n_trials+1,
            phase_durations=[self.end_duration],
            txt='')
        
        self.trials.append(outro_trial)

    def change_fixation(self):

        if self.fix_task == "fix":
            present_time = self.clock.getTime()
            if self.next_dot_time<len(self.dot_switch_color_times):
                if present_time<self.dot_switch_color_times[self.current_dot_time]:                
                    self.fixation_disk_1.draw()
                    self.dot_switch_color_times[self.current_dot_time]
                else:
                    if present_time<self.dot_switch_color_times[self.next_dot_time]:
                        self.fixation_disk_0.draw()
                        self.dot_switch_color_times[self.next_dot_time]
                    else:
                        self.current_dot_time+=2
                        self.next_dot_time+=2 
        else:
            self.fixation.draw()

    def draw_stim_contrast(
        self, 
        contrast=None, 
        stimulus=None):

        if self.fix_task != "fix":
            # switch contrast mid-way
            self.presentation_time = self.clock.getTime()
            if (self.presentation_time > -self.duration/2):
                if contrast == 'high':
                    contrast = 'low'
                elif contrast == 'low':
                    contrast = 'high'
            else:
                contrast = contrast
            
            stimulus.draw(contrast=contrast)
            
        else:
            stimulus.draw()                    

    def run(self):
        """ Runs experiment. """
        # self.create_trials()  # create them *before* running!

        if self.eyetracker_on:
            self.calibrate_eyetracker()

        self.start_experiment()

        if self.eyetracker_on:
            self.start_recording_eyetracker()
        for trial in self.trials:
            trial.run()

        correct = (self.hits/self.n_trials)*100
        logging.warn(f"Performance:\t{round(correct,2)}% ({self.hits}/{self.n_trials})")

        self.close()

# iti function based on negative exponential
def _return_itis(mean_duration, minimal_duration, maximal_duration, n_trials):
    itis = np.random.exponential(scale=mean_duration-minimal_duration, size=n_trials)
    itis += minimal_duration
    itis[itis>maximal_duration] = maximal_duration
    return itis

def iterative_itis(mean_duration=6, minimal_duration=3, maximal_duration=18, n_trials=None, leeway=0, verbose=False):
    
    nits = 0
    itis = _return_itis(
        mean_duration=mean_duration,
        minimal_duration=minimal_duration,
        maximal_duration=maximal_duration,
        n_trials=n_trials)

    total_iti_duration = n_trials * mean_duration
    min_iti_duration = total_iti_duration - leeway
    max_iti_duration = total_iti_duration + leeway
    while (itis.sum() < min_iti_duration) | (itis.sum() > max_iti_duration):
        itis = _return_itis(
            mean_duration=mean_duration,
            minimal_duration=minimal_duration,
            maximal_duration=maximal_duration,
            n_trials=n_trials)
        nits += 1

    if verbose:
        print(f'ITIs created with total ITI duration of {round(itis.sum(),2)}s after {nits} iterations')    

    return itis    
