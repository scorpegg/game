import sqlite3
import pygame
import os
import sys
import random
from os import path
import time

pygame.init()
size = width, height = 1600, 800
screen = pygame.display.set_mode(size)
background_rect = screen.get_rect()
font_name = pygame.font.match_font('arial')


def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, (0, 0, 0))
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname).convert()
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


class DataBaseApp:
    def __init__(self, n, s):
        self.con = sqlite3.connect("score_db")
        cur = self.con.cursor()
        print(n, s)
        cur.execute("INSERT INTO history(nickname,score) VALUES ('{0}',{1})".format(n, s))
        self.con.commit()
        self.con.close()


class DataBaseOut:
    def __init__(self):
        self.con = sqlite3.connect("score_db")
        cur = self.con.cursor()
        res = cur.execute("""SELECT nickname FROM history ORDER BY score DESC LIMIT 0,5""")
        with open("top_5.txt", "w") as file:
            for i in list(res):
                file.write(i[0] + '\n')
        file.close()
        self.con.commit()
        self.con.close()


class Hero(pygame.sprite.Sprite):
    score = 0
    image = load_image("Hero.png", -1)

    def __init__(self):
        super().__init__(all_sprites)
        self.rect = self.image.get_rect()
        self.rect.y = 500
        self.image = Hero.image
        hero_squad.add(self)
        self.score = 0

    def update(self):
        if to_left:
            self.rect.x -= 25
        elif to_right:
            self.rect.x += 25
        elif to_down:
            self.rect.y += 25
        elif to_up:
            self.rect.y -= 25


class Bomb(pygame.sprite.Sprite):
    image = load_image("bomb.png", -1)

    def __init__(self, air_x):
        super().__init__(all_sprites)
        self.image = Bomb.image
        self.rect = self.image.get_rect()
        self.rect.x = air_x + random.choice(range(-200, 10))
        self.rect.y = random.choice(range(100))

    def update(self):
        if self.rect.y < 2000:
            self.rect = self.rect.move(0, 10)
        elif self.rect.y > 2000:
            self.kill()
        for sprite in hero_squad:
            if pygame.sprite.collide_mask(self, sprite):
                self.kill()
                sprite.kill()
                DataBaseApp(nick, Hero.score)
                end_screen_lose()


class AnimatedSprite(pygame.sprite.Sprite):
    img = load_image('animated_helicopter.png')

    def __init__(self, img, columns, rows):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(img, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(0, 0)

    def cut_sheet(self, img, columns, rows):
        self.rect = pygame.Rect(0, 0, img.get_width() // columns,
                                img.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(img.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(10, 0)
        if self.rect.bottomleft[0] % 200 == 0 and self.rect.bottomleft[0] < 1600:
            Friend(self.rect.bottomleft[0])
            if time < 400 and random.choice(range(10)) in range(2):
                Bomb(self.rect.bottomleft[0])
            if 800 > time > 600 and random.choice(range(10)) in range(4):
                Bomb(self.rect.bottomleft[0])
            if time > 800 and random.choice(range(10)) in range(7):
                Bomb(self.rect.bottomleft[0])

        if self.rect.center[0] > 2000:
            self.rect.x = 0
            self.rect.y = 0


class Friend(pygame.sprite.Sprite):
    image = load_image("friend.png", -1)

    def __init__(self, air_x):
        super().__init__(all_sprites)
        self.image = Friend.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = air_x + random.choice(range(-200, 10))
        self.rect.y = random.choice(range(100))

    def update(self):
        if self.rect.y < 2000:
            self.rect = self.rect.move(0, 10)
        elif self.rect.y > 2000:
            self.kill()
        for sprite in hero_squad:
            if pygame.sprite.collide_mask(self, sprite):
                self.kill()
                Hero.score += 1
        draw_text(screen, 'счёт:' + str(Hero.score), 30, 880, 10)


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    with open(os.path.join('data', 'intro_text'), encoding="UTF-8") as a:
        intro_text = list(map(str.strip, a.readlines()))

    fon = pygame.transform.scale(load_image('fon.jpg'), size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 100
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height + 50
        screen.blit(string_rendered, intro_rect)
    input_box = pygame.Rect(10, 400, 140, 32)
    color_inactive = pygame.Color('#ff00ff')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        nick = text
                        text = ''
                        done = True

                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        txt_surface = font.render(text, True, color)
        width = max(200, txt_surface.get_width() + 10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)
        pygame.display.flip()
        clock.tick(fps)
    return nick


def end_screen_win():
    with open(os.path.join('data', 'win_text'), encoding="UTF-8") as a:
        intro_text = list(map(str.strip, a.readlines()))
    fon = pygame.transform.scale(load_image('win_fon.jpg'), size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 100
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 100
        intro_rect.top = text_coord
        intro_rect.x = 400
        text_coord += intro_rect.height + 5
        screen.blit(string_rendered, intro_rect)
        DataBaseOut()
    with open('top_5.txt', encoding="UTF-8") as b:
        t_5 = list(map(str.strip, b.readlines()))
        for line in t_5:
            string_rendered = font.render(line, 1, pygame.Color('black'))
            top_5_rect = string_rendered.get_rect()
            text_coord += 10
            top_5_rect.top = text_coord
            top_5_rect.x = 100
            text_coord += top_5_rect.height + 5
            screen.blit(string_rendered, top_5_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
        pygame.display.flip()
        clock.tick(fps)


def end_screen_lose():
    with open(os.path.join('data', 'lose_text'), encoding="UTF-8") as a:
        intro_text = list(map(str.strip, a.readlines()))
    fon = pygame.transform.scale(load_image('lose_fon.jpg'), size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = 100
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('red'))
        intro_rect = string_rendered.get_rect()
        text_coord += 100
        intro_rect.top = text_coord
        intro_rect.x = 400
        text_coord += intro_rect.height + 5
        screen.blit(string_rendered, intro_rect)
        DataBaseOut()
    with open('top_5.txt', encoding="UTF-8") as b:
        t_5 = list(map(str.strip, b.readlines()))
        for line in t_5:
            string_rendered = font.render(line, 1, pygame.Color('red'))
            top_5_rect = string_rendered.get_rect()
            text_coord += 10
            top_5_rect.top = text_coord
            top_5_rect.x = 400
            text_coord += top_5_rect.height + 5
            screen.blit(string_rendered, top_5_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
        pygame.display.flip()
        clock.tick(fps)


all_sprites = pygame.sprite.Group()
running = True
clock = pygame.time.Clock()
fps = 30
score = 0
to_left = False
to_right = False
to_down = False
to_up = False
speed = 20
nick = start_screen()
AnimatedSprite(load_image("animated_helicopter.png", -1), 1, 4)
hero_squad = pygame.sprite.Group()
Hero()
time = 0
top_5 = []
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                to_left = True
            if event.key == pygame.K_RIGHT:
                to_right = True
            if event.key == pygame.K_DOWN:
                to_down = True
            if event.key == pygame.K_UP:
                to_up = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                to_left = False
            if event.key == pygame.K_RIGHT:
                to_right = False
            if event.key == pygame.K_DOWN:
                to_down = False
            if event.key == pygame.K_UP:
                to_up = False
        if Hero.score >= 10:
            DataBaseApp(nick, Hero.score)
            end_screen_win()

    time += 1
    clock.tick(fps)
    screen.fill((0, 191, 255))
    all_sprites.draw(screen)
    all_sprites.update()
    pygame.display.flip()
