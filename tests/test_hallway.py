import logging

import pytest
from graphenv.examples.hallway.hallway_model import HallwayModel, HallwayQModel
from graphenv.examples.hallway.hallway_state import HallwayState
from graphenv.graph_env import GraphEnv
from ray.rllib.agents import dqn, ppo
from ray.rllib.models import ModelCatalog
from ray.tune.registry import register_env


@pytest.fixture
def hallway_state() -> HallwayState:
    return HallwayState(5)


@pytest.fixture
def hallway_env(hallway_state) -> GraphEnv:
    return GraphEnv({"state": hallway_state, "max_num_children": 2})


def test_observation_space(hallway_state: HallwayState):
    assert hallway_state.observation_space


def test_children(hallway_state: HallwayState):
    children_list = hallway_state.children
    assert len(children_list) == 1

    children_list = children_list[0].children
    assert len(children_list) == 2


def test_terminal(hallway_state: HallwayState):
    assert hallway_state.new(0).terminal is False
    assert hallway_state.new(4).terminal is True
    # assert hallway_state.new(3, 10).terminal is True


def test_max_num_children(hallway_state: HallwayState):
    hallway_env = GraphEnv({"state": hallway_state.new(2), "max_num_children": 1})
    with pytest.raises(RuntimeError):
        hallway_env.step(0)

    hallway_env = GraphEnv({"state": hallway_state.new(2), "max_num_children": 1})
    with pytest.raises(RuntimeError):
        hallway_env.step(1)


def test_reward(hallway_state: HallwayState):
    assert hallway_state.new(5).reward > 0
    assert hallway_state.new(3).reward == -0.1


def test_graphenv_reset(hallway_env: GraphEnv):
    obs = hallway_env.reset()
    assert len(obs["action_mask"]) == 3
    assert obs["action_mask"].sum() == 1


def test_graphenv_step(hallway_env: GraphEnv):
    obs, reward, terminal, info = hallway_env.step(0)

    for _ in range(3):
        assert terminal is False
        assert reward == -0.1
        assert hallway_env.observation_space.contains(obs)
        assert hallway_env.action_space.contains(1)
        obs, reward, terminal, info = hallway_env.step(1)

    assert terminal is True
    assert reward > 0


def test_ppo(ray_init, ppo_config):

    ModelCatalog.register_custom_model("HallwayModel", HallwayModel)
    register_env("graphenv", lambda config: GraphEnv(config))

    config = {
        "env": "graphenv",
        "env_config": {
            "state": HallwayState(5),
            "max_num_children": 2,
        },
        "log_level": "DEBUG",
        "model": {
            "custom_model": "HallwayModel",
            "custom_model_config": {"hidden_dim": 32},
        },
    }
    ppo_config.update(config)
    trainer = ppo.PPOTrainer(config=ppo_config)
    trainer.train()


def test_dqn(ray_init, dqn_config, caplog):

    caplog.set_level(logging.DEBUG)

    ModelCatalog.register_custom_model("HallwayQModel", HallwayQModel)
    register_env("graphenv", lambda config: GraphEnv(config))

    config = {
        "env": "graphenv",
        "env_config": {
            "state": HallwayState(5),
            "max_num_children": 2,
        },
        "hiddens": False,
        "dueling": False,
        # "log_level": "DEBUG",
        "model": {
            "custom_model": "HallwayQModel",
            "custom_model_config": {"hidden_dim": 32},
        },
    }
    dqn_config.update(config)
    trainer = dqn.DQNTrainer(config=dqn_config)
    trainer.train()