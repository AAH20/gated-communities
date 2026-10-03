# API Reference

Base URL: `https://api.gated-communities.example.com/v1`

All requests require authentication via Bearer token unless noted otherwise.

## Authentication

### POST /auth/register

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123",
  "firstName": "John",
  "lastName": "Doe",
  "phone": "+1234567890",
  "communityId": "uuid"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "role": "resident",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

### POST /auth/login

Authenticate and receive access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecureP@ss123"
}
```

**Response (200):**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIs...",
  "expiresIn": 86400,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "resident"
  }
}
```

### POST /auth/refresh

Refresh an expired access token.

**Request Body:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "expiresIn": 86400
}
```

### POST /auth/logout

Invalidate the current access token.

**Headers:** `Authorization: Bearer <token>`

**Response (204):** No content.

---

## Communities

### GET /communities

List all communities (admin only).

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Items per page (default: 20) |
| `search` | string | Search by name |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Sunrise Heights",
      "address": "123 Main St",
      "totalUnits": 250,
      "activeResidents": 238,
      "createdAt": "2023-06-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "totalPages": 1
  }
}
```

### POST /communities

Create a new community (admin only).

**Request Body:**
```json
{
  "name": "Sunrise Heights",
  "address": "123 Main St, City, State 12345",
  "totalUnits": 250,
  "adminEmail": "admin@sunriseheights.com"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "name": "Sunrise Heights",
  "address": "123 Main St, City, State 12345",
  "totalUnits": 250,
  "createdAt": "2024-01-15T10:30:00Z"
}
```

### GET /communities/:id

Get community details.

**Response (200):**
```json
{
  "id": "uuid",
  "name": "Sunrise Heights",
  "address": "123 Main St, City, State 12345",
  "totalUnits": 250,
  "activeResidents": 238,
  "amenities": ["clubhouse", "gym", "pool", "tennis"],
  "createdAt": "2023-06-01T00:00:00Z"
}
```

### PUT /communities/:id

Update community details (admin only).

**Request Body:**
```json
{
  "name": "Sunrise Heights Updated",
  "totalUnits": 260
}
```

**Response (200):** Updated community object.

### DELETE /communities/:id

Delete a community (admin only).

**Response (204):** No content.

---

## Residents

### GET /residents

List residents in a community.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `communityId` | string | Filter by community |
| `building` | string | Filter by building |
| `unit` | string | Filter by unit |
| `status` | string | `active`, `inactive`, `pending` |
| `page` | integer | Page number |
| `limit` | integer | Items per page |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "userId": "uuid",
      "firstName": "John",
      "lastName": "Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "building": "A",
      "unit": "101",
      "status": "active",
      "moveInDate": "2023-08-01",
      "vehicles": [
        {
          "id": "uuid",
          "plateNumber": "ABC123",
          "type": "car"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 238,
    "totalPages": 12
  }
}
```

### POST /residents

Add a new resident to a community.

**Request Body:**
```json
{
  "userId": "uuid",
  "communityId": "uuid",
  "building": "A",
  "unit": "101",
  "moveInDate": "2024-01-15",
  "role": "owner"
}
```

**Response (201):** Created resident object.

### GET /residents/:id

Get resident details.

**Response (200):**
```json
{
  "id": "uuid",
  "userId": "uuid",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "building": "A",
  "unit": "101",
  "status": "active",
  "moveInDate": "2023-08-01",
  "vehicles": [],
  "householdMembers": [],
  "createdAt": "2023-08-01T00:00:00Z"
}
```

### PUT /residents/:id

Update resident information.

**Request Body:**
```json
{
  "phone": "+1987654321",
  "status": "active"
}
```

**Response (200):** Updated resident object.

### DELETE /residents/:id

Remove a resident (sets status to inactive).

**Response (204):** No content.

---

## Visitors

### GET /visitors

List visitor records.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `communityId` | string | Filter by community |
| `status` | string | `pending`, `approved`, `denied`, `checked_in`, `checked_out` |
| `dateFrom` | string | Start date (ISO 8601) |
| `dateTo` | string | End date (ISO 8601) |
| `page` | integer | Page number |
| `limit` | integer | Items per page |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "firstName": "Jane",
      "lastName": "Smith",
      "phone": "+1234567890",
      "hostResidentId": "uuid",
      "purpose": "Family visit",
      "status": "approved",
      "qrCode": "data:image/png;base64,...",
      "validFrom": "2024-01-20T08:00:00Z",
      "validUntil": "2024-01-20T20:00:00Z",
      "checkedInAt": null,
      "checkedOutAt": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "totalPages": 3
  }
}
```

