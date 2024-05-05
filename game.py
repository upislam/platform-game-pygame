import pygame
import random
import math
import os

pygame.init()

pygame.display.set_caption("A Platformer game")  # Set the title of the window

# Global variables
WIDTH, HEIGHT = 1200, 800
FPS = 60
PLAYER_VEL = 5

WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))   # Set the window size

# Blitting is a term used in computer graphics, particularly in the context of 2D graphics libraries like Pygame.
# It refers to the process of copying pixels from one image (or surface) onto another.


def flip_image(image, direction):
    if direction == 'x':
        return pygame.transform.flip(image, True, False)
    elif direction == 'y':
        return pygame.transform.flip(image, False, True)
    elif direction == 'xy':
        return pygame.transform.flip(image, True, True)


def flip_sprites(sprite_list, direction):
    flipped_sprites = []
    for sprite in sprite_list:
        flipped_sprites.append(flip_image(sprite, direction))
    return flipped_sprites


def load_sprite_sheets(dir1, dir2, width, height, is_both_way):
    path = os.path.join("assets", dir1, dir2)
    sprite_sheet_paths = [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]

    all_sprites = {}

    for sprite_sheet_path in sprite_sheet_paths:
        # Convert the image to the same pixel format as the display for faster blitting
        sprite_sheet = pygame.image.load(os.path.join(path, sprite_sheet_path)).convert_alpha()

        sprites = []
        for i in range(0, sprite_sheet.get_width(), width):
            # pygame.SRCALPHA: This flag indicates that the surface will have an alpha channel, allowing for transparency.
            # This argument specifies the number of bits to use for color depth.
            # In this case, 32 bits per pixel (bpp) are used, which typically means 8 bits each for red, green, blue, and alpha channels.
            # This is a common choice for surfaces with alpha transparency.

            # Create a transparent surface where main sprite will be blitted(copied) from the sprite sheet
            sprite = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i, 0, width, height)
            sprite.blit(sprite_sheet, (0, 0), rect)
            sprite = pygame.transform.scale2x(sprite)
            sprites.append(sprite)

        if is_both_way:
            all_sprites[sprite_sheet_path.replace('.png', "") + '_left'] = flip_sprites(sprites, 'x')
            all_sprites[sprite_sheet_path.replace('.png', "") + '_right'] = sprites
        else:
            all_sprites[sprite_sheet_path.replace('.png', "")] = sprites
    return all_sprites


class Player(pygame.sprite.Sprite):
    GRAVITY = 1

    PLAYER_SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.direction = "left"
        self.animation_count = 0  # used to keep track of animated indices of the sprite
        self.sprite = self.PLAYER_SPRITES['idle_' + self.direction][0]
        self.mask = pygame.mask.from_surface(self.sprite)
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.fall_count = 0
        self.jump_count = 0
        self.is_hit = False
        self.hit_count = 0

    def move_left(self, x_vel):
        self.x_vel = -x_vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, x_vel):
        self.x_vel = x_vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def move(self, fps, objects):
        # x movement
        self.rect.x += self.x_vel
        self.rect.y += self.y_vel

        # y movement with gravity
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)  # time * gravity; used min with 1 cause initial fall_count is less

        self.fall_count += 1
        self.animation_count += 1

        if self.is_hit:
            self.hit_count += 1
        if self.hit_count >= fps*2:
            self.is_hit = False
            self.hit_count = 0

        # self.get_vertical_collision_objects(objects)  ## already calling in key_input_handler
        self.update_sprite()

    def update_sprite(self):
        if self.animation_count // self.ANIMATION_DELAY >= len(self.PLAYER_SPRITES):
            self.animation_count = 0
        if self.is_hit:
            sprites = self.PLAYER_SPRITES['hit_' + self.direction]
        elif self.y_vel > self.GRAVITY*2:  # did not do > 0 greater than 0 also applies when player is standing
            sprites = self.PLAYER_SPRITES['fall_' + self.direction]
        elif self.y_vel < 0:
            sprites = self.PLAYER_SPRITES['jump_' + self.direction]
        elif self.x_vel == 0:
            sprites = self.PLAYER_SPRITES['idle_' + self.direction]
        else:
            sprites = self.PLAYER_SPRITES['run_' + self.direction]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.rect_mask_adjustment()

    def hit(self):
        self.is_hit = True
        self.hit_count = 0

    def rect_mask_adjustment(self):
        #  it adjusts the width and height of the rect to the sprite's width and height
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        # it creates a bitmask (a binary image where each pixel indicates whether the corresponding pixel in the
        # original image is transparent or opaque) from the sprite for pixel perfect collision
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, window, offset_x):
        # pygame.draw.rect(window, self.COLOR, self.rect)
        window.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

    def get_vertical_collision_objects(self, objects):
        collision_objects = []
        for obj in objects:
            if pygame.sprite.collide_mask(self, obj):
                if self.y_vel > 0:
                    self.rect.bottom = obj.rect.top
                    self.y_vel = 0
                    self.fall_count = 0
                    self.jump_count = 0
                    # self.animation_count = 0  # the player keeps getting collided with the platform, so animation_count should not be reset

                elif self.y_vel < 0:
                    self.rect.top = obj.rect.bottom
                    self.y_vel *= -1  # changing the direction of falling of the player
                    self.fall_count = 0
                    # self.jump_count = 0  # this is tricky, if we do this, then player can jump again in the air
                    # self.animation_count = 0  # the player keeps getting collided with the platform, so animation_count should not be reset
                collision_objects.append(obj)
        return collision_objects

    def jump(self):
        self.y_vel = - self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:  # if player is jumping for the first time
            self.fall_count = 0

    def check_horizontal_collision_objects(self, objects, dx):
        # it works with prediction
        self.rect.x += dx
        # self.rect_mask_adjustment()  # this is not needed as we are not changing the sprite

        collision_happened = False
        collision_objects = []
        for obj in objects:
            if pygame.sprite.collide_mask(self, obj):
                collision_happened = True
                collision_objects.append(obj)

        self.rect.x += -dx
        # self.rect_mask_adjustment() # this is not needed as we are not changing the sprite
        return collision_happened, collision_objects


