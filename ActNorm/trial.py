import numpy as np
from exptools2.core import Trial
from psychopy.visual import TextStim

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

        if self.phase == 1:

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
                if self.session.stim_design == "checker":
                    self.session.ActStim.draw_mask()

                self.session.draw_stim_contrast(stimulus=self.session.ActStim, contrast=contrast)
            else:
                self.session.draw_stim_contrast(stimulus=self.session.SupprStim, contrast=contrast)
                # self.session.SupprStim.draw()
                self.session.SupprMask.draw()

        # draw fixation
        self.session.change_fixation()

    def get_events(self):
        events = super().get_events()

        if self.condition == "act":
            perf = "act"
        else:
            perf = "suppr"

        if events:    
            for i,r in events:

                if i != "t":

                    hits = getattr(self.session, f"{perf}_hits")
                    miss = getattr(self.session, f"{perf}_miss")

                    # ignore responses before onset time
                    if hasattr(self, "onset_time"):
                        if r > (self.onset_time + self.session.settings['design'].get('stim_duration')/2):
                            # contrast high means it starts at low | LOW >> HIGH
                            if self.contrast == "high" and i == 'b':
                                hits +=1
                                print(f"\tHIT (response = {i})")
                            # contrast low means it starts at high | HIGH >> LOW
                            elif self.contrast == "low" and i == 'e':
                                hits +=1
                                print(f"\tHIT (response = {i})")
                            else:
                                miss +=1
                                print(f"\tMISS (response = {i})")

                            setattr(self.session, f"{perf}_hits", hits)
                            setattr(self.session, f"{perf}_miss", miss)

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

    def __init__(
        self, 
        session, 
        trial_nr, 
        phase_durations=None,
        txt="Waiting for scanner triggers.", **kwargs):

        super().__init__(session, trial_nr, phase_durations, txt, **kwargs)

    def draw(self):
        if self.phase == 0:
            self.text.draw()
        else:
            self.session.change_fixation()              

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

    def draw(self):
        # draw fixation
        self.session.change_fixation()

    def get_events(self):
        events = Trial.get_events(self)

        if events:
            for key, t in events:
                if key == 'space':
                    self.stop_phase()
