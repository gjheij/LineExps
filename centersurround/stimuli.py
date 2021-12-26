import numpy as np
from psychopy.visual import TextStim, Line, RadialStim, Circle
from psychopy import tools


class FixationLines(object):

    def __init__(self, win, circle_radius, color, *args, **kwargs):
        self.color = color
        self.line1 = Line(win, start=(-circle_radius, -circle_radius),
                          end=(circle_radius, circle_radius), lineColor=self.color, *args, **kwargs)
        self.line2 = Line(win, start=(-circle_radius, circle_radius),
                          end=(circle_radius, -circle_radius), lineColor=self.color, *args, **kwargs)

    def draw(self):
        self.line1.draw()
        self.line2.draw()

    def setColor(self, color):
        self.line1.color = color
        self.line2.color = color
        self.color = color
        

class PRFStim(object):   

    def __init__(self, session):

        self.session = session

        if hasattr(self.session, 'prf_parameters'):
            self.size_prf = self.session.prf_parameters['size'][self.session.hemi]
            self.x_loc = self.session.prf_parameters['x'][self.session.hemi]
            self.y_loc = self.session.prf_parameters['y'][self.session.hemi]

            self.size_prf_pix = tools.monitorunittools.deg2pix(self.size_prf, self.session.monitor)
            self.x_loc_pix = tools.monitorunittools.deg2pix(self.x_loc, self.session.monitor)
            self.y_loc_pix = tools.monitorunittools.deg2pix(self.y_loc, self.session.monitor)
        else:
            self.size_prf = 1000.0

        self.prf_stimulus = Circle(win=self.session.win,
                                    size=(self.size_prf_pix, self.size_prf_pix),
                                    pos=(self.x_loc_pix, self.y_loc_pix),
                                    units='pix',
                                    fillColor="#65CC14",
                                    lineColor=[0, 0, 0],
                                    opacity=0.5,
                                    edges=128)

    def draw(self):
        self.prf_stimulus.draw()        

