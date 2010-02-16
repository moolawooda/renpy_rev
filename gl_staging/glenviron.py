# This file contains the code required to set up (and change) OpenGL texture
# environments to implement various effects.

import _renpy_tegl as gl

# Constants, that are used to store the last kind of blend a class was
# used for. (So we can avoid changing the GL state unnecessarily.)
NONE = 0
BLIT = 1
BLEND = 2
IMAGEBLEND = 3

class GLEnviron(object):

    def init_common(self):
        """
        Code that is, for now, common to the different environments, and
        doesn't need to be changed over the course of execution.
        """

        gl.Enable(gl.BLEND)
        gl.BlendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)

    def blit_environ(self):
        """
        Set up a normal blit environment. The texture to be blitted should
        be TEXTURE0.
        """

        raise Exception("Not implemented.")

    def blend_environ(self, fraction):
        """
        Set up an environment that blends from TEXTURE0 to TEXTURE1.

        `fraction` is the fraction of the blend complete.
        """

        raise Exception("Not implemented.")


    def imageblend_environ(self, fraction, ramp):
        """
        Setup an environment that does an imageblend from TEXTURE1 to TEXTURE2.
        The controlling image is TEXTURE0.

        `fraction` is the fraction of the blend complete.
        `ramp` is the length of the ramp.
        """

        raise Exception("Not implemented.")
        
        
