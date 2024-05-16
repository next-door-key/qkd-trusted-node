import inspect
import json
import logging
from typing import Union, Callable

import aiormq
from aiormq.abc import AbstractConnection, AbstractChannel, DeliveredMessage
from fastapi.encoders import jsonable_encoder

from app.config import Settings

logger = logging.getLogger('uvicorn.error')


class Broker:
    def __init__(self, settings: Settings):
        self._connection: Union[AbstractConnection, None] = None
        self._channel: Union[AbstractChannel, None] = None
        self._queue = None

        self._url = 'amqp://{}:{}@{}:{}/'.format(
            settings.mq_username,
            settings.mq_password,
            settings.mq_host,
            settings.mq_port
        )

        self._queue_name = settings.mq_shared_queue
        self._is_master = settings.is_master

        self.callbacks = []

    async def connect(self):
        logger.info('Connecting to broker...')

        self._connection = await aiormq.connect(self._url)
        self._channel = await self._connection.channel()

        logger.info('Connected to broker.')

        await self._declare_queue()

        if not self._is_master:
            await self._setup_listener()
            logger.info('Broker listener created. Listening to new messages.')

    async def _declare_queue(self, passive: bool = False):
        self._queue = await self._channel.queue_declare(
            queue=self._queue_name,
            passive=passive
        )

    async def disconnect(self):
        logger.warning('Closing broker connection')

        await self._connection.close()
        self._channel = None

    async def has_consumers(self) -> bool:
        if not self._is_master:
            return True

        if self._channel is None or self._channel.is_closed:
            return False

        if self._queue is None:
            return False

        await self._declare_queue(passive=True)

        return self._queue.consumer_count > 0

    async def _setup_listener(self):
        await self._channel.basic_consume(
            queue=self._queue_name,
            consumer_callback=self._receive_message
        )

    async def _receive_message(self, message: DeliveredMessage):
        try:
            json_message = json.loads(message.body.decode())

            logger.info('Received new message from broker, type: %s', json_message['type'])
        except ValueError:
            logger.info('Received new non-JSON message from broker: %s', message.body)

        try:
            for callback in self.callbacks:
                await callback(message)

            await self._channel.basic_ack(message.delivery_tag)
        except Exception:
            await self._channel.basic_nack(message.delivery_tag)

            raise

    def register_callback(self, cb: Callable):
        if not inspect.iscoroutinefunction(cb):
            raise ValueError('The given callback function must be awaitable')

        self.callbacks.append(cb)

    async def send_message(self, message: dict) -> None:
        if self._channel is None or self._channel.is_closed:
            logger.warning('Cannot send message because broker channel is closed')
            return

        await self._channel.basic_publish(routing_key=self._queue_name,
                                          body=json.dumps(jsonable_encoder(message)).encode())
