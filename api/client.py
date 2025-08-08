import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class BookingAPIClient:
    """A client to interact with the mock restaurant booking API."""

    def __init__(self):
        self.base_url = "http://localhost:8547/api/ConsumerApi/v1/Restaurant/TheHungryUnicorn"
        bearer_token = os.getenv("API_BEARER_TOKEN")
        if not bearer_token:
            raise ValueError("API_BEARER_TOKEN not found in .env file")
        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Generic request handler."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(method, url, headers=self.headers, data=data)
            response.raise_for_status()
            return {"status": response.status_code, "data": response.json()}
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if "application/json" in e.response.headers.get("Content-Type", "") else e.response.text
            return {"status": e.response.status_code, "error": error_data}
        except Exception as e:
            return {"status": 500, "error": f"An unexpected error occurred: {str(e)}"}

    def check_availability(self, visit_date: str, party_size: int) -> Dict[str, Any]:
        print(f"--- Calling API: check_availability ---")
        payload = {"VisitDate": visit_date, "PartySize": party_size, "ChannelCode": "ONLINE"}
        return self._make_request("POST", "/AvailabilitySearch", data=payload)

    def create_booking(self, visit_date: str, visit_time: str, party_size: int, first_name: str, surname: str, email: str, mobile: str) -> Dict[str, Any]:
        print(f"--- Calling API: create_booking ---")
        payload = {
            "VisitDate": visit_date, "VisitTime": visit_time, "PartySize": party_size,
            "ChannelCode": "ONLINE", "Customer[FirstName]": first_name,
            "Customer[Surname]": surname, "Customer[Email]": email, "Customer[Mobile]": mobile
        }
        return self._make_request("POST", "/BookingWithStripeToken", data=payload)

    def get_booking_details(self, booking_reference: str) -> Dict[str, Any]:
        print(f"--- Calling API: get_booking_details ---")
        return self._make_request("GET", f"/Booking/{booking_reference}")

    def update_booking(self, booking_reference: str, new_date: Optional[str] = None, new_time: Optional[str] = None, new_party_size: Optional[int] = None) -> Dict[str, Any]:
        print(f"--- Calling API: update_booking ---")
        payload = {}
        if new_date: payload["VisitDate"] = new_date
        if new_time: payload["VisitTime"] = new_time
        if new_party_size: payload["PartySize"] = new_party_size
        return self._make_request("PATCH", f"/Booking/{booking_reference}", data=payload)

    def cancel_booking(self, booking_reference: str) -> Dict[str, Any]:
        print(f"--- Calling API: cancel_booking ---")
        payload = {
            "micrositeName": "TheHungryUnicorn", "bookingReference": booking_reference,
            "cancellationReasonId": 1
        }
        return self._make_request("POST", f"/Booking/{booking_reference}/Cancel", data=payload)

#### **`utils/parsers.py`**

from datetime import datetime, timedelta

def parse_natural_date(date_str: str) -> str:
    """
    Parses a natural language date string into 'YYYY-MM-DD' format.
    A simple implementation for demonstration.
    """
    if not date_str:
        return ""
    
    date_str = date_str.lower()
    today = datetime.now().date()
    
    if "today" in date_str:
        return today.strftime('%Y-%m-%d')
    if "tomorrow" in date_str:
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')
    if "next friday" in date_str:
        days_ahead = 4 - today.weekday()
        if days_ahead <= 0: days_ahead += 7
        return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
    
    # Basic check for YYYY-MM-DD format
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except ValueError:
        return "" # Indicate parsing failed