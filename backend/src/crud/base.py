from pydantic import BaseModel


class BaseQuery(BaseModel):
    limit: int = 50
    page: int = 1
