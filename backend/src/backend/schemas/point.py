from pydantic import BaseModel, ConfigDict, Field


class WorkingHoursSlot(BaseModel):
    days: list[int] = Field(description="0=Пн … 6=Вс")
    open: str
    close: str


class PointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    address: str
    schedule: list[WorkingHoursSlot]
    schedule_label: str
    phone: str
    is_active: bool
