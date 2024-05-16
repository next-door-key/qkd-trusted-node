from functools import lru_cache
from typing import Union

import OpenSSL
from OpenSSL.crypto import X509
from fastapi import HTTPException, Request

from app.config import Settings
from app.internal.lifecycle import Lifecycle
from app.models.kme_sae_ids import KmeSaeIds


def _get_common_name_from_certificate(certificate: X509) -> str:
    common_name = tuple(filter(lambda x: x[0] == b'CN', certificate.get_subject().get_components()))

    return '' if len(common_name) == 0 else common_name[0][1].decode('utf-8')


def _get_client_certificate(request: Request) -> tuple[int, str]:
    client_cert_binary = request.scope['transport'].get_extra_info('ssl_object').getpeercert(True)
    client_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, client_cert_binary)

    return client_cert.get_serial_number(), _get_common_name_from_certificate(client_cert)


async def validate_sae_id_from_tls_cert(request: Request):
    settings = get_settings()

    request_cert_serial_number, request_sae_id = _get_client_certificate(request)

    if len(settings.attached_saes) == 0:
        raise HTTPException(status_code=400, detail='There are no attached SAEs configured')

    cert_found = False

    for sae in settings.attached_saes:
        cert = OpenSSL.crypto.load_certificate(
            type=OpenSSL.crypto.FILETYPE_PEM,
            buffer=open(sae.sae_cert, 'rb').read()
        )

        cert_sae_id = _get_common_name_from_certificate(cert)
        cert_serial_number = cert.get_serial_number()

        if (
                request_sae_id == sae.sae_id and
                request_sae_id == cert_sae_id and
                request_cert_serial_number == cert_serial_number
        ):
            cert_found = True
            break

    if not cert_found:
        raise HTTPException(
            status_code=400,
            detail='The calling SAE certificate is not found in local DB'
        )


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
