# OnionGrade AI

## AI-Powered Onion Quality Assessment & Digital Procurement System

**Smart India Hackathon (SIH) Project**

OnionGrade AI is an AI-powered agricultural technology platform designed to automate and standardize onion quality assessment and procurement grading.

The system combines **YOLO11 object detection**, **EfficientNet-based quality classification**, automated grading, digital PDF report generation, market-price integration, and role-based portals for **Farmers, Procurement Officers, and Government Authorities**.

---

## 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Problem Statement](#-problem-statement)
- [Proposed Solution](#-proposed-solution)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [AI Pipeline](#-ai-pipeline)
- [Quality Classification](#-quality-classification)
- [Grading Logic](#-grading-logic)
- [Project Structure](#-project-structure)
- [Technology Stack](#-technology-stack)
- [AI Model Information](#-ai-model-information)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [System Workflow](#-system-workflow)
- [Officer Portal](#-officer-portal)
- [Farmer Portal](#-farmer-portal)
- [Government Portal](#-government-portal)
- [Digital Reports](#-digital-reports)
- [Market Price Integration](#-market-price-integration)
- [Security](#-security)
- [Replacing AI Models](#-replacing-ai-models)
- [Limitations](#-limitations)
- [Future Scope](#-future-scope)
- [Project Status](#-project-status)
- [Demo](#-demo)
- [Team](#-team)

---

## 🌾 Project Overview

Quality assessment and grading of onions is traditionally performed through manual visual inspection. The assessment can vary between evaluators, which may lead to inconsistent grading, manual errors, disputes, and limited digital traceability.

**OnionGrade AI** provides an automated computer-vision-based approach for onion quality assessment.

The system:

1. Detects onions from uploaded images or camera input.
2. Extracts individual onion crops.
3. Classifies each onion based on visible quality.
4. Aggregates results across the complete batch.
5. Converts quality results into procurement grades.
6. Generates a digital PDF assessment report.
7. Provides mandi market-price information.
8. Maintains digital evaluation and transaction records.

---

## ❗ Problem Statement

Traditional onion quality assessment can involve manual inspection and subjective decision-making.

Major challenges include:

- Subjective quality assessment
- Variation between evaluators
- Manual counting and classification errors
- Inconsistent grading
- Disputes between farmers and procurement authorities
- Paper-based records
- Limited auditability
- Lack of accessible market-price information
- Difficulty maintaining transparent historical records

---

## 💡 Proposed Solution

OnionGrade AI combines computer vision, machine learning, automated grading, and digital record management into one platform.

The proposed workflow is:

```text
Image / Live Camera
        ↓
Image Processing
        ↓
YOLO11 Onion Detection
        ↓
Individual Onion Crops
        ↓
EfficientNet Quality Classification
        ↓
Batch-Level Aggregation
        ↓
Grade A / URS / Rejected
        ↓
Digital PDF Report
        ↓
Farmer / Officer / Government Records
```

The platform aims to make onion quality assessment:

- Faster
- More consistent
- Transparent
- Digitally traceable
- Easier to monitor

---

## 🚀 Key Features

### 🤖 AI-Based Quality Assessment

- YOLO11-based onion detection
- Detection of multiple onions in a single image
- Individual onion cropping
- EfficientNet-based quality classification
- Batch-level aggregation
- Confidence-based uncertainty handling

### 📊 Automated Grading

The system classifies onions into:

- Healthy
- Damaged
- Rotten
- Sprouted

The classifications are converted into:

- Grade A
- URS
- Rejected

### 👮 Officer Portal

Procurement officers can:

- Login securely
- Search and select farmers
- Upload onion images
- Capture samples through camera input
- Run AI evaluation
- Review detected onions
- Review quality classification
- Review batch-level results
- Confirm the evaluation
- Generate the digital PDF report

### 👨‍🌾 Farmer Portal

Farmers can:

- Login securely
- View their evaluation results
- View report history
- View quality statistics
- View generated reports
- Download PDF reports
- View mandi market-price information

### 🏛️ Government Portal

Government authorities can monitor:

- Registered farmers
- Field officers
- Procurement centers
- Evaluations
- Transactions
- Quality statistics
- Reports
- Audit records
- Market-price information
- Historical records

### 📄 Digital PDF Reports

The system automatically generates digital assessment reports using **ReportLab**.

### 📈 Market Price Integration

The platform supports integration with official mandi market-price data.

### 🔐 Secure Role-Based Access

Different user roles have controlled access to their respective functionality and records.

---

## 🏗️ System Architecture

```text
                         ONIONGRADE AI
                              │
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
          FARMER          OFFICER        GOVERNMENT
          PORTAL           PORTAL           PORTAL
              │               │               │
              └───────────────┼───────────────┘
                              ↓
                       PYTHON / FLASK
                          BACKEND
                              │
                ┌─────────────┴─────────────┐
                ↓                           ↓
          DATABASE                     AI PIPELINE
       PostgreSQL / SQLite                  │
                                            │
                              ┌─────────────┴─────────────┐
                              ↓                           ↓
                           YOLO11                    EfficientNet
                          Detection                  Classification
                              │                           │
                              └─────────────┬─────────────┘
                                            ↓
                                    QUALITY GRADING
                                            │
                              ┌─────────────┼─────────────┐
                              ↓             ↓             ↓
                           Grade A         URS         Rejected
                                            │
                                            ↓
                                      DIGITAL REPORT
```

---

## 🤖 AI Pipeline

### 1. Image Input

The system accepts onion images in the following formats:

- JPG
- JPEG
- PNG
- WEBP

Images may contain one or multiple onions.

### 2. Onion Detection

The **YOLO11 Nano** object detection model identifies individual onions.

For every detected onion, the model provides:

- Bounding Box
- Confidence Score

Detector implementation: `backend/ai/detector.py`

### 3. Individual Onion Cropping

Each detected onion is extracted from the original image.

```text
Original Image
      ↓
YOLO11 Detection
      ↓
Bounding Boxes
      ↓
Individual Onion Crops
```

### 4. Quality Classification

Each onion crop is passed to the EfficientNet-based classification model.

Model input: `224 × 224 × 3`

The classifier predicts one of four classes:

- Healthy
- Damaged
- Rotten
- Sprouted

Classifier implementation: `backend/ai/classifier.py`

### 5. Confidence Handling

The classification confidence threshold is: **0.50**

If the prediction confidence is below the threshold:

> Prediction → **Uncertain**

Uncertain onions are kept separate and are not automatically assigned to a procurement grade.

---

## 📊 Quality Classification

| Classification | Description |
|---|---|
| Healthy | Good-quality onion |
| Damaged | Onion showing physical damage |
| Rotten | Onion showing visible rot or decay |
| Sprouted | Onion showing sprouting |
| Uncertain | Prediction confidence below threshold |

---

## 🏷️ Grading Logic

The AI classification results are converted into procurement categories.

| AI Classification | Procurement Category |
|---|---|
| Healthy | Grade A |
| Damaged | URS |
| Rotten | Rejected |
| Sprouted | Rejected |
| Uncertain | Not Assigned |

### Batch-Level Calculation

```text
Grade A % = Healthy / Total Observed × 100

URS % = Damaged / Total Observed × 100

Rejected % = (Rotten + Sprouted) / Total Observed × 100
```

The system aggregates actual onion counts across the complete batch.

---

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
│   ├── css/
│   │   └── main.css
│   ├── js/
│   │   ├── main.js
│   │   ├── evaluate.js
│   │   └── charts.js
│   ├── images/
│   │   └── logo.svg
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

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| Programming Language | Python |
| Backend | Flask |
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
| Market Data | Data.gov.in / AGMARKNET Integration |

---

## 📊 AI Model Information

### YOLO11 Detection Model

**Model:** YOLO11 Nano

**Dataset:**

| Split | Images |
|---|---|
| Total | 4,242 |
| Training | 2,968 |
| Validation | 850 |
| Testing | 424 |

**Training Configuration:**

- Epochs: 50
- Image Size: 640
- Batch Size: 16

**Detection Performance:**

| Metric | Value |
|---|---|
| Precision | ~0.976 |
| Recall | ~0.953 |
| mAP@50 | ~0.991 |
| mAP@50-95 | ~0.939 |

### EfficientNet Quality Classifier

The classifier identifies four onion-quality classes:

- Damaged
- Healthy
- Rotten
- Sprouted

**Input size:** `224 × 224 × 3`

The classifier uses confidence-based handling for uncertain predictions.

---

## 🚀 Installation

### Prerequisites

Make sure the following are installed:

- Python 3.10+
- pip
- Git

> Python 3.13 has been tested with the project.

### 1. Clone Repository

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd Onion_Project
```

### 2. Create Virtual Environment

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

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Create a `.env` file from `.env.example`.

**Windows**

```bash
copy .env.example .env
```

Example configuration:

```env
SECRET_KEY=your-secret-key

DATABASE_URL=sqlite:///instance/oniongrade.db

DETECTION_MODEL=models/best.pt
CLASSIFICATION_MODEL=models/final_onion_quality_model.keras

MARKET_API_KEY=your-api-key
MARKET_API_URL=your-api-url
```

> **Important**
>
> Do not upload your real `.env`, API keys, passwords, or secret keys to GitHub.
>
> Add `.env` to `.gitignore`.

### 🧠 AI Model Files

Place the trained models inside `models/`.

Required files:

```text
models/best.pt
models/final_onion_quality_model.keras
```

If the model files are too large for GitHub, store them using an appropriate model/file hosting service and provide download instructions in this README.

---

## ▶️ Running the Application

Start the Flask application:

```bash
python app.py
```

Then open:

```text
http://localhost:5000
```

in your browser.

---

## 🔄 System Workflow

The complete system workflow is:

```text
Officer Login
      ↓
Select Farmer
      ↓
Upload / Capture Onion Images
      ↓
Run AI Evaluation
      ↓
YOLO11 Detection
      ↓
Individual Onion Crops
      ↓
EfficientNet Classification
      ↓
Quality Aggregation
      ↓
Grade A / URS / Rejected
      ↓
Officer Review
      ↓
Confirm Evaluation
      ↓
Generate Digital PDF Report
      ↓
Farmer Portal
      ↓
Government Portal
```

---

## 👮 Officer Portal

The procurement officer performs the initial onion evaluation.

### Workflow

```text
Officer Login
      ↓
Officer Dashboard
      ↓
Select Farmer
      ↓
Upload / Capture Images
      ↓
Run AI Evaluation
      ↓
Review Results
      ↓
Confirm & Submit
      ↓
Generate PDF Report
```

### Officer can:

- Search farmers
- Select a farmer
- Upload multiple images
- Run the AI pipeline
- View annotated images
- View onion-level classification
- View quality distribution
- Review Grade A / URS / Rejected counts
- Confirm evaluation
- Generate PDF report

---

## 👨‍🌾 Farmer Portal

The Farmer Portal provides access to the farmer's evaluation information.

### Farmer can view:

- Farmer details
- Total evaluations
- Grade A count
- URS count
- Rejected count
- Evaluation history
- Quality reports
- Digital PDF reports
- Market-price information

### Report Workflow

```text
Officer Confirms Evaluation
          ↓
Digital Report Generated
          ↓
Report Linked to Farmer
          ↓
Farmer Login
          ↓
View Report
          ↓
Download PDF
```

---

## 🏛️ Government Portal

The Government Portal provides centralized monitoring and digital record management.

### Dashboard

The dashboard can provide:

- Total farmers
- Total officers
- Procurement centers
- Total evaluations
- Quality distribution
- Recent evaluations
- Transactions
- Market information

### Farmer Registry

Stores information such as:

- Farmer ID
- Name
- Mobile Number
- Village
- Taluka
- District
- Evaluation History

### Officer Registry

Stores:

- Officer ID
- Name
- Procurement Center
- Location
- Evaluation Activity

### Digital Transactions

Transaction records can contain:

- Transaction ID
- Report ID
- Farmer
- Officer
- Procurement Center
- Date / Time
- Quality Counts
- Grade Distribution
- Market Price
- Report Reference

### Audit & Compliance

The system maintains digital records related to:

- Who performed the action
- What action was performed
- When the action occurred

---

## 📄 Digital Reports

After the officer confirms an evaluation, OnionGrade AI generates a digital PDF report.

The report can contain:

- Report ID
- Farmer details
- Officer details
- Evaluation date/time
- Total onions evaluated
- Healthy count
- Damaged count
- Rotten count
- Sprouted count
- Grade A percentage
- URS percentage
- Rejected percentage
- Market price
- Final assessment
- Evaluation details

PDF generation is handled using **ReportLab**.

---

## 📈 Market Price Integration

OnionGrade AI supports integration with official government mandi market-price data.

The market-price service is located at:

```text
backend/services/market_price_service.py
```

The system can display:

- Minimum price
- Maximum price
- Modal price
- Market name
- Commodity
- Update date/time

**Example market:** Lasalgaon Mandi

> The displayed value should be treated as the latest available mandi price, depending on the external data source's update frequency.

---

## 🔐 Security

The system implements multiple security mechanisms.

### Role-Based Access Control

The application separates access for:

- Farmer
- Officer
- Government / Admin

### Password Security

Passwords are stored using secure password hashing through Werkzeug security utilities.

### File Upload Security

Uploaded images are:

- Validated
- Restricted to supported extensions
- Renamed using UUIDs
- Stored using controlled file paths

Supported formats: JPG, JPEG, PNG, WEBP

### Farmer Report Protection

Farmers can access reports associated with their own farmer account.

Unauthorized access to another farmer's protected report is prevented.

---

## 🔄 Replacing AI Models

To replace the YOLO model:

```text
models/my_new_yolo.pt
```

To replace the classifier:

```text
models/my_new_classifier.keras
```

Update the `.env` file:

```env
DETECTION_MODEL=models/my_new_yolo.pt
CLASSIFICATION_MODEL=models/my_new_classifier.keras
```

Restart the application:

```bash
python app.py
```

The new models will be loaded during application startup.

---

## ⚠️ Limitations

### Physical Size Estimation

Physical onion diameter/size estimation is not included in the current version.

Reliable physical measurement from an arbitrary RGB image requires appropriate calibration, scale reference, depth information, or another controlled measurement setup.

The architecture can be extended in the future to support calibrated size estimation.

### Model Confidence

Predictions below the configured confidence threshold are marked **Uncertain**.

They are not automatically assigned to a procurement grade.

### Market Data

Market-price information depends on the availability and update frequency of the external government data source.

---

## 🔮 Future Scope

Future improvements may include:

- Calibrated onion-size estimation
- Support for additional onion varieties
- Larger and more diverse datasets
- Improved low-light image handling
- Mobile application
- Edge AI deployment
- Multi-language farmer interface
- Wider government-system integration
- Advanced analytics
- Automated procurement workflows
- Real-time monitoring at procurement centers

---

## 📌 Project Status

**Status:** Functional Prototype / Hackathon Implementation

Implemented components include:

- AI onion detection
- AI quality classification
- Automated grading
- Officer Portal
- Farmer Portal
- Government monitoring functionality
- Authentication
- Database integration
- PDF report generation
- Market-price integration capability
- Digital evaluation records

The project can be further optimized and tested for production-scale deployment.

---

## 🎥 Project Demo

### YouTube Demonstration

**OnionGrade AI | AI-Based Onion Quality Assessment & Digital Grading System | SIH26031**

Add your YouTube link here: `https://youtu.be/3Ji59fw6_HE?feature=shared`

Or use:

```markdown
[▶️ Watch the OnionGrade AI Demonstration](https://youtu.be/3Ji59fw6_HE?feature=shared)
```

---

## 📸 Screenshots

Add screenshots to the repository under `docs/`:

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

Then add them to this README:

```markdown
![Officer Dashboard](docs/officer-dashboard.png)

![AI Evaluation](docs/ai-evaluation.png)

![Farmer Dashboard](docs/farmer-dashboard.png)

![Government Dashboard](docs/government-dashboard.png)
```

---

## 📂 Important GitHub Files

Before pushing the project to GitHub, make sure you have:

- `README.md`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `app.py`
- `config.py`
- `backend/`
- `models/`
- `static/`
- `templates/`

## 🚫 Files to Exclude from GitHub

Do not commit:

```text
.env
venv/
__pycache__/
*.pyc
instance/*.db
uploads/*
outputs/*
reports/pdf/*
```

unless you intentionally want to distribute demo files.

Example `.gitignore`:

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

# Uploaded Files
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

This project was developed as an academic and hackathon project.

If the repository is intended to be open source, add an appropriate license after confirming that the included datasets, trained models, images, and third-party components permit redistribution.

---

## 👥 Team

**Team CropVision**

Developed as part of: **Smart India Hackathon**

**Problem Statement:** SIH26031

---

⭐ **OnionGrade AI** — AI-powered onion quality assessment and digital procurement platform for faster, more consistent, transparent, and digitally traceable agricultural quality assessment.
