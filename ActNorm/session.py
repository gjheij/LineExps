from exptools2.core import PylinkEyetrackerSession
import numpy as np
import pandas as pd
from psychopy import tools, logging
from psychopy.visual import Circle
from stimuli import (
    SizeResponseStim, 
    SuppressionMask)
from trial import (
    SizeResponseTrial, 
    InstructionTrial, 
    DummyWaiterTrial, 
    OutroTrial)
import os
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
        """
        super().__init__(
            output_str, 
            output_dir=output_dir, 
            settings_file=settings_file, 
            eyetracker_on=eyetracker_on)  # initialize parent class!
        
        self.task = task
        self.demo = demo
        
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

        logging.warn(f"stim sizes: {self.stim_sizes}dva")

        self.duration           = self.settings['design'].get('stim_duration')
        self.n_trials           = self.settings['design'].get('n_trials')
        self.outro_trial_time   = self.settings['design'].get('end_duration')
        self.isi_file           = opj(os.getcwd(), f"itis_task-{self.task}.txt")

        # make activation stimulus
        self.pos = (self.x_loc, self.y_loc)
        self.ActStim = SizeResponseStim(
            self,
            pos=self.pos,
            radialCycles=self.settings['stimuli'].get('radial_cycles')/2,
            angularCycles=self.settings['stimuli'].get('angular_cycles')/2,
            size=self.stim_sizes[0]
            )
        
        # make suppression stimulus + mask 
        self.SupprStim = SizeResponseStim(
            self,
            pos=self.pos,
            radialCycles=self.settings['stimuli'].get('radial_cycles'),
            angularCycles=self.settings['stimuli'].get('angular_cycles'),
            size=(30,30)
            )
        
        self.SupprMask = SuppressionMask(self)

        # set timing if demo=True
        self.start_duration = self.settings['design'].get('start_duration')
        self.end_duration = self.settings['design'].get('end_duration')
        self.static_isi = self.settings['design'].get('static_isi')
        self.custom_isi = self.settings['design'].get('custom_isi')
        if self.demo:
            self.n_trials = 2
            self.end_duration = 5
            self.start_duration = 5
            self.static_isi = 3
            self.custom_isi = False

    def create_trials(self):
        """ Creates trials (ideally before running your session!) """

        fixation_radius_deg = self.settings['stimuli']['Size_fixation_dot_in_degrees']

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
        print(f"Total experiment time: {round(self.total_experiment_time,2)}s")

        dummy_trial = DummyWaiterTrial(
            session=self,
            trial_nr=0,
            phase_durations=[np.inf, self.start_duration],
            txt='waiting for scanner trigger')

        # parameters
        if self.custom_isi:
            self.order_file = opj(os.getcwd(), f"order_task-{self.task}.txt")
            if not os.path.exists(self.order_file):
                presented_stims = np.r_[np.ones(self.n_trials//2, dtype=int), np.zeros(self.n_trials//2, dtype=int)]
                np.random.shuffle(presented_stims)
            else:
                print(f'Using order-file {self.order_file}')
                presented_stims = list(np.loadtxt(self.order_file, dtype=int))
        else:
            presented_stims = np.r_[np.ones(self.n_trials//2, dtype=int), np.zeros(self.n_trials//2, dtype=int)]
            np.random.shuffle(presented_stims)

        if len(presented_stims) != len(itis):
            raise ValueError(f"Number of stimulus presentations ({len(presented_stims)}) does not match the number of ISIs ({len(itis)})")

        self.trials = [dummy_trial]
        for i in range(self.n_trials):

            # append trial
            self.trials.append(SizeResponseTrial(
                session=self,
                trial_nr=1+i,
                phase_durations=[itis[i], self.duration],
                phase_names=['iti', 'stim'],
                parameters={
                    'condition': ["act","norm"][presented_stims[i]],
                    'fix_color_changetime': np.random.rand()*self.settings['design'].get('mean_iti_duration')},
                timing='seconds',
                verbose=True))

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
