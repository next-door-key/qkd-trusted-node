from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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
