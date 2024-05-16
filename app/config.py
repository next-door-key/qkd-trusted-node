import argparse
from typing import Any, Dict, Tuple, Type

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    JsonConfigSettingsSource,
)


class Settings(BaseSettings):
    _parser = argparse.ArgumentParser()

    _parser.add_argument('-p', '--port', type=int, default=8000, help='Port to bind on')
    _parser.add_argument('-r', '--reload', type=bool, default=False, help='Reload when changes found')
    _parser.add_argument('-s', '--settings', type=str, default='settings.json', help='Settings file name')

    _args = _parser.parse_args()

    model_config = SettingsConfigDict(json_file=_args.settings, json_file_encoding='utf-8')

    is_master: bool = False

    kme_id: str
    attached_sae_id: str

    linked_to_kme: str
    linked_kme_id: str
    linked_sae_id: str

    min_key_size: int = 64
    max_key_size: int = 1024
    default_key_size: int = 128
    max_key_count: int = 1000
    max_keys_per_request: int = 128

    key_generation_timeout_in_seconds: int = 2

    mq_host: str = 'localhost'
    mq_port: int = 5672
    mq_username: str = 'guest'
    mq_password: str = 'guest'
    mq_shared_queue: str

    ca_file: str
    kme_cert: str
    kme_key: str
    sae_cert: str

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: Type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return init_settings, env_settings, dotenv_settings, JsonConfigSettingsSource(settings_cls)
