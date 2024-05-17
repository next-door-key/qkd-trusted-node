import logging

import requests
from fastapi.encoders import jsonable_encoder

from app.dependencies import get_settings
from app.models.discover_requests import WalkedNode

logger = logging.getLogger('uvicorn.error')


def discover_trusted_nodes(
        walked_nodes: list[WalkedNode] = [],
        distance: int = 0
) -> list[WalkedNode]:
    settings = get_settings()

    walked_nodes = walked_nodes

    default_node = WalkedNode(
        trusted_node_id=settings.id,
        kme_ids=list(map(lambda kme: kme.kme_id, settings.attached_kmes)),
        sae_ids=list(map(lambda sae: sae.sae_id, settings.attached_saes)),
        trusted_node_ids=list(map(lambda node: node.id, settings.attached_trusted_nodes)),
        distance=distance
    )

    walked_nodes.append(default_node)

    for trusted_node in settings.attached_trusted_nodes:
        # Prevent infinite loops (dirty, but works)
        try:
            for walked_node in walked_nodes:
                if trusted_node.id == walked_node.trusted_node_id:
                    raise RuntimeWarning('Skip to the next node')
        except RuntimeWarning:
            continue

        try:
            response = requests.post(
                url=f'{trusted_node.url}/api/v1/discover/trusted_nodes',
                verify=False,
                cert=(trusted_node.cert, trusted_node.key),
                json={'walked_nodes': jsonable_encoder(walked_nodes), 'distance': distance + 1},
                timeout=5
            ).json()

            for walked_node in response['walked_nodes']:
                if walked_node not in jsonable_encoder(walked_nodes):
                    walked_nodes.append(WalkedNode(**walked_node))
        except requests.exceptions.ConnectionError:
            logger.error('Failed to connect to %s', trusted_node.url)

            return [default_node]
        except requests.exceptions.ReadTimeout:
            logger.error('Connection to %s timed out', trusted_node.url)

            return [default_node]

    return walked_nodes
