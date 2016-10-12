import pyglet
import geometry
from camera import Camera
import numpy as np
import director as dr
import lights
'''converts WaveFront files into nested lists of vertices, normals, and texture coordinates,
suitable for flattening and passing as pyglet vertex lists. Only designed to work with
simple blender objects, not to match the full spec.'''

class WaveParser:
    def __init__(self):
        self.vertices = None
        self.normals = None
        self.tex_coords = None

    def parse(self, mfile):
        lines = mfile.readlines()
        self.vertices, self.normals, self.tex_coords = [], [], []
        raw_vertices, raw_normals, raw_tex_coords = [], [], []
        raw_indices = {}
        self.index_array = {}
        used_vertices, used_normals, used_tex_coords = set(), set(), set()
        combos = {}
        
        for i, line in enumerate(lines):
            vals = line.lower().strip().split()
            if vals[0] == 'o':
                trimmed = vals[1].split('_')[0]
                raw_indices[trimmed] = []
                curr_indices = raw_indices[trimmed]
            elif vals[0] == 'v':
                raw_vertices.append([float(val) for val in vals[1:4]])
            elif vals[0] == 'vn':
                raw_normals.append([float(val) for val in vals[1:4]])
            elif vals[0] == 'vt':
                raw_tex_coords.append([float(val) for val in vals[1:3]])
            elif vals[0] == 'f':
                curr_indices.append(vals[1:])

        def extend_lists(val):
            if not val in combos:
                v, t, n = val.split('/')
                try:
                    self.vertices.append(raw_vertices[int(v)-1])
                    self.normals.append(raw_normals[int(n)-1])
                    self.tex_coords.append(raw_tex_coords[int(t)-1])
                except IndexError:
                    print v, t, n
                    print len(raw_vertices)
                    print len(raw_normals)
                    print len(raw_tex_coords)
                    assert False
                combos[val] = len(self.vertices) - 1
            return combos[val]
                
        for key, val in raw_indices.items():
            self.index_array[key] = []
            for indices in val:
                self.index_array[key].append([extend_lists(v) for v in indices])
        self.cleanup()

    def cleanup(self):
        self.vertices = np.array(self.vertices)
        self.normals = np.array(self.normals)
        self.tex_coords = np.array(self.tex_coords)
        self.fix_indices()

    def fix_indices(self):
        '''set index sequences so they are counter-clockwise when the average of the
        normals points towards the camera. Only guaranteed to work for triangles.'''
        self.indices = {}
        for key, val in self.index_array.items():
            self.indices[key] = []
            for indices in val:

                face_normal = np.cross(self.vertices[indices[2]] - self.vertices[indices[0]],
                                                     self.vertices[indices[1]] - self.vertices[indices[0]])
                avg_normal = np.sum(self.normals[indices], axis=0)
                if np.dot(avg_normal, face_normal)  > 0:
                    indices[2], indices[1] = indices[1], indices[2]
                self.indices[key].extend(indices)

    def print_out(self):
        for i in range(len(self.vertices)):
            print 'v: %r t: %r n: %r' %(listround(self.vertices[i], 2),
                                        listround(self.tex_coords[i], 2),
                                        listround(self.normals[i], 2))
        print
        print self.indices


def listround(mlist, digits=0):
    return [round(v, digits) for v in mlist]

def test():
    parser = WaveParser()
    with open('imagery/book.obj') as book:
        parser.parse(book)
    vertices = 500*parser.vertices
    normals = parser.normals
    tex_coords = parser.tex_coords
    colors = np.ones((vertices.shape[0], 4))
    texture = pyglet.image.load('parchment.png').texture
    window = pyglet.window.Window(800, 800)
    camera = Camera([0, .5, 1000], [0, 0, 0], 1, 90, window.width, window.height)
    scene = dr.Scene(camera)
    for key, indices in parser.indices.items():
        mesh = geometry.Mesh(indices, vertices, normals, tex_coords, colors, texture)
        scene.add_world_object(mesh)
    scene.add_light(lights.CandleLight([100, 200, 500], 1.0))
    scene.set_ambient([.3, .3, .9])
    def rotate_cam(angle):
        camera.eye = geometry.matrix_transform(camera.eye,
            geometry.make_rotation_matrix([0, np.sqrt(.5), np.sqrt(.5)], .5*angle))
    pyglet.clock.schedule_interval(rotate_cam, 1.0/60) 
    @window.event
    def on_draw():
        window.clear()
        scene.draw()
    pyglet.app.run()

if __name__ == '__main__':
    test()
        
