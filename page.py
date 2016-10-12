import director as dr
import geometry
import framebuffer
import pyglet
from pyglet.gl import *
import camera
import lights
from loremipsum import get_paragraphs
from wave_parser import WaveParser
import os

'''All the logic associated with the book simulation itself'''

pyglet.font.add_file(os.getcwd() + '/fonts/Summerti.ttf')
summer = pyglet.font.load('Summerti')


class PageTurner(dr.Updater):
    vector = [0, 1, 0]
    
    def __init__(self, target, initial, duration, right_to_left=True):
        '''
        Parameters:
            right_to_left (bool): which way to turn the page
            top: whether the page is top or bottom
        '''
        dr.Updater.__init__(self, target, initial, duration)
        self.curve = Page.curve
        self.right_to_left = right_to_left
        direction = 2*(int(right_to_left) -.5)
        self.angles = -direction*geometry.get_flap_angles(Page.width, self.curve)

    def on_update(self, manager, dt, targets=[]):
        dr.Updater.on_update(self, manager, dt)
        if len(targets) == 0:
            targets = [self.target]
        if self.age < 0:
            return
        for target in targets:
            angles = self.age*1.0/self.duration*self.angles
            if  target.right_side:
                vertices = Page.right_vertices
                if target.face_up:
                    normals = Page.right_top_normals
                else:
                    normals = Page.right_bottom_normals
            else:
                vertices = Page.left_vertices
                if target.face_up:
                    normals = Page.left_top_normals
                else:
                    normals = Page.left_bottom_normals
            vertices = geometry.flap(vertices, self.vector, angles)
            normals = geometry.flap(normals, self.vector, angles)
            target.mesh.update_vertices(vertices)
            target.mesh.update_normals(normals)
        if self.duration is not None:
            if self.age == self.duration:
                self.end()


class FolioTurner(dr.Updater):
    def __init__(self, target, initial, duration, right_to_left):
        dr.Updater.__init__(self, target, initial, duration)
        self.halfway = False
        self.right_to_left = right_to_left
        if right_to_left: #turning right to left
            self.child_targets = (self.target.middle_right, self.target.top_right)
        else:
            self.child_targets = (self.target.middle_left, self.target.top_left)
        self.child = PageTurner(self.child_targets[0], initial, duration, right_to_left)
        self.child.active = True

    def start(self, scene):
        dr.Updater.start(self, scene)
        self.target.flipping = True

    def on_update(self, manager, dt):
        self.child.on_update(self, dt, self.child_targets)
        dr.Updater.on_update(self, manager, dt)
        if not self.halfway and self.age > .5*self.duration:
            self.halfway = True
            self.target.on_half_turned(self, self.target, self.right_to_left)
        if self.child.dead:
            self.end()

    def end(self):
        for target in self.child_targets:
            target.face_up = not target.face_up
            target.right_side = not target.right_side
            target.set_mesh()
        (self.target.bottom_right, self.target.middle_right,
                self.target.bottom_left, self.target.middle_left) = (None, None, None, None)
        self.target.flipping = False
        dr.Updater.end(self)     


class BlenderObject(object):
    '''convert an externally created WaveFront object into an OpenGL renderable mesh'''
    def __init__(self):
        parser = WaveParser()
        parser.parse(open(self.object_name))
        vertices = self.size*parser.vertices
        normals = parser.normals
        indices = parser.indices.items()[0][1]
        tex_coords = parser.tex_coords
        colors = [[1, 1, 1, 1]]*vertices.shape[0]
        geometry.translate(vertices, self.origin_shift, inplace=True)
        self.meshes = []
        for key in self.texture_names:
            texture = pyglet.image.load(self.texture_names[key]).texture
            self.meshes.append(geometry.Mesh(
                parser.indices[key], vertices, normals, tex_coords,
                                  colors, texture)
                               )

    def draw(self):
        for mesh in self.meshes:
            mesh.draw()


class BookCover(BlenderObject):
    '''background for the pages'''
    object_name = 'imagery/book.obj'
    size = 260
    texture_names = {'spine': 'leather.png',
                 'cover': 'leather.png',
                     'pages': 'parchment.png',
                            }
    origin_shift = [2, 2, -30]

    
