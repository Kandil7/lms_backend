from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentBase(BaseModel):
    order_id: UUID
    amount: float = Field(ge=0)
    currency: str = Field(max_length=3)
    payment_method: str = Field(max_length=50)
    status: str = Field(max_length=20)


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=20)
    transaction_id: str | None = Field(default=None, max_length=100)
    metadata: dict | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    user_id: UUID
    amount: float
    currency: str
    payment_method: str
    status: str
    transaction_id: str | None
    metadata: dict | None = Field(default=None, validation_alias="payment_metadata")
    created_at: datetime
    updated_at: datetime


class OrderBase(BaseModel):
    user_id: UUID
    total_amount: float = Field(ge=0)
    currency: str = Field(max_length=3)
    status: str = Field(max_length=20)


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=20)
    metadata: dict | None = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    total_amount: float
    currency: str
    status: str
    metadata: dict | None = Field(default=None, validation_alias="order_metadata")
    created_at: datetime
    updated_at: datetime
    items: list["OrderItemResponse"] = Field(default_factory=list)


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OrderItemBase(BaseModel):
    order_id: UUID
    course_id: UUID
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)
    total_price: float = Field(ge=0)


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemUpdate(BaseModel):
    quantity: int | None = Field(default=None, ge=1)
    unit_price: float | None = Field(default=None, ge=0)
    total_price: float | None = Field(default=None, ge=0)
    metadata: dict | None = None


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    course_id: UUID
    quantity: int
    unit_price: float
    total_price: float
    metadata: dict | None = Field(default=None, validation_alias="item_metadata")
    created_at: datetime
    updated_at: datetime


# Update forward references
OrderResponse.model_rebuild()
