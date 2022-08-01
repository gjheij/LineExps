import numpy as np
from exptools2.core import Trial
from psychopy.visual import TextStim
import os
opj = os.path.join


class pRFTrial(Trial):

    def __init__(self, session, trial_nr, phase_durations, phase_names, parameters, timing, position, orientation, stimulus, verbose=True):
        """ Initializes a pRFTrial object.

        Parameters
        ----------
        session : exptools Session object
            A Session object (needed for metadata)
        trial_nr: int
            Trial nr of trial
        phase_durations : array-like
            List/tuple/array with phase durations
        phase_names : array-like
            List/tuple/array with names for phases (only for logging),
            optional (if None, all are named 'stim')
        parameters : dict
            Dict of parameters that needs to be added to the log of this trial
        timing : str
            The "units" of the phase durations. Default is 'seconds', where we
            assume the phase-durations are in seconds. The other option is
            'frames', where the phase-"duration" refers to the number of frames.
        position: tuple, optional
            Tuple denoting the new location of the bar. If [ix,0], the y-component remains the same, which means the bar sweeps from L>R. If [0,ix], it means the x-component remains the same. The bar sweeps Up>Down (vice versa)
        orientation: int, optional
            The default bar is horizontal; if '0' is specified, the bar is horizontal, if '90', we have a vertical bar.
        stimulus: pRFStim-object, optional
            Specify a thin/thick bar. Defined in `session.use_stimulus`
        verbose : bool
            Whether to print extra output (mostly timing info)
        """
        
        # this thing initializes exptools2.core.trial. Most stuff is required for logging
        super().__init__(session, trial_nr, phase_durations, phase_names, parameters, timing, load_next_during_phase=None, verbose=verbose)

        # these we actually need here
        self.parameters     = parameters
        self.frame_count    = 0
        self.position       = position
        self.orientation    = orientation
        self.stimulus       = stimulus
        
    def run(self):

        if self.parameters['condition'] != 'blank':
            self.stimulus.stimulus_1.setOri(self.orientation)
            self.stimulus.stimulus_1.setPos(self.position)
            self.stimulus.stimulus_2.setOri(self.orientation)
            self.stimulus.stimulus_2.setPos(self.position)

        # calls exptools2/core/trial.py
        super().run()

    def draw(self):
        
        self.frame_count += 1
        if self.parameters['condition'] != 'blank':

            phase = np.fmod(self.session.settings['design'].get('stim_duration')+self.session.timer.getTime(), 1.0/self.session.frequency) * self.session.frequency
            if phase < 0.5:
                self.stimulus.stimulus_1.draw()
            else:
                self.stimulus.stimulus_2.draw()                

            self.session.mask_stim.draw()

        # pRF cue
        self.session.cue.draw()
        
        # fixation task
        if self.frame_count == 1:
            if self.parameters['fix_color_changetime'] == True:
                if self.session.start_color == 0:
                    self.session.fixation_disk_0.setColor([-1,1,-1])
                    self.session.start_color = 1
                elif self.session.start_color == 1:
                    self.session.fixation_disk_0.setColor([1,-1,-1])
                    self.session.start_color = 0
        elif self.frame_count == 2:
            # only do screenshotting offline to avoid dropping of frames DURING the experiment
            if self.session.screenshots:
                fname = opj(self.session.screen_dir, self.session.output_str+'_Screenshots{}.png'.format(str(self.trial_nr-2).rjust(len(str(self.session.n_trials)),'0')))
                self.session.win.getMovieFrame()
                self.session.win.saveMovieFrames(fname)                    

        self.session.fixation_disk_0.draw()

