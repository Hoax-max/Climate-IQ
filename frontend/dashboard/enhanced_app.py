"""
Enhanced Streamlit application for Climate Action Intelligence Platform
With comprehensive heat maps, real-time data, and advanced visualizations
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import json
import os
import sys
from datetime import datetime, timedelta
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.rag_system.climate_rag import ClimateRAGSystem
from backend.api_handlers.climate_apis import ClimateAPIHandler
from backend.data_processors.impact_tracker import ImpactTracker
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="ClimateIQ - AI Climate Action Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #2E8B57, #228B22, #32CD32);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #f0f8f0, #e8f5e8);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #228B22;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .action-card {
        background: linear-gradient(135deg, #f8f9fa, #ffffff);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .heat-map-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stats-container {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .warning-box {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: 1px solid #ffc107;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        border: 1px solid #28a745;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_systems():
    """Initialize backend systems"""
    try:
        rag_system = ClimateRAGSystem()
        rag_system.initialize_with_sample_data()
        
        api_handler = ClimateAPIHandler()
        impact_tracker = ImpactTracker()
        
        return rag_system, api_handler, impact_tracker
    except Exception as e:
        st.error(f"Error initializing systems: {e}")
        return None, None, None

def create_emissions_heat_map(api_handler, bounds=None, year=2022, sector=None):
    """Create an interactive emissions heat map"""
    try:
        # Get heat map data
        heat_data = api_handler.get_emissions_heat_map_data(bounds, year, sector)
        
        if 'error' in heat_data:
            st.error(f"Error loading heat map data: {heat_data['error']}")
            return None
        
        # Create base map
        center_lat = (bounds['north'] + bounds['south']) / 2 if bounds else 20
        center_lon = (bounds['east'] + bounds['west']) / 2 if bounds else 0
        
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=4,
            tiles='OpenStreetMap'
        )
        
        # Add heat map points
        heat_points = []
        for point in heat_data.get('points', []):
            if point['intensity'] > 0:
                heat_points.append([
                    point['lat'], 
                    point['lon'], 
                    min(point['intensity'] / 1000, 1.0)  # Normalize intensity
                ])
                
                # Add marker for major sources
                if point['intensity'] > 100000:  # Major emitters
                    folium.CircleMarker(
                        location=[point['lat'], point['lon']],
                        radius=max(5, min(point['intensity'] / 50000, 20)),
                        popup=f"{point['name']}<br>Emissions: {point['intensity']:,.0f} tons CO2e",
                        color='red',
                        fillColor='red',
                        fillOpacity=0.6
                    ).add_to(m)
        
        # Add heat map layer
        if heat_points:
            from folium.plugins import HeatMap
            HeatMap(
                heat_points,
                min_opacity=0.2,
                max_zoom=18,
                radius=15,
                blur=10,
                gradient={0.4: 'blue', 0.65: 'lime', 0.8: 'orange', 1.0: 'red'}
            ).add_to(m)
        
        return m, heat_data
        
    except Exception as e:
        st.error(f"Error creating heat map: {e}")
        return None, None

def display_global_dashboard(api_handler):
    """Display global emissions dashboard"""
    st.header("🌍 Global Emissions Dashboard")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔥 Global Emissions Heat Map")
        
        # Heat map controls
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            year = st.selectbox("Year", [2022, 2021, 2020], key="heatmap_year")
        with col_b:
            sector = st.selectbox("Sector", [
                None, "power", "transportation", "buildings", 
                "fossil-fuel-operations", "manufacturing", "agriculture"
            ], key="heatmap_sector")
        with col_c:
            if st.button("🔄 Update Heat Map"):
                st.rerun()
        
        # Create and display heat map
        heat_map, heat_data = create_emissions_heat_map(api_handler, year=year, sector=sector)
        
        if heat_map:
            st_folium(heat_map, width=700, height=500)
            
            if heat_data:
                st.info(f"📊 Showing {heat_data['total_sources']} emission sources for {year}")
        else:
            st.warning("Heat map data temporarily unavailable. Showing sample visualization.")
            
            # Create sample heat map with mock data
            sample_data = pd.DataFrame({
                'lat': np.random.uniform(-60, 60, 100),
                'lon': np.random.uniform(-120, 120, 100),
                'emissions': np.random.exponential(1000, 100)
            })
            
            fig = px.density_mapbox(
                sample_data, 
                lat='lat', 
                lon='lon', 
                z='emissions',
                radius=10,
                center=dict(lat=20, lon=0),
                zoom=2,
                mapbox_style="open-street-map",
                title="Sample Global Emissions Heat Map"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Key Statistics")
        
        # Get global overview
        overview = api_handler.get_global_emissions_overview(year)
        
        if 'error' not in overview:
            st.metric(
                "🌍 Global Emissions", 
                f"{overview.get('total_global_emissions', 0):,.0f} Mt CO2e",
                help="Total global CO2 equivalent emissions"
            )
            
            # Top emitting countries
            st.markdown("### 🏆 Top Emitting Countries")
            top_countries = overview.get('top_countries', [])[:5]
            
            for i, country in enumerate(top_countries):
                st.write(f"{i+1}. **{country['country']}**: {country['emissions']:,.0f} Mt")
        else:
            # Sample data
            st.metric("🌍 Global Emissions", "36,700 Mt CO2e")
            st.markdown("### 🏆 Top Emitting Countries")
            sample_countries = [
                "China: 11,472 Mt", "United States: 5,007 Mt", 
                "India: 2,709 Mt", "Russia: 1,756 Mt", "Japan: 1,107 Mt"
            ]
            for country in sample_countries:
                st.write(f"• {country}")
        
        # Sector breakdown
        st.markdown("### 🏭 Emissions by Sector")
        sector_data = pd.DataFrame({
            'Sector': ['Power', 'Transportation', 'Manufacturing', 'Buildings', 'Agriculture'],
            'Emissions': [14500, 8200, 6100, 3900, 2800]
        })
        
        fig = px.pie(
            sector_data, 
            values='Emissions', 
            names='Sector',
            title="Global Emissions by Sector (Mt CO2e)"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

def display_location_analysis(api_handler):
    """Display location-specific climate analysis"""
    st.header("📍 Location Climate Analysis")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎯 Select Location")
        
        # Location input methods
        input_method = st.radio("Input Method", ["City Name", "Coordinates"])
        
        if input_method == "City Name":
            location = st.text_input("Enter city name", value="New York, NY")
            # Convert to coordinates (simplified)
            lat, lon = 40.7128, -74.0060  # Default to NYC
        else:
            lat = st.number_input("Latitude", value=40.7128, format="%.4f")
            lon = st.number_input("Longitude", value=-74.0060, format="%.4f")
        
        if st.button("🔍 Analyze Location"):
            with st.spinner("Analyzing location..."):
                # Get comprehensive location profile
                profile = api_handler.get_location_climate_profile(lat, lon)
                
                if 'error' not in profile:
                    st.session_state.location_profile = profile
                    st.success("✅ Analysis complete!")
                else:
                    st.error(f"Error: {profile['error']}")
    
    with col2:
        st.subheader("🌡️ Climate Profile")
        
        if 'location_profile' in st.session_state:
            profile = st.session_state.location_profile
            
            # Weather information
            weather = profile.get('weather', {})
            if 'error' not in weather:
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("🌡️ Temperature", f"{weather.get('temperature', 0):.1f}°C")
                with col_b:
                    st.metric("💧 Humidity", f"{weather.get('humidity', 0)}%")
                with col_c:
                    st.metric("💨 Wind Speed", f"{weather.get('wind_speed', 0):.1f} m/s")
            
            # Air quality
            air_quality = profile.get('air_quality', {})
            if 'error' not in air_quality:
                aqi = air_quality.get('aqi', 1)
                aqi_levels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
                aqi_colors = {1: "green", 2: "lightgreen", 3: "yellow", 4: "orange", 5: "red"}
                
                st.markdown(f"**Air Quality:** <span style='color: {aqi_colors[aqi]}'>{aqi_levels[aqi]} (AQI: {aqi})</span>", 
                          unsafe_allow_html=True)
            
            # Renewable energy potential
            renewable = profile.get('renewable_potential', {})
            if 'error' not in renewable:
                col_a, col_b = st.columns(2)
                with col_a:
                    solar_potential = renewable.get('solar_potential', 'Unknown')
                    solar_color = {"High": "green", "Medium": "orange", "Low": "red"}.get(solar_potential, "gray")
                    st.markdown(f"**☀️ Solar Potential:** <span style='color: {solar_color}'>{solar_potential}</span>", 
                              unsafe_allow_html=True)
                with col_b:
                    wind_potential = renewable.get('wind_potential', 'Unknown')
                    wind_color = {"High": "green", "Medium": "orange", "Low": "red"}.get(wind_potential, "gray")
                    st.markdown(f"**💨 Wind Potential:** <span style='color: {wind_color}'>{wind_potential}</span>", 
                              unsafe_allow_html=True)
            
            # Nearby emissions sources
            emissions = profile.get('nearby_emissions', {})
            if 'error' not in emissions and 'emissions_sources' in emissions:
                st.subheader("🏭 Nearby Emission Sources")
                sources = emissions['emissions_sources']
                if isinstance(sources, list) and sources:
                    for source in sources[:5]:  # Show top 5
                        name = source.get('properties', {}).get('name', 'Unknown Source')
                        st.write(f"• {name}")
                else:
                    st.info("No major emission sources detected in the area")
        else:
            st.info("👆 Select a location above to see detailed climate analysis")

def display_sector_deep_dive(api_handler):
    """Display detailed sector analysis"""
    st.header("🏭 Sector Deep Dive")
    
    # Sector selection
    sectors = [
        "power", "transportation", "buildings", "fossil-fuel-operations",
        "manufacturing", "mineral-extraction", "agriculture", "waste",
        "fluorinated-gases", "forestry-and-land-use"
    ]
    
    selected_sector = st.selectbox("Select Sector for Analysis", sectors)
    year = st.selectbox("Year", [2022, 2021, 2020], key="sector_year")
    
    if st.button("📊 Analyze Sector"):
        with st.spinner(f"Analyzing {selected_sector} sector..."):
            analysis = api_handler.get_sector_analysis(selected_sector, year)
            
            if 'error' not in analysis:
                st.session_state.sector_analysis = analysis
                st.success("✅ Sector analysis complete!")
            else:
                st.error(f"Error: {analysis['error']}")
    
    if 'sector_analysis' in st.session_state:
        analysis = st.session_state.sector_analysis
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"📈 {selected_sector.title()} Sector Overview")
            
            # Sector emissions summary
            sector_emissions = analysis.get('sector_emissions', [])
            if sector_emissions:
                total_emissions = sum(item.get('Emissions', 0) for item in sector_emissions if isinstance(item, dict))
                st.metric("Total Sector Emissions", f"{total_emissions:,.0f} Mt CO2e")
            
            # Country breakdown
            country_breakdown = analysis.get('country_breakdown', [])
            if country_breakdown:
                st.subheader("🌍 Top Countries in Sector")
                df = pd.DataFrame(country_breakdown[:10])
                if not df.empty and 'Country' in df.columns:
                    fig = px.bar(
                        df.head(10), 
                        x='Country', 
                        y='Emissions' if 'Emissions' in df.columns else df.columns[1],
                        title=f"Top 10 Countries - {selected_sector.title()} Emissions"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🏭 Major Sources")
            
            major_sources = analysis.get('major_sources', [])
            if major_sources and isinstance(major_sources, list):
                for i, source in enumerate(major_sources[:5]):
                    if isinstance(source, dict):
                        name = source.get('properties', {}).get('name', f'Source {i+1}')
                        location = source.get('properties', {}).get('location', 'Unknown')
                        st.write(f"**{i+1}. {name}**")
                        st.write(f"   📍 Location: {location}")
                        
                        # Emissions data
                        emissions = source.get('emissions', [])
                        if emissions:
                            for emission in emissions:
                                if emission.get('gas') == 'co2e':
                                    st.write(f"   🌱 Emissions: {emission.get('quantity', 0):,.0f} tons CO2e")
                                    break
                        st.write("---")
            else:
                st.info("No detailed source information available for this sector")

def main():
    """Main application function"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌍 ClimateIQ - Advanced Climate Intelligence Platform</h1>
        <p>Real-time climate data, emissions tracking, and AI-powered insights for climate action</p>
        <p><strong>Powered by IBM watsonx.ai • Climate TRACE • Real-time APIs</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize systems
    rag_system, api_handler, impact_tracker = initialize_systems()
    
    # Check if systems initialized properly
    if not all([rag_system, api_handler, impact_tracker]):
        st.markdown("""
        <div class="warning-box">
            <h4>⚠️ Demo Mode Active</h4>
            <p>Some backend services are not fully configured. The platform is running in demonstration mode with sample data and limited functionality.</p>
            <p><strong>For full functionality:</strong> Configure API keys in the .env file</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="success-box">
            <h4>✅ All Systems Online</h4>
            <p>Climate data APIs, AI systems, and real-time monitoring are fully operational.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Sidebar for navigation and user profile
    with st.sidebar:
        st.header("🎛️ Navigation")
        
        page = st.selectbox("Select View", [
            "🌍 Global Dashboard",
            "📍 Location Analysis", 
            "🏭 Sector Deep Dive",
            "🎯 Action Plan",
            "📊 Impact Tracker",
            "💬 AI Assistant",
            "🏆 Community"
        ])
        
        st.header("👤 Your Profile")
        
        # User identification
        user_id = st.text_input("User ID", value="demo_user", help="Enter a unique identifier")
        
        # Location and basic info
        location = st.text_input("📍 Location", value="New York, NY", help="Enter your city, state/country")
        lifestyle = st.selectbox("🏠 Lifestyle", ["Urban", "Suburban", "Rural"])
        household_size = st.number_input("👥 Household Size", min_value=1, max_value=10, value=2)
        
        # Interests and goals
        st.subheader("🎯 Climate Goals")
        interests = st.multiselect(
            "Areas of Interest",
            ["Energy Efficiency", "Renewable Energy", "Transportation", "Food & Diet", "Waste Reduction", "Water Conservation"],
            default=["Energy Efficiency", "Transportation"]
        )
        
        budget = st.selectbox("💰 Budget for Climate Actions", ["Low ($0-500)", "Medium ($500-2000)", "High ($2000+)"])
        
        # Current actions
        current_actions = st.text_area("Current Climate Actions", 
                                     placeholder="Describe any climate actions you're already taking...")
    
    # User profile dictionary
    user_profile = {
        'user_id': user_id,
        'location': location,
        'lifestyle': lifestyle,
        'household_size': household_size,
        'interests': interests,
        'budget': budget,
        'current_actions': current_actions
    }
    
    # Display selected page
    if page == "🌍 Global Dashboard":
        display_global_dashboard(api_handler)
    elif page == "📍 Location Analysis":
        display_location_analysis(api_handler)
    elif page == "🏭 Sector Deep Dive":
        display_sector_deep_dive(api_handler)
    elif page == "🎯 Action Plan":
        from frontend.dashboard.main_app import display_action_plan
        display_action_plan(rag_system, user_profile, not all([rag_system, api_handler, impact_tracker]))
    elif page == "📊 Impact Tracker":
        from frontend.dashboard.main_app import display_impact_tracker
        display_impact_tracker(impact_tracker, user_id, not all([rag_system, api_handler, impact_tracker]))
    elif page == "💬 AI Assistant":
        from frontend.dashboard.main_app import display_ai_assistant
        display_ai_assistant(rag_system, user_profile, not all([rag_system, api_handler, impact_tracker]))
    elif page == "🏆 Community":
        from frontend.dashboard.main_app import display_community
        display_community(impact_tracker, not all([rag_system, api_handler, impact_tracker]))

if __name__ == "__main__":
    main()