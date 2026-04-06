"""
Hotel Booking Tools for ReAct Agent
Simulates a hotel booking system with mock data.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random

# ─── Mock Hotel Database ──────────────────────────────────────────────────────

HOTELS_DB = {
    "HN001": {
        "id": "HN001", "name": "Metropole Hanoi",
        "city": "Hanoi", "stars": 5,
        "price_per_night": 250,
        "amenities": ["WiFi", "Pool", "Spa", "Restaurant", "Gym"],
        "address": "15 Ngo Quyen, Hoan Kiem, Hanoi",
        "rating": 4.8, "available_rooms": 12,
    },
    "HN002": {
        "id": "HN002", "name": "Hanoi La Siesta Hotel",
        "city": "Hanoi", "stars": 4,
        "price_per_night": 90,
        "amenities": ["WiFi", "Rooftop Bar", "Restaurant", "Airport Transfer"],
        "address": "94 Ma May, Hoan Kiem, Hanoi",
        "rating": 4.6, "available_rooms": 8,
    },
    "HN003": {
        "id": "HN003", "name": "Hanoi Budget Inn",
        "city": "Hanoi", "stars": 2,
        "price_per_night": 25,
        "amenities": ["WiFi", "Breakfast"],
        "address": "32 Hang Bong, Hoan Kiem, Hanoi",
        "rating": 4.0, "available_rooms": 20,
    },
    "SGN001": {
        "id": "SGN001", "name": "Park Hyatt Saigon",
        "city": "Ho Chi Minh",
        "stars": 5, "price_per_night": 300,
        "amenities": ["WiFi", "Pool", "Spa", "Fine Dining", "Concierge"],
        "address": "2 Lam Son Square, District 1, HCMC",
        "rating": 4.9, "available_rooms": 5,
    },
    "SGN002": {
        "id": "SGN002", "name": "Caravelle Saigon",
        "city": "Ho Chi Minh",
        "stars": 5, "price_per_night": 220,
        "amenities": ["WiFi", "Pool", "Rooftop Bar", "Spa"],
        "address": "19 Lam Son Square, District 1, HCMC",
        "rating": 4.7, "available_rooms": 15,
    },
    "DAN001": {
        "id": "DAN001", "name": "InterContinental Danang",
        "city": "Da Nang",
        "stars": 5, "price_per_night": 400,
        "amenities": ["Private Beach", "Pool", "Spa", "Golf", "Restaurant"],
        "address": "Son Tra Peninsula, Da Nang",
        "rating": 4.9, "available_rooms": 3,
    },
}

BOOKINGS_DB: Dict[str, Dict] = {}

# ─── Tool Functions ────────────────────────────────────────────────────────────

def search_hotels(city: str, checkin: str, checkout: str,
                  max_price: Optional[float] = None,
                  min_stars: Optional[int] = None) -> str:
    """
    Search available hotels in a city.
    Args:
        city: City name (e.g. 'Hanoi', 'Ho Chi Minh', 'Da Nang')
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        max_price: Maximum price per night (USD)
        min_stars: Minimum star rating
    """
    results = []
    city_lower = city.lower()

    for hotel in HOTELS_DB.values():
        if city_lower not in hotel["city"].lower():
            continue
        if max_price and hotel["price_per_night"] > max_price:
            continue
        if min_stars and hotel["stars"] < min_stars:
            continue
        if hotel["available_rooms"] == 0:
            continue

        try:
            ci = datetime.strptime(checkin, "%Y-%m-%d")
            co = datetime.strptime(checkout, "%Y-%m-%d")
            nights = (co - ci).days
            total = nights * hotel["price_per_night"]
        except ValueError:
            return json.dumps({"error": "Invalid date format. Use YYYY-MM-DD."})

        results.append({
            "hotel_id": hotel["id"],
            "name": hotel["name"],
            "stars": "⭐" * hotel["stars"],
            "price_per_night": f"${hotel['price_per_night']}",
            "total_price": f"${total} for {nights} nights",
            "rating": hotel["rating"],
            "amenities": ", ".join(hotel["amenities"]),
            "address": hotel["address"],
            "available_rooms": hotel["available_rooms"],
        })

    if not results:
        return json.dumps({"message": f"No hotels found in {city} matching your criteria."})

    results.sort(key=lambda x: x["rating"], reverse=True)
    return json.dumps({"hotels": results, "total_found": len(results)}, ensure_ascii=False)


def get_hotel_details(hotel_id: str) -> str:
    """
    Get full details about a specific hotel.
    Args:
        hotel_id: Hotel ID (e.g. 'HN001', 'SGN001')
    """
    hotel = HOTELS_DB.get(hotel_id.upper())
    if not hotel:
        return json.dumps({"error": f"Hotel '{hotel_id}' not found."})
    return json.dumps(hotel, ensure_ascii=False)


def book_hotel(hotel_id: str, guest_name: str, checkin: str,
               checkout: str, num_rooms: int = 1) -> str:
    """
    Book a hotel room.
    Args:
        hotel_id: Hotel ID to book
        guest_name: Full name of the guest
        checkin: Check-in date (YYYY-MM-DD)
        checkout: Check-out date (YYYY-MM-DD)
        num_rooms: Number of rooms to book
    """
    hotel = HOTELS_DB.get(hotel_id.upper())
    if not hotel:
        return json.dumps({"error": f"Hotel '{hotel_id}' not found."})

    if hotel["available_rooms"] < num_rooms:
        return json.dumps({
            "error": f"Not enough rooms. Only {hotel['available_rooms']} available."
        })

    try:
        ci = datetime.strptime(checkin, "%Y-%m-%d")
        co = datetime.strptime(checkout, "%Y-%m-%d")
        nights = (co - ci).days
        if nights <= 0:
            return json.dumps({"error": "Checkout must be after check-in date."})
    except ValueError:
        return json.dumps({"error": "Invalid date format. Use YYYY-MM-DD."})

    total_price = nights * hotel["price_per_night"] * num_rooms
    booking_id = f"BK{random.randint(10000, 99999)}"

    BOOKINGS_DB[booking_id] = {
        "booking_id": booking_id,
        "hotel_id": hotel_id,
        "hotel_name": hotel["name"],
        "guest_name": guest_name,
        "checkin": checkin,
        "checkout": checkout,
        "nights": nights,
        "num_rooms": num_rooms,
        "total_price": total_price,
        "status": "CONFIRMED",
    }

    # Update available rooms
    HOTELS_DB[hotel_id.upper()]["available_rooms"] -= num_rooms

    return json.dumps({
        "success": True,
        "booking_id": booking_id,
        "hotel": hotel["name"],
        "guest": guest_name,
        "checkin": checkin,
        "checkout": checkout,
        "nights": nights,
        "rooms": num_rooms,
        "total_price": f"${total_price}",
        "status": "✅ CONFIRMED",
        "message": f"Booking confirmed! Please save your booking ID: {booking_id}",
    }, ensure_ascii=False)


def cancel_booking(booking_id: str) -> str:
    """
    Cancel an existing booking.
    Args:
        booking_id: Booking ID to cancel (e.g. 'BK12345')
    """
    booking = BOOKINGS_DB.get(booking_id.upper())
    if not booking:
        return json.dumps({"error": f"Booking '{booking_id}' not found."})

    if booking["status"] == "CANCELLED":
        return json.dumps({"error": "This booking is already cancelled."})

    # Restore room availability
    hotel_id = booking["hotel_id"].upper()
    if hotel_id in HOTELS_DB:
        HOTELS_DB[hotel_id]["available_rooms"] += booking["num_rooms"]

    BOOKINGS_DB[booking_id]["status"] = "CANCELLED"

    return json.dumps({
        "success": True,
        "booking_id": booking_id,
        "message": f"Booking {booking_id} at {booking['hotel_name']} has been cancelled.",
        "refund": f"${booking['total_price']} will be refunded within 5-7 business days.",
    }, ensure_ascii=False)


def get_booking_info(booking_id: str) -> str:
    """
    Get details of an existing booking.
    Args:
        booking_id: Booking ID to look up
    """
    booking = BOOKINGS_DB.get(booking_id.upper())
    if not booking:
        return json.dumps({"error": f"Booking '{booking_id}' not found."})
    return json.dumps(booking, ensure_ascii=False)


# ─── Tool Registry ─────────────────────────────────────────────────────────────

HOTEL_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "search_hotels",
        "description": "Search for available hotels in a city by date range and optional filters (max price, min stars).",
        "function": search_hotels,
        "args_example": 'city="Hanoi", checkin="2025-08-01", checkout="2025-08-05"',
    },
    {
        "name": "get_hotel_details",
        "description": "Get full details about a specific hotel using its hotel ID.",
        "function": get_hotel_details,
        "args_example": 'hotel_id="HN001"',
    },
    {
        "name": "book_hotel",
        "description": "Book a hotel room for a guest. Returns a booking confirmation with booking ID.",
        "function": book_hotel,
        "args_example": 'hotel_id="HN001", guest_name="Nguyen Van A", checkin="2025-08-01", checkout="2025-08-05", num_rooms=1',
    },
    {
        "name": "cancel_booking",
        "description": "Cancel an existing hotel booking using its booking ID.",
        "function": cancel_booking,
        "args_example": 'booking_id="BK12345"',
    },
    {
        "name": "get_booking_info",
        "description": "Look up details of an existing booking using its booking ID.",
        "function": get_booking_info,
        "args_example": 'booking_id="BK12345"',
    },
]