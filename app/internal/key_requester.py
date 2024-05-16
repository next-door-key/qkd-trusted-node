from typing import Any

import requests

from app.config import Settings
from app.models.key_container import ActivatedKeyContainer


def _post_request(endpoint: str, data: dict) -> Any:
    settings = Settings()

    kme_address = settings.linked_to_kme
    certs = (settings.kme_cert, settings.kme_key)

    print(certs)

    return requests.post(f'{kme_address}/api/v1/{endpoint}', cert=certs, json=data, verify=False).json()


def ask_for_key(master_sae_id: str, slave_sae_id: str, size: int) -> ActivatedKeyContainer:
    response = _post_request('internal/ask_for_key', {
        'master_sae_id': master_sae_id,
        'slave_sae_id': slave_sae_id,
        'size': size
    })

    if 'detail' in response:
        raise RuntimeError(f'Something went wrong trying to deactivate a key, response: {response}')

    return ActivatedKeyContainer(
        **response['data']
    )


def ask_to_deactivate_key(activated_key: ActivatedKeyContainer):
    response = _post_request('internal/deactivate_key', {
        'key_ID': str(activated_key.key_ID),
    })

    if 'detail' in response:
        raise RuntimeError(f'Something went wrong trying to deactivate a key, response: {response}')

    return ActivatedKeyContainer(
        **response['data']
    )
