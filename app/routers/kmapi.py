import base64
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.config import Settings, AttachedKmes
from app.dependencies import get_settings, get_lifecycle, _get_client_certificate
from app.internal.lifecycle import Lifecycle
from app.internal.requestor import get_request, post_request
from app.models.discover_requests import WalkedNode
from app.models.requests import ExternalKeysRequest

router = APIRouter(
    prefix='/kmapi',
    tags=['kmapi'],
    responses={404: {'message': 'Not found'}}
)


@router.get('/versions')
async def versions():
    return {
        'versions': [
            'v1'
        ],
        'extension': {}
    }


@router.post('/v1/ext_keys')
async def ext_keys(
        request: Request,
        data: ExternalKeysRequest,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)]
):
    # Get from where the request was coming from
    trusted_node_id = _get_client_certificate(request)[1]

    # Find the requesting trusted node
    caller_trusted_node: WalkedNode = list(filter(
        lambda node: node.trusted_node_id == trusted_node_id,
        data.discovered_network
    ))[0]

    # Find the appropriate KME
    for kme in settings.attached_kmes:
        if kme.distance != 0:
            continue

        if kme.kme_id not in caller_trusted_node.kme_ids:
            continue

        key = get_request(
            kme.kme_id,
            f'/api/v1/keys/{trusted_node_id}/dec_keys?key_ID={data.key_id}'
        )['keys'][0]

        path_to_go = data.path_to_go[1:]

        if type(data.key) is tuple:
            xor_key = data.key[0]
        else:
            xor_key = data.key

        if xor_key is not None:
            key_a = base64.b64decode(xor_key)
            key_b = base64.b64decode(key['key'])

            key['key'] = base64.b64encode(
                bytes(a ^ b for a, b in zip(key_a, key_b))
            ).decode('ascii')

        if len(path_to_go) == 0:
            return key

        next_trusted_node_id = path_to_go[0]
        next_kme: AttachedKmes | None = None

        for kme in settings.attached_kmes:
            if kme.distance != 0:
                continue

            for node in data.discovered_network:
                if node.trusted_node_id != next_trusted_node_id:
                    continue

                if kme.kme_id not in node.kme_ids:
                    continue

                next_kme = kme

                break

        next_key = get_request(next_kme.kme_id, f'/api/v1/keys/{next_trusted_node_id}/enc_keys')['keys'][0]

        # TODO: Check if xor properly works
        key_a = base64.b64decode(key['key'])
        key_b = base64.b64decode(next_key['key'])

        xor_key = base64.b64encode(
            bytes(a ^ b for a, b in zip(key_a, key_b))
        ).decode('ascii')

        resp = post_request(next_trusted_node_id, f'/api/v1/kmapi/v1/ext_keys', {
            'key_id': next_key['key_ID'],
            'key': xor_key,
            'initiator_trusted_node_id': data.initiator_trusted_node_id,
            'initiator_sae_id': data.initiator_sae_id,
            'target_trusted_node_id': data.target_trusted_node_id,
            'target_sae_node_id': data.target_sae_node_id,
            'path_to_go': path_to_go,
            'discovered_network': data.discovered_network
        })

        print(resp)

        return resp

    # Ask the KME about the key

    # Debug
