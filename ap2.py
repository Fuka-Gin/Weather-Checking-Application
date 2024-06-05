import tkinter as tk
import requests
from pymongo import MongoClient
import pymongo
from datetime import datetime, timezone
from tenacity import retry, wait_exponential, stop_after_attempt

# Set up MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["WeatherApplication"]
collection = db["WeatherData"]

# Function to get weather data from OpenWeatherMap API
@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def get_weather(city_name):
    api_key = "e67d26ea926e3c5313b292170b4574a8"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        weather_data = response.json()

        if "name" in weather_data:
            city_name = weather_data["name"]
            weather_condition = weather_data["weather"][0]["description"]
            temperature = weather_data["main"]["temp"]
            humidity = float(weather_data["main"]["humidity"])
            wind_speed = float(weather_data["wind"]["speed"])
            current_timestamp = datetime.now(timezone.utc)

            weather_info = {
                "location": city_name, 
                "weather_condition": weather_condition,
                "temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "timestamp": current_timestamp
            }
            return weather_info
        else:
            return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None
        else:
            raise

# Function to store weather data in MongoDB
def store_weather_data(weather_info):
    if weather_info:
        collection.insert_one(weather_info)
        print("Weather data stored successfully.")
    else:
        print("No weather data to store.")

# Function to retrieve historical weather data from MongoDB
def get_historical_weather(city):
    query = {"location": city}
    historical_weather_data = collection.find(query).sort("timestamp", pymongo.DESCENDING).skip(1).limit(11)
    historical_weather_list = list(historical_weather_data)
    
    return historical_weather_list

# Function to display current and historical weather data in the Tkinter GUI
def display_weather():
    city = entry.get()
    current_weather_info = get_weather(city)
    if current_weather_info:
        store_weather_data(current_weather_info)
        
        historical_weather = get_historical_weather(city)
        
        weather_info = "Current Weather:\n"
        weather_info += (f"Weather: {current_weather_info['weather_condition']}, "
                        f"Temperature: {current_weather_info['temperature']}°C, "
                        f"Humidity: {current_weather_info['humidity']}%, "
                        f"Wind Speed: {current_weather_info['wind_speed']} m/s\n\n")

        for idx, data in enumerate(historical_weather):
            time_label = f"{idx + 1} hour{'s' if idx + 1 > 1 else ''} ago"
            weather_info += (f"{time_label}: Weather: {data['weather_condition']}, "
                            f"Temperature: {data['temperature']}°C, "
                            f"Humidity: {data['humidity']}%, "
                            f"Wind Speed: {data['wind_speed']} m/s\n")
        
        label.config(text=weather_info)
    else:
        label.config(text="City not found. Please enter a valid city name.")

# Setup Tkinter GUI
app = tk.Tk()
app.title("Weather App")

canvas = tk.Canvas(app, height=400, width=300)
canvas.pack()

frame = tk.Frame(app, bg="#80c1ff", bd=5)
frame.place(relx=0.5, rely=0.1, relwidth=0.75, relheight=0.1, anchor="n")

entry = tk.Entry(frame, font=("Arial", 14))
entry.place(relwidth=0.65, relheight=1)

button = tk.Button(frame, text="Get Weather", font=("Arial", 12), command=display_weather)
button.place(relx=0.7, relheight=1, relwidth=0.3)

lower_frame = tk.Frame(app, bg="#80c1ff", bd=10)
lower_frame.place(relx=0.5, rely=0.25, relwidth=0.75, relheight=0.6, anchor="n")

label = tk.Label(lower_frame, font=("Arial", 16), anchor="nw", justify="left", bd=4)
label.place(relwidth=1, relheight=1)

app.mainloop()