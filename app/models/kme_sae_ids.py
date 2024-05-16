from pydantic import BaseModel


class KmeSaeIds(BaseModel):
    master_kme_id: str
    slave_kme_id: str
    master_sae_id: str
    slave_sae_id: str
