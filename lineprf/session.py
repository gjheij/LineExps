from exptools2.core import Session, PylinkEyetrackerSession
import numpy as np
import os
import pandas as pd
from psychopy import tools
from psychopy.visual import filters, GratingStim, Circle
import scipy.stats as ss
from stimuli import BarStim, PRFStim
from trial import pRFTrial, InstructionTrial, DummyWaiterTrial, OutroTrial

opj = os.path.join
class pRFSession(PylinkEyetrackerSession):
    def __init__(self, output_str, output_dir, settings_file, eyetracker_on=True, params_file=None, hemi="L"):
        """ Initializes pRFSession.

        Parameters
        ----------
        output_str: str
            Basename for all output-files (like logs), e.g., "sub-01_task-stroop_run-1"
        output_dir: str
            Path to desired output-directory (default: None, which results in $pwd/logs)
        settings_file: str
            Path to yaml-file with settings (default: None, which results in the package's
            default settings file (in data/default_settings.yml)
        eyetracker_on: bool, optional
            Turn on eyetracker; requires that pylink is installed, default = True
        params_file: str, optional
            pRF parameter file as per the output of `call_targetvertex` in `linescanning/bin` folder. File will be read in and indexed on `hemi`. Then, it will look for the `x`, `y`, and `size` parameters to set the target site around which the bars will be presented. Should be placed in the 'prf_params'-folder with matching subject-IDs
        hemi: str, optional
            Hemisphere to utilize the pRF parameters from, default = 'L'

        Example
        ----------
        >>> from session import pRFSession
        >>> session_object = pRFSession(output_str='sub-001_ses-2_run-1_task-PRF',
        >>>                             output_dir='logs',
        >>>                             settings_file='settings.yml',
        >>>                             eyetracker_on=True,
        >>>                             params_file='prf_params/sub-001_ses-1_desc-best_vertices',
        >>>                             hemi=hemi)            
        """
        
        # this thing initializes exptool2.core.session
        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file, eyetracker_on=eyetracker_on)  # initialize parent class!

        # set default color of fixation dot to red 
        self.start_color = 0

        # get locations from settings file. These represent the amount of bars from the center of the stimulus
        self.horizontal_locations   = self.settings['design'].get('horizontal_locations')
        self.vertical_locations     = self.settings['design'].get('vertical_locations')
        self.duration               = self.settings['design'].get('stim_duration')
        self.frequency              = self.settings['stimuli'].get('frequency')
        self.stim_repetitions       = self.settings['design'].get('stim_repetitions')
        self.current_stim           = 1
        self.outro_trial_time       = self.settings['design'].get('end_duration')

        # convert target site to pixels
        self.hemi = hemi
        if params_file:
            self.prf_parameters = pd.read_csv(params_file).set_index('hemi')
            self.x_loc          = self.prf_parameters['x'][self.hemi]                           # position on x-axis in DVA     > sets location for cue
            self.y_loc          = self.prf_parameters['y'][self.hemi]                           # position on y-axis in DVA     > sets location for cue
            self.x_loc_pix      = tools.monitorunittools.deg2pix(self.x_loc, self.monitor)      # position on x-axis in pixels  > required for deciding on bar location below
            self.y_loc_pix      = tools.monitorunittools.deg2pix(self.y_loc, self.monitor)      # position on y-axis in pixels  > required for deciding on bar location below

        # plot the tiny pRF as marker/cue
        self.prf = PRFStim(self)

        # thin bar
        self.bar_width_deg_thin = self.settings['stimuli'].get('bar_width_deg')
        self.thin_bar   = BarStim(session=self,
                                  frequency=self.frequency,
                                  bar_width=self.bar_width_deg_thin,
                                  squares_in_bar=self.settings['stimuli'].get('squares_in_bar'))

        # thick bar
        self.bar_width_deg_thick = self.bar_width_deg_thin*2
        self.thick_bar  = BarStim(session=self,
                                  frequency=self.frequency,
                                  bar_width=self.bar_width_deg_thick,
                                  squares_in_bar=self.settings['stimuli'].get('squares_in_bar')*2)

        #two colors of the fixation circle for the task
        self.fixation_disk_0 = Circle(self.win, 
                                      units='deg', 
                                      radius=self.settings['stimuli'].get('fix_radius'), 
                                      fillColor=[1,-1,-1], 
                                      lineColor=[1,-1,-1])   
        
        self.fixation_disk_1 = Circle(self.win, 
                                      units='deg', 
                                      radius=self.settings['stimuli'].get('fix_radius'), 
                                      fillColor=[-1,1,-1], 
                                      lineColor=[-1,1,-1])

        print(f"Screen size = {self.win.size}")

    def create_design(self):
        """ Creates design (ideally before running your session!) """

        ## contains two bar passes (vertical/horizontal)
        self.two_bar_pass_design = np.array([np.arange(0,len(self.vertical_locations)) for i in ['vertical', 'horizontal']]).flatten().astype(int)

        ## define rest period for 2*bar pass
        self.rest = np.full(int(len(self.vertical_locations)*2),-1)

        ## contains two bar passes, rest period, for thin/thick bars
        self.block_design = np.r_[self.two_bar_pass_design, 
                                  self.rest,
                                  self.two_bar_pass_design].astype(int)

        ## contains two bar passes, rest period, and reverse (1 iter = 640)
        self.part_design = np.r_[self.block_design,
                                 self.rest,
                                 self.block_design[::-1],
                                 self.rest].astype(int)

        # track design iterations
        self.iter_design = np.r_[[np.full_like(self.part_design,i+1) for i in range(self.stim_repetitions)]].flatten().astype(int)

        ## contains 'block_design' x times
        self.full_design = np.r_[[self.part_design for i in range(self.stim_repetitions)]].flatten().astype(int)

        # keep track of thin/thick bars
        self.thin   = np.r_[[np.zeros(len(self.vertical_locations)) for i in range(2)]].flatten()
        self.thick  = np.r_[[np.ones(len(self.vertical_locations)) for i in range(2)]].flatten()
        
        # matches "part_design"
        self.bar_rest = np.full(len(self.rest), 2)
        self.thin_thick = np.r_[self.thin,              # first sweep is thin bars
                                self.bar_rest,          # then rest
                                self.thick,             # second sweep is thick bars
                                self.bar_rest,          # then rest
                                self.thin,              # third sweep is thin bars reversed
                                self.bar_rest,          # then rest 
                                self.thick,             # final sweep is thick bars reversed
                                self.bar_rest].flatten().astype(int)
        
        # matches "full_design"
        self.thin_thick = np.r_[[self.thin_thick for i in range(self.stim_repetitions)]].flatten().astype(int)

        print(f'full design has shape {self.full_design.shape}; running {self.stim_repetitions} iteration(s) of experiment')

        # keep track of orientations (horizontal/vertical); matches "two_bar_pass_design"
        self.oris = np.r_[np.zeros(len(self.vertical_locations)), 
                          np.ones(len(self.vertical_locations))]

        # matches "block_design"
        self.oris_block = np.r_[self.oris,
                                np.full(len(self.rest),2),
                                self.oris].flatten().astype(int)
        
        # matches "part_design"
        self.oris_part = np.r_[self.oris_block,
                               self.rest,
                               self.oris_block,
                               self.rest].astype(int)                          
        
        # matches "full_design"
        self.oris_full = np.r_[[self.oris_part for i in range(self.stim_repetitions)]].flatten().astype(int)

        # set n_trials
        self.n_trials = len(self.oris_full)
        print(f'n_trials has shape {self.n_trials}')

    def create_trials(self):
        """ Creates trials (ideally before running your session!) """

        # fixation changes:
        self.p_change           = self.settings['design'].get('fix_change_prob')
        self.change_fixation    = np.zeros_like(self.full_design)
        self.n_switch           = len(self.full_design) * self.p_change
        self.interval           = int(len(self.change_fixation)/self.n_switch)
        self.change_fixation[::self.interval] = 1
        self.change_fixation.astype(bool)

        # timing
        self.total_experiment_time = self.settings['design'].get('start_duration') + self.settings['design'].get('end_duration') + (self.n_trials*self.duration)
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

        self.trials = [instruction_trial, dummy_trial]

        # keep track of orientation we're traversing through (horizontal or verticals)
        vert = 0
        hori = 0

        # loop through trials
        for i in range(self.n_trials):

            # get which step we're at for horizontal/vertical steps
            cond = ['horizontal', 'vertical', 'blank'][self.oris_full[i]]
            if cond == "vertical":
                pos_step = self.vertical_locations[self.full_design[i]]
                vert += 1
            elif cond == "horizontal":
                pos_step = self.horizontal_locations[self.full_design[i]]
                hori += 1

            # divide by two to make thick bar travers the plane in the same manner as thin bar
            thick = ['thin', 'thick', 'rest'][self.thin_thick[i]]
            if thick == "thick":
                pos_step /= 2
                self.bar_width_degrees = self.bar_width_deg_thick
                self.use_stimulus = self.thick_bar
            elif thick == 'thin':
                self.bar_width_degrees = self.bar_width_deg_thin
                self.use_stimulus = self.thin_bar

            # convert bar widths to pixels
            self.bar_width_pixels = tools.monitorunittools.deg2pix(self.bar_width_degrees, self.monitor)

            # set starting position of bars depending on orientation and hemifield
            if self.hemi.upper() == "L":
                self.start_pos = [self.x_loc_pix, self.y_loc_pix]
            elif self.hemi.upper() == "R":
                if trial == "horizontal":
                    self.start_pos = [0-(self.win.size[1]/2), 0]
                else:
                    self.start_pos = [0+(self.bar_width_pixels/2)-(self.win.size[0]/2), 0]        

            # set new position somewhere in grid
            if cond == "horizontal":
                self.ori = 90
                new_pos = self.start_pos[1]+(self.bar_width_pixels*pos_step)
                self.pos = [self.start_pos[0],new_pos]
            else:
                self.ori = 0
                new_pos = self.start_pos[0]+(self.bar_width_pixels*pos_step)
                self.pos = [new_pos,self.start_pos[1]]

            # append trial
            self.trials.append(pRFTrial(session=self,
                                        trial_nr=2+i,
                                        phase_durations=[self.duration],
                                        phase_names=['stim'],
                                        parameters={'condition': cond,
                                                    'thickness': thick,
                                                    'fix_color_changetime': self.change_fixation[i],
                                                    'step': pos_step,
                                                    'design_iteration': self.iter_design[i],
                                                    'hemi': self.hemi},
                                        timing='seconds',
                                        position=self.pos,
                                        orientation=self.ori,
                                        stimulus=self.use_stimulus,
                                        verbose=False))
        self.trials.append(outro_trial)

        # the fraction of [x_rad,y_rad] controls the size of aperture. Default is [1,1] (whole screen, like in Marco's experiments)
        y_rad = self.settings['stimuli'].get('fraction_aperture_size') 
        x_rad = (self.win.size[1]/self.win.size[0])*y_rad

        mask = filters.makeMask(matrixSize=self.win.size[0],
                                shape='raisedCosine',
                                radius=np.array([x_rad,y_rad]),
                                center=((1/(self.win.size[0]/2))*self.x_loc_pix, (1/(self.win.size[1]/2)*self.y_loc_pix)),
                                range=[-1, 1],
                                fringeWidth=0.02)

        mask_size = [self.win.size[0], self.win.size[1]]
        self.mask_stim = GratingStim(self.win,
                                     mask=-mask,
                                     tex=None,
                                     units='pix',
                                     size=mask_size,
                                     #pos=np.array((self.x_loc_pix,self.y_loc_pix)),
                                     color=[0, 0, 0])

    def run(self):
        """ Runs experiment. """

        if self.eyetracker_on:
            self.calibrate_eyetracker()

        self.start_experiment()

        if self.eyetracker_on:
            self.start_recording_eyetracker()
        for trial in self.trials:
            trial.run()

        self.close()
