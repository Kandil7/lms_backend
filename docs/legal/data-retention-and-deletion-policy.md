# Data Retention and Deletion Policy

## 1. Purpose
Define retention periods and deletion workflow for user and operational data.

## 2. Data Categories and Retention

| Data Category | Examples | Retention |
|---|---|---|
| Account data | user profile, role, auth metadata | active account + 24 months |
| Learning records | enrollments, progress, quiz attempts, certificates | 36 months |
| Operational logs | API/service logs | 90 days |
| Security logs | auth events, incident traces | 12 months |
| Backups | DB dumps | 30 days |

Adjust periods to legal/contract obligations in your jurisdiction.

## 3. Deletion Triggers
- User-initiated deletion request.
- Contract termination.
- Expiry of retention period.
- Legal requirement to erase data.

## 4. Deletion Workflow
1. Validate requester identity.
2. Create deletion ticket with scope and due date.
3. Delete/anonymize primary data.
4. Queue deletion propagation for derived stores.
5. Confirm deletion in logs and close ticket.

## 5. Backup Deletion Constraints
- Backups are immutable for retention window.
- Deleted records may remain in backups until expiration.
- Restored backups must re-apply deletion queue before production use.

## 6. Data Subject Requests
- Response SLA: within 30 days.
- Contact: `<privacy-contact@email.com>`.

## 7. Audit and Review
- Review retention and deletion controls quarterly.
- Keep evidence of deletion and review outcomes.

