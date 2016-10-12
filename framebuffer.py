from pyglet.gl import *
import pyglet

class Framebuffer(object):
    '''An OpenGL framebuffer object with an associated texture, since pyglet's built-in
    classes don't seem to have a method to bind them as the active framebuffer'''
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.id = GLuint()
        glGenFramebuffers(1, self.id)
        glBindFramebuffer(GL_FRAMEBUFFER, self.id)
        self.texture = pyglet.image.Texture.create(width, height, min_filter=GL_LINEAR,
                                                   mag_filter=GL_LINEAR)
        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                               self.texture.id, 0)
        
        draw_buffers = GLenum(GL_COLOR_ATTACHMENT0)
        glDrawBuffers(1, draw_buffers)
        status =  glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status == GL_FRAMEBUFFER_COMPLETE:
            pass
        elif status == GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT:
            assert False, "Incomplete attachment"
        elif status == GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT:
            assert False, "Must have at least one image"
        elif status == GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER:
            assert False, "Draw buffer missing color attachment point"
        elif status == GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER:
            assert False, "Read buffer missing attachment point"
        elif status == GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE:
            assert False, "Mismatched multisampling"
        elif status == GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS:
            assert False, "Mismatched numbers of layers"
        else:
            assert False, "Unknown error %r" %status
        #note: framebuffer is bound by default after initializing!

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.id)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT)

    def unbind(self, window):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, window.width, window.height)

    def __del__(self):
        del self.texture
        glDeleteFramebuffers(1, self.id)
        glDeleteRenderbuffers(1, self.depth_id)

