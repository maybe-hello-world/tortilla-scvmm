from pydantic import BaseModel


class VMInfo(BaseModel):
    vmid: str
