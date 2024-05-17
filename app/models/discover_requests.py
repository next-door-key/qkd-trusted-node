from pydantic import BaseModel


class WalkedNode(BaseModel):
    trusted_node_id: str
    kme_ids: list[str]
    sae_ids: list[str]
    trusted_node_ids: list[str]
    distance: int


class DiscoverTrustedNodesRequest(BaseModel):
    walked_nodes: list[WalkedNode] = []
    distance: int = 0
