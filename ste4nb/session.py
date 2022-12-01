import numpy as np
import scipy.stats as ss
import pandas as pd
from exptools2.core.session import _merge_settings
from exptools2.core import PylinkEyetrackerSession
from stimuli import FixationLines, HemiFieldStim
from trial import (
    TwoSidedTrial, 
    InstructionTrial, 
    DummyWaiterTrial, 
    OutroTrial)
import os
import yaml
opj = os.path.join

class TwoSidedSession(PylinkEyetrackerSession):
    def __init__(self, output_str, output_dir, settings_file, eyetracker_on=False, condition='HC'):
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
        """

        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file, eyetracker_on=eyetracker_on)  # initialize parent class!
        self.dyns = self.settings['design'].get('dyns')
        self.nsa = self.settings['design'].get('nsa')
        self.duration = self.settings['design'].get('stim_duration')
        self.t_r = self.settings['design'].get('t_r')
        self.condition = condition    

        # self.fixation = FixationLines(win=self.win, 
        #                             circle_radius=self.settings['stimuli'].get('aperture_radius')*2,
        #                             linewidth=self.settings['stimuli'].get('fix_line_width'),
        #                             color=(1, -1, -1))

        # self.report_fixation = FixationLines(win=self.win, 
        #                             circle_radius=self.settings['stimuli'].get('fix_radius')*2,
        #                             linewidth=self.settings['stimuli'].get('fix_line_width'),
        #                             color=self.settings['stimuli'].get('fix_color'))

        self.hemistim = HemiFieldStim(
            session=self,
            angular_cycles=self.settings['stimuli'].get('angular_cycles'),
            radial_cycles=self.settings['stimuli'].get('radial_cycles'),
            border_radius=self.settings['stimuli'].get('border_radius'),
            pacman_angle=self.settings['stimuli'].get('pacman_angle'),
            n_mask_pixels=self.settings['stimuli'].get('n_mask_pixels'),
            frequency=self.settings['stimuli'].get('frequency'))

    def create_trials(self):
        """ Creates trials (ideally before running your session!) """
        
        # stuff for accuracy
        self.correct_responses = 0
        self.responses = 0
        self.total_responses = 0
        self.start_contrast = None

        avg_duration = self.t_r*self.dyns
        if not self.settings['design'].get("fixed_iti"):
            
            # one dynamic is averages*tr
            n_trials = int(avg_duration/self.settings['design'].get('mean_iti_duration'))-1 # we're also doing a stimulus @t=0

            itis = iterative_itis(
                mean_duration=self.settings['design'].get('mean_iti_duration'),
                minimal_duration=self.settings['design'].get('minimal_iti_duration'),
                maximal_duration=self.settings['design'].get('maximal_iti_duration'),
                n_trials=n_trials,
                leeway=self.settings['design'].get('total_iti_duration_leeway'),
                verbose=True)

        else:
            itis = np.r_[[self.settings['design'].get('mean_iti_duration') for ii in range(self.settings['design'].get('n_trials'))]]

        self.total_experiment_time = self.settings['design'].get('start_duration') + self.settings['design'].get('end_duration') + avg_duration*self.nsa
        
        # get presentation times within NSA block
        self.present_at = np.r_[0, itis].cumsum()
        self.present_at[1:] += self.duration

        print(f"Total experiment time: {round(self.total_experiment_time,2)}s")
        print(f"Presentation times: {self.present_at}")

        instruction_trial = InstructionTrial(
            session=self, 
            trial_nr=0, 
            phase_durations=[np.inf],
            txt='Please keep fixating at the center.', 
            keys=['space'])

        dummy_trial = DummyWaiterTrial(
            session=self, 
            trial_nr=1, 
            phase_durations=[np.inf, self.settings['design'].get('start_duration')],
            txt='Waiting for experiment to start')

        outro_trial = OutroTrial(
            session=self, 
            trial_nr=self.nsa+2, 
            phase_durations=[self.settings['design'].get('end_duration')],
            txt='')        

        self.trials = [instruction_trial, dummy_trial]
        for i in range(self.nsa):
            self.trials.append(
                TwoSidedTrial(
                    session=self,
                    trial_nr=2+i,
                    phase_names=['stim'],
                    phase_durations=[avg_duration],
                    parameters={'condition': self.condition},
                    timing='seconds',
                    verbose=True))

        self.trials.append(outro_trial)

    def create_trial(self):
        pass

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

        self.add_settings = {"presentation_times": f"{[ii for ii in self.present_at]}"}

        # merge settings
        _merge_settings(self.settings, self.add_settings)

        # write to disk
        settings_out = opj(self.output_dir, self.output_str + '_expsettings.yml')
        with open(settings_out, 'w') as f_out:
            yaml.dump(self.settings, f_out, indent=4, default_flow_style=False)

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