import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="LTP Analysis Dashboard", layout="wide")

st.title("🔧 LTP Analysis Dashboard")
st.markdown("Upload your repair shop data to analyze Long Time Pending (LTP) appliances")

# LTP Thresholds configuration
LTP_THRESHOLDS = {
    'HA': 7,
    'DTV': 7,
    'HHP': 4,
    'MTN': 4,
    'default': 4
}

def get_ltp_threshold(model_code):
    """Determine LTP threshold based on model code."""
    if pd.isna(model_code):
        return LTP_THRESHOLDS['default']
    
    model_upper = str(model_code).upper().strip()
    
    for code, threshold in LTP_THRESHOLDS.items():
        if code != 'default' and code in model_upper:
            return threshold
    
    return LTP_THRESHOLDS['default']

def detect_column(df, keywords, column_type="column"):
    """Generic column detection function."""
    # First pass: exact keyword matches
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if any(keyword == col_lower for keyword in keywords):
            return col
    
    # Second pass: partial matches
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if any(keyword in col_lower for keyword in keywords):
            return col
    
    # For date columns, try parsing
    if column_type == "date":
        for col in df.columns:
            try:
                sample = df[col].dropna().iloc[:5]
                pd.to_datetime(sample)
                return col
            except:
                continue
    
    return None

def detect_requested_date_column(df):
    """Detect the Requested Date column (when item was received)."""
    requested_keywords = ['requested date', 'request date', 'intake date', 'received date', 'started date']
    return detect_column(df, requested_keywords, "date")

def detect_model_code_column(df):
    model_keywords = ['model code', 'model', 'code', 'type', 'category', 'appliance type', 'product']
    return detect_column(df, model_keywords)

def detect_anticipated_date_column(df):
    """Detect the First Anticipated / Anticipated Date column (used for LTP calculation)."""
    anticipated_keywords = [
        'first anticipated date',
        'first anticipated',
        'anticipated date',
        'anticipated',
        'expected date',
        'completion date',
        'due date',
        'target date'
    ]
    return detect_column(df, anticipated_keywords, "date")

# --- new: robust date detection that prefers Anticipated Date ---
def detect_date_column(df):
    """
    Return the best date column to use for LTP calculation.
    Preference order:
      1. Anticipated / First Anticipated Date
      2. Requested / Intake / Received Date
      3. Any datetime-typed column
      4. Any column parsable as dates (sample)
      5. Any column with 'date' in its name
    """
    # 1) prefer anticipated
    col = detect_anticipated_date_column(df)
    if col:
        return col

    # 2) fall back to requested variants
    col = detect_requested_date_column(df)
    if col:
        return col

    # 3) any datetime dtype
    for c in df.columns:
        try:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                return c
        except Exception:
            pass

    # 4) try parsing small samples
    for c in df.columns:
        try:
            sample = df[c].dropna().iloc[:5]
            if len(sample) == 0:
                continue
            pd.to_datetime(sample)
            return c
        except Exception:
            continue

    # 5) any column name containing 'date'
    for c in df.columns:
        if 'date' in str(c).lower():
            return c

    return None

def detect_tracking_column(df):
    tracking_keywords = ['tracking no', 'tracking', 'reference', 'ref no', 'job no', 'job number', 'id', 'ticket']
    return detect_column(df, tracking_keywords)

def detect_status_column(df):
    status_keywords = ['status', 'state', 'condition', 'progress', 'stage']
    return detect_column(df, status_keywords)

