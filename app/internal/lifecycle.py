import urllib3
from fastapi import FastAPI
from uvicorn.protocols.http.httptools_impl import HttpToolsProtocol

from app.config import Settings
from app.internal.key_manager import KeyManager


class Lifecycle:
    key_manager: KeyManager | None = None

    def __init__(self, app: FastAPI, settings: Settings):
        self.app = app
        self.settings = settings

    def _verify_settings(self):
        if self.settings.min_key_size > self.settings.max_key_size:
            raise ValueError('Please define a correct range of min, max key sizes')

        if self.settings.min_key_size % 8 != 0:
            raise ValueError('Min key size must be a multiple of 8')

        if self.settings.default_key_size % 8 != 0:
            raise ValueError('Default key size must be a multiple of 8')

        if self.settings.max_key_size % 8 != 0:
            raise ValueError('Max key size must be a multiple of 8')

        if self.settings.default_key_size < self.settings.min_key_size or self.settings.default_key_size > self.settings.max_key_size:
            raise ValueError('Default key size must be in the range of min/max key sizes')

        if (
                self.settings.min_key_size <= 0 or
                self.settings.max_key_size <= 0 or
                self.settings.default_key_size <= 0 or
                self.settings.max_key_count <= 0 or
                self.settings.max_keys_per_request <= 0
        ):
            raise ValueError('All numeric config values must be above 0')

    def _configure_tls(self):
        urllib3.disable_warnings()

        # Add mTLS certificates into the request scope
        old_on_url = HttpToolsProtocol.on_url

        def new_on_url(self, url):
            old_on_url(self, url)
            self.scope['transport'] = self.transport

        HttpToolsProtocol.on_url = new_on_url

    async def before_start(self):
        self._verify_settings()
        self._configure_tls()

        self.key_manager = KeyManager(self.settings)

    async def after_landing(self):
        pass
