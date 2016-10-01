import pyglet
from pyglet.gl import *
import random
from math import sin, pi

def glvec(args):
    return (GLfloat * len(args))(*args)


class SpotLight:
    '''localized lightsource'''
    def __init__(self, position, color=[1.0, 1.0, 1.0], direction=(0, 0, -1.0)):
        '''
        parameters:
            position (list of 3 floats): x, y, z
            color (list of 3 floats): rgb
            direction (iterable of 3 floats): direction light points
            '''
        
        self.position = glvec(position + [1.0])
        self.color = glvec(color+[1.0])
        self.direction = glvec(direction)

    def set_position(self, position):
        self.position = glvec(position+[1.0])

    def set_color(self, color):
        self.color = glvec(color+[1.0])

    def set_direction(self, direction):
        self.direction = glvec(direction)

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
            glLightfv(gl_light, GL_SPOT_DIRECTION, light.direction)

    def set_ambient(self, color):
        self.masterLight.set_color(color)

    def add_light(self, light):
        if self.lights_avail:
            self.external_lights.append((light, self.lights_avail.pop()))
            return self.external_lights[-1][0]
        else:
            raise IndexError, "No more available lights (max: 7)"

    def remove_light(self, light):
        for entry in self.external_lights:
            if entry[0] is light:
                self.external_lights.remove(entry)
                self.lights_avail.add(entry[1])

class CandleLight:
    omegas = [5*pi/2, 3*pi/2]
    base_color = (1.0, .9, .7)
    dim_factor = .06
    cycle_length = 2
    def __init__(self, position, max_intensity=1):
        self.position = glvec(position + [1.0])
        self.max_intensity = max_intensity
        self.clock = 0
        self.flicker = False
        self.set_color()
        self.direction = glvec((0, 0, -1))


    def set_color(self):
        if self.flicker:
            intensity = self.max_intensity - self.dim_factor*sum([sin(omega*self.clock)**2
                                               for omega in self.omegas])
        else:
            intensity = self.max_intensity
        self.color = glvec([c*intensity for c in self.base_color] + [1.0])

    def update(self, dt):
        self.clock += dt
        self.clock = self.clock%self.cycle_length
        if abs(self.clock - self.cycle_length) < dt:
            if self.flicker == False and random.random() > .67:
                self.flicker = True
            elif self.flicker == True and random.random() > .33:
                self.flicker = False
        self.set_color()
    
