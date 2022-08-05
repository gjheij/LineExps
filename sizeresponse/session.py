from exptools2.core import Session, PylinkEyetrackerSession
import numpy as np
import pandas as pd
from psychopy import tools, logging
import scipy.stats as ss
from stimuli import FixationLines, SizeResponseStim, pRFCue
from trial import SizeResponseTrial, InstructionTrial, DummyWaiterTrial, OutroTrial

class SizeResponseSession(PylinkEyetrackerSession):
    def __init__(self, output_str, output_dir, settings_file, eyetracker_on=True, params_file=None, size_file=None, hemi="L"):
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
        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file, eyetracker_on=eyetracker_on)  # initialize parent class!
        
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
                    
        self.repetitions        = self.settings['design'].get('stim_repetitions')
        self.duration           = self.settings['design'].get('stim_duration')
        self.n_trials           = self.repetitions * len(self.stim_sizes)
        self.outro_trial_time   = self.settings['design'].get('end_duration')

        
        # Make sure that we have an even number of nr_stim_sizes*repetitions so we can balance constrasts properly
        if (self.n_trials % 2) != 0:
            raise ValueError(f"n_trials is not an even number with {self.n_trials}, {self.repetitions} repetitions, and {len(self.stim_sizes)} stim sizes..\nTry an even number >10")

        # define crossing fixation lines
        self.fixation = FixationLines(win=self.win,
                                      circle_radius=self.settings['stimuli'].get('aperture_radius')*2,
                                      color=(1, -1, -1),
                                      linewidth=self.settings['stimuli'].get('fix_line_width'))

        self.report_fixation = FixationLines(win=self.win,
                                             circle_radius=self.settings['stimuli'].get('fix_radius')*2,
                                             color=self.settings['stimuli'].get('fix_color'))

        # initiate stimulus and cue object
        self.SizeStim = SizeResponseStim(self)
        self.cue = pRFCue(self)

        # define button options
        self.button_options = self.settings['various'].get('buttons')

    def create_trials(self):
        """ Creates trials (ideally before running your session!) """
        
        # stuff for accuracy
        self.correct_responses  = 0
        self.responses          = 0
        self.total_responses    = 0
        self.start_contrast     = None

        # ITI stuff
        total_iti_duration      = self.n_trials * self.settings['design'].get('mean_iti_duration')
        min_iti_duration        = total_iti_duration - self.settings['design'].get('total_iti_duration_leeway'),
        max_iti_duration        = total_iti_duration + self.settings['design'].get('total_iti_duration_leeway')

        def return_itis(mean_duration, minimal_duration, maximal_duration, n_trials):
            itis = np.random.exponential(scale=mean_duration-minimal_duration, size=n_trials)
            itis += minimal_duration
            itis[itis>maximal_duration] = maximal_duration
            return itis

        nits = 0
        itis = return_itis(mean_duration=self.settings['design'].get('mean_iti_duration'),
                           minimal_duration=self.settings['design'].get('minimal_iti_duration'),
                           maximal_duration=self.settings['design'].get('maximal_iti_duration'),
                           n_trials=self.n_trials)
        while (itis.sum() < min_iti_duration) | (itis.sum() > max_iti_duration):
            itis = return_itis(mean_duration=self.settings['design'].get('mean_iti_duration'),
                               minimal_duration=self.settings['design'].get('minimal_iti_duration'),
                               maximal_duration=self.settings['design'].get('maximal_iti_duration'),
                               n_trials=self.n_trials)
            nits += 1

        print(f'ITIs created with total ITI duration of {itis.sum()} after {nits} iterations')
        self.total_experiment_time = itis.sum() + self.settings['design'].get('start_duration') + self.settings['design'].get('end_duration') + (self.n_trials*self.duration)
        print(f"Total experiment time: {round(self.total_experiment_time,2)}s")

        instruction_trial = InstructionTrial(session=self,
                                             trial_nr=0,
                                             phase_durations=[np.inf],
                                             txt='Please keep fixating at the center.',
                                             keys=['space'])

        dummy_trial = DummyWaiterTrial(session=self,
                                       trial_nr=1,
                                       phase_durations=[np.inf, self.settings['design'].get('start_duration')],
                                       txt='Waiting for experiment to start')

        outro_trial = OutroTrial(session=self,
                                 trial_nr=self.n_trials+2,
                                 phase_durations=[self.outro_trial_time],
                                 txt='')
        # parameters
        presented_stims = np.r_[[np.full(self.n_trials//len(self.stim_sizes), i) for i,r in enumerate(self.stim_sizes)]].flatten()
        np.random.shuffle(presented_stims)

        # set half of stims to start with low contrast, other half to start with high contrast
        contrast = np.r_[np.ones(self.n_trials//2, dtype=int), np.zeros(self.n_trials//2, dtype=int)]
        np.random.shuffle(contrast)
        self.trials = [instruction_trial, dummy_trial]
        for i in range(self.n_trials):

            # get the stim size for this trial and set the size
            self.stim_size_this_trial = self.stim_sizes[presented_stims[i]]
            
            # append trial
            self.trials.append(SizeResponseTrial(session=self,
                                                 trial_nr=2+i,
                                                 phase_durations=[itis[i], self.settings['design'].get ('stim_duration')],
                                                 phase_names=['iti', 'stim'],
                                                 parameters={'condition': self.stim_size_this_trial,
                                                             'contrast': ['high', 'low'][contrast[i]],
                                                             'fix_color_changetime': np.random.rand()*self.settings['design'].get('mean_iti_duration')},
                                                 timing='seconds',
                                                 verbose=True))
        self.trials.append(outro_trial)

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

        print(f"Received {self.responses}/{self.n_trials} responses. {round(self.correct_responses/self.n_trials*100,2)}% was accurate")

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
        new = [float(i) for i in new]
        new = np.array(new)

        return new

    else:
        # array is already in non-string format
        return string_array
