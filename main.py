import pyglet
import page
from camera import Camera
from math import sin, cos
import lights

if __name__ == '__main__':
    width, height, size = 50, 50, 500
    pointsL = [(0, 0),
               (-.07*size, .15*size),
               (-.2*size, .15*size),
               (-.3*size, .12*size),
               (-size, .06*size)]
    config = pyglet.gl.Config(sample_buffers=1, samples=4)
    window = pyglet.window.Window(3*size, 2*size, config=config)

    length = size/width
    img = pyglet.image.load('parchment.png')
    flagR = page.FlatMesh(width, height, length, img.texture)
    flagL = page.FlatMesh(width, height, length, img.texture)
    lightset = lights.LightSet()
    candle = lightset.add_light(lights.CandleLight([size/2, size/2, 800], .9))
    lightset.set_ambient([0, 0, 0])
    camera =  Camera([0, .2*size, .8*size], [0, size/2, 0], aspect=window.width*1.0/window.height)
    
    @window.event
    def on_draw():
        window.clear()
        camera.focus()
        lightset.draw()
        flagR.draw()
        flagL.draw()
        camera.hud_mode()

    verticesL, verticesR, normalsL, normalsR = [], [], [], []
    for i in range(width+1):
        xL, zL, nxL, nzL = page.bezier5curve(i*1.0/(width+1), pointsL)
        for j in range(height+1):
            verticesL.extend([xL, j*length, zL])
            normalsL.extend([nxL, 0, nzL])
            verticesR.extend([-xL, j*length, zL])
            normalsR.extend([-nxL, 0, nzL])
    flagR.update_vertices(verticesR)
    flagR.update_normals(normalsR)
    flagL.update_vertices(verticesL)
    flagL.update_normals(normalsL)

    def update(dt):
        candle.update(dt)
        window.clear()
        
    pyglet.clock.schedule_interval(update, 2.0/120)

    pyglet.app.run()
