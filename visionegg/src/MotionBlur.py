# This is the python source code for the MotionBlur module of the Vision Egg package.
#
#
# Copyright (c) 2001 Andrew Straw.  Distributed under the terms of the
# GNU General Public License (GPL).

####################################################################
#
#        Import all the necessary packages
#
####################################################################

import string
__version__ = string.split('$Revision$')[1]
__date__ = string.join(string.split('$Date$')[1:3], ' ')
__author__ = 'Andrew Straw <astraw@users.sourceforge.net>'

import math, cPickle

from VisionEgg import *
from imageConvolution import *

import Image, ImageDraw                         # Python Imaging Library packages
				                # from PyOpenGL:
from OpenGL.GL import *                         #   main package
from Numeric import * 		 	        # Numeric Python package
from MLab import *                              # Matlab function imitation from Numeric Python

####################################################################
#
#        Everything needed to create a motion blurred drum
#
####################################################################

class ParamHolder: # dummy class to hold copy of params, basically plays role of C struct
    pass

class BlurTextureFamily:
    # Should make this a little smoother -
    # 1) Need to take advantage of the fact that unblurred_texture is of type Texture
    # 2) Should make checksum of original image and check that with the cache
    # 3) Could save images to system RAM, not openGL ram, and use SubTexture
    #    to stick image into GL memory at draw time. (Rather than switching
    #    between textures resident in OpenGL.)
    def __init__(self,unblurred_texture,target_fps=180.0,maxSpeed=2000.0,numCachedTextures=10,cacheFunction='linear',blurKernel='boxcar'):
        if not isinstance(unblurred_texture,Texture):
            raise TypeError("unblurred_texture must be an instance of VisionEgg.Texture")
        self.p = ParamHolder()
        # Compute blur family parameters
        self.orig = unblurred_texture.orig
        self.p.im_width = self.orig.size[0]
        self.p.target_fps = target_fps
        self.p.sec_per_frame = 1.0/self.p.target_fps
        self.p.maxSpeed = maxSpeed # dps
        self.p.numCachedTextures = numCachedTextures
        self.p.blurKernel = blurKernel
        self.p.cacheFunction = cacheFunction

        # calculate speedList based on parameters
        self.p.speedList = self.computeSpeedList(self.p)

        # nothing is loaded into OpenGL yet
        self.texGLIdList = []
        self.texGLSpeedsDps = zeros((0,)) # empty array

        #now load images into OpenGL
        self.loadToGL(self.p)
        
    def computeSpeedList(self,p):
        if p.cacheFunction == 'linear':
            dpsSpeedList = arange(0.0,p.maxSpeed,p.maxSpeed/p.numCachedTextures) # dps
        elif p.cacheFunction == 'exp': # exponentially increasing speed look up table
            dpsSpeedList = arange(float(p.numCachedTextures))/float(p.numCachedTextures)
            logmax = math.log(p.maxSpeed)
            dpsSpeedList = dpsSpeedList*logmax
            dpsSpeedList = exp(dpsSpeedList)
        elif p.cacheFunction == 'hand_picked1':
            pixSpeedList = array([0.0, 10.0, 20.0])
            dpsSpeedList = pixSpeedList / float(p.im_width)*360.0 / p.sec_per_frame
        elif p.cacheFunction == 'hand_picked2':
            dpsSpeedList = array([0.0, 250.0, 500.0, 1000.0, 1500.0])
        else:
            raise RuntimeError("Unknown cacheFunction '%s'"%(p.cacheFunction,))
        
        pixSpeedList = dpsSpeedList * float(p.im_width)/360.0 * p.sec_per_frame
        speedList = []
        for i in range(dpsSpeedList.shape[0]):
            speedList.append( (dpsSpeedList[i], pixSpeedList[i]) )
        return speedList

    def loadToGL(self,p,cache_filename="blur_params.pickle"):
        # clear OpenGL if needed
        if (len(self.texGLIdList) != 0) or (self.texGLSpeedsDps.shape[0] != 0):
            raise NotImplemetedError("No code yet to clear textures out of OpenGL")
        else:
            self.texGLSpeedsDps = [] # make this a list for now, convert to Numeric array later
        
        # check to see if this family has already been computed and is cached
        use_cache = 1
        try:
            f = open(cache_filename,"rb")
            cached_p = cPickle.load(f)
            for attr in dir(p):
                val = getattr(p,attr)
                try:
                    cached_val = getattr(cached_p,attr)
                    if val != cached_val: # Attributes not the same, don't use cache
                        use_cache = 0
                        break
                except: # Attribute not in cached version, don't use cache
                    use_cache = 0
                    break 
        except (IOError, EOFError):
            use_cache = 0

        if use_cache:
            print "Found cache file '%s', loading images."%cache_filename
        else:
            print "Cache file '%s' not valid, blurring images."%cache_filename

        print "Motion blur for display at %f frames per second"%p.target_fps

        # compute (or load) the blurred images, load into OpenGL
        if use_cache:
            p = cached_p
        else:
            p.filenames = [ 'original texture' ] # initialize list
            new_cache_valid = 1 # will set to 0 if something goes wrong, otherwise save the new cache params

        # Load original image first
        tex = TextureFromPILImage( self.orig )
        self.texGLIdList.append( tex.load() ) # create OpenGL texture object
        self.texGLSpeedsDps.append( 0.0 ) # lower bound of speed this texture is used for

        for i in range(1,len(p.speedList)): # index zero is unblurred image, which we don't need to blur!
            (deg_per_sec, pix_per_frame) = p.speedList[i]
            if not use_cache:
                if p.blurKernel == 'gaussian':
                    filter = GaussianFilter(pix_per_frame/10.0) # This sigma is wrong, must figure it out!
                elif p.blurKernel == 'boxcar':
                    filter = BoxcarFilter(pix_per_frame)
                else:
                    raise RuntimeError("Filter type '%s' not implemented"%(p.blurKernel,))
                blurred = convolveImageHoriz(self.orig,filter)
                filename = "blur_cache%02d.ppm"%(i,)
                try:
                    blurred.save(filename)
                    p.filenames.append(filename)
                    print "Saved '%s' (blurred for %.1f degrees per second, %.2f pixels per frame)"%(filename,deg_per_sec,pix_per_frame)
                except:
                    new_cache_valid = 0
                    print "Failed to save '%s'"%(filename)
            else: # use cache
                filename = p.filenames[i]
                print "Loading '%s' (blurred for %.1f degrees per second, %.2f pixels per frame)"%(filename,deg_per_sec,pix_per_frame)
                blurred = Image.open(filename)
            tex = TextureFromPILImage( blurred )
            self.texGLIdList.append( tex.load() ) # create OpenGL texture object
            self.texGLSpeedsDps.append( deg_per_sec ) # lower bound of speed this texture is used for
            
        self.texGLSpeedsDps = array(self.texGLSpeedsDps) # convert back to Numeric array type

        # save our cache parameters if we re-made the cache
        if not use_cache: # save our new cache parameters
            if new_cache_valid:
                try:
                    f = open(cache_filename,"wb")
                    cPickle.dump(p,f)
                except IOError:
                    print "Failed to save cache parameters is '%s'"%(cache_filename,)
                    
