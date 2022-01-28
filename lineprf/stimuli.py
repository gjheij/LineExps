import numpy as np
from psychopy.visual import Circle, GratingStim
from psychopy import tools

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

class BarStim(object):

    def __init__(self,
                session,
                frequency=8,
                bar_width=None,
                squares_in_bar=None):

        self.session                = session
        self.squares_in_bar         = squares_in_bar
        self.bar_width_deg          = bar_width
        self.tex_nr_pix             = 2048
        self.border_radius          = self.session.settings['stimuli'].get('border_radius')
        self.n_mask_pixels          = self.session.settings['stimuli'].get('n_mask_pixels')
        self.frequency              = self.session.settings['stimuli'].get('frequency')
        
        # Convert bar width in degrees to pixels
        self.bar_width_in_pixels    = tools.monitorunittools.deg2pix(self.bar_width_deg, self.session.monitor)*self.tex_nr_pix/self.session.win.size[1]
        self.bar_width              = tools.monitorunittools.deg2pix(self.bar_width_deg, self.session.monitor)
        
        #construct basic space for textures
        bar_width_in_radians        = np.pi*self.squares_in_bar
        bar_pixels_per_radian       = bar_width_in_radians/self.bar_width_in_pixels
        pixels_ls                   = np.linspace((-self.tex_nr_pix/2)*bar_pixels_per_radian,(self.tex_nr_pix/2)*bar_pixels_per_radian,self.tex_nr_pix)
        tex_x, tex_y                = np.meshgrid(pixels_ls, pixels_ls)
        
        #construct textues, alsoand making sure that also the single-square bar is centered in the middle
        if self.squares_in_bar==1:
            self.sqr_tex            = np.sign(np.sin(tex_x-np.pi/2) * np.sin(tex_y))
            self.sqr_tex_phase_1    = np.sign(np.sin(tex_x-np.pi/2) * np.sin(tex_y+np.sign(np.sin(tex_x-np.pi/2))*np.pi))
            self.sqr_tex_phase_2    = np.sign(np.sign(np.abs(tex_x-np.pi/2)) * np.sin(tex_y+np.pi/2))
        else:                
            self.sqr_tex            = np.sign(np.sin(tex_x) * np.sin(tex_y))   
            self.sqr_tex_phase_1    = np.sign(np.sin(tex_x) * np.sin(tex_y+np.sign(np.sin(tex_x))*np.pi))
            self.sqr_tex_phase_2    = np.sign(np.sign(np.abs(tex_x)) * np.sin(tex_y+np.pi/2))
            
        
        bar_start_idx   = int(np.round(self.tex_nr_pix/2-self.bar_width_in_pixels/2))
        bar_end_idx     = int(bar_start_idx+self.bar_width_in_pixels)

        self.sqr_tex[:,:bar_start_idx]  = 0       
        self.sqr_tex[:,bar_end_idx:]    = 0

        self.sqr_tex_phase_1[:,:bar_start_idx]  = 0                   
        self.sqr_tex_phase_1[:,bar_end_idx:]    = 0

        self.sqr_tex_phase_2[:,:bar_start_idx]  = 0                
        self.sqr_tex_phase_2[:,bar_end_idx:]    = 0       

        ### 
        mask = np.ones((self.n_mask_pixels))
        mask[-int(self.border_radius*self.n_mask_pixels):]    = (np.cos(np.linspace(0,np.pi,int(self.border_radius*self.n_mask_pixels)))+1)/2
        mask[:int(self.border_radius*self.n_mask_pixels)]     = (np.cos(np.linspace(0,np.pi,int(self.border_radius*self.n_mask_pixels))[::-1])+1)/2

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