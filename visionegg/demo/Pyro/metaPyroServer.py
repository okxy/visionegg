#!/usr/bin/env python
"""Sinusoidal grating stimulus with complex control from metaPyroGUI

This demo illustrates a very easy way to exert complex control of
visual stimuli in an experimental setting.  A Vision Egg server is
started, which opens the display and will do all the drawing.  There
is a "meta-controller" which is served (via Pyro) to another program
which controls the stimuli.  The meta-controller can store information
in a higher-level format than the Controllers used on individual
instances of the Stimulus class.

You will need to have a Pyro Name Server running on your network for
this to work.  It comes with the Pyro distribution as a script in the
bin directory called ns.  Run it, run this script, and then run
metaPyroGUI.py from any computer on your network.

"""

# Copyright (c) 2002 Andrew Straw.  Distributed under the terms
# of the GNU Lesser General Public License (LGPL).

import sys
import VisionEgg.Core
import VisionEgg.Gratings
import VisionEgg.PyroHelpers
import Pyro.core

from metaPyroGUI import GratingMetaParameters

class GratingExperimentMetaController( Pyro.core.ObjBase ):
    """Encapsulates all parameters controlling a grating"""
    def __init__(self,presentation,grating_stimulus):
        self.server_close_callback = None
        Pyro.core.ObjBase.__init__(self)
        self.meta_params = GratingMetaParameters()
        if not isinstance(presentation,VisionEgg.Core.Presentation):
            raise ValueError("Expecting instance of VisionEgg.Core.Presentation")
        if not isinstance(grating_stimulus,VisionEgg.Gratings.SinGrating2D):
            raise ValueError("Expecting instance of VisionEgg.Gratings.SinGrating2D")
        self.p = presentation
        self.stim = grating_stimulus

        self.p.add_controller(self.stim,'on',VisionEgg.Core.FunctionController(during_go_func=self.on_function))

    def set_server_closed_instance(self,instance):
        self.server_closed_instance = instance

    def get_parameters(self):
        return self.meta_params

    def set_parameters(self, new_parameters):
        if isinstance(new_parameters, GratingMetaParameters):
            self.meta_params = new_parameters
        else:
            raise ValueError("Argument to set_parameters must be instance of GratingMetaParameters")
#        self.meta_params = new_parameters
        self.update()

    def on_function(self,t=-1.0): # default time to between trials time
        """Compute when the grating is on"""
        if t <= self.meta_params.pre_stim_sec:
            return 0 # not on yet
        elif t <= (self.meta_params.pre_stim_sec + self.meta_params.stim_sec):
            return 1 # on
        else:
            return 0 # off again
        
    def update(self):
        self.stim.parameters.contrast = self.meta_params.contrast
        self.stim.parameters.orientation = self.meta_params.orient
        self.stim.parameters.spatial_freq = self.meta_params.sf
        self.stim.parameters.temporal_freq_hz = self.meta_params.tf
        self.p.go_duration = self.meta_params.pre_stim_sec + self.meta_params.stim_sec + self.meta_params.post_stim_sec

    def go(self):
        self.p.parameters.enter_go_loop = 1

    def quit_server(self):
        self.p.parameters.quit = 1

# Don't do anything unless this script is being run
if __name__ == '__main__':
    
    pyro_server = VisionEgg.PyroHelpers.PyroServer()

    # get Vision Egg stimulus ready to go
    screen = VisionEgg.Core.Screen.create_default()
    stimulus = VisionEgg.Gratings.SinGrating2D()
    viewport = VisionEgg.Core.Viewport(screen=screen,stimuli=[stimulus])
    p = VisionEgg.Core.Presentation(viewports=[viewport])

    # now hand over control of stimulus to GratingExperimentMetaController
    meta_controller = GratingExperimentMetaController(p,stimulus)
    pyro_server.connect(meta_controller,"meta_controller")

    # get listener controller and register it
    p.add_controller(None,None, pyro_server.create_listener_controller())

    # enter endless loop
    p.run_forever()
