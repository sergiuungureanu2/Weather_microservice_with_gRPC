import dash
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
from datetime import datetime, timezone
from client.weather_client import get_current_weather, get_weather_history


app = Dash(__name__, external_stylesheets=["https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.css"])
app.title = " Weather Dashboard"

DEFAULT_CITY = "Iasi"
REFRESH_INTERVAL = 60 * 1000  #60sec


app.layout = html.Div([
    html.H1(" Weather Insights", className="ui header center aligned", style={"marginTop": "20px"}),

    html.Div([
        html.Div([
            html.Label("Select City:", className="ui header"),
            dcc.Input(id="city-input", type="text", placeholder="Enter city name...", value=DEFAULT_CITY,
                      className="ui input", style={"marginRight": "10px"}),
            html.Button("Update", id="update-btn", n_clicks=0, className="ui blue button")
        ], className="ui center aligned segment"),
    ]),

    html.Div(id="current-weather", className="ui raised segment center aligned", style={"margin": "20px"}),

    html.Div([
        html.Div([
            html.H3(" Temperature Trend", className="ui header center aligned"),
            dcc.Graph(id="temperature-chart", style={"height": "400px"})
        ], className="eight wide column"),

        html.Div([
            html.H3(" Humidity Trend", className="ui header center aligned"),
            dcc.Graph(id="humidity-chart", style={"height": "400px"})
        ], className="eight wide column"),
    ], className="ui grid"),

    html.Div(id="last-update", className="ui center aligned small header", style={"marginTop": "20px"}),

    dcc.Interval(id="refresh-timer", interval=REFRESH_INTERVAL, n_intervals=0)
], className="ui container")

@app.callback(
    [Output("current-weather", "children"),
     Output("temperature-chart", "figure"),
     Output("humidity-chart", "figure"),
     Output("last-update", "children")],
    [Input("refresh-timer", "n_intervals"),
     Input("update-btn", "n_clicks"),
     Input("city-input", "value")]
)
def update_dashboard(n_intervals, n_clicks, city):
    if not city:
        city = DEFAULT_CITY
    else:
        city = city.strip()


    try:
        current = get_current_weather(city)
    except Exception as e:
        current = {"error": f"Failed to fetch current weather: {e}"}

    try:
        history = get_weather_history(city, limit=50)
    except Exception as e:
        history = []
        current_display = html.Div(f"Error fetching history: {e}", className="ui red message")

    if "error" in current:
        current_display = html.Div(f" Error: {current['error']}", className="ui red message")
    else:
        api_time = current.get("api_timestamp")
        req_time = current.get("request_timestamp")
        api_time_str = datetime.fromtimestamp(api_time).strftime("%Y-%m-%d %H:%M:%S") if api_time else "Unknown"
        req_time_str = datetime.fromtimestamp(req_time).strftime("%Y-%m-%d %H:%M:%S") if req_time else "Unknown"

        current_display = html.Div([
            html.H2(f"Weather in {current['city']}, {current['country']}", className="ui header"),
            html.Div([
                html.P(f" Temperature: {current['temperature']} °C"),
                html.P(f" Humidity: {current['humidity']}%"),
                html.P(f" Wind Speed: {current['wind_speed']} m/s"),
                html.P(f" Conditions: {current['description']}"),
                html.P(f" Observation time: {api_time_str}"),
                html.P(f" Request time: {req_time_str}")
            ], className="ui relaxed list", style={"fontSize": "16px"})
        ])

    if history:
        times, temps, hums = [], [], []
        for entry in history:
            if entry.get("datetime"):
                local_dt = entry["datetime"].replace(tzinfo=timezone.utc).astimezone()
                time_str = local_dt.strftime("%Y-%m-%d %H:%M:%S")
            elif entry.get("timestamp"):
                time_str = datetime.fromtimestamp(entry["timestamp"]).astimezone().strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = "Unknown"

            times.append(time_str)
            temps.append(entry.get("temperature", 0))
            hums.append(entry.get("humidity", 0))

        temp_fig = px.line(
            x=times, y=temps, markers=True,
            labels={"x": "Time", "y": "Temperature (°C)"},
            title=f"Temperature Trend for {city}",
        )
        temp_fig.update_traces(line_color="#ff7f0e")
        temp_fig.update_layout(plot_bgcolor="#f9f9f9")

        hum_fig = px.line(
            x=times, y=hums, markers=True,
            labels={"x": "Time", "y": "Humidity (%)"},
            title=f"Humidity Trend for {city}",
        )
        hum_fig.update_traces(line_color="#1f77b4")
        hum_fig.update_layout(plot_bgcolor="#f9f9f9")

    else:
        temp_fig = px.line(title="No historical temperature data available")
        hum_fig = px.line(title="No historical humidity data available")

    last_update = f" Last auto-refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    return current_display, temp_fig, hum_fig, last_update


if __name__ == "__main__":
    app.run(debug=True, port=8050)
