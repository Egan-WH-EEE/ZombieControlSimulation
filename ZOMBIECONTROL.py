# python ZOMBIECONTROL.py
# Imports libraries
import pygame
import math
from math import sin, cos, pi
import copy
import random

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

font = pygame.font.Font(None, 36)

manual_button = pygame.Rect(10, 10, 120, 40)
mpc_button = pygame.Rect(140, 10, 120, 40)

mode = "manual"

# Player initial position and speed
player_x, player_y = 400, 300
player_speed = 4

# Zombie initial position and speed
#zombies = [ [100, 100], [700, 100], [100, 600], [700, 500], ]
zombies = [
    [100, 100]
    ]
zombie_speed = 3.5
spawn_timer = 0

# Used for frame control
flash_timer = 0

# MPC constants
score = [0]*32
Wz = 200
Wc = 0.2


def zombie_distance(z):
    dx = player_x - z[0]
    dy = player_y - z[1]
    return dx*dx + dy*dy


def argmax(lst):
    return max(range(len(lst)), key=lambda i: lst[i])

running = True
prev_direction = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if manual_button.collidepoint(event.pos):
                mode = "manual"
            if mpc_button.collidepoint(event.pos):
                mode = "mpc"

    if mode == "manual":
    # Manual player control
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: player_y -= player_speed
        if keys[pygame.K_s]: player_y += player_speed
        if keys[pygame.K_a]: player_x -= player_speed
        if keys[pygame.K_d]: player_x += player_speed

    elif mode == "mpc":
    # MPC player control
        for i in range(32): # 32 directions around full circle, pi/16 step
            score[i] = 0
            dummy_player_x = player_x
            dummy_player_y = player_y
            dummy_zombies = copy.deepcopy(zombies)

            for t in range(6):
                dummy_player_x += player_speed * sin(i * pi / 16)
                dummy_player_y -= player_speed * cos(i * pi / 16)
                # Keep player inside screen bounds
                dummy_player_x = max(10, min(790, dummy_player_x))
                dummy_player_y = max(10, min(590, dummy_player_y))


                for z in dummy_zombies:
                    dx = dummy_player_x - z[0]
                    dy = dummy_player_y - z[1]
                    dist = (dx**2 + dy**2) ** 0.5
                    if dist > 0:
                        z[0] += zombie_speed * dx / dist
                        z[1] += zombie_speed * dy / dist

            min_z_dist = min(
                ((dummy_player_x - z[0])**2 + (dummy_player_y - z[1])**2) ** 0.5
                for z in dummy_zombies
            )

            dist_left   = dummy_player_x - 10
            dist_right  = 790 - dummy_player_x
            dist_top    = dummy_player_y - 10
            dist_bottom = 590 - dummy_player_y
            open_space  = min(dist_left, dist_right, dist_top, dist_bottom)

            angular_diff = min(abs(i - prev_direction), 32 - abs(i - prev_direction))
            bias = 0.0005 * (16 - angular_diff)  # closer to prev direction = bigger bonus

            zombie_penalty = Wz / (min_z_dist + 1)**2
            wall_penalty = Wc / (open_space + 1)**2
            score[i] = -zombie_penalty - wall_penalty + bias

        best_direction = argmax(score)
        prev_direction = best_direction
        angle = best_direction * (pi / 16)
        dx = sin(angle)
        dy = -cos(angle)
        player_x += player_speed * dx
        player_y += player_speed * dy

    # Calculate how far each zombie is from player
    for z in zombies:
        dx = player_x - z[0]
        dy = player_y - z[1]
        dist = (dx**2 + dy**2) ** 0.5
        if dist > 0:
            z[0] += zombie_speed * dx / dist
            z[1] += zombie_speed * dy / dist

    # Prevent zombie overlap with each other
    for i in range(len(zombies)):
        for j in range(i+1, len(zombies)):
            dx = zombies[i][0] - zombies[j][0]
            dy = zombies[i][1] - zombies[j][1]
            dist = (dx**2 + dy**2) ** 0.5
            if dist < 20 and dist > 0:
                overlap = 20 - dist
                zombies[i][0] += dx/dist * overlap/2
                zombies[i][1] += dy/dist * overlap/2
                zombies[j][0] -= dx/dist * overlap/2
                zombies[j][1] -= dy/dist * overlap/2

    # Detect when zombie touches player
    for z in zombies:
    # get dx, dy from player to zombie
        dx = player_x - z[0]
        dy = player_y - z[1]
        dist = (dx**2 + dy**2) ** 0.5
    # check if dist < minimum
        if 0 < dist < 20:
    # if so, flash red and reset initial conditions
            flash_timer = 10
            zombies = [[100, 100]]
            player_x, player_y = 400, 300

    # Keep player inside screen bounds
    player_x = max(10, min(790, player_x))
    player_y = max(10, min(590, player_y))

    spawn_timer += clock.get_time()  # milliseconds since last frame
    if spawn_timer >= 2000:  # 2 seconds
        spawn_timer = 0

        # Spawn 1 new zombie at random location
        zombies.append([400, 300])

    # Draw all positions and background
    screen.fill((0, 0, 0))
    if flash_timer > 0:
        pygame.draw.circle(screen, (255, 0, 0), (int(player_x), int(player_y)), 10)
        flash_timer -= 1
        pygame.time.delay(50)
    else:
        pygame.draw.circle(screen, (0, 100, 255), (int(player_x), int(player_y)), 10)
    for z in zombies:
        pygame.draw.circle(screen, (200, 100, 0), (int(z[0]), int(z[1])), 10)
    manual_color = (0, 200, 0) if mode == "manual" else (100, 100, 100)
    mpc_color = (0, 200, 0) if mode == "mpc" else (100, 100, 100)

    pygame.draw.rect(screen, manual_color, manual_button)
    pygame.draw.rect(screen, mpc_color, mpc_button)

    zcount_text = font.render(f"Zombies: {len(zombies)}", True, (255, 255, 255))
    screen.blit(zcount_text, (650, 18))

    manual_text = font.render("Manual", True, (255, 255, 255))
    mpc_text = font.render("MPC", True, (255, 255, 255))

    screen.blit(manual_text, (20, 18))
    screen.blit(mpc_text, (150, 18))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
