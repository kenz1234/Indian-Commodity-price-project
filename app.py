import streamlit as st
import pandas as pd
import pickle
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


st.set_page_config(
    page_title="Agricultural Price Predictor",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #E8F5E9 0%, #C8E6C9 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .prediction-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .metric-card {
        background: black;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-size: 1.2rem;
        padding: 0.8rem;
        border-radius: 10px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
""", unsafe_allow_html=True)



@st.cache_resource
def load_models():
    try:
        with open("model.pkl", "rb") as f:
            model = pickle.load(f)
        with open("encoders.pkl", "rb") as f:
            encoders = pickle.load(f)
        return model, encoders
    except FileNotFoundError:
        st.error("⚠️ Model files not found. Please ensure 'model.pkl' and 'encoders.pkl' are in the directory.")
        return None, None


@st.cache_data
def load_mapping_files():
    try:
        state_district_market = pd.read_csv("state_district_market.csv")
        commodity_variety_grade = pd.read_csv("commodity_variety_code.csv")
        return state_district_market, commodity_variety_grade
    except FileNotFoundError:
        st.warning("⚠️ Mapping files not found. Using manual entry mode.")
        return None, None

@st.cache_data
def load_historical_data():
    try:
        df = pd.read_csv("combined.csv")
        df["Arrival_Date"] = pd.to_datetime(df["Arrival_Date"])
        return df
    except FileNotFoundError:
        return None


model, encoders = load_models()
state_district_market, commodity_variety_grade = load_mapping_files()
historical_data = load_historical_data()


st.markdown('<div class="main-header">🌾 Agricultural Price Prediction System 🌾</div>', unsafe_allow_html=True)


with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2917/2917995.png", width=100)
    st.title("Navigation")
    page = st.radio("Select Page:", ["🔮 Price Prediction", "📊 Market Analysis", "📈 Trends & Insights"])

    st.markdown("---")
    st.markdown("### About")
    st.info(
        "This system helps farmers predict agricultural commodity prices and analyze market trends across different regions.")


if page == "🔮 Price Prediction":
    st.header("🔮 Predict Commodity Prices")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Enter Details")

       
        st.markdown("#### 📍 Location Details")
        loc_col1, loc_col2, loc_col3 = st.columns(3)

        with loc_col1:
            if state_district_market is not None:
                states = sorted(state_district_market['State'].unique())
                state = st.selectbox("State", states)
                districts = sorted(state_district_market[state_district_market['State'] == state]['District'].unique())
            else:
                state = st.text_input("State")
                districts = []

        with loc_col2:
            if state_district_market is not None and districts:
                district = st.selectbox("District", districts)
                markets = sorted(state_district_market[
                                     (state_district_market['State'] == state) &
                                     (state_district_market['District'] == district)
                                     ]['Market'].unique())
            else:
                district = st.text_input("District")
                markets = []

        with loc_col3:
            if state_district_market is not None and markets:
                market = st.selectbox("Market", markets)
            else:
                market = st.text_input("Market")

       
        st.markdown("#### 🌾 Commodity Details")
        comm_col1, comm_col2, comm_col3 = st.columns(3)

        with comm_col1:
            if commodity_variety_grade is not None:
                commodities = sorted(commodity_variety_grade['Commodity'].unique())
                commodity = st.selectbox("Commodity", commodities)
                varieties = sorted(commodity_variety_grade[
                                       commodity_variety_grade['Commodity'] == commodity
                                       ]['Variety'].unique())
            else:
                commodity = st.text_input("Commodity")
                varieties = []

        with comm_col2:
            if commodity_variety_grade is not None and varieties:
                variety = st.selectbox("Variety", varieties)
              
                commodity_code_row = commodity_variety_grade[
                    (commodity_variety_grade['Commodity'] == commodity) &
                    (commodity_variety_grade['Variety'] == variety)
                    ]
                if not commodity_code_row.empty and 'Commodity_Code' in commodity_code_row.columns:
                    commodity_code = commodity_code_row.iloc[0]['Commodity_Code']
                else:
                    commodity_code = 0

                grades = sorted(commodity_variety_grade[
                                    (commodity_variety_grade['Commodity'] == commodity) &
                                    (commodity_variety_grade['Variety'] == variety)
                                    ]['Grade'].unique())
            else:
                variety = st.text_input("Variety")
                grades = []
                commodity_code = 0

        with comm_col3:
            if commodity_variety_grade is not None and grades:
                grade = st.selectbox("Grade", grades)
            else:
                grade = st.text_input("Grade")

        
        st.markdown("#### 💰 Expected Price Range (Optional)")
        price_col1, price_col2 = st.columns(2)

        with price_col1:
            min_price = st.number_input(
                "Minimum Price (₹/Quintal)",
                min_value=0.0,
                value=1000.0,
                step=100.0,
                help="Expected minimum price in the market"
            )

        with price_col2:
            max_price = st.number_input(
                "Maximum Price (₹/Quintal)",
                min_value=0.0,
                value=5000.0,
                step=100.0,
                help="Expected maximum price in the market"
            )

     
        st.markdown("#### 📅 Prediction Date")
        prediction_date = st.date_input(
            "Select Date",
            value=datetime.now(),
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        )

        predict_button = st.button("🔮 Predict Price", use_container_width=True)

    with col2:
        st.subheader("Quick Info")
        st.markdown("""
        <div class="metric-card">
        <h4>📋 How to Use:</h4>
        <ol>
        <li>Select your location details</li>
        <li>Choose the commodity</li>
        <li>Pick a prediction date</li>
        <li>Click 'Predict Price'</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)


    if predict_button and model is not None and encoders is not None:
        try:
            year = prediction_date.year
            month = prediction_date.month
            day = prediction_date.day
            weekofyear = prediction_date.isocalendar()[1]

            if historical_data is not None and min_price == 1000.0 and max_price == 5000.0:
                hist_filtered = historical_data[
                    (historical_data['State'] == state) &
                    (historical_data['Commodity'] == commodity)
                    ]
                if not hist_filtered.empty:
                    min_price = hist_filtered['Min_Price'].mean() if 'Min_Price' in hist_filtered.columns else min_price
                    max_price = hist_filtered['Max_Price'].mean() if 'Max_Price' in hist_filtered.columns else max_price

            input_data = {
                'State': encoders['State'].transform([state])[0],
                'District': encoders['District'].transform([district])[0],
                'Market': encoders['Market'].transform([market])[0],
                'Commodity': encoders['Commodity'].transform([commodity])[0],
                'Variety': encoders['Variety'].transform([variety])[0],
                'Grade': encoders['Grade'].transform([grade])[0],
                'Min_Price': min_price,
                'Max_Price': max_price,
                'Commodity_Code': commodity_code if 'commodity_code' in locals() else 0,
                'year': year,
                'month': month,
                'day': day,
                'weekofyear': weekofyear
            }

            input_df = pd.DataFrame([input_data])
            column_order = ['State', 'District', 'Market', 'Commodity', 'Variety', 'Grade',
                            'Min_Price', 'Max_Price', 'Commodity_Code', 'year', 'month', 'day', 'weekofyear']
            input_df = input_df[column_order]
            prediction = model.predict(input_df)[0]

            
            st.markdown("---")
            st.markdown(f"""
            <div class="prediction-box">
                <h2>Predicted Price</h2>
                <h1 style="font-size: 3rem; margin: 1rem 0;">₹ {prediction:.2f}</h1>
                <p style="font-size: 1.2rem;">per Quintal</p>
            </div>
            """, unsafe_allow_html=True)

            
            st.markdown("### 📊 Price Insights")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Per Kg", f"₹ {prediction / 100:.2f}")
            with col2:
                st.metric("Per 50 Kg", f"₹ {prediction / 2:.2f}")
            with col3:
                st.metric("Per Ton", f"₹ {prediction * 10:.2f}")
            with col4:
                margin = ((prediction - min_price) / min_price * 100) if min_price > 0 else 0
                st.metric("Potential Margin", f"{margin:.1f}%")

        
            if historical_data is not None:
                hist_filtered = historical_data[
                    (historical_data['State'] == state) &
                    (historical_data['Commodity'] == commodity)
                    ]
                if not hist_filtered.empty:
                    avg_price = hist_filtered['Modal_Price'].mean()
                    price_diff = prediction - avg_price
                    price_diff_pct = (price_diff / avg_price) * 100
                    st.markdown("### 📈 Comparison with Historical Average")
                    if price_diff > 0:
                        st.success(
                            f"Predicted price is ₹{price_diff:.2f} ({price_diff_pct:.1f}%) higher than historical average (₹{avg_price:.2f})")
                    else:
                        st.info(
                            f"Predicted price is ₹{abs(price_diff):.2f} ({abs(price_diff_pct):.1f}%) lower than historical average (₹{avg_price:.2f})")

        except Exception as e:
            st.error(f"❌ Prediction failed: {str(e)}")
            st.info("Please ensure all fields are filled correctly and the values exist in the training data.")

