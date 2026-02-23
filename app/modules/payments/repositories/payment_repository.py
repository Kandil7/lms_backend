from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.payments.models.payment import Order, Payment, OrderItem


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_payment_by_id(self, payment_id: UUID) -> Payment | None:
        stmt = select(Payment).where(Payment.id == payment_id)
        return self.db.scalar(stmt)

    def get_order_by_id(self, order_id: UUID) -> Order | None:
        stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        return self.db.scalar(stmt)

    def get_orders_by_user(self, user_id: UUID, *, page: int, page_size: int) -> tuple[list[Order], int]:
        total_stmt = select(func.count()).select_from(Order).where(Order.user_id == user_id)
        total = int(self.db.scalar(total_stmt) or 0)

        stmt = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size).options(selectinload(Order.items))
        
        items = list(self.db.scalars(stmt).all())
        return items, total

    def create_order(self, **fields) -> Order:
        if "metadata" in fields and "order_metadata" not in fields:
            fields["order_metadata"] = fields.pop("metadata")
        order = Order(**fields)
        self.db.add(order)
        self.db.flush()
        self.db.refresh(order)
        return order

    def create_payment(self, **fields) -> Payment:
        if "metadata" in fields and "payment_metadata" not in fields:
            fields["payment_metadata"] = fields.pop("metadata")
        payment = Payment(**fields)
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)
        return payment

    def create_order_item(self, **fields) -> OrderItem:
        if "metadata" in fields and "item_metadata" not in fields:
            fields["item_metadata"] = fields.pop("metadata")
        item = OrderItem(**fields)
        self.db.add(item)
        self.db.flush()
        self.db.refresh(item)
        return item

    def update_order(self, order: Order, **fields) -> Order:
        if "metadata" in fields and "order_metadata" not in fields:
            fields["order_metadata"] = fields.pop("metadata")
        for key, value in fields.items():
            setattr(order, key, value)
        self.db.add(order)
        self.db.flush()
        self.db.refresh(order)
        return order

    def update_payment(self, payment: Payment, **fields) -> Payment:
        if "metadata" in fields and "payment_metadata" not in fields:
            fields["payment_metadata"] = fields.pop("metadata")
        for key, value in fields.items():
            setattr(payment, key, value)
        self.db.add(payment)
        self.db.flush()
        self.db.refresh(payment)
        return payment

    def delete_order(self, order: Order) -> None:
        self.db.delete(order)
        self.db.flush()
