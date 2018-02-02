import random

class Agent(object):
    def __init__(self, identity, gene=None):
        self.i = identity
        # Identification number, string, etc.
        if gene is None:
            gene = ""
            for i in range(256):
                gene += random.choice("sfrl")
        self.gene = gene
        self.score = 0
    def __str__(self):
        return str(self.i)
    __repr__ = __str__
    # By default, prints agent ID as representation

class Pop(object):
    scores = None
    # List of agent scores in order of self.agents
    def __init__(self, n=50, ids=None):
        # A list of IDs can be used to name agents
        self.n = n
        if ids is None:
            ids = [i for i in range(n)]
        self.agents = []
        for i in range(n):
            self.agents.append(Agent(ids[i]))
        self.update()
    def __str__(self):
        return str(self.agents)
    __repr__ = __str__
    def update(self):
        # Called after calling environment.step to update scores, etc.
        self.scores = [a.score for a in self.agents]
    def grow(self, n=50, ids=None):
        self.n += n
        if ids is None:
            m = max([(a.i if type(a.i) is int else 0) for a in self.agents]) + 1
            ids = [i for i in range(m, m + n)]
        for i in range(n):
            self.agents.append(Agent(ids[i]))
        self.update()
    def generate(self):
        # This will generate a new population based on score selection
        pass

class Env(object):
    # self contains a padded grid whose dimensions
    # (without padding) are self.length and self.width
    length = 0
    pop = None
    def __init__(self, width=30, length=30):
        self.width = width
        self.grid = 4 * [(width + 4) * [True]]
        self.extend(length)
    def __str__(self):
        out = ""
        for i in self.grid:
            for j in i:
                if j is False: s = " "
                elif j is True: s = "X"
                else: s = "O"
                out += s
            out += "\n"
        return out[:-1]
    __repr__ = __str__
    def populate(self, pop=None, rows=5, pos=None):
        # Add a population (one only) to the environment
        # "rows" specifies number of top rows in which to scatter agents
        # A list of positions can be given instead
        if self.pop is not None:
            print("Environment is already populated"); return
        if pop is None:
            pop = Pop()
        self.pop = pop
        if pos is None:
            pos = random.sample(range(self.width * rows), pop.n)
            for i in range(pop.n):
                r = pos[i] // self.width + 2
                c = pos[i] % self.width + 2
                if not self.grid[r][c]:
                    self.grid[r][c] = pop.agents[i]
        else:
            for i in range(pop.n):
                r, c = pos[i]
                if not self.grid[r][c]:
                    self.grid[r][c] = pop.agents[i]
    def depopulate(self):
        # Dissociate population from environment
        # Does not affect population or agents
        self.clear("agents")
        self.pop = None
    def block(self, density=0.05, rmin=10, rmax=None, blks=None):
        # Add obstacles; similar functionality to self.populate
        if blks is None:
            if rmax is None:
                rmax = self.length
            bnum = int(density * self.width * (rmax - rmin))
            blks = random.sample(range(self.width * rmin, self.width * rmax), bnum)
            for i in blks:
                r = i // self.width + 2
                c = i % self.width + 2
                self.grid[r][c] = self.grid[r][c] or True
        else:
            for i in blks:
                r, c = i
                self.grid[r][c] = self.grid[r][c] or True
    def clear(self, w="all"):
        # Clear obstacles ("blocks"), agents, or both from self.grid
        # Clearing agents does not remove them from their populations
        for r in range(2, self.length + 2):
            for c in range(2, self.width + 2):
                if w is "all":
                    self.grid[r][c] = False
                elif w in ("ag", "agent", "agents"):
                    if type(self.grid[r][c]) is Agent:
                        self.grid[r][c] = False
                elif w in ("b", "block", "blocks"):
                    if self.grid[r][c] is True:
                        self.grid[r][c] = False
                else:
                    print("Wrong argument"); return
    def extend(self, rows=1, blocking=False, density=0.05):
        # Appends rows to self.grid
        # blocking=True creates obstacles in the new rows
        self.grid = self.grid[:-2]
        for i in range(rows):
            self.grid += [[True, True] + self.width * [False] + [True, True]]
        self.grid += 2 * [(self.width + 4) * [True]]
        if blocking:
            self.block(density, self.length, self.length + rows)
        self.length += rows
    def find(self, identity):
        # Get agent's row and column by ID
        for r in range(2, self.length + 2):
            for c in range(2, self.width + 2):
                if type(self.grid[r][c]) is Agent:
                    if self.grid[r][c].i == identity:
                        return (r, c)
        print("Agent not found")
    def show(self, *identity):
        # Display agent by ID
        out = ""
        for i in self.grid:
            for j in i:
                if j is False: s = " "
                elif j is True: s = "X"
                elif j.i in identity: s = "@"
                else: s = "-"
                out += s
            out += "\n"
        print(out[:-1])
    def remove(self, *identity):
        # Remove agent by ID
        # Does not remove agent from its population
        for i in identity:
            r, c = self.find(i)
            self.grid[r][c] = False
    def neighborhood(self, identity=None, r=None, c=None, index=False):
        # Use index=True to get the numerical value from 0 to 255
        if identity is not None:
            r, c = self.find(identity)
        neighbor = 0
        for i in ((0, -2), (0, -1), (0, 1), (0, 2),\
                  (1, -1), (1, 0), (1, 1), (2, 0)):
            neighbor <<= 1
            neighbor += bool(self.grid[r + i[0]][c + i[1]])
        return neighbor if index else self.grid[r][c].gene[neighbor]
    def step(self, n=1, inf=True, blocking=False, density=0.05):
        # Moves all the agents, reading rows from left to right up the grid
        # Automatically extends the grid when agents get close to the bottom
        # "skip" is used to avoid moving an agent again after it has moved right
        # Adds a point for successful forward movement
        # Subtracts a point in all other cases
        for i in range(n):
            distance = None
            skip = False
            for r in range(self.length + 1, 1, -1):
                for c in range(2, self.width + 2):
                    if skip:
                        skip = False
                    elif type(self.grid[r][c]) is Agent:
                        if distance is None:
                            distance = r - 2
                        move = self.neighborhood(r=r, c=c)
                        if move is "f" and not self.grid[r + 1][c]:
                            self.grid[r + 1][c] = self.grid[r][c]
                            self.grid[r][c] = False
                            self.grid[r + 1][c].score += 1
                        elif move is "r" and not self.grid[r][c + 1]:
                            self.grid[r][c + 1] = self.grid[r][c]
                            self.grid[r][c] = False
                            self.grid[r][c + 1].score -= 1
                            skip = True
                        elif move is "l" and not self.grid[r][c - 1]:
                            self.grid[r][c - 1] = self.grid[r][c]
                            self.grid[r][c] = False
                            self.grid[r][c - 1].score -= 1
                        else:
                            self.grid[r][c].score -= 1
            if inf and distance > self.length - 4:
                self.extend(self.width, blocking, density)
        self.pop.update()