def get_block(size):
    path = os.path.join("assets", "Terrain", "Terrain.png")
    sprite = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(sprite, (0, 0), rect)
    return pygame.transform.scale2x(surface)


def get_fire_sprites(size):
    path = os.path.join("assets", "Traps", "Fire")
    sprite = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(sprite, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.sprite = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, window, offset_x):
        window.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size, "block")
        self.sprite = get_block(size)
        self.mask = pygame.mask.from_surface(self.sprite)
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))


class Fire(Object):
    FIRE_SPRITES = load_sprite_sheets("Traps", "Fire", 16, 32, False)
    ANIMATION_DELAY = 10

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.sprite = self.FIRE_SPRITES['off'][0]
        self.mask = pygame.mask.from_surface(self.sprite)
        self.animation_count = 0
        self.animation_name = "off"

    def rect_mask_adjustment(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def hit(self):
        self.animation_name = "hit"

    def move(self):
        if self.animation_count // self.ANIMATION_DELAY >= len(self.FIRE_SPRITES):
            self.animation_count = 0
        sprites = self.FIRE_SPRITES[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.rect_mask_adjustment()
        self.animation_count += 1


def key_input_handler(player, objects):  # this can handle keys continuously pressed
    keys = pygame.key.get_pressed()

    left_collision, left_collision_objects = player.check_horizontal_collision_objects(objects, -PLAYER_VEL*2)  # multi by 2 cause pixels are readjusted. can vary the detection
    right_collision, right_collision_objects = player.check_horizontal_collision_objects(objects, PLAYER_VEL*2)  # multi by 2 cause pixels are readjusted. can vary the detection

    player.x_vel = 0
    if keys[pygame.K_LEFT] and not left_collision:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not right_collision:
        player.move_right(PLAYER_VEL)

    collision_objects = player.get_vertical_collision_objects(objects)
    collision_objects.extend(left_collision_objects)
    collision_objects.extend(right_collision_objects)

    for obj in collision_objects:
        if obj.name == "fire":
            player.hit()


def get_background_pixels(bg_name):
    background = pygame.image.load(os.path.join("assets", "Background", bg_name))
    _, _, width, height = background.get_rect()
    pixels = []

    i = 0
    j = 0
    while i < WIDTH:
        while j < HEIGHT:
            pixels.append((i, j))
            j += width
        i += width
        j = 0
    return pixels, background


def draw(window, pixels, background, player, objects, offset_x):
    for pixel in pixels:
        window.blit(background, pixel)  # does not need offset cause its pixel position not changes

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)
    pygame.display.update()


def main(window):
    clock = pygame.time.Clock()
    is_running = True
    block_size = 48
    double_block_size = block_size * 2  # as we are 2x scaling the block
    scrolling_effect_left_boundary_x = 200
    scrolling_effect_right_boundary_x = WIDTH - scrolling_effect_left_boundary_x

    scrolling_effect_offset_x = 0

    background_pixels, background = get_background_pixels("Blue.png")
    player = Player(100, 100, 50, 50)
    platform = [Block(i, HEIGHT - double_block_size, block_size) for i in range(-WIDTH, 2*WIDTH, double_block_size)]
    all_objects = [*platform]  # just expanding the platform list
    all_objects.append(Block(0, HEIGHT - double_block_size * 2, block_size))
    all_objects.append(Block(double_block_size * 3, HEIGHT - double_block_size * 4, block_size))
    fire = Fire(300, HEIGHT - double_block_size - 32*2, 16, 32)
    fire.on()
    all_objects.append(fire)
    while is_running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:  # we will only allow consecutive 2 jumps
                    player.jump()

        actual_left_x = player.rect.left - scrolling_effect_offset_x
        actual_right_x = player.rect.right - scrolling_effect_offset_x
        if (actual_left_x < scrolling_effect_left_boundary_x and player.x_vel < 0) or (actual_right_x > scrolling_effect_right_boundary_x and player.x_vel > 0):
            scrolling_effect_offset_x += player.x_vel

        fire.move()
        player.move(FPS, all_objects)
        key_input_handler(player, all_objects)
        draw(window, background_pixels, background, player, all_objects, scrolling_effect_offset_x)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(WINDOW)
