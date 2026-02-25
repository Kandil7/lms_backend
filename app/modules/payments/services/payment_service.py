from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import Role
from app.modules.payments.repositories.payment_repository import PaymentRepository
from app.modules.payments.schemas.payment import OrderCreate, OrderUpdate, PaymentCreate, PaymentUpdate


class PaymentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PaymentRepository(db)

    def get_order(self, order_id: UUID, current_user):
        order = self.repo.get_order_by_id(order_id)
        if not order:
            raise NotFoundException("Order not found")
        
        if current_user.role != Role.ADMIN.value and order.user_id != current_user.id:
            raise ForbiddenException("Not authorized to access this order")
            
        return order

    def get_orders_by_user(self, user_id: UUID, *, page: int, page_size: int):
        return self.repo.get_orders_by_user(user_id, page=page, page_size=page_size)

    def create_order(self, payload: OrderCreate, current_user):
        if current_user.role not in {Role.ADMIN.value, Role.INSTRUCTOR.value, Role.STUDENT.value}:
            raise ForbiddenException("Only students, instructors, or admins can create orders")

        # Validate that user exists
        if payload.user_id != current_user.id:
            if current_user.role != Role.ADMIN.value:
                raise ForbiddenException("Cannot create order for another user")
        
        order = self.repo.create_order(
            user_id=payload.user_id,
            total_amount=payload.total_amount,
            currency=payload.currency,
            status=payload.status,
        )
        self._commit()
        self.db.refresh(order)
        return order

    def create_payment(self, payload: PaymentCreate, current_user):
        # Get order to validate it exists and belongs to user
        order = self.repo.get_order_by_id(payload.order_id)
        if not order:
            raise NotFoundException("Order not found")
        
        if current_user.role != Role.ADMIN.value and order.user_id != current_user.id:
            raise ForbiddenException("Not authorized to create payment for this order")
        
        payment = self.repo.create_payment(
            order_id=payload.order_id,
            user_id=order.user_id,
            amount=payload.amount,
            currency=payload.currency,
            payment_method=payload.payment_method,
            status=payload.status,
        )
        self._commit()
        self.db.refresh(payment)
        return payment

    def update_order(self, order_id: UUID, payload: OrderUpdate, current_user):
        order = self.repo.get_order_by_id(order_id)
        if not order:
            raise NotFoundException("Order not found")
        
        if current_user.role != Role.ADMIN.value and order.user_id != current_user.id:
            raise ForbiddenException("Not authorized to update this order")
        
        fields = payload.model_dump(exclude_unset=True)
        if "metadata" in fields and "order_metadata" not in fields:
            fields["order_metadata"] = fields.pop("metadata")
        order = self.repo.update_order(order, **fields)
        self._commit()
        self.db.refresh(order)
        return order

    def update_payment(self, payment_id: UUID, payload: PaymentUpdate, current_user):
        payment = self.repo.get_payment_by_id(payment_id)
        if not payment:
            raise NotFoundException("Payment not found")
        
        # Get associated order to check permissions
        order = self.repo.get_order_by_id(payment.order_id)
        if not order:
            raise NotFoundException("Associated order not found")
        
        if current_user.role != Role.ADMIN.value and order.user_id != current_user.id:
            raise ForbiddenException("Not authorized to update this payment")
        
        fields = payload.model_dump(exclude_unset=True)
        if "metadata" in fields and "payment_metadata" not in fields:
            fields["payment_metadata"] = fields.pop("metadata")
        payment = self.repo.update_payment(payment, **fields)
        self._commit()
        self.db.refresh(payment)
        return payment

    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
