import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="LTP Analysis Dashboard", layout="wide")

st.title("🔧 LTP Analysis Dashboard")
st.markdown("Upload your repair shop data to analyze Long Time Pending (LTP) appliances")

LTP_THRESHOLDS = {
    'HA': 7,
    'DTV': 7,
    'HHP': 4,
    'MTN': 4,
    'default': 4
}

def get_ltp_threshold(model_code):
    if pd.isna(model_code):
        return LTP_THRESHOLDS['default']
    
    model_upper = str(model_code).upper().strip()
    
    for code, threshold in LTP_THRESHOLDS.items():
        if code in model_upper:
            return threshold
    
    return LTP_THRESHOLDS['default']

def detect_date_column(df):
    date_keywords = ['requested date', 'request date', 'date', 'intake', 'received', 'started', 'created', 'opened', 'submitted']
    
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in date_keywords):
            return col
    
    for col in df.columns:
        try:
            pd.to_datetime(df[col].dropna().iloc[0])
            return col
        except:
            continue
    
    return None

def detect_model_code_column(df):
    model_keywords = ['model', 'code', 'model code', 'type', 'category', 'appliance type']
    
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in model_keywords):
            return col
    
    return None

def detect_tracking_column(df):
    tracking_keywords = ['tracking', 'tracking no', 'reference', 'ref no', 'job no', 'id']
    
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in tracking_keywords):
            return col
    
    return None

def detect_status_column(df):
    status_keywords = ['status', 'state', 'condition', 'progress']
    
    for col in df.columns:
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in status_keywords):
            return col
    
    return None

def process_data(df):
    date_col = detect_date_column(df)
    model_col = detect_model_code_column(df)
    tracking_col = detect_tracking_column(df)
    status_col = detect_status_column(df)
    
    if date_col is None:
        st.error("❌ Could not detect a date column. Please ensure your file has a 'Requested Date' column.")
        return None, None, None, None, None
    
    if model_col is None:
        st.warning("⚠️ Could not detect a Model Code column. Using default LTP threshold of 4 days for all items.")
    
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    df = df[df[date_col].notna()].copy()
    
    today = pd.Timestamp(datetime.now().date())
    df['days_pending'] = (today - df[date_col]).dt.days
    
    if model_col:
        df['ltp_threshold'] = df[model_col].apply(get_ltp_threshold)
    else:
        df['ltp_threshold'] = LTP_THRESHOLDS['default']
    
    df['is_ltp'] = df['days_pending'] > df['ltp_threshold']
    df['ltp_status'] = df['is_ltp'].apply(lambda x: '🚨 LTP' if x else '✅ On Time')
    
    df['ltp_date'] = df.apply(lambda row: row[date_col] + timedelta(days=int(row['ltp_threshold'])), axis=1)
    
    return df, date_col, model_col, tracking_col, status_col

