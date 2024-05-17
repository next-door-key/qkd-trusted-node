from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import Settings
from app.dependencies import get_settings, get_lifecycle, validate_sae_id_from_tls_cert, _get_client_certificate
from app.internal.discovery import discover_trusted_nodes
from app.internal.lifecycle import Lifecycle
from app.internal.path_finder import find_shortest_path
from app.internal.requestor import get_request, post_request
from app.models.discover_requests import WalkedNode
from app.models.requests import PostEncryptionKeysRequest, GetEncryptionKeysRequest, GetDecryptionKeysRequest, \
    PostDecryptionKeysRequest

router = APIRouter(
    prefix='/keys',
    tags=['keys'],
    dependencies=[Depends(validate_sae_id_from_tls_cert)],
    responses={404: {'message': 'Not found'}}
)


@router.get('/{slave_sae_id}/status')
async def status(
        request: Request,
        slave_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)]
):
    trusted_nodes = discover_trusted_nodes()

    slave_kme_id = None

    for trusted_node in trusted_nodes:
        if trusted_node.trusted_node_id != settings.id and slave_sae_id in trusted_node.sae_ids:
            slave_kme_id = trusted_node.trusted_node_id
            break

    if not slave_kme_id:
        raise HTTPException(status_code=400, detail='The given slave_sae_id cannot be routed to')

    master_sae_id = _get_client_certificate(request)[1]

    return {
        'source_KME_ID': settings.id,
        'target_KME_ID': slave_kme_id,
        'master_SAE_ID': master_sae_id,
        'slave_SAE_ID': slave_sae_id,
        'key_size': settings.default_key_size,
        'stored_key_count': 0,
        'max_key_count': settings.max_key_count,
        'max_key_per_request': settings.max_keys_per_request,
        'max_key_size': settings.max_key_size,
        'min_key_size': settings.min_key_size,
        'max_SAE_ID_count': 0,
    }


def _get_node_by_id(trusted_nodes: list[WalkedNode], trusted_node_id: str) -> WalkedNode:
    return list(filter(
        lambda node: node.trusted_node_id == trusted_node_id,
        trusted_nodes)
    )[0]


@router.get('/{slave_sae_id}/enc_keys')
async def get_encryption_keys(
        request: Request,
        slave_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)],
        query: GetEncryptionKeysRequest = Depends()
):
    master_sae_id = _get_client_certificate(request)[1]

    # Get list of all trusted nodes
    trusted_nodes = discover_trusted_nodes()

    point_a: WalkedNode = list(filter(
        lambda node: node.trusted_node_id == settings.id and node.distance == 0,
        trusted_nodes)
    )[0]

    if not point_a:
        raise HTTPException(status_code=400, detail='This should not have happened')

    point_b: WalkedNode | None = None

    for trusted_node in trusted_nodes:
        if trusted_node.trusted_node_id != settings.id and slave_sae_id in trusted_node.sae_ids:
            point_b = trusted_node
            break

    if not point_b:
        raise HTTPException(status_code=400, detail='The given slave_sae_id cannot be routed to')

    # Find the path of the least distance
    path_to_go = find_shortest_path(
        point_a_id=point_a.trusted_node_id,
        point_b_id=point_b.trusted_node_id,
        trusted_nodes=trusted_nodes
    )

    # Check all the statuses (maybe) to ensure reliable delivery
    for trusted_node_id in path_to_go:
        if trusted_node_id == settings.id:
            continue

        trusted_node = _get_node_by_id(trusted_nodes, trusted_node_id)

        for kme in settings.attached_kmes:
            # Select attached KME
            if kme.distance != 0:
                continue

            # Select only that KME that is possible to be accessed by the other trusted node
            if kme.kme_id not in trusted_node.kme_ids:
                continue

            response = get_request(kme.kme_id, f'/api/v1/keys/{trusted_node_id}/enc_keys')

            print(response)

            resp = post_request(trusted_node_id, f'/api/v1/kmapi/v1/ext_keys', {
                'key_id': response['keys'][0]['key_ID'],
                'initiator_trusted_node_id': settings.id,
                'initiator_sae_id': master_sae_id,
                'target_trusted_node_id': point_b.trusted_node_id,
                'target_sae_node_id': slave_sae_id,
                'path_to_go': path_to_go[1:],
                'discovered_network': trusted_nodes
            })

            return resp

            # Prevent multiple requests (just in case)
            break

        break

    return {
        'point_a': point_a,
        'point_b': point_b,
        'path_to_go': path_to_go,
    }

    # For each hop:
    #   1) TN1 -> KME1, /enc_keys
    #   2) TN1 -> TN2, /notify w/ key ID
    #   3) TN2 -> KME1, /dec_keys
    #   4) If there are hops remaining, continue, else return key
    #   5) TN2 -> KME2, /enc_keys
    #   6) TN2 -> TN3, /notify w/ key ID w/ key (KME1 key XOR KME2 key)
    #   7) TN3 -> KME2, /dec_keys
    #   8) TN3 -> get raw key from XOR'd key with the KME2 key
    #   9) If there are hops remaining, repeat, else return key

    pass


@router.post('/{slave_sae_id}/enc_keys')
async def post_encryption_keys(
        slave_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)],
        data: PostEncryptionKeysRequest
):
    pass


@router.get('/{master_sae_id}/dec_keys')
async def get_decryption_keys(
        master_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)],
        query: GetDecryptionKeysRequest = Depends()
):
    pass


@router.post('/{master_sae_id}/dec_keys')
async def get_decryption_keys(
        master_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)],
        data: PostDecryptionKeysRequest
):
    pass
