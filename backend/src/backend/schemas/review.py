from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_name: str
    car_model: str
    text: str
    point_id: int | None
    created_at: datetime
