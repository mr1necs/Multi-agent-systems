import sys, pygame
import numpy as np
import math
import time

sz = (1500, 1000)


def dist(p1, p2):
    return np.linalg.norm(np.subtract(p1, p2))


def euclid(p1, p2):
    return np.sqrt(np.sum((np.array(p1) - np.array(p2)) ** 2))


def rot(v, ang):
    s, c = np.sin(ang), np.cos(ang)
    return [v[0] * c - v[1] * s, v[0] * s + v[1] * c]


def rotArr(vv, ang):
    return [rot(v, ang) for v in vv]


pygame.font.init()
font = pygame.font.SysFont('segoeuisemibold', 15)


def drawText(screen, s, x, y):
    surf = font.render(s, True, (0, 0, 0))
    screen.blit(surf, (x, y))


def drawRotRect(screen, color, pc, w, h, ang):
    pts = [
        [-w / 2, -h / 2],
        [w / 2, -h / 2],
        [w / 2, h / 2],
        [-w / 2, h / 2],
    ]

    pts = rotArr(pts, ang)
    pts = np.add(pts, pc)
    pygame.draw.polygon(screen, color, pts, 2)


class Bullet:
    def __init__(self, x, y, ang, t):
        self.x = x
        self.y = y
        self.ang = ang
        self.vx = 200
        self.L = 10
        self.exploded = False
        self.fromTank = t

    def getPos(self):
        return [self.x, self.y]

    def draw(self, screen):
        p0 = self.getPos()
        p1 = [-self.L / 2, 0]
        p1 = rot(p1, self.ang)
        p2 = [self.L / 2, 0]
        p2 = rot(p2, self.ang)

        pygame.draw.line(screen, (0, 0, 0), np.add(p0, p1), np.add(p0, p2), 3)

    def sim(self, dt):
        vec = [self.vx, 0]
        vec = rot(vec, self.ang)
        self.x += vec[0] * dt
        self.y += vec[1] * dt


class Tank:
    def __init__(self, id, x, y, ang):
        self.id = id
        self.x = x
        self.y = y
        self.ang = ang
        self.angGun = ang
        self.L = 70
        self.W = 45
        self.vx = 0
        self.vy = 0
        self.va = 0
        self.vaGun = 0
        self.health = 100
        self.color = (0, 0, 0)
        self.shootAvailable = True
        self.gunReady = False
        self.blocked = False
        self.oldPos = [x, y]

    def fire(self):
        r = self.W / 2.3
        LGun = self.L / 2
        p2 = rot([r + LGun, 0], self.angGun)
        p2 = np.add(self.getPos(), p2)
        b = Bullet(*p2, self.angGun, self)

        return b

    def getPos(self):
        return [self.x, self.y]

    def draw(self, screen):
        pts = [
            [self.L / 2, self.W / 2],
            [self.L / 2, -self.W / 2],
            [-self.L / 2, -self.W / 2],
            [-self.L / 2, self.W / 2]
        ]

        pts = rotArr(pts, self.ang)
        pts = np.add(pts, self.getPos())

        pygame.draw.polygon(screen, self.color, pts, 2)

        r = self.W / 2.3

        pygame.draw.circle(screen, self.color, self.getPos(), r, 2)

        LGun = self.L / 2
        p0 = self.getPos()
        p1 = rot([r, 0], self.angGun)
        p2 = rot([r + LGun, 0], self.angGun)

        pygame.draw.line(screen, self.color, np.add(p0, p1), np.add(p0, p2), 3)
        drawText(screen, f"{self.id} ({self.health})", self.x, self.y - self.L / 2 - 12)

    def sim(self, dt):
        vec = [self.vx, self.vy]
        vec = rot(vec, self.ang)
        self.oldPos = [self.x, self.y]
        self.x += vec[0] * dt
        self.y += vec[1] * dt
        self.ang = (self.ang + self.va * dt) % (2 * np.pi)
        self.angGun = (self.angGun + self.vaGun * dt) % (2 * np.pi)


def find_enemy(t, tanks):
    nearest_enemy = tanks[np.argmin(
        [euclid(t.getPos(), enemy.getPos()) if enemy.id // 1000 != t.id // 1000 and enemy.health > 0 else 10 ** 10 for
         enemy in tanks])]

    return nearest_enemy if np.min(
        [euclid(t.getPos(), enemy.getPos()) if enemy.id // 1000 != t.id // 1000 and enemy.health > 0 else 10 ** 10 for
         enemy in tanks]) != 10 ** 10 else None


def find_block(t, tanks):
    return tanks[np.argmin([euclid(t.getPos(),
                                   block.getPos()) if block.id != t.id and block.id // 1000 == t.id // 1000 or block.health <= 0 else 10 ** 10
                            for block in tanks])]


def find_ang(ang, pos, target_pos):
    direction_vector = np.array(target_pos) - np.array(pos)
    direction_vector_normalized = direction_vector / np.linalg.norm(direction_vector)
    target_angle_rad = np.arctan2(direction_vector_normalized[1], direction_vector_normalized[0])
    turn_angle = target_angle_rad - ang

    return (np.degrees(turn_angle) + 180) % 360 - 180


def blocked(t, ang):
    t.va = (0 - ang / abs(ang)) * 3


