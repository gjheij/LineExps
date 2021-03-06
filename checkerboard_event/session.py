import numpy as np
import scipy.stats as ss
import pandas as pd

from exptools2.core import Session, PylinkEyetrackerSession
from stimuli import FixationLines, HemiFieldStim
from trial import TwoSidedTrial, InstructionTrial, DummyWaiterTrial, OutroTrial

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
        self.n_trials = self.settings['design'].get('n_trials')
        self.duration = self.settings['design'].get('stim_duration')
        self.condition = condition

        self.fixation = FixationLines(win=self.win, 
                                    circle_radius=self.settings['stimuli'].get('aperture_radius')*2,
                                    linewidth=self.settings['stimuli'].get('fix_line_width'),
                                    color=(1, -1, -1))

        self.report_fixation = FixationLines(win=self.win, 
                                    circle_radius=self.settings['stimuli'].get('fix_radius')*2,
                                    linewidth=self.settings['stimuli'].get('fix_line_width'),
                                    color=self.settings['stimuli'].get('fix_color'))

        self.hemistim = HemiFieldStim(session=self,
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
                                 phase_durations=[self.settings['design'].get('end_duration')],
                                 txt='')        

        self.trials = [instruction_trial, dummy_trial]
        for i in range(self.n_trials):
            self.trials.append(TwoSidedTrial(session=self,
                                             trial_nr=2+i,
                                             phase_names=['iti', 'stim'],
                                             phase_durations=[itis[i], self.settings['design'].get ('stim_duration')],
                                             parameters={'condition': self.condition,
                                                         'fix_color_changetime': np.random.rand()*self.settings['design'].get('mean_iti_duration')},
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

        print(f"Received {self.responses}/{self.n_trials} responses. {round(self.correct_responses/self.n_trials*100,2)}% was accurate")

        self.close()
