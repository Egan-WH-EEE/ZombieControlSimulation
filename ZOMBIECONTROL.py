# python /Users/eg4nhrr/Documents/ZOMBIECONTROL.py
# Imports libraries
import pygame
import math
from math import sin, cos, pi
import copy
import time
import random

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

font = pygame.font.Font(None, 36)

manual_button = pygame.Rect(10, 10, 120, 40)
pid_button = pygame.Rect(140, 10, 120, 40)
mpc_button = pygame.Rect(270, 10, 120, 40)

mode = "manual"

# Player initial position and speed
player_x, player_y = 400, 300
player_speed = 4

# Zombie initial position and speed
#zombies = [ [100, 100], [700, 100], [100, 600], [700, 500], ]
zombies = [
    [100, 100]
    ]
zombie_speed = 1
spawn_timer = 0


# Used for frame control
flash_timer = 0

# PID constants
Kp = 100
Ki = 100
Kd = 100
vx = 0
vy = 0
integral_x = 0
integral_y = 0
prev_error_x = 0
prev_error_y = 0

# MPC constants
score = [0]*32
Wz = 2
Wc = 0.05


def zombie_distance(z):
    dx = player_x - z[0]
    dy = player_y - z[1]
    return dx*dx + dy*dy


def argmax(lst):
    return max(range(len(lst)), key=lambda i: lst[i])

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if manual_button.collidepoint(event.pos):
                mode = "manual"
            if pid_button.collidepoint(event.pos):
                mode = "pid"
            if mpc_button.collidepoint(event.pos):
                mode = "mpc"

    if mode == "manual":
    # Manual player control
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: player_y -= player_speed
        if keys[pygame.K_s]: player_y += player_speed
        if keys[pygame.K_a]: player_x -= player_speed
        if keys[pygame.K_d]: player_x += player_speed

    elif mode == "pid":
    # PID player control
        nearest_zombie = min(zombies, key=zombie_distance)
        zx, zy = nearest_zombie
        error_x = player_x - zx
        error_y = player_y - zy
        e = [error_x, error_y]
        integral_x += error_x
        integral_y += error_y
        P_x = Kp * error_x
        P_y = Kp * error_y
        I_x = Ki * integral_x
        I_y = Ki * integral_y
        D_x = Kd * (error_x - prev_error_x)
        D_y = Kd * (error_y - prev_error_y)
        vx += (P_x + I_x + D_x)
        vy += (P_y + I_y + D_y)
        vx *= 0.5
        vy *= 0.5

        # Limit max speed
        max_speed = 3
        speed = math.hypot(vx, vy)
        if speed > max_speed:
            vx = vx / speed * max_speed
            vy = vy / speed * max_speed
            
        player_x += vx
        player_y += vy
        prev_error_x = error_x
        prev_error_y = error_y
    elif mode == "mpc":
    # MPC player control
        for i in range(32): # 8 directions - Up, Right, Down, Left, UR, BR, BL, UL
            score[i] = 0
            valid = True
            dummy_player_x = player_x
            dummy_player_y = player_y
            dummy_zombies = copy.deepcopy(zombies)
            
            for t in range(6):
                dummy_player_x += player_speed * sin(i * pi / 16)
                dummy_player_y -= player_speed * cos(i * pi / 16)

                if not (10 < dummy_player_x < 790 and 10 < dummy_player_y < 590):
                    valid = False
                    break
            
                for z in dummy_zombies:
                    dx = dummy_player_x - z[0]
                    dy = dummy_player_y - z[1]
                    dist = (dx**2 + dy**2) ** 0.5
                    if dist > 0:
                        z[0] += zombie_speed * dx / dist
                        z[1] += zombie_speed * dy / dist

            if not valid:
                score[i] = -999999
                continue

            min_z_dist = min(
            ((dummy_player_x - z[0])**2 + (dummy_player_y - z[1])**2) ** 0.5
            for z in dummy_zombies
            )

            dist_left   = dummy_player_x - 10
            dist_right  = 790 - dummy_player_x
            dist_top    = dummy_player_y - 10
            dist_bottom = 590 - dummy_player_y
            open_space  = min(dist_left, dist_right, dist_top, dist_bottom)

            score[i] = min_z_dist + 0.5 * open_space
            
        best_direction = argmax(score)
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
        if 0<dist<20:
    # if so, flash red and reset initial conditions
            flash_timer = 10
            zombies = [[100,100]]
            player_x, player_y = 400, 300



    # Keep player inside screen bounds
    player_x = max(10, min(790, player_x))
    player_y = max(10, min(590, player_y))

    spawn_timer += clock.get_time()  # milliseconds since last frame
    if spawn_timer >= 4000:  # 10 seconds
        spawn_timer = 0

        # Spawn 1 new zombie at random location
        zombies.append([random.randint(10,790),random.randint(10,590)])
    
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
    pygame.draw.rect(screen, (100,100,100), manual_button)
    pygame.draw.rect(screen, (100,100,100), pid_button)
    pygame.draw.rect(screen, (100,100,100), mpc_button)

    zcount_text = font.render(f"Zombies: {len(zombies)}", True, (255,255,255))
    screen.blit(zcount_text, (650, 18))

    manual_text = font.render("Manual", True, (255,255,255))
    pid_text = font.render("PID", True, (255,255,255))
    mpc_text = font.render("MPC", True, (255,255,255))

    screen.blit(manual_text, (20, 18))
    screen.blit(pid_text, (170, 18))
    screen.blit(mpc_text, (320, 18))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
