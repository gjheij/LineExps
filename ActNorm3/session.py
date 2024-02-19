from exptools2.core import PylinkEyetrackerSession
import numpy as np
import pandas as pd
from psychopy import tools, logging
from psychopy.visual import Circle
from stimuli import (
    SizeResponseStim, 
    SuppressionMask,
    DelimiterLines,
    FixationCross)
from trial import (
    SizeResponseTrial, 
    DummyWaiterTrial, 
    ScreenDelimiterTrial,
    OutroTrial)
from exptools2.core.session import _merge_settings
import os
import yaml
opj = os.path.join

class SizeResponseSession(PylinkEyetrackerSession):
    def __init__(
        self, 
        output_str, 
        output_dir, 
        settings_file, 
        eyetracker_on=True, 
        params_file=None, 
        task=None,
        hemi="L",
        fix_task="fix",
        demo=False,
        screenshots=False,
        screen_delimit_trial=False):

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
        """
        super().__init__(
            output_str, 
            output_dir=output_dir, 
            settings_file=settings_file, 
            eyetracker_on=eyetracker_on)  # initialize parent class!
        
        self.task = task
        self.demo = demo
        self.screenshots = screenshots
        self.fix_task = fix_task
        self.fixation_width = self.settings['various'].get('fixation_width')
        self.fixation_color = self.settings['various'].get('fixation_color')
        self.intended_duration = self.settings['design'].get('intended_duration')
        self.n_stims = self.settings['stimuli'].get('n_stims')
        self.ring_width = self.settings['stimuli'].get('ring_width')
        self.n_repetitions = self.settings['stimuli'].get('n_repetitions')
        self.screen_delimit_trial = screen_delimit_trial

        self.screen_dir  = opj(output_dir, output_str+'_Screenshots')
        if self.screenshots:
            os.makedirs(self.screen_dir, exist_ok=True)

        # convert target site to pixels
        self.hemi = hemi
        if params_file:
            self.prf_parameters = pd.read_csv(params_file).set_index('hemi')
            self.x_loc          = self.prf_parameters['x'][self.hemi]                           # position on x-axis in DVA     > sets location for cue
            self.y_loc          = self.prf_parameters['y'][self.hemi]                           # position on y-axis in DVA     > sets location for cue
            self.x_loc_pix      = tools.monitorunittools.deg2pix(self.x_loc, self.monitor)      # position on x-axis in pixels  > required for deciding on bar location below
            self.y_loc_pix      = tools.monitorunittools.deg2pix(self.y_loc, self.monitor)      # position on y-axis in pixels  > required for deciding on bar location below
            self.stim_sizes     = string2float(self.prf_parameters['stim_sizes'][self.hemi]) 	# stim sizes now stored in same file
        else:
            # center stuff if not parameter file is
            self.x_loc, self.y_loc, self.x_loc_pix, self.y_loc_pix = 0,0,0,0            
            self.stim_sizes = self.settings['stimuli'].get('stim_sizes')

        self.evs = ["act","suppr_1","suppr_2"]
        self.duration = self.settings['design'].get('stim_duration')
        self.n_trials = self.n_repetitions*len(self.evs)
        self.outro_trial_time = self.settings['design'].get('end_duration')
        self.isi_file = opj(os.getcwd(), f"itis_task-{self.task}.txt")
        self.stim_ratios = self.settings['stimuli'].get('stim_ratio')

        # make activation stimulus
        rad_cycles_per_degree = self.settings['stimuli'].get('rad_cycles_per_degree')
        ang_cycles_per_degree = self.settings['stimuli'].get('ang_cycles_per_degree')
        rad_cycles = int(np.ceil(self.stim_sizes[0])*rad_cycles_per_degree)
        ang_cycles = int(np.ceil(self.stim_sizes[0])*ang_cycles_per_degree)
        
        self.pos = (self.x_loc, self.y_loc)
        self.ActStim = SizeResponseStim(
            self,
            pos=self.pos,
            radialCycles=rad_cycles,
            angularCycles=ang_cycles,
            size=self.stim_sizes[0]
            )
        
        # make suppression stimulus + mask 
        self.cut_bottom = self.settings['stimuli'].get("bottom_pixels")
        self.cut_top = self.settings['stimuli'].get("top_pixels")
        x_dist = (self.win.size[0]//2)-self.x_loc_pix
        y_dist = ((self.win.size[1]//2)-self.cut_bottom)-abs(self.y_loc_pix)

        if x_dist < y_dist:
            use_dist = x_dist
        else:
            use_dist = y_dist
        
        # convert to degrees
        suppr_size_1 = tools.monitorunittools.pix2deg(use_dist*2, self.monitor)
        suppr_size_2 = ((suppr_size_1-self.stim_sizes[0])/2)+self.stim_sizes[0]
        
        suprr_sizes = [suppr_size_2,suppr_size_1]
        self.stims = {
            "act": self.ActStim
        }

        print(f"Act size:\t{round(self.stim_sizes[0],2)}dva")
        print(f"Suppr size:\t{[round(i,2) for i in suprr_sizes]}dva")

        for ix,suppr in enumerate(suprr_sizes):
            rad_cycles = int(suppr*rad_cycles_per_degree)
            ang_cycles = int(suppr*ang_cycles_per_degree)
            self.SupprStim = SizeResponseStim(
                self,
                pos=self.pos,
                radialCycles=rad_cycles, # self.settings['stimuli'].get('radial_cycles')*int(mask_size/self.stim_sizes[0]),
                angularCycles=ang_cycles, #self.settings['stimuli'].get('angular_cycles')*int(mask_size/self.stim_sizes[0]),
                size=suppr,
                )
            
            
            self.SupprMask = SuppressionMask(
                self, 
                size=(suppr-self.ring_width),
                pos=self.pos
            )

            self.stims[f"suppr_{ix+1}"] = {}
            self.stims[f"suppr_{ix+1}"]["stim"] = self.SupprStim
            self.stims[f"suppr_{ix+1}"]["mask"] = self.SupprMask

        # set timing if demo=True
        self.start_duration = self.settings['design'].get('start_duration')
        self.end_duration = self.settings['design'].get('end_duration')
        self.static_isi = self.settings['design'].get('static_isi')
        self.custom_isi = self.settings['design'].get('custom_isi')
        self.dummy_duration = self.settings["Task_settings"].get("dummy_time")
        if self.demo:
            self.n_trials = self.n_stims
            self.start_duration = 5
            self.static_isi = 3
            self.n_repetitions = 1
            self.end_duration = (self.start_duration-self.static_isi)
            self.custom_isi = True
            self.dummy_duration = 0

        # delimiter stimuli
        if self.screen_delimit_trial:
            self.delim = DelimiterLines(
                win=self.win, 
                color=self.settings['various'].get('cue_color'),
                colorSpace="hex")
            
    def create_trials(self):
        """ Creates trials (ideally before running your session!) """

        # # set stuff for performance split on stimulus type
        # for ii in ["hits","fa","miss","cr"]:
        #     for stim in ["act","suppr"]:
        #         setattr(self, f"{stim}_{ii}", 0)

        dummy_id = -1
        self.cut_pixels = {"top": 0, "right": 0, "bottom": 0, "left": 0}
        if self.screen_delimit_trial:
            delimiter_trial = ScreenDelimiterTrial(
                session=self,
                trial_nr=dummy_id,
                phase_durations=[np.inf,np.inf,np.inf,np.inf],
                keys=['b', 'y', 'r'],
                delim_step=self.settings['Task_settings'].get('delimiter_increments')
            )
            
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
                self.iti_file = opj(os.getcwd(), f"itis_task-{self.task}.txt")
                if os.path.exists(self.iti_file):
                    print(f'Using ITI-file {self.iti_file}')
                    itis = np.loadtxt(self.iti_file)
                else:
                    raise ValueError(f"Invalid option.. Create a file called '{self.iti_file}' with {self.n_trials} ISIs, use 'run = demo', or set 'custom_isi' to 'False' in 'settings.yml'")
            else:
                itis = np.full(self.n_trials, self.static_isi)

        self.total_experiment_time = itis.sum() + self.start_duration + self.end_duration + (self.n_trials*self.duration)

        self.add_to_total = 0
        if not self.demo:
            if self.total_experiment_time < self.intended_duration:
                self.add_to_total = self.intended_duration-self.total_experiment_time
            elif self.intended_duration<self.total_experiment_time:
                raise ValueError(f"WARNING: intended duration ({self.intended_duration}) is smaller than total experiment time ({self.total_experiment_time})")
            
        self.total_experiment_time += self.add_to_total
        self.end_duration += self.add_to_total
        print(f"Total experiment time: {round(self.total_experiment_time,2)}s (added {self.add_to_total}s to total time)")

        dummy_trial = DummyWaiterTrial(
            session=self,
            trial_nr=0,
            phase_durations=[np.inf, self.start_duration],
            phase_names=["dummy","intro"],
            txt=None # "None" will show fixation cross
        )

        # parameters
        if self.custom_isi:
            if self.demo:
                self.presented_stims = np.hstack([np.full(self.n_repetitions,ii) for ii in range(self.n_stims)])
            else:
                self.order_file = opj(os.getcwd(), f"order_task-{self.task}.txt")
                if not os.path.exists(self.order_file):
                    self.presented_stims = np.hstack([np.full(self.n_repetitions,ii) for ii in range(self.n_stims)])
                    np.random.shuffle(self.presented_stims)
                else:
                    print(f'Using order-file {self.order_file}')
                    self.presented_stims = list(np.loadtxt(self.order_file, dtype=int))
        else:
            self.presented_stims = np.hstack([np.full(self.n_repetitions,ii) for ii in range(self.n_stims)])
            np.random.shuffle(self.presented_stims)

        if len(self.presented_stims) != len(itis):
            raise ValueError(f"Number of stimulus presentations ({len(self.presented_stims)}) does not match the number of ISIs ({len(itis)})")
        
        if isinstance(self.presented_stims, list):
            self.presented_stims = np.array(self.presented_stims)

        # create list of times at which to switch the fixation color; make a bunch more that total_experiment_time so it continues in the outro_trial and during dummy scan
        self.button_freq = 1/self.settings['design'].get('mean_button_duration')

        # define period in which fixation switches can occur. Do not allow switches in the last 5 seconds of experiment
        self.button_period = (self.total_experiment_time+self.dummy_duration)-5
        self.n_changes = int(self.button_freq*self.button_period)
        print(f"Fixation changes: {self.n_changes} in {self.total_experiment_time+self.dummy_duration}s (freq = {self.button_freq})")

        # initial guess
        self.dot_switch_color_times = _return_itis(
            mean_duration=self.settings['design'].get('mean_button_duration'),
            minimal_duration=self.settings['design'].get('minimal_button_duration'),
            maximal_duration=self.settings['design'].get('maximal_button_duration'),
            n_trials=self.n_changes,
        )       
        self.total_fix_time = self.dot_switch_color_times.sum()

        # force ITIs to be within time span
        while self.total_fix_time > self.button_period: 
            self.dot_switch_color_times = _return_itis(
                mean_duration=self.settings['design'].get('mean_button_duration'),
                minimal_duration=self.settings['design'].get('minimal_button_duration'),
                maximal_duration=self.settings['design'].get('maximal_button_duration'),
                n_trials=self.n_changes,
            )
            
            self.total_fix_time = self.dot_switch_color_times.sum()

        # cumsum together
        self.dot_switch_color_times = np.cumsum(self.dot_switch_color_times)
        self.actual_dot_switch_color_times = []        
        
        # insert delimiter trial if requested
        if self.screen_delimit_trial:
            self.trials = [delimiter_trial, dummy_trial]   
        else:
            self.trials = [dummy_trial]

        len_start_ = len(self.trials)

        for i in range(self.n_trials):

            # append trial
            self.trials.append(SizeResponseTrial(
                session=self,
                trial_nr=len_start_+i,
                phase_durations=[self.duration, itis[i]],
                phase_names=['stim', 'iti'],
                parameters={
                    'condition': self.evs[self.presented_stims[i]],
                    'fixation_color_switch': None,
                    'contrast': ['high', 'low'][self.contrast[i]]
                },
                timing='seconds',
                verbose=True))

        # needed to keep track of which dot to print
        self.correct_responses = 0
        self.total_responses = 0        
        self.dot_count = 0

        self.current_dot_time = 0
        self.next_dot_time = 1

        outro_trial = OutroTrial(
            session=self,
            trial_nr=self.n_trials+1,
            phase_durations=[self.end_duration],
            phase_names=["outro"],
            txt='')
        
        self.trials.append(outro_trial)

    def change_fixation(self):
        
        if self.fix_task in ["fix","both"]:
            present_time = self.clock.getTime()

            #hacky way to draw the correct dot color. could be improved
            if self.next_dot_time<len(self.dot_switch_color_times):
                if present_time<self.dot_switch_color_times[self.current_dot_time]:                
                    self.fixation_disk_1.draw()
                else:
                    if present_time<self.dot_switch_color_times[self.next_dot_time]:
                        self.fixation_disk_0.draw()
                    else:
                        self.current_dot_time+=2
                        self.next_dot_time+=2
            else:
                # deal with ending; final dot depends on whether number of presses is odd/even
                if present_time>self.dot_switch_color_times[-1]:
                    if (len(self.dot_switch_color_times) % 2) == 0:  
                        self.fixation_disk_1.draw()
                    else:
                        self.fixation_disk_0.draw()
                else:
                    self.fixation_disk_1.draw()

        else:
            self.fixation.draw()

    def draw_stim_contrast(self, contrast=None, stimulus=None):

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

        logging.warn(f"Performance FIXATION task:\t{round((self.correct_responses/self.n_changes)*100,2)}% ({self.correct_responses}/{self.n_changes} [resp interval = {self.settings['Task_settings']['response_interval']}s])")

        self.add_settings = {"screen_delim": self.cut_pixels}

        # merge settings
        _merge_settings(self.settings, self.add_settings)

        # save logged switch times
        if len(self.actual_dot_switch_color_times)>0:
            np.save(opj(self.output_dir, self.output_str+'_DotSwitchColorTimes.npy'), np.array(self.
            actual_dot_switch_color_times))

        settings_out = opj(self.output_dir, self.output_str + '_expsettings.yml')
        with open(settings_out, 'w') as f_out:
            yaml.dump(self.settings, f_out, indent=4, default_flow_style=False)

        self.close()

def string2float(string_array):
    """string2float
    This function converts a array in string representation to a regular float array. This can happen, for instance, when you've stored a numpy array in a pandas dataframe (such is the case with the 'normal' vector). It starts by splitting based on empty spaces, filter these, and convert any remaining elements to floats and returns these in an array.
    Parameters
    ----------
    string_array: str
        string to be converted to a valid numpy array with float values
    Returns
    ----------
    numpy.ndarray
        array containing elements in float rather than in string representation
    Example
    ----------
    >>> string2float('[ -7.42 -92.97 -15.28]')
    array([ -7.42, -92.97, -15.28])
    """

    if type(string_array) == str:
        new = string_array[1:-1].split(' ')[0:]
        new = list(filter(None, new))
        new = [float(i.strip(",")) for i in new]
        new = np.array(new)

        return new

    else:
        # array is already in non-string format
        return string_array

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
