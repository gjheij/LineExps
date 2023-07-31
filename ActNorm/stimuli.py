import numpy as np
from psychopy.visual import (
    RadialStim, 
    Circle,
    GratingStim,
    Line, 
    ShapeStim)
from psychopy import tools

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

    def __init__(self, session, act=False, **kwargs):

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

class SizeResponseStim():

    def __init__(
        self, 
        session,
        stim_design="radial",
        *args,
        **kwargs):

        self.session = session
        self.frequency = self.session.settings['stimuli'].get('frequency')

        if stim_design == "radial":
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
        else:
            for ii in ["radialCycles","angularCycles","size"]:
                if ii in list(kwargs.keys()):
                    _ = kwargs.pop(ii)

            if "pos" in list(kwargs.keys()):
                pos = kwargs["pos"]
                if isinstance(pos, (int,float)):
                    pos = tools.monitorunittools.deg2pix(pos, self.session.monitor)
                else:
                    pos = [tools.monitorunittools.deg2pix(i, self.session.monitor) for i in pos]
                
                kwargs["pos"] = pos
                
            self.squares_in_bar         = 2
            self.bar_width_deg          = 1.25
            self.tex_nr_pix             = 2048
            self.border_radius          = 0.2
            self.n_mask_pixels          = 1000
            
            # Convert bar width in degrees to pixels
            self.bar_width_in_pixels = tools.monitorunittools.deg2pix(self.bar_width_deg, self.session.monitor)*self.tex_nr_pix/self.session.win.size[1]
            self.bar_width = tools.monitorunittools.deg2pix(self.bar_width_deg, self.session.monitor)
            
            #construct basic space for textures
            bar_width_in_radians = np.pi*self.squares_in_bar
            bar_pixels_per_radian = bar_width_in_radians/self.bar_width_in_pixels
            pixels_ls = np.linspace((-self.tex_nr_pix/2)*bar_pixels_per_radian,(self.tex_nr_pix/2)*bar_pixels_per_radian,self.tex_nr_pix)
            tex_x, tex_y = np.meshgrid(pixels_ls, pixels_ls)

            self.sqr_tex = np.sign(np.sin(tex_x) * np.sin(tex_y))   
            self.sqr_tex_phase_1 = np.sign(np.sin(tex_x) * np.sin(tex_y+np.sign(np.sin(tex_x))*np.pi))
            self.sqr_tex_phase_2 = np.sign(np.sign(np.abs(tex_x)) * np.sin(tex_y+np.pi/2))

            self.stimulus_1 = GratingStim(
                win=self.session.win,
                # mask=mask,
                tex=self.sqr_tex_phase_1,
                units='pix',
                color=1,
                size=[self.session.win.size[1], self.session.win.size[1]],
                **kwargs)

            # white and black stimulus
            self.stimulus_2 = GratingStim(
                win=self.session.win,
                tex=self.sqr_tex_phase_1,
                units='pix',      
                color=-1,
                size=[self.session.win.size[1], self.session.win.size[1]],
                **kwargs)            

    def draw(self, contrast=None):

        phase = np.fmod(self.session.settings['design'].get('stim_duration')+self.session.timer.getTime(), 1.0/self.frequency) * self.frequency
        
        # contrast options contains 2 contrast types, low (0.6) and high (1)
        if isinstance(contrast, str):
            contrast_options = self.session.settings['stimuli'].get('contrasts')
            if contrast == 'low':
                select_contrast = contrast_options[0]
            elif contrast == 'high':
                select_contrast = contrast_options[1]
            
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
