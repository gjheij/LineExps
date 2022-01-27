import numpy as np
from exptools2.core import Trial
from psychopy.visual import TextStim
from stimuli import FixationLines
from psychopy import tools
import os
opj = os.path.join

class TwoSidedTrial(Trial):

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

        self.parameters = parameters
        self.frame_count = 0
        
    def run(self):

        if self.parameters['condition'] != 'blank':

            if  self.parameters['thickness'] == 'thin':
                self.draw_this_stim = self.session.thin_bar
            elif self.parameters['thickness'] == 'thick':
                self.draw_this_stim = self.session.thick_bar

            self.draw_this_stim.stimulus_1.setOri(self.parameters['orientation'])
            self.draw_this_stim.stimulus_1.setPos(self.parameters['position'])
            self.draw_this_stim.stimulus_2.setOri(self.parameters['orientation'])
            self.draw_this_stim.stimulus_2.setPos(self.parameters['position'])

        super().run()

    def draw(self):
        
        self.frame_count += 1
        if self.parameters['condition'] != 'blank':

            phase = np.fmod(self.session.settings['design'].get('stim_duration')+self.session.timer.getTime(), 1.0/self.session.frequency) * self.session.frequency
            if phase < 0.5:
                self.draw_this_stim.stimulus_1.draw()
            else:
                self.draw_this_stim.stimulus_2.draw()                

            self.session.mask_stim.draw()

        # pRF cue
        self.session.prf.draw()
        
        # fixation task
        if self.frame_count == 1:
            if self.parameters['fix_color_changetime'] == True:
                if self.session.start_color == 0:
                    self.session.fixation_disk_0.setColor([-1,1,-1])
                    self.session.start_color = 1
                elif self.session.start_color == 1:
                    self.session.fixation_disk_0.setColor([1,-1,-1])
                    self.session.start_color = 0
        # elif self.frame_count == 2:
        #     self.session.win.getMovieFrame()
        #     fname = opj(self.session.screen_dir, self.session.output_str+'_Screenshots{}.png'.format(str(self.trial_nr-2).rjust(len(str(self.session.n_trials)),'0')))
        #     self.session.win.saveMovieFrames(fname)

            # img = np.array(self.session.win.movieFrames[0])
            # sum_channels = np.sum(img,axis=-1)
            # median_img = np.median(sum_channels)

            # binary = sum_channels != median_img
            # self.session.design_matrix[...,self.trial_nr-2] = binary
            # self.session.win.movieFrames = []

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
