""" Quest - An epic journey.

Simple demo that demonstrates PyTMX and pyscroll.

requires pygame and pytmx.

https://github.com/bitcraft/pytmx

pip install pytmx
"""
import os.path

import pygame
from pygame.locals import *
from pytmx.util_pygame import load_pygame

import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup

# define configuration variables here
RESOURCES_DIR = 'data'

HERO_JUMP_HEIGHT = 180
HERO_MOVE_SPEED = 200  # pixels per second
GRAVITY = 1000
MAP_FILENAME = 'maps/dungeon_0.tmx'


# simple wrapper to keep the screen resizeable
def init_screen(width, height):
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    return screen


# make loading maps a little easier
def get_map(filename):
    return os.path.join(RESOURCES_DIR, filename)


# make loading images a little easier
def load_image(filename):
    return pygame.image.load(os.path.join(RESOURCES_DIR, filename))



class Hero(pygame.sprite.Sprite):
    """ Our Hero

    The Hero has three collision rects, one for the whole sprite "rect" and
    "old_rect", and another to check collisions with walls, called "feet".

    The position list is used because pygame rects are inaccurate for
    positioning sprites; because the values they get are 'rounded down'
    as integers, the sprite would move faster moving left or up.

    Feet is 1/2 as wide as the normal rect, and 8 pixels tall.  This size size
    allows the top of the sprite to overlap walls.  The feet rect is used for
    collisions, while the 'rect' rect is used for drawing.

    There is also an old_rect that is used to reposition the sprite if it
    collides with level walls.
    """



    def __init__(self, map_data_object):
        pygame.sprite.Sprite.__init__(self)

        self.STATE_STANDING = 0
        self.STATE_WALKING = 1
        self.STATE_JUMPING = 2

        self.FRAME_DELAY_STANDING =1
        self.FRAME_DELAY_WALKING = 1
        self.FRAME_DELAY_JUMPING = 1

        self.FACING_RIGHT = 0
        self.FACING_LEFT = 1

        self.MILLISECONDS_TO_SECONDS = 1000.0

        self.COLLISION_BOX_OFFSET = 8


        self.time_in_state = 0.0
        self.current_walking_frame = 0
        self.current_standing_frame = 0
        self.current_jumping_frame = 0
        self.load_sprites()
        self.velocity = [0, 0]
        self.state = self.STATE_STANDING
        self.facing = self.FACING_RIGHT
        self._position = [map_data_object.x, map_data_object.y]
        self._old_position = self.position
        self.rect = pygame.Rect(8, 0, self.image.get_rect().width - 8, self.image.get_rect().height)

    def set_state(self, state):
        if self.state != state:
            self.state = state
            self.time_in_state = 0.0


    def load_sprites(self):
        self.spritesheet = Spritesheet('data/art/platformer_template_g.png')
        # Sprite is 16x16 pixels at location 0,0 in the file...
        #image = ss.image_at((0, 0, 32, 32))
        #images = []
        # Load two images into an array, their transparent bit is (255, 255, 255)
        standing_images = self.spritesheet.images_at((
            pygame.Rect(0, 0, 32, 32),pygame.Rect(32, 0, 32, 32),
            pygame.Rect(64, 0, 32, 32),pygame.Rect(96, 0, 32, 32)
            ), colorkey= (0,255,81))

        walk_images = self.spritesheet.images_at((
            pygame.Rect(128, 0, 32, 32),pygame.Rect(160, 0, 32, 32),
            pygame.Rect(192, 0, 32, 32),pygame.Rect(224, 0, 32, 32),
            pygame.Rect(0, 0, 32, 32),pygame.Rect(32, 0, 32, 32),
            pygame.Rect(64, 0, 32, 32),pygame.Rect(96, 0, 32, 32),
            ), colorkey= (0,255,81))

        jumping_images = self.spritesheet.images_at((
            pygame.Rect(160, 160, 32, 32),
            ), colorkey= (0,255,81))

        self.walk_images = []
        for walk_image in walk_images:
            self.walk_images.append(walk_image.convert_alpha())


        self.standing_images = []
        for standing_image in standing_images:
            self.standing_images.append(standing_image.convert_alpha())

        self.jumping_images = []
        for jumping_image in jumping_images:
            self.jumping_images.append(jumping_image.convert_alpha())


        self.image = self.standing_images[self.current_standing_frame]

    @property
    def position(self):
        return list(self._position)

    @position.setter
    def position(self, value):
        self._position = list(value)

    def get_floor_sensor(self):
        return pygame.Rect(self.position[0]+self.COLLISION_BOX_OFFSET, self.position[1]+2, self.rect.width -self.COLLISION_BOX_OFFSET, self.rect.height)

    def get_ceiling_sensor(self):
        return pygame.Rect(self.position[0]+self.COLLISION_BOX_OFFSET, self.position[1]-self.rect.height, self.rect.width, 2)

    def get_body_sensor(self):
        return pygame.Rect(self.position[0]+self.COLLISION_BOX_OFFSET, self.position[1], self.rect.width -self.COLLISION_BOX_OFFSET, self.rect.height)


    def calc_grav(self, game, dt):
        """ Calculate effect of gravity. """
        floor_sensor = self.get_floor_sensor()
        collidelist = floor_sensor.collidelist(game.walls)

        hero_is_airborne = collidelist == -1


        if hero_is_airborne:
            if self.velocity[1] == 0:
                self.velocity[1] = GRAVITY * dt
            else:
                print("increasing downward velocity: {}".format(self.velocity[1]))
                self.velocity[1] += GRAVITY * dt
                print("is now: {}".format(self.velocity[1]))

    def animate(self, dt, game):
        if(self.state == self.STATE_WALKING):
            #if self.time_in_state > self.FRAME_DELAY_WALKING:
            self.current_walking_frame  = int(self.time_in_state * self.MILLISECONDS_TO_SECONDS % len(self.walk_images))
            self.image = self.walk_images[self.current_walking_frame]
            self.time_in_state += dt

            print("Walking frame: {}".format(self.current_walking_frame))
        elif(self.state == self.STATE_STANDING):
            #if self.time_in_state > self.FRAME_DELAY_STANDING:
            self.current_standing_frame  = int(self.time_in_state * self.MILLISECONDS_TO_SECONDS % len(self.standing_images))
            self.image = self.standing_images[self.current_standing_frame]
            self.time_in_state += dt
            print("time_standing: {}".format(self.time_in_state))
            print("len(walk_images){}".format(len(self.walk_images)))
            print("Standing frame: {}".format(self.current_standing_frame))
        elif(self.state == self.STATE_JUMPING):
            #if self.time_in_state > self.FRAME_DELAY_STANDING:
            self.current_jump_frame = int(self.time_in_state * self.MILLISECONDS_TO_SECONDS % len(self.jumping_images))
            self.image = self.jumping_images[self.current_jump_frame]
            self.time_in_state += dt
            print("time_standing: {}".format(self.time_in_state))
            print("len(jump_images){}".format(len(self.jumping_images)))
            print("Jumping")
        else:
            print("state is {}".format(self.state))
        print("delta_time: {}".format(dt))

        if self.facing == self.FACING_LEFT:
            self.image = pygame.transform.flip(self.image,True,False)

    def update(self, dt, game):
        self.calc_grav(game, dt)
        self.animate(dt, game)

        self._old_position = self._position[:]
        self.move(dt, game)


    def move(self, dt, game):
        # Move each axis separately. Note that this checks for collisions both times.
        dx = self.velocity[0]
        dy = self.velocity[1]
        if dx != 0:
            self.move_single_axis(dx, 0, dt)
        if dy != 0:
            self.move_single_axis(0, dy, dt)
        self.rect.topleft = self._position
    def move_single_axis(self, dx, dy, dt):
        #print("hero_destination: ({}, {})".format(dx *dt, dy *dt))
        self._position[0] += dx * dt
        self._position[1] += dy * dt

        #print("Game walls: {}".format(game.walls))
        self.rect.topleft = self._position


        body_sensor = self.get_body_sensor()
        for wall in game.walls:
            if body_sensor.colliderect(wall.rect):
                if dx > 0: # Moving right; Hit the left side of the wall
                    #print(" -- Moving right; Hit the left side of the wall")
                    self.rect.right = wall.rect.left
                if dx < 0: # Moving left; Hit the right side of the wall
                    #print(" -- Moving left; Hit the right side of the wall")
                    self.rect.left = wall.rect.right - self.COLLISION_BOX_OFFSET
                if dy > 0: # Moving down; Hit the top side of the wall
                    #print(" -- Moving down; Hit the top side of the wall")
                    self.rect.bottom = wall.rect.top
                if dy < 0: # Moving up; Hit the bottom side of the wall
                    #print(" -- Moving up; Hit the bottom side of the wall")
                    self.rect.top = wall.rect.bottom

        self._position[0] = self.rect.topleft[0]
        self._position[1] = self.rect.topleft[1]



