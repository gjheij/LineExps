from exptools2.core import Session, PylinkEyetrackerSession
import numpy as np
import os
import pandas as pd
from psychopy import tools
from psychopy.visual import filters, GratingStim, Circle
from stimuli import (
    BarStim, 
    pRFCue, 
    DelimiterLines)
import sys
import json
import random
from trial import (
    pRFTrial, 
    InstructionTrial, 
    DummyWaiterTrial, 
    ScreenDelimiterTrial,
    EmptyBarPassTrial)

opj = os.path.join
class pRFSession(PylinkEyetrackerSession):
    def __init__(self, output_str, output_dir, settings_file, eyetracker_on=True, params_file=None, hemi="L", screenshots=False, delimit_screen=False):
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
        screenshots: bool, optional
            Make screenshots during the experiment. Generally this will be False. Only run this offline without a subject to get the png's for the design matrix. DO NOT USE WITH A SUBJECTS!! FRAMES MIGHT BE DROPPED, SCREWING UP PRESENTATION AND TIMING!            
        delimit_screen: bool, optional
            Have the participant delineate the FOV; saves out a json-file with pixels to be removed from the design matrix. Generally only needed once, unless you have multiple designs in your experiment (might interfere otherwise with finding the json-file in `spinoza_fitprfs`). If False (= default) a json-file with the following is written:
            {
                "top": 0,
                "right": 0,
                "bottom": 0,
                "left": 0
            }
            If you have a full session of the same experiment, this is fine, as the first log-directory will be taken to create the design matrix. One solution is to copy the one created json file into all other log-directories.

        Example
        ----------
        >>> from session import pRFSession
        >>> session_object = pRFSession(output_str='sub-001_ses-2_run-1_task-PRF',
        >>>                             output_dir='logs',
        >>>                             settings_file='settings.yml',
        >>>                             eyetracker_on=True,
        >>>                             params_file='prf_params/sub-001_ses-1_desc-best_vertices',
        >>>                             hemi=hemi,
        >>>                             screenshots=False,
        >>>                             delimit_screen=True)
        """
        
        # this thing initializes exptool2.core.session
        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file, eyetracker_on=eyetracker_on)  # initialize parent class!

        # set default color of fixation dot to red 
        self.start_color = 0
        
        # set screen delimiter
        self.screen_delimit_trial = delimit_screen

        # set screenshot (directory); ONLY DO THIS OFFLINE!! SAVING SCREENSHOTS CAUSES DROPPED FRAMES
        self.screenshots = screenshots
        self.screen_dir  = opj(output_dir, output_str+'_Screenshots')
        if self.screenshots:
            os.makedirs(self.screen_dir, exist_ok=True)

        # get locations from settings file. These represent the amount of bars from the center of the stimulus
        self.output                 = opj(output_dir, output_str)
        self.span                   = self.settings['design'].get('span_locations')
        self.bar_steps              = self.settings['design'].get('bar_steps')
        self.bar_locations          = np.linspace(*self.span, self.bar_steps)
        self.duration               = self.settings['design'].get('stim_duration')
        self.frequency              = self.settings['stimuli'].get('frequency')
        self.stim_repetitions       = self.settings['design'].get('stim_repetitions')
        self.intro_trial_time       = self.settings['design'].get('start_duration')
        self.outro_trial_time       = self.settings['design'].get('end_duration')
        self.inter_sweep_blank      = self.settings['design'].get('inter_sweep_blank')
        self.bar_directions         = self.settings['stimuli'].get('bar_directions')

        # convert target site to pixels
        self.hemi = hemi
        if os.path.exists(params_file):
            self.prf_parameters = pd.read_csv(params_file).set_index('hemi')
            self.x_loc          = self.prf_parameters['x'][self.hemi]                           # position on x-axis in DVA     > sets location for cue
            self.y_loc          = self.prf_parameters['y'][self.hemi]                           # position on y-axis in DVA     > sets location for cue
            self.x_loc_pix      = tools.monitorunittools.deg2pix(self.x_loc, self.monitor)      # position on x-axis in pixels  > required for deciding on bar location below
            self.y_loc_pix      = tools.monitorunittools.deg2pix(self.y_loc, self.monitor)      # position on y-axis in pixels  > required for deciding on bar location below
        else:
            # center stuff if not parameter file is
            self.x_loc, self.y_loc, self.x_loc_pix, self.y_loc_pix = 0,0,0,0

        self.create_stimuli()
        self.create_trials()

    def create_stimuli(self):
        """create stimuli, both background bitmaps, and bar apertures
        """

        # plot the tiny pRF as marker/cue
        self.cue = pRFCue(self)

        # bar stimuli
        self.bar_widths = self.settings['stimuli'].get('bar_widths')
        self.squares_in_bar = self.settings['stimuli'].get('squares_in_bar')
        for ii in range(len(self.bar_widths)):
            bars = BarStim(session=self,
                           frequency=self.frequency,
                           bar_width=self.bar_widths[ii],
                           squares_in_bar=self.squares_in_bar[ii])
            
            for stim in bars.stimulus_1,bars.stimulus_2:
                stim.draw()

            setattr(self, f"bar_{ii}", bars)
        
        # two colors of the fixation circle for the task
        self.fixation_disk_0 = Circle(self.win, 
                                      units='pix', 
                                      size=self.settings['stimuli'].get('dot_size'),
                                      fillColor=[1,-1,-1], 
                                      lineColor=[1,-1,-1])

        self.fixation_disk_1 = Circle(self.win, 
                                      units='pix', 
                                      size=self.settings['stimuli'].get('dot_size'), 
                                      fillColor=[-1,1,-1], 
                                      lineColor=[-1,1,-1])                                       

        # delimiter stimuli
        if self.screen_delimit_trial:
            self.delim = DelimiterLines(win=self.win, 
                                        color=self.settings['stimuli'].get('cue_color'),
                                        colorSpace="hex")

    def create_trials(self):
        """ Creates trials (ideally before running your session!) """

        # screen delimiter trial
        self.cut_pixels = {"top": 0, "right": 0, "bottom": 0, "left": 0}
        if self.screen_delimit_trial:
            delimiter_trial = ScreenDelimiterTrial(session=self,
                                                   trial_nr=0,
                                                   phase_durations=[np.inf,np.inf,np.inf,np.inf],
                                                   keys=['b', 'y', 'r'],
                                                   delim_step=self.settings['stimuli'].get('delimiter_increments'))                       
        
        # decide on dummy trial ID depending on the presence of delimiter trial
        if self.screen_delimit_trial:
            dummy_id = 1
        else:
            dummy_id = 0

        # Only 1 phase of np.inf so that we can run the fixation task right of the bat
        dummy_trial = DummyWaiterTrial(session=self,
                                       trial_nr=dummy_id,
                                       phase_durations=[np.inf],
                                       txt='Waiting for scanner trigger')


        if self.screen_delimit_trial:
            self.trials = [delimiter_trial, dummy_trial]
        else:
            self.trials = [dummy_trial]

        self.init_trial = len(self.trials)
        trial_counter = len(self.trials)
        
        # baseline trial
        intro_trial = EmptyBarPassTrial(
            session=self,
            trial_nr=trial_counter,
            phase_durations=[self.intro_trial_time],
            phase_names=['stim'],
            timing='seconds',
            parameters={'condition': 'blank'},
            verbose=True)

        self.trials.append(intro_trial)
        trial_counter += 1
        start_time = self.intro_trial_time
        # iterations
        for n in range(self.stim_repetitions):
        
            # invert directions
            for inv in range(2):

                if inv == 0:
                    locations = self.bar_locations
                else:
                    locations = self.bar_locations[::-1]

                # bar widths
                for i in range(len(self.bar_widths)):

                    # bar directions
                    for j, bd in enumerate(self.bar_directions):

                        if bd < 0: # no bar
                            phase_durations = [self.inter_sweep_blank]
                            condition = "blank"

                            self.trials.append(EmptyBarPassTrial(
                                session=self,
                                trial_nr=trial_counter,
                                phase_durations=phase_durations,
                                phase_names=['stim'],
                                timing='seconds',
                                parameters={'condition': condition},
                                verbose=True)
                                )

                            trial_counter += 1
                            start_time += phase_durations[0]
                        else:
                            
                            phase_durations = [self.duration]     
                                            
                            # bar locations
                            for k, loc in enumerate(locations):
                                
                                if i > 0:
                                    self.pos_step = loc/(self.bar_widths[1]/self.bar_widths[0])
                                else:
                                    self.pos_step = loc

                                # get bar width in pixels to determine steps
                                self.bar_width_pixels = tools.monitorunittools.deg2pix(self.bar_widths[i], self.monitor)

                                # define start position (different depending on whether left or right hemi is targeted)
                                if self.hemi.upper() == "L":
                                    self.start_pos = [self.x_loc_pix, self.y_loc_pix]
                                elif self.hemi.upper() == "R":
                                    if bd == 90 or bd == 270:
                                        self.start_pos = [0-(self.win.size[1]/2), 0]
                                    else:
                                        self.start_pos = [0+(self.bar_width_pixels/2)-(self.win.size[0]/2), 0]

                                # set new position somewhere in grid
                                # if cond == "horizontal":
                                if bd == 90 or bd == 270:
                                    self.new_position = self.start_pos[1]+(self.bar_width_pixels*self.pos_step)
                                    self.set_position = [self.start_pos[0],self.new_position]
                                    condition = "horizontal"
                                else:
                                    condition = "vertical"
                                    self.new_position = self.start_pos[0]+(self.bar_width_pixels*self.pos_step)
                                    self.set_position = [self.new_position,self.start_pos[1]]
                                
                                self.trials.append(pRFTrial(
                                    session=self,
                                    trial_nr=trial_counter,
                                    phase_durations=phase_durations,
                                    phase_names=['stim'],
                                    timing='seconds',
                                    verbose=False, 
                                    position=self.set_position,
                                    orientation=bd,
                                    parameters={'condition': condition},
                                    stimulus=getattr(self, f"bar_{i}"))
                                    )

                                # update trial counter
                                trial_counter += 1
                                start_time += phase_durations[0]

        # outro trial
        outro_trial = EmptyBarPassTrial(
            session=self,
            trial_nr=trial_counter,
            phase_durations=[self.outro_trial_time],
            phase_names=['stim'],
            timing='seconds',
            parameters={'condition': 'blank'},
            verbose=True)

        self.trials.append(outro_trial)
        self.total_time = start_time + self.outro_trial_time

        print(f"Total experiment time: {self.total_time}s")
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
                                     color=[0, 0, 0])

        # create list of times at which to switch the fixation color; make a bunch more that total_time so it continues in the outro_trial
        self.dot_switch_color_times = np.arange(3, self.total_time*1.5, float(self.settings['Task_settings']['color_switch_interval']))
        self.dot_switch_color_times += (2*np.random.rand(len(self.dot_switch_color_times))-1)

        # needed to keep track of which dot to print
        self.current_dot_time=0
        self.next_dot_time=1

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

    def run(self):
        """ Runs experiment. """

        if self.eyetracker_on:
            self.calibrate_eyetracker()
            self.start_recording_eyetracker()

        self.start_experiment()
        for trial in self.trials:
            trial.run()

        # write pixels-to-remove from design matrix to json file
        fjson = json.dumps(self.cut_pixels, indent=4)
        f = open(opj(self.output+'_desc-screen.json'), "w")
        f.write(fjson)
        f.close()        
            
        self.close()
