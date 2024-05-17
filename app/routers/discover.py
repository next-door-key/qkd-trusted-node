import logging

from fastapi import APIRouter

from app.internal.discovery import discover_trusted_nodes
from app.models.discover_requests import DiscoverTrustedNodesRequest

logger = logging.getLogger('uvicorn.error')

router = APIRouter(
    prefix='/discover',
    tags=['discover'],
    responses={404: {'message': 'Not found'}}
)


@router.post('/trusted_nodes')
async def trusted_nodes(data: DiscoverTrustedNodesRequest):
    return {
        'walked_nodes': discover_trusted_nodes(data.walked_nodes, data.distance)
    }