class Page(object):
    '''should only be added as a world_object to avoid messing up cameras'''
    background_name = 'parchment.png'
    size = 500
    width, height = 50, 50
    length = size/width
    curve = geometry.PageCurve(size)
    right_vertices, right_top_normals = geometry.make_vertices(width, height, length, curve)
    left_vertices = geometry.flip(right_vertices, axis='x')
    right_bottom_normals = geometry.reverse(right_top_normals)
    left_top_normals = geometry.flip(right_top_normals, 'x')
    left_bottom_normals = geometry.reverse(left_top_normals)
    right_top_tex_coords = geometry.make_tex_coords(right_vertices)
    right_bottom_tex_coords = geometry.flip(right_top_tex_coords, 'x')
    colors = geometry.make_solid_colors(width, height)
    #create a simple shadowing effect in the page crease
    colors[0][:] = [.5, .5, .5, 1.0]
    colors[1][:] = [.7, .7, .7, 1.0]
    colors[2][:] = [.8, .8, .8, 1.0]
    colors[3][:] = [.9, .9, .9, 1.0]
    colors[4][:] = [.95, .95, .95, 1.0]
    top_indices = geometry.make_indices(width, height, CCW=True)
    bottom_indices = geometry.make_indices(width, height, CCW=False)
    
    def __init__(self, mcamera, window, scene, face_up, right_side):
        '''
        Parameters:
            camera, window: camera and pyglet.window.Window instances
            face_up (bool): page is initially face_up
            right_side (bool): whether page is initially to the left or right of the opening
        '''
        self.camera = mcamera
        self.face_up = face_up
        self.right_side = right_side
        self.top_right = (self.face_up == self.right_side)
        self.flat_scene = scene
        self.texture = self.flat_scene.get_texture()
        indices = self.choose_indices()
        vertices = self.choose_vertices()
        tex_coords = self.choose_tex_coords()
        normals = self.choose_normals()
        self.mesh = geometry.Mesh(indices, vertices, normals, tex_coords, self.colors,
                                  self.texture)

    def set_mesh(self):
        vertices = self.choose_vertices()
        self.mesh.update_vertices(vertices)
        normals = self.choose_normals()
        self.mesh.update_normals(normals)

    def choose_indices(self):
        if self.top_right:
            return self.top_indices
        else:
            return self.bottom_indices

    def choose_vertices(self):
        if self.right_side:
            return self.right_vertices
        else:
            return self.left_vertices

    def choose_normals(self):
        if self.face_up:
            if self.right_side:
                return self.right_top_normals
            else:
                return self.left_top_normals
        else:
            if self.right_side:
                return self.right_bottom_normals
            else:
                return self.left_bottom_normals

    def choose_tex_coords(self):
        if self.top_right:
            return  self.right_top_tex_coords
        else:
            return self.right_bottom_tex_coords

    def set_texture(self):
        self.flat_scene.draw()

    def draw(self):
        self.camera.focus()
        pyglet.gl.glEnable(pyglet.gl.GL_LIGHTING)
        self.mesh.draw()
        self.camera.hud_mode()

    def __del__(self):
        del self.flat_scene
        del self.mesh
        del self.texture


class Folio(dr.Scene):
    '''Next level up from Page, manages the collection of pages currently being shown to the user'''
    def __init__(self, camera, window, scenes):
        dr.Scene.__init__(self, camera)
        self.bottom_left = None
        self.middle_left = None
        self.top_left = Page(camera, window, scenes[0], True, False)
        self.bottom_right = None
        self.middle_right = None
        self.top_right = Page(camera, window, scenes[1], True, True)
        self.flipping = False

    def set_textures(self):
        for page in [self.bottom_left, self.bottom_right, self.middle_left, self.middle_right,
                     self.top_left, self.top_right]:
            try:
                page.set_texture()
            except AttributeError:
                pass

    def draw(self):
        for page in [self.bottom_left, self.bottom_right, self.middle_left, self.middle_right,
                     self.top_left, self.top_right]:
            try:
                page.draw()
            except AttributeError:
                pass

    def on_half_turned(self, updater, target, right_to_left):
        if right_to_left:
            self.shuffle_left()
        else:
            self.shuffle_right()

    def shuffle_left(self):
        self.bottom_left = self.top_left
        self.middle_left = self.top_right
        self.top_left = self.middle_right
        self.top_right = self.bottom_right
        self.bottom_right = None
        self.middle_right = None
        self.dispatch_event('on_empty_right', self)

    def shuffle_right(self):
        self.bottom_right = self.top_right
        self.middle_right = self.top_left
        self.top_right = self.middle_left
        self.top_left = self.bottom_left
        self.bottom_left = None
        self.middle_left = None
        self.dispatch_event('on_empty_left', self)