### POST /visitors

Register a new visitor.

**Request Body:**
```json
{
  "communityId": "uuid",
  "hostResidentId": "uuid",
  "firstName": "Jane",
  "lastName": "Smith",
  "phone": "+1234567890",
  "purpose": "Family visit",
  "validFrom": "2024-01-20T08:00:00Z",
  "validUntil": "2024-01-20T20:00:00Z",
  "vehiclePlate": "XYZ789"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "status": "pending",
  "qrCode": "data:image/png;base64,...",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

### POST /visitors/:id/approve

Approve a visitor request (security/admin only).

**Response (200):** Updated visitor object with `status: "approved"`.

### POST /visitors/:id/deny

Deny a visitor request (security/admin only).

**Request Body:**
```json
{
  "reason": "Invalid credentials"
}
```

**Response (200):** Updated visitor object with `status: "denied"`.

### POST /visitors/:id/check-in

Record visitor check-in (security only).

**Response (200):** Updated visitor object with `checkedInAt` timestamp.

### POST /visitors/:id/check-out

Record visitor check-out (security only).

**Response (200):** Updated visitor object with `checkedOutAt` timestamp.

### GET /visitors/qr/:code

Validate a visitor QR code (public endpoint for gate scanners).

**Response (200):**
```json
{
  "valid": true,
  "visitor": {
    "id": "uuid",
    "firstName": "Jane",
    "lastName": "Smith",
    "hostUnit": "A-101",
    "validUntil": "2024-01-20T20:00:00Z"
  }
}
```

---

## Amenities

### GET /amenities

List all amenities in a community.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `communityId` | string | Filter by community |
| `type` | string | `clubhouse`, `gym`, `pool`, `tennis`, `other` |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Community Pool",
      "type": "pool",
      "capacity": 50,
      "location": "Building B, Ground Floor",
      "operatingHours": "06:00-22:00",
      "requiresBooking": true,
      "maxBookingHours": 2
    }
  ]
}
```

### POST /amenities

Create a new amenity (admin only).

**Request Body:**
```json
{
  "communityId": "uuid",
  "name": "Tennis Court A",
  "type": "tennis",
  "capacity": 4,
  "location": "East Wing",
  "operatingHours": "07:00-21:00",
  "requiresBooking": true,
  "maxBookingHours": 1
}
```

**Response (201):** Created amenity object.

### GET /amenities/:id

Get amenity details.

**Response (200):** Amenity object.

### PUT /amenities/:id

Update amenity details (admin only).

**Request Body:**
```json
{
  "operatingHours": "06:00-22:00",
  "maxBookingHours": 2
}
```

**Response (200):** Updated amenity object.

### DELETE /amenities/:id

Delete an amenity (admin only).

**Response (204):** No content.

---

## Bookings

### GET /bookings

