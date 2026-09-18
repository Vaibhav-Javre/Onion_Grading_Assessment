<div align="center">

# 🧅 OnionGrade AI

### AI-Powered Onion Quality Assessment & Digital Procurement System

**A Smart India Hackathon (SIH) Project — Problem Statement SIH26031**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#)
[![Flask](https://img.shields.io/badge/Backend-Flask-000000?logo=flask&logoColor=white)](#)
[![YOLO11](https://img.shields.io/badge/Detection-YOLO11-purple)](#)
[![EfficientNet](https://img.shields.io/badge/Classification-EfficientNet-orange)](#)
[![TensorFlow](https://img.shields.io/badge/DeepLearning-TensorFlow%2FKeras-FF6F00?logo=tensorflow&logoColor=white)](#)
[![Status](https://img.shields.io/badge/Status-Hackathon%20Prototype-yellow)](#)
[![License](https://img.shields.io/badge/License-Academic%2FHackathon-lightgrey)](#)

*Faster. More consistent. Transparent. Digitally traceable.*

</div>

---

## 🗒️ At a Glance

| | |
|---|---|
| **What it does** | Automates onion quality grading using computer vision instead of manual visual inspection |
| **Who it's for** | Farmers, Procurement Officers, and Government Authorities |
| **Core AI** | YOLO11 (detection) + EfficientNet (quality classification) |
| **Output** | Grade A / URS / Rejected classification + digital PDF report |
| **Stack** | Python, Flask, TensorFlow/Keras, OpenCV, SQLAlchemy, ReportLab |
| **Status** | Functional prototype built for Smart India Hackathon |

---

## 📌 Table of Contents

1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Proposed Solution](#proposed-solution)
4. [Key Features](#key-features)
5. [System Architecture](#system-architecture)
6. [AI Pipeline](#ai-pipeline)
7. [Quality Classification](#quality-classification)
8. [Grading Logic](#grading-logic)
9. [Project Structure](#project-structure)
10. [Technology Stack](#technology-stack)
11. [AI Model Information](#ai-model-information)
12. [Installation](#installation)
13. [Configuration](#configuration)
14. [Running the Application](#running-the-application)
15. [System Workflow](#system-workflow)
16. [Officer Portal](#officer-portal)
17. [Farmer Portal](#farmer-portal)
18. [Government Portal](#government-portal)
19. [Digital Reports](#digital-reports)
20. [Market Price Integration](#market-price-integration)
21. [Security](#security)
22. [Replacing AI Models](#replacing-ai-models)
23. [Limitations](#limitations)
24. [Future Scope](#future-scope)
25. [Project Status](#project-status)
26. [Demo](#project-demo)
27. [Screenshots](#screenshots)
28. [Team](#team)

---

<a id="project-overview"></a>
## 🌾 Project Overview

Quality assessment and grading of onions is traditionally performed through **manual visual inspection**. This process can vary significantly between evaluators, leading to inconsistent grading, manual counting errors, disputes, and little to no digital traceability.

**OnionGrade AI** replaces this subjective process with an automated, computer-vision-based pipeline. Given a photo (or live camera feed) of a batch of onions, the system:

1. 🔍 Detects individual onions in the image
2. ✂️ Crops each detected onion
3. 🏷️ Classifies each onion's visible quality
4. 📊 Aggregates results across the full batch
5. 🎯 Converts results into a procurement grade
6. 📄 Generates a digital PDF assessment report
7. 💰 Attaches live mandi market-price data
8. 🗄️ Stores everything as a searchable, auditable digital record

---

<a id="problem-statement"></a>
## ❗ Problem Statement

| Challenge | Impact |
|---|---|
| Subjective quality assessment | No two evaluators grade the same way |
| Variation between evaluators | Inconsistent outcomes across procurement centers |
| Manual counting & classification errors | Human fatigue and bias |
| Inconsistent grading | Farmer distrust in the process |
| Farmer–officer disputes | Delays and friction at procurement |
| Paper-based records | Records are lost, damaged, or hard to search |
| Limited auditability | No clear trail of who assessed what, and when |
| Inaccessible market-price info | Farmers negotiate without price transparency |
| No historical record-keeping | Impossible to analyze quality trends over time |

---

<a id="proposed-solution"></a>
## 💡 Proposed Solution

OnionGrade AI combines **computer vision**, **machine learning**, **automated grading logic**, and **digital record management** into a single platform.

```text
Image / Live Camera
        │
        ▼
Image Processing
        │
        ▼
YOLO11 Onion Detection
        │
        ▼
Individual Onion Crops
        │
        ▼
EfficientNet Quality Classification
        │
        ▼
Batch-Level Aggregation
        │
        ▼
Grade A / URS / Rejected
        │
        ▼
Digital PDF Report
        │
        ▼
Farmer / Officer / Government Records
```

---

<a id="key-features"></a>
## 🚀 Key Features

### 🤖 AI-Based Quality Assessment
- YOLO11-based onion detection, capable of finding multiple onions per image
- Automatic cropping of each detected onion
- EfficientNet-based per-onion quality classification
- Batch-level result aggregation
- Confidence-based handling of uncertain predictions

### 📊 Automated Grading
The AI classifies each onion as **Healthy**, **Damaged**, **Rotten**, or **Sprouted**, which the system then converts into a procurement category: **Grade A**, **URS**, or **Rejected**.

#<a id="officer-portal"></a>
## 👮 Officer Portal
Login → search/select a farmer → upload or capture images → run AI evaluation → review results → confirm → generate PDF report.

#<a id="farmer-portal"></a>
## 👨‍🌾 Farmer Portal
View evaluation results, report history, quality statistics, downloadable PDF reports, and current mandi market prices.

#<a id="government-portal"></a>
## 🏛️ Government Portal
Centralized monitoring of registered farmers, field officers, procurement centers, evaluations, transactions, quality statistics, audit records, and market data.

### 📄 Digital PDF Reports
Every confirmed evaluation automatically generates a formatted PDF report via **ReportLab**.

#<a id="market-price-integration"></a>
## 📈 Market Price Integration
Live integration with official government mandi price data (e.g. AGMARKNET).

### 🔐 Secure Role-Based Access
Farmers, officers, and government/admin users each get scoped access to only their relevant data.

---

<a id="system-architecture"></a>
## 🏗️ System Architecture

```text
                              ONIONGRADE AI
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
            FARMER               OFFICER            GOVERNMENT
            PORTAL                PORTAL               PORTAL
                │                   │                   │
                └───────────────────┼───────────────────┘
                                    ▼
                          PYTHON / FLASK BACKEND
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
             DATABASE                            AI PIPELINE
        (PostgreSQL / SQLite)                          │
                                        ┌───────────────┴───────────────┐
                                        ▼                               ▼
                                     YOLO11                       EfficientNet
                                    Detection                     Classification
                                        │                               │
                                        └───────────────┬───────────────┘
                                                        ▼
                                              QUALITY GRADING
                                                        │
                                    ┌───────────────────┼───────────────────┐
                                    ▼                   ▼                   ▼
                                 Grade A               URS               Rejected
                                                        │
                                                        ▼
                                              DIGITAL PDF REPORT
```

---

<a id="ai-pipeline"></a>
## 🤖 AI Pipeline

### 1️⃣ Image Input
Accepted formats: **JPG · JPEG · PNG · WEBP**. Images may contain one or many onions.

### 2️⃣ Onion Detection
The **YOLO11 Nano** object detection model locates every onion in the frame, returning a bounding box and confidence score for each.
> Implementation: `backend/ai/detector.py`

### 3️⃣ Individual Onion Cropping
```text
Original Image → YOLO11 Detection → Bounding Boxes → Individual Onion Crops
```

### 4️⃣ Quality Classification
Each crop is resized to `224 × 224 × 3` and passed through the **EfficientNet** classifier, which predicts one of: Healthy, Damaged, Rotten, Sprouted.
> Implementation: `backend/ai/classifier.py`

### 5️⃣ Confidence Handling
Classification confidence threshold: **0.50**

If a prediction falls below this threshold, it is labeled **Uncertain** and excluded from automatic grade assignment — keeping low-confidence predictions from skewing the batch result.

---

<a id="quality-classification"></a>
## 📊 Quality Classification

| Classification | Description |
|---|---|
| 🟢 Healthy | Good-quality onion |
| 🟠 Damaged | Onion showing physical damage |
| 🔴 Rotten | Onion showing visible rot or decay |
| 🟡 Sprouted | Onion showing sprouting |
| ⚪ Uncertain | Prediction confidence below threshold |

---

<a id="grading-logic"></a>
## 🏷️ Grading Logic

| AI Classification | Procurement Category |
|---|---|
| Healthy | **Grade A** |
| Damaged | **URS** |
| Rotten | **Rejected** |
| Sprouted | **Rejected** |
| Uncertain | Not Assigned |

**Batch-level formulas:**

```text
Grade A %   = Healthy / Total Observed × 100
URS %       = Damaged / Total Observed × 100
Rejected %  = (Rotten + Sprouted) / Total Observed × 100
```

The system aggregates actual onion counts across the complete batch to compute these percentages.

---

<a id="project-structure"></a>
## 📁 Project Structure

```text
oniongrade_ai/
│
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
│
├── backend/
│   ├── ai/
│   │   ├── detector.py
│   │   ├── classifier.py
│   │   └── pipeline.py
│   │
│   ├── database/
│   │   └── db.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── farmer.py
│   │   ├── officer.py
│   │   ├── evaluation.py
│   │   ├── report.py
│   │   └── market.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── farmer.py
│   │   ├── officer.py
│   │   ├── reports.py
│   │   ├── market.py
│   │   └── views.py
│   │
│   ├── services/
│   │   ├── pdf_service.py
│   │   └── market_price_service.py
│   │
│   └── utils/
│       ├── auth_helpers.py
│       ├── file_helpers.py
│       └── seed_data.py
│
├── models/
│   ├── best.pt
│   └── final_onion_quality_model.keras
│
├── static/
│   ├── css/main.css
│   ├── js/
│   │   ├── main.js
│   │   ├── evaluate.js
│   │   └── charts.js
│   ├── images/logo.svg
│   └── samples/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── farmer/
│   └── officer/
│
├── uploads/
├── outputs/
├── reports/
│   └── pdf/
│
└── instance/
    └── oniongrade.db
```

---

<a id="technology-stack"></a>
## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| Language | Python |
| Backend Framework | Flask |
| AI Detection | YOLO11 |
| AI Classification | EfficientNet |
| Deep Learning | TensorFlow / Keras |
| Image Processing | OpenCV, NumPy |
| Database | SQLite / PostgreSQL |
| ORM | SQLAlchemy |
| Frontend | HTML5, CSS3, JavaScript |
| Charts | Chart.js |
| PDF Generation | ReportLab |
| Authentication | Werkzeug Security |
| Market Data | Data.gov.in / AGMARKNET |

---

<a id="ai-model-information"></a>
## 📊 AI Model Information

### YOLO11 Detection Model
**Model:** YOLO11 Nano

| Dataset Split | Images |
|---|---|
| Total | 4,242 |
| Training | 2,968 |
| Validation | 850 |
| Testing | 424 |

**Training config:** 50 epochs · image size 640 · batch size 16

**Performance:**

| Metric | Score |
|---|---|
| Precision | ~0.976 |
| Recall | ~0.953 |
| mAP@50 | ~0.991 |
| mAP@50-95 | ~0.939 |

### EfficientNet Quality Classifier
Predicts 4 classes — Healthy, Damaged, Rotten, Sprouted — from a `224 × 224 × 3` input, with confidence-based handling for uncertain predictions.

---

<a id="installation"></a>
## 🚀 Installation

### Prerequisites
- Python 3.10+ (3.13 tested)
- pip
- Git

### 1. Clone the repository
```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd Onion_Project
```

### 2. Create a virtual environment

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

<a id="configuration"></a>
## ⚙️ Configuration

Copy the example environment file:
```bash
copy .env.example .env        # Windows
# or
cp .env.example .env          # Linux / macOS
```

Example `.env`:
```env
SECRET_KEY=your-secret-key

DATABASE_URL=sqlite:///instance/oniongrade.db

DETECTION_MODEL=models/best.pt
CLASSIFICATION_MODEL=models/final_onion_quality_model.keras

MARKET_API_KEY=your-api-key
MARKET_API_URL=your-api-url
```

> ⚠️ **Never commit your real `.env`, API keys, passwords, or secret keys to GitHub.** Make sure `.env` is listed in `.gitignore`.

**Required model files** (place inside `models/`):
```text
models/best.pt
models/final_onion_quality_model.keras
```
If these are too large for GitHub, host them externally and document the download steps here.

---

<a id="running-the-application"></a>
## ▶️ Running the Application

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

---

<a id="system-workflow"></a>
## 🔄 System Workflow

```text
Officer Login → Select Farmer → Upload/Capture Images → Run AI Evaluation
      → YOLO11 Detection → Onion Crops → EfficientNet Classification
      → Quality Aggregation → Grade A / URS / Rejected
      → Officer Review → Confirm Evaluation → Generate PDF Report
      → Farmer Portal → Government Portal
```

---

## 👮 Officer Portal

The procurement officer performs the initial onion evaluation.

```text
Officer Login → Dashboard → Select Farmer → Upload/Capture Images
      → Run AI Evaluation → Review Results → Confirm & Submit → Generate PDF
```

**Capabilities:** search & select farmers · upload multiple images · run the AI pipeline · view annotated images and onion-level classification · view quality distribution · review Grade A/URS/Rejected counts · confirm evaluation · generate PDF report.

---

## 👨‍🌾 Farmer Portal

Gives farmers self-service access to their own evaluation data.

**Capabilities:** view farmer details, total evaluations, Grade A/URS/Rejected counts, evaluation history, quality reports, downloadable PDF reports, and market-price information.

```text
Officer Confirms Evaluation → Report Generated → Linked to Farmer
      → Farmer Logs In → Views Report → Downloads PDF
```

---

## 🏛️ Government Portal

Centralized oversight and digital record management.

| Module | Tracks |
|---|---|
| Dashboard | Total farmers, officers, centers, evaluations, quality distribution, recent activity |
| Farmer Registry | Farmer ID, name, mobile, village, taluka, district, evaluation history |
| Officer Registry | Officer ID, name, procurement center, location, activity |
| Digital Transactions | Transaction/report ID, farmer, officer, center, date/time, quality counts, grade distribution, market price |
| Audit & Compliance | Who performed an action, what it was, and when it occurred |

---

<a id="digital-reports"></a>
## 📄 Digital Reports

Generated automatically after officer confirmation, using **ReportLab**. Each report includes:

Report ID · Farmer details · Officer details · Evaluation date/time · Total onions evaluated · Healthy/Damaged/Rotten/Sprouted counts · Grade A % · URS % · Rejected % · Market price · Final assessment · Evaluation details.

---

## 📈 Market Price Integration

Integrates with official government mandi price data via `backend/services/market_price_service.py`, displaying minimum, maximum, and modal price, market name, commodity, and last-updated time (e.g. **Lasalgaon Mandi**).

> Displayed values reflect the latest data available from the external source, subject to its own update frequency.

---

<a id="security"></a>
## 🔐 Security

| Area | Implementation |
|---|---|
| Role-Based Access Control | Separate access scopes for Farmer, Officer, Government/Admin |
| Password Security | Hashed via Werkzeug security utilities |
| File Upload Security | Validated extensions, UUID-renamed files, controlled storage paths (JPG/JPEG/PNG/WEBP only) |
| Farmer Report Protection | Farmers can only access their own reports |

---

<a id="replacing-ai-models"></a>
## 🔄 Replacing AI Models

1. Drop in your new model files:
   ```text
   models/my_new_yolo.pt
   models/my_new_classifier.keras
   ```
2. Update `.env`:
   ```env
   DETECTION_MODEL=models/my_new_yolo.pt
   CLASSIFICATION_MODEL=models/my_new_classifier.keras
   ```
3. Restart:
   ```bash
   python app.py
   ```
   The new models load automatically on startup.

---

<a id="limitations"></a>
## ⚠️ Limitations

- **Physical size estimation** — onion diameter/size isn't measured yet; this needs calibration, a scale reference, or depth data.
- **Model confidence** — predictions below 0.50 confidence are marked Uncertain and not auto-graded.
- **Market data** — accuracy and freshness depend on the external government data source.

---

<a id="future-scope"></a>
## 🔮 Future Scope

- Calibrated onion-size estimation
- Support for additional onion varieties
- Larger, more diverse datasets
- Improved low-light image handling
- Mobile application
- Edge AI deployment
- Multi-language farmer interface
- Wider government-system integration
- Advanced analytics
- Automated procurement workflows
- Real-time monitoring at procurement centers

---

<a id="project-status"></a>
## 📌 Project Status

**Status:** ✅ Functional Prototype / Hackathon Implementation

Implemented: AI detection & classification · automated grading · Officer, Farmer & Government portals · authentication · database integration · PDF report generation · market-price integration · digital evaluation records.

The project can be further optimized and tested for production-scale deployment.

---

<a id="project-demo"></a>
## 🎥 Project Demo

**OnionGrade AI | AI-Based Onion Quality Assessment & Digital Grading System | SIH26031**

[▶️ Watch the OnionGrade AI Demonstration](YOUR_YOUTUBE_VIDEO_LINK)

---

<a id="screenshots"></a>
## 📸 Screenshots

> Add screenshots to `docs/` and reference them below.

```text
docs/
├── landing-page.png
├── officer-dashboard.png
├── ai-evaluation.png
├── detection-result.png
├── grading-result.png
├── pdf-report.png
├── farmer-dashboard.png
├── government-dashboard.png
└── market-price.png
```

```markdown
![Officer Dashboard](docs/officer-dashboard.png)
![AI Evaluation](docs/ai-evaluation.png)
![Farmer Dashboard](docs/farmer-dashboard.png)
![Government Dashboard](docs/government-dashboard.png)
```

---

## 📂 Files to Include on GitHub

`README.md` · `requirements.txt` · `.env.example` · `.gitignore` · `app.py` · `config.py` · `backend/` · `models/` · `static/` · `templates/`

### 🚫 Files to Exclude

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo

# Virtual Environment
venv/
env/
.venv/

# Environment Variables
.env

# Database
instance/*.db

# Uploaded / Generated Files
uploads/*
outputs/*
reports/pdf/*

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

## 📜 License

Developed as an academic and hackathon project. If open-sourcing this repository, confirm that included datasets, trained models, images, and third-party components permit redistribution before adding a license.

---

<a id="team"></a>
## 👥 Team

<div align="center">

### Team CropVision
Developed for the **Smart India Hackathon**
**Problem Statement:** SIH26031

---

⭐ **OnionGrade AI** — bringing AI-powered, transparent, and digitally traceable quality assessment to onion procurement.

</div>
