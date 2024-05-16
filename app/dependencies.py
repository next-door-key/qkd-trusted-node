import os
from functools import lru_cache
from typing import Union

import OpenSSL
from fastapi import HTTPException, Request

from app.config import Settings
from app.internal.lifecycle import Lifecycle
from app.models.kme_sae_ids import KmeSaeIds


async def validate_sae_id_from_tls_cert(request: Request):
    settings = get_settings()

    client_cert_binary = request.scope['transport'].get_extra_info('ssl_object').getpeercert(True)
    client_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, client_cert_binary)

    common_name = tuple(filter(lambda x: x[0] == b'CN', client_cert.get_subject().get_components()))
    client_cert_serial_number = client_cert.get_serial_number()

    request_sae_id = '' if len(common_name) == 0 else common_name[0][1].decode('utf-8')

    sae_cert = OpenSSL.crypto.load_certificate(
        OpenSSL.crypto.FILETYPE_PEM,
        open(os.getenv('SAE_CERT'), 'rb').read()
    )

    sae_id_from_cert = tuple(filter(lambda x: x[0] == b'CN', sae_cert.get_subject().get_components()))
    sae_id_from_cert = '' if len(sae_id_from_cert) == 0 else sae_id_from_cert[0][1].decode('utf-8')

    if request_sae_id != settings.attached_sae_id or request_sae_id != sae_id_from_cert:
        raise HTTPException(status_code=400,
                            detail='The calling SAE certificate id does not match the stored certificate')

    if sae_cert.get_serial_number() != client_cert_serial_number:
        raise HTTPException(status_code=400,
                            detail='The calling SAE certificate serial number does not match the stored certificate')


def get_kme_and_sae_ids_from_slave_id(slave_sae_id: str) -> KmeSaeIds:
    settings = get_settings()

    if slave_sae_id == settings.attached_sae_id:
        master_kme_id = settings.linked_kme_id
        slave_kme_id = settings.kme_id

        master_sae_id = settings.linked_sae_id
    elif slave_sae_id == settings.linked_sae_id:
        master_kme_id = settings.kme_id
        slave_kme_id = settings.linked_kme_id

        master_sae_id = settings.attached_sae_id
    else:
        raise HTTPException(status_code=400, detail=f'Linked KME with linked SAE ID {slave_sae_id} is not found')

    return KmeSaeIds(
        master_kme_id=master_kme_id,
        slave_kme_id=slave_kme_id,
        master_sae_id=master_sae_id,
        slave_sae_id=slave_sae_id
    )


def get_kme_and_sae_ids_from_master_id(master_sae_id: str) -> KmeSaeIds:
    settings = get_settings()

    if master_sae_id == settings.linked_sae_id:
        master_kme_id = settings.linked_kme_id
        slave_kme_id = settings.kme_id

        slave_sae_id = settings.attached_sae_id
    elif master_sae_id == settings.attached_sae_id:
        master_kme_id = settings.kme_id
        slave_kme_id = settings.linked_kme_id

        slave_sae_id = settings.linked_sae_id
    else:
        raise HTTPException(status_code=400, detail=f'Linked KME with linked SAE ID {master_sae_id} is not found')

    return KmeSaeIds(
        master_kme_id=master_kme_id,
        slave_kme_id=slave_kme_id,
        master_sae_id=master_sae_id,
        slave_sae_id=slave_sae_id
    )


@lru_cache
def get_settings():
    return Settings()


def get_lifecycle(request: Request) -> Union[Lifecycle, None]:
    return request.app.lifecycle
