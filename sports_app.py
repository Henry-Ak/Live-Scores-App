import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import datetime

# Database connection
def get_database_connection():
    secrets = st.secrets["postgres"]
    conn_string = f"postgresql+psycopg2://{secrets['DB_USER']}:{secrets['DB_PASSWORD']}@{secrets['HOST']}/{secrets['DB']}"
    engine = create_engine(conn_string)
    return engine.connect()

# Fetch data from database
def fetch_data():
    conn = get_database_connection()
    query = "SELECT * FROM student.ha_livescores"
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Convert dateevent and streventtime to datetime if they are not already
    df['dateevent'] = pd.to_datetime(df['dateevent'])
    df['streventtime'] = pd.to_datetime(df['streventtime'], errors='coerce')  # Handle invalid values
    
    return df

# Main Streamlit app
def main():
    st.title("Live Sports Scores Dashboard")
    
    # Fetch data
    df = fetch_data()
    
    # Filter options
    sports = df['strsport'].unique()
    sport_filter = st.sidebar.selectbox("Select Sport", sports)
    
    # Set a wider default date range
    start_date = datetime.date(2024, 1, 1)
    end_date = datetime.date(2024, 12, 31)
    date_filter = st.sidebar.date_input("Select Date Range", [start_date, end_date])
    
    # Time range filter
    time_filter = st.sidebar.slider("Select Time Range (24hr format)", 0, 23, (0, 23))
    
    # Apply filters
    filtered_df = df[df['strsport'].str.lower() == sport_filter.lower()]  # Ensure case insensitivity
    if date_filter:
        start_date, end_date = [pd.to_datetime(date).date() for date in date_filter]
        filtered_df = filtered_df[(filtered_df['dateevent'].dt.date >= start_date) & 
                                  (filtered_df['dateevent'].dt.date <= end_date)]
    if time_filter:
        filtered_df = filtered_df[(filtered_df['streventtime'].dt.hour >= time_filter[0]) &
                                  (filtered_df['streventtime'].dt.hour <= time_filter[1])]
    
    # Display selected date and time range
    st.write(f"Current Date Range: {date_filter[0]} to {date_filter[1]}")
    st.write(f"Current Time Range: {time_filter[0]}:00 to {time_filter[1]}:59")
    
    # Search functionality
    search_term = st.sidebar.text_input("Search Teams or Competitions")
    if search_term:
        filtered_df = filtered_df[filtered_df.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)]
    
    # Display filtered table with selected columns
    columns_to_display = ['strsport', 'strleague', 'strhometeam', 'strawayteam', 'inthomescore', 'intawayscore',
                          'strstatus', 'strprogress', 'streventtime', 'dateevent', 'updated']
    st.dataframe(filtered_df[columns_to_display])
    
    # Visualizations
    st.subheader("Score Comparison")
    if not filtered_df.empty:
        chart_data = filtered_df[['strhometeam', 'inthomescore', 'intawayscore']].set_index('strhometeam')
        st.bar_chart(chart_data, use_container_width=True, color=['#1f77b4', '#ff7f0e'])
        st.text("Hover over bars for details.")
        st.write("(Blue: Away Team, Orange: Home Team)")
    
    st.subheader("Match-Up Overview")
    for _, row in filtered_df.iterrows():
        col1, col2, col3 = st.columns([2, 1, 2])  # Adjusting column widths
        with col1:
            st.image(row['strhometeambadge'], width=150)
            st.header(row['strhometeam'])
        with col2:
            st.markdown("<h1 style='text-align:center;margin-top:60px;'>vs</h1>", unsafe_allow_html=True)
            st.markdown(f"**Date:** {row['dateevent'].strftime('%Y-%m-%d')}")
            st.markdown(f"**Time:** {row['streventtime'].strftime('%H:%M:%S') if pd.notna(row['streventtime']) else 'Unknown'}")
        with col3:
            st.image(row['strawayteambadge'], width=150)
            st.header(row['strawayteam'])
    
if __name__ == "__main__":
    main()
