# Overview

This is a **Streamlit-based web application** for analyzing Long Time Pending (LTP) appliances in repair shops. The dashboard allows users to upload repair shop data and visualize which appliances have been pending beyond acceptable repair time thresholds. The application categorizes different appliance types (phones, fridges, washing machines, etc.) with specific time thresholds and provides analytical insights through interactive visualizations using Plotly.

**Current Status (November 19, 2025):** MVP complete and running. Core functionality operational including CSV/Excel upload, automatic LTP detection with category-specific thresholds, dashboard visualizations, and filterable data tables.

# User Preferences

Preferred communication style: Simple, everyday language.

**Development Approach:** User prefers streamlined features without unnecessary complexity. Focus on essential functionality first, then add advanced features only when needed.

# System Architecture

## Frontend Architecture

**Technology:** Streamlit web framework with wide layout configuration

**Rationale:** Streamlit was chosen for rapid development of data-driven dashboards without requiring extensive frontend development. The wide layout maximizes screen real estate for data visualization and analysis.

**Key Components:**
- File upload interface for CSV/Excel data ingestion
- Interactive Plotly visualizations (charts and graphs)
- Responsive dashboard layout using Streamlit's column system

## Data Processing Layer

**Approach:** Pandas-based data manipulation with custom business logic

**Problem Addressed:** Different appliance types require different repair time thresholds to determine if they're "Long Time Pending"

**Solution:** Dictionary-based threshold mapping system (LTP_THRESHOLDS) that maps appliance types to acceptable repair durations in days

**Threshold Strategy:**
- HA and DTV model codes: 7 days
- HHP and MTN model codes: 4 days
- Fallback default: 4 days for unrecognized model codes

**Flexible Column Detection:** The system automatically identifies:
- `Requested Date` column for intake date tracking
- `Model Code` column for determining LTP thresholds (HA, DTV, HHP, MTN)
- `Tracking No` column for unique job reference identification
- Service Type and Status columns (optional)

## Visualization Layer

**Technology:** Plotly Express and Plotly Graph Objects

**Rationale:** Plotly provides interactive, publication-quality visualizations that are essential for data exploration and presentation. The dual approach (Express for simple charts, Graph Objects for complex customization) offers flexibility.

**Trade-offs:**
- **Pros:** Rich interactivity, professional appearance, easy integration with Streamlit
- **Cons:** Larger bundle size compared to static visualization libraries

## Data Input Strategy

**Flexible Upload System:** Accepts multiple data formats (implied CSV/Excel support)

**Smart Column Detection:** Automatically identifies relevant columns (date columns) rather than requiring strict schema adherence, reducing user friction and supporting various data sources

# External Dependencies

## Python Libraries

- **streamlit**: Web application framework and UI components
- **pandas**: Data manipulation and analysis
- **plotly.express**: High-level visualization creation
- **plotly.graph_objects**: Low-level visualization customization
- **datetime**: Date/time manipulation for LTP calculations

## Data Requirements

**Input Format:** CSV or Excel files containing:
- Appliance type information
- Date columns (intake/received/started dates)
- Additional repair shop data fields

**No Database:** Application operates in stateless mode with session-based data uploads (no persistent storage)

## Deployment Considerations

**Platform:** Streamlit app — platform-agnostic (can be deployed to any PaaS, cloud VM, or container)
- Entry point: `app.py` for Streamlit application
- Secondary file: `main.py` (minimal Python entry point, useful for quick checks)
