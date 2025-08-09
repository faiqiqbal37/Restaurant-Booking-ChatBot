# Path: api/client.py

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
        """Generic request handler with improved error handling."""
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"Making {method} request to: {url}")
            print(f"Headers: {self.headers}")
            if data:
                print(f"Data: {data}")
            
            response = requests.request(method, url, headers=self.headers, data=data, timeout=30)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            # Handle successful responses
            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    print(f"Response data: {response_data}")
                    return {"status": response.status_code, "data": response_data}
                except ValueError as e:
                    print(f"Failed to parse JSON response: {e}")
                    return {"status": response.status_code, "data": response.text}
            
            # Handle error responses
            else:
                try:
                    error_data = response.json()
                    print(f"Error response: {error_data}")
                    return {"status": response.status_code, "error": error_data}
                except ValueError:
                    print(f"Error response (text): {response.text}")
                    return {"status": response.status_code, "error": response.text}
                    
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
            return {"status": 500, "error": "Could not connect to the restaurant booking system. Please check if the server is running."}
        except requests.exceptions.Timeout as e:
            print(f"Timeout error: {e}")
            return {"status": 500, "error": "Request timed out. Please try again."}
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {"status": 500, "error": f"Request failed: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {"status": 500, "error": f"An unexpected error occurred: {str(e)}"}

    def check_availability(self, visit_date: str, party_size: int) -> Dict[str, Any]:
        """Check availability for a specific date and party size."""
        print(f"--- Calling API: check_availability ---")
        print(f"Visit Date: {visit_date}, Party Size: {party_size}")
        
        payload = {
            "VisitDate": visit_date, 
            "PartySize": party_size, 
            "ChannelCode": "ONLINE"
        }
        return self._make_request("POST", "/AvailabilitySearch", data=payload)

    def create_booking(self, visit_date: str, visit_time: str, party_size: int, 
                      first_name: str, surname: str, email: str, mobile: str) -> Dict[str, Any]:
        """Create a new booking."""
        print(f"--- Calling API: create_booking ---")
        print(f"Details: {visit_date} {visit_time} for {party_size} people")
        
        payload = {
            "VisitDate": visit_date, 
            "VisitTime": visit_time, 
            "PartySize": party_size,
            "ChannelCode": "ONLINE", 
            "Customer[FirstName]": first_name,
            "Customer[Surname]": surname, 
            "Customer[Email]": email, 
            "Customer[Mobile]": mobile
        }
        return self._make_request("POST", "/BookingWithStripeToken", data=payload)

    def get_booking_details(self, booking_reference: str) -> Dict[str, Any]:
        """Get details of an existing booking."""
        print(f"--- Calling API: get_booking_details ---")
        print(f"Booking Reference: {booking_reference}")
        return self._make_request("GET", f"/Booking/{booking_reference}")

    def update_booking(self, booking_reference: str, new_date: Optional[str] = None, 
                      new_time: Optional[str] = None, new_party_size: Optional[int] = None) -> Dict[str, Any]:
        """Update an existing booking."""
        print(f"--- Calling API: update_booking ---")
        print(f"Booking Reference: {booking_reference}")
        
        payload = {}
        if new_date: 
            payload["VisitDate"] = new_date
            print(f"New date: {new_date}")
        if new_time: 
            payload["VisitTime"] = new_time
            print(f"New time: {new_time}")
        if new_party_size: 
            payload["PartySize"] = new_party_size
            print(f"New party size: {new_party_size}")
            
        if not payload:
            return {"status": 400, "error": "No update parameters provided"}
            
        return self._make_request("PATCH", f"/Booking/{booking_reference}", data=payload)

    def cancel_booking(self, booking_reference: str) -> Dict[str, Any]:
        """Cancel an existing booking."""
        print(f"--- Calling API: cancel_booking ---")
        print(f"Booking Reference: {booking_reference}")
        
        payload = {
            "micrositeName": "TheHungryUnicorn", 
            "bookingReference": booking_reference,
            "cancellationReasonId": 1  # "Customer Request"
        }
        return self._make_request("POST", f"/Booking/{booking_reference}/Cancel", data=payload)

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to the server."""
        try:
            response = requests.get("http://localhost:8547/", timeout=10)
            if response.status_code == 200:
                return {"status": "success", "message": "Server is running"}
            else:
                return {"status": "error", "message": f"Server returned status {response.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Cannot connect to server. Is it running on port 8547?"}
        except Exception as e:
            return {"status": "error", "message": f"Connection test failed: {str(e)}"}