def process_data(df):
    """Process uploaded data and calculate LTP metrics.

    Rows with placeholder dates like '00.00.0000' are kept and marked as
    'Pending Assignment' instead of being removed.
    """
    date_col = detect_date_column(df)
    model_col = detect_model_code_column(df)
    tracking_col = detect_tracking_column(df)
    status_col = detect_status_column(df)

    if date_col is None:
        st.error("❌ Could not detect a date column. Please ensure your file has an Anticipated Date (preferred) or a Requested/Intake/Date column.")
        return None, None, None, None, None

    # Normalize column to string for placeholder detection
    date_series_raw = df[date_col].astype(str).str.strip()

    # Common placeholder patterns to treat as "Pending Assignment"
    placeholders = {'00.00.0000', '00/00/0000', '0000-00-00', '00-00-0000', '0.0.0.0', 'nan', 'none', ''}
    is_pending_assignment = date_series_raw.str.lower().isin({p.lower() for p in placeholders})

    # Mark pending-assignment rows
    df = df.copy()
    df['pending_assignment'] = is_pending_assignment

    # Replace known placeholders with NA before parsing so they become NaT
    df.loc[df['pending_assignment'], date_col] = pd.NA

    # Parse dates (coerce errors to NaT)
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # Rows with NaT that are NOT pending_assignment are truly invalid and will be removed
    invalid_mask = df[date_col].isna() & (~df['pending_assignment'])
    invalid_count = invalid_mask.sum()
    if invalid_count > 0:
        st.warning(f"⚠️ Removed {invalid_count} rows with invalid/unparseable dates (not placeholders).")
        # show a sample of invalid rows for debugging
        try:
            sample_cols = [c for c in [tracking_col, date_col] if c in df.columns]
            st.dataframe(df[invalid_mask][sample_cols].head(20), use_container_width=True)
        except Exception:
            pass
        df = df[~invalid_mask].copy()

    if len(df) == 0:
        st.error("❌ No valid data remaining after date parsing.")
        return None, None, None, None, None

    # Calculate days_pending only for rows with a valid date
    today = pd.Timestamp(datetime.now().date())
    df['days_pending'] = pd.NA
    valid_date_mask = df[date_col].notna()
    df.loc[valid_date_mask, 'days_pending'] = (today - df.loc[valid_date_mask, date_col]).dt.days

    # Apply LTP thresholds
    if model_col and model_col in df.columns:
        df['ltp_threshold'] = df[model_col].apply(get_ltp_threshold)
    else:
        df['ltp_threshold'] = LTP_THRESHOLDS['default']

    # Determine LTP status:
    # - Rows with pending_assignment => detailed_status = 'Pending Assignment'
    # - Rows with valid date => compute normal LTP
    df['is_ltp'] = False
    df.loc[valid_date_mask, 'is_ltp'] = df.loc[valid_date_mask, 'days_pending'] > df.loc[valid_date_mask, 'ltp_threshold']

    df['ltp_status'] = df.apply(
        lambda r: 'Pending Assignment' if r.get('pending_assignment', False)
        else ('🚨 LTP' if r['is_ltp'] else '✅ On Time'),
        axis=1
    )

    # Calculate expected completion date (LTP deadline) for valid dates
    df['ltp_deadline'] = pd.NaT
    df.loc[valid_date_mask, 'ltp_deadline'] = df.loc[valid_date_mask].apply(
        lambda row: row[date_col] + timedelta(days=int(row['ltp_threshold'])),
        axis=1
    )

    # Days in LTP / days before LTP - only meaningful for rows with valid dates
    df['days_in_ltp'] = 0
    df['days_before_ltp'] = 0

    df.loc[valid_date_mask, 'days_in_ltp'] = df.loc[valid_date_mask].apply(
        lambda row: max(0, int(row['days_pending']) - int(row['ltp_threshold'])) if row['is_ltp'] else 0,
        axis=1
    )

    df.loc[valid_date_mask, 'days_before_ltp'] = df.loc[valid_date_mask].apply(
        lambda row: max(0, int(row['ltp_threshold']) - int(row['days_pending'])) if not row['is_ltp'] else 0,
        axis=1
    )

    # Detailed status string
    def _detailed_status(row):
        if row.get('pending_assignment', False):
            return '🟡 Pending Assignment'
        if row['is_ltp']:
            return f"🚨 LTP ({int(row['days_in_ltp'])} days overdue)"
        return f"✅ On Time ({int(row['days_before_ltp'])} days left)"

    df['detailed_status'] = df.apply(_detailed_status, axis=1)

    return df, date_col, model_col, tracking_col, status_col

def export_to_excel(df, filename="ltp_report.xlsx"):
    """Export data to Excel with formatting.

    Tries to use `xlsxwriter` for improved formatting. If `xlsxwriter` is
    not available, falls back to `openpyxl` engine (no header styling).
    """
    output = io.BytesIO()

    # Choose engine: prefer xlsxwriter if installed
    try:
        import xlsxwriter  # noqa: F401
        engine = 'xlsxwriter'
    except Exception:
        engine = 'openpyxl'

    with pd.ExcelWriter(output, engine=engine) as writer:
        df.to_excel(writer, sheet_name='LTP Analysis', index=False)

        if engine == 'xlsxwriter':
            workbook = writer.book
            worksheet = writer.sheets['LTP Analysis']

            # Header formatting for xlsxwriter
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })

            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)

    output.seek(0)
    return output.getvalue()

