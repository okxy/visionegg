#!/usr/bin/env python

import math
from VisionEgg.Core import *
from VisionEgg.AppHelper import *
from VisionEgg.MoreStimuli import *
from VisionEgg.MotionBlur import *

target_velocity = 25.0
drum_max_speed = 50.0 # degrees per second

def x_as_function_of_time(t):
    return target_velocity*sin(0.1*2.0*math.pi*t)

def y_as_function_of_time(t):
    return target_velocity*sin(0.1*2.0*math.pi*t)

def orientation(dummy):
    return 135.0

def angle_as_function_of_time(t):
    return drum_max_speed*math.cos(0.2*2*math.pi*t) # rotate at 90 degrees per second

def one_during_experiment(t):
    if t < 0.0:
        return 0.0
    else:
        return 1.0

screen = get_default_screen()
projection = SimplePerspectiveProjection(fov_x=90.0)
viewport = Viewport(screen,(0,0),screen.size,projection)
target = Target2D()
target.init_gl()
viewport.add_overlay(target)
try:
    texture = TextureFromFile("orig.bmp") # try to open a texture file
except:
    texture = Texture(size=(256,16)) # otherwise, generate one

drum = BlurredDrum(max_speed=drum_max_speed, texture=texture)
drum.init_gl()
viewport.add_stimulus(drum)

p = Presentation(duration_sec=10.0,viewports=[viewport])

p.add_realtime_controller(target.parameters,'x', x_as_function_of_time)
p.add_realtime_controller(target.parameters,'y', y_as_function_of_time)
p.add_realtime_controller(drum.parameters,'angle', angle_as_function_of_time)
p.add_realtime_controller(drum.parameters,'cur_time', lambda t: t)
p.add_transitional_controller(target.parameters,'orientation', orientation)
p.add_transitional_controller(target.parameters,'on', one_during_experiment)
p.add_transitional_controller(drum.parameters,'contrast', one_during_experiment)

p.go()


