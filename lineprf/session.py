import numpy as np
import scipy.stats as ss
import pandas as pd
import os
opj = os.path.join

from exptools2.core import Session, PylinkEyetrackerSession
from stimuli import FixationLines, HemiFieldStim, PRFStim
from trial import TwoSidedTrial, InstructionTrial, DummyWaiterTrial, OutroTrial
from psychopy import tools
from psychopy.visual import filters, GratingStim, Circle

class TwoSidedSession(PylinkEyetrackerSession):
    def __init__(self, output_str, output_dir, settings_file, eyetracker_on=True, params_file=None, hemi="L"):
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
        self.screen_dir = output_dir+'/'+output_str+'_Screenshots'
        if not os.path.exists(self.screen_dir):
            os.mkdir(self.screen_dir)

        # set default color to red
        self.start_color = 0

        # self.n_trials = self.settings['design'].get('n_trials')

        # get locations from settings file. These represent the amount of bars from the center of the stimulus
        self.horizontal_locations = self.settings['design'].get('horizontal_locations')
        self.horizontal_locations = self.horizontal_locations
        self.vertical_locations = self.settings['design'].get('vertical_locations')

        self.stim_repetitions = self.settings['design'].get('stim_repetitions')
        self.duration = self.settings['design'].get('stim_duration')
        self.n_trials = int(len(self.horizontal_locations)+len(self.vertical_locations))*self.stim_repetitions
        
        self.fixation = FixationLines(win=self.win,
                                      circle_radius=self.settings['stimuli'].get('fix_radius'),
                                      color=0,
                                      linewidth=self.settings['stimuli'].get('fix_line_width'))

        self.report_fixation = FixationLines(win=self.win, 
                                            circle_radius=self.settings['stimuli'].get('fix_radius'),
                                            color=self.settings['stimuli'].get('fix_color'))

        self.hemi = hemi
        if params_file:
            self.prf_parameters = pd.read_csv(params_file).set_index('hemi')
            self.size_prf = self.prf_parameters['size'][self.hemi]
            self.x_loc = self.prf_parameters['x'][self.hemi]
            self.y_loc = self.prf_parameters['y'][self.hemi]

            self.size_prf_pix = tools.monitorunittools.deg2pix(self.size_prf, self.monitor)
            self.x_loc_pix = tools.monitorunittools.deg2pix(self.x_loc, self.monitor)
            self.y_loc_pix = tools.monitorunittools.deg2pix(self.y_loc, self.monitor)

        self.hemistim = HemiFieldStim(session=self,
                angular_cycles=self.settings['stimuli'].get('angular_cycles'),
                radial_cycles=self.settings['stimuli'].get('radial_cycles'),
                border_radius=self.settings['stimuli'].get('border_radius'),
                pacman_angle=self.settings['stimuli'].get('pacman_angle'),
                n_mask_pixels=self.settings['stimuli'].get('n_mask_pixels'),
                frequency=self.settings['stimuli'].get('frequency'))

        self.prf = PRFStim(self)

        #two colors of the fixation circle for the task
        self.fixation_disk_0 = Circle(self.win,
                                      units='deg', radius=self.settings['stimuli'].get('fix_radius'),
                                      fillColor=[1, -1, -1], lineColor=[1, -1, -1])

        self.fixation_disk_1 = Circle(self.win,
                                      units='deg', radius=self.settings['stimuli'].get('fix_radius'),
                                      fillColor=[-1, 1, -1], lineColor=[-1, 1, -1])

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

        # Create full design up front
        test_chunk = np.array([np.arange(0,len(self.vertical_locations)) for i in ['vertical', 'horizontal']]).flatten().astype(int)
        part_design = np.r_[test_chunk, np.zeros(len(self.vertical_locations)), test_chunk[::-1]].astype(int)
        full_design = np.r_[[part_design for i in range(self.stim_repetitions)]].flatten().astype(int)

        oris = np.r_[np.zeros(len(self.vertical_locations)),    # Up/down
                     np.ones(len(self.horizontal_locations)),   # Right/left
                     np.full(len(self.vertical_locations),2),   # Rest
                     np.zeros(len(self.vertical_locations)),    # Down/up
                     np.ones(len(self.horizontal_locations))].astype(int)   # Left/Right

        oris_full = np.r_[[oris for i in range(self.stim_repetitions)]].flatten().astype(int)
        
        # fixation changes:
        p_change = self.settings['design'].get('fix_change_prob')
        self.change_fixation = change_fixation = np.r_[[(np.random.choice(a=[True, False], size=len(full_design), p=[p_change, 1-p_change])) for i in range(self.stim_repetitions)]].flatten()

        self.n_trials = len(oris_full)

        total_iti_duration = self.n_trials * self.settings['design'].get('mean_iti_duration')
        min_iti_duration = total_iti_duration - self.settings['design'].get('total_iti_duration_leeway'),
        max_iti_duration = total_iti_duration + self.settings['design'].get('total_iti_duration_leeway')

        if not self.settings['design'].get('use_static_isi'):
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

            self.total_time = itis.sum()
        else:

            itis = np.full(len(oris_full), self.settings['design'].get('static_isi'))
            self.total_time = self.n_trials*self.settings['design'].get('stim_duration')+self.settings['design'].get('end_duration')
        
        print(f"Total experiment time: {round(itis.sum() + self.settings['design'].get('start_duration') + self.settings['design'].get('end_duration') + (self.n_trials*self.duration),2)}s")


        # parameters
        left_rights = np.r_[np.ones(self.n_trials//2, dtype=int), np.zeros(self.n_trials//2, dtype=int)]
        
        ###############################################################################################################
        # UNCOMMENT DURING REAL EXPERIMENT!
        ###############################################################################################################
        # np.random.shuffle(left_rights)
        # np.random.shuffle(self.horizontal_locations)
        # np.random.shuffle(self.vertical_locations)
        ###############################################################################################################

        position = {"vertical": np.r_[[np.full((len(self.vertical_locations)*self.stim_repetitions)//len(self.vertical_locations), i) for i,e in enumerate(self.vertical_locations)]].flatten(),
                    "horizontal": np.r_[[np.full((len(self.horizontal_locations)*self.stim_repetitions)//len(self.horizontal_locations), i) for i,e in enumerate(self.horizontal_locations)]].flatten()}

        # print(f"There are {position['vertical'].shape[0]} vertical trials")
        # print(f"There are {position['horizontal'].shape[0]} horizontal trials")

        self.trials = [instruction_trial, dummy_trial]

        print(full_design)
        vert = 0
        hori = 0
        for i in range(self.n_trials):

            # get which step we're at for horizontal/vertical steps
            cond = ['horizontal', 'vertical', 'blank'][oris_full[i]]
            if cond == "vertical":
                # idx = position[cond][vert]
                pos_step = self.vertical_locations[full_design[i]]
                vert += 1
            elif cond == "horizontal":
                # idx = position[cond][hori]
                pos_step = self.horizontal_locations[full_design[i]]
                hori += 1

            self.trials.append(TwoSidedTrial(session=self,
                                            trial_nr=2+i,
                                            phase_durations=[itis[i], self.settings['design'].get('stim_duration')],
                                            phase_names=['iti', 'stim'],
                                            parameters={'condition': cond,
                                                        'fix_color_changetime': self.change_fixation[i]},
                                            step=pos_step,
                                            timing='seconds',
                                            hemi=self.hemi,
                                            verbose=True))
        self.trials.append(outro_trial)

        #generate raised cosine alpha mask
        y_rad = 0.5
        x_rad = (self.win.size[1]/self.win.size[0])*y_rad

        mask = filters.makeMask(matrixSize=self.win.size[0],
                                shape='raisedCosine',
                                radius=np.array([x_rad,y_rad]),
                                center=(0,0),
                                range=[-1, 1],
                                fringeWidth=0.02)

        mask_size = [self.win.size[0], self.win.size[1]]
        self.mask_stim = GratingStim(self.win,
                                     mask=-mask,
                                     tex=None,
                                     units='pix',
                                     size=mask_size,
                                     pos=np.array((self.x_loc_pix,self.y_loc_pix)),
                                     color=[0, 0, 0])


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
        self.win.saveMovieFrames(opj(self.screen_dir, self.output_str+'_Screenshot.png'))

        self.close()
