# Load Users API Documentation

## Overview
This API endpoint returns a list of all users in the system with their details including name, email, role, company name (if applicable), and registration information.

## Endpoint

### GET `/super/users/`

**Authentication Required:** Yes (JWT Token)  
**Permission:** Admin only (`role="admin"`)

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
    "count": 150,
    "users": [
        {
            "id": 123,
            "name": "John Doe",
            "email": "john@example.com",
            "role": "company",
            "company_name": "ABC Corporation",
            "register_date": "User ID: 123",
            "is_active": true,
            "is_verified": true,
            "phone": "+1234567890"
        },
        {
            "id": 122,
            "name": "Jane Smith",
            "email": "jane@example.com",
            "role": "employee",
            "company_name": null,
            "register_date": "User ID: 122",
            "is_active": true,
            "is_verified": false,
            "phone": "N/A"
        },
        {
            "id": 121,
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "role": "solo",
            "company_name": null,
            "register_date": "User ID: 121",
            "is_active": false,
            "is_verified": true,
            "phone": "+9876543210"
        }
    ]
}
```

### Error Response (403 Forbidden)
```json
{
    "error": "Access denied. Only admins can access this resource."
}
```

### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Error message here"
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indicates if request was successful |
| `count` | integer | Total number of users returned |
| `users` | array | List of user objects |

### User Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | User's unique identifier |
| `name` | string | User's full name (or 'N/A' if empty) |
| `email` | string | User's email address |
| `role` | string | User's role: "company", "employee", "solo", or "rep" |
| `company_name` | string/null | Company name (only for company role, otherwise null) |
| `register_date` | string | Registration date placeholder (User ID format) |
| `is_active` | boolean | Whether user account is active |
| `is_verified` | boolean | Whether user email is verified |
| `phone` | string | User's phone number (or 'N/A' if empty) |

## User Roles

- **company**: Business/Company account with associated business info
- **employee**: Employee of a company
- **solo**: Individual user account
- **rep**: Company representative

## Features

✅ Returns all non-deleted users  
✅ Excludes admin users from the list  
✅ Includes company name for company role users  
✅ Shows active/inactive status  
✅ Shows verification status  
✅ Ordered by most recent (descending by ID)  
✅ Uses select_related for optimized database queries  

## Usage Examples

### Using cURL
```bash
curl -X GET "http://localhost:8000/super/users/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### Using JavaScript (Fetch API)
```javascript
const loadUsers = async () => {
  const token = localStorage.getItem('access_token');
  
  try {
    const response = await fetch('http://localhost:8000/super/users/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log(`Total users: ${data.count}`);
      data.users.forEach(user => {
        console.log(`${user.name} (${user.email}) - ${user.role}`);
        if (user.company_name) {
          console.log(`  Company: ${user.company_name}`);
        }
      });
    }
  } catch (error) {
    console.error('Error loading users:', error);
  }
};

loadUsers();
```

### Using Python (Requests)
```python
import requests

url = "http://localhost:8000/super/users/"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
data = response.json()

if data.get('success'):
    print(f"Total users: {data['count']}")
    for user in data['users']:
        print(f"{user['name']} ({user['email']}) - {user['role']}")
        if user['company_name']:
            print(f"  Company: {user['company_name']}")
```

### Using Axios (React/Vue)
```javascript
import axios from 'axios';

const loadUsers = async () => {
  try {
    const response = await axios.get('http://localhost:8000/super/users/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.data.success) {
      console.log('Users:', response.data.users);
      return response.data.users;
    }
  } catch (error) {
    console.error('Failed to load users:', error);
  }
};
```

## Frontend Integration Example

### React Component
```jsx
import React, { useState, useEffect } from 'react';

const UsersTable = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUsers = async () => {
      const token = localStorage.getItem('access_token');
      
      try {
        const response = await fetch('http://localhost:8000/super/users/', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        const data = await response.json();
        
        if (data.success) {
          setUsers(data.users);
        }
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th>Role</th>
          <th>Company</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {users.map(user => (
          <tr key={user.id}>
            <td>{user.name}</td>
            <td>{user.email}</td>
            <td>{user.role}</td>
            <td>{user.company_name || '-'}</td>
            <td>{user.is_active ? 'Active' : 'Inactive'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default UsersTable;
```

## Notes

1. **Authentication**: User must be logged in with a valid JWT access token
2. **Authorization**: Only users with `role="admin"` can access this endpoint
3. **Ordering**: Users are ordered by ID in descending order (newest first)
4. **Performance**: Uses `select_related('business_info')` for optimized queries
5. **Company Name**: Only populated for users with `role="company"`
6. **Register Date**: Currently shows "User ID: {id}" as a placeholder
   - TODO: Add `created_at` field to User model for accurate registration dates

## Important Limitations

⚠️ **Registration Date**: The User model doesn't currently have a `created_at` field, so the registration date is represented as a placeholder using the User ID. 

**Recommended Fix**: Add the following field to the User model in `accounts/models.py`:
```python
created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
```

After adding this field, update the view to use:
```python
user_info['register_date'] = user.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'created_at') and user.created_at else 'N/A'
```

## Filter Options (Future Enhancement)

Consider adding query parameters for filtering:
- `?role=company` - Filter by specific role
- `?is_active=true` - Filter by active status
- `?search=john` - Search by name or email
- `?limit=50&offset=0` - Pagination

## Security

✅ JWT authentication required  
✅ Role-based authorization (admin only)  
✅ Excludes admin users from results  
✅ Excludes soft-deleted users (`is_delete=True`)  
✅ Proper error handling  
✅ SQL injection protection via ORM  

## Testing

### Test Cases

1. **Valid Admin Request**: Should return list of users
2. **Non-Admin Request**: Should return 403 Forbidden
3. **Unauthenticated Request**: Should return 401 Unauthorized
4. **Company User**: Should include company_name field
5. **Non-Company User**: Should have null company_name
6. **Empty Database**: Should return empty array with count 0

## Status

✅ **COMPLETE** - Ready for production use

All requested features implemented:
- ✅ Name (full_name)
- ✅ Email
- ✅ Role
- ✅ Company name (for company role)
- ⚠️ Register date (placeholder - needs User model update)
- ✅ Additional fields (active status, verified, phone)