uploaded_file = st.file_uploader("📁 Upload your CSV or Excel file", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
        
        st.success(f"✅ File uploaded successfully! Found {len(df_raw)} records.")
        
        with st.expander("📋 Preview Raw Data (First 10 rows)"):
            st.dataframe(df_raw.head(10), use_container_width=True)
        
        df, date_col, model_col, tracking_col, status_col = process_data(df_raw)
        
        if df is not None:
            st.markdown("---")
            st.header("📊 Dashboard Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_appliances = len(df)
            ltp_count = df['is_ltp'].sum()
            ltp_percentage = (ltp_count / total_appliances * 100) if total_appliances > 0 else 0
            avg_days = df['days_pending'].mean()
            
            with col1:
                st.metric("🔧 Total Appliances", f"{total_appliances}")
            
            with col2:
                st.metric("🚨 LTP Items", f"{ltp_count}", 
                         delta=f"{ltp_percentage:.1f}%", 
                         delta_color="inverse")
            
            with col3:
                st.metric("✅ On Time", f"{total_appliances - ltp_count}")
            
            with col4:
                st.metric("⏱️ Avg Days Pending", f"{avg_days:.1f}")
            
            st.markdown("---")
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("📈 LTP Status Distribution")
                ltp_dist = df['ltp_status'].value_counts()
                fig_ltp = px.pie(
                    values=ltp_dist.values, 
                    names=ltp_dist.index,
                    color=ltp_dist.index,
                    color_discrete_map={'🚨 LTP': '#ff4b4b', '✅ On Time': '#00cc66'}
                )
                fig_ltp.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_ltp, use_container_width=True)
            
            with col_right:
                st.subheader("📊 Days Pending Distribution")
                fig_hist = px.histogram(
                    df, 
                    x='days_pending',
                    nbins=20,
                    labels={'days_pending': 'Days Pending'},
                    color_discrete_sequence=['#1f77b4']
                )
                fig_hist.add_vline(x=df['ltp_threshold'].median(), 
                                  line_dash="dash", 
                                  line_color="red",
                                  annotation_text="Typical LTP Threshold")
                st.plotly_chart(fig_hist, use_container_width=True)
            
            if model_col:
                st.markdown("---")
                st.subheader("🔍 Analysis by Model Code")
                
                appliance_analysis = df.groupby(model_col).agg({
                    'is_ltp': ['sum', 'count'],
                    'days_pending': 'mean',
                    'ltp_threshold': 'first'
                }).round(1)
                
                appliance_analysis.columns = ['LTP Count', 'Total', 'Avg Days Pending', 'LTP Threshold']
                appliance_analysis['On Time'] = appliance_analysis['Total'] - appliance_analysis['LTP Count']
                appliance_analysis['LTP %'] = (appliance_analysis['LTP Count'] / appliance_analysis['Total'] * 100).round(1)
                appliance_analysis = appliance_analysis.sort_values('LTP Count', ascending=False)
                
                col_chart, col_table = st.columns([2, 1])
                
                with col_chart:
                    fig_bar = go.Figure()
                    fig_bar.add_trace(go.Bar(
                        name='On Time',
                        x=appliance_analysis.index,
                        y=appliance_analysis['On Time'],
                        marker_color='#00cc66'
                    ))
                    fig_bar.add_trace(go.Bar(
                        name='LTP',
                        x=appliance_analysis.index,
                        y=appliance_analysis['LTP Count'],
                        marker_color='#ff4b4b'
                    ))
                    fig_bar.update_layout(
                        barmode='stack',
                        title='LTP vs On Time by Model Code',
                        xaxis_title='Model Code',
                        yaxis_title='Count'
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col_table:
                    st.dataframe(
                        appliance_analysis[['Total', 'LTP Count', 'LTP %', 'LTP Threshold']],
                        use_container_width=True
                    )
            
            if status_col:
                st.markdown("---")
                st.subheader("📋 Status Breakdown")
                
                status_dist = df[status_col].value_counts()
                fig_status = px.bar(
                    x=status_dist.index,
                    y=status_dist.values,
                    labels={'x': 'Status', 'y': 'Count'},
                    color=status_dist.values,
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            st.markdown("---")
            st.header("📋 Detailed Data Table")
            
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                filter_ltp = st.selectbox(
                    "Filter by LTP Status",
                    ["All", "LTP Only", "On Time Only"]
                )
            
            with filter_col2:
                if model_col:
                    model_codes = ['All'] + sorted(df[model_col].unique().tolist())
                    filter_model = st.selectbox(
                        "Filter by Model Code",
                        model_codes
                    )
                else:
                    filter_model = 'All'
            
            df_filtered = df.copy()
            
            if filter_ltp == "LTP Only":
                df_filtered = df_filtered[df_filtered['is_ltp'] == True]
            elif filter_ltp == "On Time Only":
                df_filtered = df_filtered[df_filtered['is_ltp'] == False]
            
            if model_col and filter_model != 'All':
                df_filtered = df_filtered[df_filtered[model_col] == filter_model]
            
            display_columns = [col for col in df.columns if col not in ['is_ltp', 'ltp_threshold']]
            
            def highlight_ltp(row):
                if row['ltp_status'] == '🚨 LTP':
                    return ['background-color: #ffcccc'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                df_filtered[display_columns].style.apply(highlight_ltp, axis=1),
                use_container_width=True,
                height=400
            )
            
            st.info(f"📊 Showing {len(df_filtered)} of {len(df)} records")
            
            if ltp_count > 0:
                st.markdown("---")
                st.header("⚠️ LTP Alert Summary")
                ltp_items = df[df['is_ltp'] == True].copy()
                ltp_items = ltp_items.sort_values('days_pending', ascending=False)
                
                st.error(f"🚨 **{ltp_count} items are currently in LTP status and require immediate attention!**")
                
                st.dataframe(
                    ltp_items[display_columns].head(10),
                    use_container_width=True
                )
                
                if len(ltp_items) > 10:
                    st.caption(f"Showing top 10 most overdue items. Use filters above to see all {len(ltp_items)} LTP items.")
    
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.info("Please ensure your file contains proper date columns and is formatted correctly.")

else:
    st.info("👆 Please upload a CSV or Excel file to begin analysis")
    
    st.markdown("---")
    st.subheader("ℹ️ How to use this tool:")
    st.markdown("""
    1. **Upload your file** - CSV or Excel format containing repair data
    2. **Required columns:**
       - **Requested Date** - When the device was booked for repair
       - **Model Code** - Device model code (HA, DTV, HHP, MTN, etc.)
       - **Tracking No** - Unique job reference number (optional)
       - **Service Type** - Type of service (optional)
    3. **LTP Thresholds** - Automatically applied based on Model Code:
       - **HA, DTV**: 7 days
       - **HHP, MTN**: 4 days
       - Other models: 4 days (default)
    4. **Review the dashboard** to see which items are in LTP status
    5. **Use filters** to focus on specific model codes or LTP items only
    
    **Note:** The system calculates "Days Pending" as the time from Requested Date to today, 
    and flags items as LTP when they exceed their model-specific threshold.
    """)
