import numpy as np
from exptools2.core import Trial
from psychopy.visual import TextStim
from stimuli import FixationLines
from linescanning.utils import reverse_sign
import os
opj = os.path.join

class TwoSidedTrial(Trial):

    def __init__(self, session, trial_nr, phase_durations, phase_names,
                 parameters, timing, step=None, hemi=None,
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
        self.condition = self.parameters['condition']
        self.fix_changed = False
        self.trial_count = 0
        self.step_nr = step

    def create_trial(self):
        pass

    def run(self):
        if self.parameters['condition'] == 'center':
            self.session.hemistim.stimulus_1.ori = 0
            self.session.hemistim.stimulus_2.ori = 0
        else:
            self.session.hemistim.stimulus_1.ori = 180
            self.session.hemistim.stimulus_2.ori = 180
        super().run()

    def draw(self):
        if self.phase == 1:
            self.trial_count += 1
            # draw aperture around pRF
            # self.session.aperture.draw()
            if self.parameters['condition'] != 'blank':
                self.session.hemistim.draw(trial=self.parameters['condition'], position=self.step_nr)
                self.session.mask_stim.draw()

            # not sure why it is two, but if you do 1 it's still blank
            if self.trial_count == 2:
                self.session.win.getMovieFrame()

        # ################################################################q###############################################
        # # COMMENT OUT DURING REAL EXPERIMENT!
        # ###############################################################################################################
        self.session.prf.draw()
        # ###############################################################################################################

        # self.session.fixation.draw()
        # self.session.report_fixation.draw()

        # print(self.parameters['fix_color_changetime']+self.session.timer.getTime())
        # if (self.parameters['fix_color_changetime']+self.session.timer.getTime() > 5) & (not self.fix_changed):
        #     self.session.report_fixation.setColor(-self.session.report_fixation.color)
        #     self.fix_changed = True

        if self.trial_count == 1:
            print(f"start_color = {self.session.start_color}; switch = {self.parameters['fix_color_changetime']}")
            if self.parameters['fix_color_changetime'] == True:
            
                if self.session.start_color == 0:
                    self.session.fixation_disk_0.setColor([-1,1,-1])
                    self.session.start_color = 1
                elif self.session.start_color == 1:
                    self.session.fixation_disk_0.setColor([1,-1,-1])
                    self.session.start_color = 0

        self.session.fixation_disk_0.draw()

class InstructionTrial(Trial):
    """ Simple trial with instruction text. """

    def __init__(self, session, trial_nr, phase_durations=[np.inf],
                 txt=None, keys=None, **kwargs):

        super().__init__(session, trial_nr, phase_durations, **kwargs)

        txt_height = self.session.settings['various'].get('text_height')
        txt_width = self.session.settings['various'].get('text_width')

        if txt is None:
            txt = '''Press any button to continue.'''

        self.text = TextStim(self.session.win, txt,
                             height=txt_height, wrapWidth=txt_width, **kwargs)

        self.keys = keys

    def draw(self):
        # self.session.fixation.draw()
        # self.session.report_fixation.draw()

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
        # self.session.report_fixation.draw()
        self.session.fixation_disk_0.draw()
        if self.phase == 0:
            self.text.draw()
        else:
            # self.session.report_fixation.draw()
            pass

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
