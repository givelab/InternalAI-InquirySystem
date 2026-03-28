from pydantic import BaseModel, ConfigDict


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid", validate_assignment=True)


class PaginationModel(ConfiguredBaseModel):
    count: int
    page: int
    limit: int
