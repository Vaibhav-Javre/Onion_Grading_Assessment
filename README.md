# OnionGrade AI

### AI-Powered Onion Quality Assessment & Digital Procurement System
**Smart India Hackathon (SIH) Project**

---

## 🌾 Project Overview

Quality assessment and grading of onions is traditionally subjective and varies significantly across agricultural procurement centers (APMC Mandis). This lack of standardization leads to:
- Frequent disputes between farmers and procurement authorities
- Inconsistent quality grading and arbitrary pricing cuts
- Lack of verifiable audit trails and paper slip manipulation
- Severe market information asymmetry for rural farmers

**OnionGrade AI** is a production-grade full-stack agricultural technology platform that standardizes onion quality assessment. Using computer vision (**YOLO11** object detection and a custom deep **CNN quality classifier**), the system automatically detects bulk onions, classifies each bulb into **Healthy**, **Damaged**, **Rotten**, or **Sprouted**, and generates certified procurement grade decisions (**Grade A**, **URS**, **Rejected**), complete with official **ReportLab PDF assessment certificates** and **live Mandi market prices**.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.13, Flask, Werkzeug (scrypt password hashing), Modular Blueprints |
| **Database & ORM** | SQLite (development) / PostgreSQL compatible, SQLAlchemy 2.0 ORM |
| **AI / Machine Learning** | Ultralytics YOLO11 (object detection), TensorFlow 2.x & Keras 3.x (quality classification), OpenCV, NumPy |
| **PDF Generation** | ReportLab (government APMC-compliant certificate layout) |
| **Frontend** | HTML5, Vanilla CSS3 (custom agricultural design system), JavaScript (ES6+), Chart.js |
| **Live Market Feeds** | APMC Mandi price service with Agmarknet / Data.gov.in integration capability |

---

## 🏛️ System Architecture

```
oniongrade_ai/
├── app.py                          # Flask application factory & startup
├── config.py                       # Configuration & threshold settings
├── requirements.txt                # System dependencies
├── .env.example                    # Sample environment variables
├── README.md                       # Documentation
│
├── backend/
│   ├── ai/
│   │   ├── detector.py             # YOLO11 onion detector (singleton/cached)
│   │   ├── classifier.py           # Keras quality classification model (singleton/cached)
│   │   └── pipeline.py             # Integrated detection + classification + annotation pipeline
│   ├── database/
│   │   └── db.py                   # SQLAlchemy instance and schema creation
│   ├── models/
│   │   ├── user.py                 # User model (Farmer & Officer roles)
│   │   ├── farmer.py               # FarmerProfile model (Farmer ID, Location)
│   │   ├── officer.py              # OfficerProfile model (Officer ID, Center)
│   │   ├── evaluation.py           # Evaluation and EvaluationItem models
│   │   ├── report.py               # Report model (PDF path, size)
│   │   └── market.py               # MarketPrice model (Mandi price records)
│   ├── routes/
│   │   ├── auth.py                 # Register, Login, Logout, Session API
│   │   ├── farmer.py               # Farmer dashboard, reports, profile API
│   │   ├── officer.py              # Officer dashboard, evaluation wizard API
│   │   ├── reports.py              # Secured report details and PDF streaming API
│   │   ├── market.py               # Live market prices & district filters API
│   │   └── views.py                # Page rendering routes
│   ├── services/
│   │   ├── pdf_service.py          # ReportLab official PDF generator
│   │   └── market_price_service.py # APMC Mandi price service & Agmarknet integration
│   └── utils/
│       ├── auth_helpers.py         # @login_required, @role_required, ID generators
│       ├── file_helpers.py         # UUID file storage, extension validation
│       └── seed_data.py            # Demo seed data (farmers, officer, reports)
│
├── models/
│   ├── best.pt                     # YOLO11 onion detector model
│   └── final_onion_quality_model.keras # Keras 4-class quality classifier
│
├── static/
│   ├── css/main.css                # Custom agricultural design system
│   ├── js/
│   │   ├── main.js                 # Global UI & toast notifications
│   │   ├── evaluate.js             # 5-step evaluation wizard & live charts
│   │   └── charts.js               # Chart.js donut, bar, and trend renderers
│   ├── images/logo.svg             # OnionGrade AI vector logo
│   └── samples/                    # Quick test sample onion images
│
├── templates/                      # Jinja2 responsive templates
│   ├── base.html                   # Base layout & collapsible sidebar
│   ├── index.html                  # Public landing page
│   ├── auth/                       # Farmer login/register & Officer login
│   ├── farmer/                     # Farmer dashboard, reports, and market
│   └── officer/                    # Officer dashboard, evaluation wizard, reports
│
├── uploads/                        # Uploaded batch images (UUID-named)
├── outputs/                        # Annotated output images with bounding boxes
├── reports/pdf/                    # Generated official assessment PDFs
└── instance/
    └── oniongrade.db               # SQLite database
```

---

## 🤖 AI Pipeline & Quality Grading Logic

### Pipeline Stages
1. **Input**: High-resolution batch photograph of onions (JPG, JPEG, PNG, WEBP).
2. **YOLO11 Detection** (`backend/ai/detector.py`):
   - Model: `models/best.pt`
   - Detects all visible onion bulbs with bounding box coordinates `[x1, y1, x2, y2]` and confidence score.
3. **Cropping**:
   - Each detected bulb is extracted into an individual sub-image.
4. **CNN Quality Classification** (`backend/ai/classifier.py`):
   - Model: `models/final_onion_quality_model.keras`
   - Input shape: `(224, 224, 3)`
   - Classifies each crop into exactly 4 classes:
     - **Healthy**
     - **Damaged**
     - **Rotten**
     - **Sprouted**
   - If confidence is below the threshold (`0.50`), the item is flagged as **Uncertain**.
