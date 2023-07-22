import pygame, sys, json


def load_settings(path):
    with open(path, "r") as f:
        dict = json.load(f)
        global COLORS, WORLD_HEIGHT, WORLD_WIDTH, DAMAP, WIDTH, HEIGHT, FPS
        COLORS, WORLD_HEIGHT, WORLD_WIDTH, WIDTH, HEIGHT, FPS = dict["COLORS"], dict["WORLD HEIGHT"],\
                                                                dict["WORLD WIDTH"],\
                                                                dict["WIDTH"], dict["HEIGHT"], dict["FPS"]


WORLD_WIDTH, WORLD_HEIGHT = 0, 0
COLORS = []
WIDTH = 1000
HEIGHT = 1000
FPS = 50
load_settings("settings.json")

screen_size = (WIDTH, HEIGHT)
tile_width = tile_height = 50
pygame.init()
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption('Pathfinding')
clock = pygame.time.Clock()


class World:
    def __init__(self, world, wall_symbol=1):
        self.world = [[[cell, False] for cell in row] for row in world]
        self.wall_symbol = wall_symbol

    def __len__(self):
        return len(self.world)

    def __getitem__(self, item):
        return self.world[item]

    def ys_from_coords(self, coords):
        y, x = coords
        y, x = max(0, min(len(self), y)), max(0, min(len(self[0]), x))
        return y, x

    def set_cell(self, coords, value):
        y, x = self.ys_from_coords(coords)
        self.world[y][x] = [value, self.world[y][x][1]]

    def get_cell(self, coords):
        y, x = self.ys_from_coords(coords)
        return self[y][x]

    def width(self):
        return len(self.world[0])

    def height(self):
        return len(self.world)

    def visit(self, coords):
        y, x = self.ys_from_coords(coords)
        self[y][x][1] = True

    def is_visited(self, coords):
        y, x = self.ys_from_coords(coords)
        return self[y][x][1]

    def is_wall(self, coords):
        y, x = self.ys_from_coords(coords)
        return self[y][x][0] == self.wall_symbol

    def find_unique_num(self, num):
        for y, row in enumerate(self.world):
            for x, cell in enumerate(row):
                if cell[0] == num:
                    return y, x

    def surroundings(self, coords):
        y, x = self.ys_from_coords(coords)
        res = [[None for _ in range(3)] for _ in range(3)]
        for yy in range(max(0, y - 1), min(self.height(), y + 2)):
            for xx in range(max(0, x - 1), min(self.width(), x + 2)):
                if (yy != y or xx != x) and not self.is_wall((yy, xx)) and abs(xx - x) + abs(yy - y) == 1:
                    res[1 + (yy - y)][1 + (xx - x)] = (self.world[yy][xx], (yy, xx))
        return res

    def path(self, y1, x1, y2, x2):
        if self.is_wall((y1, x1)) or self.is_wall((y2, x2)):
            raise ValueError
        last_points = [[y1, x1]]
        paths = [0, last_points.copy()]
        while not (y2, x2) in last_points:
            sus = []
            for ind, point in enumerate(last_points):
                res = []
                if isinstance(point, list) or isinstance(point, tuple):
                    last_points.remove(point)
                    self.visit(point)
                    surroundings = self.surroundings(point)
                    for row in surroundings:
                        for i in row:
                            if i is not None and not self.is_visited(i[1]):
                                last_points.insert(ind, i[1])
                                res.append([point, i[-1]])
                    sus.append(res)
                if (y2, x2) in last_points:
                    break
            if not sus:
                self.unvisit_all()
                return
            paths.append(sus)
        needed_point, final_res, breaksss, nex_gen = (y2, x2), [], False, False
        for lists_of_children_of_points in paths[-1::-1]:
            if breaksss:
                break
            for list_of_children_of_points in lists_of_children_of_points[-1::-1]:
                if breaksss or nex_gen:
                    nex_gen = False
                    break
                for child in list_of_children_of_points:
                    if isinstance(child, int):
                        final_res.append(child)
                        breaksss = True
                        break
                    if child[1] == needed_point:
                        final_res.append(child[1])
                        needed_point = child[0]
                        # nex_gen = True
                        # break
        final_res[-1] = (y1, x1)
        self.unvisit_all()
        return final_res

    def unvisit_all(self):
        for y in range(self.height()):
            for x in range(self.width()):
                self[y][x][1] = False


def empty_map(w, h):
    return [[0 for _ in range(w)] for _ in range(h)]


class Board:
    def __init__(self, world=World(empty_map(10, 10))):
        if not isinstance(world, World):
            world = World(world)
        self.world = world
        self.path = []
        self.clicked_cell = None
        self.running = False

    def draw(self):
        for y, row in enumerate(self.world):
            for x, cell in enumerate(row):
                screen.fill(pygame.Color(*COLORS[str(cell[0])]), (WIDTH * x / self.world.width(),
                                                                  HEIGHT * y / self.world.height(),
                                                                  WIDTH / self.world.width(),
                                                                  HEIGHT / self.world.height()))
        pygame.display.flip()

    def run(self):
        self.running = True
        self.draw()
        mouse_button_that_is_currently_being_held = None
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_button_that_is_currently_being_held = event.button
                    self.clicked_cell = None
                    self.cell_clicking_handler(event.pos, mouse_button_that_is_currently_being_held)
                if event.type == pygame.MOUSEBUTTONUP:
                    mouse_button_that_is_currently_being_held = None
                    self.clicked_cell = None
                if event.type == pygame.MOUSEMOTION and mouse_button_that_is_currently_being_held:
                    self.cell_clicking_handler(event.pos, mouse_button_that_is_currently_being_held)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.make_path()
                    self.draw()
            if self.path:
                self.world.set_cell(self.world.find_unique_num(2), 0)
                self.world.set_cell(self.path[0], 2)
                self.draw()
                if len(self.path) >= 1:
                    self.path = self.path[1:]
                else:
                    self.path = []
            clock.tick(FPS)

    def cell_clicking_handler(self, pos, btn):
        if self.get_cell_click(pos) != self.clicked_cell:
            self.clicked_cell = self.get_cell_click(pos)
            if btn == 1:
                if self.world.get_cell(self.clicked_cell)[0] != 0:
                    self.world.set_cell(self.clicked_cell, 0)
                else:
                    self.world.set_cell(self.clicked_cell, 1)
            elif btn == 3:
                if self.world.find_unique_num(2) and not self.world.find_unique_num(3):
                    self.world.set_cell(self.clicked_cell, 3)
                elif not self.world.find_unique_num(2):
                    self.world.set_cell(self.clicked_cell, 2)
            if self.path and btn:
                self.make_path()
            self.draw()

    def make_path(self):
        if self.world.find_unique_num(2) and self.world.find_unique_num(3):
            path = self.world.path(*self.world.find_unique_num(2), *self.world.find_unique_num(3))
            if path:
                self.path = path[-1::-1]
            else:
                self.path = []

    def get_cell_click(self, pos):
        x_0_1, y_0_1 = pos[0] / WIDTH, pos[1] / HEIGHT
        cell_x, cell_y = max(0, min(1, x_0_1)) * self.world.width(), max(0, min(1, y_0_1)) * self.world.height()
        return int(cell_y), int(cell_x)


the_map = empty_map(WORLD_WIDTH, WORLD_HEIGHT)
b = Board(the_map)
b.run()