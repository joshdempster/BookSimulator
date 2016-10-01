import pyglet
import page
from camera import Camera
from math import sin, cos
import lights

if __name__ == '__main__':
    config = pyglet.gl.Config(sample_buffers=1, samples=4)
    window = pyglet.window.Window(800, 800, config=config)

    width, height, size = 1, 1, 400
    length = size/width
    img = pyglet.image.load('texture_test.bmp')
    flag = page.TestFlag(width, height, length, img.texture)
    lightset = lights.LightSet()
    camera =  Camera([200, 200, -500], [200, 200, 0])
    @window.event
    def on_draw():
        window.clear()
        camera.focus()
        lightset.draw()
        flag.draw()
        camera.hud_mode()

    curr_time = 0

    def update(dt):
        global curr_time
        curr_time += dt
        #camera.eye[0] = 200+1000*sin(curr_time)
        #camera.eye[2] = -1000*cos(curr_time)
        vertices = []
        for j in range(flag.height+1):
            for i in range(flag.width+1):
                vertices.extend([i*flag.length, j*flag.length, 50*sin(i*.01*flag.length+5*curr_time)])
        flag.update_vertices(vertices)
    #pyglet.clock.schedule_interval(update, 1.0/120)

    pyglet.app.run()