elif page == "📊 Market Analysis":
    st.header("📊 Market Analysis Dashboard")
    if historical_data is not None:
        st.subheader("🔍 Apply Filters")
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_states = st.multiselect(
                "Select States",
                options=sorted(historical_data['State'].unique()),
                default=sorted(historical_data['State'].unique())[:3]
            )

        with col2:
            selected_commodities = st.multiselect(
                "Select Commodities",
                options=sorted(historical_data['Commodity'].unique()),
                default=sorted(historical_data['Commodity'].unique())[:5]
            )

        with col3:
            year_range = st.slider(
                "Select Year Range",
                int(historical_data['Arrival_Date'].dt.year.min()),
                int(historical_data['Arrival_Date'].dt.year.max()),
                (int(historical_data['Arrival_Date'].dt.year.max()) - 2,
                 int(historical_data['Arrival_Date'].dt.year.max()))
            )

    
        filtered_data = historical_data[
            (historical_data['State'].isin(selected_states)) &
            (historical_data['Commodity'].isin(selected_commodities)) &
            (historical_data['Arrival_Date'].dt.year >= year_range[0]) &
            (historical_data['Arrival_Date'].dt.year <= year_range[1])
            ]

        if not filtered_data.empty:
            st.markdown("---")
            st.subheader("🗺️ State-wise Price Analysis")

            state_avg = filtered_data.groupby('State')['Modal_Price'].agg(['mean', 'min', 'max']).reset_index()
            state_avg.columns = ['State', 'Average Price', 'Min Price', 'Max Price']

            fig_state = go.Figure()
            fig_state.add_trace(go.Bar(
                x=state_avg['State'],
                y=state_avg['Average Price'],
                name='Average Price',
                marker_color='#4CAF50'
            ))
            fig_state.update_layout(
                title="Average Prices by State (₹/Quintal)",
                xaxis_title="State",
                yaxis_title="Price (₹)",
                height=400
            )
            st.plotly_chart(fig_state, use_container_width=True)
            st.markdown("---")
            st.subheader("🏘️ District-wise Price Analysis")

            district_avg = filtered_data.groupby(['State', 'District'])['Modal_Price'].mean().reset_index()
            district_avg = district_avg.sort_values('Modal_Price', ascending=False).head(15)

            fig_district = px.bar(
                district_avg,
                x='Modal_Price',
                y='District',
                color='State',
                orientation='h',
                title='Top 15 Districts by Average Price (₹/Quintal)',
                labels={'Modal_Price': 'Average Price (₹)', 'District': 'District'}
            )
            fig_district.update_layout(height=500)
            st.plotly_chart(fig_district, use_container_width=True)
            st.markdown("---")
            st.subheader("🌾 Commodity Price Comparison")

            commodity_stats = filtered_data.groupby('Commodity')['Modal_Price'].agg(['mean', 'std']).reset_index()
            commodity_stats.columns = ['Commodity', 'Average Price', 'Std Dev']
            commodity_stats = commodity_stats.sort_values('Average Price', ascending=False)

            fig_commodity = go.Figure()
            fig_commodity.add_trace(go.Bar(
                x=commodity_stats['Commodity'],
                y=commodity_stats['Average Price'],
                error_y=dict(type='data', array=commodity_stats['Std Dev']),
                marker_color='#FF9800'
            ))
            fig_commodity.update_layout(
                title="Average Prices by Commodity with Standard Deviation (₹/Quintal)",
                xaxis_title="Commodity",
                yaxis_title="Price (₹)",
                height=400
            )
            st.plotly_chart(fig_commodity, use_container_width=True)

            st.markdown("---")
            st.subheader("📈 Summary Statistics")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", f"{len(filtered_data):,}")
            with col2:
                st.metric("Average Price", f"₹{filtered_data['Modal_Price'].mean():.2f}")
            with col3:
                st.metric("Highest Price", f"₹{filtered_data['Modal_Price'].max():.2f}")
            with col4:
                st.metric("Lowest Price", f"₹{filtered_data['Modal_Price'].min():.2f}")

        else:
            st.warning("⚠️ No data available for the selected filters.")

    else:
        st.error("❌ Historical data not found. Please ensure 'combined.csv' is available.")


