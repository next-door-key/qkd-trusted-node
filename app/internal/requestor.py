from typing import Any

import requests
from fastapi.encoders import jsonable_encoder

from app.config import AttachedKmes, AttachedTrustedNodes
from app.dependencies import get_settings


def get_request(kme_id: str, endpoint: str) -> Any:
    settings = get_settings()

    kme: AttachedKmes = list(filter(lambda kme: kme.kme_id == kme_id, settings.attached_kmes))[0]

    return requests.get(
        url=f'{kme.url}{endpoint}',
        verify=False,
        cert=(kme.sae_cert, kme.sae_key),
        timeout=5
    ).json()


def post_request(trusted_node_id: str, endpoint: str, json) -> Any:
    settings = get_settings()

    trusted_node: AttachedTrustedNodes = list(filter(
        lambda tn: tn.id == trusted_node_id,
        settings.attached_trusted_nodes)
    )[0]

    return requests.post(
        url=f'{trusted_node.url}{endpoint}',
        verify=False,
        cert=(trusted_node.cert, trusted_node.key),
        timeout=5,
        json=jsonable_encoder(json)
    ).json()
