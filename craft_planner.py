import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
from heapq import heappop, heappush

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])


class State(OrderedDict):
    """ This class is a thin wrapper around an OrderedDict, which is simply a dictionary which keeps the order in
        which elements are added (for consistent key-value pair comparisons). Here, we have provided functionality
        for hashing, should you need to use a state as a key in another dictionary, e.g. distance[state] = 5. By
        default, dictionaries are not hashable. Additionally, when the state is converted to a string, it removes
        all items with quantity 0.

        Use of this state representation is optional, should you prefer another.
    """

    def __key(self):
        return tuple(self.items())

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def copy(self):
        new_state = State()
        new_state.update(self)
        return new_state

    def __str__(self):
        return str(dict(item for item in self.items() if item[1] > 0))


def make_checker(rule):
    # Returns a function to determine whether a state meets a rule's requirements.
    # This code runs once, when the rules are constructed before the search is attempted.

    def check(state):
        tools = ["bench", "wooden_pickaxe", "iron_pickaxe", "stone_pickaxe", "wooden_axe", "stone_axe", "iron_axe", "furnace"]
        resources = ["wood", "coal", "cobble", "ingot", "ore", "plank", "stick"]
        #print("state = "+str(state))
        for item in rule['Produces'].items():
            if item[0] in state:
                if state[item[0]] >= 1 and item[0] in tools:
                    return False
                if item[0] in resources and state[item[0]] > 20:
                    return False
        if 'Requires' in rule:
            #print("Requires = "+str(rule['Requires']))
            # This code is called by graph(state) and runs millions of times.
            # Tip: Do something with rule['Consumes'] and rule['Requires'].
            for item in rule['Requires'].items():
                #print("required item checker = "+str(item))
                if item[0] not in state:
                    #print("Does not have required item")
                    return False
                if not state[item[0]]:
                    #print("Does not have enough required item")
                    return False
        if'Consumes' in rule:
            for item in rule['Consumes'].items():
                #print("Consumed item checker = "+str(item))
                if item[0] not in state:
                    #print("Does not have consumed item")
                    return False
                if item[1] > state[item[0]]:
                    #print("Does not have enough consumed item")
                    return False
                #print("Loopin")

        return True

    return check


def make_effector(rule):
    # Returns a function which transitions from state to new_state given the rule.
    # This code runs once, when the rules are constructed before the search is attempted.

    def effect(state):
        tools = ["bench", "wooden_pickaxe", "iron_pickaxe", "stone_pickaxe", "wooden_axe", "stone_axe", "iron_axe", "furnace"]
        #print("state = "+str(state))
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].
        new_state = state.copy()
        if 'Consumes' in rule:
            for item in rule['Consumes'].items():
                if item in tools:
                    continue
                #print("item consumed "+str(item))
                new_state[item[0]] = new_state[item[0]] - rule['Consumes'][item[0]]
        if 'Produces' in rule:
            #print("Produces is in rule")
            for item in rule['Produces'].items():
                #print("Item in produces = "+str(state))
                if new_state[item[0]]:
                    new_state[item[0]] += rule['Produces'][item[0]]
                else:
                    new_state[item[0]] = rule['Produces'][item[0]]
                #print("After effector applied = "+str(state))
        return new_state

    return effect


def make_goal_checker(goal):
    # Returns a function which checks if the state has met the goal criteria.
    # This code runs once, before the search is attempted.

    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        for item in goal.items():
            if item[0] not in state:
                return False
            if item[1] > state[item[0]]:
                return False
        return True
    #return False

    return is_goal


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    for r in all_recipes:
        if r.check(state):
            yield (r.name, r.effect(state), r.cost)


'''
def get_recipes(state, state, goal):
    for r in all_recipes
        if r.check(state) and goal in r['Produces']:
            yield(r.name, r.effect(state), r.cost)
'''

def heuristic(state):
    # This heuristic function should guide your search.
    score = 0
    for item in Crafting['Goal'].items():
        if item[0] in state:
            if item[1] <= state[item[0]]:
                score += (3*state[item[0]])
    return 100-score


'''def backup(state, goal):
    dist={}
    prev={}
    path=[]
    for item in goal.items():
        if item[0] in state:
            if item[1] <= state[item[0]]:
                continue
            else:
                
                backup(state, item)
                continue
            for name, adj_state, cost in get_recipes(state):
        
        path.extend(backup(state, item))
'''

def estimated_remaining(state, goal):
    sums = 0
    for item in goal.items():
        if item[0] in state:
            if item[1] < state[item[0]]:
                sums += item[1]
            else:
                sums += state[item[0]]
    return sum(goal.values()) - sums



def search(graph, state, is_goal, limit, heuristic, Crafting):
    start_time = time()
    path = None
    current_distance = 0
    current_node = state
    distances = {state:0}
    costs = {state: 0}
    previous_cell = {state:None}
    queue = [(0, state)]
    # Search
    while time() - start_time < limit:
        while queue:
            current_distance, current_node = heappop(queue)
            temp = current_node
            #print("current_node = "+str(current_node))
            if is_goal(current_node):
                cost = distances[current_node]
                path=[]
                while current_node:
                    path.append((current_node))
                    current_node = previous_cell[current_node]
                total = 0
                for item in path:
                    total += costs[item]
                return ((time() - start_time), path[-2::-1], total)
            for name, node, cost in graph(current_node):
                costs[node] = cost
                cost += heuristic(node)
                new_distance = current_distance + cost
                if node not in distances or new_distance < distances[node]:
                    distances[node] = new_distance
                    if node not in previous_cell:
                        previous_cell[node] = current_node
                    if is_goal(node) or is_goal(current_node):
                        cost = distances[node]
                        path=[]
                        while node:
                            path.append((node))
                            node = previous_cell[node]
                        total=0
                        for item in path:
                            total += costs[item]
                        return ((time() - start_time), path[-2::-1], total)
                    remaining_distance = estimated_remaining(node, Crafting['Goal'])
                    heappush(queue, (remaining_distance, node))

    print("Failed to find a path from", state, 'within time limit.')
    return None

if __name__ == '__main__':
    with open('Crafting.json') as f:
        Crafting = json.load(f)

    # List of items that can be in your inventory:
    print('All items:',Crafting['Items'])

    # List of items in your initial inventory with amounts:
    print('Initial inventory:',Crafting['Initial'])

    # List of items needed to be in your inventory at the end of the plan:
    print('Goal:',Crafting['Goal'])

    # Dict of crafting recipes (each is a dict):
#print('Example recipe:','craft stone_pickaxe at bench ->',Crafting['Recipes']['craft stone_pickaxe at bench'])

    # Build rules
    all_recipes = []
    for name, rule in Crafting['Recipes'].items():
        checker = make_checker(rule)
        effector = make_effector(rule)
        recipe = Recipe(name, checker, effector, rule['Time'])
        all_recipes.append(recipe)

    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])

    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']})
    state.update(Crafting['Initial'])

    # Search - This is you!
    limit = 30

    time, path, cost = search(graph, state, is_goal, limit, heuristic, Crafting)
    print("Time: "+str(time))
    if path:
        for node in path:
            print(node)
        stats = {'total_cost' : cost, 'length' : len(path)}
        print("\n"+str(stats))
    pass