class Wall(pygame.sprite.Sprite):
    """
        A sprite extension for all the walls in the game
    """

    def __init__(self, map_data_object):
        pygame.sprite.Sprite.__init__(self)
        self._position = [map_data_object.x, map_data_object.y]
        self.rect = pygame.Rect(
            map_data_object.x, map_data_object.y,
            map_data_object.width, map_data_object.height)

    @property
    def position(self):
        return list(self._position)

    @position.setter
    def position(self, value):
        self._position = list(value)





class Spritesheet(object):
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert()
        except pygame.error:
            print ('Unable to load spritesheet image: {}').format(filename)
            raise SystemExit
    # Load a specific image from a specific rectangle
    def image_at(self, rectangle, colorkey = None):
        "Loads image from x,y,x+offset,y+offset"
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size).convert()
        image.blit(self.sheet, (0, 0), rect)
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)
        return image
    # Load a whole bunch of images and return them as a list
    def images_at(self, rects, colorkey = None):
        "Loads multiple images, supply a list of coordinates"
        return [self.image_at(rect, colorkey) for rect in rects]
    # Load a whole strip of images
    def load_strip(self, rect, image_count, colorkey = None):
        "Loads a strip of images and returns them as a list"
        tups = [(rect[0]+rect[2]*x, rect[1], rect[2], rect[3])
                for x in range(image_count)]
        return self.images_at(tups, colorkey)