class HemiFieldStim(object):

    def __init__(self,
                session,
                angular_cycles,
                radial_cycles,
                border_radius,
                pacman_angle=20,
                n_mask_pixels=1000,
                frequency=8.0):

        self.session = session
        self.angular_cycles = angular_cycles
        self.radial_cycles = radial_cycles
        self.border_radius = border_radius
        self.pacman_angle = pacman_angle
        self.n_mask_pixels = n_mask_pixels
        self.frequency = frequency

        mask = np.ones((n_mask_pixels))
        mask[-int(border_radius*n_mask_pixels):] = (np.cos(np.linspace(0,np.pi,int(border_radius*n_mask_pixels)))+1)/2
        mask[:int(border_radius*n_mask_pixels)] = (np.cos(np.linspace(0,np.pi,int(border_radius*n_mask_pixels))[::-1])+1)/2

        if hasattr(self.session, 'prf_parameters'):
            self.size_prf = self.session.prf_parameters['size'][self.session.hemi]
            self.x_loc = self.session.prf_parameters['x'][self.session.hemi]
            self.y_loc = self.session.prf_parameters['y'][self.session.hemi]

            self.size_prf_pix = tools.monitorunittools.deg2pix(self.size_prf, self.session.monitor)
            self.x_loc_pix = tools.monitorunittools.deg2pix(self.x_loc, self.session.monitor)
            self.y_loc_pix = tools.monitorunittools.deg2pix(self.y_loc, self.session.monitor)

            print(f"target pRF-size: {self.size_prf} [{self.size_prf_pix}px]")
            print(f"target pRF x_loc: {self.x_loc} [{self.x_loc_pix}px]")
            print(f"target pRF y_loc: {self.y_loc} [{self.y_loc_pix}px]")
        else:
            self.size_prf = 1000.0

        self.stimulus_1 = RadialStim(win=self.session.win,
                                    mask=mask,
                                    size=(self.size_prf_pix,self.size_prf_pix),
                                    radialCycles=self.radial_cycles,
                                    angularCycles=self.angular_cycles,
                                    texRes=128,
                                    angularRes=100,
                                    pos=(self.x_loc_pix, self.y_loc_pix),
                                    ori=180,
                                    color=1,
                                    units='pix')

        self.stimulus_2 = RadialStim(win=self.session.win,
                                    mask=mask,
                                    size=(self.size_prf_pix,self.size_prf_pix),
                                    radialCycles=self.radial_cycles,
                                    angularCycles=self.angular_cycles,
                                    texRes=128,
                                    angularRes=100,
                                    pos=(self.x_loc_pix, self.y_loc_pix),
                                    ori=180,
                                    color=-1,
                                    units='pix')

        factor = 2
        self.stimulus_3 = RadialStim(win=self.session.win,
                                     mask=mask,
                                     size=(self.size_prf_pix*factor,self.size_prf_pix*factor),
                                     radialCycles=self.radial_cycles*factor,
                                     angularCycles=self.angular_cycles*factor,
                                     texRes=128,
                                     angularRes=100,
                                     pos=(self.x_loc_pix, self.y_loc_pix),
                                     ori=180,
                                     color=1,
                                     units='pix')

        self.stimulus_4 = RadialStim(win=self.session.win,
                                     mask=mask,
                                     size=(self.size_prf_pix*factor,self.size_prf_pix*factor),
                                     radialCycles=self.radial_cycles*factor,
                                     angularCycles=self.angular_cycles*factor,
                                     texRes=128,
                                     angularRes=100,
                                     pos=(self.x_loc_pix, self.y_loc_pix),
                                     ori=180,
                                     color=-1,
                                     units='pix')

        self.stimulus_5 = RadialStim(win=self.session.win,
                                     mask=mask,
                                     size=(self.size_prf_pix*3,self.size_prf_pix*3),
                                     radialCycles=self.radial_cycles*factor,
                                     angularCycles=self.angular_cycles*factor,
                                     texRes=128,
                                     angularRes=100,
                                     pos=(self.x_loc_pix, self.y_loc_pix),
                                     ori=180,
                                     color=1,
                                     units='pix')

        self.stimulus_6 = RadialStim(win=self.session.win,
                                     mask=mask,
                                     size=(self.size_prf_pix*3,self.size_prf_pix*3),
                                     radialCycles=self.radial_cycles*factor,
                                     angularCycles=self.angular_cycles*factor,
                                     texRes=128,
                                     angularRes=100,
                                     pos=(self.x_loc_pix, self.y_loc_pix),
                                     ori=180,
                                     color=-1,
                                     units='pix')                                     

        self.block_center1 = Circle(win=self.session.win,
                                    size=(self.size_prf_pix,self.size_prf_pix),
                                    pos=(self.x_loc_pix, self.y_loc_pix),
                                    units='pix',
                                    fillColor=[0,0,0],
                                    lineColor=[0,0,0],
                                    edges=128)

        self.block_center2 = Circle(win=self.session.win,
                                    size=(self.size_prf_pix*2,self.size_prf_pix*2),
                                    pos=(self.x_loc_pix, self.y_loc_pix),
                                    units='pix',
                                    fillColor=[0,0,0],
                                    lineColor=[0,0,0],
                                    edges=128)                                    


    def draw(self, trial=None):

        rotationRate = 0.1  # revs per sec
        t = 0
        phase = np.fmod(self.session.settings['design'].get('stim_duration')+self.session.timer.getTime(), 1.0/self.frequency) * self.frequency

        if trial == "center":
            if phase < 0.5:
                self.stimulus_1.draw()
            else:
                self.stimulus_2.draw()
        elif trial == "surround":
            if phase < 0.5:
                self.stimulus_3.draw()
            else:
                self.stimulus_4.draw()
            self.block_center1.draw()
        elif trial == "outside":
            if phase < 0.5:
                self.stimulus_5.draw()
            else:
                self.stimulus_6.draw()
            self.block_center2.draw()