elif page == "📈 Trends & Insights":
    st.header("📈 Price Trends & Market Insights")

    if historical_data is not None:
        selected_commodity = st.selectbox(
            "Select Commodity for Trend Analysis",
            sorted(historical_data['Commodity'].unique())
        )
        selected_state = st.selectbox(
            "Select State",
            sorted(historical_data['State'].unique())
        )


        trend_data = historical_data[
            (historical_data['Commodity'] == selected_commodity) &
            (historical_data['State'] == selected_state)
            ].copy()

        if not trend_data.empty:
            st.markdown("---")
            st.subheader(f"📊 Monthly Price Trend - {selected_commodity} in {selected_state}")

            trend_data['YearMonth'] = trend_data['Arrival_Date'].dt.to_period('M').astype(str)
            monthly_avg = trend_data.groupby('YearMonth')['Modal_Price'].mean().reset_index()

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=monthly_avg['YearMonth'],
                y=monthly_avg['Modal_Price'],
                mode='lines+markers',
                name='Average Price',
                line=dict(color='#2196F3', width=3),
                marker=dict(size=8)
            ))
            fig_trend.update_layout(
                title=f"Monthly Average Price Trend (₹/Quintal)",
                xaxis_title="Month",
                yaxis_title="Price (₹)",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            st.markdown("---")
            st.subheader("🌦️ Seasonal Price Pattern")

            trend_data['Month'] = trend_data['Arrival_Date'].dt.month
            seasonal_avg = trend_data.groupby('Month')['Modal_Price'].mean().reset_index()
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            seasonal_avg['Month_Name'] = seasonal_avg['Month'].apply(lambda x: month_names[x - 1])

            fig_seasonal = go.Figure()
            fig_seasonal.add_trace(go.Bar(
                x=seasonal_avg['Month_Name'],
                y=seasonal_avg['Modal_Price'],
                marker_color='#9C27B0',
                text=seasonal_avg['Modal_Price'].round(2),
                textposition='outside'
            ))
            fig_seasonal.update_layout(
                title="Average Prices by Month",
                xaxis_title="Month",
                yaxis_title="Average Price (₹)",
                height=400
            )
            st.plotly_chart(fig_seasonal, use_container_width=True)
            st.markdown("---")
            st.subheader("📊 Price Distribution")

            col1, col2 = st.columns(2)

            with col1:
                fig_hist = px.histogram(
                    trend_data,
                    x='Modal_Price',
                    nbins=30,
                    title="Price Distribution",
                    labels={'Modal_Price': 'Price (₹)', 'count': 'Frequency'}
                )
                fig_hist.update_traces(marker_color='#FF5722')
                st.plotly_chart(fig_hist, use_container_width=True)

            with col2:
                fig_box = px.box(
                    trend_data,
                    y='Modal_Price',
                    title="Price Box Plot",
                    labels={'Modal_Price': 'Price (₹)'}
                )
                fig_box.update_traces(marker_color='#00BCD4')
                st.plotly_chart(fig_box, use_container_width=True)

      
            st.markdown("---")
            st.subheader("💡 Key Insights")

            col1, col2, col3 = st.columns(3)

            with col1:
                highest_month = seasonal_avg.loc[seasonal_avg['Modal_Price'].idxmax(), 'Month_Name']
                highest_price = seasonal_avg['Modal_Price'].max()
                st.info(f"**Highest prices** typically in **{highest_month}** (₹{highest_price:.2f})")

            with col2:
                lowest_month = seasonal_avg.loc[seasonal_avg['Modal_Price'].idxmin(), 'Month_Name']
                lowest_price = seasonal_avg['Modal_Price'].min()
                st.info(f"**Lowest prices** typically in **{lowest_month}** (₹{lowest_price:.2f})")

            with col3:
                price_volatility = trend_data['Modal_Price'].std()
                st.info(f"**Price volatility**: ₹{price_volatility:.2f} (Std Dev)")

        else:
            st.warning(f"⚠️ No data available for {selected_commodity} in {selected_state}")

    else:
        st.error("❌ Historical data not found. Please ensure 'combined.csv' is available.")


st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🌾 Agricultural Price Prediction System | Empowering Farmers with Data-Driven Insights</p>
    <p style="font-size: 0.9rem;">Built with ❤️ for Indian Farmers</p>
</div>
""", unsafe_allow_html=True)
