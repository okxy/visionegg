#!/usr/bin/env python

"""Draw dots, using your own event loop.

This bypasses the VisionEgg.Core.Presentation class.  It may be easier
to create simple experiments this way."""

import VisionEgg
from VisionEgg.Core import *
import pygame
from pygame.locals import *
from VisionEgg.Text import *
from VisionEgg.Dots import *

screen = get_default_screen()
screen.parameters.bgcolor = (0.0,0.0,0.0,0.0) # black (RGBA)

dots = DotArea2D( center                  = ( screen.size[0]/2.0, screen.size[1]/2.0 ),
                  size                    = ( 300.0 , 300.0 ),
                  signal_fraction         = 0.1,
                  signal_direction_deg    = 180.0,
                  velocity_pixels_per_sec = 10.0,
                  dot_lifespan_sec        = 5.0,
                  dot_size                = 3.0,
                  num_dots                = 100)

text = Text( text = "Vision Egg dot_simple_loop demo.",
             position = (screen.size[0]/2,2),
             anchor = 'bottom',
             color = (1.0,1.0,1.0,1.0))

viewport = Viewport( screen=screen, stimuli=[dots,text] )

# The main loop below is an alternative to using the
# VisionEgg.Core.Presentation class.

while not pygame.event.peek((QUIT,KEYDOWN,MOUSEBUTTONDOWN)):
    screen.clear()
    viewport.draw()
    swap_buffers()
