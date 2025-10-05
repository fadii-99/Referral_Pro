# Super Admin Dashboard API

## Overview
This API provides comprehensive dashboard analytics for super administrators of the ReferralPro platform.

## Endpoint

### GET `/super/dashboard/`

**Authentication Required:** Yes (JWT Token)  
**Permission:** Super Admin only (`role="superadmin"`)

## Request Headers
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Response Format

### Success Response (200 OK)
```json
{
    "success": true,
    "data": {
        "active_users": 150,
        "total_referrals": 523,
        "total_revenue": 45280.50,
        "total_points": 12500,
        "total_cashout": 0,
        "active_subscribers": 45,
        "cancelled_subscriptions": 8,
        
        "user_trend": [
            {
                "month": "January 2025",
                "users": 12
            },
            {
                "month": "February 2025",
                "users": 18
            }
        ],
        
        "referral_breakdown": [
            {
                "month": "January 2025",
                "pending": 5,
                "friend_opted_in": 3,
                "business_accepted": 2,
                "in_progress": 4,
                "completed": 10,
                "cancelled": 1
            }
        ],
        
        "revenue_trend": [
            {
                "month": "January 2025",
                "revenue": 3450.00
            },
            {
                "month": "February 2025",
                "revenue": 4200.50
            }
        ],
        
        "users_by_role": [
            {
                "role": "company",
                "count": 45
            },
            {
                "role": "employee",
                "count": 89
            },
            {
                "role": "solo",
                "count": 16
            }
        ],
        
        "referrals_by_status": [
            {
                "status": "completed",
                "count": 125
            },
            {
                "status": "pending",
                "count": 32
            },
            {
                "status": "in_progress",
                "count": 18
            }
        ],
        
        "recent_transactions": [
            {
                "id": 1,
                "user__email": "company@example.com",
                "amount": 99.99,
                "transaction_type": "subscription",
                "created_at": "2025-10-01T10:30:00Z",
                "payment_method": "stripe"
            }
        ],
        
        "summary": {
            "total_users": 150,
            "total_companies": 45,
            "total_employees": 89,
            "total_solo_users": 16,
            "completed_referrals": 125,
            "pending_referrals": 32
        }
    }
}
```

### Error Response (403 Forbidden)
```json
{
    "error": "Access denied. Only superadmins can access this resource."
}
```

### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Error message here"
}
```

## Data Fields Description

### Main Metrics
- **active_users**: Number of currently active users (excluding superadmins)
- **total_referrals**: Total number of referrals in the system
- **total_revenue**: Total revenue from successful transactions (in USD)
- **total_points**: Total points awarded from completed referrals
- **total_cashout**: Total cashout amount (currently 0, requires implementation)
- **active_subscribers**: Number of active paid subscribers
- **cancelled_subscriptions**: Number of cancelled subscriptions

### Graph Data
- **user_trend**: Monthly user registration trend for last 12 months
- **referral_breakdown**: Monthly referral status breakdown for last 12 months
- **revenue_trend**: Monthly revenue trend for last 12 months

### Additional Insights
- **users_by_role**: Distribution of users by role (company, employee, solo)
- **referrals_by_status**: Distribution of referrals by status
- **recent_transactions**: Last 10 successful transactions

### Summary Statistics
- **total_users**: Total non-deleted users (excluding superadmins)
- **total_companies**: Total company accounts
- **total_employees**: Total employee accounts
- **total_solo_users**: Total solo user accounts
- **completed_referrals**: Total completed referrals
- **pending_referrals**: Total pending referrals

## Usage Example

### Using cURL
```bash
curl -X GET "http://localhost:8000/super/dashboard/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Using JavaScript (Fetch API)
```javascript
fetch('http://localhost:8000/super/dashboard/', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### Using Python (Requests)
```python
import requests

url = "http://localhost:8000/super/dashboard/"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
print(response.json())
```

## Notes

1. **Authentication**: User must be logged in with a valid JWT access token
2. **Authorization**: Only users with `role="superadmin"` can access this endpoint
3. **Date Ranges**: All trends show data for the last 12 months
4. **Timezone**: All timestamps are in UTC
5. **Currency**: All revenue amounts are in USD

## TODO / Future Enhancements

1. Add `created_at` field to User model for accurate user trend tracking
2. Implement Cashout model and integrate total cashout calculation
3. Add filtering by date range (query parameters)
4. Add pagination for recent transactions
5. Add export functionality (CSV/Excel)
6. Add real-time WebSocket updates for live metrics
7. Add caching for improved performance

## Error Handling

The API handles various error scenarios:
- Missing or invalid JWT token → 401 Unauthorized
- Non-superadmin user → 403 Forbidden
- Database errors → 500 Internal Server Error
- General exceptions → 500 with error message
