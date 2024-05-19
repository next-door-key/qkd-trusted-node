import base64
import logging
from typing import Union

from app.config import Settings
from app.models.key_container import KeyContainer, ActivatedKeyContainer, ActivatedKeyMetadata

logger = logging.getLogger('uvicorn.error')


class KeyManager:
    def __init__(self, settings: Settings):
        self._max_key_count = settings.max_key_count

        self._activated_keys: list[ActivatedKeyContainer] = []

    def get_activated_key_count(self):
        return len(self._activated_keys)

    def _remove_key(self, key_id: str) -> bool:
        removed = False

        for i, key in enumerate(self._activated_keys):
            if str(key.key_ID) == key_id:
                del self._activated_keys[i]
                removed = True

        if not removed:
            logger.warning(f'Was asked to remove key from key pools, but the key did not exist, id: {key_id}')

        return removed

    def _activate_key(
            self,
            key: KeyContainer,
            master_sae_id: str,
            slave_sae_id: str,
            size: int
    ) -> ActivatedKeyContainer:
        activated_key = ActivatedKeyContainer(
            master_sae_id=master_sae_id,
            slave_sae_id=slave_sae_id,
            size=size,
            key_ID=key.key_container.key_ID,
            key=key.key
        )

        self._activated_keys.append(activated_key)

        return activated_key

    def add_activated_key(
            self,
            master_sae_id: str,
            slave_sae_id: str,
            key: KeyContainer
    ) -> ActivatedKeyContainer:
        activated_key = ActivatedKeyContainer(
            master_sae_id=master_sae_id,
            slave_sae_id=slave_sae_id,
            size=len(base64.b64decode(key.key)),
            key_ID=key.key_ID,
            key=key.key,
        )

        self._activated_keys.append(activated_key)

        return activated_key

    def _get_activated_key_by_id(self, key_id: str) -> ActivatedKeyContainer:
        for key in self._activated_keys:
            if str(key.key_ID) == key_id:
                return key

        raise ValueError('Key cannot be found because key_id is not found in activated keys')

    def get_activated_key_metadata(self, key_id: str) -> Union[ActivatedKeyMetadata, None]:
        try:
            key = self._get_activated_key_by_id(key_id)

            return ActivatedKeyMetadata(
                master_sae_id=key.master_sae_id,
                slave_sae_id=key.slave_sae_id,
                size=key.size,
                key_ID=key.key_ID,
            )
        except ValueError:
            return None

    def deactivate_key(self, key_id: str) -> ActivatedKeyContainer:
        activated_key = self._get_activated_key_by_id(key_id)

        self._remove_key(key_id)

        return activated_key
