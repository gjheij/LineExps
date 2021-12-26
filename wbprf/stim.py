#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 14:07:02 2019

@author: marcoaqil
"""
import numpy as np
from psychopy import visual
from psychopy import tools

class ApertureStim(object):   

    def __init__(self, session):

        self.session = session
        self.session.win.allowStencil = True
        
        self.aperture_factor = self.session.settings['PRF stimulus settings'].get('aperture_factor_of_prf_size')

        self.aperture_stimulus = visual.Aperture(win=self.session.win,
                                                 size=(self.session.size_prf_pix*self.aperture_factor,
                                                       self.session.size_prf_pix*self.aperture_factor),
                                                 pos=(self.session.x_loc_pix,
                                                      self.session.y_loc_pix))
        
        self.aperture_stimulus.enabled = False 

    def draw(self):
        pass
        # self.aperture_stimulus.enabled = True


class PRFStim(object):  
    def __init__(self, session, 
                        squares_in_bar=2 ,
                        bar_width_deg=1.25,
                        tex_nr_pix=2048,
                        flicker_frequency=6, 

                        **kwargs):
        self.session = session
        self.squares_in_bar = squares_in_bar
        self.bar_width_deg = bar_width_deg
        self.tex_nr_pix = tex_nr_pix
        self.flicker_frequency = flicker_frequency

        #calculate the bar width in pixels, with respect to the texture
        self.bar_width_in_pixels = tools.monitorunittools.deg2pix(bar_width_deg, self.session.monitor)*self.tex_nr_pix/self.session.win.size[1]
        
        
        #construct basic space for textures
        bar_width_in_radians = np.pi*self.squares_in_bar
        bar_pixels_per_radian = bar_width_in_radians/self.bar_width_in_pixels
        pixels_ls = np.linspace((-self.tex_nr_pix/2)*bar_pixels_per_radian,(self.tex_nr_pix/2)*bar_pixels_per_radian,self.tex_nr_pix)

        tex_x, tex_y = np.meshgrid(pixels_ls, pixels_ls)
        
        #construct textues, alsoand making sure that also the single-square bar is centered in the middle
        if squares_in_bar==1:
            self.sqr_tex = np.sign(np.sin(tex_x-np.pi/2) * np.sin(tex_y))
            self.sqr_tex_phase_1 = np.sign(np.sin(tex_x-np.pi/2) * np.sin(tex_y+np.sign(np.sin(tex_x-np.pi/2))*np.pi/4))
            self.sqr_tex_phase_2 = np.sign(np.sign(np.abs(tex_x-np.pi/2)) * np.sin(tex_y+np.pi/2))
        else:                
            self.sqr_tex = np.sign(np.sin(tex_x) * np.sin(tex_y))   
            self.sqr_tex_phase_1 = np.sign(np.sin(tex_x) * np.sin(tex_y+np.sign(np.sin(tex_x))*np.pi/4))
            self.sqr_tex_phase_2 = np.sign(np.sign(np.abs(tex_x)) * np.sin(tex_y+np.pi/2))
            
        
        bar_start_idx=int(np.round(self.tex_nr_pix/2-self.bar_width_in_pixels/2))
        bar_end_idx=int(bar_start_idx+self.bar_width_in_pixels)+1

        self.sqr_tex[:,:bar_start_idx] = 0       
        self.sqr_tex[:,bar_end_idx:] = 0

        self.sqr_tex_phase_1[:,:bar_start_idx] = 0                   
        self.sqr_tex_phase_1[:,bar_end_idx:] = 0

        self.sqr_tex_phase_2[:,:bar_start_idx] = 0                
        self.sqr_tex_phase_2[:,bar_end_idx:] = 0
        
        
        #construct stimuli with psychopy and textures in different position/phases
        self.checkerboard_1 = visual.GratingStim(self.session.win,
                                                 tex=self.sqr_tex,
                                                 units='pix',
                                                 size=[self.session.win.size[1],self.session.win.size[1]])
        self.checkerboard_2 = visual.GratingStim(self.session.win,
                                                 tex=self.sqr_tex_phase_1,                                               
                                                 units='pix',
                                                 size=[self.session.win.size[1],self.session.win.size[1]])
        self.checkerboard_3 = visual.GratingStim(self.session.win,
                                                 tex=self.sqr_tex_phase_2,                                                
                                                 units='pix',
                                                 size=[self.session.win.size[1],self.session.win.size[1]])
        
        
        
        #for reasons of symmetry, some stimuli (4 and 8 in the order) are generated differently  if the bar has only one square
        if self.squares_in_bar!=1:                
            self.checkerboard_4 = visual.GratingStim(self.session.win,
                                                     tex=np.fliplr(self.sqr_tex_phase_1),
                                                     units='pix',
                                                     size=[self.session.win.size[1],self.session.win.size[1]])
            self.checkerboard_8 = visual.GratingStim(self.session.win,
                                                     tex=-np.fliplr(self.sqr_tex_phase_1),
                                                     units='pix',
                                                     size=[self.session.win.size[1],self.session.win.size[1]])
                
        else:         
            self.checkerboard_4 = visual.GratingStim(self.session.win, 
                                                     tex=np.flipud(self.sqr_tex_phase_1),
                                                     units='pix',
                                                     size=[self.session.win.size[1],self.session.win.size[1]])
            
            self.checkerboard_8 = visual.GratingStim(self.session.win,
                                                     tex=-np.flipud(self.sqr_tex_phase_1),
                                                     units='pix',
                                                     size=[self.session.win.size[1],self.session.win.size[1]])
        
        #all other textures are the same
        self.checkerboard_5 = visual.GratingStim(self.session.win,
                                                 tex=-self.sqr_tex,
                                                 units='pix',
                                                 size=[self.session.win.size[1],self.session.win.size[1]])
            
        self.checkerboard_6 = visual.GratingStim(self.session.win,
                                                 tex=-self.sqr_tex_phase_1,
                                                 units='pix',
                                                 size=[self.session.win.size[1],self.session.win.size[1]])
            
        self.checkerboard_7 = visual.GratingStim(self.session.win,
                                                 tex=-self.sqr_tex_phase_2,
                                                 units='pix',
                                                 size=[self.session.win.size[1],self.session.win.size[1]])

            

        
    #this is the function that actually draws the stimulus. the sequence of different textures gives the illusion of motion.
    def draw(self, time, pos_in_ori, orientation,  bar_direction):
        
        #calculate position of the bar in relation to its orientation
        x_pos, y_pos = np.cos((2.0*np.pi)*-orientation/360.0)*pos_in_ori, np.sin((2.0*np.pi)*-orientation/360.0)*pos_in_ori
        
        #convert current time to sine/cosine to decide which texture to draw
        sin = np.sin(2*np.pi*time*self.flicker_frequency)
        cos = np.cos(2*np.pi*time*self.flicker_frequency)

        #set position, orientation, texture, and draw bar. bar moving up or down simply has reversed order of presentation
        if bar_direction==0:
            if sin > 0 and cos > 0 and cos > sin:
                self.checkerboard_1.setPos([x_pos, y_pos])
                self.checkerboard_1.setOri(orientation)
                self.checkerboard_1.draw()
            elif sin > 0 and cos > 0 and cos < sin:
                self.checkerboard_2.setPos([x_pos, y_pos])
                self.checkerboard_2.setOri(orientation)
                self.checkerboard_2.draw()
            elif sin > 0 and cos < 0 and np.abs(cos) < sin:
                self.checkerboard_3.setPos([x_pos, y_pos])
                self.checkerboard_3.setOri(orientation)
                self.checkerboard_3.draw()
            elif sin > 0 and cos < 0 and np.abs(cos) > sin:
                self.checkerboard_4.setPos([x_pos, y_pos])
                self.checkerboard_4.setOri(orientation)
                self.checkerboard_4.draw()
            elif sin < 0 and cos < 0 and cos < sin:
                self.checkerboard_5.setPos([x_pos, y_pos])
                self.checkerboard_5.setOri(orientation)
                self.checkerboard_5.draw()
            elif sin < 0 and cos < 0 and cos > sin:
                self.checkerboard_6.setPos([x_pos, y_pos])
                self.checkerboard_6.setOri(orientation)
                self.checkerboard_6.draw()
            elif sin < 0 and cos > 0 and cos < np.abs(sin):
                self.checkerboard_7.setPos([x_pos, y_pos])
                self.checkerboard_7.setOri(orientation)
                self.checkerboard_7.draw()
            else:
                self.checkerboard_8.setPos([x_pos, y_pos])
                self.checkerboard_8.setOri(orientation)
                self.checkerboard_8.draw()
        else:
            if sin > 0 and cos > 0 and cos > sin:
                self.checkerboard_8.setPos([x_pos, y_pos])
                self.checkerboard_8.setOri(orientation)
                self.checkerboard_8.draw()
            elif sin > 0 and cos > 0 and cos < sin:
                self.checkerboard_7.setPos([x_pos, y_pos])
                self.checkerboard_7.setOri(orientation)
                self.checkerboard_7.draw()
            elif sin > 0 and cos < 0 and np.abs(cos) < sin:
                self.checkerboard_6.setPos([x_pos, y_pos])
                self.checkerboard_6.setOri(orientation)
                self.checkerboard_6.draw()
            elif sin > 0 and cos < 0 and np.abs(cos) > sin:
                self.checkerboard_5.setPos([x_pos, y_pos])
                self.checkerboard_5.setOri(orientation)
                self.checkerboard_5.draw()
            elif sin < 0 and cos < 0 and cos < sin:
                self.checkerboard_4.setPos([x_pos, y_pos])
                self.checkerboard_4.setOri(orientation)
                self.checkerboard_4.draw()
            elif sin < 0 and cos < 0 and cos > sin:
                self.checkerboard_3.setPos([x_pos, y_pos])
                self.checkerboard_3.setOri(orientation)
                self.checkerboard_3.draw()
            elif sin < 0 and cos > 0 and cos < np.abs(sin):
                self.checkerboard_2.setPos([x_pos, y_pos])
                self.checkerboard_2.setOri(orientation)
                self.checkerboard_2.draw()
            else:
                self.checkerboard_1.setPos([x_pos, y_pos])
                self.checkerboard_1.setOri(orientation)
                self.checkerboard_1.draw()            
            




