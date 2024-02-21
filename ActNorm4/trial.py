import numpy as np
from exptools2.core import Trial
from psychopy.visual import TextStim
import os
from psychopy import tools
p2d = tools.monitorunittools.pix2deg
d2p = tools.monitorunittools.deg2pix

opj = os.path.join

class SizeResponseTrial(Trial):

    def __init__(
        self, 
        session, 
        trial_nr, 
        phase_durations, 
        phase_names,
        parameters, 
        timing,
        verbose=True):
        """ Initializes a StroopTrial object.

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
        verbose : bool
            Whether to print extra output (mostly timing info)
        """
        super().__init__(
            session, 
            trial_nr, 
            phase_durations, 
            phase_names,
            parameters, 
            timing, 
            load_next_during_phase=None, 
            verbose=verbose)
            
        self.condition          = self.parameters['condition']
        self.contrast           = self.parameters['contrast']
        self.presentation_time  = 0
        self.fix_changed        = False
        self.frame_count        = 0
        self.verbose            = verbose

    def create_trial(self):
        pass

    def run(self):
        pass
        super().run()

    def draw(self):

        if self.phase == 0:

            self.frame_count += 1
            self.onset_time = self.session.timer.getTime()

            # store the start contrast for later reference to response
            if self.frame_count == 1:
                msg = f"\tstimulus: {self.condition} | contrast = {self.contrast}"
                print(msg)

            if self.session.fix_task != "fix":
                # switch contrast mid-way
                self.presentation_time = self.session.timer.getTime()
                if (self.presentation_time > -self.session.settings['design'].get('stim_duration')/2):
                    if self.contrast == 'high':
                        contrast = 'low'
                    elif self.contrast == 'low':
                        contrast = 'high'
                else:
                    contrast = self.contrast
            else:
                contrast = None

            # update stimulus characteristics depending on which stimulus
            if self.condition == "act":
                self.session.draw_stim_contrast(stimulus=self.session.stims[self.condition], contrast=contrast)
            else:
                self.session.draw_stim_contrast(stimulus=self.session.stims[self.condition]["stim"], contrast=contrast)
                # self.session.SupprStim.draw()
                self.session.stims[self.condition]["mask"].draw()


        if self.frame_count == 2:
            if self.session.screenshots:
                self.session.win.getMovieFrame()
                fname = opj(self.session.screen_dir, self.session.output_str+'_Screenshots{}.png'.format(str(self.trial_nr)))
                self.session.win.saveMovieFrames(fname)
                
        # draw fixation
        self.session.change_fixation()

    def get_events(self):
        events = super().get_events()

        if events:    
            for i,r in events:

                if i != "t":
                    
                    self.session.total_responses += 1
                    #tracking percentage of correct responses per session
                    if self.session.dot_count <= len(self.session.dot_switch_color_times): 
                        print(f"\tResponse: {r}")
                        if r > self.session.dot_switch_color_times[self.session.dot_count-1] and \
                            r < self.session.dot_switch_color_times[self.session.dot_count-1] + float(self.session.settings['Task_settings']['response_interval']):
                            self.session.correct_responses +=1 
                            print(f'\tFIXATION TASK | #correct {self.session.correct_responses}') #testing

        # update counter
        if self.session.fix_task in ["fix","both"]:
            if self.session.dot_count < len(self.session.dot_switch_color_times): 
                switch_time = self.session.clock.getTime()
                if switch_time > self.session.dot_switch_color_times[self.session.dot_count]:
                    self.session.dot_count += 1   
                    print(f'\tSWITCH COLOR: {switch_time}') #testing
                    self.session.actual_dot_switch_color_times.append(switch_time)

