import pyglet
from pyglet.gl import *

class Camera:
    def __init__(self, eye, target):
        '''
        parameters:
            eye (list of 3 float): camera position
            target (list of 3 float): target position
        '''
        self.eye = eye
        self.target = target
        self._pitch = 0
        self._yaw = 0
        self._roll = 0
    
    def focus(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.eye[0], self.eye[1], self.eye[2],
                  self.target[0], self.target[1], self.target[2],
                  0, 1, 0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(90, 1, 1, 5000)
        glEnable(GL_LIGHTING)

    def hud_mode(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_LIGHTING)
