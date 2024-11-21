import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import folium
from datetime import datetime
from streamlit_folium import st_folium

# API Configurations
OPENWEATHER_API_KEY = "6be3dabbe9def2d145988325a818e95a"
AQICN_API_KEY = "YOUR_AQI_API_KEY"  # You'll need to sign up for an AQI API key
BASE_URL = "http://api.openweathermap.org/data/2.5"
AQI_BASE_URL = "https://api.waqi.info/feed"

def get_air_quality_data(lat, lon):
    """Fetch air quality data for given coordinates."""
    try:
        url = f"{AQI_BASE_URL}/geo:{lat};{lon}/?token={AQICN_API_KEY}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'ok':
                return data['data']
        return None
    except Exception as e:
        st.error(f"Air Quality Data Error: {e}")
        return None

def get_pollen_risk_level(pollen_count):
    """Determine pollen risk level."""
    if pollen_count < 30:
        return "Low", "🟢 Low Risk"
    elif 30 <= pollen_count < 50:
        return "Moderate", "🟡 Moderate Risk"
    elif 50 <= pollen_count < 80:
        return "High", "🟠 High Risk"
    else:
        return "Very High", "🔴 Very High Risk"

def get_weather_condition_style(condition):
    """Dynamically style based on weather condition."""
    condition_styles = {
        'Thunderstorm': {
            'background': 'linear-gradient(135deg, #373B44, #4286f4)',
            'text_color': 'white',
            'warning_level': 'High Alert ⚡',
            'icon': '⛈️'
        },
        'Drizzle': {
            'background': 'linear-gradient(135deg, #83a4d4, #b6fbff)',
            'text_color': 'navy',
            'warning_level': 'Mild Rain ☔',
            'icon': '🌧️'
        },
        'Rain': {
            'background': 'linear-gradient(135deg, #2c3e50, #3498db)',
            'text_color': 'white',
            'warning_level': 'Heavy Rain 🌊',
            'icon': '🌧️'
        },
        'Snow': {
            'background': 'linear-gradient(135deg, #a1c4fd, #white)',
            'text_color': 'navy',
            'warning_level': 'Snowfall ❄️',
            'icon': '❄️'
        },
        'Clear': {
            'background': 'linear-gradient(135deg, #56ccf2, #2f80ed)',
            'text_color': 'white',
            'warning_level': 'Sunny Day ☀️',
            'icon': '☀️'
        },
        'Clouds': {
            'background': 'linear-gradient(135deg, #bdc3c7, #2c3e50)',
            'text_color': 'white',
            'warning_level': 'Cloudy Day ☁️',
            'icon': '☁️'
        },
        'default': {
            'background': 'linear-gradient(135deg, #f5f7fa, #c3cfe2)',
            'text_color': 'black',
            'warning_level': 'Normal Conditions 🌈',
            'icon': '🌈'
        }
    }
    
    return condition_styles.get(condition, condition_styles['default'])

def simulate_pollen_count(temp, humidity):
    """Simulate pollen count based on temperature and humidity."""
    # Simple simulation logic
    base_pollen = 20
    temp_factor = (temp - 15) * 2  # More pollen in warmer temperatures
    humidity_factor = humidity / 10
    
    pollen_count = base_pollen + temp_factor + humidity_factor
    return max(0, min(pollen_count, 100))  # Normalize between 0-100

