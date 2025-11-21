# Weather Microservice with gRPC

## Project Goal
Build a simple client-server application using gRPC in Python where:
- The server fetches live weather data for a given city using a public weather API (OpenWeatherMap).
- The client sends the city name and receives the weather details in a clean output.

## Functional Requirements
### gRPC Server
- Accepts a city name from the client.
- Calls a weather API to retrieve current weather data.
- Returns:
  - City Name
  - Temperature (Celsius)
  - Weather Description (e.g., Clear, Cloudy)
  - Humidity (%)
  - Wind speed (optional)
- Saves extracted data in a MongoDB database.
- Protects the gRPC endpoint with an API key (`x-api-key`).

### gRPC Client
- CLI for the user to:
  - Input a city name
  - Display the weather data
- Handles errors gracefully (e.g., unknown city, API failure)

### Frontend (Dash)
- Simple UI to display a chart showing temperature fluctuation over time for a selected city.

## External API: OpenWeatherMap
- **Endpoint:**
  `http://api.openweathermap.org/data/2.5/weather?q={city name}&appid={API key}&units=metric`
- **How to use:**
  - Sign up at https://openweathermap.org/
  - Generate a free API key.
  - Free tier: 60 requests/minute.

## Suggested Architecture
```
client.py ---> grpc server (weather_server.py) ---> OpenWeatherMap API
   |                |\
   |                +--> MongoDB (for history)
   |
   +--> Dash frontend (dashboard.py)
```

## Example Usage
```
$ python client.py
Enter city name: London

Weather for London:
Temperature: 18.6 °C
Humidity: 82%
Conditions: light rain
Wind Speed: 4.6 m/s
```

## Development Tips
- Use `grpc_tools.protoc` to generate Python files from `.proto`.
- Use try-except blocks to handle invalid city names or HTTP errors.
- Save weather data in MongoDB for historical charting.
- Create unit/integration tests for both server and client logic.
- Use Docker for containerization (all services can run in one or multiple containers).
- Protect the gRPC endpoint with an API key (`x-api-key`).

## Running with Docker
1. Build and start all services:
   ```
   docker compose up --build
   ```
2. Access the Dash frontend at [http://localhost:18050](http://localhost:18050) (or the port you mapped).
3. The gRPC server and MongoDB run in the background.

## Testing
- Unit and integration tests are in the `tests/` folder.
- Run with pytest:
  ```
  pytest
  ```

## API Key Protection
- The gRPC server requires an API key in the `x-api-key` metadata for all requests.
- Set your key in the `.env` file and client configuration.

---
