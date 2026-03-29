# 🧬 Project Lazarus: Medical Forensic Recovery Dashboard

## 📌 Overview

Project Lazarus is a **Streamlit-based forensic analytics dashboard** designed to reconstruct and analyze corrupted medical datasets.

It ingests fragmented patient data (demographics, telemetry, and prescriptions), applies decoding and normalization techniques, and presents a **clean, interactive dashboard for patient monitoring and investigation**.

---

## 🚀 Features

### 🔍 Data Recovery & Cleaning

* Automatically detects required dataset files
* Handles inconsistent column names using normalization
* Supports multiple file naming conventions
* Gracefully handles missing or corrupted data

### 🧠 Intelligent Decoding

* **Caesar Cipher Decryption** for encoded patient names and medications
* **Hexadecimal → Numeric conversion** for telemetry values
* Smart ID parsing from mixed-format identifiers

### 📊 Patient Identity Reconstruction

* Builds identity cards with:

  * Patient ID
  * Decoded Name
  * Age
  * Ward classification (Even/Odd logic)

### ❤️ Vitals Monitoring

* Time-series visualization of:

  * Heart Rate (BPM)
  * Oxygen Levels (SpO₂)
* Missing oxygen values interpolated automatically
* Real-time **triage classification**:

  * `CRITICAL` → BPM < 60 or > 100
  * `STABLE` → Normal range

### 💊 Pharmacy Intelligence

* Decrypts scrambled medication data using patient-specific logic
* Displays both raw and decoded prescriptions

### 🧪 Diagnostics Panel

* Inspect detected dataset schemas
* Debug column mismatches easily

---

## 📁 Project Structure

```
.
├── app.py
└── data/
    ├── patient_demographics.csv
    ├── telemetry_logs.csv
    └── prescription_audit.csv
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/REPO_NAME.git
cd REPO_NAME
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

If no requirements file:

```bash
pip install streamlit pandas numpy
```

---

## ▶️ Usage

### Step 1: Add Data

Place the required CSV files inside the `data/` folder:

* `patient_demographics.csv`
* `telemetry_logs.csv`
* `prescription_audit.csv`

---

### Step 2: Run the App

```bash
streamlit run app.py
```

---

### Step 3: Open Dashboard

Streamlit will automatically open in your browser.

---

## 🧠 Core Concepts Used

* Data Normalization
* Time-Series Processing
* Interpolation Techniques
* Cipher Decryption (Caesar Shift)
* Hexadecimal Parsing
* Data Merging & Transformation
* Interactive Visualization (Streamlit)

---

## ⚠️ Error Handling

If required files are missing:

```
Missing required file(s): ...
Place CSVs in ./data
```

---

## 🎯 Use Cases

* Medical data recovery systems
* Cyber-forensics on corrupted datasets
* Healthcare monitoring dashboards
* Hackathon / prototype systems

---

## 🔮 Future Improvements

* Machine Learning-based anomaly detection
* Real-time data streaming support
* Authentication & secure access layer
* Advanced patient risk scoring

---

## 🏁 Conclusion

Project Lazarus demonstrates how **data engineering + simple cryptography + visualization** can transform noisy datasets into actionable medical insights.

---

## 👨‍💻 Author

Developed as part of a forensic data recovery and analytics project.
