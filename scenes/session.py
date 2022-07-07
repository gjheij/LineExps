import numpy as np
import scipy.stats as ss
import pandas as pd
import os
import h5py
import urllib
from psychopy.visual import GratingStim
from psychopy import logging
from exptools2.core import Session, PylinkEyetrackerSession
from stimuli import FixationLines, HemiFieldStim
from trial import TwoSidedTrial, InstructionTrial, DummyWaiterTrial, OutroTrial
import random

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
        self.frequency = self.settings['stimuli'].get('frequency')
        self.condition = condition
        self.isi_file = self.settings['design'].get('isi_file')

        # stimulus materials
        self.stim_file_path = os.path.join(os.path.abspath('../data'), self.settings['stimuli'].get('bg_stim_h5file'))
        if not os.path.isfile(self.stim_file_path):
            logging.warn(f'Downloading stimulus file from figshare to {self.stim_file_path}')
            urllib.request.urlretrieve(self.settings['stimuli'].get('bg_stim_url'), self.stim_file_path)

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
        self.correct_responses  = 0
        self.responses          = 0
        self.total_responses    = 0

        # stimuli
        h5stimfile = h5py.File(self.stim_file_path, 'r')
        self.bg_images = (-1 + np.array(h5stimfile.get('stimuli')) / 128)*1
        h5stimfile.close()

        self.image_bg_stims = [GratingStim(win=self.win,
                                           tex=bg_img,
                                           units='pix', 
                                           mask='raisedCos',
                                           texRes=self.bg_images.shape[1],
                                           colorSpace='rgb',
                                           size=self.settings['stimuli'].get('stim_size_pixels'),
                                           interpolate=True)
                               for bg_img in self.bg_images]

        self.image_bg_stims_neg = [GratingStim(win=self.win,
                                           tex=bg_img*-1,
                                           units='pix', 
                                           mask='raisedCos',
                                           texRes=self.bg_images.shape[1],
                                           colorSpace='rgb',
                                           size=self.settings['stimuli'].get('stim_size_pixels'),
                                           interpolate=True)
                               for bg_img in self.bg_images]

        # make some examples for the instructions
        self.example1 = GratingStim(win=self.win,
                                    tex=self.bg_images[random.choice(range(0,self.bg_images.shape[0]))],
                                    units='pix', 
                                    mask='raisedCos',
                                    texRes=self.bg_images.shape[1],
                                    colorSpace='rgb',
                                    size=self.settings['stimuli'].get('stim_size_pixels')*0.6,
                                    pos=[0-self.win.size[1]//2, 0],
                                    interpolate=True)

        self.example2 = GratingStim(win=self.win,
                                    tex=self.bg_images[random.choice(range(0,self.bg_images.shape[0]))]*-1,
                                    units='pix', 
                                    mask='raisedCos',
                                    texRes=self.bg_images.shape[1],
                                    colorSpace='rgb',
                                    size=self.settings['stimuli'].get('stim_size_pixels')*0.6,
                                    pos=[0+self.win.size[1]//2, 0],
                                    interpolate=True)


        # draw all the bg stimuli once, before they are used in the trials
        for ibs in self.image_bg_stims:
            ibs.draw()

        intromask = GratingStim(self.win, tex=np.ones((4,4)), contrast=1, color=(0.0, 0.0, 0.0), size=self.settings['stimuli'].get('stim_size_pixels'))
        intromask.draw()
        self.win.flip()
        self.win.flip()

        # ITI stuff
        if self.isi_file == "None":
            total_iti_duration = self.n_trials * self.settings['design'].get('mean_iti_duration')
            min_iti_duration   = total_iti_duration - self.settings['design'].get('total_iti_duration_leeway'),
            max_iti_duration   = total_iti_duration + self.settings['design'].get('total_iti_duration_leeway')

            nits = 0
            itis = _return_itis(mean_duration=self.settings['design'].get('mean_iti_duration'),
                                minimal_duration=self.settings['design'].get('minimal_iti_duration'),
                                maximal_duration=self.settings['design'].get('maximal_iti_duration'),
                                n_trials=self.n_trials)

            while (itis.sum() < min_iti_duration) | (itis.sum() > max_iti_duration):
                itis = _return_itis(mean_duration=self.settings['design'].get('mean_iti_duration'),
                                    minimal_duration=self.settings['design'].get('minimal_iti_duration'),
                                    maximal_duration=self.settings['design'].get('maximal_iti_duration'),
                                    n_trials=self.n_trials)
                nits += 1

            print(f'ITIs created with total ITI duration of {itis.sum()} after {nits} iterations')
        else:
            itis = np.loadtxt(self.isi_file)

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
                                 keys=['q'],
                                 txt='')        

        self.trials = [instruction_trial, dummy_trial]

        # half of stimuli contains target
        self.contains_target = np.r_[np.ones(self.n_trials//2, dtype=int), np.zeros(self.n_trials//2, dtype=int)]

        # randomize target
        np.random.shuffle(self.contains_target)
        
        # make trials
        self.old_target_idx = None
        for i in range(self.n_trials):

            # create list of random images based on frequency and stim duration
            self.image_ids = random.sample(range(0, self.bg_images.shape[0]), k=int(np.ceil(self.settings['stimuli'].get('frequency')*self.duration))+1)
            
            # select images
            self.selected_imgs = [self.image_bg_stims[img] for img in self.image_ids]
                
            # select index of target image
            if self.contains_target[i] == 1:
                self.target_on = True

                # from: https://stackoverflow.com/questions/53018527/how-to-select-randomly-a-pairs-of-adjacent-elements-from-a-python-list
                # make list of target indices
                image_ids = np.arange(0,len(self.image_ids))

                # create list of pairs
                image_id_pairs = [[i, j] for i, j in zip(image_ids[:-1], image_ids[1:])]

                # select random pair
                self.target_idx = random.choice(image_id_pairs)
                self.old_target_idx = self.target_idx.copy()

                # pick two random negative images
                self.negative_idx = random.sample(range(0, self.bg_images.shape[0]), k=2)
                for ix,idx in enumerate(self.target_idx):
                    self.selected_imgs[idx] = self.image_bg_stims_neg[self.negative_idx[ix]]

            else:
                self.target_on = False
                self.target_idx = None

            print(f"Trial #{2+i}; {self.target_idx}")

            self.trials.append(TwoSidedTrial(session=self,
                                             trial_nr=2+i,
                                             phase_names=['iti', 'stim'],
                                             phase_durations=[itis[i], self.settings['design'].get ('stim_duration')],
                                             parameters={'condition': self.condition,
                                                         'fix_color_changetime': np.random.rand()*self.settings['design'].get('mean_iti_duration'),
                                                         'target': self.target_on},
                                             image_objects=self.selected_imgs,
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

# iti function based on negative exponential
def _return_itis(mean_duration, minimal_duration, maximal_duration, n_trials):
    itis = np.random.exponential(scale=mean_duration-minimal_duration, size=n_trials)
    itis += minimal_duration
    itis[itis>maximal_duration] = maximal_duration
    return itis