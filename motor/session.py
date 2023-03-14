from exptools2.core import Session
import numpy as np
import pandas as pd
from psychopy import tools, logging
import scipy.stats as ss
from stimuli import FixationCross, MotorStim, MotorMovie
from trial import MotorTrial, InstructionTrial, DummyWaiterTrial, OutroTrial
import os
opj = os.path.join
opd = os.path.dirname

class MotorSession(Session):
    def __init__(self, output_str, output_dir, settings_file):
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
        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file)  # initialize parent class!

        self.duration           = self.settings['design'].get('stim_duration')
        self.n_trials           = self.settings['design'].get('n_trials')
        self.outro_trial_time   = self.settings['design'].get('end_duration')
        self.unilateral_hand    = self.settings['design'].get('unilateral_hand')
        self.stim_height        = self.settings['stimuli'].get('text_height')
        self.stim_width         = self.settings['stimuli'].get('text_width')
        self.fixation_width     = self.settings['various'].get('fixation_width')
        self.fixation_color     = self.settings['various'].get('fixation_color')
        # self.unilateral_movie   = "1hand.mp4"
        self.bilateral_movie    = "2hands.mp4"
        self.lh_movie           = "lhand.mp4"
        self.rh_movie           = "rhand.mp4"
        
        # make list of movie files
        self.movie_files = [self.bilateral_movie, self.lh_movie, self.rh_movie]

        # define crossing fixation lines
        self.fixation = FixationCross(
            win=self.win, 
            lineWidth=self.fixation_width, 
            color=self.fixation_color)

        # define button options
        self.button_options = self.settings['various'].get('buttons')

        # define stim:
        self.motorstim  = MotorStim(session=self)
        self.motormovie = MotorMovie(session=self)

        for movie in self.motormovie.movies:
            movie.draw()
            
    def create_trials(self):
        """ Creates trials (ideally before running your session!) """

        itis = iterative_itis(
            mean_duration=self.settings['design'].get('mean_iti_duration'),
            minimal_duration=self.settings['design'].get('minimal_iti_duration'),
            maximal_duration=self.settings['design'].get('maximal_iti_duration'),
            n_trials=self.n_trials,
            leeway=self.settings['design'].get('total_iti_duration_leeway'),
            verbose=True)

        self.total_experiment_time = itis.sum() + self.settings['design'].get('start_duration') + self.settings['design'].get('end_duration') + (self.n_trials*self.duration)
        print(f"Total experiment time: {round(self.total_experiment_time,2)}s")

        dummy_trial = DummyWaiterTrial(
            session=self,
            trial_nr=0,
            phase_durations=[np.inf, self.settings['design'].get('start_duration')])

        outro_trial = OutroTrial(
            session=self,
            trial_nr=self.n_trials+2,
            phase_durations=[self.outro_trial_time],
            txt='')
        
        # parameters
        self.movement = np.r_[
            np.zeros(self.n_trials//3, dtype=int),
            np.ones(self.n_trials//3, dtype=int), 
            np.full(self.n_trials//3, 2, dtype=int)]
        
        np.random.shuffle(self.movement)

        self.trials = [dummy_trial]
        for i in range(self.n_trials):
            
            # append trial
            self.trials.append(
                MotorTrial(
                    session=self,
                    trial_nr=1+i,
                    phase_durations=[itis[i], self.settings['design'].get('stim_duration')],
                    phase_names=['iti','stim'],
                    parameters={'condition': ['bilateral','right','left'][self.movement[i]]},
                    timing='seconds',
                    verbose=True))
        self.trials.append(outro_trial)

    def run(self):
        """ Runs experiment. """
        self.create_trials()  # create them *before* running!
        self.start_experiment()
        for trial in self.trials:
            trial.run()

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
