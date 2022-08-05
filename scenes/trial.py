import numpy as np
from exptools2.core import Trial
from psychopy.visual import TextStim
from psychopy.core import getTime
from stimuli import FixationLines
import math, time
import random 

class TwoSidedTrial(Trial):

    def __init__(self, session, trial_nr, phase_durations, phase_names,
                 parameters, timing, image_objects=None,
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

        self.fix_changed = False
        self.bg_display_frame = -1

        # random.choices can create duplicates; random.sample doesn't 
        # https://stackoverflow.com/questions/70565925/how-to-disable-duplicated-items-in-random-choice
        # self.image_ids = random.sample(range(0, self.session.bg_images.shape[0]), k=int(np.ceil(self.session.settings['stimuli'].get('frequency')*self.session.duration)))

        self.image_objects = image_objects
        self.start_time = getTime()
        self.trial_nr = trial_nr
        self.target_on = parameters['target']
        self.target_idx = parameters['target_idx']
        self.frame_count = 0
        self.frame_count2 = 0

    def create_trial(self):
        pass

    def run(self):
        pass
        super().run()

    def draw(self):
        if self.phase == 0:
            self.phase0_time = getTime()
            self.frame_count += 1
            if self.frame_count == 1:
                print(f"Target: {self.target_on}")
        elif self.phase == 1: 
            total_display_time = (getTime() - self.phase0_time)
            bg_display_frame = int(math.floor(total_display_time * self.session.frequency))
            
            if bg_display_frame != self.bg_display_frame:
                self.bg_display_frame = bg_display_frame
            else:
                # write onset of target to event file
                if self.target_on:
                    if bg_display_frame == self.target_idx:
                        target_onset = self.session.clock.getTime()
                        self.frame_count2 += 1
                        if self.frame_count2 == 1:
                            print(f"Trial ID: {self.trial_nr}")
                        self.session.global_log.loc[self.session.global_log["trial_nr"] == self.trial_nr, "target_onset"] = target_onset # - self.session.exp_start

                self.image_objects[self.bg_display_frame].draw()

        self.session.fixation.draw()
        self.session.report_fixation.draw()
            
    def get_events(self):
        events = super().get_events()

        if events:    
            for i,r in events:
                self.session.total_responses += 1

                print(f"\tResponse: {i}")
                if self.target_on == True and i == 'b':
                    self.session.correct_responses += 1
                elif self.target_on == False and i == 'b':
                    self.session.false_alarms +=1
                else:
                    self.session.missed_responses += 1

        else:
            # no event and target False = correct rejection
            if self.target_on == True:
                self.session.correct_rejection += 1

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

        # make example textStim
        self.text_example1 = TextStim(self.session.win, 
                                      "Example of POSITIVE image",
                                      height=txt_height, wrapWidth=txt_width, 
                                      pos=(self.session.example1.pos[0], self.session.example1.pos[1]-self.session.example1.size[1]//2),
                                      units='pix', 
                                      **kwargs)

        self.text_example2 = TextStim(self.session.win, 
                                      "Example of NEGATIVE image",
                                      height=txt_height, wrapWidth=txt_width, 
                                      pos=(self.session.example2.pos[0], self.session.example2.pos[1]-self.session.example2.size[1]//2),
                                      units='pix', 
                                      **kwargs)                                      
        self.text_objs = [self.text_example1, self.text_example2]

    def draw(self):
        # self.session.fixation.draw()
        # self.session.report_fixation.draw()

        # self.text.draw()

        for ix,ex in enumerate([self.session.example1, self.session.example2]):
            ex.draw()
            self.text_objs[ix].draw()

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
                    self.session.experiment_start_time = getTime()
                    if self.phase == 0:
                        self.stop_phase()

class OutroTrial(Trial):
    """ Simple trial with only fixation cross.  """

    def __init__(self, session, trial_nr, phase_durations=[np.inf],
                 txt=None, keys=None, **kwargs):

        super().__init__(session, trial_nr, phase_durations, **kwargs)

        txt_height = self.session.settings['various'].get('text_height')
        txt_width = self.session.settings['various'].get('text_width')

        txt = ''''''
        self.text = TextStim(self.session.win, txt,
                             height=txt_height, wrapWidth=txt_width, **kwargs)

        self.keys = keys
    
    def draw(self):
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
