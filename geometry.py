import pyglet
from pyglet.gl import *
import numpy as np
from math import sin, cos, sqrt, atan2, pi
import random

'''Sets up the framework for rendering 3D objects with pyglet, and provides utility to functions
for generating curved meshes without needing to import them from WaveFront files. Also
provides convenience functions for altering meshes. Meshes are stored as numpy arrays for
fast transformations.'''

def make_indices(width, height, CCW=True):
    '''
    generate indices for glDrawElements to correctly tesselate a rectangular mesh with triangles
    Parameters:
        width, height (ints): number of horizontal and vertical edges in the mesh
        CCW (bool): changes the sense of the indices to counter-clockwise
    Returns: list of int
    '''
    indices = []
    for x in range(width):
        for y in range(height):
            index0 = x*(height+1) + y
            if not CCW:
                index1 = index0 + 1
                index2 = index0 + (height+1)
            else:
                index2 = index0 + 1
                index1 = index0 + (height+1)
            index3 = index0 + height + 2
            if (x+y)%2:
                indices.extend([index0, index1, index2])
                indices.extend([index3, index2, index1])
            else:
                indices.extend([index0, index1, index3])
                indices.extend([index0, index3, index2])
    return indices

def make_vertices(width, height, length, curve=None, bumpiness=(0, 0, .1)):
    '''
    Generate the vertices and normals for a mesh
    Parameters:
        width, height: as in make_indices
        length (float): length of mesh edges
        curve (None or instance of CurveX): specifies mesh shape
        bumpiness (tuple of 3 float): random deviation from curve in each direction
    Returns: (vertices, normals) (3D numpy arrays)
        Note: rows/first index corresponds to u values in the mesh, columns to v
    '''
    vertices, normals, = [], []
    for i in range(width+1):
        for mylist in vertices, normals:
            mylist.append([])
        x, z, nx, nz = i*length, 0, 0, 1 
        if isinstance(curve, CurveX):
            x, z, nx, nz = curve(i*1.0/width)
        elif curve is not None:
            raise ValueError, "if not None, curve must be CurveX instance"
        for j in range(height+1):
            y, ny = j*length, 0
            bump = [b *random.random()*length - .5 for b in bumpiness]
            vertices[-1].append([x+bump[0], y+bump[1] , z+bump[2]])
            normals[-1].append([nx, ny, nz])
    return np.array(vertices), np.array(normals)

def make_tex_coords(vertices):
    '''Returns unstretched texture coordinates'''
    #find the distance between each vertex and its lower and left neighbors
    #distances[0]: lower (-x) neighbor distances
    distances = [
        np.sqrt(np.sum(np.square(vertices - np.roll(vertices, 1, ax)), axis=2)) for ax in (0, 1)]
    for d in distances:
        d[0, :] = 0
        d[:, 0] = 0
    #sum to get unnormalized u, v surface coordinates
    tex_coords = [
        np.cumsum(distances[axis], axis=axis) for axis in 0, 1
        ]
    #normalize
    with np.errstate(invalid='ignore'):
        tex_coords[0] /= tex_coords[0][-1, :]
        tex_coords[0][:, 0] = 0
        tex_coords[1] /= tex_coords[1][:, -1, np.newaxis]
        tex_coords[1][0, :] = 0
    #make coordinates swapped
    return np.array(tex_coords).swapaxes(1, 2).swapaxes(0, 2)

def make_solid_colors(width, height, color=[1.0, 1.0, 1.0, 1.0]):
    ''' Returns RGBA colors for the mesh'''
    colors = []
    for i in range(width+1):
        colors.append([])
        for j in range(height+1):
           colors[-1].append(color)
    return np.array(colors)

def make_coordinate_colors(width, height, green, right_side=True):
    '''Useful for mousepicking. Since green is uniform, it identifies which object was picked'''
    colors = []
    for i in range(width+1):
        colors.append([])
        if right_side:
            u = i*1.0/width
        else:
            u = 1.0 - (i*1.0/width)
        for j in range(height+1):
            colors[-1].append([u, green, j*1.0/height, 1.0])
    return np.array(colors)

def _interpret_axis(axis):
    if axis == 'x':
        axis = 0
    elif axis == 'y':
        axis = 1
    elif axis == 'z':
        axis = 2
    return axis

def flip(vertices, axis, inplace=False):
    axis = _interpret_axis(axis)
    if inplace:
        vertices[:, :, axis] = -vertices[:, :, axis]
        return vertices
    else:
        out = np.copy(vertices)
        out[:, :, axis] = -out[:, :, axis]
        return out

