import numpy as np
from exptools2.core import Trial
from psychopy.visual import TextStim

class SizeResponseTrial(Trial):

    def __init__(self, session, trial_nr, phase_durations, phase_names,
                 parameters, timing,
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
        super().__init__(session, trial_nr, phase_durations, phase_names,
                         parameters, timing, load_next_during_phase=None, verbose=verbose)
        self.condition          = self.parameters['condition']
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
            self.presentation_time = self.session.timer.getTime()
            if self.presentation_time > -self.session.settings['design'].get('cue_time'):
                self.session.report_fixation.setColor(self.session.settings['stimuli'].get('cue_color'))
        
        if self.phase == 1:
            self.session.report_fixation.setColor(self.session.settings['stimuli'].get('fix_color'))

            self.frame_count += 1

            # store the start contrast for later reference to response
            if self.frame_count == 1:
                self.session.start_contrast = self.parameters['contrast']
                msg = f"\tStimulus size: {self.condition:.5f}"
                print(msg)

            # switch contrast mid-way
            self.presentation_time = self.session.timer.getTime()
            if (self.presentation_time > -self.session.settings['design'].get('stim_duration')/2):
                if self.parameters['contrast'] == 'high':
                    contrast = 'low'
                elif self.parameters['contrast'] == 'low':
                    contrast = 'high'
            else:
                contrast = self.parameters['contrast']
            

            self.session.SizeStim.draw(size=self.condition, contrast=contrast)

        # draw pRF-location to screen for illustrative purposes
        self.session.cue.draw()
        self.session.fixation.draw()
        self.session.report_fixation.draw()


    def get_events(self):
        events = super().get_events()

        if events:    
            for i,r in events:
                self.session.responses += 1
                if self.session.start_contrast == 'high' and i == self.session.button_options[0]:
                    self.session.correct_responses += 1
                elif self.session.start_contrast == 'low' and i == self.session.button_options[1]:
                    self.session.correct_responses += 1

                print(f"Contrast was '{self.session.start_contrast}'; response was {i}")


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
        self.session.cue.draw()
        self.session.fixation.draw()
        self.session.report_fixation.draw()
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
        self.session.cue.draw()
        self.session.fixation.draw()
        if self.phase == 0:
            self.text.draw()
        else:
            self.session.report_fixation.draw()

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
