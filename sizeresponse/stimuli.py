import numpy as np
from psychopy.visual import TextStim, Line, RadialStim, Circle

class FixationLines(object):

    def __init__(self, win, circle_radius, color, linewidth=1.5, *args, **kwargs):
        self.color = color
        self.linewidth = linewidth
        self.line1 = Line(win, 
                          start=(-circle_radius, -circle_radius),
                          end=(circle_radius, circle_radius), 
                          lineColor=self.color, 
                          lineWidth=self.linewidth, *args, **kwargs)

        self.line2 = Line(win, 
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
        

class pRFCue(object):   

    def __init__(self, session):

        self.session        = session
        self.size_cue       = self.session.settings['stimuli'].get('cue_size')
        self.color_cue      = self.session.settings['stimuli'].get('cue_color')
        self.prf_cue        = Circle(win=self.session.win,
                                     size=(self.size_cue, self.size_cue),
                                     pos=(self.session.x_loc, self.session.y_loc),
                                     units='deg',
                                     fillColor=self.color_cue,
                                     lineColor=[0, 0, 0],
                                     opacity=0.1,
                                     edges=128)

    def draw(self):
        self.prf_cue.draw()        

class SizeResponseStim(object):

    def __init__(self, session):

        self.session                = session
        self.border_radius          = self.session.settings['stimuli'].get('border_radius')
        self.n_mask_pixels          = self.session.settings['stimuli'].get('n_mask_pixels')
        self.angular_cycles         = self.session.settings['stimuli'].get('angular_cycles')
        self.radial_cycles          = self.session.settings['stimuli'].get('radial_cycles')
        self.border_radius          = self.session.settings['stimuli'].get('border_radius')
        self.pacman_angle           = self.session.settings['stimuli'].get('pacman_angle')
        self.frequency              = self.session.settings['stimuli'].get('frequency')

        # construct gradient on the outside of stimuli; avoid hard borders > wonky stuff happens
        mask = np.ones((self.n_mask_pixels))
        mask[-int(self.border_radius*self.n_mask_pixels):] = (np.cos(np.linspace(0,np.pi,int(self.border_radius*self.n_mask_pixels)))+1)/2
        mask[:int(self.border_radius*self.n_mask_pixels)] = (np.cos(np.linspace(0,np.pi,int(self.border_radius*self.n_mask_pixels))[::-1])+1)/2

        self.stimulus_1 = RadialStim(win=self.session.win,
                                     mask=mask,
                                     angularCycles=self.angular_cycles,
                                     texRes=128,
                                     angularRes=100,
                                     pos=(self.session.x_loc, self.session.y_loc),
                                     ori=180,
                                     units='deg')

        self.stimulus_2 = RadialStim(win=self.session.win,
                                     mask=mask,
                                     angularCycles=self.angular_cycles,
                                     texRes=128,
                                     angularRes=100,
                                     pos=(self.session.x_loc, self.session.y_loc),
                                     ori=180,
                                     units='deg')                          

    def draw(self, size=None, contrast=None):

        phase = np.fmod(self.session.settings['design'].get('stim_duration')+self.session.timer.getTime(), 1.0/self.frequency) * self.frequency

        # contrast options contains 2 contrast types, low (0.6) and high (1)
        contrast_options = self.session.settings['stimuli'].get('contrasts')
        if contrast == 'low':
            select_contrast = contrast_options[0]
        elif contrast == 'high':
            select_contrast = contrast_options[1]

        # print(f'Contrast = {select_contrast}')
            
        # update size and contrast
        if phase < 0.5:
            self.stimulus_1.setColor(select_contrast)
            self.stimulus_1.setSize(size, units='deg')
            self.stimulus_1.setRadialCycles(self.radial_cycles*size)            
            self.stimulus_1.draw()
        else:
            self.stimulus_2.setColor(-select_contrast)
            self.stimulus_2.setSize(size, units='deg')
            self.stimulus_2.setRadialCycles(self.radial_cycles*size)            
            self.stimulus_2.draw()