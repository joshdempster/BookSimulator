import pyglet
from pyglet.gl import *
from math import sin, cos, sqrt

def generate_flat_mesh(width, height, length):
    '''create information necessary for OpenGL to render quads, formatted for passing to the GPU
    Parameters:
        width (int): number of horizontal edges
        height (int): number of vertical edges
        length (float): edge length
    Returns:
        vertices, normals, colors, texture coordinates, indices (lists)
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
            tex_coords.extend([i*1.0/width, j*1.0/height])
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
    return vertices, normals, colors, tex_coords, indices

class FlatMesh(object):
    def __init__(self, width, height, length, texture):
        '''
        parameters:
            width (int): number of horizontal edges
            height (int): number of vertical edges
            length (float): edge length
            texture (pyglet.graphics.Texture): image for mesh
        '''
        self.width, self.height, self.length = width, height, length
        self.texture = texture
        self.group = pyglet.graphics.TextureGroup(self.texture)
        self.batch = pyglet.graphics.Batch()
        vertices, normals, colors, tex_coords, indices = generate_flat_mesh(
                                                                        self.width, self.height, self.length)
        self.vertex_list = self.batch.add_indexed(
            len(vertices)/3, GL_TRIANGLES, self.group, indices,
            ('v3f', vertices),
            ('n3f', normals),
            ('c4f', colors),
            ('t2f', tex_coords)
            )
                                
    def draw(self):
        glEnable(GL_NORMALIZE)
        self.batch.draw()

    def update_normals(self, normals):
        assert len(normals) == len(self.vertex_list.normals), "Invalid number of normals passed"
        self.vertex_list.normals = normals
        
    def update_vertices(self, vertices):
        assert len(vertices) == len(self.vertex_list.vertices), "Invalid number of vertices passed"
        self.vertex_list.vertices = vertices

def bezier5curve(s, points):
    '''
    Generate bezier curve with five points
    Parameters:
        s (float): point along the curve
        points (list of 5 tuples of 2 float): points the curve passes through
    returns:
        [x, z, nx, nz]: location and norm of curve at that point
    '''
    prefactors = [1, 4, 6, 4, 1]
    out = [0, 0, 0, 0]
    for i, v in enumerate(prefactors):
        p = v * s**i * (1-s)**(4-i)
        for j in range(2):
            out[j] += p*points[i][j]
    normal_prefactors = [
        -4*(1-s)**3,
        4*(1-s)**3 - 12*s*(1-s)**2,
        12*s*(1-s)*(1- 2* s),
        12*s**2*(1-s) - 4*s**3,
        4*s**3
        ]
    ratio = sum([normal_prefactors[i]*points[i][1] for i in range(5)])*1.0/sum([
        normal_prefactors[i]*points[i][0] for i in range(5)])
    out[3] = (1+ratio**2)**(-.5)
    out[2] = -ratio*out[3]
    return out
    
            
    
        
