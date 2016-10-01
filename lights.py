import pyglet
from pyglet.gl import *

def glvec(args):
    return (GLfloat * len(args))(*args)


class SpotLight:
    '''localized lightsource'''
    def __init__(self, position, color):
        '''color: list of three floats for rgb \
position: list of three floats'''
        
        self.position = glvec(position+[1.0])
        self.color = glvec(color+[1.0])

    def set_position(self, position):
        self.position = glvec(position+[1.0])

    def set_color(self, color):
        self.color = glvec(color+[1.0])

class MasterLight:
    '''light source at infinity'''
    def __init__(self, color):
        '''color: list of three floats for rgb'''
        self.color = glvec(color+[1.0])

    def set_color(self, color):
        self.color = glvec(color+[1.0])

class LightSet:
    '''gl binding system for lights. Meant to be used as a singleton'''
    def __init__(self):
        #set up openGL context
        glClearColor(0, 0, 0, 1)
        glEnable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (GLfloat*4)(0, 0, 1.0, 0.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (GLfloat*4)(0, 0, 0, 1.0))

        #set up lights
        self.masterLight = MasterLight([1.0, 1.0, 1.0])
        self.lights_avail = set([])     
        for i in range(1,8):
            exec "self.lights_avail.add(GL_LIGHT%i)" %i           
        for gl_light in self.lights_avail:
            glEnable(gl_light)
            glLightfv(gl_light, GL_AMBIENT, (GLfloat*4)(0, 0, 0, 1.0))
            glLightfv(gl_light, GL_SPECULAR, (GLfloat*4)(0, 0, 0, 1.0))
            glLightfv(gl_light, GL_DIFFUSE, (GLfloat*4)(0, 0, 0, 1.0))
            glLightfv(gl_light, GL_SPOT_CUTOFF, GLfloat(90))
            glLightfv(gl_light, GL_SPOT_EXPONENT, GLfloat(.5))
        self.external_lights = [] #(pointer to light, glLight)
        
    def draw(self):
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, self.masterLight.color)
        for light, gl_light in self.external_lights:
            glEnable(gl_light)
            glLightfv(gl_light, GL_POSITION, light.position)
            glLightfv(gl_light, GL_DIFFUSE, light.color)

    def add_light(self, light):
        if self.lights_avail:
            self.external_lights.append((light, self.lights_avail.pop()))

    def remove_light(self, light):
        for entry in self.external_lights:
            if entry[0] is light:
                self.external_lights.remove(entry)
                self.lights_avail.add(entry[1])
