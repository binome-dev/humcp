from unittest.mock import MagicMock, patch

import pytest

from src.tools.google.calendar import (
    google_calendar_create_event,
    google_calendar_delete_event,
    google_calendar_events,
    google_calendar_list,
)


@pytest.fixture
def mock_calendar_service():
    with patch("src.tools.google.calendar.get_google_service") as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


class TestListCalendars:
    @pytest.mark.asyncio
    async def test_list_calendars_success(self, mock_calendar_service):
        mock_calendar_service.calendarList().list().execute.return_value = {
            "items": [
                {
                    "id": "primary",
                    "summary": "My Calendar",
                    "description": "Personal calendar",
                    "primary": True,
                    "accessRole": "owner",
                },
                {
                    "id": "work@group.calendar.google.com",
                    "summary": "Work",
                    "description": "Work meetings",
                    "primary": False,
                    "accessRole": "reader",
                },
            ]
        }

        result = await google_calendar_list()
        assert result["success"] is True
        assert result["data"]["total"] == 2
        assert result["data"]["calendars"][0]["id"] == "primary"
        assert result["data"]["calendars"][0]["primary"] is True

    @pytest.mark.asyncio
    async def test_list_calendars_empty(self, mock_calendar_service):
        mock_calendar_service.calendarList().list().execute.return_value = {"items": []}

        result = await google_calendar_list()
        assert result["success"] is True
        assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_calendars_error(self, mock_calendar_service):
        mock_calendar_service.calendarList().list().execute.side_effect = Exception(
            "Auth failed"
        )

        result = await google_calendar_list()
        assert result["success"] is False
        assert "Auth failed" in result["error"]


class TestEvents:
    @pytest.mark.asyncio
    async def test_events_success(self, mock_calendar_service):
        mock_calendar_service.events().list().execute.return_value = {
            "items": [
                {
                    "id": "event1",
                    "summary": "Team Meeting",
                    "description": "Weekly sync",
                    "start": {"dateTime": "2024-01-15T10:00:00Z"},
                    "end": {"dateTime": "2024-01-15T11:00:00Z"},
                    "location": "Room A",
                    "status": "confirmed",
                    "htmlLink": "https://calendar.google.com/event1",
                }
            ]
        }

        result = await google_calendar_events()
        assert result["success"] is True
        assert result["data"]["total"] == 1
        assert result["data"]["events"][0]["title"] == "Team Meeting"
        assert result["data"]["events"][0]["location"] == "Room A"

    @pytest.mark.asyncio
    async def test_events_all_day(self, mock_calendar_service):
        mock_calendar_service.events().list().execute.return_value = {
            "items": [
                {
                    "id": "event2",
                    "summary": "Holiday",
                    "start": {"date": "2024-01-01"},
                    "end": {"date": "2024-01-02"},
                    "status": "confirmed",
                }
            ]
        }

        result = await google_calendar_events()
        assert result["success"] is True
        assert result["data"]["events"][0]["start"] == "2024-01-01"

    @pytest.mark.asyncio
    async def test_events_with_custom_params(self, mock_calendar_service):
        mock_calendar_service.events().list().execute.return_value = {"items": []}

        result = await google_calendar_events(
            calendar_id="work@group.calendar.google.com", days_ahead=14
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_events_error(self, mock_calendar_service):
        mock_calendar_service.events().list().execute.side_effect = Exception(
            "Calendar not found"
        )

        result = await google_calendar_events(calendar_id="invalid")
        assert result["success"] is False


class TestCreateEvent:
    @pytest.mark.asyncio
    async def test_create_event_success(self, mock_calendar_service):
        mock_calendar_service.events().insert().execute.return_value = {
            "id": "new_event",
            "summary": "New Meeting",
            "start": {"dateTime": "2024-01-20T14:00:00Z"},
            "end": {"dateTime": "2024-01-20T15:00:00Z"},
            "htmlLink": "https://calendar.google.com/new_event",
        }

        result = await google_calendar_create_event(
            title="New Meeting",
            start_time="2024-01-20T14:00:00Z",
            end_time="2024-01-20T15:00:00Z",
        )
        assert result["success"] is True
        assert result["data"]["id"] == "new_event"
        assert result["data"]["title"] == "New Meeting"

    @pytest.mark.asyncio
    async def test_create_event_with_attendees(self, mock_calendar_service):
        mock_calendar_service.events().insert().execute.return_value = {
            "id": "team_event",
            "summary": "Team Sync",
            "start": {"dateTime": "2024-01-20T14:00:00Z"},
            "end": {"dateTime": "2024-01-20T15:00:00Z"},
            "htmlLink": "https://calendar.google.com/team_event",
        }

        result = await google_calendar_create_event(
            title="Team Sync",
            start_time="2024-01-20T14:00:00Z",
            end_time="2024-01-20T15:00:00Z",
            attendees="alice@example.com, bob@example.com",
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_create_event_error(self, mock_calendar_service):
        mock_calendar_service.events().insert().execute.side_effect = Exception(
            "Invalid time"
        )

        result = await google_calendar_create_event(
            title="Bad Event",
            start_time="invalid",
            end_time="invalid",
        )
        assert result["success"] is False


class TestDeleteEvent:
    @pytest.mark.asyncio
    async def test_delete_event_success(self, mock_calendar_service):
        mock_calendar_service.events().delete().execute.return_value = None

        result = await google_calendar_delete_event("event123")
        assert result["success"] is True
        assert result["data"]["deleted_event_id"] == "event123"

    @pytest.mark.asyncio
    async def test_delete_event_not_found(self, mock_calendar_service):
        mock_calendar_service.events().delete().execute.side_effect = Exception(
            "Event not found"
        )

        result = await google_calendar_delete_event("nonexistent")
        assert result["success"] is False
