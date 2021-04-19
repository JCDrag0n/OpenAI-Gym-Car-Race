import os
import argparse
import heapq
import copy
import statistics

from collections import namedtuple

from stable_baselines3.common.env_checker import check_env
from stable_baselines3 import PPO

from gym_car_race.SelfDriveEnv import Car, Track, Utils
from gym_car_race.training_utils import TensorboardCallback, linear_schedule
from gym_car_race.config import cfg


class Node:

    def __init__(self, state):
        """
        Creates/Initializes a Node object from a dictionary
        ----------
        dict: dict
                state: dict

                    angle:          (int)
                        Direction of the car. 0 is straight up
                    pos:            ([int, int])
                        Pixel coords of the topleft box corner of the car
                    sensors:        ([[int, int, int, int]...])
                        Array of n sensors. Each sensor is a list of 4 numbers
                        representing the x positions representing the x coord, y coord,
                        angle from car tip, anddistance from car tip respectively
                    traveled:       ([(int, int)...])
                        List of (x, y) tuples. Each element corresponds to a TrackBorder
                        that has been reached by the car
                    crashed:        (bool)
                        True if the car has crashed, false otherwise
                    has_finished:   (bool)
                        True if car has finished the race, false otherwise
                    done:           (bool)
                        True if either the car has finished or crashed, false otherwise
        """
        self.state = state  # Car state attributes listed above

        # Initialize both f(n) and g(n) values to infinity. Finds the better
        # node using < operator. f(n) and g(n) are set in the algorithm after
        # exploration, so this doesn't matter.
        self.fCost = float("inf")
        self.gCost = float("inf")

        self.prev_node = None  # parent node (for solution tracking)

    def __eq__(self, other):
        """
        Overrides == operator. Forces == comparison of state dictionaries
        """
        return self.state == other.state if other else False

    def __lt__(self, other):
        """
        Overrides < operator. Forces < comparison of f(n) values
        """
        return self.fCost < other.fCost if other else False

    def __hash__(self):
        """
        Overrides hash operator. The Node object will be hashed through its
        state dictionary. Frozenset is used to make the dictionary immutable
        so the hash function can return a consistent hash (for a single run
        of the program, not a hash across different versions of Python or
        different instances of running this program)
        """
        return hash(frozenset(self.state.items()))

    # Getters/Setters for object attributes
    def getState(self):
        return self.state

    def setFCost(self, cost):
        self.fCost = cost

    def getFCost(self):
        return self.fCost

    def setGCost(self, cost):
        self.gCost = cost

    def getGCost(self):
        return self.gCost

    def setPrev(self, node, direction):
        self.prev_node = (node, direction)

    def getPrev(self):
        return self.prev_node