class ScreenDelimiterTrial(Trial):

    def __init__(
        self, 
        session, 
        trial_nr, 
        phase_durations=[np.inf,np.inf,np.inf,np.inf], 
        keys=None, 
        delim_step=10, 
        **kwargs):

        super().__init__(
            session, 
            trial_nr, 
            phase_durations, 
            **kwargs)

        self.session = session
        self.keys = keys
        self.increments = delim_step
        self.txt_height = self.session.settings['various'].get('text_height')
        self.txt_width = self.session.settings['various'].get('text_width')

    def draw(self, **kwargs):

        if self.phase == 0:
            txt = """
Tell the experimenter when you see a horizontal line on the screen"""
            self.start_pos = (-self.session.win.size[0]//2,self.session.win.size[1]//3)
            self.session.delim.line1.start = self.start_pos
            self.session.delim.line1.end = (self.session.win.size[0],self.start_pos[1])
        elif self.phase == 1:
            txt = """
Tell the experimenter when you see a vertical line on the screen"""
            self.start_pos = (self.session.win.size[0]//2.5,-self.session.win.size[1]//2)
            self.session.delim.line1.start = self.start_pos
            self.session.delim.line1.end = (self.start_pos[0],self.session.win.size[1])     
        elif self.phase == 2:
            txt = """
Tell the experimenter when you see a horizontal line on the screen"""
            self.start_pos = (-self.session.win.size[0]//2,-self.session.win.size[1]//3)
            self.session.delim.line1.start = self.start_pos
            self.session.delim.line1.end = (self.session.win.size[0],self.start_pos[1])
        elif self.phase == 3:
            txt = """
Tell the experimenter when you see a vertical line on the screen"""
            self.start_pos = (-self.session.win.size[0]//2.5,-self.session.win.size[1]//2)
            self.session.delim.line1.start = self.start_pos 
            self.session.delim.line1.end = (self.start_pos[0],self.session.win.size[1])     

        self.text = TextStim(
            self.session.win, 
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
                print(key)
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

    def __init__(
        self, 
        session, 
        trial_nr, 
        phase_durations=[np.inf],
        txt=None, 
        keys=None, 
        *args,
        **kwargs):

        super().__init__(
            session, 
            trial_nr, 
            phase_durations, 
            *args,
            **kwargs)

        txt_height = self.session.settings['various'].get('text_height')
        txt_width = self.session.settings['various'].get('text_width')

        if txt is None:
            txt = '''Press any button to continue.'''

        self.text = TextStim(
            self.session.win, 
            txt, 
            height=txt_height, 
            wrapWidth=txt_width
        )
        self.keys = keys

    def draw(self):
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

    def __init__(
        self, 
        session, 
        trial_nr, 
        phase_durations=None,
        txt="Waiting for scanner triggers.", 
        *args,
        **kwargs):

        self.txt = txt
        super().__init__(
            session, 
            trial_nr, 
            phase_durations, 
            self.txt, 
            *args,
            **kwargs
        )

    def draw(self):
        if self.phase == 0:
            if isinstance(self.txt, str):
                self.text.draw()
            else:
                self.session.change_fixation()
        else:
            self.session.change_fixation()

    def get_events(self):
        events = Trial.get_events(self)

        if events:
            for key, r in events:
                if key == self.session.mri_trigger:
                    if self.phase == 0:
                        self.stop_phase()
                        self.session.experiment_start_time = self.session.clock.getTime()
                        print(self.session.experiment_start_time)
                else:
                    if key != "t":
                        
                        self.session.total_responses += 1

                        #tracking percentage of correct responses per session
                        if self.session.dot_count <= len(self.session.dot_switch_color_times): 
                            print(f"\tResponse: {r}")
                            if r > self.session.dot_switch_color_times[self.session.dot_count-1] and \
                                r < self.session.dot_switch_color_times[self.session.dot_count-1] + float(self.session.settings['Task_settings']['response_interval']):
                                self.session.correct_responses +=1 
                                print(f'\tFIXATION TASK | #correct {self.session.correct_responses}') #testing

        # update counter
        if self.session.fix_task in ["fix","both"]:
            if self.session.dot_count < len(self.session.dot_switch_color_times): 
                switch_time = self.session.clock.getTime()
                if switch_time > self.session.dot_switch_color_times[self.session.dot_count]:
                    self.session.dot_count += 1   
                    print(f'\tSWITCH COLOR: {switch_time}') #testing
                    self.session.actual_dot_switch_color_times.append(switch_time)

class OutroTrial(InstructionTrial):
    """ Simple trial with only fixation cross.  """

    def __init__(self, session, trial_nr, phase_durations, txt='', **kwargs):

        txt = ''''''
        super().__init__(session, trial_nr, phase_durations, txt=txt, **kwargs)

    def draw(self):
        # draw fixation
        self.session.change_fixation()

    def get_events(self):
        events = Trial.get_events(self)

        if events:
            for key, r in events:
                if key == 'space':
                    self.stop_phase()
                else:
                    if key != "t":
                        
                        self.session.total_responses += 1

                        #tracking percentage of correct responses per session
                        if self.session.dot_count <= len(self.session.dot_switch_color_times): 
                            print(f"\tResponse: {r}")
                            if r > self.session.dot_switch_color_times[self.session.dot_count-1] and \
                                r < self.session.dot_switch_color_times[self.session.dot_count-1] + float(self.session.settings['Task_settings']['response_interval']):
                                self.session.correct_responses +=1 
                                print(f'\tFIXATION TASK | #correct {self.session.correct_responses}') #testing

        # update counter
        if self.session.fix_task in ["fix","both"]:
            if self.session.dot_count < len(self.session.dot_switch_color_times): 
                switch_time = self.session.clock.getTime()
                if switch_time > self.session.dot_switch_color_times[self.session.dot_count]:
                    self.session.dot_count += 1   
                    print(f'\tSWITCH COLOR: {switch_time}') #testing
                    self.session.actual_dot_switch_color_times.append(switch_time)
