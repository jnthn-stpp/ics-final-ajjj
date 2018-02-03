import random

class Agent(object):
    score = 0
    move = None
    def __init__(self, identity, gene=None):
        self.i = identity
        # Identification number, string, etc.
        if gene is None:
            gene = ""
            for i in range(256):
                gene += random.choice("sfrl")
        self.gene = gene
    def __str__(self):
        return str(self.i)
    __repr__ = __str__
    # By default, prints agent ID as representation

class Pop(object):
    scores = None
    fitness = None
    # List of agent scores in order of self.agents
    def __init__(self, n=0, ids=None):
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
        self.n = len(self.agents)
        self.scores = [a.score for a in self.agents]
        if self.n > 0:
            self.fitness = sum(self.scores) / self.n
    def reset(self):
        for i in self.agents:
            i.score = 0
        self.update()
    def grow(self, n=50, ids=None):
        if ids is None:
            m = max([(a.i if type(a.i) is int else 0) for a in self.agents]) + 1
            ids = [i for i in range(m, m + n)]
        for i in range(n):
            self.agents.append(Agent(ids[i]))
        self.update()
    def generate(self, mr=0, pairs=None, mp=None):
        if pairs is None:
            pairs = self.n // 2
        np = Pop()
        np.n = 2 * pairs
        self.update()
        minscore = min(self.scores)
        oldscores = [x - minscore + 1 for x in self.scores]
        scoresum = sum(oldscores)
        for i in range(pairs):
            li = random.randrange(scoresum) + 1
            ri = random.randrange(scoresum) + 1
            la = None
            ra = None
            for j in range(self.n):
                li -= oldscores[j]
                if li <= 0:
                    la = self.agents[j]; break
            for j in range(self.n):
                ri -= oldscores[j]
                if ri <= 0:
                    ra = self.agents[j]; break
            cutsite = random.randrange(256)
            lg = la.gene[:cutsite] + ra.gene[cutsite:]
            rg = ra.gene[:cutsite] + la.gene[cutsite:]
            if mp is None:
                mp = [(1 - mr) ** 256]
            for j in mutationsites(mr, mp):
                lg = lg[:j] + random.choice("sfrl") + lg[j + 1:]
            for j in mutationsites(mr, mp):
                rg = rg[:j] + random.choice("sfrl") + rg[j + 1:]
            np.agents.append(Agent(2 * i, lg))
            np.agents.append(Agent(2 * i + 1, rg))
            np.update()
        return np

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
    def populate(self, n=50, pop=None, rows=None, pos=None):
        # Add a population (one only) to the environment
        # "rows" specifies number of top rows in which to scatter agents
        # A list of positions can be given instead
        if self.pop is not None:
            print("Environment is already populated"); return
        if pop is None:
            pop = Pop(n)
        self.pop = pop
        if rows is None:
            rows = 2 * (n // self.width + 1)
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
    def neighborhood(self, identity=None, r=None, c=None):
        if identity is not None:
            r, c = self.find(identity)
        neighbor = 0
        for i in ((0, -2), (0, -1), (0, 1), (0, 2),\
                  (1, -1), (1, 0), (1, 1), (2, 0)):
            neighbor <<= 1
            neighbor += bool(self.grid[r + i[0]][c + i[1]])
        return neighbor
    def setmoves(self):
        for r in range(2, self.length + 2):
                for c in range(2, self.width + 2):
                    cell = self.grid[r][c]
                    if type(cell) is Agent:
                        neighbor = self.neighborhood(r=r, c=c)
                        cell.move = cell.gene[neighbor]
    def step(self, n=1, inf=True, blocking=False, density=0.05, points=(1, 0, -5, -10)):
        for i in range(n):
            distance = None
            self.setmoves()
            for r in range(self.length + 1, 1, -1):
                for c in random.sample(range(2, self.width + 2), self.width):
                    cell = self.grid[r][c]
                    if type(cell) is Agent:
                        if distance is None:
                            distance = r
                        if cell.move is "f":
                            space = self.grid[r + 1][c]
                            if space:
                                if type(space) is Agent and space.move is "n":
                                    cell.score += points[2]
                                else:
                                    cell.score += points[3]
                            else:
                                self.grid[r + 1][c] = cell
                                self.grid[r][c] = False
                                cell.score += points[0]
                        elif cell.move in "rl":
                            offset = 1 if cell.move is "r" else -1
                            space = self.grid[r][c + offset]
                            if space:
                                if type(space) is Agent and space.move is "n":
                                    cell.score += points[2]
                                    space.score += points[2]
                                else:
                                    cell.score += points[3]
                            else:
                                self.grid[r][c + offset] = cell
                                self.grid[r][c] = False
                                cell.score += points[1]
                                cell.move = "n"
                        elif cell.move is "s":
                            cell.score += points[1]
            if inf and distance > self.length - 2:
                self.extend(self.width, blocking, density)
        self.pop.update()

def run(env, pop, n=1, s=100, mr=0.01, out=[], mutationprobabilities=None):
    env.depopulate()
    pop.reset()
    mutationprobabilities.append((1 - mr) ** 256)
    for i in range(n):
        env.populate(pop=pop)
        env.step(s)
        out.append(pop.fitness)
        pop = pop.generate(mr, mp=mutationprobabilities)
        env.depopulate()
    return pop

def mutationsites(mr, mp):
    n = random.random()
    for i in range(len(mp)):
        n -= mp[i]
        if n <= 0:
            return random.sample(range(256), i)
    for i in range(len(mp) - 1, 257):
        if n <= 0:
            return random.sample(range(256), i)
        mp.append(mp[i] * (mr * (256 - i)) / ((1 - mr) * (i + 1)))
        n -= mp[i + 1]
    return range(256)
