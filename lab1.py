import numpy as np
import pygame, sys
import time

# Вспомогательная функция для вычисления Евклидова расстояния
def dist(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return np.sqrt(dx * dx + dy * dy)

# Модель целевого объекта
class Obj:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.reservedRobot = None
        self.finished = False

    def getPos(self):
        return (self.x, self.y)

    def draw(self, screen):
        r = 10
        pygame.draw.ellipse(screen, self.color, [self.x - r, self.y - r, 2 * r, 2 * r], 2)

# Модель автономного транспортного робота
class Robot:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.attachedObj = None
        self.target = None

    def getPos(self):
        return (self.x, self.y)

    def draw(self, screen):
        r = 20
        pygame.draw.ellipse(screen, (255, 0, 0), [self.x - r, self.y - r, 2 * r, 2 * r], 2)

    def simulate(self):
        if self.target is not None:
            p1 = self.target
            p2 = (self.x, self.y)
            v = np.array(p1) - np.array(p2)
            d = dist(p1, p2)
            if d > 0:
                v = v / d
            self.x += v[0] * 5
            self.y += v[1] * 5

        if self.attachedObj is not None:
            self.attachedObj.x = self.x
            self.attachedObj.y = self.y

    def findNearestObj(self, objs, threshold=100500):
        res = None
        D = 100500
        for o in objs:
            if o.reservedRobot is not None and o.reservedRobot != self:
                continue
            if o.finished:
                continue
            dNew = dist(o.getPos(), self.getPos())
            if dNew < D:
                D = dNew
                res = o
        if D > threshold:
            res = None
        return res

    def take(self, obj):
        if obj is not None:
            self.attachedObj = obj

# Распределение задач между роботами

def distributeTasks(robots, objs, goal):
    for r in robots:
        if r.attachedObj is not None and dist(r.getPos(), goal.getPos()) < 20:
            r.attachedObj.finished = True
            r.attachedObj = None
            r.target = None
        else:
            if r.attachedObj is None:
                obj = r.findNearestObj(objs)
                if obj is not None and dist(r.getPos(), obj.getPos()) < 20:
                    r.take(obj)
                    r.target = goal.getPos()
                    return

            if r.target is None and r.attachedObj is None:
                obj = r.findNearestObj(objs)
                if obj is None:
                    continue
                if obj.reservedRobot is not None:
                    continue
                r.target = obj.getPos()
                obj.reservedRobot = r

# Проверка завершения миссии

def checkMission(robots, objs, goal):
    for r in robots:
        if dist(r.getPos(), goal.getPos()) > 20:
            return False
    for o in objs:
        if o.reservedRobot is None:
            return False
    return True

# Генерация объектов в случайных позициях

def generateObjects(N, WIDTH, HEIGHT):
    res = []
    for i in range(N):
        o = Obj(np.random.randint(50, WIDTH - 50), np.random.randint(50, HEIGHT - 50), (0, 255, 0))
        res.append(o)
    return res

# Основная функция

def main():
    WIDTH = 1000
    HEIGHT = 800

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    start = time.time()

    robots = [
        Robot(150, 150),
        Robot(250, 250),
        Robot(350, 350)
    ]

    objs = generateObjects(10, WIDTH, HEIGHT)

    goal = Obj(750, 450, (0, 0, 255))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if checkMission(robots, objs, goal):
            break

        screen.fill((255, 255, 255))

        distributeTasks(robots, objs, goal)

        for r in robots:
            r.simulate()
            r.draw(screen)

        for o in objs:
            o.draw(screen)

        goal.draw(screen)

        pygame.display.update()
        pygame.time.delay(50)

    end = time.time()
    print(end - start)

main()
