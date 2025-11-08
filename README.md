# ✈️ Travel Planner — Flight & Hotel Booking App (Amadeus API + Streamlit + Gemini)

A modern and interactive **travel booking dashboard** built using **Streamlit**, the **Amadeus API**, and powered by **Google Gemini**.  
Search, compare, and book flights and hotels seamlessly — all within a single, intuitive interface.

---

## 🌍 Overview

This app provides a unified platform to:
- Search for **flights** between two destinations.
- Explore **hotels** based on city, rating, and stay duration.
- Preview offers directly from **Amadeus’ sandbox API**.
- Simulate bookings for both flights and hotels using **dummy traveler and payment information**.

Perfect for prototyping travel tech apps, dashboards, or Amadeus API integrations.

---

## 🖼️ UI Preview

<img width="1916" height="855" alt="image" src="https://github.com/user-attachments/assets/0b7a3cc3-9225-4fb4-9e41-637b161836ea" />
<img width="1918" height="872" alt="image" src="https://github.com/user-attachments/assets/51eb5715-df7f-4e09-b1f1-725397e9adc8" />

---

## ⚙️ Features

✅ **Flight Search**
- Enter origin, destination, and departure date.
- Retrieve live flight offers via the Amadeus API.
- Display key details: airline, route, time, and price.

✅ **Hotel Search**
- Filter by city, check-in/out dates, and star rating.
- Browse hotel offers with prices and IDs.
- Uses `amadeus.reference_data.locations.hotels.by_city` and `hotel_offers_search` endpoints.

✅ **Booking Simulation**
- Confirm bookings using mock traveler and payment data.
- Logs responses and confirmations to the console.
- Safe to use in sandbox (no real transactions).

✅ **Streamlit Sidebar Controls**
- Quick, interactive UI for input and filtering.
- Select filters (e.g. hotel stars ⭐⭐⭐⭐).
- Dynamic response rendering.

---

## 🧩 Tech Stack

| Layer | Technology |
|:------|:------------|
| **Frontend/UI** | Streamlit |
| **Backend Logic** | Python |
| **API Integration** | Amadeus SDK |
| **Environment Management** | `os` (for API keys) |
| **Data Handling** | Native Python + Streamlit widgets |

---

## 🚀 Getting Started

### 1️⃣ Clone the repository
```bash
git clone https://github.com/yourusername/travel-planner.git
cd travel-planner
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Configure your Amadeus and Google AI Studio credentials  
Open the project files and replace each placeholder labeled `"INSERT YOUR OWN"` with your personal API keys from the [**Amadeus for Developers Portal**](https://developers.amadeus.com/) and [**Google AI Studio**](https://aistudio.google.com/).

### 4️⃣ Run the app  
Launch the application by running Streamlit and specifying the path to the `travelagent.py` file:

```bash
streamlit run travelagent.py
```
💡Note: Make sure you’re executing this command from a directory where Streamlit is installed and your virtual environment (if any) is active.



