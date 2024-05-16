from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import Settings
from app.dependencies import get_settings, get_lifecycle, validate_sae_id_from_tls_cert
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
        slave_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)]
):
    pass


@router.get('/{slave_sae_id}/enc_keys')
async def get_encryption_keys(
        slave_sae_id: str,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)],
        query: GetEncryptionKeysRequest = Depends()
):
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
