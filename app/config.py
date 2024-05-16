import argparse
from typing import Any, Dict, Tuple, Type

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    JsonConfigSettingsSource,
)


class AttachedKmes(BaseModel):
    url: str
    kme_id: str
    kme_cert: str
    sae_cert: str
    sae_key: str


class AttachedSaes(BaseModel):
    sae_id: str
    sae_cert: str


class Settings(BaseSettings):
    _parser = argparse.ArgumentParser()

    _parser.add_argument('-p', '--port', type=int, default=8000, help='Port to bind on')
    _parser.add_argument('-r', '--reload', type=bool, default=False, help='Reload when changes found')
    _parser.add_argument('-s', '--settings', type=str, default='settings.json', help='Settings file name')

    _args = _parser.parse_args()

    model_config = SettingsConfigDict(json_file=_args.settings, json_file_encoding='utf-8')

    id: str

    server_cert_file: str
    server_key_file: str
    ca_file: str

    attached_kmes: list[AttachedKmes]
    attached_saes: list[AttachedSaes]

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