# File uploader
uploaded_file = st.file_uploader("📁 Upload your CSV or Excel file", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Load data
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
        
        st.success(f"✅ File uploaded successfully! Found {len(df_raw)} records.")
        
        # Preview raw data
        with st.expander("📋 Preview Raw Data (First 10 rows)"):
            st.dataframe(df_raw.head(10), use_container_width=True)
        
        # Process data
        df, date_col, model_col, tracking_col, status_col = process_data(df_raw)
        
        if df is not None:
            st.markdown("---")
            st.header("📊 Dashboard Overview")
            
            # Key metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            total_appliances = len(df)
            ltp_count = df['is_ltp'].sum()
            on_time_count = total_appliances - ltp_count
            ltp_percentage = (ltp_count / total_appliances * 100) if total_appliances > 0 else 0
            avg_days = df['days_pending'].mean()
            max_days_in_ltp = df['days_in_ltp'].max() if ltp_count > 0 else 0
            
            with col1:
                st.metric("🔧 Total Appliances", f"{total_appliances:,}")
            
            with col2:
                st.metric("🚨 LTP Items", f"{ltp_count:,}", 
                         delta=f"{ltp_percentage:.1f}%", 
                         delta_color="inverse")
            
            with col3:
                st.metric("✅ On Time", f"{on_time_count:,}")
            
            with col4:
                st.metric("⏱️ Avg Days Pending", f"{avg_days:.1f}")
            
            with col5:
                st.metric("⚠️ Max Days in LTP", f"{int(max_days_in_ltp)}")
            
            st.markdown("---")
            
            # Visualizations
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("📈 LTP Status Distribution")
                ltp_dist = df['ltp_status'].value_counts()
                fig_ltp = px.pie(
                    values=ltp_dist.values, 
                    names=ltp_dist.index,
                    color=ltp_dist.index,
                    color_discrete_map={'🚨 LTP': '#ff4b4b', '✅ On Time': '#00cc66'},
                    hole=0.4
                )
                fig_ltp.update_traces(textposition='inside', textinfo='percent+label')
                fig_ltp.update_layout(showlegend=False)
                st.plotly_chart(fig_ltp, use_container_width=True)
            
            with col_right:
                st.subheader("📊 Days Pending Distribution")
                fig_hist = px.histogram(
                    df, 
                    x='days_pending',
                    nbins=30,
                    labels={'days_pending': 'Days Pending'},
                    color_discrete_sequence=['#1f77b4']
                )
                fig_hist.add_vline(
                    x=df['ltp_threshold'].median(), 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="Median LTP Threshold",
                    annotation_position="top"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            # Trend analysis
            if date_col:
                st.markdown("---")
                st.subheader("📅 Daily Intake Trend")
                
                daily_intake = df.groupby(df[date_col].dt.date).size().reset_index()
                daily_intake.columns = ['Date', 'Count']
                
                fig_trend = px.line(
                    daily_intake, 
                    x='Date', 
                    y='Count',
                    markers=True,
                    labels={'Count': 'Appliances Received'},
                    color_discrete_sequence=['#636EFA']
                )
                fig_trend.update_layout(hovermode='x unified')
                st.plotly_chart(fig_trend, use_container_width=True)
            
            # Model analysis
            if model_col:
                st.markdown("---")
                st.subheader("🔍 Analysis by Model Code")
                
                # ensure 'days_in_ltp' exists so aggregation won't fail
                if 'days_in_ltp' not in df.columns:
                    df['days_in_ltp'] = 0

                # aggregate by model code (use days_in_ltp instead of missing days_overdue)
                appliance_analysis = df.groupby(model_col).agg({
                    'is_ltp': ['sum', 'count'],
                    'days_pending': 'mean',
                    'ltp_threshold': 'first',
                    'days_in_ltp': 'sum'
                }).round(1)

                # flatten / rename columns to readable names
                appliance_analysis.columns = ['LTP Count', 'Total', 'Avg Days Pending', 'LTP Threshold', 'Total Days in LTP']
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
                        marker_color='#00cc66',
                        text=appliance_analysis['On Time'],
                        textposition='inside'
                    ))
                    fig_bar.add_trace(go.Bar(
                        name='LTP',
                        x=appliance_analysis.index,
                        y=appliance_analysis['LTP Count'],
                        marker_color='#ff4b4b',
                        text=appliance_analysis['LTP Count'],
                        textposition='inside'
                    ))
                    fig_bar.update_layout(
                        barmode='stack',
                        title='LTP vs On Time by Model Code',
                        xaxis_title='Model Code',
                        yaxis_title='Count',
                        showlegend=True
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with col_table:
                    st.dataframe(
                        appliance_analysis[['Total', 'LTP Count', 'LTP %', 'Avg Days Pending']].style.format({
                            'Total': '{:,.0f}',
                            'LTP Count': '{:,.0f}',
                            'LTP %': '{:.1f}%',
                            'Avg Days Pending': '{:.1f}'
                        }),
                        use_container_width=True
                    )
            
            # Status breakdown
            if status_col:
                st.markdown("---")
                st.subheader("📋 Status Breakdown")
                
                col_status1, col_status2 = st.columns(2)
                
                with col_status1:
                    status_dist = df[status_col].value_counts()
                    fig_status = px.bar(
                        x=status_dist.index,
                        y=status_dist.values,
                        labels={'x': 'Status', 'y': 'Count'},
                        color=status_dist.values,
                        color_continuous_scale='Blues',
                        text=status_dist.values
                    )
                    fig_status.update_traces(textposition='outside')
                    st.plotly_chart(fig_status, use_container_width=True)
                
                with col_status2:
                    # LTP by status
                    ltp_by_status = df[df['is_ltp']].groupby(status_col).size().sort_values(ascending=False)
                    if len(ltp_by_status) > 0:
                        fig_ltp_status = px.bar(
                            x=ltp_by_status.index,
                            y=ltp_by_status.values,
                            labels={'x': 'Status', 'y': 'LTP Count'},
                            color=ltp_by_status.values,
                            color_continuous_scale='Reds',
                            text=ltp_by_status.values,
                            title='LTP Items by Status'
                        )
                        fig_ltp_status.update_traces(textposition='outside')
                        st.plotly_chart(fig_ltp_status, use_container_width=True)
            
            # Detailed data table
            st.markdown("---")
            st.header("📋 Detailed Data Table")
            
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                filter_ltp = st.selectbox(
                    "Filter by LTP Status",
                    ["All", "LTP Only", "On Time Only"]
                )
            
            with filter_col2:
                if model_col:
                    model_codes = ['All'] + sorted(df[model_col].dropna().unique().tolist())
                    filter_model = st.selectbox(
                        "Filter by Model Code",
                        model_codes
                    )
                else:
                    filter_model = 'All'
            
            with filter_col3:
                sort_by = st.selectbox(
                    "Sort by",
                    ["Days Pending (High to Low)", "Days Pending (Low to High)", "Date (Newest)", "Date (Oldest)"]
                )
            
            # Apply filters
            df_filtered = df.copy()
            
            if filter_ltp == "LTP Only":
                df_filtered = df_filtered[df_filtered['is_ltp'] == True]
            elif filter_ltp == "On Time Only":
                df_filtered = df_filtered[df_filtered['is_ltp'] == False]
            
            if model_col and filter_model != 'All':
                df_filtered = df_filtered[df_filtered[model_col] == filter_model]
            
            # Apply sorting
            if sort_by == "Days Pending (High to Low)":
                df_filtered = df_filtered.sort_values('days_pending', ascending=False)
            elif sort_by == "Days Pending (Low to High)":
                df_filtered = df_filtered.sort_values('days_pending', ascending=True)
            elif sort_by == "Date (Newest)":
                df_filtered = df_filtered.sort_values(date_col, ascending=False)
            else:  # Date (Oldest)
                df_filtered = df_filtered.sort_values(date_col, ascending=True)
            
            # Select display columns
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
            
            st.info(f"📊 Showing {len(df_filtered):,} of {len(df):,} records")
            
            # Export functionality
            st.markdown("---")
            col_export1, col_export2 = st.columns([3, 1])
            
            with col_export2:
                excel_data = export_to_excel(df_filtered[display_columns])
                st.download_button(
                    label="📥 Download Filtered Data (Excel)",
                    data=excel_data,
                    file_name=f"ltp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # LTP Alert Summary
            if ltp_count > 0:
                st.markdown("---")
                st.header("⚠️ LTP Alert Summary")
                ltp_items = df[df['is_ltp'] == True].copy()
                # sort by computed days in LTP
                ltp_items = ltp_items.sort_values('days_in_ltp', ascending=False)
                
                # ensure final_columns exists (fallback to a sensible default if it was not defined)
                if 'final_columns' not in locals() and 'final_columns' not in globals():
                    display_columns = [col for col in df.columns if col not in ['is_ltp', 'ltp_threshold']]
                    priority_cols = ['detailed_status', 'days_pending', 'days_in_ltp', 'days_before_ltp', 'ltp_deadline']
                    other_cols = [col for col in display_columns if col not in priority_cols]
                    final_columns = [c for c in priority_cols if c in df.columns] + other_cols

                st.error(f"🚨 **{ltp_count:,} items are currently in LTP status and require immediate attention!**")
                
                # Top overdue items
                st.subheader("🔴 Most Overdue Items")
                st.dataframe(
                    ltp_items[final_columns].head(10),
                    use_container_width=True
                )
                
                if len(ltp_items) > 10:
                    st.caption(f"Showing top 10 most overdue items. Use filters above to see all {len(ltp_items):,} LTP items.")
    
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.exception(e)
        st.info("Please ensure your file contains proper date columns and is formatted correctly.")

else:
    st.info("👆 Please upload a CSV or Excel file to begin analysis")
    
    st.markdown("---")
    st.subheader("ℹ️ How to use this tool:")
    st.markdown("""
    1. **Upload your file** - CSV or Excel format containing repair data
    2. **Required columns:**
       - **Date column** (e.g., Requested Date, Intake Date) - When the device was booked
       - **Model Code** (optional) - Device model code (HA, DTV, HHP, MTN, etc.)
       - **Tracking No** (optional) - Unique job reference number
       - **Status** (optional) - Current service status
    3. **LTP Thresholds** - Automatically applied based on Model Code:
       - **HA, DTV**: 7 days
       - **HHP**: 4 days
       - **Other models**: 4 days (default)
    4. **Review the dashboard** to identify LTP items
    5. **Use filters** to focus on specific categories
    6. **Export results** for further analysis or reporting
    
    **Note:** LTP status is calculated as days from the request date exceeding the model-specific threshold.
    """)

def render_signature():
    footer_html = """
    <style>
    .dv-footer{
      position:fixed;
      bottom:8px;
      right:12px;
      font-size:11px;
      color:#6c757d;
      padding:6px 10px;
      border-radius:6px;
      background: rgba(255,255,255,0.85);
      box-shadow: 0 1px 6px rgba(0,0,0,0.08);
      z-index:9999;
      backdrop-filter: blur(4px);
    }
    .dv-footer a{ color:inherit; text-decoration:none; font-weight:600; }
    .dv-footer a:hover{ text-decoration:underline; }
    .dv-footer small{ color: #6b7280; margin-left:6px; font-weight:400; }
    </style>
    <div class="dv-footer" role="note" aria-label="app signature">
      Built for <strong>MM All Electronics</strong> • Built by <a href="https://devpulse.inc" target="_blank" rel="noopener">K. Ntulo</a>
      <small>— devpulse.inc</small>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)

# Hide only Streamlit "Share / Deploy" badge but keep header/footer and your signature
st.markdown(
    """
    <style>
      header { visibility: hidden; }
      footer { visibility: hidden; }
      .stApp { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar controls
if 'show_signature' not in st.session_state:
    st.session_state['show_signature'] = True

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.checkbox("Show signature", value=st.session_state['show_signature'], key='show_signature')
    
    if st.checkbox("Show developer info", value=False):
        st.markdown("""
        **Developer:** K. Ntulo  
        **Company:** devpulse.inc  
        **Developed for:** MM All Electronics  
        **Contact:** [danailntulo@gmail.com](mailto:danailntulo@gmail.com)
        """)
    
    st.markdown("---")
    st.markdown("### 📖 About")
    st.markdown("""
    This dashboard helps track and analyze Long Time Pending (LTP) appliances 
    in the repair workflow, enabling better service management and customer communication.
    """)

if st.session_state.get('show_signature', True):
    render_signature()