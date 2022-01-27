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
        self.duration = self.settings['design'].get('stim_duration')
        self.intended_experiment_time = self.settings['design'].get('intended_duration')
        self.frequency = self.settings['stimuli'].get('frequency')
        self.stim_repetitions = self.settings['design'].get('stim_repetitions')
        self.n_trials = int(len(self.horizontal_locations)+len(self.vertical_locations))*self.stim_repetitions
        self.current_stim = 1

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

        self.prf = PRFStim(self)

        self.thin_bar = HemiFieldStim(session=self,
                angular_cycles=self.settings['stimuli'].get('angular_cycles'),
                radial_cycles=self.settings['stimuli'].get('radial_cycles'),
                border_radius=self.settings['stimuli'].get('border_radius'),
                pacman_angle=self.settings['stimuli'].get('pacman_angle'),
                n_mask_pixels=self.settings['stimuli'].get('n_mask_pixels'),
                frequency=self.frequency,
                bar_width=self.settings['stimuli'].get('bar_width_deg'),
                squares_in_bar=self.settings['stimuli'].get('squares_in_bar'))

        self.thick_bar = HemiFieldStim(session=self,
                angular_cycles=self.settings['stimuli'].get('angular_cycles'),
                radial_cycles=self.settings['stimuli'].get('radial_cycles'),
                border_radius=self.settings['stimuli'].get('border_radius'),
                pacman_angle=self.settings['stimuli'].get('pacman_angle'),
                n_mask_pixels=self.settings['stimuli'].get('n_mask_pixels'),
                frequency=self.frequency,
                bar_width=self.settings['stimuli'].get('bar_width_deg')*2,
                squares_in_bar=self.settings['stimuli'].get('squares_in_bar')*2)

        #two colors of the fixation circle for the task
        self.fixation_disk_0 = Circle(self.win, 
            units='deg', radius=self.settings['stimuli'].get('fix_radius'), 
            fillColor=[1,-1,-1], lineColor=[1,-1,-1])
        
        self.fixation_disk_1 = Circle(self.win, 
            units='deg', radius=self.settings['stimuli'].get('fix_radius'), 
            fillColor=[-1,1,-1], lineColor=[-1,1,-1])

        print(f"Screen size = {self.win.size}")

    def create_trials(self):
        """ Creates trials (ideally before running your session!) """

        # Create full design up front
        ## contains two bar passes (vertical/horizontal)
        two_bar_pass_design = np.array([np.arange(0,len(self.vertical_locations)) for i in ['vertical', 'horizontal']]).flatten().astype(int)
        rest = np.full(int(len(self.vertical_locations)*2),-1)

        ## contains two bar passes, rest period, for thin/thick bars
        block_design = np.r_[two_bar_pass_design, 
                             rest,
                             two_bar_pass_design].astype(int)

        ## contains two bar passes, rest period, and reverse (1 iter = 640)
        part_design = np.r_[block_design,
                            rest,
                            block_design[::-1],
                            rest].astype(int)

        # track design iterations
        iter_design = np.r_[[np.full_like(part_design,i+1) for i in range(self.stim_repetitions)]].flatten().astype(int)

        ## contains 'block_design' x times
        full_design = np.r_[[part_design for i in range(self.stim_repetitions)]].flatten().astype(int)

        # keep track of thin/thick bars
        thin = np.r_[[np.zeros(len(self.vertical_locations)) for i in range(2)]].flatten()
        thick = np.r_[[np.ones(len(self.vertical_locations)) for i in range(2)]].flatten()
        
        # matches "part_design"
        thin_thick = np.r_[thin, np.full(len(rest), 2), thick, np.full(len(rest), 2), thin, np.full(len(rest), 2), thick, np.full(len(rest), 2)].flatten().astype(int)
        
        # matches "full_design"
        thin_thick = np.r_[[thin_thick for i in range(self.stim_repetitions)]].flatten().astype(int)

        print(f'full design has shape {full_design.shape}; running {self.stim_repetitions} iteration(s) of experiment')

        # keep track of orientations (horizontal/vertical); matches "two_bar_pass_design"
        oris = np.r_[np.zeros(len(self.vertical_locations)), 
                     np.ones(len(self.vertical_locations))]

        # matches "block_design"
        oris_block = np.r_[oris,
                          np.full(len(rest),2),
                          oris].flatten().astype(int)
        
        # matches "part_design"
        oris_part = np.r_[oris_block,
                          rest,
                          oris_block,
                          rest].astype(int)                          
        
        # matches "full_design"
        oris_full = np.r_[[oris_part for i in range(self.stim_repetitions)]].flatten().astype(int)

        # fixation changes:
        p_change = self.settings['design'].get('fix_change_prob')
        # self.change_fixation = np.r_[[(np.random.choice(a=[True, False], size=len(full_design), p=[p_change, 1-p_change])) for i in range(self.stim_repetitions)]].flatten()
        
        self.change_fixation = np.zeros_like(full_design)
        n_switch = len(full_design) * p_change
        interval = int(len(self.change_fixation)/n_switch)
        self.change_fixation[::interval] = 1
        self.change_fixation.astype(bool)

        self.n_trials = len(oris_full)
        self.total_experiment_time = self.settings['design'].get('start_duration') + self.settings['design'].get('end_duration') + (self.n_trials*self.duration)
        print(f"Total experiment time: {round(self.total_experiment_time,2)}s")
        
        # pad experiment time at the end
        if self.intended_experiment_time != 0:
            if self.total_experiment_time < self.intended_experiment_time:
                add_time =  (self.intended_experiment_time - self.total_experiment_time)
                self.outro_trial_time = self.settings['design'].get('end_duration') + add_time
                print(f"Adding {round(add_time,2)}s to outro trial duration to match intended experiment time of {self.intended_experiment_time}s")
            elif self.total_experiment_time > self.intended_experiment_time:
                remove_time = (self.total_experiment_time - self.intended_experiment_time)
                if remove_time > self.settings['design'].get('end_duration'):
                    print("WARNING: time to cut exceeds baseline time at the end of the experiment. Please increase 'intended_experiment_time', or decrease number of iterations")
                    self.outro_trial_time = self.settings['design'].get('end_duration')
                else:
                    self.outro_trial_time = self.settings['design'].get('end_duration') - remove_time
                    print(f"Cutting {round(remove_time,2)}s from outro trial duration to match intended experiment time of {self.intended_experiment_time}s")
        else:
            self.outro_trial_time = self.settings['design'].get('end_duration')

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

        # print(full_design)
        vert = 0
        hori = 0

        print(f'n_trials has shape {self.n_trials}')
        # self.design_matrix = np.ones((self.win.size[1],self.win.size[0],self.n_trials))
        # print(self.design_matrix.shape)
        # track zeros in full_design. Uneven = thin; even = thick
        self.zero_count = 0
        for i in range(self.n_trials):

            if full_design[i] == 0:
                self.zero_count += 1

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

            thick = ['thin', 'thick', 'rest'][thin_thick[i]]
            if thick == "thick":
                pos_step /= 2 # divide by two to make thick bar travers the plane in the same manner as thin bar
                self.bar_width_degrees = self.settings['stimuli'].get('bar_width_deg')*2        
            elif thick == 'thin':
                self.bar_width_degrees = self.settings['stimuli'].get('bar_width_deg')

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

            self.trials.append(TwoSidedTrial(session=self,
                                            trial_nr=2+i,
                                            phase_durations=[self.duration],
                                            phase_names=['stim'],
                                            parameters={'condition': cond,
                                                        'thickness': thick,
                                                        'fix_color_changetime': self.change_fixation[i],
                                                        'step': pos_step,
                                                        'position': self.pos, 
                                                        'orientation': self.ori,
                                                        'design_iteration': iter_design[i],
                                                        'hemi': self.hemi},
                                            timing='seconds',
                                            verbose=True))
        self.trials.append(outro_trial)

        #generate raised cosine alpha mask
        y_rad = self.settings['stimuli'].get('fraction_aperture_size') # the fraction of [x_rad,y_rad] controls the size of aperture. Default is [1,1] (whole screen, like in Marco's experiments)
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

    # def create_trial(self):
    #     pass

    def run(self):
        """ Runs experiment. """
        self.create_trials()  # create them *before* running!

        if self.eyetracker_on:
            self.calibrate_eyetracker()

        self.start_experiment()

        if self.eyetracker_on:
            self.start_recording_eyetracker()
        for trial in self.trials:
            trial.run()
        # self.win.saveMovieFrames(opj(self.screen_dir, self.output_str+'_Screenshot.png'))
        # np.save(opj(self.screen_dir, self.output_str+'_DesignMatrix.npy'), self.design_matrix)
        self.close()
