---
name: calendar-tools
description: Manages calendar bookings and video conferencing. Use when the user needs to check availability, create bookings on Cal.com, or schedule and manage Zoom meetings.
---

# Calendar Tools

Tools for booking management (Cal.com) and video conferencing (Zoom).

## Cal.com

### List bookings

```python
result = await calcom_list_bookings(status="upcoming")
```

### Create booking

```python
result = await calcom_create_booking(
    event_type_id=12345,
    start="2025-03-15T10:00:00Z",
    name="John Doe",
    email="john@example.com",
    timezone="America/New_York"
)
```

### Check availability

```python
result = await calcom_get_availability(
    event_type_id=12345,
    date_from="2025-03-15",
    date_to="2025-03-20"
)
```

**Env:** `CALCOM_API_KEY`, `CALCOM_BASE_URL` (optional, defaults to `https://api.cal.com/v2`)

## Zoom

### Create meeting

```python
result = await zoom_create_meeting(
    topic="Weekly Standup",
    start_time="2025-03-15T10:00:00Z",
    duration=30,
    timezone="America/New_York"
)
```

### List meetings

```python
result = await zoom_list_meetings(meeting_type="scheduled")
```

### Get meeting details

```python
result = await zoom_get_meeting(meeting_id="123456789")
```

**Env:** `ZOOM_ACCOUNT_ID`, `ZOOM_CLIENT_ID`, `ZOOM_CLIENT_SECRET`

## Response Format

All tools return:
```json
{
  "success": true,
  "data": { ... }
}
```

On error:
```json
{
  "success": false,
  "error": "Error description"
}
```

## When to Use

- Checking calendar availability before scheduling
- Creating bookings or appointments via Cal.com
- Scheduling Zoom meetings for teams
- Listing upcoming meetings or bookings
- Building scheduling automation workflows