Folio.register_event_type('on_empty_right')
Folio.register_event_type('on_empty_left')


class Book(dr.Scene):
    '''Combines management of Folio with managing the contents of pages not
    currently shown and decorative background objects.'''
    def __init__(self, mcamera, window, npages, starting=0):
        '''
        Parameters:
            mcamera, window (camera and window instances)
            npages (int): number of dummy pages to start with
            starting (int): which page to open with
        '''
        self.current = starting #current left page
        dr.Scene.__init__(self, mcamera)
        self.window = window
        self.background = pyglet.sprite.Sprite(
            pyglet.image.load(Page.background_name))
        self.simple_camera = camera.SimpleCamera(
            self.background.width, self.background.height)
        self.scenes = [dr.TextureScene(
            self.simple_camera,
            window,
            self.background.width, self.background.height,
            self.background)
                       for i in range(npages)]
        self.pick = PagePicker(self.camera, self.window)
        self.cover = self.add_world_object(BookCover())
        self.folio = Folio(mcamera, window, self.scenes[self.current:self.current+2])
        self.add_world_object(self.folio)
        self.window.push_handlers(self)

    def draw(self):
        self.folio.set_textures()
        dr.Scene.draw(self)

    def flip_right(self, new_scene):
        '''new_scene: scene that will take up the new left page'''
        self.set_to(new_scene)
        self.folio.middle_right = Page(
                self.camera, self.window, self.scenes[self.current], False, True)
        self.folio.bottom_right = Page(
                self.camera, self.window, self.scenes[self.current+1], True, True)
        self.add_updater(FolioTurner(self.folio, 0, 1.5, True))

    def flip_left(self, new_scene):
        self.set_to(new_scene)
        self.folio.middle_left = Page(
                self.camera, self.window, self.scenes[self.current], False, False)
        self.folio.bottom_left = Page(
                self.camera, self.window, self.scenes[self.current+1], True, False)
        self.add_updater(FolioTurner(self.folio, 0, 1.5, False))

    def set_to(self, new_scene):
        if isinstance(new_scene, int):
            self.current = new_scene
        else:
            self.current  = self.scenes.index(new_scene)

    def on_mouse_press(self, x, y, button, mods):
        if self.folio.flipping:
            return
        side, u, v = self.pick(x, y)
        if side == 'right' and u > .8 and self.current < len(self.scenes) - 3:
            self.flip_right(self.scenes[self.current + 2])
        elif side == 'left' and u < .2 and self.current > 1:
            self.flip_left(self.scenes[self.current - 2])

class PagePicker(object):
    '''uses pixel color to translate a click into UV coordinates in the page'''
    def __init__(self, camera, window):
        self.camera = camera
        self.window = window
        self.read_out = (GLfloat * 3)(0, 0, 0)
        right_colors = geometry.make_coordinate_colors(Page.width, Page.height, 1.0, True)
        left_colors = geometry.make_coordinate_colors(Page.width, Page.height, .5, False)
        texture = pyglet.image.SolidColorImagePattern((255, 255, 255, 255)
                                                      ).create_image(1024, 1024).texture
        self.right_mesh = geometry.Mesh(
            Page.top_indices, Page.right_vertices, Page.right_top_normals,
            Page.right_top_tex_coords, right_colors, texture
            )
        self.left_mesh = geometry.Mesh(
            Page.bottom_indices, Page.left_vertices, Page.left_top_normals,
            Page.right_bottom_tex_coords, left_colors, texture
            )

    def draw(self):
        self.window.clear()
        self.camera.focus()
        pyglet.gl.glDisable(pyglet.gl.GL_LIGHTING)
        self.right_mesh.draw()
        self.left_mesh.draw()

    def __call__(self, x, y):
        self.draw()
        glReadPixels(x, y, 1, 1, GL_RGB, GL_FLOAT, self.read_out)
        u, green, v = tuple([v for v in self.read_out])
        if green > .75:
            side = 'right'
        elif green > .25:
            side = 'left'
        else:
            side = None
        return (side, u, v)


def create_random_page():
    '''lorem ipsum generator'''
    text = '\t'+'\n\t'.join(get_paragraphs(2))
    return pyglet.text.Label(text, x=100, y=924, width=824, height=400, multiline=True,
                             color=[20, 12, 8, 200], font_name='Summertime', font_size=30)