5. **Annotation** (`backend/ai/pipeline.py`):
   - Draws distinct color-coded bounding boxes and badges on the image:
     - 🟩 **Healthy** (Vibrant Green)
     - 🟨 **Damaged** (Amber / Warm Gold)
     - 🟥 **Rotten** (Crimson Red)
     - 🟧 **Sprouted** (Deep Orange)

### Official Procurement Grading Rules
Per agricultural procurement standards:
- **Grade A**: Healthy onions (`Healthy` count)
- **URS** (Under Regular Standard): Damaged onions (`Damaged` count)
- **Rejected**: Rotten and sprouted onions (`Rotten` + `Sprouted` count)

> **Important**: Size estimation / diameter measurement is strictly excluded from this version per project specification. A clean architectural hook (`FUTURE_EXTENSION_POINT_SIZE_ESTIMATION`) is preserved in `backend/ai/pipeline.py` for future segmentation integration.

---

## 🚀 Quick Setup & Installation

### 1. Prerequisites
- Python 3.10+ (Python 3.13 tested and verified)
- pip package manager

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone <repo-url>
cd Onion_Project

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/macOS
```

### 3. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Adjust configurations as needed (or use default development values).

### 5. Verify Model Files
Ensure models exist in the `models/` directory:
- `models/best.pt` (YOLO11 detector)
- `models/final_onion_quality_model.keras` (Keras classifier)

### 6. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 🔑 Demo Accounts & Test Credentials

The system automatically seeds demo accounts on first launch:

| Role | Username / Identifier | Password | Details |
|---|---|---|---|
| **Farmer 1** | `9876543210` (or `FMR-2026-0001`) | `farmer123` | Ramesh Patil (Pimpalgaon Baswant, Nashik) |
| **Farmer 2** | `9823012345` (or `FMR-2026-0002`) | `farmer123` | Suresh Deshmukh (Vinchur, Yeola) |
| **Officer** | `OFF-2026-001` (or `vikram.shinde@apmc.gov.in`) | `officer123` | Vikram Shinde (Lasalgaon APMC Yard) |

*Convenient "Fill Demo Credentials" buttons are provided on both login pages for rapid hackathon presentation.*

---

## 📋 Step-by-Step Demonstration Walkthrough

### 1. Procurement Officer Workflow:
1. Navigate to `/login/officer` and click **Fill Demo Officer Credentials**.
2. From the **Officer Dashboard**, click **📷 SCAN / EVALUATE ONIONS**.
3. **Step 1: Select Farmer**: Type `Ramesh` or `FMR-2026-0001` in the search bar and click **Select**.
4. **Step 2: Upload Image**: Click any test sample button (e.g., **Sample 1** or **Sample 2**) or drag and drop an onion image.
5. Click **⚡ Run AI Quality Evaluation Pipeline**.
6. Observe the animated multi-step progress bar (`Uploading...` → `Detecting onions...` → `Classifying quality...` → `Generating grading...`).
7. **Step 3: Review Results**:
   - Inspect the annotated image with green, amber, and red bounding boxes.
   - View the interactive Chart.js Quality Donut and Grade Distribution Bar charts.
   - Review the individual onion detection breakdown.
8. Click **✓ Confirm & Submit Report**.
9. A permanent Report ID (e.g., `ONR-2026-001091`) is created and an official ReportLab PDF is generated. Click **📥 Download Certified PDF**.

### 2. Farmer Portal Workflow:
1. Log out or open an incognito window, navigate to `/login/farmer`, and sign in with `9876543210` / `farmer123`.
2. Notice the **Farmer Dashboard** displaying:
   - Total Evaluations, Grade A count, URS count, Rejected count.
   - The newly submitted report appears immediately under **My Onion Reports**.
3. Click **View Report** to inspect the detailed digital report and annotated image.
4. Click **Download PDF** to download the official agricultural quality certificate.
5. Navigate to **Market Prices** to see real-time wholesale Mandi prices across districts.

---

## 🔒 Security & Role Protection
- **Role Isolation**: Strict `@role_required("officer")` and `@role_required("farmer")` decorators prevent unauthorized cross-portal access.
- **Farmer Report Isolation**: Farmers can strictly **only** view reports associated with their own `farmer_id`. Attempting to access another farmer's report ID directly via URL returns a `403 Forbidden` response.
- **Password Security**: Passwords hashed using PBKDF2/scrypt (`werkzeug.security`).
- **File Upload Security**: Uploaded files are renamed with UUIDs and checked against an allowed extension whitelist (`jpg`, `jpeg`, `png`, `webp`).

---

## 📈 Live Mandi Market Price Integration
- Service located at `backend/services/market_price_service.py`.
- Integrates live wholesale trading rates for major onion hubs (Lasalgaon, Pimpalgaon, Pune APMC, Solapur, Ahmednagar, Azadpur Delhi, Indore, etc.).
- Includes minimum, maximum, and modal wholesale prices in ₹/Quintal, arrival tonnage, and last updated timestamps.
- Can connect directly to the Government of India Open Data / Agmarknet API by setting `MARKET_API_KEY` and `MARKET_API_URL` in `.env`.

---

## 🔄 Replacing AI Models
To replace models with updated weights:
1. Place new detector `.pt` weights in `models/` (e.g., `models/my_new_yolo.pt`).
2. Place new classifier `.keras` weights in `models/` (e.g., `models/my_new_classifier.keras`).
3. Update paths in `.env` or `config.py`:
   ```env
   DETECTION_MODEL=models/my_new_yolo.pt
   CLASSIFICATION_MODEL=models/my_new_classifier.keras
   ```
4. Restart the application. The system will load the new models on startup.
