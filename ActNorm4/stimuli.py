import numpy as np
from psychopy.visual import (
    RadialStim, 
    Circle,
    GratingStim,
    Line, 
    ShapeStim,
    filters)
from psychopy import visual

class FixationCross(object):

    def __init__(self, win, lineWidth, color, *args, **kwargs):
        self.color = color
        self.linewidth = lineWidth
        self.fixation = ShapeStim(
            win, 
            vertices=((0, -0.1), (0, 0.1), (0,0), (-0.1,0), (0.1, 0)),
            lineWidth=self.linewidth,
            closeShape=False,
            lineColor=self.color)

    def draw(self):
        self.fixation.draw()

    def setColor(self, color):
        self.fixation.color = color
        self.color = color

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

    def __init__(
        self, 
        session, 
        **kwargs):

        self.session = session
        self.size_cue = self.session.settings['stimuli'].get('cue_size')
        self.color_cue = self.session.settings['stimuli'].get('cue_color')
        self.prf_cue = Circle(
            win=self.session.win,
            units='deg',
            fillColor=[0,0,0],
            lineColor=[0,0,0],
            **kwargs)
        
    def draw(self):
        self.prf_cue.draw()        

class DelimiterLines(object):

    def __init__(self, win, color, *args, **kwargs):
        self.color = color
        self.line1 = visual.Line(
            win, 
            lineWidth=3, 
            lineColor=self.color, 
            opacity=0.3, 
            units="pix",
            *args, 
            **kwargs)

    def draw(self):
        self.line1.draw()

class SizeResponseStim():

    def __init__(
        self, 
        session,
        duration,
        *args,
        **kwargs):

        self.session = session
        self.duration = duration
        self.frequency = self.session.settings['stimuli'].get('frequency')

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
        
    def draw(self, contrast=None):

        phase = np.fmod(self.duration+self.session.timer.getTime(), 1.0/self.frequency) * self.frequency
        
        # contrast options contains 2 contrast types, low (0.6) and high (1)
        if isinstance(contrast, str):
            if contrast == 'low':
                select_contrast = self.contrast_options[0]
            elif contrast == 'high':
                select_contrast = self.contrast_options[1]
            
            # update contrast
            if phase < 0.5:
                self.stimulus_1.setColor(select_contrast)
                self.stimulus_1.draw()
            else:
                self.stimulus_2.setColor(-select_contrast)        
                self.stimulus_2.draw()
        else:
            if phase < 0.5:
                self.stimulus_1.draw()
            else:
                self.stimulus_2.draw()

    def draw_mask(self):
        self.mask_stim.draw()
