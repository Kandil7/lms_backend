from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.payments.schemas.payment import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    PaymentCreate,
    PaymentResponse,
)
from app.modules.payments.services.payment_service import PaymentService
from app.utils.pagination import PageParams, paginate

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderResponse:
    service = PaymentService(db)
    order = service.create_order(payload, current_user)
    return OrderResponse.model_validate(order)


@router.get("/orders", response_model=OrderListResponse)
def list_orders(
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderListResponse:
    service = PaymentService(db)
    orders, total = service.get_orders_by_user(current_user.id, page=page, page_size=page_size)

    result = paginate(
        [OrderResponse.model_validate(order) for order in orders],
        total,
        PageParams(page=page, page_size=page_size),
    )
    return OrderListResponse.model_validate(result)


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderResponse:
    service = PaymentService(db)
    order = service.get_order(order_id, current_user)
    return OrderResponse.model_validate(order)


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    service = PaymentService(db)
    payment = service.create_payment(payload, current_user)
    return PaymentResponse.model_validate(payment)
