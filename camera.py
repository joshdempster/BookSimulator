import pyglet
from pyglet.gl import *
'''Two camera classes for setting up OpenGL views. SimpleCamera is strictly 2D and is designed
to render to a texture. Camera is a full 3D camera with an HUD mode for drawing 2D elements'''

class SimpleCamera:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def focus(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.width, 0, self.height)
        glEnable(GL_LIGHTING)

    def hud_mode(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.width, 0, self.height)
        glDisable(GL_LIGHTING)
    

class Camera:
    def __init__(self, eye, target, aspect, field_of_view, width, height):
        '''
        parameters:
            eye (list of 3 float): camera position
            target (list of 3 float): target position
            aspect (float): aspect ratio for window
            field_of_view(float): width of x axis in degrees
            width, height (int): window size
        '''
        self.eye = eye
        self.target = target
        self.aspect = aspect
        self.field_of_view = field_of_view
        self._pitch = 0
        self._yaw = 0
        self._roll = 0
        self.width = width
        self.height = height
    
    def focus(self):
        '''the 3D mode'''
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.eye[0], self.eye[1], self.eye[2],
                  self.target[0], self.target[1], self.target[2],
                  0, 1, 0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.aspect, 1, 5000)
        glEnable(GL_LIGHTING)

    def hud_mode(self):
        '''no lighting or view transformations will be applied'''
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.width, 0, self.height)
        glDisable(GL_LIGHTING)
