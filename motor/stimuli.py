import numpy as np
from psychopy.visual import TextStim, ShapeStim, RadialStim, MovieStim3


class FixationCross(object):

    def __init__(self, win, lineWidth, color, *args, **kwargs):
        self.color      = color
        self.linewidth  = lineWidth
        self.fixation   = ShapeStim(
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
        
class MotorStim(object):

    def __init__(self, session):
        self.session = session

    def draw(self, text=None, **kwargs):
        self.text = TextStim(
            self.session.win, 
            text, 
            height=0.4, 
            pos=(0,-4.5),
            wrapWidth=self.session.settings['various'].get('text_width'), 
            **kwargs)
        
        self.text.draw()

class MotorMovie():

    def __init__(self, session):

        self.session = session
        x,y = self.session.win.size
        new_size = [x*0.7, y*0.7]

        # initialize movies
        self.movies = []
        for ix,ii in enumerate(self.session.movie_files):
            mov = MovieStim3(self.session.win, filename=ii, loop=True, size=new_size)
            setattr(self, f"movie{ix+1}", mov)

            self.movies.append(mov)
