import asyncio
import base64
import json
import logging
from typing import Union

from aiormq.abc import DeliveredMessage

from app.config import Settings
from app.internal import key_generator, key_requester
from app.internal.broker import Broker
from app.models.key_container import FullKeyContainer, ActivatedKeyContainer, ActivatedKeyMetadata

logger = logging.getLogger('uvicorn.error')


class KeyManager:
    def __init__(self, settings: Settings, broker: Broker):
        self._is_master = settings.is_master
        self._broker = broker

        self._min_key_size = settings.min_key_size
        self._default_key_size = settings.default_key_size
        self._max_key_size = settings.max_key_size

        self._key_generate_timeout_in_seconds = settings.key_generation_timeout_in_seconds
        self._max_key_count = settings.max_key_count

        self._keys: list[FullKeyContainer] = []
        self._activated_keys: list[ActivatedKeyContainer] = []

    async def start_generating(self):
        if not self._is_master:
            self._broker.register_callback(self._listen_to_new_keys)
            return

        has_consumers = False
        is_key_pool_full = False

        while True:
            if self.get_key_count() >= self._max_key_count:
                await asyncio.sleep(self._key_generate_timeout_in_seconds)

                if not is_key_pool_full:
                    logger.warning(
                        f'Key pool is full, not generating any more keys ({self.get_key_count()}/{self._max_key_count}).')

                    is_key_pool_full = True

                continue
            elif is_key_pool_full:
                is_key_pool_full = False

            if not await self._broker.has_consumers():
                logger.warning('Waiting 10 seconds for 2nd KME to come online...')
                await asyncio.sleep(10)

                continue

            if not has_consumers:
                logger.info('Found the 2nd KME, starting key generation.')
                has_consumers = True

            await asyncio.sleep(self._key_generate_timeout_in_seconds)
            await self._generate_key()

    async def _generate_key(self):
        key = key_generator.generate(self._min_key_size, self._max_key_size)

        self._keys.append(key)
        await self._broadcast_key(key)

    async def _broadcast_key(self, key: FullKeyContainer):
        await self._broker.send_message({
            'type': 'new_key',
            'data': key.model_dump()
        })

    async def _broadcast_activated_key(self, key: ActivatedKeyContainer):
        await self._broker.send_message({
            'type': 'activated_key',
            'data': key.model_dump()
        })

    async def _broadcast_deactivated_key(self, key: ActivatedKeyContainer):
        await self._broker.send_message({
            'type': 'deactivated_key',
            'data': key.model_dump()
        })

    async def _listen_to_new_keys(self, message: DeliveredMessage):
        json_message = json.loads(message.body.decode())

        data = json_message['data']

        if json_message['type'] == 'new_key':
            self._keys.append(FullKeyContainer(**data))
        elif json_message['type'] == 'activated_key':
            self._activated_keys.append(ActivatedKeyContainer(**data))
        elif json_message['type'] == 'deactivated_key':
            self._remove_key(str(ActivatedKeyContainer(**data).key_ID))

    def get_key_count(self):
        return len(self._keys)

    def get_activated_key_count(self):
        return len(self._activated_keys)

    def _get_single_key(self) -> FullKeyContainer:
        return self._keys.pop()

    def _remove_key(self, key_id: str) -> bool:
        removed = False

        for i, key in enumerate(self._keys):
            if str(key.key_container.key_ID) == key_id:
                del self._keys[i]
                removed = True

        for i, key in enumerate(self._activated_keys):
            if str(key.key_ID) == key_id:
                del self._activated_keys[i]
                removed = True

        if not removed:
            logger.warning(f'Was asked to remove key from key pools, but the key did not exist, id: {key_id}')

        return removed

    def _get_key_from_key_parts(self, key_parts: list[str], size: int) -> str:
        merged_key = b''

        for part in key_parts:
            merged_key += base64.b64decode(part)

            if len(merged_key) >= size:
                return base64.b64encode(merged_key).decode('ascii')

        raise RuntimeError('This should not be possible')

    def _activate_key(
            self,
            key: FullKeyContainer,
            master_sae_id: str,
            slave_sae_id: str,
            size: int
    ) -> ActivatedKeyContainer:
        activated_key = ActivatedKeyContainer(
            master_sae_id=master_sae_id,
            slave_sae_id=slave_sae_id,
            size=size,
            key_ID=key.key_container.key_ID,
            key=self._get_key_from_key_parts(key.key_container.key_parts, size)
        )

        self._activated_keys.append(activated_key)

        return activated_key

    async def get_key(
            self,
            master_sae_id: str,
            slave_sae_id: str,
            size: int,
            do_broadcast: bool = True
    ) -> ActivatedKeyContainer:
        activated_key: ActivatedKeyContainer

        if self._is_master:
            activated_key = self._activate_key(self._get_single_key(), master_sae_id, slave_sae_id, size)

            if do_broadcast:
                await self._broadcast_activated_key(activated_key)
        else:
            activated_key = key_requester.ask_for_key(master_sae_id, slave_sae_id, size)

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

    async def deactivate_key(self, key_id: str, do_broadcast: bool = True) -> ActivatedKeyContainer:
        activated_key = self._get_activated_key_by_id(key_id)

        if self._is_master:
            self._remove_key(key_id)

            if do_broadcast:
                await self._broadcast_deactivated_key(activated_key)
        else:
            key_requester.ask_to_deactivate_key(activated_key)

            self._remove_key(key_id)

        return activated_key
