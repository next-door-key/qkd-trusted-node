from typing import Annotated

from fastapi import APIRouter, Depends

from app.config import Settings
from app.dependencies import get_settings, get_lifecycle
from app.internal.lifecycle import Lifecycle

router = APIRouter(
    prefix='/internal',
    tags=['internal'],
    responses={404: {'message': 'Not found'}}
)


@router.get('/key_stores')
async def get_key_store(
        settings: Annotated[Settings, Depends(get_settings)],
        lifecycle: Annotated[Lifecycle, Depends(get_lifecycle)]
):
    return {
        'activated_keys': lifecycle.key_manager._activated_keys,
    }
