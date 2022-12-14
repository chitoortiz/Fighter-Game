import pygame
from timer import Timer


class Fighter:
    def __init__(self, player, x, y, flip, data, sprite_sheet, animation_steps, attack_fx):
        self.player = player
        self.size = data[0]
        self.image_scale = data[1]
        self.offset = data[2]
        self.flip = flip
        self.animation_list = self.load_images(sprite_sheet, animation_steps)
        self.action = 0  # 0: idle, 1: run, 2: jump, 3: attack1, 4: attack2, 5: hit, 6: death
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.update_time = pygame.time.get_ticks()
        self.rect = pygame.Rect((x, y, 80, 180))
        self.vel_y = 0
        self.running = False
        self.jump = False
        self.attacking = False
        self.attack_type = 0
        self.attack_cooldown = 0
        self.attack_time_offset = 0
        self.attack_fx = attack_fx
        self.hit = False
        self.health = 100
        self.alive = True

        self.target = None
        if self.player == 1:
            self.attack1_offset = Timer(500, self.attack_hitbox)
            self.attack2_offset = Timer(350, self.attack_hitbox)
        if self.player == 2:
            self.attack1_offset = Timer(400, self.attack_hitbox)
            self.attack2_offset = Timer(500, self.attack_hitbox)

    def load_images(self, sprite_sheet, animation_steps):
        # extract images from sprite sheet
        animation_list = []
        for y, animation in enumerate(animation_steps):
            temp_img_list = []
            for x in range(animation):
                temp_img = sprite_sheet.subsurface(x * self.size, y * self.size, self.size, self.size)
                temp_img_list.append(
                    pygame.transform.scale(temp_img, (self.size * self.image_scale, self.size * self.image_scale)))
            animation_list.append(temp_img_list)

        return animation_list

    def move(self, screen_width, screen_height, surf, target, round_over):
        SPEED = 10
        GRAVITY = 2
        dx = 0
        dy = 0
        self.running = False
        self.attack_type = 0

        # get key presses
        key = pygame.key.get_pressed()

        # can only perform actions if not attacking
        if not self.attacking and self.alive and not round_over:
            # check player 1 controls
            if self.player == 1:
                # movement
                if key[pygame.K_a]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_d]:
                    dx = SPEED
                    self.running = True
                # jump
                if key[pygame.K_w] and not self.jump:
                    self.vel_y = -30
                    self.jump = True
                # attack
                if key[pygame.K_r]:
                    self.attack1(target)
                    self.attack_type = 1
                if key[pygame.K_t]:
                    self.attack2(target)
                    self.attack_type = 2
            # check player 2 controls
            if self.player == 2:
                # movement
                if key[pygame.K_LEFT]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_RIGHT]:
                    dx = SPEED
                    self.running = True
                # jump
                if key[pygame.K_UP] and not self.jump:
                    self.vel_y = -30
                    self.jump = True
                # attack
                if key[pygame.K_KP1]:
                    self.attack1(target)
                    self.attack_type = 1
                if key[pygame.K_KP2]:
                    self.attack2(target)
                    self.attack_type = 2

        # apply gravity
        self.vel_y += GRAVITY
        dy += self.vel_y

        # ensure player stays on screen
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > screen_width:
            dx = screen_width - self.rect.right
        if self.rect.bottom + dy > screen_height - 110:
            self.vel_y = 0
            self.jump = False
            dy = screen_height - 110 - self.rect.bottom

        # ensure player face each other
        if target.rect.centerx > self.rect.centerx:
            self.flip = False
        else:
            self.flip = True

        # apply attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # apply attack time offset cooldown
        self.attack1_offset.update()
        self.attack2_offset.update()

        # update player position
        self.rect.x += dx
        self.rect.y += dy

    # handle animation updates
    def update(self):
        # check what action the player is performing
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.update_action(6)  # 6:death
        elif self.hit:
            self.update_action(5)  # 5:hit
        elif self.attacking:
            if self.attack_type == 1:
                self.update_action(3)  # 3:attack1
            elif self.attack_type == 2:
                self.update_action(4)  # 4:attack2
        elif self.jump:
            self.update_action(2)  # 2:jump
        elif self.running:
            self.update_action(1)  # 1:run
        else:
            self.update_action(0)  # 0:idle

        animation_cooldown = 100
        # update image
        self.image = self.animation_list[self.action][self.frame_index]
        # check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            if self.action == 3 or self.action == 4:
                self.attack_time_offset = 10
            self.update_time = pygame.time.get_ticks()
        # check if animation has finished
        if self.frame_index >= len(self.animation_list[self.action]):
            # if the player is dead the end the animation
            if not self.alive:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
                # check if an attack was executed
                if self.action == 3 or self.action == 4:
                    self.attacking = False
                    self.attack_cooldown = 20
                # check if damage was taken
                if self.action == 5:
                    self.hit = False
                    # if the player was in the middle of an attack, then attack is stopped
                    self.attacking = False
                    self.attack_cooldown = 20

    def attack1(self, target):
        if self.attack_cooldown == 0:
            self.attacking = True
            self.target = target
            self.attack1_offset.activate()

    def attack2(self, target):
        if self.attack_cooldown == 0:
            self.attacking = True
            self.target = target
            self.attack2_offset.activate()

    def attack_hitbox(self):
        self.attack_fx.play()
        attacking_rect = pygame.Rect(self.rect.centerx - (2 * self.rect.width * self.flip), self.rect.y,
                                     2 * self.rect.width, self.rect.height)
        if attacking_rect.colliderect(self.target.rect):
            self.target.health -= 10
            self.target.hit = True

    def update_action(self, new_action):
        # check if the new action is different from the previous one
        if new_action != self.action:
            self.action = new_action
            # update animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self, surf):
        img = pygame.transform.flip(self.image, self.flip, False)
        surf.blit(img, (
        self.rect.x - (self.offset[0] * self.image_scale), self.rect.y - (self.offset[1] * self.image_scale)))
