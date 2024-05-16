from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings
from app.dependencies import get_settings, get_lifecycle
from app.internal.lifecycle import Lifecycle
from app.models.requests import PostAskForKeyRequest, PostAskForKeyDeactivationRequest

router = APIRouter(
    prefix='/internal',
    tags=['internal'],
    responses={404: {'message': 'Not found'}}
)


@router.post('/ask_for_key')
async def ask_for_key(
        data: PostAskForKeyRequest,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)]
):
    # Masters do not use this method but use the broker directly, slaves are only allowed to interact with this endpoint
    if not settings.is_master:
        raise HTTPException(status_code=400, detail='This endpoint can only be used by slaves')

    # Validate if the SAE ids are correctly given
    if data.master_sae_id != settings.attached_sae_id and data.master_sae_id != settings.linked_sae_id:
        raise HTTPException(status_code=400, detail='The given master_sae_id is not found.')

    if data.slave_sae_id != settings.attached_sae_id and data.slave_sae_id != settings.linked_sae_id:
        raise HTTPException(status_code=400, detail='The given slave_sae_id is not found.')

    return {'data': await lifecycle.key_manager.get_key(
        master_sae_id=data.master_sae_id,
        slave_sae_id=data.slave_sae_id,
        size=data.size,
        do_broadcast=False
    )}


@router.post('/deactivate_key')
async def deactivate_key(
        data: PostAskForKeyDeactivationRequest,
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)]
):
    # Masters do not use this method but use the broker directly, slaves are only allowed to interact with this endpoint
    if not settings.is_master:
        raise HTTPException(status_code=400, detail='This endpoint can only be used by slaves')

    return {'data': await lifecycle.key_manager.deactivate_key(
        key_id=str(data.key_ID),
        do_broadcast=False
    )}


@router.get('/key_stores')
async def get_key_store(
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)]
):
    return {
        'keys': lifecycle.key_manager._keys,
        'activated_keys': lifecycle.key_manager._activated_keys,
        'settings': settings
    }
