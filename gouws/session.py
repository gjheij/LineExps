import numpy as np
import scipy.stats as ss

from exptools2.core import Session, PylinkEyetrackerSession
from stimuli import FixationLines, HemiFieldStim
from trial import TwoSidedTrial, InstructionTrial, DummyWaiterTrial, OutroTrial

class TwoSidedSession(PylinkEyetrackerSession):
    def __init__(self, output_str, output_dir, settings_file, eyetracker_on=True):
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

        self.fixation = FixationLines(win=self.win, 
                                    circle_radius=self.settings['stimuli'].get('aperture_radius')*2,
                                    color=(1, -1, -1))

        self.report_fixation = FixationLines(win=self.win, 
                                    circle_radius=self.settings['stimuli'].get('fix_radius')*2,
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

        total_iti_duration = self.n_trials * self.settings['design'].get('mean_iti_duration')
        min_iti_duration = total_iti_duration - self.settings['design'].get('total_iti_duration_leeway'), 
        max_iti_duration = total_iti_duration + self.settings['design'].get('total_iti_duration_leeway')

        def return_itis(mean_duration, minimal_duration, maximal_duration, n_trials):
            itis = np.random.exponential(scale=mean_duration-minimal_duration, size=n_trials)
            itis += minimal_duration
            itis[itis>maximal_duration] = maximal_duration
            return itis

        nits = 0
        itis = return_itis(
            mean_duration=self.settings['design'].get('mean_iti_duration'),
            minimal_duration=self.settings['design'].get('minimal_iti_duration'),
            maximal_duration=self.settings['design'].get('maximal_iti_duration'),
            n_trials=self.n_trials)
        while (itis.sum() < min_iti_duration) | (itis.sum() > max_iti_duration):
            itis = return_itis(
                mean_duration=self.settings['design'].get('mean_iti_duration'),
                minimal_duration=self.settings['design'].get('minimal_iti_duration'),
                maximal_duration=self.settings['design'].get('maximal_iti_duration'),
                n_trials=self.n_trials)
            nits += 1
        print(f'ITIs created with total ITI duration of {itis.sum()} after {nits} iterations')

        # parameters
        left_rights = np.r_[np.ones(self.n_trials//2, dtype=int), np.zeros(self.n_trials//2, dtype=int)]

        # set start direction
        directions = np.r_[np.ones(self.n_trials//4, dtype=int), -np.ones(self.n_trials//4, dtype=int),
                           np.ones(self.n_trials//4, dtype=int), -np.ones(self.n_trials//4, dtype=int)]

        direction_changes = np.r_[np.ones(self.n_trials//8, dtype=int), np.zeros(self.n_trials//8, dtype=int),
                                  np.ones(self.n_trials//8, dtype=int), np.zeros(self.n_trials//8, dtype=int),
                                  np.ones(self.n_trials//8, dtype=int), np.zeros(self.n_trials//8, dtype=int),
                                  np.ones(self.n_trials//8, dtype=int), np.zeros(self.n_trials//8, dtype=int)]

        if not left_rights.shape == directions.shape == direction_changes.shape:
            raise ValueError("Arrays do not have matching shapes")

        stims = np.arange(left_rights.shape[0])
        np.random.shuffle(stims)

        self.trials = [instruction_trial, dummy_trial]
        for i in range(self.n_trials):
            self.trials.append(TwoSidedTrial(
                session=self, 
                trial_nr=2+i, 
                phase_durations=[itis[i], self.settings['design'].get('stim_duration')], 
                phase_names=['iti', 'stim'],
                parameters={'condition': ['left', 'right'][left_rights[stims[i]]],
                            'direction': directions[stims[i]],
                            'direction_changes': direction_changes[stims[i]],
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

        self.close()
    