class QuestGame(object):
    """ This class is a basic game.

    It also reads input and moves the Hero around the map.
    Finally, it uses a pyscroll group to render the map and Hero.
    This class will load data, create a pyscroll group, a hero object.
    """
    filename = get_map(MAP_FILENAME)

    def __init__(self):

        # true while running
        self.running = False

        self.debug = False

        # load data from pytmx
        self.tmx_data = load_pygame(self.filename)

        # setup level geometry with simple pygame rects, loaded from pytmx
        self.walls = list()
        self.npcs = list()
        for map_object in self.tmx_data.objects:
            if map_object.type == "wall":
                self.walls.append(Wall(map_object))
            elif map_object.type == "guard":
                print("npc load failed: reimplement npc")
                #self.npcs.append(Npc(map_object))
            elif map_object.type == "hero":
                self.hero = Hero(map_object)

        # create new data source for pyscroll
        map_data = pyscroll.data.TiledMapData(self.tmx_data)





        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(map_data, screen.get_size(), clamp_camera=True, tall_sprites=1)
        self.map_layer.zoom = 2

        # pyscroll supports layered rendering.  our map has 3 'under' layers
        # layers begin with 0, so the layers are 0, 1, and 2.
        # since we want the sprite to be on top of layer 1, we set the default
        # layer for sprites as 2
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)


        # add our hero to the group
        self.group.add(self.hero)
        for npc in self.npcs:
            self.group.add(npc)


    def draw(self, surface):

        # center the map/screen on our Hero
        self.group.center(self.hero.rect.center)
        # draw the map and all sprites


        self.group.draw(surface)


        if(self.debug):
            floor_sensor_rect = self.hero.get_floor_sensor()

            ox, oy = self.map_layer.get_center_offset()
            new_rect = floor_sensor_rect.move(ox * 2, oy * 2)

            pygame.draw.rect(surface, (255,0,0), new_rect)

    def handle_input(self, dt):
        """ Handle pygame input events
        """
        poll = pygame.event.poll

        event = poll()
        while event:
            if event.type == QUIT:
                self.running = False
                break

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                    break
            # this will be handled if the window is resized
            elif event.type == VIDEORESIZE:
                init_screen(event.w, event.h)
                self.map_layer.set_size((event.w, event.h))

            event = poll()

        # using get_pressed is slightly less accurate than testing for events
        # but is much easier to use.
        pressed = pygame.key.get_pressed()


        floor_sensor = self.hero.get_floor_sensor()
        floor_collidelist = floor_sensor.collidelist(self.walls)
        hero_is_airborne = floor_collidelist == -1


        ceiling_sensor = self.hero.get_ceiling_sensor()
        ceiling_collidelist = ceiling_sensor.collidelist(self.walls)
        hero_touches_ceiling = ceiling_collidelist != -1




        if pressed[K_l]:
            print("airborne: {}".format(hero_is_airborne))
            print("hero position: {}, {}".format(self.hero.position[0], self.hero.position[1]))
            print("hero_touches_ceiling: {}".format(hero_touches_ceiling))
            print("hero_is_airborne: {}".format(hero_is_airborne))
        if hero_is_airborne == False:

            #JUMP
            if pressed[K_SPACE]:
                self.hero.set_state(self.hero.STATE_JUMPING)

                # stop the player animation
                if pressed[K_LEFT] and pressed[K_RIGHT] == False:
                    # play the jump left animations
                    self.hero.velocity[0] = -HERO_MOVE_SPEED
                    self.hero.facing = self.hero.FACING_LEFT
                    jumped_direction = 0
                elif pressed[K_RIGHT] and pressed[K_LEFT] == False:
                    self.hero.velocity[0] = HERO_MOVE_SPEED
                    self.hero.facing = self.hero.FACING_RIGHT
                    jumped_direction = 1
                self.hero.velocity[1]= -HERO_JUMP_HEIGHT
            elif pressed[K_LEFT] and pressed[K_RIGHT] == False:
                self.hero.set_state(self.hero.STATE_WALKING)
                self.hero.facing = self.hero.FACING_LEFT
                self.hero.velocity[0] = -HERO_MOVE_SPEED
            elif pressed[K_RIGHT] and pressed[K_LEFT] == False:
                self.hero.set_state(self.hero.STATE_WALKING)
                self.hero.facing = self.hero.FACING_RIGHT
                self.hero.velocity[0] = HERO_MOVE_SPEED
            else:
                self.hero.state = self.hero.STATE_STANDING
                self.hero.velocity[0] = 0


    def update(self, dt):
        """ Tasks that occur over time should be handled here
        """
        self.group.update(dt, self)

    def run(self):
        """ Run the game loop
        """
        clock = pygame.time.Clock()
        self.running = True

        from collections import deque
        times = deque(maxlen=30)

        try:
            while self.running:
                dt = clock.tick(60) / 1000.
                times.append(clock.get_fps())

                self.handle_input(dt)
                self.update(dt)
                self.draw(screen)
                pygame.display.flip()

        except KeyboardInterrupt:
            self.running = False


if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    screen = init_screen(800, 600)
    pygame.display.set_caption('Test Game.')

    try:
        game = QuestGame()
        game.run()
    except:
        pygame.quit()
        raise
