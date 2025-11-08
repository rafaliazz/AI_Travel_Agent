"""
Amadeus API handler
From here we interact with the Amadeus API endpoints 
"""

from amadeus import Client, ResponseError
import os


# ============================================================
#  CONFIGURATION
# ============================================================

AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY", "PYCJ0VVSdjFX4FwyEPotNa73xdLysrxp")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET", "tSQ04QnGAPQFeDKk")

amadeus = Client(
    client_id=AMADEUS_API_KEY,
    client_secret=AMADEUS_API_SECRET
)


# ============================================================
#  FLIGHT METHODS
# ============================================================

def search_flights(origin: str, destination: str, departure_date: str, adults: int = 1, max_results: int = 3):
    """
    Search for flights between two airports using Amadeus API.
    Returns a list of flight offers.
    """
    try:
        print(f"\n✈️ Searching flights from {origin} → {destination} on {departure_date}...")

        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults,
            max=max_results
        )

        if response.data == None: 
            print("No available Flights")
            return None

        flights = []
        for idx, offer in enumerate(response.data):
            flights.append(offer)
            price = offer["price"]["total"]
            itineraries = offer["itineraries"]
            first_leg = itineraries[0]["segments"][0]
            last_leg = itineraries[0]["segments"][len(itineraries[0]["segments"])-1]

            departure = first_leg["departure"]["iataCode"]
            arrival = last_leg["arrival"]["iataCode"]
            departure_time = first_leg["departure"]["at"]
            arrival_time = last_leg["arrival"]["at"]
            carrier = first_leg["carrierCode"]

            print(f"\nFlight #{idx+1}")
            print(f"  Airline: {carrier}")
            print(f"  From: {departure} ({departure_time})")
            print(f"  To: {arrival} ({arrival_time})")
            print(f"  Price: €{price}")
            print("-" * 40)

        return flights

    except ResponseError as e:
        print("❌ Flight Search Error:", e)
        return []


def book_flight(flight_offer):
    """
    Book a flight using Amadeus API (sandbox).
    Expects a flight offer object returned by search_flights().
    """
    try:
        print("\n🧾 Booking flight (sandbox)...")

        travelers = [
            {
                "id": "1",
                "dateOfBirth": "1990-01-01",
                "name": {"firstName": "BOB", "lastName": "SMITH"},
                "gender": "MALE",
                "contact": {
                    "emailAddress": "bob.smith@example.com",
                    "phones": [
                        {"deviceType": "MOBILE", "countryCallingCode": "1", "number": "5555555555"}
                    ]
                },
                "documents": [
                    {
                        "documentType": "PASSPORT",
                        "birthPlace": "US",
                        "issuanceLocation": "US",
                        "issuanceDate": "2015-01-01",
                        "number": "123456789",
                        "expiryDate": "2030-01-01",
                        "issuanceCountry": "US",
                        "validityCountry": "US",
                        "nationality": "US",
                        "holder": True
                    }
                ]
            }
        ]

        response = amadeus.booking.flight_orders.post(
            flight=flight_offer,
            travelers=travelers
        )

        print("✅ Flight booked successfully!")
        return response.data

    except ResponseError as e:
        print("❌ Flight Booking Error:", e)
        return None


# ============================================================
#  HOTEL METHODS
# ============================================================

def search_hotels(city_code: str, check_in: str, check_out: str, radius_km: int = 20, rating=None):
    """
    Search for hotels in a given city using Amadeus API.
    Returns a list of hotel offers with their IDs.
    """
    try:
        print(f"\n🏨 Searching for hotels in {city_code} ({check_in} to {check_out})...")

        if rating == None: 
            hotel_response = amadeus.reference_data.locations.hotels.by_city.get(
                cityCode=city_code,
                radius=radius_km,
            )
        else: 
            hotel_response = amadeus.reference_data.locations.hotels.by_city.get(
                cityCode=city_code,
                radius=radius_km,
                ratings=rating
            )
        if hotel_response.data == None: 
            print("No available Hotels")
            return None 
        
        hotel_ids = [hotel["hotelId"] for hotel in hotel_response.data[:10]]
        print(f"Found {len(hotel_ids)} hotels: {hotel_ids}")

        offers_response = amadeus.shopping.hotel_offers_search.get(
            hotelIds=hotel_ids,
            checkInDate=check_in,
            checkOutDate=check_out
        )
        if offers_response.data == None: 
            print("No available Hotels")
            return None 
        
        hotel_offers = []
        for hotel_entry in offers_response.data:
            hotel_name = hotel_entry["hotel"]["name"]
            for offer in hotel_entry["offers"]:
                offer_info = {
                    "hotel_name": hotel_name,
                    "offer_id": offer["id"],
                    "price": offer["price"]["base"],
                    "currency": offer["price"]["currency"]
                }
                hotel_offers.append(offer_info)
                print(f"💤 {hotel_name} — {offer_info['price']} {offer_info['currency']} (Offer ID: {offer_info['offer_id']})")

        return hotel_offers

    except ResponseError as e:
        print("❌ Hotel Search Error:", e)
        return []


def book_hotel(hotel_offer_id: str):
    """
    Book a hotel using Amadeus API sandbox with a given offer ID.
    """
    try:
        print(f"\n🧾 Booking hotel offer {hotel_offer_id}...")

        booking_response = amadeus.booking.hotel_orders.post(
            travel_agent={"contact": {"email": "bob.smith@email.com"}},
            guests=[
                {
                    "tid": 1,
                    "title": "MR",
                    "firstName": "BOB",
                    "lastName": "SMITH",
                    "phone": "+33679278416",
                    "email": "bob.smith@email.com"
                }
            ],
            room_associations=[
                {
                    "guestReferences": [{"guestReference": "1"}],
                    "hotelOfferId": hotel_offer_id
                }
            ],
            payment={
                "method": "CREDIT_CARD",
                "paymentCard": {
                    "paymentCardInfo": {
                        "vendorCode": "VI",
                        "cardNumber": "4151289722471370",
                        "expiryDate": "2026-08",
                        "holderName": "BOB SMITH"
                    }
                }
            }
        )

        print("✅ Hotel booked successfully!")
        return booking_response.data

    except ResponseError as e:
        print("❌ Hotel Booking Error:", e)
        return None


# ============================================================
#  TEST CASES
# ============================================================

if __name__ == "__main__":
    # --- Test Flight Search + Booking ---
    flights = search_flights(origin="CGK", destination="AMS", departure_date="2025-12-20")

    # print(flights[1])
    if flights:
        print("🧭 Booking the first available flight...")
        print(flights[0])
        book_flight(flights[0])

    # # --- Test Hotel Search + Booking ---
    # hotels = search_hotels(city_code="AMS", check_in="2025-12-20", check_out="2025-12-23", rating=5)
    # if hotels:
    #     print("🛏️ Booking the first available hotel...")
    #     book_hotel(hotels[0]["offer_id"])
