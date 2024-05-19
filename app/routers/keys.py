from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import Settings
from app.dependencies import get_settings, get_lifecycle, validate_sae_id_from_tls_cert, _get_client_certificate
from app.internal import request_processor
from app.internal.discovery import discover_trusted_nodes
from app.internal.lifecycle import Lifecycle
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


@router.get('/{slave_sae_id}/enc_keys')
async def get_encryption_keys(
        request: Request,
        slave_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)],
        query: GetEncryptionKeysRequest = Depends()
):
    master_sae_id = _get_client_certificate(request)[1]

    return request_processor.get_encryption_keys(
        master_sae_id=master_sae_id,
        slave_sae_id=slave_sae_id,
        number=query.number,
        size=query.size,
        settings=settings,
        lifecycle=lifecycle,
    )


@router.post('/{slave_sae_id}/enc_keys')
async def post_encryption_keys(
        request: Request,
        slave_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)],
        data: PostEncryptionKeysRequest
):
    master_sae_id = _get_client_certificate(request)[1]

    return request_processor.get_encryption_keys(
        master_sae_id=master_sae_id,
        slave_sae_id=slave_sae_id,
        number=data.number,
        size=data.size,
        settings=settings,
        lifecycle=lifecycle,
    )


@router.get('/{master_sae_id}/dec_keys')
async def get_decryption_keys(
        request: Request,
        master_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)],
        query: GetDecryptionKeysRequest = Depends()
):
    slave_sae_id = _get_client_certificate(request)[1]

    return request_processor.get_decryption_keys(
        master_sae_id=master_sae_id,
        slave_sae_id=slave_sae_id,
        key_ids=[query.key_ID],
        settings=settings,
        lifecycle=lifecycle,
    )


@router.post('/{master_sae_id}/dec_keys')
async def get_decryption_keys(
        request: Request,
        master_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)],
        data: PostDecryptionKeysRequest
):
    slave_sae_id = _get_client_certificate(request)[1]

    return request_processor.get_decryption_keys(
        master_sae_id=master_sae_id,
        slave_sae_id=slave_sae_id,
        key_ids=list(map(lambda key: key.key_ID, data.key_IDs)),
        settings=settings,
        lifecycle=lifecycle,
    )