def heuristic(node, goal):
    """
    Heuristic for the A* search algorithm
    Parameters
    ----------
    node: Node
        The generated node for heuristic calculation
    goal: Node
        The goal node for the problem
    """
    # heuristic = 0
    # for i in range(len(node.getState())):  # i represents tile number with 0 being the blank tile
    #     # Indexes 0 and 1 are the column and row coordinates respectively
    #     heuristic += (abs(goal.getState()[i][0] - node.getState()[i][0]) + abs(goal.getState()[i][1] - node.getState()[i][1])
    # return heuristic
    measurements = []
    differences = []
    for sensor in node.getState()["sensors"]:
        measurements.append(sensor[3])
    # average /= len(sensor)
    stddev = statistics.variance(measurements)
    middle = [measurements[(len(measurements) - 1)], measurements[0]]
    i = 0
    j = len(measurements) - 1
    while i < j:
        differences.append(abs(measurements[i] - measurements[j]))
        i += 1
        j -= 1

    # return Utils.dist(goal, node.getState()["pos"])*(statistics.mean(differences)) - measurements[(len(measurements) - 1)//2] - (len(node.getState()["reward_history"]))/(stddev + 1)
    return 0.5*(Utils.dist(goal, node.getState()["pos"])+(statistics.mean(differences))) - 0.8*measurements[(len(measurements) - 1)//2]
    # return Utils.dist(goal, node.getState()["pos"]) - len(node.getState()["reward_history"])

def astar(env, actions):
    state = env.get_state()
    state["pos"] = tuple(state["pos"])
    state["reward_history"] = tuple(state["reward_history"])
    state["sensors"] = tuple(tuple(sub) for sub in state["sensors"])

    start = Node(state)
    goal = env.finish_locs  # goal = Node(how are we going to get goal state?)
    explored = set()  # Set of nodes already explored, hashed for key
    solution = []
    start.setGCost(0)  # Path cost for start node is 0
    start.setFCost(heuristic(start, goal) + start.getGCost())
    frontier = [start]  # Create frontier list, initialize with start node
    heapq.heapify(frontier)

    while(len(frontier) > 0 and len(solution) == 0):
        node = heapq.heappop(frontier)
        frontier.reverse()
        frontier.sort()
        if node.getState()["has_finished"]:
            solution = []  # initialize solution list (tuple with goal node and action (action is None))
            curr = node
            while(curr.getPrev()):  # find all parent nodes and add to the solution
                solution.append(curr.getPrev()[1])
                curr = curr.getPrev()[0]
            solution.reverse()  # ordered from goal -> start. Need to reverse
            # solution is a list containing nodes from start to finish
            # what do we want to do with this list?
        else:
            explored.add(node)
            for child, action in generate_nodes(env, node, actions):
                if child not in explored:  # graph search: if child is already explored, skip and continue with algorithm
                    child_gCost = node.getGCost() + 1

                    # replace g(n) value with better f(n) value if necessary (essentially having best version of child node in frontier)
                    if child_gCost < child.getGCost():
                        child.setPrev(node, action)
                        child.setGCost(child_gCost)

                    child.setFCost(child.getGCost() + heuristic(child, goal)) # line 122
                    frontier.reverse()
                    frontier.sort()
                    heapq.heappush(frontier, child)  # push child into frontier
    return solution


def generate_nodes(env, node, actions):
    node.state["reward_history"] = list(node.state["reward_history"])
    node.state["sensors"] = list(list(sub) for sub in node.state["sensors"])
    env.set_state(node.state)
    children = []
    for action in actions:
        for step in action:
            env.step(step)
            env.render()
        child = env.get_state()
        child["pos"] = tuple(child["pos"])
        child["reward_history"] = tuple(child["reward_history"])
        child["sensors"] = tuple(tuple(sub) for sub in child["sensors"])
        if not child["crashed"]:
            children.append((Node(child), action))
        env.set_state(node.state)
    node.state["reward_history"] = tuple(node.state["reward_history"])
    node.state["sensors"] = tuple(tuple(sub) for sub in node.state["sensors"])
    return children


def main():
    """
    Main function
    ----------
    Opens the file containing the start and goal states, parsing each line.
    Initializes start and goal nodes.
    Runs A* search with start and goal states through function call
    Builds the Output.txt file through function call
    """

    # Set the directory where your models should be stored as well as the name of
    # the model that you want to load/save

    model_dir = "./models/"
    model_name = "model1"
    os.makedirs(model_dir, exist_ok=True)

    # load args from user's command input
    parser = argparse.ArgumentParser()
    parser.description = "To customize your map: use command python example.py -reset=True"
    parser.add_argument("-reset", "--input if reset map", help="False- using default map, True - Create your own map", dest="ifreset", type=bool, default=False)
    args = parser.parse_args()

    num_of_tracks = 1

    for i in range(num_of_tracks):
        # Set up the environment using the values found in configs
        #env = Track()
        env = generate_track()
        car = Car()
        env.add_car(car)
        actions = car.get_actions()
        obs = env.reset(new=False)

        solution_actions = astar(env, actions)

        total_actions = []
        obs = env.reset(new=False)
        for action in solution_actions:
            for step in action:
                obs, rewards, done, info = env.step(step)
                env.render()
            total_actions += action

        outputFile = open("Output_" + i + ".txt", "w")  # open output file for writing
        print(*total_actions, file=outputFile)

        print(total_actions)


if __name__ == "__main__":
    main()
