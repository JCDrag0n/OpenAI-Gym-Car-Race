import os

from stable_baselines3.common.env_checker import check_env
from stable_baselines3 import PPO

from gym_car_race.SelfDriveEnv import Car, Track
from gym_car_race.training_utils import TensorboardCallback, constant_schedule, linear_schedule, run_experiment, testing, with_changes
from gym_car_race.config import cfg


def get_exp(beta):
    return lambda x : (1/beta) * math.exp(-1*x/beta)

def midline_index(obs):
    sensor_data = [entry[3] for entry in obs]    
    exp = get_exp(len(sensor_data)//4) 
    
    total = 0
    for i in range(len(sensor_data)//2):        
        diff = abs(sensor_data[i] - sensor_data[-1*i -1])
        length = sensor_data[i] + sensor_data[-1*i -1]
        percent_diff = diff/length if length else 1
        weighted_diff = exp(i) * percent_diff
        total += weighted_diff
    
    return 1 - total

@Car.reward_function
def reward_func(car):    
    # TODO: 
    # - try increasing min speed and decreasing turn radius
    # - midline index
    # - try rewards depending on action taken instead of state
    # - try including distance from end
    reward = 0
    if car.crashed:
        reward = car.config["reward"]["crash_reward"]
    elif car.has_finished:
        print('finished!')
        reward += 100
    else:
        curr = car.current_tile()
        if curr not in car.traveled:
            reward = car.config["reward"]["new_tile_reward"] * midline_index(car.sensors)
        elif car.speed <= car.config["reward"]["min_speed"]:
            reward = car.config["reward"]["same_tile_penalty"]
        else:
            reward = car.config["reward"]["same_tile_reward"]
    return reward

# Specify folders to save models/logs in

model_dir = "models"
log_dir = "logs"

os.makedirs(model_dir, exist_ok=True)

# Define tests

run_experiment(

      testing("constant learning rate with .01",            
        with_changes(
                {
                    "training": {                        
                        "learning_rate": constant_schedule(.01),
                        "log_dir": log_dir,
                    }
                }
            ),
        save_as="constant-01",
        in_dir=model_dir),
    
    testing("constant learning rate with .007",            
        with_changes(
                {
                    "training": {
                        "learning_rate": constant_schedule(.007),
                        "log_dir": log_dir,
                    }
                }
            ),
        save_as="constant-007",
        in_dir=model_dir),
    
    testing("constant learning rate with .005",            
        with_changes(
                {
                    "training": {
                        "learning_rate": constant_schedule(.005),
                        "log_dir": log_dir,
                    }
                }
            ),
        save_as="constant-005",
        in_dir=model_dir),
    
    testing("constant learning rate with .003",            
        with_changes(
                {
                    "training": {
                        "learning_rate": constant_schedule(.003),
                        "log_dir": log_dir,
                    }
                }
            ),
        save_as="constant-003",
        in_dir=model_dir),
    
    testing("constant learning rate with .001",            
        with_changes(
                {
                    "training": {
                        "learning_rate": constant_schedule(.001),
                        "log_dir": log_dir,
                    }
                }
            ),
        save_as="constant-001",
        in_dir=model_dir),

    timesteps=50000, 
    render=True,
    trials=10,
    run_after_training=False,
)