def reverse(vertices, inplace=False):
    if inplace:
        vertices *= -1
        return vertices
    else:
        return -1*vertices

def translate(vertices, vector, inplace=False):
    if inplace:
        vertices += vector
        return vertices
    else:
        out = np.copy(vertices)
        out += vector
        return out

def make_rotation_matrix(vector, angle):
    '''vector must be normalized! Rotates around the origin'''
    c = cos(angle)
    s = sin(angle)
    x, y, z = vector[0], vector[1], vector[2]
    return np.array([
            [c + x**2*(1-c),    x*y*(1-c) - z*s,    x*z*(1-c) + y*s],
            [y*x*(1-c) + z*s,   c + y**2*(1-c),    y*z*(1-c) - x*s],
            [z*x*(1-c) - y*s,   z*y*(1-c) + x*s,    c + z**2*(1-c)]
            ])

def matrix_transform(vertices, matrix, inplace=False):
    if inplace:
        vertices[:] = np.inner(vertices, matrix)
        return vertices
    else:
        return np.inner(vertices, matrix)

def flap(vertices, vector, angles, inplace=False):
    '''
    Allows rotation that is desynchronized (on the zero axis). Needed to turn pages
    Parameters:
        vertices (np.array), vector (len 3 iterable): as above
        angles (iterable): how much to rotate each row by. Length must match vertices.shape[0]
        '''
    matrix = np.zeros((3, 3))
    if inplace:
        v = vertices
    else:
        v = np.copy(vertices)
    for i, angle in enumerate(angles):
        matrix[:] = make_rotation_matrix(vector, angle)
        matrix_transform(v[i], matrix, inplace=True)
    return v

def get_flap_angles(width, curve):
    '''
    Angles to synchronize turning pages correctly
    Parameters:
        width (int): number of edges in zero axis
        curve(CurveX): geometry of initial conformation. Must be in the positive quadrant
    '''
    angles = []
    for i in range(width+1):
        x, z, nx, nz = curve(i*1.0/width)
        angles.append( pi - 2*atan2(z, x) )
    return np.array(angles)

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


class CurveX(object):
    def __init__(self):
        pass

    def __call__(self, x):
        raise NotImplementedError, "Abstract class - subclass to use"


class PageCurve(CurveX):
    '''curve for a right-facing page'''
    def __init__(self, size):
        points = [
            (0, 0),
            (.07*size, .15*size),
            (.2*size, .15*size),
            (.3*size, .12*size),
            (size, .06*size)
            ]
        def call(s): return bezier5curve(s, points)
        self.func = call

    def __call__(self, s):
        return self.func(s)

 
class Mesh(object):
    def __init__(self, indices, vertices, normals, tex_coords, colors, texture):
        '''
        parameters:
            indices (list of int): corners for each triangle in the mesh
            vertices (3D np array): vertex positions
            normals (3D np array): normals at each vertex
            tex_coords (3D np array): each vertice's position in the background texture
            colors (3D np array): 
            texture (pyglet.graphics.Texture): texture for mesh.
        '''
        self.vertices = vertices
        self.normals = normals
        self.colors = colors
        self.int_width, self.int_height = vertices.shape[0], vertices.shape[1]
        self.texture = texture
        self.group = pyglet.graphics.TextureGroup(self.texture)
        self.batch = pyglet.graphics.Batch()
        self.vertex_list = self.batch.add_indexed(
            (np.prod([i for i in vertices.shape[:-1]])), GL_TRIANGLES, self.group, indices,
            ('v3f', np.ravel(vertices)),
            ('n3f', np.ravel(normals)),
            ('t2f', np.ravel(tex_coords)),
            ('c4f', np.ravel(colors))
             )
                                
    def draw(self):
        glEnable(GL_NORMALIZE)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glEnable(GL_DEPTH_TEST)
        self.batch.draw()
        glDisable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)

    def update_normals(self, normals=None):
        if not normals is None:
            assert all([self.normals.shape[i]==normals.shape[i] for i in range(3)]
                       ), "Invalid shape for new normals"
            self.normals = normals
        self.vertex_list.normals = np.ravel(self.normals)
        
    def update_vertices(self, vertices=None):
        if not vertices is None:
            assert all([self.vertices.shape[i]==vertices.shape[i] for i in range(3)]
                   ), "Invalid shape for new vertices"
            self.vertices = vertices
        self.vertex_list.vertices = np.ravel(self.vertices)

    def reverse_normals(self):
        self.normals = -self.normals
        self.update_normals()
        
        
