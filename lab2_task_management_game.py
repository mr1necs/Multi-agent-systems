import numpy as np
import pygame
import sys
import pickle

# Цвета для состояний задач
colors = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
R = 35  # Радиус задач
WIDTH, HEIGHT = 1000, 800
tasks = []  # Список задач
ts0, ts1 = None, None  # Соединяемые задачи

def dist(p1, p2):
    """Вычисляет расстояние между двумя точками."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return np.sqrt(dx * dx + dy * dy)

# Инициализация шрифта
pygame.font.init()
font = pygame.font.SysFont('Comic Sans MS', 20)

def drawText(screen, s, x, y):
    """Рисует текст на экране."""
    surf = font.render(s, True, (0, 0, 0))
    screen.blit(surf, (x, y))

# Модель задачи
class Task:
    def __init__(self, id, x, y):
        self.id = id  # Идентификатор задачи
        self.x = x  # Координата x
        self.y = y  # Координата y
        # Состояние выполнения задачи
        # 0 - недоступна, 1 - доступна, 2 - выполняется, 3 - завершена
        self.state = 0
        self.inps = []  # Входящие задачи
        self.outs = []  # Исходящие задачи

    def getPos(self):
        """Возвращает координаты задачи."""
        return (self.x, self.y)

    def draw(self, screen):
        """Рисует задачу на экране."""
        # Рисуем эллипс для задачи
        pygame.draw.ellipse(screen, colors[self.state],
                            [self.x - R, self.y - R, 2 * R, 2 * R], 2)
        # Рисуем линии от входящих задач
        for ts in self.inps:
            pygame.draw.line(screen, (100, 100, 100), ts.getPos(), self.getPos(), 2)
        # Подписываем задачу
        drawText(screen, f"T{self.id}", self.x - 10, self.y - 10)

def findTask(pos, r):
    """Поиск задачи под курсором."""
    for ts in tasks:
        if dist(pos, ts.getPos()) < r:
            return ts


def findPossibleTasks():
    """Поиск доступных для выполнения задач."""
    for ts in tasks:
        if ts.state == 0:
            if len(ts.inps) == 0 or all([inp.state == 3 for inp in ts.inps]):
                ts.state = 1


def performTasks():
    """Выполнение задач."""
    res = []
    for ts in tasks:
        if ts.state == 1:
            ts.state = 2
        elif ts.state == 2:
            ts.state = 3
    return res


def main():
    global tasks, ts0, ts1
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Task Manager")

    # Основной цикл программы
    while True:
        drag = pygame.key.get_pressed()[pygame.K_LSHIFT]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                ts0 = findTask(event.pos, R)
                if ts0 is None and not drag:
                    ts = Task(len(tasks) + 1, *event.pos)
                    tasks.append(ts)

            if event.type == pygame.MOUSEBUTTONUP:
                if drag:
                    ts1 = findTask(event.pos, R)
                    if ts0 is not None and ts1 is not None:
                        ts0.outs.append(ts1)
                        ts1.inps.append(ts0)
                    ts0 = ts1 = None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    with open("scenario.bin", "wb") as f:
                        pickle.dump(tasks, f)

                if event.key == pygame.K_l:
                    with open("scenario.bin", "rb") as f:
                        tasks = pickle.load(f)

                if event.key == pygame.K_1:
                    findPossibleTasks()

                if event.key == pygame.K_2:
                    performTasks()

                if event.key == pygame.K_3:
                    performTasks()
                    findPossibleTasks()

        screen.fill((255, 255, 255))

        for ts in tasks:
            ts.draw(screen)

        if drag and ts0 is not None:
            pygame.draw.line(screen, (100, 100, 100), ts0.getPos(), pygame.mouse.get_pos(), 2)

        pygame.display.update()
        pygame.time.delay(50)

main()

NN = [1, 2, 3, 4, 5, 6]
