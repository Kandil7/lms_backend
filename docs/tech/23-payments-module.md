# Complete Payments Module Documentation

This document provides comprehensive documentation for the Payments module in the LMS Backend system.

---

## Table of Contents

1. [Payment Models](#1-payment-models)
2. [Payment Enums](#2-payment-enums)
3. [Payment Entity](#3-payment-entity)
4. [Subscription Entity](#4-subscription-entity)
5. [Webhook Events](#5-webhook-events)
6. [Payment Flow](#6-payment-flow)

---

## 1. Payment Models

**Location:** `app/modules/payments/models.py`

The payments module includes three main models:
- Payment
- Subscription
- PaymentWebhookEvent

---

## 2. Payment Enums

### PaymentStatus

```python
class PaymentStatus(str, Enum):
    PENDING = "pending"      # Payment initiated, not completed
    SUCCEEDED = "succeeded" # Payment completed successfully
    FAILED = "failed"       # Payment failed
    REFUNDED = "refunded"   # Payment was refunded
```

### SubscriptionStatus

```python
class SubscriptionStatus(str, Enum):
    TRIAL = "trial"         # Free trial period
    ACTIVE = "active"       # Subscription is active
    PAST_DUE = "past_due"    # Payment overdue
    CANCELED = "canceled"   # Subscription canceled
    INCOMPLETE = "incomplete" # Setup not completed
```

### PaymentType

```python
class PaymentType(str, Enum):
    ONE_TIME = "one_time"   # One-time payment
    RECURRING = "recurring" # Recurring subscription
    TRIAL = "trial"         # Free trial
```

---

## 3. Payment Entity

### Database Schema

```python
class Payment(Base):
    __tablename__ = "payments"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, index=True)
    
    # Stripe IDs
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_invoice_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    
    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    enrollment_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("enrollments.id"), nullable=True, index=True)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True, index=True)
    
    # Payment details
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EGP")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING, index=True)
    
    # Plan information
    plan_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    plan_price_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Amount breakdown
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Metadata
    payment_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="payments")
    enrollment = relationship("Enrollment", backref="payments")
    subscription = relationship("Subscription", back_populates="payments")
    
    # Properties
    @property
    def is_successful(self) -> bool:
        return self.status == PaymentStatus.SUCCEEDED
    
    @property
    def is_recurring(self) -> bool:
        return self.payment_type == PaymentType.RECURRING
```

### Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| ix_payments_user_created_at | user_id, created_at | User payment history |
| ix_payments_status_created_at | status, created_at | Payment analytics |
| ix_payments_subscription_created_at | subscription_id, created_at | Subscription payments |

---

## 4. Subscription Entity

### Database Schema

```python
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, index=True)
    
    # Stripe IDs
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    
    # Foreign key
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Subscription details
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    plan_price_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.INCOMPLETE, index=True)
    
    # Period tracking
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    courses_accessed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_usage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Metadata
    subscription_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="subscriptions")
    payments = relationship("Payment", back_populates="subscription")
    
    # Properties
    @property
    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE
    
    @property
    def days_remaining(self) -> int:
        if not self.current_period_end:
            return 0
        end = self.current_period_end
        if end.tzinfo is None:
            end = end.replace(tzinfo=UTC)
        return max(0, (end - datetime.now(UTC)).days)
```

### Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| ix_subscriptions_user_status | user_id, status | User subscriptions |
| ix_subscriptions_period_end | current_period_end | Expiring subscriptions |

---

## 5. Webhook Events

### Database Schema

```python
class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, index=True)
    
    # Stripe event data
    stripe_event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    
    # Event payload
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

### Supported Event Types

| Event Type | Description |
|------------|-------------|
| payment_intent.succeeded | Payment completed |
| payment_intent.payment_failed | Payment failed |
| customer.subscription.created | Subscription created |
| customer.subscription.updated | Subscription updated |
| customer.subscription.deleted | Subscription canceled |
| invoice.paid | Invoice paid |
| invoice.payment_failed | Invoice payment failed |

---

## 6. Payment Flow

### One-Time Payment Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ONE-TIME PAYMENT FLOW                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. User initiates payment                                         │
│     └─> Create Payment record (pending)                            │
│                                                                     │
│  2. Redirect to payment gateway                                    │
│     └─> Stripe Checkout / Paymob / MyFatoorah                      │
│                                                                     │
│  3. Payment processing                                             │
│     └─> User completes payment on gateway                          │
│                                                                     │
│  4. Webhook received                                               │
│     └─> Create PaymentWebhookEvent                                 │
│     └─> Process payment                                            │
│     └─> Update Payment status                                      │
│                                                                     │
│  5. Enrollment activated                                           │
│     └─> Link payment to enrollment                                │
│     └─> Grant course access                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Subscription Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SUBSCRIPTION PAYMENT FLOW                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. User subscribes                                               │
│     └─> Create Subscription (incomplete)                           │
│     └─> Create Payment (pending)                                   │
│                                                                     │
│  2. Initial payment                                               │
│     └─> Process via gateway                                        │
│     └─> Webhook: subscription.created                             │
│     └─> Update Subscription (active)                               │
│                                                                     │
│  3. Subscription period                                           │
│     └─> Track usage                                               │
│     └─> Monitor days remaining                                     │
│                                                                     │
│  4. Renewal payment                                               │
│     └─> Webhook: invoice.paid                                    │
│     └─> Update period dates                                        │
│                                                                     │
│  5. Cancellation                                                  │
│     └─> Webhook: subscription.deleted                            │
│     └─> Update Subscription (canceled)                            │
│     └─> Revoke access                                             │
│                                                                     │
└────────────────────────────────────────────────────────────────────---

## Summary

The Payments module provides─┘
```

:

1. **Payment Tracking** - One-time and recurring payments
2. **Subscription Management** - Active subscription tracking
3. **Webhook Processing** - Gateway event handling
4. **Usage Tracking** - Monitor subscription usage