class ScreenDelimiterTrial(Trial):

    def __init__(self, session, trial_nr, phase_durations=[np.inf,np.inf,np.inf,np.inf], keys=None, delim_step=10, **kwargs):

        super().__init__(session, trial_nr, phase_durations, **kwargs)
        self.session = session
        self.keys = keys
        self.increments = delim_step
        self.txt_height = self.session.settings['various'].get('text_height')*1.5
        self.txt_width = self.session.settings['various'].get('text_width')*4

    def draw(self, **kwargs):

        if self.phase == 0:
            txt = """
Use your right INDEX finger (or 'b') to move the bar UP
Use your right RING finger (or 'y') to move the bar DOWN
            

Use your right PINKY (or 'r') to continue to the next stage"""
            self.start_pos = (-self.session.win.size[0]//2,self.session.win.size[1]//3)
            self.session.delim.line1.start = self.start_pos
            self.session.delim.line1.end = (self.session.win.size[0],self.start_pos[1])
        elif self.phase == 1:
            txt = """
Use your right INDEX (or 'b') finger to move the bar RIGHT
Use your right RING (or 'y') finger to move the bar LEFT
            

Use your right PINKY (or 'r') to continue to the next stage"""
            self.start_pos = (self.session.win.size[0]//2.5,-self.session.win.size[1]//2)
            self.session.delim.line1.start = self.start_pos
            self.session.delim.line1.end = (self.start_pos[0],self.session.win.size[1])     
        elif self.phase == 2:
            txt = """
Use your right INDEX (or 'b') finger to move the bar DOWN
Use your right RING (or 'y') finger to move the bar UP
            

Use your right PINKY (or 'r') to continue to the next stage"""
            self.start_pos = (-self.session.win.size[0]//2,-self.session.win.size[1]//3)
            self.session.delim.line1.start = self.start_pos
            self.session.delim.line1.end = (self.session.win.size[0],self.start_pos[1])
        elif self.phase == 3:
            txt = """
Use your right INDEX (or 'b') finger to move the bar LEFT
Use your right RING (or 'y') finger to move the bar RIGHT
            

Use your right PINKY (or 'r') to continue to the experiment"""
            self.start_pos = (-self.session.win.size[0]//2.5,-self.session.win.size[1]//2)
            self.session.delim.line1.start = self.start_pos 
            self.session.delim.line1.end = (self.start_pos[0],self.session.win.size[1])     

        self.text = TextStim(self.session.win, 
                             txt, 
                             height=self.txt_height, 
                             wrapWidth=self.txt_width, 
                             **kwargs)
        self.session.delim.draw()
        self.text.draw()

    def get_events(self):
        events = super().get_events()

        if self.keys is None:
            if events:
                self.stop_phase()
        else:
            for key, t in events:
                if key == "q":
                    self.stop_phase()
                elif key == "b":
                    if self.phase == 0:
                        self.session.delim.line1.pos[1] += self.increments
                    elif self.phase == 1:
                        self.session.delim.line1.pos[0] += self.increments
                    elif self.phase == 2:
                        self.session.delim.line1.pos[1] -= self.increments
                    elif self.phase == 3:
                        self.session.delim.line1.pos[0] -= self.increments
                elif key == "y":
                    if self.phase == 0:
                        self.session.delim.line1.pos[1] -= self.increments
                    elif self.phase == 1:
                        self.session.delim.line1.pos[0] -= self.increments
                    elif self.phase == 2:
                        self.session.delim.line1.pos[1] += self.increments
                    elif self.phase == 3:
                        self.session.delim.line1.pos[0] += self.increments
                elif key == "r":
                    self.final_position = [self.start_pos[ii]+self.session.delim.line1.pos[ii] for ii in range(len(self.start_pos))]
                    if self.phase == 0:
                        self.session.cut_pixels['top'] = int((self.session.win.size[1]//2) - self.final_position[1])
                    elif self.phase == 1:
                        self.session.cut_pixels['right'] = int((self.session.win.size[0]//2) - abs(self.final_position[0]))
                    elif self.phase == 2:
                        self.session.cut_pixels['bottom'] = int((self.session.win.size[1]//2) - abs(self.final_position[1]))
                    elif self.phase == 3:
                        self.session.cut_pixels['left'] = int((self.session.win.size[0]//2) - abs(self.final_position[0]))

                        print(self.session.cut_pixels)

                    self.stop_phase()             
                    self.session.delim.line1.pos = (0,0)

class InstructionTrial(Trial):
    """ Simple trial with instruction text. """

    def __init__(self, session, trial_nr, phase_durations=[np.inf],
                 txt=None, keys=None, **kwargs):

        super().__init__(session, trial_nr, phase_durations, **kwargs)

        txt_height  = self.session.settings['various'].get('text_height')
        txt_width   = self.session.settings['various'].get('text_width')

        if txt is None:
            txt = '''Press any button to continue.'''

        self.text = TextStim(self.session.win, txt, height=txt_height, wrapWidth=txt_width, **kwargs)
        self.keys = keys

    def draw(self):
        self.session.fixation_disk_0.draw()
        self.text.draw()

    def get_events(self):
        events = super().get_events()

        if self.keys is None:
            if events:
                self.stop_phase()
        else:
            for key, t in events:
                if key in self.keys:
                    self.stop_phase()


class DummyWaiterTrial(InstructionTrial):
    """ Simple trial with text (trial x) and fixation. """

    def __init__(self, session, trial_nr, phase_durations=None,
                 txt="Waiting for scanner triggers.", **kwargs):

        super().__init__(session, trial_nr, phase_durations, txt, **kwargs)

    def draw(self):
        self.session.fixation_disk_0.draw()
        if self.phase == 0:
            self.text.draw()

    def get_events(self):
        events = Trial.get_events(self)

        if events:
            for key, t in events:
                if key == self.session.mri_trigger:
                    if self.phase == 0:
                        self.stop_phase()

class OutroTrial(InstructionTrial):
    """ Simple trial with only fixation cross.  """

    def __init__(self, session, trial_nr, phase_durations, txt='', **kwargs):

        txt = ''''''
        super().__init__(session, trial_nr, phase_durations, txt=txt, **kwargs)

    def get_events(self):
        events = Trial.get_events(self)

        if events:
            for key, t in events:
                if key == 'space':
                    self.stop_phase()  
