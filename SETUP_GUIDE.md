# LTP Analysis Dashboard - Setup & Deployment Guide

## 📋 Table of Contents
1. [Running Locally on Your PC](#running-locally-on-your-pc)
2. [Testing the Application](#testing-the-application)
3. [Deploying & Hosting](#deploying--hosting)
4. [Troubleshooting](#troubleshooting)

---

## 🖥️ Running Locally on Your PC

### Step 1: Install Python
1. **Download Python 3.11** from [python.org/downloads](https://www.python.org/downloads/)
2. During installation, **check the box** that says "Add Python to PATH"
3. Verify installation by opening **Command Prompt** (Windows) or **Terminal** (Mac/Linux) and typing:
   ```bash
   python --version
   ```
   You should see: `Python 3.11.x`

### Step 2: Download the Project Files
1. In Replit, click on the **three dots menu** (⋮) in the file explorer
2. Download these files to a folder on your PC:
   - `app.py` (main application)
   - `pyproject.toml` (dependencies list)
   - `.streamlit/config.toml` (configuration)

**OR** if you're an Explorer/Staff user, download the entire project folder

### Step 3: Install Required Packages
1. Open **Command Prompt** (Windows) or **Terminal** (Mac/Linux)
2. Navigate to your project folder:
   ```bash
   cd C:\path\to\your\project
   ```
   (Replace with your actual folder path)

3. Install the required packages:
   ```bash
   pip install streamlit pandas plotly openpyxl
   ```

### Step 4: Run the Application
1. In the same Command Prompt/Terminal, run:
   ```bash
   streamlit run app.py --server.port 5000
   ```

2. The app will open automatically in your browser at:
   ```
   http://localhost:5000
   ```

3. To stop the app, press **Ctrl+C** in the Command Prompt/Terminal

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
   - **HA, DTV**: Should show 7 days threshold
   - **HHP, MTN**: Should show 4 days threshold

### Test 4: Use Filters
1. Try "Filter by LTP Status" → Select "LTP Only"
   - Should show only red/overdue items
2. Try "Filter by Model Code" → Select a specific code (e.g., "DTV")
   - Should show only that model type

---

## 🌐 Deploying & Hosting (Making it Live on the Internet)

### Option 1: Host on Replit (Recommended - Easiest)

#### A. Publish Your App
1. In your Replit workspace, click the **"Publish"** button (top right)
2. Replit will automatically select **Autoscale Deployment** (best for web apps)
3. Configure settings:
   - **App Name**: Choose a name (e.g., "ltp-dashboard")
   - **Machine Power**: Start with small (you can upgrade later)
   - **Run Command**: Already set to `streamlit run app.py --server.port 5000`
4. Click **"Deploy"**

#### B. Your App Will Be Live!
- You'll get a URL like: `https://your-app-name.replit.app`
- Anyone can access it (share the link with your team)
- The app stays online 24/7
- Automatically scales if you get more users

#### C. Add a Custom Domain (Optional)
1. In the Publish settings, click **"Add Custom Domain"**
2. You can either:
   - **Buy a domain through Replit** (e.g., `ltp-analysis.com`)
   - **Link your existing domain** (e.g., `dashboard.yourcompany.com`)
3. Follow the setup instructions provided by Replit

**Cost Considerations:**
- Basic hosting is included with your Replit plan
- Custom domains may have additional costs
- Check the Replit pricing page for current rates

---

### Option 2: Host on Your Own Server

If you want full control and have your own server:

#### A. Using a Cloud Provider (AWS, Google Cloud, Azure, DigitalOcean)
1. **Rent a server** (called VPS or Virtual Machine)
2. **Install Python 3.11** on the server
3. **Upload your project files** to the server
4. **Install packages**: `pip install streamlit pandas plotly openpyxl`
5. **Run the app**:
   ```bash
   streamlit run app.py --server.port 5000 --server.address 0.0.0.0
   ```
6. **Keep it running** using a process manager like `pm2` or `supervisor`
7. **Get a domain** and point it to your server's IP address
8. **Set up HTTPS** using services like Let's Encrypt (for security)

**Note:** This option is more complex and requires technical knowledge.

---

### Option 3: Local Network Only (For Internal Use Only)

If you only want people in your office to access it:

1. **Run the app on one computer** in your office
2. Find that computer's **local IP address**:
   - Windows: Run `ipconfig` in Command Prompt
   - Mac/Linux: Run `ifconfig` in Terminal
   - Look for something like `192.168.1.100`
3. **Run the app**:
   ```bash
   streamlit run app.py --server.port 5000 --server.address 0.0.0.0
   ```
4. **Share the link** with your team:
   ```
   http://192.168.1.100:5000
   ```
   (Replace with your actual IP)

**Limitations:**
- Only works on the same WiFi/network
- The computer must stay on and running the app
- Not accessible from outside your office

---

## 🔧 Troubleshooting

### Problem: "Python is not recognized"
**Solution:** Python wasn't added to PATH during installation
- Reinstall Python and check "Add Python to PATH"
- OR manually add Python to your PATH environment variable

### Problem: "Module not found" error
**Solution:** Packages not installed
```bash
pip install streamlit pandas plotly openpyxl
```

### Problem: "Port 5000 already in use"
**Solution:** Another app is using that port
- Use a different port: `streamlit run app.py --server.port 8501`

### Problem: Can't upload Excel file
**Solution:** Missing openpyxl package
```bash
pip install openpyxl
```

### Problem: App runs but shows errors with my spreadsheet
**Solution:** Check your spreadsheet has:
- A column named "Requested Date" (or similar)
- A column named "Model Code" (with HA, DTV, HHP, MTN values)
- Dates formatted properly (e.g., 11.18.2025 or 2025-11-18)

### Problem: Deployment failed on Replit
**Solution:**
1. Check your internet connection
2. Try a different browser
3. In Replit Shell, run: `kill 1` to restart the VM
4. Try publishing again

---

## 📞 Getting Help

- **Replit Issues**: Contact Replit support through the platform
- **App Bugs**: Check the Replit console logs for error messages
- **Need Changes**: Request modifications to the app functionality

---

## 🎯 Quick Start Summary

**For Local Testing:**
```bash
# Install Python 3.11
# Install packages
pip install streamlit pandas plotly openpyxl

# Run the app
streamlit run app.py --server.port 5000
```

**For Online Hosting (Easiest):**
1. Click "Publish" button in Replit
2. Choose Autoscale Deployment
3. Click Deploy
4. Share your `.replit.app` URL

**That's it!** Your LTP Analysis Dashboard is ready to use! 🎉
