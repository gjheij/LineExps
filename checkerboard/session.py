import numpy as np
from exptools2.core import PylinkEyetrackerSession
from psychopy.visual import Circle
from stimuli import CheckerStim
from trial import (
    CheckerTrial, 
    InstructionTrial, 
    DummyWaiterTrial, 
    OutroTrial)

class CheckerSession(PylinkEyetrackerSession):
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
        self.repetitions = self.settings['design'].get('stim_repetitions')
        self.duration = self.settings['design'].get('stim_duration')

        self.checkerstim = CheckerStim(
            session=self,
            angular_cycles=self.settings['stimuli'].get('angular_cycles'),
            radial_cycles=self.settings['stimuli'].get('radial_cycles'),
            border_radius=self.settings['stimuli'].get('border_radius'),
            pacman_angle=self.settings['stimuli'].get('pacman_angle'),
            n_mask_pixels=self.settings['stimuli'].get('n_mask_pixels'),
            frequency=self.settings['stimuli'].get('frequency'))

    def create_trials(self):
        """ Creates trials (ideally before running your session!) """
        
        # two colors of the fixation circle for the task
        self.fixation_disk_0 = Circle(
            self.win, 
            units='pix', 
            size=self.settings['stimuli'].get('dot_size'),
            fillColor=[1,-1,-1], 
            lineColor=[1,-1,-1])

        self.fixation_disk_1 = Circle(
            self.win, 
            units='pix', 
            size=self.settings['stimuli'].get('dot_size'), 
            fillColor=[-1,1,-1], 
            lineColor=[-1,1,-1])

        # nr of stimuli
        self.n_trials = self.repetitions

        # ITI stuff
        if not isinstance(self.settings['design'].get('static_isi'), (int,float)):
            itis = iterative_itis(
                mean_duration=self.settings['design'].get('mean_iti_duration'),
                minimal_duration=self.settings['design'].get('minimal_iti_duration'),
                maximal_duration=self.settings['design'].get('maximal_iti_duration'),
                n_trials=self.n_trials,
                leeway=self.settings['design'].get('total_iti_duration_leeway'),
                verbose=True)
        else:
            itis = np.full(self.n_trials, self.settings['design'].get('static_isi'))

        # parameters

        self.total_experiment_time = self.settings['design'].get('start_duration') + (self.n_trials * self.settings['design'].get('stim_duration')) + itis.sum() + self.settings['design'].get('end_duration')

        print(f"Total experiment time = {self.total_experiment_time}, with {self.repetitions}x ON/OFF")

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


        self.trials = [instruction_trial, dummy_trial]
        for i in range(self.n_trials):
            self.trials.append(CheckerTrial(
                session=self,
                trial_nr=2+i,
                phase_durations=[itis[i], self.settings['design'].get('stim_duration')],
                phase_names=['iti','stim'],
                parameters={'condition': 'on'},
                timing='seconds',
                verbose=True))

        # create list of times at which to switch the fixation color; make a bunch more that total_experiment_time so it continues in the outro_trial
        self.dot_switch_color_times = np.arange(3, self.total_experiment_time*1.5, float(self.settings['Task_settings']['color_switch_interval']))
        self.dot_switch_color_times += (2*np.random.rand(len(self.dot_switch_color_times))-1)

        # needed to keep track of which dot to print
        self.current_dot_time = 0
        self.next_dot_time = 1

        # append outro trial
        outro_trial = OutroTrial(
            session=self, 
            trial_nr=self.n_trials+2, 
            phase_durations=[self.settings['design'].get('end_duration')],
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

