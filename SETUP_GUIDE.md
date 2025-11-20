# LTP Analysis Dashboard - Setup & Deployment Guide

## 📋 Table of Contents
1. [Running Locally on Your PC](#running-locally-on-your-pc)
2. [Testing the Application](#testing-the-application)
3. [Deploying & Hosting](#deploying--hosting)
4. [Troubleshooting](#troubleshooting)

---

## 🖥️ Running Locally on Your PC

### Step 1: Install Python
1. **Download Python 3.11** from https://www.python.org/downloads/
2. During installation, **check the box** that says "Add Python to PATH"
3. Verify installation by opening **Command Prompt** (Windows) or **Terminal** (Mac/Linux) and typing:
   ```bash
   python --version
   ```
   You should see: `Python 3.11.x`

### Step 2: Download the Project Files
1. Clone the repository or download the ZIP and extract it. Example (Git):
   ```powershell
   git clone https://github.com/Khensanintulo911/-LTP-Analysis-Dashboard.git
   cd -LTP-Analysis-Dashboard
   ```

### Step 3: Install Required Packages
1. Open **Command Prompt** (Windows) or **Terminal** (Mac/Linux)
2. Navigate to your project folder:
   ```bash
   cd C:\path\to\your\project
   ```
3. Install the required packages:
   ```bash
   pip install streamlit pandas plotly openpyxl
   ```

### Step 4: Run the Application
1. In the same Command Prompt/Terminal, run:
   ```bash
   streamlit run app.py --server.port 5000
   ```
2. The app will open in your browser at:
   ```
   http://localhost:5000
   ```
3. To stop the app, press **Ctrl+C** in the terminal.

---

## 🧪 Testing the Application

### Test 1: Upload Your Spreadsheet
1. Open the app in your browser
2. Click "Browse files" or drag & drop your Excel/CSV file
3. **Expected Result:**
   - ✅ Success message showing number of records
   - ✅ Preview of your raw data
   - ✅ Dashboard appears with metrics and charts

### Test 2: Verify LTP Detection
1. Check the dashboard metrics:
   - **Total Appliances** - Should match your file row count
   - **LTP Items** - Items exceeding their threshold
   - **Avg Days Pending** - Average repair time

2. Look at the data table (scroll down)
   - **Red rows** = LTP items (exceeded threshold)
   - **White rows** = On-time items

### Test 3: Check Model Code Thresholds
1. Find the "Analysis by Model Code" section
2. Verify thresholds are correct:
   - **HA, DTV**: 7 days
   - **HHP, MTN**: 4 days

### Test 4: Use Filters
1. "Filter by LTP Status" → Select "LTP Only" to show only overdue items
2. "Filter by Model Code" → Select a specific code to filter

---

## 🌐 Deploying & Hosting (Making it Live on the Internet)

### Option 1: Host on a PaaS or Managed Hosting
Use a platform-as-a-service (Render, Railway, Fly, Heroku, etc.):

- Create a new service and point it to the repository.
- Configure build steps (example: `pip install -r requirements.txt`).
- Configure the start command:
  ```
  streamlit run app.py --server.port 5000
  ```
- Deploy and use the provided URL.

### Option 2: Host on Your Own Server (VM/VPS)
1. Rent a server (VPS) and install Python 3.11.
2. Upload project files or clone the repo.
3. Install packages:
   ```bash
   pip install streamlit pandas plotly openpyxl
   ```
4. Run the app and bind to all interfaces:
   ```bash
   streamlit run app.py --server.port 5000 --server.address 0.0.0.0
   ```
5. Use a process manager (pm2, supervisor) to keep it running and configure HTTPS via Let's Encrypt.

### Option 3: Local Network Only (Internal Access)
1. Run the app on a machine in your local network.
2. Find the machine IP (Windows: `ipconfig`).
3. Run:
   ```bash
   streamlit run app.py --server.port 5000 --server.address 0.0.0.0
   ```
4. Share `http://<machine-ip>:5000` with your team.

---

## 🔧 Troubleshooting

### Problem: "Python is not recognized"
**Solution:** Add Python to PATH or reinstall with "Add Python to PATH" enabled.

### Problem: "Module not found" error
**Solution:** Install missing packages:
```bash
pip install streamlit pandas plotly openpyxl
```

### Problem: "Port 5000 already in use"
**Solution:** Use a different port:
```bash
streamlit run app.py --server.port 8501
```

### Problem: Can't upload Excel file
**Solution:** Install the Excel engine:
```bash
pip install openpyxl
```

### Problem: App runs but shows errors with my spreadsheet
**Solution:** Ensure your spreadsheet includes:
- A "Requested Date" column (or similar)
- A "Model Code" column with expected codes (HA, DTV, HHP, MTN)
- Proper date formatting (YYYY-MM-DD or recognizable formats)

---

## 📞 Getting Help & Repo
- Repository: https://github.com/Khensanintulo911/-LTP-Analysis-Dashboard
- For issues with the app, open an issue on the repository or contact the developer directly.

---

## 🎯 Quick Start Summary

**For Local Testing:**
```bash
pip install streamlit pandas plotly openpyxl
streamlit run app.py --server.port 5000
```

**For Online Hosting:** Push the project to your chosen hosting provider, set the start command to `streamlit run app.py --server.port 5000`, and follow the provider's deployment steps.

That's it — your LTP Analysis Dashboard is ready to use. 🎉