def get_weather_data(city):
    """Enhanced weather data fetching with additional context."""
    try:
        # Current Weather
        current_url = f"{BASE_URL}/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        current_response = requests.get(current_url)
        
        if current_response.status_code != 200:
            st.error(f"Error: {current_response.status_code}")
            return None
        
        current_data = current_response.json()
        
        # Forecast
        forecast_url = f"{BASE_URL}/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        forecast_response = requests.get(forecast_url)
        
        if forecast_response.status_code != 200:
            st.error(f"Forecast Error: {forecast_response.status_code}")
            return None
        
        forecast_data = forecast_response.json()
        
        # Air Quality Data
        lat = current_data['coord']['lat']
        lon = current_data['coord']['lon']
        air_quality_data = get_air_quality_data(lat, lon)
        
        # Simulate Pollen Count
        pollen_count = simulate_pollen_count(
            current_data['main']['temp'], 
            current_data['main']['humidity']
        )
        
        return {
            'current': current_data,
            'forecast': forecast_data,
            'air_quality': air_quality_data,
            'pollen_count': pollen_count
        }
    
    except Exception as e:
        st.error(f"Unexpected Error: {e}")
        return None
    
def create_forecast_dataframe(forecast_data):
    """
    Create a pandas DataFrame from OpenWeatherMap forecast data.
    
    Args:
        forecast_data (dict): The forecast data from OpenWeatherMap API
        
    Returns:
        pandas.DataFrame: Processed forecast data with datetime, temperature, humidity, and wind speed
    """
    forecast_list = []
    
    for item in forecast_data['list']:
        # Convert timestamp to datetime
        dt = datetime.fromtimestamp(item['dt'])
        
        forecast_list.append({
            'datetime': dt,
            'temp': item['main']['temp'],
            'feels_like': item['main']['feels_like'],
            'humidity': item['main']['humidity'],
            'wind_speed': item['wind']['speed'],
            'description': item['weather'][0]['description'],
            'main_weather': item['weather'][0]['main']
        })
    
    # Create DataFrame
    df = pd.DataFrame(forecast_list)
    
    # Add some derived columns that might be useful for analysis
    df['hour'] = df['datetime'].dt.hour
    df['date'] = df['datetime'].dt.date
    
    # Calculate daily aggregates
    df['daily_temp_avg'] = df.groupby('date')['temp'].transform('mean')
    df['daily_humidity_avg'] = df.groupby('date')['humidity'].transform('mean')
    df['daily_wind_avg'] = df.groupby('date')['wind_speed'].transform('mean')
    
    return df

