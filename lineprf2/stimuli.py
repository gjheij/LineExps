import numpy as np
from psychopy.visual import TextStim, Line, RadialStim, Circle, GratingStim
from psychopy import tools


class FixationLines(object):

    def __init__(self, win, circle_radius, color, linewidth=1.5, *args, **kwargs):
        self.color = color
        self.linewidth = linewidth
        # self.line1 = Line(win,
        #                   start=(-circle_radius, -circle_radius),
        #                   end=(circle_radius, circle_radius),
        #                   lineColor=self.color,
        #                   lineWidth=self.linewidth, *args, **kwargs)

        # self.line2 = Line(win,
        #                   start=(-circle_radius, circle_radius),
        #                   end=(circle_radius, -circle_radius),
        #                   lineColor=self.color,
        #                   lineWidth=self.linewidth, *args, **kwargs)

        self.line1 = Circle(win,
                            circle_radius,
                            fillColor=self.color,
                            lineColor=None,
                            units='deg')

        self.line2 = Circle(win,
                            circle_radius,
                            fillColor=self.color,
                            lineColor=None,
                            units='deg')

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
             # self.session.prf_parameters['size'][self.session.hemi]
            self.x_loc = self.session.prf_parameters['x'][self.session.hemi]
            self.y_loc = self.session.prf_parameters['y'][self.session.hemi]
        else:
            self.size_prf = 1000.0

        self.size_prf = self.session.settings['stimuli'].get('cue_size')
        self.color_prf = self.session.settings['stimuli'].get('cue_color')
        self.prf_stimulus = Circle(win=self.session.win,
                                   size=(self.size_prf, self.size_prf),
                                   pos=(self.x_loc, self.y_loc),
                                   units='deg',
                                   fillColor=self.color_prf,
                                   lineColor=[0, 0, 0],
                                   opacity=0.1,
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
                bar_width=0.625,
                squares_in_bar=1,
                n_mask_pixels=1000,
                frequency=8.0):

        self.session = session
        self.angular_cycles = angular_cycles
        self.radial_cycles = radial_cycles
        self.border_radius = border_radius
        self.pacman_angle = pacman_angle
        self.n_mask_pixels = n_mask_pixels
        self.frequency = frequency
        self.squares_in_bar = squares_in_bar
        self.bar_width_deg = bar_width
        self.tex_nr_pix = 2048

        self.bar_width_in_pixels = tools.monitorunittools.deg2pix(self.bar_width_deg, self.session.monitor)*self.tex_nr_pix/self.session.win.size[1]
        
        self.bar_width = tools.monitorunittools.deg2pix(self.bar_width_deg, self.session.monitor)
        projection_width = self.session.win.size[0]/2
        
        #construct basic space for textures
        bar_width_in_radians = np.pi*self.squares_in_bar
        bar_pixels_per_radian = bar_width_in_radians/self.bar_width_in_pixels
        pixels_ls = np.linspace((-self.tex_nr_pix/2)*bar_pixels_per_radian,(self.tex_nr_pix/2)*bar_pixels_per_radian,self.tex_nr_pix)

        tex_x, tex_y = np.meshgrid(pixels_ls, pixels_ls)
        
        #construct textues, alsoand making sure that also the single-square bar is centered in the middle
        if self.squares_in_bar==1:
            self.sqr_tex = np.sign(np.sin(tex_x-np.pi/2) * np.sin(tex_y))
            self.sqr_tex_phase_1 = np.sign(np.sin(tex_x-np.pi/2) * np.sin(tex_y+np.sign(np.sin(tex_x-np.pi/2))*np.pi))
            self.sqr_tex_phase_2 = np.sign(np.sign(np.abs(tex_x-np.pi/2)) * np.sin(tex_y+np.pi/2))
        else:                
            self.sqr_tex = np.sign(np.sin(tex_x) * np.sin(tex_y))   
            self.sqr_tex_phase_1 = np.sign(np.sin(tex_x) * np.sin(tex_y+np.sign(np.sin(tex_x))*np.pi))
            self.sqr_tex_phase_2 = np.sign(np.sign(np.abs(tex_x)) * np.sin(tex_y+np.pi/2))
            
        
        bar_start_idx=int(np.round(self.tex_nr_pix/2-self.bar_width_in_pixels/2))
        bar_end_idx=int(bar_start_idx+self.bar_width_in_pixels)

        self.sqr_tex[:,:bar_start_idx] = 0       
        self.sqr_tex[:,bar_end_idx:] = 0

        self.sqr_tex_phase_1[:,:bar_start_idx] = 0                   
        self.sqr_tex_phase_1[:,bar_end_idx:] = 0

        self.sqr_tex_phase_2[:,:bar_start_idx] = 0                
        self.sqr_tex_phase_2[:,bar_end_idx:] = 0       

        ### 

        mask = np.ones((n_mask_pixels))
        mask[-int(border_radius*n_mask_pixels):] = (np.cos(np.linspace(0,np.pi,int(border_radius*n_mask_pixels)))+1)/2
        mask[:int(border_radius*n_mask_pixels)] = (np.cos(np.linspace(0,np.pi,int(border_radius*n_mask_pixels))[::-1])+1)/2

        self.stimulus_1 = GratingStim(self.session.win,
                                        tex=self.sqr_tex_phase_1,
                                        units='pix',
                                        color=1,
                                        size=[self.session.win.size[1], self.session.win.size[1]])
        self.stimulus_2 = GratingStim(self.session.win,
                                        tex=self.sqr_tex_phase_1,
                                        units='pix',
                                        color=-1,
                                        size=[self.session.win.size[1], self.session.win.size[1]])


    def draw(self):
        pass
