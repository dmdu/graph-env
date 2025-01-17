from math import sqrt
from typing import Dict, List, Optional

import gym
import networkx as nx
import numpy as np
from graphenv.examples.tsp.tsp_preprocessor import TSPPreprocessor
from graphenv.examples.tsp.tsp_state import TSPState


class TSPNFPState(TSPState):
    def __init__(
        self,
        G: nx.Graph,
        graph_inputs: Optional[Dict] = None,
        max_num_neighbors: Optional[int] = None,
        tour: List[int] = [0],
    ) -> None:
        super().__init__(G, tour)
        if graph_inputs is None:
            graph_inputs = TSPPreprocessor(max_num_neighbors=max_num_neighbors)(G)
        self.graph_inputs = graph_inputs
        self.num_edges = len(graph_inputs["edge_weights"])

    def new(self, tour: List[int] = [0]):
        return self.__class__(self.G, graph_inputs=self.graph_inputs, tour=tour)

    @property
    def observation_space(self) -> gym.spaces.Dict:
        return gym.spaces.Dict(
            {
                "current_node": gym.spaces.Box(
                    low=0,
                    high=self.num_nodes,
                    shape=(),
                    dtype=int,
                ),
                "distance": gym.spaces.Box(
                    low=0,
                    high=sqrt(2),
                    shape=(),
                    dtype=float,
                ),
                "node_visited": gym.spaces.Box(
                    low=0,
                    high=2,
                    shape=(self.num_nodes,),
                    dtype=int,
                ),
                "edge_weights": gym.spaces.Box(
                    low=0,
                    high=sqrt(2),
                    shape=(self.num_edges,),
                    dtype=float,
                ),
                "connectivity": gym.spaces.Box(
                    low=0,
                    high=self.num_nodes,
                    shape=(self.num_edges, 2),
                    dtype=int,
                ),
            }
        )

    def _make_observation(self) -> Dict[str, np.ndarray]:
        """Return an observation.  The dict returned here needs to match
        both the self.observation_space in this class, as well as the input
        layer in tsp_model.TSPModel

        Returns:
            Observation dict.
        """
        outputs = dict(self.graph_inputs)  # not sure the shallow copy is necessary

        node_visited = np.ones(self.num_nodes, dtype=np.int64)
        node_visited[self.tour] += 1

        if len(self.tour) > 1:
            distance = self.G.get_edge_data(self.tour[-2], self.tour[-1])["weight"]
        else:
            # First node
            distance = 0.0

        outputs.update(
            {
                "current_node": self.tour[-1],
                "distance": distance,
                "node_visited": node_visited,
            }
        )
        return outputs
