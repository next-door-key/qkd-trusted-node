from app.internal.djikstras_algorithm import dijkstra_algorithm
from app.internal.graph import Graph
from app.models.discover_requests import WalkedNode


def find_shortest_path(point_a_id: str, point_b_id: str, trusted_nodes: list[WalkedNode]):
    init_graph = {}

    for trusted_node in trusted_nodes:
        init_graph[trusted_node.trusted_node_id] = {}

    for trusted_node in trusted_nodes:
        for tn_id in trusted_node.trusted_node_ids:
            init_graph[trusted_node.trusted_node_id][tn_id] = trusted_node.distance

    graph = Graph(list(map(lambda node: node.trusted_node_id, trusted_nodes)), init_graph)

    previous_nodes, shortest_path = dijkstra_algorithm(graph=graph, start_node=point_a_id)

    path = []
    node = point_b_id

    while node != point_a_id:
        path.append(node)
        node = previous_nodes[node]

    # Add the start node manually
    path.append(point_a_id)

    return list(reversed(path))
