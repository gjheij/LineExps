import numpy as np
from psychopy.visual import TextStim, ShapeStim, RadialStim, MovieStim3


class FixationCross(object):

    def __init__(self, win, lineWidth, color, *args, **kwargs):
        self.color      = color
        self.linewidth  = lineWidth
        self.fixation   = ShapeStim(win, 
                                    vertices=((0, -0.5), (0, 0.5), (0,0), (-0.5,0), (0.5, 0)),
                                    lineWidth=self.linewidth,
                                    closeShape=False,
                                    lineColor=self.color)

    def draw(self):
        self.fixation.draw()


class MotorStim(object):

    def __init__(self, session, text=None, **kwargs):

        self.session = session
        self.text = TextStim(self.session.win, text, height=self.session.stim_height, wrapWidth=self.session.stim_width, **kwargs)

    def draw(self, text=None, **kwargs):
        self.text = TextStim(self.session.win, text, height=self.session.stim_height, wrapWidth=self.session.stim_width, **kwargs)
        self.text.draw()

class MotorMovie():

    def __init__(self, session):

        self.session = session
        x,y = self.session.win.size
        new_size = [x*0.5, y*0.5]
        self.movie1 = MovieStim3(self.session.win, filename=self.session.movie_files[0], loop=True, size=new_size)
        self.movie2 = MovieStim3(self.session.win, filename=self.session.movie_files[1], loop=True, size=new_size)