class FixedFunctionGLEnviron(GLEnviron):
    """
    This is an OpenGL environment that uses the fixed-function pipeline.

    It requires ARB_texture_env_combine and ARB_texture_env_crossbar to
    work.
    """

    def __init__(self):
        
        # The last blend environ used.
        self.last_environ = NONE

        # The last ramp length asked for.
        self.last_ramp = -1

        # The last ramplen actually used.
        self.last_ramplen = -1
        
        self.init_common()

        # A table that maps ramp lengths to the setup of the fixed-function
        # units.        
        self.ramp_setup = [
            # Fields are:
            # ramp length,
            # unit 1 scale,
            # unit 2 function,
            # unit 2 scale,

            (256, 1.0, gl.REPLACE, 1.0),
            (128, 1.0, gl.REPLACE, 2.0),
            (64, 1.0, gl.REPLACE, 4.0),
            (32, 1.0, gl.ADD, 4.0),
            (16, 2.0, gl.ADD, 4.0),
            (8, 4.0, gl.ADD, 4.0),
            ]
            
        

    def disable(self, unit):
        """
        Disables the given texture combiner.
        """

        gl.ActiveTextureARB(unit)
        gl.Disable(gl.TEXTURE_2D)
        
    def combine_mode(self, unit,
                     color_function=gl.MODULATE,
                     color_arg0=gl.TEXTURE,
                     color_arg1=gl.PREVIOUS_ARB,
                     color_arg2=gl.CONSTANT_ARB,
                     color_source0=gl.SRC_COLOR,
                     color_source1=gl.SRC_COLOR,
                     color_source2=gl.SRC_COLOR,
                     color_scale=1.0,
                     alpha_function=gl.MODULATE,
                     alpha_arg0=gl.TEXTURE,
                     alpha_arg1=gl.PREVIOUS_ARB,
                     alpha_arg2=gl.CONSTANT_ARB,
                     alpha_source0=gl.SRC_ALPHA,
                     alpha_source1=gl.SRC_ALPHA,
                     alpha_source2=gl.SRC_ALPHA,
                     alpha_scale=1.0):

        gl.ActiveTextureARB(unit)
        gl.Enable(gl.TEXTURE_2D)

        gl.TexEnvi(gl.TEXTURE_ENV, gl.TEXTURE_ENV_MODE, gl.COMBINE_ARB)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.COMBINE_RGB_ARB, color_function)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.COMBINE_ALPHA_ARB, alpha_function)

        gl.TexEnvi(gl.TEXTURE_ENV, gl.SOURCE0_RGB_ARB, color_arg0)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.OPERAND0_RGB_ARB, color_source0)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.SOURCE1_RGB_ARB, color_arg1)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.OPERAND1_RGB_ARB, color_source1)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.SOURCE2_RGB_ARB, color_arg2)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.OPERAND2_RGB_ARB, color_source2)

        gl.TexEnvi(gl.TEXTURE_ENV, gl.SOURCE0_ALPHA_ARB, alpha_arg0)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.OPERAND0_ALPHA_ARB, alpha_source0)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.SOURCE1_ALPHA_ARB, alpha_arg1)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.OPERAND1_ALPHA_ARB, alpha_source1)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.SOURCE2_ALPHA_ARB, alpha_arg2)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.OPERAND2_ALPHA_ARB, alpha_source2)

        gl.TexEnvf(gl.TEXTURE_ENV, gl.RGB_SCALE_ARB, color_scale)
        gl.TexEnvf(gl.TEXTURE_ENV, gl.ALPHA_SCALE, alpha_scale)

        
    def blit_environ(self):

        if self.last_environ != BLIT:

            # Set unit 0 to modulate.
            self.combine_mode(gl.TEXTURE0_ARB,
                              color_function=gl.MODULATE,
                              alpha_function=gl.MODULATE)
            
            # Disable units 1, 2 and 3.
            self.disable(gl.TEXTURE1_ARB)
            self.disable(gl.TEXTURE2_ARB)
            self.disable(gl.TEXTURE3_ARB)
            
            self.last_environ = BLIT
        
    def blend_environ(self, fraction):

        if self.last_environ != BLEND:

            # Get texture 0.
            self.combine_mode(gl.TEXTURE0_ARB,
                              color_function=gl.REPLACE,
                              alpha_function=gl.REPLACE)

            # Use interpolate to combine texture 0 with texture 1, as
            # controlled by the constant of texture unit 1.
            self.combine_mode(gl.TEXTURE1_ARB,
                              color_function=gl.INTERPOLATE_ARB,
                              color_arg0=gl.TEXTURE1_ARB,
                              color_arg1=gl.TEXTURE0_ARB,
                              alpha_function=gl.INTERPOLATE_ARB,
                              alpha_arg0=gl.TEXTURE1_ARB,
                              alpha_arg1=gl.TEXTURE0_ARB)

            # Combine the interpolated result with the primary color, to
            # allow for tinting and alpha adjustments.
            self.combine_mode(gl.TEXTURE2_ARB,
                              color_function=gl.MODULATE,
                              color_arg0=gl.PREVIOUS_ARB,
                              color_arg1=gl.PRIMARY_COLOR_ARB,
                              alpha_function=gl.MODULATE,
                              alpha_arg0=gl.PREVIOUS_ARB,
                              alpha_arg1=gl.PRIMARY_COLOR_ARB)
            
            # Disable texture unit 3.
            self.disable(gl.TEXTURE3_ARB)
            
            self.last_environ = BLEND
                            
        gl.ActiveTextureARB(gl.TEXTURE1_ARB)
        gl.TexEnvfv(gl.TEXTURE_ENV, gl.TEXTURE_ENV_COLOR, (fraction, fraction, fraction, fraction))

        
        
    def imageblend_environ(self, fraction, ramp):

        if self.last_environ != IMAGEBLEND or self.last_ramp != ramp:

            # Figure out the details of the ramp.
            for i in self.ramp_setup:
                ramplen, t0scale, t1function, t1scale = i

                # We round the ramplen down, unless we're below the
                # smallest size, in which case we increase it.
                if ramplen <= ramp:
                    break

            # Unit 0 loads in the control image, and adds/subtracts an
            # offset to/from it. (We'll set it up to subtract here,
            # and change this later on as necessary.)
            # 
            # It multiplies this result by up to 4.
            self.combine_mode(gl.TEXTURE0_ARB,
                              color_function=gl.SUBTRACT_ARB,
                              alpha_function=gl.SUBTRACT_ARB,
                              color_arg1=gl.CONSTANT_ARB,
                              alpha_arg1=gl.CONSTANT_ARB,
                              color_scale=t0scale,
                              alpha_scale=t0scale)

            # Unit 1 will multiply the result of stage 1 by up to 8. 
            #
            # It also takes the first source texture, but we don't
            # access it directly yet.
            self.combine_mode(gl.TEXTURE1_ARB,
                              color_function=t1function,
                              alpha_function=t1function,
                              color_arg0=gl.PREVIOUS_ARB,
                              color_arg1=gl.PREVIOUS_ARB,
                              alpha_arg0=gl.PREVIOUS_ARB,
                              alpha_arg1=gl.PREVIOUS_ARB,
                              color_scale=t1scale,
                              alpha_scale=t1scale)

            # Unit 2 uses the result of unit 1 to interpolate between the
            # unit 1 and unit 2 textures.
            self.combine_mode(gl.TEXTURE2_ARB,
                              color_function=gl.INTERPOLATE_ARB,
                              alpha_function=gl.INTERPOLATE_ARB,
                              color_arg0=gl.TEXTURE2_ARB,
                              color_arg1=gl.TEXTURE1_ARB,
                              color_arg2=gl.PREVIOUS_ARB,
                              alpha_arg0=gl.TEXTURE2_ARB,
                              alpha_arg1=gl.TEXTURE1_ARB,
                              alpha_arg2=gl.PREVIOUS_ARB)

            # Finally, Unit 3 modulates the result of unit 2 with the color.
            self.combine_mode(gl.TEXTURE3_ARB,
                              color_function=gl.MODULATE,
                              color_arg0=gl.PREVIOUS_ARB,
                              color_arg1=gl.PRIMARY_COLOR_ARB,
                              alpha_function=gl.MODULATE,
                              alpha_arg0=gl.PREVIOUS_ARB,
                              alpha_arg1=gl.PRIMARY_COLOR_ARB)
            
            self.last_environ = IMAGEBLEND
            self.last_ramp = ramp
            self.last_ramplen = ramplen

        # Compute the offset to apply to the alpha.            
        start = -1.0
        end = self.last_ramplen / 256.0        
        offset = start + ( end - start) * fraction

        # Decide if we're adding or subtracting.
        if offset < 0:
            function = gl.SUBTRACT_ARB
            offset = -offset
        else:
            function = gl.ADD

        # Setup unit 0 as appropriate.
        gl.ActiveTextureARB(gl.TEXTURE0_ARB)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.COMBINE_RGB_ARB, function)
        gl.TexEnvi(gl.TEXTURE_ENV, gl.COMBINE_ALPHA_ARB, function)
        gl.TexEnvfv(gl.TEXTURE_ENV, gl.TEXTURE_ENV_COLOR, (offset, offset, offset, offset))
        
                              
                
            
        
        
        
        
