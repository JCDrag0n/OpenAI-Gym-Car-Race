#!/usr/bin/env python
import random
from astar import *
import copy


class TrackEnv(Env):

    def __init__(self, x, y):
        # REMEMBER HE PADDED ITITITITIITITITII BRUHRURHURHUH
        # PLEZZZSZ REMMRMRMRMRMRMR MEEEEEE
        self.curr = (0, 0)
        self.goal = (0, 0)
        self.x = x
        self.y = y
        self.track = [[0]*x for i in range(y)]
        for row in range(y):
            for col in range(x):
                self.track[row][col] = "1"
        # top right - self.track[1][self._num_blocks_x - 2]
        # bottom right - self.track[self._num_blocks_y - 3][self._num_blocks_x - 2]
        # top left - self.track[1][1]
        # bottom left - self.track[self._num_blocks_y - 3][1]
        finish_list = [(y - 3, x - 2, True), (y - 3, 1, False)]
        start_list = [(1, 1, True), (1, x - 2, False)]
        start_y, start_x, smid = random.choice(start_list)
        finish_y, finish_x, fmid = random.choice(finish_list)
        for row in range(3):
            for col in range(2):
                self.track[start_y + row][start_x + col] = "s"
                self.track[finish_y + row][finish_x + col] = "f"
        if smid:
            self.curr = (start_y + 1, start_x + 2)
        else:
            self.curr = (start_y + 1, start_x - 1)

        if fmid:
            self.goal = (finish_y + 1, finish_x - 1)
        else:
            self.goal = (finish_y + 1, finish_x + 1)

        self.state = (self.curr, self.track)

    def set_state(self, state):
        self.curr, self.track = copy.deepcopy(state)

    def get_state(self):
        return copy.deepcopy(self.state)

    def get_actions(self):
        moves = [(x, y) for x in range(-1, 2) for y in range(-1, 2) if (x != 0 or y != 0)]
        actions = []
        for row, col in moves:
            move = (self.curr[0] + row, self.curr[1] + col)
            if(move[1] > self.x - 1 or move[0] > self.y - 1 or move[0] < 0 or move[1] < 0):
                continue
            if(self.track[move[0]][move[1]] == "s"):
                print("HIT S: " + str((row, col)))
                continue
            if(self.track[move[0]][move[1]] == "0"):
                print("HIT 0: " + str((row, col)))
                continue
            actions.append((row, col))
        return actions

    def step(self, action):
        self.track[self.curr[0]][self.curr[1]] = "0"
        self.curr = (self.curr[0] + action[0], self.curr[1] + action[1])

    def heuristic(self):
        return ((self.curr[0]-self.goal[0])**2 + (self.curr[1]-self.goal[1])**2)**.5

    def print_state(self, state):
        for row in state[1]:
            print(row)

    def done(self):
        return self.curr == self.goal


class TrackGenerator:

    @staticmethod
    def connect_track(x, y):
        pass


if __name__ == "__main__":
    track = TrackEnv(10, 11)
    start_node = Node(None, track.state, 0, track.heuristic())
    run_astar(start_node, track)


    # for i in range(20):
    #     try:
    #         move = random.choice(track.get_actions())
    #         print("MOVEEE: " + str(move))
    #         track.step(move)
    #         track.print_state(track.get_state())
    #     except:
    #         print("GOTTEEEEE")
