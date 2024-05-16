import base64
import os
import uuid

from app.models.key_container import FullKeyContainer, KeyPartsContainer


def _generate_key_part(size: int) -> str:
    return base64.b64encode(os.urandom(size)).decode('ascii')


def generate(min_size: int, max_size: int) -> FullKeyContainer:
    key_parts = []

    for i in range(min_size, max_size, 8):
        key_parts.append(_generate_key_part(8))

    return FullKeyContainer(
        key_container=KeyPartsContainer(
            key_ID=str(uuid.uuid4()),
            key_parts=key_parts,
        )
    )
