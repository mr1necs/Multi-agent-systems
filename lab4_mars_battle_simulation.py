import sys, pygame
import numpy as np
import math
import random

# Размер окна
sz = (800, 600)

# Вспомогательные функции
def dist(p1, p2):
    return np.linalg.norm(np.subtract(p1, p2))

def rot(v, ang):
    s, c = math.sin(ang), math.cos(ang)
    return [v[0] * c - v[1] * s, v[0] * s + v[1] * c]

def rotArr(vv, ang):
    return [rot(v, ang) for v in vv]

pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 20)

def drawText(screen, s, x, y):
    surf = font.render(s, True, (0, 0, 0))
    screen.blit(surf, (x, y))

# Модель пули
class Bullet:
    def __init__(self, x, y, ang, team):
        self.x = x
        self.y = y
        self.ang = ang
        self.vx = 200
        self.L = 10
        self.exploded = False
        self.team = team  # Команда, которой принадлежит пуля

    def getPos(self):
        return [self.x, self.y]

    def draw(self, screen):
        p0 = self.getPos()
        p1 = rot([-self.L / 2, 0], self.ang)
        p2 = rot([+self.L / 2, 0], self.ang)
        pygame.draw.line(screen, (0, 0, 0), np.add(p0, p1), np.add(p0, p2), 3)

    def sim(self, dt):
        vec = rot([self.vx, 0], self.ang)
        self.x += vec[0] * dt
        self.y += vec[1] * dt

# Модель танка
class Tank:
    def __init__(self, id, x, y, ang, color, team):
        self.id = id
        self.x = x
        self.y = y
        self.ang = ang
        self.angGun = 0
        self.L = 70
        self.W = 45
        self.vx = random.uniform(10, 30)
        self.va = random.uniform(-0.5, 0.5)
        self.health = 100
        self.is_active = True
        self.cooldown = 0
        self.color = color
        self.team = team  # Команда танка

    def fire(self, target):
        if not self.is_active or self.cooldown > 0:
            return None
        r = self.W / 2.3
        LGun = self.L / 2
        p2 = rot([r + LGun, 0], self.ang + self.angGun)
        p2 = np.add(self.getPos(), p2)
        self.cooldown = 0.2
        return Bullet(*p2, self.ang + self.angGun, self.team)

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
        pygame.draw.circle(screen, self.color, self.getPos(), int(r), 2)

        LGun = self.L / 2
        p0 = self.getPos()
        p1 = rot([r, 0], self.ang + self.angGun)
        p2 = rot([r + LGun, 0], self.ang + self.angGun)
        pygame.draw.line(screen, self.color, np.add(p0, p1), np.add(p0, p2), 3)

        drawText(screen, f"{self.id} ({int(self.health)})", self.x, self.y - self.L / 2 - 12)

    def sim(self, dt):
        if not self.is_active:
            return
        vec = rot([self.vx, 0], self.ang)
        self.x += vec[0] * dt
        self.y += vec[1] * dt
        self.ang += self.va * dt

        if self.cooldown > 0:
            self.cooldown -= dt

        self.x = max(self.W / 2, min(sz[0] - self.W / 2, self.x))
        self.y = max(self.L / 2, min(sz[1] - self.L / 2, self.y))

        if self.health <= 0:
            self.is_active = False

# Основная функция
def main():
    screen = pygame.display.set_mode(sz)
    timer = pygame.time.Clock()
    fps = 20

    # Создаем команды танков
    n = 2
    team1 = [Tank(i, 200 + n * 5, 100 + i * 100, 0, (255, 0, 0), 1) for i in range(4)]
    team2 = [Tank(i + 4, 600 + n * 5, 100 + i * 100, math.pi, (0, 0, 255), 2) for i in range(4)]

    tanks = team1 + team2
    bullets = []

    # Начало сражения
    start_time = pygame.time.get_ticks()

    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                sys.exit(0)

        dt = 1 / fps

        # Движение танков и стрельба
        for t in tanks:
            t.sim(dt)
            if t.is_active:
                enemies = [e for e in tanks if e.id != t.id and e.is_active]
                if enemies:
                    closest_enemy = min(enemies, key=lambda e: dist(t.getPos(), e.getPos()))
                    bullet = t.fire(closest_enemy.getPos())
                    if bullet:
                        bullets.append(bullet)

        # Движение пуль и проверка попаданий
        for b in bullets:
            b.sim(dt)
            if b.x < 0 or b.x > sz[0] or b.y < 0 or b.y > sz[1]:
                b.exploded = True
            for t in tanks:
                if t.team != b.team and dist(t.getPos(), b.getPos()) < t.L / 2 and t.is_active:
                    b.exploded = True
                    t.health -= 10
                    break

        bullets = [b for b in bullets if not b.exploded]

        # Проверка окончания сражения
        team1_active = any(t.is_active for t in team1)
        team2_active = any(t.is_active for t in team2)

        if not team1_active or not team2_active:
            battle_time = (pygame.time.get_ticks() - start_time) / 1000  # Время в секундах
            team1_health = sum(t.health for t in team1 if t.is_active)
            team2_health = sum(t.health for t in team2 if t.is_active)
            winner = "Team 1 (Red)" if team1_active else "Team 2 (Blue)"
            print(f"Battle finished in {battle_time:.2f} seconds")
            print(f"Winner: {winner}")
            print(f"Team 1 remaining health: {team1_health}")
            print(f"Team 2 remaining health: {team2_health}")
            pygame.quit()
            sys.exit(0)

        # Отрисовка
        screen.fill((255, 255, 255))
        for t in tanks:
            t.draw(screen)
        for b in bullets:
            b.draw(screen)

        drawText(screen, f"NBullets = {len(bullets)}", 5, 5)

        pygame.display.flip()
        timer.tick(fps)

main()