import numpy as np
from psychopy.visual import RadialStim

class CheckerStim(object):

    def __init__(
        self,
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

        self.stimulus_1 = RadialStim(
            win=self.session.win, 
            mask=mask, 
            size=(1000.0, 1000.0), 
            radialCycles=self.radial_cycles, 
            angularCycles=self.angular_cycles, 
            texRes=128, 
            angularRes=100,
            pos=(0.0, 0.0),
            ori=180,
            color=1)
        self.stimulus_2 = RadialStim(
            win=self.session.win, 
            mask=mask, 
            size=(1000.0, 1000.0), 
            radialCycles=self.radial_cycles,
            angularCycles=self.angular_cycles, 
            texRes=128, 
            angularRes=100,
            pos=(0.0, 0.0),
            ori=180,
            color=-1)                   

    def draw(self):

        phase = np.fmod(self.session.settings['design'].get('stim_duration')+self.session.timer.getTime(), 1.0/self.frequency) * self.frequency
        if phase < 0.5:          
            self.stimulus_1.draw()
        else:          
            self.stimulus_2.draw()