def main():
    # Page Configuration
    st.set_page_config(
        page_title="WeatherPro Enhanced", 
        page_icon="🌈", 
        layout="wide"
    )
    
    # Custom CSS for Enhanced Styling
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        transform: scale(1.05);
        background-color: rgba(255,255,255,0.2);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        color: white;
        box-shadow: 0 15px 30px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Animated Gradient Title
    st.markdown("""
    <h1 style="
        background : linear-gradient(45deg, #ff6b6b, #4ecdc4, #45aaf2);
        background-size: 200% auto;
        color: #000;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
        text-align: center;
        padding: 20px;
        font-size: 3rem;
    ">
    🌈 WeatherPro: Advanced Forecast Explorer
    </h1>
    <style>
    @keyframes shine {
        to { background-position: 200% center; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # City Input with Enhanced Styling
    col_search, col_geo = st.columns([3, 1])
    
    with col_search:
        city = st.text_input("Enter City Name", "London", 
                            help="Explore weather insights for any city")
    
    if city:
        weather_data = get_weather_data(city)
        
        if weather_data:
            current = weather_data['current']
            condition_main = current['weather'][0]['main']
            condition_style = get_weather_condition_style(condition_main)
            
            # Dynamic Weather Condition Card
            st.markdown(f"""
            <div style="background: {condition_style['background']}; 
                        color: {condition_style['text_color']}; 
                        padding: 20px; 
                        border-radius: 15px;">
                <h2>{condition_style['icon']} {condition_main} Conditions</h2>
                <h3>Warning Level: {condition_style['warning_level']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Current Weather Card
            st.markdown(f"""
            <div class="metric-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="margin-bottom: 10px;">{city.capitalize()}, {current.get('sys', {}).get('country', '')}</h2>
                        <h3 style="color: #e0e0e0; margin-bottom: 15px;">{current['weather'][0]['description'].capitalize()}</h3>
                    </div>
                    <img src="http://openweathermap.org/img/wn/{current['weather'][0]['icon']}@2x.png" width="120" style="filter: drop-shadow(0 0 10px rgba(0,0,0,0.3));">
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 15px;">
                    <div>
                        <h4>🌡️ Temperature: {current['main']['temp']}°C</h4>
                        <h4>🌡️ Feels Like: {current['main']['feels_like']}°C</h4>
                    </div>
                    <div>
                        <h4>💧 Humidity: {current['main']['humidity']}%</h4>
                        <h4>💨 Wind: {current['wind']['speed']} m/s</h4>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Air Quality Section
            if weather_data.get('air_quality'):
                aqi = weather_data['air_quality']['aqi']
                aqi_text = {
                    1: "Good 🟢",
                    2: "Moderate 🟡",
                    3: "Unhealthy for Sensitive Groups 🟠",
                    4: "Unhealthy 🔴",
                    5: "Very Unhealthy 🟣"
                }
                
                st.markdown(f"""
                <div class="metric-card">
                    <h3>🌍 Air Quality Index</h3>
                    <p>AQI: {aqi} - {aqi_text.get(aqi, 'Unknown')}</p>
                    {f"<p>Dominant Pollutant: {weather_data['air_quality']['dominentpol']}</p>" if 'dominentpol' in weather_data['air_quality'] else ''}
                </div>
                """, unsafe_allow_html=True)
            
            # Pollen Count Section
            pollen_count = weather_data['pollen_count']
            pollen_risk, pollen_text = get_pollen_risk_level(pollen_count)
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>🌼 Pollen Forecast</h3>
                <p>Estimated Pollen Count: {pollen_count:.1f}</p>
                <p>Risk Level: {pollen_text}</p>
                {"<p style='color:red;'>Recommendation: Consider staying indoors if you have allergies.</p>" if pollen_risk in ['High', 'Very High'] else ""}
            </div>
            """, unsafe_allow_html=True)
            
            # Add Map Feature
            lat = current['coord']['lat']
            lon = current['coord']['lon']
            map_center = [lat, lon]
            folium_map = folium.Map(location=map_center, zoom_start=10)
            folium.Marker(location=map_center, popup=f"{city.capitalize()}").add_to(folium_map)
            st_folium(folium_map, width=700, height=500)
            
            # Forecast Data Processing and Visualization
            try:
                forecast_df = create_forecast_dataframe(weather_data['forecast'])
                
                # Animated Tabbed Visualizations
                tab1, tab2, tab3, tab4 = st.tabs([
                    "🌡️ Temperature", 
                    "💧 Humidity", 
                    "💨 Wind Forecast", 
                    "📊 Detailed Insights"
                ])
                
                with tab1:
                    fig_temp = go.Figure()
                    fig_temp.add_trace(go.Scatter(
                        x=forecast_df['datetime'], 
                        y=forecast_df['temp'],
                        mode='lines+markers',
                        name='Temperature',
                        line=dict(color='#FF6B6B', width=4, shape='spline'),
                        marker=dict(size=12, color='#FF6B6B', symbol='circle',
                                  line=dict(width=2, color='white')),
                        hovertemplate='Date: %{x}<br>Temperature: %{y}°C<extra></extra>'
                    ))
                    fig_temp.update_layout(
                        title='Temperature Trend with Smooth Interpolation',
                        xaxis_title='Date',
                        yaxis_title='Temperature (°C)',
                        template='plotly_white',
                        height=500
                    )
                    st.plotly_chart(fig_temp, use_container_width=True)
                
                # Continue with the rest of your existing visualization code...
                # (Humidity, Wind Forecast, and Detailed Insights tabs)
                
            except Exception as e:
                st.error(f"Error processing forecast data: {e}")
        else:
            st.error("Unable to fetch weather data. Please check the city name.")

if __name__ == "__main__":
    main()