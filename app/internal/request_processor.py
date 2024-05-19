from uuid import UUID

from fastapi import HTTPException

from app.config import Settings
from app.internal.discovery import discover_trusted_nodes
from app.internal.lifecycle import Lifecycle
from app.internal.path_finder import find_shortest_path
from app.internal.requestor import get_request, post_request
from app.models.discover_requests import WalkedNode
from app.models.key_container import KeyContainer


def _get_node_by_id(trusted_nodes: list[WalkedNode], trusted_node_id: str) -> WalkedNode:
    return list(filter(
        lambda node: node.trusted_node_id == trusted_node_id,
        trusted_nodes)
    )[0]


def get_encryption_keys(
        master_sae_id: str,
        slave_sae_id: str,
        number: int,
        size: int,
        settings: Settings,
        lifecycle: Lifecycle
):
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

    key_containers = []

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

            response = get_request(
                kme.kme_id,
                f'/api/v1/keys/{trusted_node_id}/enc_keys?number={number}&size={size}'
            )

            for key in response['keys']:
                print(f'key to send: {key["key_ID"]}, {key["key"][:20]}')

                lifecycle.key_manager.add_activated_key(master_sae_id, slave_sae_id, KeyContainer(**key))

                response = post_request(trusted_node_id, f'/api/v1/kmapi/v1/ext_keys', {
                    'first_key_id': key['key_ID'],
                    'key_id': key['key_ID'],
                    'initiator_trusted_node_id': settings.id,
                    'initiator_sae_id': master_sae_id,
                    'target_trusted_node_id': point_b.trusted_node_id,
                    'target_sae_node_id': slave_sae_id,
                    'path_to_go': path_to_go[1:],
                    'discovered_network': trusted_nodes
                })

                key_containers.append(response)

        return {'keys': key_containers}

    raise HTTPException(
        status_code=400,
        detail='Unable to find proper path to nodes, probably configuration error'
    )


def get_decryption_keys(
        master_sae_id: str,
        slave_sae_id: str,
        key_ids: list[UUID],
        settings: Settings,
        lifecycle: Lifecycle
):
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
        if trusted_node.trusted_node_id != settings.id and master_sae_id in trusted_node.sae_ids:
            point_b = trusted_node
            break

    if not point_b:
        raise HTTPException(status_code=400, detail='The given master_sae_id cannot be routed to')

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

            for key_id in key_ids:
                key_id = str(key_id)

                print(f'key to deactivate: {key_id}')

                lifecycle.key_manager.deactivate_key(key_id)

            response = post_request(trusted_node_id, f'/api/v1/kmapi/v1/void', {
                'key_ids': key_ids,
                'initiator_sae_id': master_sae_id,
                'target_sae_id': slave_sae_id,
                'path_to_go': path_to_go[1:],
                'discovered_network': trusted_nodes
            })

            return {'keys': response}

    raise HTTPException(
        status_code=400,
        detail='Unable to find proper path to nodes, probably configuration error'
    )
