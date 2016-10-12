import pyglet
import director as dr
import page
from camera import Camera
import lights


def main():
    config = pyglet.gl.Config(sample_buffers=1, samples=4)
    window  = pyglet.window.Window(1200, 600, config=config)
    camera = Camera(
        [0, 200, 1200],
        [0, page.Page.size/2, 0],
        aspect=window.width*1.0/window.height,
        field_of_view=30, width=window.width, height=window.height)
    director = dr.Director()
    book = page.Book(camera, window, 20)
    for scene in book.scenes:
        scene.add_hud_object(page.create_random_page())
    light = book.add_light(lights.CandleLight([250, 350, 800], .9))
    book.set_ambient([.05, .07, .08])
    director.start_scene(book)
    @window.event
    def on_draw():
        window.clear()
        director.draw()
    pyglet.clock.schedule_interval(director.update, 1.0/60)
    pyglet.app.run()

if __name__ == '__main__':
    main()
