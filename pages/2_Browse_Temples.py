import streamlit as st
import pandas as pd
from database import get_all_temples, search_temples
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Browse Temples", page_icon="🗂️", layout="wide")

st.title("🗂️ Browse Temples")
st.markdown("Explore documented temples with search and filtering capabilities.")

# Search and filter section
st.subheader("🔍 Search & Filter")
col1, col2, col3 = st.columns(3)

with col1:
    search_term = st.text_input("Search temples", placeholder="Name, deity, or location...")

with col2:
    architectural_styles = ["All Styles", "Dravidian", "Nagara", "Vesara", "Indo-Islamic", "Colonial", "Modern", "Other", "Unknown"]
    selected_style = st.selectbox("Architectural Style", architectural_styles)

with col3:
    sort_by = st.selectbox("Sort by", ["Most Recent", "Alphabetical", "Built Year"])

# Get temples data
if search_term:
    style_filter = None if selected_style == "All Styles" else selected_style
    temples_df = search_temples(search_term, style_filter)
else:
    temples_df = get_all_temples()
    if not temples_df.empty and selected_style != "All Styles":
        temples_df = temples_df[temples_df['architectural_style'] == selected_style]

# Apply sorting
if not temples_df.empty:
    if sort_by == "Alphabetical":
        temples_df = temples_df.sort_values('name')
    elif sort_by == "Built Year":
        temples_df = temples_df.sort_values('built_year', na_position='last')
    # Most Recent is default (already sorted by created_at DESC)

# Display results
st.subheader(f"📋 Results ({len(temples_df)} temples found)")

if temples_df.empty:
    st.info("No temples found matching your criteria. Try adjusting your search or filters.")
else:
    # Display options
    view_mode = st.radio("View Mode", ["Cards", "Table", "Map"], horizontal=True)
    
    if view_mode == "Cards":
        # Card view
        cols_per_row = 2
        for i in range(0, len(temples_df), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, (_, temple) in enumerate(temples_df.iloc[i:i+cols_per_row].iterrows()):
                with cols[j]:
                    with st.container():
                        st.markdown(f"### {temple['name']}")
                        
                        col_left, col_right = st.columns([2, 1])
                        
                        with col_left:
                            if temple['deity']:
                                st.write(f"🕉️ **Deity:** {temple['deity']}")
                            if temple['architectural_style']:
                                st.write(f"🏛️ **Style:** {temple['architectural_style']}")
                            if temple['built_year']:
                                st.write(f"📅 **Built:** {temple['built_year']}")
                            if temple['location_address']:
                                st.write(f"📍 **Location:** {temple['location_address']}")
                        
                        with col_right:
                            if temple['latitude'] and temple['longitude']:
                                st.write(f"**Coordinates:**")
                                st.write(f"{temple['latitude']:.4f}, {temple['longitude']:.4f}")
                        
                        if temple['history']:
                            with st.expander("📜 History & Significance"):
                                st.write(temple['history'])
                        
                        if temple['contributor_name']:
                            st.caption(f"Contributed by: {temple['contributor_name']}")
                        else:
                            st.caption("Contributed anonymously")
                        
                        st.caption(f"Added: {temple['created_at'].strftime('%Y-%m-%d')}")
                        st.markdown("---")
    
    elif view_mode == "Table":
        # Table view
        display_df = temples_df[['name', 'deity', 'architectural_style', 'built_year', 'location_address', 'contributor_name', 'created_at']].copy()
        display_df['created_at'] = display_df['created_at'].dt.strftime('%Y-%m-%d')
        display_df.columns = ['Name', 'Deity', 'Style', 'Built Year', 'Location', 'Contributor', 'Added Date']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Show details for selected temple
        if not display_df.empty:
            selected_temple_name = st.selectbox("Select temple for details", temples_df['name'].tolist())
            selected_temple = temples_df[temples_df['name'] == selected_temple_name].iloc[0]
            
            with st.expander(f"Details for {selected_temple_name}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Name:** {selected_temple['name']}")
                    st.write(f"**Deity:** {selected_temple['deity'] or 'Not specified'}")
                    st.write(f"**Architectural Style:** {selected_temple['architectural_style'] or 'Not specified'}")
                    st.write(f"**Built Year:** {selected_temple['built_year'] or 'Unknown'}")
                
                with col2:
                    st.write(f"**Location:** {selected_temple['location_address'] or 'Not specified'}")
                    if selected_temple['latitude'] and selected_temple['longitude']:
                        st.write(f"**Coordinates:** {selected_temple['latitude']:.6f}, {selected_temple['longitude']:.6f}")
                    st.write(f"**Contributor:** {selected_temple['contributor_name'] or 'Anonymous'}")
                    st.write(f"**Added:** {selected_temple['created_at'].strftime('%Y-%m-%d %H:%M')}")
                
                if selected_temple['history']:
                    st.write("**History & Significance:**")
                    st.write(selected_temple['history'])
    
    elif view_mode == "Map":
        # Map view
        temples_with_coords = temples_df.dropna(subset=['latitude', 'longitude'])
        
        if temples_with_coords.empty:
            st.warning("No temples with coordinates found for map display.")
        else:
            # Create map centered on mean coordinates
            center_lat = temples_with_coords['latitude'].mean()
            center_lon = temples_with_coords['longitude'].mean()
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
            
            # Add markers for each temple
            for _, temple in temples_with_coords.iterrows():
                popup_content = f"""
                <b>{temple['name']}</b><br>
                Deity: {temple['deity'] or 'Not specified'}<br>
                Style: {temple['architectural_style'] or 'Not specified'}<br>
                Built: {temple['built_year'] or 'Unknown'}<br>
                Contributor: {temple['contributor_name'] or 'Anonymous'}
                """
                
                folium.Marker(
                    location=[temple['latitude'], temple['longitude']],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=temple['name'],
                    icon=folium.Icon(color='red', icon='home')
                ).add_to(m)
            
            # Display map
            st_folium(m, width=700, height=500)
            
            st.info(f"Showing {len(temples_with_coords)} temples with location data on the map.")

# Statistics
if not temples_df.empty:
    st.markdown("---")
    st.subheader("📊 Browse Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Temples", len(temples_df))
    
    with col2:
        temples_with_coords = temples_df.dropna(subset=['latitude', 'longitude'])
        st.metric("With Coordinates", len(temples_with_coords))
    
    with col3:
        temples_with_year = temples_df.dropna(subset=['built_year'])
        if not temples_with_year.empty:
            avg_year = int(temples_with_year['built_year'].mean())
            st.metric("Avg Built Year", avg_year)
        else:
            st.metric("Avg Built Year", "N/A")
    
    with col4:
        style_counts = temples_df['architectural_style'].value_counts()
        if not style_counts.empty:
            most_common_style = style_counts.index[0]
            st.metric("Most Common Style", most_common_style)
        else:
            st.metric("Most Common Style", "N/A")

# Navigation
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🏠 Back to Home"):
        st.switch_page("app.py")
with col2:
    if st.button("📤 Upload Content"):
        st.switch_page("pages/1_Upload_Content.py")
with col3:
    if st.button("🗺️ Heritage Map"):
        st.switch_page("pages/5_Heritage_Map.py")
