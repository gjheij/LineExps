#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 14:06:36 2019

@author: marcoaqil
"""

from exptools2.core.trial import Trial
from psychopy import event
import numpy as np
import os

opj = os.path.join



class PRFTrial(Trial):

    def __init__(self, session, trial_nr, bar_orientation, bar_position_in_ori, bar_direction, *args, **kwargs):
        
        #trial number and bar parameters   
        self.ID = trial_nr
        self.bar_orientation = bar_orientation
        self.bar_position_in_ori = bar_position_in_ori
        self.bar_direction = bar_direction
        self.session=session

        #here we decide how to go from each trial (bar position) to the next.    
        if self.session.settings['PRF stimulus settings']['Scanner sync']==True:
            #dummy value: if scanning or simulating a scanner, everything is synced to the output 't' of the scanner
            phase_durations = [100]
        else:
            #if not synced to a real or simulated scanner, take the bar pass step as length
            phase_durations = [self.session.settings['PRF stimulus settings']['Bar step length']] 
            
        #add topup time to last trial
        if self.session.settings['mri']['topup_scan']==True:
            if self.ID == self.session.trial_number-1:
                phase_durations=[self.session.topup_scan_duration]
            

        super().__init__(session, trial_nr,
            phase_durations, verbose=False,
            *args,
            **kwargs)

    
    def draw(self, *args, **kwargs):
        # draw bar stimulus and circular (raised cosine) aperture from Session class
        self.session.draw_stimulus() 
        self.session.mask_stim.draw()
        
        
        
    def get_events(self):
        """ Logs responses/triggers """
        events = event.getKeys(timeStamped=self.session.clock)
        if events:
            if 'q' in [ev[0] for ev in events]:  # specific key in settings?

                np.save(opj(self.session.output_dir, self.session.output_str+'_simple_response_data.npy'), {"Expected number of responses":len(self.session.dot_switch_color_times),
                                                                                  "Total subject responses":self.session.total_responses,
                                                                                  f"Correct responses (within {self.session.settings['Task settings']['response interval']}s of dot color change)":self.session.correct_responses})
           
                if self.session.settings['PRF stimulus settings']['Screenshot']==True:
                    self.session.win.saveMovieFrames(opj(self.session.screen_dir, self.session.output_str+'_Screenshot.png'))
                     
                self.session.close()
                self.session.quit()
 
            for key, t in events:
 
                if key == self.session.mri_trigger:
                    event_type = 'pulse'
                    #marco edit. the second bit is a hack to avoid double-counting of the first t when simulating a scanner
                    if self.session.settings['PRF stimulus settings']['Scanner sync']==True and t>0.1:                       
                        self.exit_phase=True
                        #ideally, for speed, would want  getMovieFrame to be called right after the first winflip. 
                        #but this would have to be dun from inside trial.run()
                        if self.session.settings['PRF stimulus settings']['Screenshot']==True:
                            self.session.win.getMovieFrame()
                else:
                    event_type = 'response'
                    self.session.total_responses += 1
                     
                    #tracking percentage of correct responses per session
                    if self.session.dot_count < len(self.session.dot_switch_color_times): 
                        if t > self.session.dot_switch_color_times[self.session.dot_count] and \
                            t < self.session.dot_switch_color_times[self.session.dot_count] + float(self.session.settings['Task settings']['response interval']):
                            self.session.correct_responses +=1 
                            # print(f'number correct responses: {self.session.correct_responses}') #testing
                             


 
                idx = self.session.global_log.shape[0]
                self.session.global_log.loc[idx, 'trial_nr'] = self.trial_nr
                self.session.global_log.loc[idx, 'onset'] = t
                self.session.global_log.loc[idx, 'event_type'] = event_type
                self.session.global_log.loc[idx, 'phase'] = self.phase
                self.session.global_log.loc[idx, 'response'] = key
 
                for param, val in self.parameters.items():
                    self.session.global_log.loc[idx, param] = val
 
                #self.trial_log['response_key'][self.phase].append(key)
                #self.trial_log['response_onset'][self.phase].append(t)
                #self.trial_log['response_time'][self.phase].append(t - self.start_trial)
 
                if key != self.session.mri_trigger:
                    self.last_resp = key
                    self.last_resp_onset = t
        
        #update counter
        if self.session.dot_count < len(self.session.dot_switch_color_times): 
            if self.session.clock.getTime() > self.session.dot_switch_color_times[self.session.dot_count] + \
                float(self.session.settings['Task settings']['response interval'])+0.1: #to give time to respond
                self.session.dot_count += 1   
                # print(f'dot count: {self.session.dot_count}') #testing
    
