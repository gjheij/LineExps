import numpy as np
from exptools2.core import Trial
from psychopy.visual import TextStim

class MotorTrial(Trial):

    def __init__(self, session, trial_nr, phase_durations, phase_names,
                 parameters, timing, verbose=True):
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
        super().__init__(session, trial_nr, phase_durations, phase_names,
                         parameters, timing, load_next_during_phase=None, verbose=verbose)
        self.condition  = self.parameters['condition']
        self.session    = session

    def run(self):
        if self.condition == "bilateral":
            self.display_instructions = f"clench BOTH HANDS"
        else:
            self.display_instructions = f"clench {self.condition.upper()} HAND"

        super().run()

    def draw(self):
        if self.phase == 0:
            self.presentation_time = self.session.timer.getTime()
            if self.presentation_time > -self.session.settings['design'].get('cue_time'):
                self.session.fixation.setColor(self.session.settings['stimuli'].get('cue_color'))
                        
        if self.phase == 1:  

            # reset fixation cross color
            self.session.fixation.setColor(self.session.fixation_color)            

            # # present instructions
            # self.session.motorstim.draw(text=self.display_instructions)

            # show correct video
            if self.condition == "bilateral":
                self.session.motormovie.movie1.draw()
            elif self.condition == "left":
                self.session.motormovie.movie2.draw()
            elif self.condition == "right":
                self.session.motormovie.movie3.draw()                
        else:
            self.session.fixation.draw()

    def get_events(self):
        events = super().get_events()


class InstructionTrial(Trial):
    """ Simple trial with instruction text. """

    def __init__(self, session, trial_nr, phase_durations=[np.inf],
                 txt=None, keys=None, **kwargs):

        super().__init__(session, trial_nr, phase_durations, **kwargs)

        txt_height = self.session.settings['various'].get('text_height')
        txt_width = self.session.settings['various'].get('text_width')

        if txt is None:
            txt = '''Press any button to continue.'''

        self.text = TextStim(self.session.win, txt, height=txt_height, wrapWidth=txt_width, **kwargs)
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

    def __init__(self, session, trial_nr, phase_durations=None,
                 txt="Waiting for scanner trigger", **kwargs):

        super().__init__(session, trial_nr, phase_durations, txt, **kwargs)

    def draw(self):
        if self.phase == 0:
            self.text.draw()
        else:
            self.session.fixation.draw()

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
        self.session.fixation.draw()

    def draw(self):
        self.session.fixation.draw()
        
    def get_events(self):
        events = Trial.get_events(self)

        if events:
            for key, t in events:
                if key == 'space':
                    self.stop_phase()
