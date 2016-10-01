from pyglet.gl import *
from math import sin, cos, sqrt
from ctypes import sizeof

def generate_flat_mesh(width, height, length):
    '''create information necessary for OpenGL to render quads, formatted for passing to the GPU
    Parameters:
        width (int): the width of the grid in neurons
        height (int): the height of the grid in neurons
        length (int): length of grid edges in pixels
    Returns:
        vertices, normals, colors, texture coordinates, indices (lists of OpenGL types)
    '''
    #set up the coordinates of all corners
    vertices = []
    colors = []
    normals = []
    tex_coords = []
    for j in range(height+1):
        for i in range(width+1):
            vertices.extend([i*length, j*length, 20*sin(.1*i)])
            colors.extend([1.0, 1.0, 1.0, 1.0])
            normals.extend([0, 0, 1])
            tex_coords.extend([0, 0, i*1.0/width, j*1.0/height])
    print tex_coords
    vertices = (GLfloat * len(vertices))(*vertices)
    colors = (GLfloat * len(colors))(*colors)
    normals = (GLfloat * len(normals))(*normals)
    tex_coords = (GLfloat * len(tex_coords))(*tex_coords)
    
    #create list of quad indices
    indices = []
    for x in range(width):
        for y in range(height):
            index0 = y*(width+1) + x
            index1 = index0 + 1
            index2 = index1 + (width+1)
            index3 = index2 - 1
            if (x+y)%2:
                indices.extend([index0, index1, index2])
                indices.extend([index2, index3, index0])
            else:
                indices.extend([index0, index1, index3])
                indices.extend([index2, index3, index1])
    indices = (GLuint * len(indices))(*indices)
    return vertices, normals, colors, tex_coords, indices

class TestFlag(object):
    def __init__(self, width, height, length, texture):
        self.width, self.height, self.length = width, height, length
        self.texture = texture
        self.vertices, self.normals, self.colors, self.tex_coords, self.indices = generate_flat_mesh(
                                                                        self.width, self.height, self.length)
        
    def draw(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        #glEnableClientState(GL_COLOR_ARRAY)
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)
        glVertexPointer(3, GL_FLOAT, 0, self.vertices)
        glNormalPointer(GL_FLOAT, 0, self.normals)
        #glColorPointer(4, GL_FLOAT, 0, self.colors)
        glTexCoordPointer(4, GL_FLOAT, 0, self.tex_coords)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, self.indices)
        glDisable(self.texture.target)

    def update_vertices(self, vertices):
        assert len(vertices) == len(self.vertices), "Invalid number of vertices passed"
        self.vertices = (GLfloat * len(vertices))(*vertices)
            
    
        