List amenity bookings.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `amenityId` | string | Filter by amenity |
| `residentId` | string | Filter by resident |
| `date` | string | Filter by date (YYYY-MM-DD) |
| `status` | string | `pending`, `confirmed`, `cancelled`, `completed` |
| `page` | integer | Page number |
| `limit` | integer | Items per page |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "amenityId": "uuid",
      "amenityName": "Community Pool",
      "residentId": "uuid",
      "residentName": "John Doe",
      "date": "2024-01-20",
      "startTime": "10:00",
      "endTime": "12:00",
      "status": "confirmed",
      "guests": 2,
      "createdAt": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 156,
    "totalPages": 8
  }
}
```

### POST /bookings

Create a new amenity booking.

**Request Body:**
```json
{
  "amenityId": "uuid",
  "date": "2024-01-20",
  "startTime": "10:00",
  "endTime": "12:00",
  "guests": 2
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "status": "confirmed",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

### GET /bookings/:id

Get booking details.

**Response (200):** Booking object.

### PUT /bookings/:id

Update a booking (before start time).

**Request Body:**
```json
{
  "startTime": "11:00",
  "endTime": "13:00",
  "guests": 3
}
```

**Response (200):** Updated booking object.

### DELETE /bookings/:id

Cancel a booking.

**Response (204):** No content.

### GET /amenities/:id/availability

Check availability for an amenity on a given date.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `date` | string | Date to check (YYYY-MM-DD) |

**Response (200):**
```json
{
  "date": "2024-01-20",
  "operatingHours": "06:00-22:00",
  "slots": [
    { "start": "06:00", "end": "07:00", "available": true },
    { "start": "07:00", "end": "08:00", "available": true },
    { "start": "08:00", "end": "09:00", "available": false, "bookingId": "uuid" },
    { "start": "09:00", "end": "10:00", "available": false, "bookingId": "uuid" },
    { "start": "10:00", "end": "11:00", "available": true }
  ]
}
```

---

## Announcements

### GET /announcements

List community announcements.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `communityId` | string | Filter by community |
| `building` | string | Filter by building |
| `priority` | string | `low`, `normal`, `high`, `urgent` |
| `page` | integer | Page number |
| `limit` | integer | Items per page |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Pool Maintenance",
      "content": "The community pool will be closed for maintenance on Jan 25.",
      "priority": "high",
      "targetBuildings": ["A", "B"],
      "authorName": "Admin",
      "createdAt": "2024-01-15T10:30:00Z",
      "expiresAt": "2024-01-25T23:59:59Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 12,
    "totalPages": 1
  }
}
```

### POST /announcements

Create a new announcement (admin only).

**Request Body:**
```json
{
  "communityId": "uuid",
  "title": "Pool Maintenance",
  "content": "The community pool will be closed for maintenance on Jan 25.",
  "priority": "high",
  "targetBuildings": ["A", "B"],
  "expiresAt": "2024-01-25T23:59:59Z"
}
```

**Response (201):** Created announcement object.

### GET /announcements/:id

Get announcement details.

**Response (200):** Announcement object.

### PUT /announcements/:id

Update an announcement (admin only).

**Request Body:**
```json
{
  "content": "Updated: Pool closed Jan 25-26.",
  "priority": "urgent"
}
```

**Response (200):** Updated announcement object.

### DELETE /announcements/:id

Delete an announcement (admin only).

**Response (204):** No content.

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Rate Limiting

API requests are rate-limited per user:

- **Standard:** 100 requests per 15 minutes
- **Burst:** 200 requests per 5 minutes

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
```

---

## Pagination

List endpoints support pagination via query parameters:

- `page` — Page number (default: 1)
- `limit` — Items per page (default: 20, max: 100)

Response includes a `pagination` object:

```json
{
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 238,
    "totalPages": 12
  }
}
```

---

## Webhooks

Configure webhooks to receive real-time events.

### POST /webhooks

Register a webhook endpoint.

**Request Body:**
```json
{
  "url": "https://your-app.com/webhooks/gated-communities",
  "events": ["visitor.checked_in", "visitor.checked_out", "booking.created"],
  "secret": "your-webhook-secret"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "url": "https://your-app.com/webhooks/gated-communities",
  "events": ["visitor.checked_in", "visitor.checked_out", "booking.created"],
  "active": true,
  "createdAt": "2024-01-15T10:30:00Z"
}
```

### Webhook Events

| Event | Description |
|-------|-------------|
| `visitor.checked_in` | Visitor entered the community |
| `visitor.checked_out` | Visitor left the community |
| `visitor.approved` | Visitor request approved |
| `visitor.denied` | Visitor request denied |
| `booking.created` | New amenity booking |
| `booking.cancelled` | Booking cancelled |
| `announcement.created` | New announcement published |
| `resident.added` | New resident moved in |
| `resident.removed` | Resident moved out |

### Webhook Payload Example

```json
{
  "id": "evt_abc123",
  "type": "visitor.checked_in",
  "createdAt": "2024-01-20T14:30:00Z",
  "data": {
    "visitorId": "uuid",
    "visitorName": "Jane Smith",
    "hostUnit": "A-101",
    "gate": "Main Entrance",
    "checkedInAt": "2024-01-20T14:30:00Z"
  }
}
```
