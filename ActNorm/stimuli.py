import numpy as np
from psychopy.visual import RadialStim, Circle,Line

class FixationLines(object):

    def __init__(self, win, circle_radius, color, linewidth=1.5, *args, **kwargs):
        self.color = color
        self.linewidth = linewidth
        self.line1 = Line(
            win, 
            start=(-circle_radius, -circle_radius),
            end=(circle_radius, circle_radius), 
            lineColor=self.color, 
            lineWidth=self.linewidth, *args, **kwargs)

        self.line2 = Line(
            win, 
            start=(-circle_radius, circle_radius),
            end=(circle_radius, -circle_radius), 
            lineColor=self.color, 
            lineWidth=self.linewidth, *args, **kwargs)

    def draw(self):
        self.line1.draw()
        self.line2.draw()

    def setColor(self, color):
        self.line1.color = color
        self.line2.color = color
        self.color = color

class SuppressionMask():   

    def __init__(self, session):

        self.session = session
        self.size_cue = self.session.settings['stimuli'].get('cue_size')
        self.color_cue = self.session.settings['stimuli'].get('cue_color')
        self.prf_cue = Circle(
            win=self.session.win,
            size=self.session.stim_sizes[1],
            pos=(self.session.x_loc, self.session.y_loc),
            units='deg',
            fillColor=[0,0,0],
            lineColor=[0,0,0])

    def draw(self):
        self.prf_cue.draw()        

class SizeResponseStim():

    def __init__(
            self, 
            session,
            *args,
            **kwargs):

        self.session                = session
        self.frequency              = self.session.settings['stimuli'].get('frequency')

        # black and white stimulus
        self.stimulus_1 = RadialStim(
            win=self.session.win,
            # mask=mask,
            texRes=128,
            angularRes=100,
            ori=180,
            units='deg',
            color=1,
            *args,
            **kwargs)

        # white and black stimulus
        self.stimulus_2 = RadialStim(
            win=self.session.win,
            # mask=mask,
            texRes=128,
            angularRes=100,
            ori=180,
            units='deg',      
            color=-1,
            *args,
            **kwargs)

    def draw(self):

        phase = np.fmod(self.session.settings['design'].get('stim_duration')+self.session.timer.getTime(), 1.0/self.frequency) * self.frequency
        if phase < 0.5:
            self.stimulus_1.draw()
        else:
            self.stimulus_2.draw()
