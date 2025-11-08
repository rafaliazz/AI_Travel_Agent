import streamlit as st
import os
import time
import random
from datetime import datetime
from agno.agent import Agent
from agno.models.google import Gemini

# import your amadeus helpers (must be in same folder)
from amadeuscaller import search_flights as am_search_flights, book_flight as am_book_flight, \
    search_hotels as am_search_hotels, book_hotel as am_book_hotel

# ==========================
# 🔑 Keys / Config
# ==========================
GOOGLE_API_KEY = "INSERT YOUR OWN"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# ==========================
# Streamlit UI Setup
# ==========================
st.set_page_config(page_title="🌍 AI Travel Planner", layout="wide")
st.markdown(
    """
    <style>
        .title { text-align: center; font-size: 36px; font-weight: bold; color: #ff5733; }
        .subtitle { text-align: center; font-size: 16px; color: #555; }
        .offer-box {
            border: 1px solid #e6e6e6;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 12px;
            background: #fff;
        }
        .small { font-size: 13px; color: #666; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<h1 class="title">✈️ AI-Powered Travel Planner</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Search and book flights & hotels (Amadeus sandbox). Gemini handles planning & research.</p>', unsafe_allow_html=True)

# ==========================
# Inputs
# ==========================
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    source = st.text_input("🛫 From (IATA):", value="CGK")
with col2:
    destination = st.text_input("🛬 To (IATA):", value="AMS")
with col3:
    passengers = st.number_input("👥 Adults", min_value=1, max_value=9, value=1)

departure_date = st.date_input("Departure Date")
return_date = st.date_input("Return Date")

travel_theme = st.selectbox("🎭 Travel Theme:", [
    "🏛️ Cultural Exploration",
    "🏖️ Relaxation",
    "🏔️ Adventure"
])

activity_preferences = st.text_area("🌍 What activities do you enjoy?", "Exploring, food, museums")

# Sidebar preferences
st.sidebar.title("Preferences")
budget = st.sidebar.radio("💰 Budget:", ["Economy", "Standard", "Luxury"])
flight_class = st.sidebar.radio("✈️ Flight Class:", ["ECONOMY", "BUSINESS", "FIRST"])
hotel_rating_choice = st.sidebar.selectbox("🏨 Hotel Rating:", ["Any", "3⭐", "4⭐", "5⭐"])

# convert hotel rating to numeric or None
if hotel_rating_choice == "Any":
    hotel_rating = None
else:
    hotel_rating = int(hotel_rating_choice.replace("⭐", ""))

# ==========================
# Gemini Agents (left in place for itinerary/research)
# ==========================
gemini_model = Gemini(id="gemini-2.0-flash-exp")

planner = Agent(
    name="Planner",
    instructions=["Generate an optimized itinerary for the user's trip."],
    model=gemini_model, 
)

def safe_run(agent, prompt, retries=4):
    for i in range(retries):
        try:
            return agent.run(prompt, stream=False)
        except Exception as e:
            if "429" in str(e) or "Too many requests" in str(e):
                wait = (2 ** i) + random.random()
                st.warning(f"Rate limit hit. Retrying in {wait:.1f}s...")
                time.sleep(wait)
            else:
                raise e
    return type("E", (), {"content": "(Request failed)"})()

def format_dt(iso):
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%b %d, %Y %H:%M")
    except Exception:
        try:
            # fallback if missing seconds
            dt = datetime.strptime(iso, "%Y-%m-%d %H:%M")
            return dt.strftime("%b %d, %Y %H:%M")
        except Exception:
            return iso

# ==========================
# Session state defaults
# ==========================
if "flight_results" not in st.session_state:
    st.session_state.flight_results = []  # list of Amadeus flight offers (raw)
if "hotel_results" not in st.session_state:
    st.session_state.hotel_results = []   # list of hotel offers (from amadeuscaller format)
if "bookings" not in st.session_state:
    st.session_state.bookings = []

# Booking triggers
if "selected_flight_idx" not in st.session_state:
    st.session_state.selected_flight_idx = None
if "selected_hotel_offer" not in st.session_state:
    st.session_state.selected_hotel_offer = None
if "do_book_flight" not in st.session_state:
    st.session_state.do_book_flight = False
if "do_book_hotel" not in st.session_state:
    st.session_state.do_book_hotel = False

# ==========================
# Main action button (search + itinerary)
# ==========================
if st.button("🚀 Generate Travel Plan"):
    # 1) Try Amadeus flight search first
    with st.spinner("✈️ Searching flights (Amadeus)..."):
        try:
            am_flights = am_search_flights(origin=source, destination=destination, departure_date=str(departure_date), adults=passengers, max_results=5)
            if not am_flights:
                raise Exception("No flights from Amadeus")
            st.session_state.flight_results = am_flights
        except Exception as e:
            st.warning(f"Amadeus flight search failed: {e}. No flight results available")

    # 2) Try Amadeus hotel search (uses your amadeuscaller.search_hotels format)
    with st.spinner("🏨 Searching hotels (Amadeus)..."):
        try:
            am_hotels = am_search_hotels(city_code=destination, check_in=str(departure_date), check_out=str(return_date), radius_km=20, rating=hotel_rating)
            if not am_hotels:
                raise Exception("No hotels from Amadeus")
            # am_search_hotels returns simplified list of dicts: {hotel_name, offer_id, price, currency}
            st.session_state.hotel_results = am_hotels
        except Exception as e:
            st.warning(f"Amadeus hotel search failed: {e}. No hotel results available.")
            st.session_state.hotel_results = []

# ==========================
# Display Flights (cards)
# ==========================
st.header("✈️ Flight Offers")

if st.session_state.flight_results:
    # Distinguish Amadeus offers (they are dicts with 'price') vs SerpAPI normalized fallback
    for i, offer in enumerate(st.session_state.flight_results):
        # Identify shape
        is_serp = "raw" in offer and "airline" in offer and ("departure_time" in offer)
        if is_serp:
            airline = offer.get("airline", "Unknown")
            price = offer.get("price", "Unknown")
            dep = offer.get("departure_city", "Unknown")
            arr = offer.get("arrival_city", "Unknown")
            dep_time = offer.get("departure_time", "N/A")
            arr_time = offer.get("arrival_time", "N/A")
            display_price = f"{price}"
        else:
            # Amadeus offer structure
            price = offer.get("price", {}).get("total", "N/A")
            currency = offer.get("price", {}).get("currency", "")
            first_itin = offer.get("itineraries", [])[0] if offer.get("itineraries") else {}
            segs = first_itin.get("segments", []) or []
            first_seg = segs[0] if segs else {}
            last_seg = segs[-1] if segs else first_seg
            airline = first_seg.get("carrierCode", "N/A")
            dep = first_seg.get("departure", {}).get("iataCode", "N/A")
            arr = last_seg.get("arrival", {}).get("iataCode", "N/A")
            dep_time = first_seg.get("departure", {}).get("at", "N/A")
            arr_time = last_seg.get("arrival", {}).get("at", "N/A")
            display_price = f"{price} {currency}"

        # Render card
        with st.container():
            st.markdown(f'<div class="offer-box">', unsafe_allow_html=True)
            st.markdown(f"**Offer #{i+1} — {airline}**")
            st.markdown(f"**Route:** {dep} → {arr}")
            st.markdown(f"**Departure:** {format_dt(dep_time)}")
            st.markdown(f"**Arrival:** {format_dt(arr_time)}")
            st.markdown(f"**Price:** {display_price}")
            st.markdown("</div>", unsafe_allow_html=True)

            # Book button: set session state then handle booking below
            if st.button(f"Book Flight #{i+1}", key=f"book_flight_{i}"):
                st.session_state.selected_flight_idx = i
                st.session_state.do_book_flight = True

else:
    st.info("No flight results yet. Click 'Generate Travel Plan' to search (Amadeus first, SerpAPI fallback).")

# Handle flight booking trigger (separate block so click persists through rerun)
if st.session_state.do_book_flight:
    idx = st.session_state.selected_flight_idx
    if idx is not None and idx < len(st.session_state.flight_results):
        offer = st.session_state.flight_results[idx]
        try:
            st.info("Booking flight... (simulated with dummy traveller data)")
            print(offer)
            booking_resp = am_book_flight(offer)  # uses dummy traveler inside amadeuscaller
            st.success("Flight booked (sandbox).")
            # record booking summary
            st.session_state.bookings.append({
                    "type": "flight",
                    "offer_index": idx,
                    "airline": offer.get("itineraries", [{}])[0].get("segments", [{}])[0].get("carrierCode", ""),
                    "price": offer.get("price", {}).get("total", "")
            })
                # show returned booking id/info if available
            if booking_resp:
                st.json(booking_resp)
            else: 
                raise Exception
        except Exception as e:
            st.error(f"Booking failed: {e}")
    else:
        st.error("Selected flight no longer available.")
    # reset trigger
    st.session_state.do_book_flight = False
    st.session_state.selected_flight_idx = None

# ==========================
# Display Hotels (cards)
# ==========================
st.header("🏨 Hotel Offers")

if st.session_state.hotel_results:
    for i, offer in enumerate(st.session_state.hotel_results):
        # Your amadeuscaller.search_hotels returns simplified offers (hotel_name, offer_id, price, currency)
        hotel_name = offer.get("hotel_name") or offer.get("hotel", {}).get("name", "Unknown")
        offer_id = offer.get("offer_id") or offer.get("id")
        price = offer.get("price")
        currency = offer.get("currency", "")
        with st.container():
            st.markdown(f'<div class="offer-box">', unsafe_allow_html=True)
            st.markdown(f"**Hotel #{i+1} — {hotel_name}**")
            st.markdown(f"**Price:** {price} {currency}")
            st.markdown(f"**Offer ID:** {offer_id}")
            st.markdown("</div>", unsafe_allow_html=True)
            if st.button(f"Book Hotel #{i+1}", key=f"book_hotel_{i}"):
                st.session_state.selected_hotel_offer = offer_id
                st.session_state.do_book_hotel = True
else:
    st.info("No hotel results yet. Click 'Generate Travel Plan' to search (Amadeus).")

# Handle hotel booking trigger
if st.session_state.do_book_hotel:
    hotel_offer_id = st.session_state.selected_hotel_offer
    if hotel_offer_id:
        try:
            st.info("Booking hotel... (simulated with dummy payment)")
            booking_resp = am_book_hotel(hotel_offer_id)  # expects a single offer id
            st.success("Hotel booked (sandbox).")
            st.session_state.bookings.append({
                "type": "hotel",
                "offer_id": hotel_offer_id,
                "hotel_name": hotel_offer_id  # we didn't keep name here; could map if needed
            })
            if booking_resp:
                st.json(booking_resp)
            else: 
                raise Exception
        except Exception as e:
            st.error(f"Hotel booking failed: {e}")
    else:
        st.error("No hotel offer selected.")
    st.session_state.do_book_hotel = False
    st.session_state.selected_hotel_offer = None

# ==========================
# Itinerary & Research area (Gemini)
# ==========================
st.header("🗺️ AI Itinerary & Research")
if st.button("🧭 Generate Itinerary (Gemini)"):
    with st.spinner("Generating..."):
        prompt = (
            f"Create a {travel_theme.lower()} itinerary for {destination} from {departure_date} to {return_date}. "
            f"User likes: {activity_preferences}. Budget: {budget}."
        )
        res = safe_run(planner, prompt)
        st.session_state.last_itinerary = res.content if res else "(No itinerary)"

if "last_itinerary" in st.session_state:
    st.subheader("Suggested itinerary")
    st.write(st.session_state.last_itinerary)

# ==========================
# Bookings sidebar
# ==========================
st.sidebar.header("📦 Your Bookings")
if st.session_state.bookings:
    for i, b in enumerate(st.session_state.bookings):
        if b["type"] == "flight":
            st.sidebar.markdown(f"**Flight #{i+1}:** {b.get('airline')} — {b.get('price')}")
        else:
            st.sidebar.markdown(f"**Hotel #{i+1}:** {b.get('offer_id')}")
else:
    st.sidebar.info("No bookings yet. Use the Book buttons on offers.")

# debug
if st.checkbox("Show debug info"):
    st.write({
        "flight_results_count": len(st.session_state.flight_results),
        "hotel_results_count": len(st.session_state.hotel_results),
        "bookings": st.session_state.bookings
    })

st.markdown("---")
st.caption("⚠️ Note: bookings are simulated (dummy traveler/payment data). Use sandbox credentials.")
