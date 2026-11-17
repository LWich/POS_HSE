from pydantic import BaseModel, ConfigDict


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class View(BaseModel):
    model_config = ConfigDict(from_attributes=True)