def rotate_tank_to_enemy(t, enemy):
    turn_angle = find_ang(t.ang, t.getPos(), enemy.getPos())
    t.va = 0 if abs(turn_angle) < 2 else (turn_angle / abs(turn_angle)) * 3


def rotate_gun_to_enemy(t, enemy):
    turn_angle = find_ang(t.angGun, t.getPos(), enemy.getPos())

    if abs(turn_angle) < 2:
        t.vaGun = 0

        if euclid(t.getPos(), enemy.getPos()) < 200:
            t.gunReady = True
        else:
            t.gunReady = False
    else:
        t.vaGun = (turn_angle / abs(turn_angle)) * 0.5


def smart_rotate(t, enemy):
    predicted_pos = np.array(enemy.getPos()) + 100 * (np.array(enemy.getPos()) - np.array(enemy.oldPos))

    turn_angle = find_ang(t.angGun, t.getPos(), predicted_pos)
    if abs(turn_angle) < 2:
        t.vaGun = 0

        if euclid(t.getPos(), enemy.getPos()) < 250:
            t.gunReady = True
        else:
            t.gunReady = False
    else:
        t.vaGun = (turn_angle / abs(turn_angle)) * 0.5


def move(t, enemy):
    t.vx = 0 if euclid(t.getPos(), enemy.getPos()) < 150 else 30


def experiments():
    count_of_teams = int(input(f'Count of teams: '))
    team_players = list(map(int, input(f'Count of tanks in teams: ').split()))
    smart_team = list(map(lambda x: x == '1', input(f'Teams bullet mode (1/0): ').split()))

    pygame.init()
    screen = pygame.display.set_mode(sz)
    timer = pygame.time.Clock()
    fps = 60
    ended = False
    winner = 0
    tanks = []

    team_radius = 400
    angle_step = 360 / count_of_teams
    player_offset_angle = 15

    for current_team in range(count_of_teams):
        team_color = [np.random.randint(0, 255) for _ in range(3)]

        for player in range(team_players[current_team]):
            angle = np.radians(current_team * angle_step)
            player_angle_offset = np.radians(player * player_offset_angle)
            x_pos = sz[0] // 2 + (team_radius + np.random.randint(-100, 100)) * np.cos(angle + player_angle_offset)
            y_pos = sz[1] // 2 + (team_radius + np.random.randint(-100, 100)) * np.sin(angle + player_angle_offset)

            tank_ang = find_ang(0, [x_pos, y_pos], [sz[0] // 2, sz[1] // 2])
            current_player = Tank(current_team * 1000 + player, x_pos, y_pos, np.radians(tank_ang))
            current_player.color = team_color
            tanks.append(current_player)

    bullets = []

    start_time = time.time()

    while not ended:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()

        dt = 1 / fps

        for t in tanks:
            if t.health > 0:
                en = find_enemy(t, tanks)
                block = find_block(t, tanks)

                if en:
                    if euclid(t.getPos(), block.getPos()) < 100 and abs(
                        find_ang(t.ang, t.getPos(), block.getPos())) < 120:
                        blocked(t, find_ang(t.ang, t.getPos(), block.getPos()))
                    else:
                        rotate_tank_to_enemy(t, en)

                    if euclid(t.getPos(), block.getPos()) < euclid(t.getPos(), en.getPos()) \
                            and abs(abs(find_ang(t.angGun, t.getPos(), en.getPos())) - abs(
                        find_ang(t.angGun, t.getPos(), np.array(block.getPos())))) < 10:
                        t.blocked = True
                    else:
                        t.blocked = False

                    if smart_team[t.id // 1000]:
                        smart_rotate(t, en)
                    else:
                        rotate_gun_to_enemy(t, en)

                    move(t, en)

                if t.shootAvailable and t.gunReady and not t.blocked:
                    b = t.fire()
                    bullets.append(b)
                    t.shootAvailable = False

                t.sim(dt)
            else:
                if t.color != (0, 0, 0):
                    team_players[t.id // 1000] -= 1

                t.color = (0, 0, 0)

        alive = sum(1 for tp in team_players if tp > 0)
        winner = next((idx + 1 for idx, tp in enumerate(team_players) if tp > 0), None)

        if alive <= 1: ended = True

        for b in bullets:
            b.sim(dt)

            if euclid(b.getPos(), b.fromTank.getPos()) > 250: b.exploded = True

            for t in tanks:
                if b.fromTank.id // 1000 != t.id // 1000 and t.health > 0 and dist(t.getPos(), b.getPos()) < t.L / 2:
                    b.exploded = True
                    t.health -= 10
                    break

            if b.exploded: b.fromTank.shootAvailable = True

        bullets = [b for b in bullets if not b.exploded]

        screen.fill((255, 255, 255))

        for b in bullets: b.draw(screen)
        for t in tanks: t.draw(screen)

        if bullets:
            drawText(screen, f"NBullets = {len(bullets)}", 5, 5)
        else:
            drawText(screen, f"NBullets = {0}", 5, 5)
        pygame.display.flip()
        timer.tick(fps)

    print(f'Time: {time.time() - start_time}s')

    if winner != 0:
        drawText(screen, f"WINNER TEAM {winner}!", sz[0] / 2, 5)
    else:
        drawText(screen, f"ALL DEFEAT!", sz[0] / 2, 5)

    pygame.display.flip()
    time.sleep(5)
    pygame.quit()


if __name__ == "__main__":
    experiments()