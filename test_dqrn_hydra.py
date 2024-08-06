"""
Stopped: MinigridConv is to complex. It reads an image
We should use a simpler network.

Also, the shape parameter does not exist in the observation.
  observation_space is a dictionary event though we probably don't want it to be
"""
from uuid import uuid1

import gym
import hydra
from gym.wrappers import RecordEpisodeStatistics
from omegaconf import DictConfig, OmegaConf

from rm_marl.agent import RewardMachineAgent, NoRMAgent
from rm_marl.envs.gym_subgoal_automata_wrapper import GymSubgoalAutomataAdapter, \
    OfficeWorldOfficeLabelingFunctionWrapper, OfficeWorldCoffeeLabelingFunctionWrapper
from rm_marl.envs.wrappers import NoisyLabelingFunctionComposer, RewardMachineWrapper, AutomataWrapper
from rm_marl.rm_transition.prob_rm_transitioner import ProbRMTransitioner
from rm_marl.algo.dqrn.model import DQRN
from rm_marl.trainer import Trainer

run_config = {
    'training': True, 'total_episodes': 150000, 'log_freq': 1, 'log_dir': 'logs', 'testing_freq': 1000,
    'greedy': True, 'synchronize': False, 'counterfactual_update': False, 'recording_freq': 1000,
    'no_display': True, 'seed': 123, 'name': 'test_dqrn', 'extra_debug_information': True,
    'num_envs': 10, 'checkpoint_freq': 10000, 'restart_from_checkpoint': False, 'use_rs': True,
    'rm_learner_kws': {'edge_cost': 2, 'n_phi_cost': 1, 'ex_penalty_multiplier': 2, 'min_penalty': 2,
                       'cross_entropy_threshold': 0.8, 'use_cross_entropy': True}, 'edge_cost': 2,
    'n_phi_cost': 2, 'ex_penalty_multiplier': 1
}
env_config = {}


# important - counterfactual_update needs to be false

def _get_base_env():
    seed = 123
    max_episode_length = 100
    use_restricted_observables = True
    env = gym.make("gym_subgoal_automata:OfficeWorldDeliverCoffee-v0",
                   params={"generation": "custom", "environment_seed": seed, "hide_state_variables": True})
    env = GymSubgoalAutomataAdapter(env, agent_id="A1", render_mode="rgb_array",  # type: ignore
                                    max_episode_length=max_episode_length,
                                    use_restricted_observables=use_restricted_observables)
    office_l = OfficeWorldOfficeLabelingFunctionWrapper(env, sensor_true_confidence=1, sensor_false_confidence=1)
    coffee_l = OfficeWorldCoffeeLabelingFunctionWrapper(env, sensor_true_confidence=1, sensor_false_confidence=1)
    env = NoisyLabelingFunctionComposer([coffee_l, office_l])

    env = RecordEpisodeStatistics(env)  # type: ignore

    return env


@hydra.main(version_base=None, config_path="new_conf", config_name="dqrn")
def run(cfg: DictConfig):
    run_config["name"] = f"{run_config['name']}/{uuid1()}"

    print(cfg)
    # Quick fix to log the hyperparameters
    run_config.update(OmegaConf.to_container(cfg))
    env = _get_base_env()
    print(run_config)

    algo = DQRN(env.observation_space, env.action_space, **cfg)
    agent = NoRMAgent(agent_id="A1", algo=algo)
    agent_dict = {agent.agent_id: agent}
    env_dict = {"E1": env}

    trainer = Trainer(env_dict, agent_dict)
    return trainer.run(run_config)


if __name__ == '__main__':
    run()
