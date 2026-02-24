# Module Guide: Business Operations & Intelligence

This guide covers the administrative and financial side of the LMS.

---

## 💳 Payments Module (`app/modules/payments`)
**Purpose**: Monetization.

### Architecture:
We use a **Provider Pattern** to support multiple gateways (Stripe, PayPal).
- `PaymentService` -> `StripeProvider` / `PayPalProvider`.

### The Checkout Flow:
1. User clicks "Buy".
2. API creates a `Transaction` (status=`pending`) and returns a Stripe `client_secret`.
3. Frontend completes payment.
4. Stripe Webhook hits `app/modules/payments/webhooks.py`.
5. Webhook verifies signature -> Updates `Transaction` to `success` -> Triggers `Enrollment`.

---

## 📊 Analytics Module (`app/modules/analytics`)
**Purpose**: Insights.

### Data Strategy:
- **Real-time**: Simple queries (e.g., "My Quiz Score") run directly against the DB.
- **Aggregated**: Heavy queries (e.g., "Revenue per Month") use **Materialized Views**.
  - `REFRESH MATERIALIZED VIEW` is triggered by a periodic Celery task (e.g., every hour).

### Dashboards:
- **Student**: Progress, recent activity.
- **Instructor**: Enrollment count, revenue share.
- **Admin**: System load, total revenue, churn rate.

---

## ⚡ WebSockets Module (`app/modules/websocket`)
**Purpose**: Real-time interactivity.

### `ConnectionManager` (`service.py`):
- Keeps a dictionary of `active_connections: Dict[str, List[WebSocket]]`.
- Keyed by `user_id` or `course_id`.

### Use Cases:
- **Notifications**: "Your assignment has been graded."
- **Live Quiz**: "Time is up!" broadcast to all takers.
- **Presence**: "50 students are viewing this lesson."
