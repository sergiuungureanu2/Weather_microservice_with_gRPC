from datetime import datetime
from client.weather_client import (
    get_current_weather,
    get_weather_history,
    get_full_weather
)


def print_weather(result):
    print("\nWeather Report")
    print("-" * 30)
    print(f"City: {result['city']}, {result['country']}")
    print(f"Temperature: {result['temperature']:.2f} °C")
    print(f"Feels like: {result['feels_like']:.2f} °C")
    print(f"Humidity: {result['humidity']}%")
    print(f"Wind Speed: {result['wind_speed']} m/s")
    print(f"Conditions: {result['description']}")
    print(f"Cloudiness: {result['clouds']}%")
    print("-" * 30)
    local_time = datetime.fromtimestamp(result['timestamp'])
    print(f"Local time: {local_time.strftime('%Y-%m-%d %H:%M:%S')}\n")



def cli_client():
    print("\nWeather CLI connected. Ready to fetch data.")

    while True:
        print("\nOptions:")
        print("1. Get current weather")
        print("2. Get weather history (latest entries)")
        print("3. Get full weather overview (current + history)")
        print("4. Exit")

        choice = input("Choose an option: ").strip()
        if choice == "1":
            city = input("Enter city name: ").strip()
            result = get_current_weather(city)
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print_weather(result)

        elif choice == "2":
            city = input("Enter city name: ").strip()
            limit = input("How many entries (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10

            history = get_weather_history(city, limit=limit)
            if not history:
                print(f"No history found for {city}.")
                continue

            print(f"\nLatest {len(history)} records for {city}:")
            print("-" * 70)
            for entry in history:
                if entry.get("datetime"):
                    date = entry["datetime"].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    date = datetime.fromtimestamp(entry.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")

                print(f"{date} | Temperature: {entry['temperature']}°C | Humidity: {entry['humidity']}% | Conditions: {entry['description']}")
            print("-" * 70)

        elif choice == "3":
            city = input("Enter city name: ").strip()
            limit = input("How many past records (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10

            data = get_full_weather(city, history_limit=limit)
            if "error" in data:
                print(f"Error: {data['error']}")
                continue

            print_weather(data["current"])

            print(f"Historical data for {city} (last {len(data['history'])} entries):")
            print("-" * 70)
            for entry in data["history"]:
                if entry.get("datetime"):
                    date = entry["datetime"].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    date = datetime.fromtimestamp(entry.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")

                print(f"{date} | Temperature: {entry['temperature']}°C | Humidity: {entry['humidity']}% | Conditions: {entry['description']}")
            print("-" * 70)

        elif choice == "4":
            print("Goodbye!")
            break

        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    cli_client()