class BlurredDrum(SpinningDrum):

    def __init__(self,
                 numCachedTextures=10,
                 target_fps=180.0,
                 maxSpeed=2000.0,
                 blurKernel='boxcar',
                 **kwargs):
        apply(SpinningDrum.__init__,(self,),kwargs)
        self.texs = BlurTextureFamily(self.drum_texture,
                                      numCachedTextures=numCachedTextures,
                                      maxSpeed=maxSpeed,
                                      blurKernel=blurKernel,
                                      target_fps=target_fps)
        self.motion_blur_on = 1
        self.last_time = 0.0
        self.last_drum_rotation = self.drum_rotation_function(self.last_time)

    def set_motion_blur_on(self,on):
        self.motion_blur_on = on
        
    def get_texture_object(self,delta_pos,delta_t):
        """Finds the appropriate texture object for the current velocity."""
        if self.motion_blur_on: # Find the appropriate texture 
            if delta_t < 1.0e-6: # less than 1 microsecond (this should be less than a frame could possibly take to draw)
                vel_dps = 0
                speedIndex = 0
            else:
                vel_dps = delta_pos/delta_t
                # Get the highest cached velocity less than or equal to the current velocity
                speedIndex = nonzero(less_equal(self.texs.texGLSpeedsDps,abs(vel_dps)))[-1]
        else: # In case motion blur is turned off
            speedIndex = 0
        return self.texs.texGLIdList[speedIndex]

    def draw_GL_scene(self):

        # I know that self.cur_time has been set for me.
        # Calculate my other variables from that.
        
        drum_rotation = self.drum_rotation_function(self.cur_time)

        delta_drum_rotation = drum_rotation - self.last_drum_rotation # change in position (units: degrees)
        delta_t = self.cur_time - self.last_time

        self.drum_texture_object = self.get_texture_object(delta_drum_rotation,delta_t) # sets the texture object that SpinningDrum uses
        SpinningDrum.draw_GL_scene(self) # call my base class to do most of the work
        
        # Set for next cycle
        self.last_time = self.cur_time
        self.last_drum_rotation = drum_rotation
