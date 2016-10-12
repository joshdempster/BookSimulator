import pyglet
import framebuffer
import lights
'''Stage management classes. The extra layer of abstraction is useful for extending to a more
complicated game.'''

class Director(object):
    '''The head honcho. Just one should be needed per game'''
    def __init__(self):
        self.scenes = []
        self.active_scene = None

    def update(self, dt):
        if self.active_scene:
            self.active_scene.update(dt)

    def draw(self):
        if self.active_scene:
            self.active_scene.draw()

    def add_scene(self, scene):
        self.scenes.append(scene)
        return scene

    def remove_scene(self, scene):
        scene.__del__()
        self.scenes.remove(scene)

    def start_scene(self, scene):
        if not scene in self.scenes:
            self.scenes.append(scene)
        self.active_scene = scene


class Scene(pyglet.event.EventDispatcher):
    '''An abstract game object container, which can be the entire environment (the parent scene)
    or some element in the environment. Scenes are dynamic (have an update method and an
    'on_update' event that updaters can use to add themselves to the update method) and
    graphical (have a draw method).'''
    def __init__(self, camera):
        self.lightSet = lights.LightSet()
        self.world_objects = [] #drawn with lighting and camera applied
        self.hud_objects = [] #drawn without camera or lighting
        self.camera = camera

    def draw(self):
        self.camera.focus()
        self.lightSet.draw()
        for obj in self.world_objects:
            obj.draw()
        self.camera.hud_mode()
        for obj in self.hud_objects:
            obj.draw()

    def update(self, dt):
        self.dispatch_event('on_update', self, dt)

    def add_updater(self, updater, start=True, end_behavior=None):
        def end(updater, target): self.remove_updater(updater)
        #specify what to do when the updater ends
        if end_behavior:
            self.on_end = end_behavior
        else:
            self.on_end = self.default_on_end
        updater.push_handlers(self)
        del self.on_end
        if start:
            updater.start(self)
        return updater

    def remove_updater(self, updater):
        self.remove_handlers(updater)

    def default_on_end(self, updater, target):
        self.remove_updater(updater)

    def add_world_object(self, obj):
        self.world_objects.append(obj)
        return obj

    def remove_world_object(self, obj):
        self.world_objects.remove(obj)

    def add_hud_object(self, obj):
        self.hud_objects.append(obj)
        return obj

    def remove_hud_object(self, obj):
        self.hud_objects.remove(obj)

    def add_light(self, light):
        self.lightSet.add_light(light)
        return light

    def remove_light(self, light):
        self.lightSet.remove_light(light)

    def set_ambient(self, color):
        self.lightSet.set_ambient(color)

Scene.register_event_type('on_update')


class TextureScene(Scene):
    '''draws to a custom framebuffer instead of the active window. Allows anything to be drawn
        on pages that could be rendered in the game, for example'''
    def __init__(self, camera, window, width, height, background):
        Scene.__init__(self, camera)
        self.framebuffer = framebuffer.Framebuffer(width, height)
        self.framebuffer.unbind(window)
        self.window = window
        self.background = background

    def draw(self):
        self.framebuffer.bind()
        self.camera.hud_mode()
        self.background.draw()
        self.camera.focus()
        #self.lightSet.draw()
        pyglet.gl.glDisable(pyglet.gl.GL_LIGHTING)
        for obj in self.world_objects:
            obj.draw()
        self.camera.hud_mode()
        for obj in self.hud_objects:
            obj.draw()
        self.framebuffer.unbind(self.window)

    def get_texture(self):
        return self.framebuffer.texture

    def __del__(self):
        del self.framebuffer


class Updater(pyglet.event.EventDispatcher):
    '''The basic method for having anything change while the app runs.'''
    def __init__(self, target, initial, duration, *args):
        '''
        Parameters:
            target: generally there will be some game object whose state the updater alters
            initial: initial age of the updater. If negative, the updater does nothing until positive.
             duration: how long after age=0 the updater persists. Use None for infinity, 0 for instant
        '''
        self.target = target
        self.children = []
        self.active = False
        self.age = initial
        self.next = None
        self.dead = False
        self.duration = duration

    def start(self, manager):
        self.active = True
        self.dispatch_event('on_start', self, self.target)
        manager.push_handlers(self)

    def pause(self):
        self.active = False

    def end(self):
        self.active = False
        self.dead = True
        self.dispatch_event('on_end', self, self.target)

    def on_update(self, scene, dt):
        if self.active:
            self.age += dt
        if self.duration is not None:
            if self.age > self.duration:
                self.age = self.duration

Updater.register_event_type('on_start')
Updater.register_event_type('on_end')     
