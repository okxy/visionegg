#!/usr/bin/env python
"""Control a target with the mouse, using your own event loop."""

# Variables to store the mouse position
mouse_position = (320.0, 240.0)
last_mouse_position = (0.0,0.0)

############################
#  Import various modules  #
############################

from VisionEgg.Core import *
from VisionEgg.MoreStimuli import *
from VisionEgg.Text import *
from math import *
import pygame

#################################
#  Initialize the various bits  #
#################################

# Initialize OpenGL graphics screen.
screen = get_default_screen()

# Set the background color to white (RGBA).
screen.parameters.bgcolor = (1.0,1.0,1.0,1.0)

# Create an instance of the Target2D class with appropriate parameters.
target = Target2D(size  = (25.0,10.0),
                  color      = (0.0,0.0,0.0,1.0)) # Set the target color (RGBA) black

text = Text( text = "Press Esc to quit, arrow keys to change size of target.",
             position = (screen.size[0]/2.0,5),
             anchor='bottom',
             color = (0.0,0.0,0.0,1.0))

# Create a Viewport instance
viewport = Viewport(screen=screen, stimuli=[target,text])

################
#  Math stuff  #
################

def cross_product(b,c):
    """Cross product between vectors, represented as tuples of length 3."""
    det_i = b[1]*c[2] - b[2]*c[1]
    det_j = b[0]*c[2] - b[2]*c[0]
    det_k = b[0]*c[1] - b[1]*c[0]
    return (det_i,-det_j,det_k)

def mag(b):
    """Magnitude of a vector."""
    return b[0]**2.0 + b[1]**2.0 + b[2]**2.0
    
# target size
target_w = 50.0
target_h = 10.0

# key state
up = 0
down = 0
left = 0
right = 0

# The main loop below is an alternative to using the
# VisionEgg.Core.Presentation class.

quit_now = 0
while not quit_now:
    if pygame.event.get(pygame.locals.QUIT):
        quit_now = 1
    for event in pygame.event.get(pygame.locals.KEYDOWN):
        if event.key == pygame.locals.K_ESCAPE:
            quit_now = 1
        elif event.key == pygame.locals.K_UP:
            up = 1
        elif event.key == pygame.locals.K_DOWN:
            down = 1
        elif event.key == pygame.locals.K_RIGHT:
            right = 1
        elif event.key == pygame.locals.K_LEFT:
            left = 1
    for event in pygame.event.get(pygame.locals.KEYUP):
        if event.key == pygame.locals.K_UP:
            up = 0
        elif event.key == pygame.locals.K_DOWN:
            down = 0
        elif event.key == pygame.locals.K_RIGHT:
            right = 0
        elif event.key == pygame.locals.K_LEFT:
            left = 0
    
    just_current_pos = mouse_position
    (x,y) = pygame.mouse.get_pos()
    y = screen.size[1]-y # convert to OpenGL coords
    mouse_position = (x,y)
    if just_current_pos != mouse_position:
        last_mouse_position = just_current_pos
        
    # Set target position
    target.parameters.center = mouse_position
    
    # Set target orientation
    b = (float(last_mouse_position[0]-mouse_position[0]),
         float(last_mouse_position[1]-mouse_position[1]),
         0.0)

    orientation_vector = cross_product(b,(0.0,0.0,1.0))
    target.parameters.orientation = -atan2(orientation_vector[1],orientation_vector[0])/math.pi*180.0

    # Set target size
    amount = 0.02
    
    if up:
        target_w = target_w+(amount*target_w)
    elif down:
        target_w = target_w-(amount*target_w)
    elif right:
        target_h = target_h+(amount*target_h)
    elif left:
        target_h = target_h-(amount*target_h)
    target_w = max(target_w,0.0)
    target_h = max(target_h,0.0)

    target.parameters.size = (target_w, target_h)

    screen.clear()
    viewport.draw()
    swap_buffers()
