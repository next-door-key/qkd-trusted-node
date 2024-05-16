from typing import Union
from uuid import UUID

from pydantic import BaseModel


class KeyIDContainer(BaseModel):
    key_ID: UUID
    key_ID_extension: Union[dict, None] = None


class KeyContainer(BaseModel):
    key_ID: UUID
    key: str


class KeyPartsContainer(BaseModel):
    key_ID: UUID
    key_parts: list


class FullKeyContainer(BaseModel):
    key_container: KeyPartsContainer


class ActivatedKeyContainer(BaseModel):
    master_sae_id: str
    slave_sae_id: str
    size: int
    key_ID: UUID
    key: str


class ActivatedKeyMetadata(BaseModel):
    master_sae_id: str
    slave_sae_id: str
    size: int
    key_ID: UUID
