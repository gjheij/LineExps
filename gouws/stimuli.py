import numpy as np
from psychopy.visual import TextStim, Line, RadialStim


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

        self.stimulus_1 = RadialStim(win=self.session.win,
                                    mask=mask,
                                    size=(1000.0, 1000.0),
                                    radialCycles=self.radial_cycles,
                                    angularCycles=self.angular_cycles,
                                    texRes=128,
                                    angularRes=100,
                                    visibleWedge=(180+pacman_angle, 270),
                                    angularPhase=1/6,
                                    pos=(0.0, 0.0),
                                    color=1)
        self.stimulus_2 = RadialStim(win=self.session.win,
                                    mask=mask,
                                    size=(1000.0, 1000.0),
                                    radialCycles=self.radial_cycles,
                                    angularCycles=self.angular_cycles,
                                    texRes=128,
                                    angularRes=100,
                                    angularPhase=1/6,
                                    visibleWedge=[270, 360-pacman_angle],
                                    pos=(0.0, 0.0),
                                    color=1)                           

    def draw(self, phase=None):

        print(phase)
        self.stimulus_1.setAngularPhase(phase, '+')
        self.stimulus_2.setAngularPhase(phase, '-')
        self.stimulus_1.draw()
        self.stimulus_2.draw()
