// Onion Evaluation Workflow Engine - Multi-Image & Multi-Angle Batch Processing

let selectedFarmer = null;
let uploadedFiles = []; // Array of File objects
let currentEvaluationId = null;
let currentEvaluationData = null;
let donutChart = null;
let barChart = null;

// Human Review & AI Confidence State
const CONFIDENCE_THRESHOLD = 0.50; // 50% Threshold per specification
let activeDetectionFilter = "all";  // "all" | "low" | "high"
let detectionSortOrder = "conf_asc"; // "conf_asc" (Low to High - default) | "conf_desc" | "onion_asc" | "onion_desc"
let humanReviewState = {};          // onion_number -> { ...item, original_class, current_class, is_confirmed, is_overridden }

// Government Mandi Price Estimation Engine State
let currentPriceData = {
  mandi_name: "Lasalgaon APMC Mandi",
  modal_price: null,
  initial_modal_price: null,
  price_date: "",
  source: "data.gov.in",
  status: "unknown",
  is_live: false,
  quality_score_pct: 0,
  estimated_price_per_quintal: null,
  quantity_quintals: 0,
  total_payout: 0,
  grade_a_pct: 0,
  urs_pct: 0,
  rejected_pct: 0,
  urs_multiplier: 0.8
};

document.addEventListener("DOMContentLoaded", () => {
  initFarmerSearch();
  initDragAndDrop();
  initCameraCapture();
  initEvaluationActions();
});

// Step 1: Farmer Search & Selection (Only within Officer's My Farmers list)
function initFarmerSearch() {
  const searchInput = document.getElementById("farmerSearchInput");
  const resultsContainer = document.getElementById("farmerSearchResults");

  if (!searchInput || !resultsContainer) return;

  let debounceTimer = null;
  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const query = searchInput.value.trim();
    if (query.length < 1) {
      loadRecentFarmers();
      return;
    }
    debounceTimer = setTimeout(() => {
      fetchFarmers(query);
    }, 250);
  });

  // Check URL query parameters for pre-selected farmer_id
  const urlParams = new URLSearchParams(window.location.search);
  const preselectId = urlParams.get("farmer_id");
  if (preselectId) {
    autoPreselectFarmer(preselectId);
  } else {
    // Load initial list of officer's farmers
    loadRecentFarmers();
  }
}

async function autoPreselectFarmer(farmerId) {
  try {
    const res = await fetch(`/api/officer/farmer-lookup/${encodeURIComponent(farmerId)}`);
    const data = await res.json();
    if (res.ok && data.success && data.farmer) {
      selectFarmer(data.farmer);
      showToast(`Selected farmer: ${data.farmer.name} (${data.farmer.farmer_id})`, "success");
    } else {
      loadRecentFarmers();
    }
  } catch (err) {
    loadRecentFarmers();
  }
}

async function fetchFarmers(query = "") {
  const container = document.getElementById("farmerSearchResults");
  try {
    const res = await fetch(`/api/officer/farmers?query=${encodeURIComponent(query)}`);
    const data = await res.json();
    if (data.success && data.farmers) {
      renderFarmerList(data.farmers);
    }
  } catch (err) {
    console.error("Error fetching farmers:", err);
  }
}

function loadRecentFarmers() {
  fetchFarmers("");
}

function renderFarmerList(farmers) {
  const container = document.getElementById("farmerSearchResults");
  if (!container) return;

  if (farmers.length === 0) {
    container.innerHTML = `
      <div style="padding: 1.5rem 1rem; text-align: center; color: #b91c1c; background: #fef2f2; border-radius: var(--radius-sm); border: 1px dashed #fca5a5;">
        <div style="font-weight: 800; font-size: 0.95rem; margin-bottom: 0.35rem;">
          Farmer not found. Please ask the farmer to register through the Farmer Portal.
        </div>
        <p style="margin: 0; font-size: 0.82rem; color: #7f1d1d;">
          You can only select farmers from your <strong>My Farmers</strong> list. If the farmer is registered centrally, add them via <strong><a href="/officer/farmers" style="color: #991b1b; text-decoration: underline;">Manage Farmers</a></strong>.
        </p>
      </div>`;
    return;
  }

  container.innerHTML = farmers.map(f => `
    <div class="farmer-select-item" onclick='selectFarmer(${JSON.stringify(f)})' style="padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-color); cursor: pointer; transition: background 0.15s ease; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div style="font-weight: 700; color: var(--text-dark); font-size: 0.95rem;">${f.name}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted);">${f.farmer_id} • 📞 ${f.phone}</div>
        <div style="font-size: 0.75rem; color: var(--primary-light);">${f.village}, ${f.taluka}, ${f.district}</div>
      </div>
      <button type="button" class="btn btn-sm btn-outline">Select →</button>
    </div>
  `).join("");
}

function selectFarmer(farmer) {
  selectedFarmer = farmer;
  const card = document.getElementById("selectedFarmerCard");
  const details = document.getElementById("selectedFarmerDetails");
  const hiddenInput = document.getElementById("selectedFarmerId");

  if (card && details && hiddenInput) {
    hiddenInput.value = farmer.farmer_id;
    details.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
        <div style="flex: 1; min-width: 280px;">
          <div style="display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; margin-bottom: 0.4rem;">
            <h4 style="color: var(--primary-green); font-size: 1.15rem; margin: 0; font-weight: 800;">${farmer.name}</h4>
            <span class="badge badge-info" style="font-family: monospace; font-weight: 700; font-size: 0.85rem;">${farmer.farmer_id}</span>
            <span class="badge badge-success" style="font-size: 0.75rem;">✓ Registered Farmer</span>
          </div>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.4rem 1.25rem; font-size: 0.85rem; color: var(--text-dark); margin-top: 0.4rem;">
            <div><b>📞 Mobile:</b> ${farmer.phone || "N/A"}</div>
            ${farmer.email ? `<div><b>✉️ Email:</b> ${farmer.email}</div>` : ""}
            <div><b>📍 Village:</b> ${farmer.village || "--"}</div>
            <div><b>Taluka:</b> ${farmer.taluka || "--"}</div>
            <div><b>District:</b> ${farmer.district || "--"}</div>
            <div><b>State:</b> ${farmer.state || "Maharashtra"}</div>
          </div>
          <div style="margin-top: 0.6rem; font-size: 0.78rem; color: #166534; background: rgba(34, 197, 94, 0.12); padding: 0.3rem 0.65rem; border-radius: 4px; display: inline-block;">
            ✓ Farmer profile loaded from registry. Ready for onion image evaluation & procurement batch.
          </div>
        </div>
        <button type="button" class="btn btn-sm btn-secondary" onclick="clearSelectedFarmer()">Change Farmer</button>
      </div>
    `;
    card.style.display = "block";
    document.getElementById("farmerSearchSection").style.display = "none";
    document.getElementById("step1Indicator").classList.add("completed");
    document.getElementById("step2Indicator").classList.add("active");
    
    // Scroll smoothly to image upload section
    document.getElementById("imageUploadSection").scrollIntoView({ behavior: "smooth" });
  }
}

function clearSelectedFarmer() {
  selectedFarmer = null;
  const hiddenInput = document.getElementById("selectedFarmerId");
  if (hiddenInput) hiddenInput.value = "";
  document.getElementById("selectedFarmerCard").style.display = "none";
  document.getElementById("farmerSearchSection").style.display = "block";
  document.getElementById("step1Indicator").classList.remove("completed");
  document.getElementById("step1Indicator").classList.add("active");
  document.getElementById("step2Indicator").classList.remove("active");
}

// Step 2: Multi-Image Drag and drop & selection
function initDragAndDrop() {
  const dropzone = document.getElementById("uploadDropzone");
  const fileInput = document.getElementById("onionImageInput");

  if (!dropzone || !fileInput) return;

  ["dragenter", "dragover"].forEach(event => {
    dropzone.addEventListener(event, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(event => {
    dropzone.addEventListener(event, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesSelection(e.dataTransfer.files);
    }
  });

  dropzone.addEventListener("click", (e) => {
    // Only trigger if click was directly on dropzone or prompt, not on gallery buttons
    if (!e.target.closest("#uploadGalleryContainer")) {
      fileInput.click();
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFilesSelection(e.target.files);
      // Reset input value so re-selecting same file triggers change event
      fileInput.value = "";
    }
  });
}

function triggerAddMoreImages(event) {
  if (event) event.stopPropagation();
  const fileInput = document.getElementById("onionImageInput");
  if (fileInput) fileInput.click();
}

function handleFilesSelection(fileList) {
  const validExtensions = ["image/jpeg", "image/png", "image/webp", "image/jpg"];
  let addedCount = 0;

  Array.from(fileList).forEach(file => {
    const isValidType = validExtensions.includes(file.type) || file.name.match(/\.(jpg|jpeg|png|webp)$/i);
    if (!isValidType) {
      showToast(`Skipped '${file.name}': Unsupported format.`, "warning");
      return;
    }
    // Prevent exact duplicates by name and size
    const isDuplicate = uploadedFiles.some(f => f.name === file.name && f.size === file.size);
    if (!isDuplicate) {
      uploadedFiles.push(file);
      addedCount++;
    }
  });

  if (addedCount > 0) {
    dismissQualityAlert();
    showToast(`Added ${addedCount} photo(s). Total: ${uploadedFiles.length}`, "success");
    renderUploadedGallery();
  }
}

function renderUploadedGallery() {
  const galleryContainer = document.getElementById("uploadGalleryContainer");
  const grid = document.getElementById("imagesPreviewGrid");
  const prompt = document.getElementById("dropzonePrompt");
  const badge = document.getElementById("imageCountBadge");
  const ctaArea = document.getElementById("analyzeButtonArea");

  if (!galleryContainer || !grid) return;

  if (uploadedFiles.length === 0) {
    galleryContainer.style.display = "none";
    if (prompt) prompt.style.display = "block";
    if (ctaArea) ctaArea.style.display = "none";
    return;
  }

  if (prompt) prompt.style.display = "none";
  galleryContainer.style.display = "block";
  if (ctaArea) ctaArea.style.display = "block";

  if (badge) {
    badge.textContent = `${uploadedFiles.length} Image${uploadedFiles.length > 1 ? "s" : ""}`;
  }

  // Render cards
  grid.innerHTML = "";
  uploadedFiles.forEach((file, index) => {
    const card = document.createElement("div");
    card.className = "image-preview-card";

    const objectUrl = URL.createObjectURL(file);
    const sizeKb = Math.round(file.size / 1024);
    const sizeStr = sizeKb > 1024 ? `${(sizeKb / 1024).toFixed(1)} MB` : `${sizeKb} KB`;

    card.innerHTML = `
      <span class="image-preview-badge">Angle #${index + 1}</span>
      <button type="button" class="image-preview-remove" title="Remove this photo" onclick="removeUploadedFile(${index}, event)">✕</button>
      <img src="${objectUrl}" class="image-preview-thumb" alt="Angle ${index + 1}" onload="URL.revokeObjectURL(this.src)">
      <div class="image-preview-card-info">
        <span style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 110px;" title="${file.name}">
          ${file.name}
        </span>
        <span style="color: var(--text-muted); font-size: 0.7rem;">${sizeStr}</span>
      </div>
    `;
    grid.appendChild(card);
  });
}

function removeUploadedFile(index, event) {
  if (event) event.stopPropagation();
  if (index >= 0 && index < uploadedFiles.length) {
    const removedName = uploadedFiles[index].name;
    uploadedFiles.splice(index, 1);
    renderUploadedGallery();
    showToast(`Removed '${removedName}'.`, "info");
  }
}

function clearAllSelectedImages(event) {
  if (event) event.stopPropagation();
  uploadedFiles = [];
  const fileInput = document.getElementById("onionImageInput");
  if (fileInput) fileInput.value = "";
  renderUploadedGallery();
  showToast("All selected images cleared.", "info");
}

// Quick Sample Image Pickers
async function loadSampleImage(filename) {
  try {
    const res = await fetch(`/static/samples/${filename}`);
    const blob = await res.blob();
    const file = new File([blob], filename, { type: blob.type || "image/jpeg" });
    handleFilesSelection([file]);
  } catch (err) {
    showToast("Failed to load sample image: " + err.message, "error");
  }
}

async function loadAllSampleImages() {
  const sampleNames = ["onion1.jpg", "onion2.jpg", "onion3.jpg", "onion4.webp", "onion5.jpg"];
  showToast("Loading 5 multi-angle sample photos...", "info");
  try {
    const files = await Promise.all(
      sampleNames.map(async name => {
        const res = await fetch(`/static/samples/${name}`);
        const blob = await res.blob();
        return new File([blob], name, { type: blob.type || "image/jpeg" });
      })
    );
    handleFilesSelection(files);
  } catch (err) {
    showToast("Failed to load sample images: " + err.message, "error");
  }
}

// Step 3: Run AI Evaluation with animated progress
async function startEvaluation() {
  if (!selectedFarmer) {
    showToast("Please select a farmer first.", "warning");
    document.getElementById("farmerSearchSection").scrollIntoView({ behavior: "smooth" });
    return;
  }

  if (uploadedFiles.length === 0) {
    showToast("Please upload at least one onion photograph.", "warning");
    return;
  }

  // Open animated progress modal
  const modal = document.getElementById("aiProgressModal");
  const stepText = document.getElementById("aiProgressStepText");
  const fill = document.getElementById("aiProgressBarFill");
  modal.style.display = "flex";

  const numImages = uploadedFiles.length;
  stepText.textContent = `Uploading ${numImages} onion photo${numImages > 1 ? "s" : ""}...`;
  fill.style.width = "20%";

  const formData = new FormData();
  formData.append("farmer_id", selectedFarmer.farmer_id);
  uploadedFiles.forEach(file => {
    formData.append("images", file);
  });

  const progressInterval = setInterval(() => {
    const curW = parseInt(fill.style.width) || 20;
    if (curW < 45) {
      fill.style.width = "45%";
      stepText.textContent = `Running YOLO11 detection across ${numImages} angle${numImages > 1 ? "s" : ""}...`;
    } else if (curW < 75) {
      fill.style.width = "75%";
      stepText.textContent = "Classifying bulb quality (Healthy, Damaged, Rotten, Sprouted)...";
    } else if (curW < 90) {
      fill.style.width = "90%";
      stepText.textContent = "Consolidating batch procurement grading...";
    }
  }, 700);

  try {
    const response = await fetch("/api/officer/evaluate", {
      method: "POST",
      body: formData
    });

    clearInterval(progressInterval);
    const data = await response.json();

    if (!response.ok || !data.success) {
      modal.style.display = "none";
      const errCode = data.code || "";
      const errMsg = data.error || "AI evaluation could not be completed. Please try again.";

      if (errCode === "IMAGE_TOO_BLURRY") {
        showQualityAlert("⚠️ Image Too Blurry Alert", "Image is too blurry. Please upload a clear image for accurate evaluation.");
        showToast("⚠️ Image is too blurry. Please upload a clear image for accurate evaluation.", "error");
      } else if (errCode === "NO_ONIONS_DETECTED") {
        showQualityAlert("🔍 No Onions Detected", "No onions were detected in the uploaded photo. Please upload an image with clearly visible onions.");
        showToast("🔍 No Onions Detected. Please upload an image containing onions.", "error");
      } else if (errCode === "IMAGE_TOO_DARK" || errCode === "IMAGE_OVEREXPOSED") {
        showQualityAlert("💡 Lighting Condition Issue", errMsg);
        showToast("💡 " + errMsg, "error");
      } else {
        showToast(errMsg, "error");
      }
      return;
    }

    fill.style.width = "100%";
    stepText.textContent = "Batch Evaluation complete ✓";

    setTimeout(() => {
      modal.style.display = "none";
      displayAIResults(data);
    }, 600);

  } catch (err) {
    clearInterval(progressInterval);
    modal.style.display = "none";
    showToast("Server connection error during evaluation: " + err.message, "error");
  }
}

// Step 4: Display AI Review Screen
function displayAIResults(data) {
  currentEvaluationId = data.evaluation_id;
  currentEvaluationData = data;
  const res = data.results;

  document.getElementById("evaluationWizard").style.display = "none";
  const reviewSection = document.getElementById("evaluationReviewSection");
  reviewSection.style.display = "block";
  reviewSection.scrollIntoView({ behavior: "smooth" });

  // Update indicators
  document.getElementById("step2Indicator").classList.add("completed");
  document.getElementById("step3Indicator").classList.add("active");

  // Overlapping Onions Advisory Banner
  const advisoryBanner = document.getElementById("resOverlappingAdvisoryBanner");
  if (advisoryBanner) {
    if (res.is_overlapping || res.advisory_notes) {
      advisoryBanner.style.display = "block";
    } else {
      advisoryBanner.style.display = "none";
    }
  }

  // Multi-Image Header Badge
  const totalImgs = res.total_images || 1;
  const totalImgsBadge = document.getElementById("resTotalImagesBadge");
  if (totalImgsBadge) {
    totalImgsBadge.textContent = `${totalImgs} Angle${totalImgs > 1 ? "s" : ""} / Image${totalImgs > 1 ? "s" : ""} Evaluated`;
  }
  const totalSub = document.getElementById("resTotalOnionsSub");
  if (totalSub) {
    totalSub.textContent = `Across all ${totalImgs} uploaded photo${totalImgs > 1 ? "s" : ""}`;
  }

  // Summary counts
  document.getElementById("resTotalOnions").textContent = res.total_onions;
  document.getElementById("resGradeA").textContent = res.grades["Grade A"].count;
  document.getElementById("resGradeAPct").textContent = res.grades["Grade A"].percentage + "%";
  document.getElementById("resURS").textContent = res.grades["URS"].count;
  document.getElementById("resURSPct").textContent = res.grades["URS"].percentage + "%";
  document.getElementById("resRejected").textContent = res.grades["Rejected"].count;
  document.getElementById("resRejectedPct").textContent = res.grades["Rejected"].percentage + "%";

  // Quality details
  document.getElementById("resHealthyCount").textContent = `${res.classes.Healthy.count} (${res.classes.Healthy.percentage}%)`;
  document.getElementById("resDamagedCount").textContent = `${res.classes.Damaged.count} (${res.classes.Damaged.percentage}%)`;
  document.getElementById("resRottenCount").textContent = `${res.classes.Rotten.count} (${res.classes.Rotten.percentage}%)`;
  document.getElementById("resSproutedCount").textContent = `${res.classes.Sprouted.count} (${res.classes.Sprouted.percentage}%)`;

  // Quality Summary Text
  document.getElementById("resQualitySummaryText").textContent = res.quality_summary;

  // Farmer Badge
  document.getElementById("resFarmerName").textContent = data.farmer.name;
  document.getElementById("resFarmerId").textContent = data.farmer.farmer_id;
  document.getElementById("resFarmerLocation").textContent = `${data.farmer.village}, ${data.farmer.taluka}, ${data.farmer.district}`;

  // Multi-Angle Image Selector Tabs
  setupMultiAngleTabs(res);

  // Initialize Government Mandi Price Estimation Engine
  initPriceEngineUI(data);

  // Charts
  if (donutChart) donutChart.destroy();
  if (barChart) barChart.destroy();

  donutChart = createQualityDonutChart(
    "reviewQualityDonutChart",
    res.classes.Healthy.count,
    res.classes.Damaged.count,
    res.classes.Rotten.count,
    res.classes.Sprouted.count
  );

  barChart = createGradeBarChart(
    "reviewGradeBarChart",
    res.grades["Grade A"].count,
    res.grades["URS"].count,
    res.grades["Rejected"].count
  );

  // Initialize and Render Human Review Table with AI Confidence & Override controls
  initHumanReviewState(res.detections || []);
  renderHumanReviewTable();
}

function setupMultiAngleTabs(res) {
  const tabsBar = document.getElementById("angleTabsBar");
  const headerLabel = document.getElementById("currentAngleHeaderLabel");
  const mainImage = document.getElementById("resAnnotatedImage");

  if (!tabsBar || !mainImage) return;

  const images = res.images || [];

  if (images.length > 1) {
    tabsBar.style.display = "flex";
    tabsBar.innerHTML = "";

    // Button 1: Consolidated Collage Overview
    const collageBtn = document.createElement("button");
    collageBtn.type = "button";
    collageBtn.className = "angle-tab-btn active";
    collageBtn.innerHTML = `🖼️ Overview Collage (${images.length} Angles)`;
    collageBtn.onclick = () => {
      tabsBar.querySelectorAll(".angle-tab-btn").forEach(b => b.classList.remove("active"));
      collageBtn.classList.add("active");
      mainImage.src = res.annotated_image_url;
      if (headerLabel) headerLabel.textContent = `Multi-Angle Grid Overview (${images.length} Angles)`;
    };
    tabsBar.appendChild(collageBtn);

    // Buttons for each individual image
    images.forEach(img => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "angle-tab-btn";
      btn.innerHTML = `Angle #${img.image_order} (${img.total_onions} bulbs)`;
      btn.onclick = () => {
        tabsBar.querySelectorAll(".angle-tab-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        mainImage.src = img.annotated_url;
        if (headerLabel) {
          headerLabel.textContent = `Angle #${img.image_order} - ${img.original_filename} (${img.total_onions} detected)`;
        }
      };
      tabsBar.appendChild(btn);
    });

    mainImage.src = res.annotated_image_url;
    if (headerLabel) headerLabel.textContent = `Multi-Angle Grid Overview (${images.length} Angles)`;

  } else {
    tabsBar.style.display = "none";
    mainImage.src = res.annotated_image_url;
    if (headerLabel) headerLabel.textContent = "Annotated Detection View";
  }
}

// Language Selection State
let selectedReportLanguage = "en";

function onReportLanguageChange(lang) {
  selectedReportLanguage = lang || "en";
  ["en", "hi", "mr"].forEach(l => {
    const card = document.getElementById("langCard" + l.charAt(0).toUpperCase() + l.slice(1));
    if (card) {
      if (l === selectedReportLanguage) {
        card.style.borderColor = "#10b981";
        card.style.background = "#f0fdf4";
        const titleEl = card.querySelector("div > div:first-child");
        if (titleEl) titleEl.style.color = "#065f46";
      } else {
        card.style.borderColor = "#cbd5e1";
        card.style.background = "#ffffff";
        const titleEl = card.querySelector("div > div:first-child");
        if (titleEl) titleEl.style.color = "#1e293b";
      }
    }
  });
}

// Step 5: Officer Confirms Evaluation
async function confirmAndSubmitReport() {
  if (!currentEvaluationId) {
    showToast("No active evaluation to confirm.", "error");
    return;
  }

  const confirmBtn = document.getElementById("confirmReportBtn");
  confirmBtn.disabled = true;
  confirmBtn.innerHTML = `<span>Generating Official ReportLab PDF...</span>`;

  try {
    const langRadio = document.querySelector('input[name="reportLanguage"]:checked');
    const chosenLang = langRadio ? langRadio.value : (selectedReportLanguage || "en");

    const payload = {
      quantity_quintals: currentPriceData.quantity_quintals || 0,
      mandi_modal_price: currentPriceData.modal_price,
      estimated_price_per_quintal: currentPriceData.estimated_price_per_quintal,
      quality_score: currentPriceData.quality_score_pct,
      total_payout: currentPriceData.total_payout,
      mandi_name: currentPriceData.mandi_name,
      mandi_price_date: currentPriceData.price_date,
      mandi_api_source: currentPriceData.source,
      urs_multiplier: currentPriceData.urs_multiplier !== undefined ? currentPriceData.urs_multiplier : 0.8,
      language: chosenLang,
      item_overrides: getItemOverridesList()
    };

    const res = await fetch(`/api/officer/evaluate/${currentEvaluationId}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (!res.ok || !data.success) {
      showToast(data.error || "Failed to confirm report.", "error");
      confirmBtn.disabled = false;
      confirmBtn.innerHTML = "✓ Confirm & Submit Report";
      return;
    }

    // Success! Show confirmation modal with language information
    document.getElementById("confirmedReportId").textContent = data.report_id;
    const finalLang = data.language || chosenLang;
    const langLabels = {
      en: "🇬🇧 English",
      hi: "🇮🇳 हिंदी (Hindi)",
      mr: "🚩 मराठी (Marathi)"
    };
    const langBadgeEl = document.getElementById("confirmedReportLangBadge");
    if (langBadgeEl) langBadgeEl.textContent = langLabels[finalLang] || finalLang.toUpperCase();
    const langNameEl = document.getElementById("confirmedReportLangName");
    if (langNameEl) langNameEl.textContent = langLabels[finalLang] || finalLang;

    const filename = `Onion_Report_${data.report_id}.pdf`;
    const downloadUrl = `/reports/download/${filename}?lang=${encodeURIComponent(finalLang)}`;

    const downloadBtn = document.getElementById("pdfDownloadLink");
    if (downloadBtn) {
      downloadBtn.href = downloadUrl;
      downloadBtn.setAttribute("download", filename);
      downloadBtn.target = "_blank";
      downloadBtn.onclick = null;
    }
    
    const viewBtn = document.getElementById("pdfViewLink");
    if (viewBtn) {
      viewBtn.href = `${downloadUrl}&inline=1`;
      viewBtn.target = "_blank";
      viewBtn.onclick = null;
    }

    document.getElementById("reportSuccessModal").style.display = "flex";

  } catch (err) {
    showToast("Error confirming evaluation: " + err.message, "error");
    confirmBtn.disabled = false;
    confirmBtn.innerHTML = "✓ Confirm & Submit Report";
  }
}

function resetEvaluation() {
  currentEvaluationId = null;
  currentEvaluationData = null;
  clearAllSelectedImages();
  document.getElementById("evaluationReviewSection").style.display = "none";
  document.getElementById("evaluationWizard").style.display = "block";
  document.getElementById("step3Indicator").classList.remove("active");
  document.getElementById("step2Indicator").classList.add("active");
  document.getElementById("evaluationWizard").scrollIntoView({ behavior: "smooth" });
}

// =========================================================
// PRICE ESTIMATION & FARMER PAYOUT ENGINE (Lasalgaon Mandi)
// =========================================================

function initPriceEngineUI(data) {
  const pe = data.price_estimation || {};
  const mandiInfo = pe.mandi_info || {};
  const grades = data.results.grades || {};

  currentPriceData.grade_a_pct = parseFloat(grades["Grade A"]?.percentage || 0);
  currentPriceData.urs_pct = parseFloat(grades["URS"]?.percentage || 0);
  currentPriceData.rejected_pct = parseFloat(grades["Rejected"]?.percentage || 0);

  currentPriceData.mandi_name = mandiInfo.market_name || "Lasalgaon APMC Mandi";
  currentPriceData.modal_price = (pe.modal_price !== null && pe.modal_price !== undefined) ? parseFloat(pe.modal_price) : null;
  currentPriceData.initial_modal_price = currentPriceData.modal_price;
  currentPriceData.price_date = mandiInfo.price_date || new Date().toLocaleDateString("en-GB");
  currentPriceData.source = mandiInfo.source || "data.gov.in";
  currentPriceData.status = mandiInfo.status || "unknown";
  currentPriceData.is_live = Boolean(mandiInfo.is_live);
  currentPriceData.quantity_quintals = 0;
  if (pe.factors && pe.factors.urs !== undefined) {
    currentPriceData.urs_multiplier = parseFloat(pe.factors.urs);
  } else {
    currentPriceData.urs_multiplier = 0.8;
  }

  const inputUrs = document.getElementById("inputUrsMultiplier");
  if (inputUrs) {
    inputUrs.value = currentPriceData.urs_multiplier;
  }

  // Header & Status Badges
  const mandiNameEl = document.getElementById("priceEngineMandiName");
  if (mandiNameEl) mandiNameEl.textContent = currentPriceData.mandi_name;

  const apiBadge = document.getElementById("priceEngineApiBadge");
  if (apiBadge) {
    if (currentPriceData.is_live) {
      apiBadge.className = "badge badge-success";
      apiBadge.textContent = "● Live data.gov.in";
    } else if (currentPriceData.status === "cached") {
      apiBadge.className = "badge badge-info";
      apiBadge.textContent = "● Recorded Mandi Benchmark";
    } else {
      apiBadge.className = "badge badge-warning";
      apiBadge.textContent = "● Mandi API Offline";
    }
  }

  const dateBadge = document.getElementById("priceEngineDateBadge");
  if (dateBadge) {
    dateBadge.textContent = `Date: ${currentPriceData.price_date}`;
  }

  const mandiLoc = document.getElementById("displayMandiLocation");
  if (mandiLoc) {
    mandiLoc.textContent = `${currentPriceData.mandi_name} (${mandiInfo.district || "Nashik"}, ${mandiInfo.state || "Maharashtra"})`;
  }

  const apiSourceEl = document.getElementById("displayApiSource");
  if (apiSourceEl) {
    apiSourceEl.textContent = currentPriceData.source;
  }

  // Price input override field
  const modalInput = document.getElementById("inputModalPriceOverride");
  if (modalInput && currentPriceData.modal_price) {
    modalInput.value = currentPriceData.modal_price;
  }

  // Quantity input field
  const qtyInput = document.getElementById("inputQuantityQuintals");
  if (qtyInput) {
    qtyInput.value = "";
  }

  recalculatePriceEngine();
}

function recalculatePriceEngine() {
  const ga = currentPriceData.grade_a_pct;
  const urs = currentPriceData.urs_pct;
  const rej = currentPriceData.rejected_pct;
  const ursMult = (currentPriceData.urs_multiplier !== undefined && !isNaN(currentPriceData.urs_multiplier))
                  ? currentPriceData.urs_multiplier
                  : 0.8;

  // Quality Score = (Grade A% × 1.0) + (URS% × urs_multiplier) + (Rejected% × 0)
  const qualityScore = Math.round(((ga * 1.0) + (urs * ursMult) + (rej * 0.0)) * 100) / 100;
  currentPriceData.quality_score_pct = qualityScore;

  // Modal Price
  const modal = currentPriceData.modal_price;

  // Estimated Quality-Adjusted Price = Modal Price × Quality Score
  let estimatedPrice = null;
  if (modal !== null && !isNaN(modal) && modal > 0) {
    estimatedPrice = Math.round((modal * (qualityScore / 100)) * 100) / 100;
  }
  currentPriceData.estimated_price_per_quintal = estimatedPrice;

  // Quantity and Final Payout
  const qty = currentPriceData.quantity_quintals || 0;
  let finalPayout = 0;
  if (estimatedPrice !== null && qty > 0) {
    finalPayout = Math.round((qty * estimatedPrice) * 100) / 100;
  }
  currentPriceData.total_payout = finalPayout;

  // Update DOM Displays
  updatePriceEngineDOM(qualityScore, estimatedPrice, finalPayout);
}

function updatePriceEngineDOM(qualityScore, estimatedPrice, finalPayout) {
  const ursMult = (currentPriceData.urs_multiplier !== undefined && !isNaN(currentPriceData.urs_multiplier))
                  ? currentPriceData.urs_multiplier
                  : 0.8;

  // Modal Price
  const modalDisplay = document.getElementById("displayModalPrice");
  if (modalDisplay) {
    modalDisplay.textContent = currentPriceData.modal_price ? `₹${currentPriceData.modal_price.toLocaleString("en-IN")}` : "₹--";
  }

  // Grade Percentages
  const gaEl = document.getElementById("factorGradeAPct");
  if (gaEl) gaEl.textContent = `${currentPriceData.grade_a_pct.toFixed(1)}%`;

  const ursEl = document.getElementById("factorURSPct");
  if (ursEl) ursEl.textContent = `${currentPriceData.urs_pct.toFixed(1)}%`;

  const ursPctHeader = document.getElementById("displayUrsMultiplierPct");
  if (ursPctHeader) {
    ursPctHeader.textContent = `${Math.round(ursMult * 100)}`;
  }

  const rejEl = document.getElementById("factorRejectedPct");
  if (rejEl) rejEl.textContent = `${currentPriceData.rejected_pct.toFixed(1)}%`;

  // Formula Breakdown Text
  const formulaHeading = document.getElementById("formulaHeadingText");
  if (formulaHeading) {
    formulaHeading.textContent = `Quality Score = (Grade A% × 1.0) + (URS% × ${ursMult}) + (Rejected% × 0)`;
  }

  const formulaText = document.getElementById("formulaCalculationText");
  if (formulaText) {
    const gaPart = (currentPriceData.grade_a_pct * 1.0).toFixed(1);
    const ursPart = (currentPriceData.urs_pct * ursMult).toFixed(1);
    formulaText.textContent = `(${currentPriceData.grade_a_pct.toFixed(1)}% × 1.0) + (${currentPriceData.urs_pct.toFixed(1)}% × ${ursMult}) + (${currentPriceData.rejected_pct.toFixed(1)}% × 0) = ${gaPart} + ${ursPart} + 0 = ${qualityScore.toFixed(1)}%`;
  }

  // Quality Score & Estimated Price
  const qsDisplay = document.getElementById("displayQualityScore");
  if (qsDisplay) qsDisplay.textContent = `${qualityScore.toFixed(1)}%`;

  const epDisplay = document.getElementById("displayEstimatedPrice");
  if (epDisplay) {
    epDisplay.textContent = estimatedPrice !== null ? `₹${estimatedPrice.toLocaleString("en-IN")} /q` : "Pending Rate";
  }

  // Quantity and Payout
  const qty = currentPriceData.quantity_quintals || 0;
  const kgDisplay = document.getElementById("quantityKgDisplay");
  if (kgDisplay) {
    kgDisplay.textContent = `${(qty * 100).toLocaleString("en-IN")} kg`;
  }

  const finalPayoutEl = document.getElementById("displayFinalPayout");
  if (finalPayoutEl) {
    finalPayoutEl.textContent = `₹${finalPayout.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  const calcQtyEl = document.getElementById("payoutCalcQty");
  if (calcQtyEl) calcQtyEl.textContent = `${qty.toFixed(2)} q`;

  const calcRateEl = document.getElementById("payoutCalcRate");
  if (calcRateEl) {
    calcRateEl.textContent = estimatedPrice !== null ? `₹${estimatedPrice.toLocaleString("en-IN")}/q` : "₹0/q";
  }
}

function onQuantityChange() {
  const input = document.getElementById("inputQuantityQuintals");
  if (!input) return;
  const val = parseFloat(input.value);
  currentPriceData.quantity_quintals = (!isNaN(val) && val >= 0) ? val : 0;
  recalculatePriceEngine();
}

function onUrsMultiplierChange() {
  const input = document.getElementById("inputUrsMultiplier");
  if (!input) return;
  let val = parseFloat(input.value);
  if (isNaN(val) || val < 0) {
    val = 0;
  }
  currentPriceData.urs_multiplier = val;
  recalculatePriceEngine();
}

function onModalPriceChange() {
  const input = document.getElementById("inputModalPriceOverride");
  if (!input) return;
  const val = parseFloat(input.value);
  if (!isNaN(val) && val > 0) {
    currentPriceData.modal_price = val;
    recalculatePriceEngine();
  }
}

function setQuantityPreset(qty) {
  const input = document.getElementById("inputQuantityQuintals");
  if (input) {
    input.value = qty;
    onQuantityChange();
  }
}

function resetModalPriceToLive() {
  if (currentPriceData.initial_modal_price) {
    currentPriceData.modal_price = currentPriceData.initial_modal_price;
    const input = document.getElementById("inputModalPriceOverride");
    if (input) input.value = currentPriceData.initial_modal_price;
    recalculatePriceEngine();
  }
}

// =========================================================
// FARMER ID LOOKUP & AUTO-POPULATION
// =========================================================
let lookedUpFarmerData = null;

function openFarmerIdLookupModal() {
  const modal = document.getElementById("lookupFarmerModal");
  if (!modal) return;
  modal.style.display = "flex";
  document.getElementById("lookupFarmerIdInput").value = "";
  document.getElementById("lookupFarmerAlert").style.display = "none";
  document.getElementById("lookupFarmerPreview").style.display = "none";
  document.getElementById("confirmSelectFarmerBtn").style.display = "none";
  lookedUpFarmerData = null;
  setTimeout(() => {
    document.getElementById("lookupFarmerIdInput").focus();
  }, 100);
}

function closeFarmerIdLookupModal() {
  const modal = document.getElementById("lookupFarmerModal");
  if (modal) modal.style.display = "none";
  lookedUpFarmerData = null;
}

function handleLookupKey(event) {
  if (event.key === "Enter") {
    executeFarmerLookup();
  }
}

async function executeFarmerLookup() {
  const idInput = document.getElementById("lookupFarmerIdInput");
  const alertBox = document.getElementById("lookupFarmerAlert");
  const previewBox = document.getElementById("lookupFarmerPreview");
  const confirmBtn = document.getElementById("confirmSelectFarmerBtn");
  const fetchBtn = document.getElementById("lookupFarmerBtn");

  const query = idInput.value.trim();
  if (!query) {
    alertBox.textContent = "Please enter a Farmer ID (e.g. FMR-2026-0001).";
    alertBox.style.background = "#fee2e2";
    alertBox.style.color = "#b91c1c";
    alertBox.style.display = "block";
    return;
  }

  alertBox.style.display = "none";
  fetchBtn.disabled = true;
  fetchBtn.textContent = "Fetching...";

  try {
    const res = await fetch(`/api/officer/farmer-lookup/${encodeURIComponent(query)}`);
    const data = await res.json();

    if (res.ok && data.success && data.farmer) {
      lookedUpFarmerData = data.farmer;

      // Populate Preview
      document.getElementById("previewFarmerName").textContent = data.farmer.name || "--";
      document.getElementById("previewFarmerId").textContent = data.farmer.farmer_id || query;
      document.getElementById("previewFarmerPhone").textContent = data.farmer.phone || "--";
      document.getElementById("previewFarmerEmail").textContent = data.farmer.email || "None";
      document.getElementById("previewFarmerVillage").textContent = data.farmer.village || "--";
      document.getElementById("previewFarmerTaluka").textContent = data.farmer.taluka || "--";
      document.getElementById("previewFarmerDistrict").textContent = data.farmer.district || "--";
      document.getElementById("previewFarmerState").textContent = data.farmer.state || "Maharashtra";

      previewBox.style.display = "block";
      confirmBtn.style.display = "inline-flex";

      alertBox.textContent = `✓ Registered farmer record found in My Farmers: ${data.farmer.name}`;
      alertBox.style.background = "#dcfce7";
      alertBox.style.color = "#166534";
      alertBox.style.display = "block";
    } else {
      lookedUpFarmerData = null;
      previewBox.style.display = "none";
      confirmBtn.style.display = "none";
      const errMsg = (data && data.error) ? data.error : "Farmer not found. Please ask the farmer to register through the Farmer Portal.";
      alertBox.innerHTML = `<strong>${errMsg}</strong>` +
        (data && data.tip ? `<div style="margin-top: 0.35rem; font-size: 0.8rem; font-weight: normal;">${data.tip}</div>` : "");
      alertBox.style.background = "#fee2e2";
      alertBox.style.color = "#b91c1c";
      alertBox.style.display = "block";
    }
  } catch (err) {
    lookedUpFarmerData = null;
    previewBox.style.display = "none";
    confirmBtn.style.display = "none";
    alertBox.textContent = "Farmer not found. Please ask the farmer to register through the Farmer Portal.";
    alertBox.style.background = "#fee2e2";
    alertBox.style.color = "#b91c1c";
    alertBox.style.display = "block";
  } finally {
    fetchBtn.disabled = false;
    fetchBtn.textContent = "Fetch Details";
  }
}

function confirmFarmerLookupSelection() {
  if (!lookedUpFarmerData) return;
  selectFarmer(lookedUpFarmerData);
  closeFarmerIdLookupModal();
  showToast(`Farmer ${lookedUpFarmerData.name} (${lookedUpFarmerData.farmer_id}) selected.`, "success");
}

function initEvaluationActions() {
  // Empty stub for action event listeners
}

// =========================================================
// LIVE CAMERA CAPTURE ENGINE
// =========================================================
let cameraStream = null;
let cameraFacingMode = "environment"; // Prefer rear camera on mobile devices

function initCameraCapture() {
  const mobileInput = document.getElementById("mobileCameraInput");
  if (mobileInput) {
    mobileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFilesSelection(e.target.files);
        mobileInput.value = "";
      }
    });
  }
}

async function openLiveCameraModal(event) {
  if (event) event.stopPropagation();

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    // WebRTC getUserMedia not supported in this environment; fallback to native file input
    showToast("Opening native camera capture...", "info");
    const mobileInput = document.getElementById("mobileCameraInput");
    if (mobileInput) mobileInput.click();
    return;
  }

  const modal = document.getElementById("liveCameraModal");
  if (!modal) return;

  modal.style.display = "flex";

  const strip = document.getElementById("cameraCapturedStrip");
  if (strip) {
    strip.innerHTML = "";
    strip.style.display = "none";
  }

  const countSpan = document.getElementById("modalCapturedCount");
  if (countSpan) countSpan.textContent = uploadedFiles.length;

  await startCameraStream();
}

async function startCameraStream() {
  stopCameraStream();

  const video = document.getElementById("cameraVideo");
  if (!video) return;

  const constraints = {
    video: {
      facingMode: { ideal: cameraFacingMode },
      width: { ideal: 1920 },
      height: { ideal: 1080 }
    },
    audio: false
  };

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = cameraStream;
    await video.play();
  } catch (err) {
    console.warn("Camera with high constraints failed, falling back to simple video:", err);
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      video.srcObject = cameraStream;
      await video.play();
    } catch (fallbackErr) {
      console.error("Camera access failed completely:", fallbackErr);
      if (fallbackErr.name === "NotAllowedError" || fallbackErr.name === "PermissionDeniedError") {
        showToast("Camera access was denied. Please allow camera permissions in browser settings.", "error");
      } else if (fallbackErr.name === "NotFoundError" || fallbackErr.name === "DevicesNotFoundError") {
        showToast("No camera detected on this system. You can upload photos instead.", "warning");
      } else {
        showToast("Unable to start live camera: " + fallbackErr.message, "error");
      }
      closeLiveCameraModal();
      // Offer native picker as alternative
      const mobileInput = document.getElementById("mobileCameraInput");
      if (mobileInput) mobileInput.click();
    }
  }
}

function stopCameraStream() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => {
      try {
        track.stop();
      } catch (e) {
        console.warn("Track stop error:", e);
      }
    });
    cameraStream = null;
  }
  const video = document.getElementById("cameraVideo");
  if (video) {
    video.srcObject = null;
  }
}

function closeLiveCameraModal() {
  stopCameraStream();
  const modal = document.getElementById("liveCameraModal");
  if (modal) modal.style.display = "none";
}

function toggleCameraFacingMode() {
  cameraFacingMode = (cameraFacingMode === "environment" ? "user" : "environment");
  showToast(`Switching camera (${cameraFacingMode === "environment" ? "Rear / Back" : "Front"})...`, "info");
  startCameraStream();
}

function capturePhotoFromCamera() {
  const video = document.getElementById("cameraVideo");
  const canvas = document.getElementById("cameraCanvas");
  const flash = document.getElementById("cameraFlash");

  if (!video || !canvas) return;

  if (video.videoWidth === 0 || video.videoHeight === 0) {
    showToast("Camera feed is warming up, please wait a second...", "warning");
    return;
  }

  // Set canvas matching video source frame size
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  // Trigger shutter flash visual effect
  if (flash) {
    flash.style.opacity = "0.85";
    setTimeout(() => { flash.style.opacity = "0"; }, 100);
  }

  // Convert frame to standard JPEG file
  canvas.toBlob((blob) => {
    if (!blob) {
      showToast("Failed to capture image frame.", "error");
      return;
    }

    const angleNumber = uploadedFiles.length + 1;
    const filename = `camera_angle_${angleNumber}_${Date.now()}.jpg`;
    const capturedFile = new File([blob], filename, { type: "image/jpeg" });

    uploadedFiles.push(capturedFile);
    renderUploadedGallery();
    updateCameraModalStrip(capturedFile);

    showToast(`✓ Snapped Angle #${angleNumber} successfully!`, "success");
  }, "image/jpeg", 0.92);
}

function updateCameraModalStrip(file) {
  const strip = document.getElementById("cameraCapturedStrip");
  const countSpan = document.getElementById("modalCapturedCount");

  if (countSpan) countSpan.textContent = uploadedFiles.length;

  if (strip) {
    strip.style.display = "flex";
    const img = document.createElement("img");
    img.className = "camera-strip-thumb";
    img.src = URL.createObjectURL(file);
    img.onload = () => URL.revokeObjectURL(img.src);
    img.title = `Angle #${uploadedFiles.length}`;
    strip.appendChild(img);
    // Scroll strip to right to show latest
    strip.scrollLeft = strip.scrollWidth;
  }
}

// Quality Check Alert Helpers
function showQualityAlert(title, message) {
  const box = document.getElementById("imageQualityAlertBox");
  const titleEl = document.getElementById("imageQualityAlertTitle");
  const msgEl = document.getElementById("imageQualityAlertMessage");
  if (box && titleEl && msgEl) {
    titleEl.textContent = title;
    msgEl.textContent = message;
    box.style.display = "block";
    box.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

function dismissQualityAlert() {
  const box = document.getElementById("imageQualityAlertBox");
  if (box) box.style.display = "none";
}

// =========================================================
// AI CONFIDENCE & HUMAN REVIEW ENGINE
// =========================================================

function initHumanReviewState(detections) {
  humanReviewState = {};
  activeDetectionFilter = "all";
  detectionSortOrder = "conf_asc"; // Default: Low confidence at top (ascending order)

  detections.forEach(d => {
    const conf = parseFloat(d.classification_confidence || 0);
    const isHigh = conf >= CONFIDENCE_THRESHOLD;
    humanReviewState[d.onion_number] = {
      onion_number: d.onion_number,
      image_order: d.image_order || 1,
      ai_class: d.class_name,
      current_class: d.class_name,
      classification_confidence: conf,
      detection_confidence: parseFloat(d.detection_confidence || 0),
      bounding_box: d.bounding_box || [0, 0, 0, 0],
      is_high_confidence: isHigh,
      is_confirmed: isHigh, // High-confidence is verified by default; low-confidence awaits officer confirmation
      is_overridden: false
    };
  });
}

function setDetectionSort(sortOrder) {
  detectionSortOrder = sortOrder;
  renderHumanReviewTable();
}

function toggleConfidenceSort() {
  detectionSortOrder = (detectionSortOrder === "conf_asc") ? "conf_desc" : "conf_asc";
  renderHumanReviewTable();
}

function toggleOnionSort() {
  detectionSortOrder = (detectionSortOrder === "onion_asc") ? "onion_desc" : "onion_asc";
  renderHumanReviewTable();
}

function setDetectionFilter(filterType) {
  activeDetectionFilter = filterType;

  // Update tab button styles
  const tabAll = document.getElementById("filterTabAll");
  const tabLow = document.getElementById("filterTabLow");
  const tabHigh = document.getElementById("filterTabHigh");

  if (tabAll) {
    tabAll.className = filterType === "all" ? "btn btn-sm btn-primary" : "btn btn-sm btn-outline";
  }
  if (tabLow) {
    tabLow.className = filterType === "low" ? "btn btn-sm btn-primary" : "btn btn-sm btn-outline";
    if (filterType !== "low") tabLow.style.borderColor = "#f59e0b";
  }
  if (tabHigh) {
    tabHigh.className = filterType === "high" ? "btn btn-sm btn-primary" : "btn btn-sm btn-outline";
    if (filterType !== "high") tabHigh.style.borderColor = "#10b981";
  }

  renderHumanReviewTable();
}

function renderHumanReviewTable() {
  const tbody = document.getElementById("detectionsTableBody");
  if (!tbody) return;

  const items = Object.values(humanReviewState);
  const totalCount = items.length;
  const lowConfItems = items.filter(it => !it.is_high_confidence);
  const lowCount = lowConfItems.length;
  const highCount = totalCount - lowCount;
  const unconfirmedLowCount = lowConfItems.filter(it => !it.is_confirmed && !it.is_overridden).length;

  // Update counter badges
  const cntAll = document.getElementById("cntAllBulbs");
  const cntLow = document.getElementById("cntLowConf");
  const cntHigh = document.getElementById("cntHighConf");
  const countBadge = document.getElementById("tableDetectionsCountBadge");
  const statusSummary = document.getElementById("humanReviewSummaryStatus");

  if (cntAll) cntAll.textContent = totalCount;
  if (cntLow) cntLow.textContent = lowCount;
  if (cntHigh) cntHigh.textContent = highCount;
  if (countBadge) countBadge.textContent = `${totalCount} Detected Bulbs`;

  if (statusSummary) {
    if (unconfirmedLowCount > 0) {
      statusSummary.innerHTML = `
        <span style="display: inline-flex; align-items: center; gap: 0.3rem; background: #fffbeb; border: 1px solid #fde68a; padding: 0.2rem 0.6rem; border-radius: 4px; color: #b45309;">
          ⚠️ <b>${unconfirmedLowCount}</b> low-confidence bulb${unconfirmedLowCount > 1 ? "s" : ""} pending officer confirmation
        </span>`;
    } else if (lowCount > 0) {
      statusSummary.innerHTML = `
        <span style="display: inline-flex; align-items: center; gap: 0.3rem; background: #ecfdf5; border: 1px solid #a7f3d0; padding: 0.2rem 0.6rem; border-radius: 4px; color: #065f46;">
          ✓ All ${lowCount} low-confidence bulbs reviewed & confirmed by Officer
        </span>`;
    } else {
      statusSummary.innerHTML = `
        <span style="display: inline-flex; align-items: center; gap: 0.3rem; background: #ecfdf5; border: 1px solid #a7f3d0; padding: 0.2rem 0.6rem; border-radius: 4px; color: #065f46;">
          ✓ All bulbs meet High Confidence threshold (≥ 50%)
        </span>`;
    }
  }

  // Filter items based on active tab
  let displayItems = [...items];
  if (activeDetectionFilter === "low") {
    displayItems = displayItems.filter(it => !it.is_high_confidence);
  } else if (activeDetectionFilter === "high") {
    displayItems = displayItems.filter(it => it.is_high_confidence);
  }

  // Sort displayItems (Default: Confidence Ascending, so low confidence images show at top)
  displayItems.sort((a, b) => {
    if (detectionSortOrder === "conf_asc") {
      const diff = (a.classification_confidence ?? 0) - (b.classification_confidence ?? 0);
      if (diff !== 0) return diff;
      return (a.onion_number ?? 0) - (b.onion_number ?? 0);
    } else if (detectionSortOrder === "conf_desc") {
      const diff = (b.classification_confidence ?? 0) - (a.classification_confidence ?? 0);
      if (diff !== 0) return diff;
      return (a.onion_number ?? 0) - (b.onion_number ?? 0);
    } else if (detectionSortOrder === "onion_desc") {
      return (b.onion_number ?? 0) - (a.onion_number ?? 0);
    } else {
      // onion_asc
      return (a.onion_number ?? 0) - (b.onion_number ?? 0);
    }
  });

  // Sync sort controls & indicators
  const sortSelect = document.getElementById("detectionSortSelect");
  if (sortSelect && sortSelect.value !== detectionSortOrder) {
    sortSelect.value = detectionSortOrder;
  }
  const confIcon = document.getElementById("confSortIcon");
  if (confIcon) {
    if (detectionSortOrder === "conf_asc") {
      confIcon.textContent = "▲ (Low 1st)";
      confIcon.style.color = "#d97706";
    } else if (detectionSortOrder === "conf_desc") {
      confIcon.textContent = "▼ (High 1st)";
      confIcon.style.color = "#047857";
    } else {
      confIcon.textContent = "↕";
      confIcon.style.color = "var(--text-muted)";
    }
  }
  const onionIcon = document.getElementById("onionSortIcon");
  if (onionIcon) {
    if (detectionSortOrder === "onion_asc") {
      onionIcon.textContent = "▲";
      onionIcon.style.color = "var(--primary-dark)";
    } else if (detectionSortOrder === "onion_desc") {
      onionIcon.textContent = "▼";
      onionIcon.style.color = "var(--primary-dark)";
    } else {
      onionIcon.textContent = "";
    }
  }

  if (displayItems.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">
          No onions match the selected filter (${activeDetectionFilter}).
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = displayItems.map(d => {
    const confPct = Math.round(d.classification_confidence * 100);
    const isHigh = d.is_high_confidence;

    // AI Prediction badge
    let aiBadgeClass = "badge-grade-a";
    if (d.ai_class === "Damaged") aiBadgeClass = "badge-grade-urs";
    else if (d.ai_class === "Rotten" || d.ai_class === "Sprouted") aiBadgeClass = "badge-grade-rej";
    else if (d.ai_class === "Uncertain") aiBadgeClass = "badge-info";

    // AI Confidence Status Badge (High Confidence vs Low Confidence)
    let confStatusHtml = "";
    if (isHigh) {
      confStatusHtml = `
        <span class="badge" style="background: #ecfdf5; color: #065f46; border: 1.5px solid #a7f3d0; font-weight: 700; padding: 0.35rem 0.6rem; display: inline-flex; align-items: center; gap: 0.3rem;">
          <span style="color: #10b981; font-weight: 900;">✓</span> High Confidence
        </span>`;
    } else {
      confStatusHtml = `
        <span class="badge" style="background: #fffbeb; color: #b45309; border: 1.5px solid #fde68a; font-weight: 700; padding: 0.35rem 0.6rem; display: inline-flex; align-items: center; gap: 0.3rem;" title="Confidence is below 50% threshold. Verification recommended.">
          <span style="color: #f59e0b; font-weight: 900;">⚠</span> Low Confidence – Manual Verification Recommended
        </span>`;
    }

    // Officer Review & Verification column
    let reviewStatusTag = "";
    if (d.is_overridden) {
      reviewStatusTag = `<span class="badge" style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 0.7rem;">✎ Overridden</span>`;
    } else if (d.is_confirmed) {
      reviewStatusTag = `<span class="badge badge-success" style="font-size: 0.7rem;">✓ Confirmed</span>`;
    } else {
      reviewStatusTag = `<span class="badge" style="background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; font-size: 0.7rem;">⚠ Pending Review</span>`;
    }

    // Quick Accept AI button if low confidence and not yet confirmed
    let quickAcceptBtn = "";
    if (!isHigh && !d.is_confirmed && !d.is_overridden) {
      quickAcceptBtn = `
        <button type="button" class="btn btn-sm btn-outline" onclick="confirmSinglePrediction(${d.onion_number})" style="font-size: 0.7rem; padding: 2px 7px; border-color: #f59e0b; color: #b45309;" title="Accept AI classification for this bulb">
          ✓ Accept AI
        </button>`;
    }

    const rowBg = (!isHigh && !d.is_confirmed && !d.is_overridden) ? "background: #fffdf5;" : "";

    return `
      <tr style="${rowBg}">
        <td><b>#${d.onion_number}</b></td>
        <td><span class="badge badge-info" style="font-size: 0.75rem;">Angle #${d.image_order}</span></td>
        <td>
          <span class="badge ${aiBadgeClass}" style="font-size: 0.8rem;">
            ${d.ai_class}
          </span>
        </td>
        <td>
          <div style="font-weight: 800; font-size: 0.9rem; color: ${isHigh ? '#047857' : '#b45309'};">
            ${confPct}%
          </div>
        </td>
        <td>
          ${confStatusHtml}
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap;">
            <select class="form-control" style="width: 155px; height: 30px; font-size: 0.8rem; font-weight: 700; padding: 2px 6px; border: 1.5px solid ${d.is_overridden ? '#3b82f6' : (!isHigh && !d.is_confirmed ? '#f59e0b' : '#10b981')}; background: white; border-radius: 4px;"
                    onchange="onOfficerOverrideChange(${d.onion_number}, this.value)"
                    title="Select confirmed grade for bulb #${d.onion_number}">
              <option value="Healthy" ${d.current_class === "Healthy" ? "selected" : ""}>Healthy (Grade A)</option>
              <option value="Damaged" ${d.current_class === "Damaged" ? "selected" : ""}>Damaged (URS)</option>
              <option value="Rotten" ${d.current_class === "Rotten" ? "selected" : ""}>Rotten (Rejected)</option>
              <option value="Sprouted" ${d.current_class === "Sprouted" ? "selected" : ""}>Sprouted (Rejected)</option>
            </select>
            ${reviewStatusTag}
            ${quickAcceptBtn}
          </div>
        </td>
        <td style="font-family: monospace; font-size: 0.72rem; color: var(--text-muted);">
          [${d.bounding_box.join(", ")}]
        </td>
      </tr>
    `;
  }).join("");
}

function onOfficerOverrideChange(onionNumber, newClass) {
  const item = humanReviewState[onionNumber];
  if (!item) return;

  item.current_class = newClass;
  item.is_overridden = (newClass !== item.ai_class);
  item.is_confirmed = true;

  // Re-render table and dynamically recalculate all metrics
  renderHumanReviewTable();
  recalculateEvaluationMetrics();
  showToast(`Bulb #${onionNumber} updated to '${newClass}'. Batch grading recalculated.`, "info");
}

function confirmSinglePrediction(onionNumber) {
  const item = humanReviewState[onionNumber];
  if (!item) return;

  item.is_confirmed = true;
  renderHumanReviewTable();
  showToast(`Bulb #${onionNumber} AI classification confirmed ✓`, "success");
}

function confirmAllPredictions() {
  const items = Object.values(humanReviewState);
  items.forEach(it => {
    it.is_confirmed = true;
  });
  renderHumanReviewTable();
  showToast(`✓ All ${items.length} bulb predictions verified and confirmed by Officer.`, "success");
}

function getItemOverridesList() {
  return Object.values(humanReviewState).map(it => ({
    onion_number: it.onion_number,
    class_name: it.current_class
  }));
}

function recalculateEvaluationMetrics() {
  const items = Object.values(humanReviewState);
  const total = items.length;
  if (total === 0) return;

  const healthyCount = items.filter(it => it.current_class === "Healthy").length;
  const damagedCount = items.filter(it => it.current_class === "Damaged").length;
  const rottenCount = items.filter(it => it.current_class === "Rotten").length;
  const sproutedCount = items.filter(it => it.current_class === "Sprouted").length;

  const gradeACount = healthyCount;
  const ursCount = damagedCount;
  const rejectedCount = rottenCount + sproutedCount;

  const healthyPct = Math.round((healthyCount / total) * 100 * 10) / 10;
  const damagedPct = Math.round((damagedCount / total) * 100 * 10) / 10;
  const rottenPct = Math.round((rottenCount / total) * 100 * 10) / 10;
  const sproutedPct = Math.round((sproutedCount / total) * 100 * 10) / 10;

  const gradeAPct = Math.round((gradeACount / total) * 100 * 10) / 10;
  const ursPct = Math.round((ursCount / total) * 100 * 10) / 10;
  const rejectedPct = Math.round((rejectedCount / total) * 100 * 10) / 10;

  // Update Summary Counts in UI
  const elGradeA = document.getElementById("resGradeA");
  const elGradeAPct = document.getElementById("resGradeAPct");
  const elURS = document.getElementById("resURS");
  const elURSPct = document.getElementById("resURSPct");
  const elRejected = document.getElementById("resRejected");
  const elRejectedPct = document.getElementById("resRejectedPct");

  if (elGradeA) elGradeA.textContent = gradeACount;
  if (elGradeAPct) elGradeAPct.textContent = gradeAPct + "%";
  if (elURS) elURS.textContent = ursCount;
  if (elURSPct) elURSPct.textContent = ursPct + "%";
  if (elRejected) elRejected.textContent = rejectedCount;
  if (elRejectedPct) elRejectedPct.textContent = rejectedPct + "%";

  // Quality Breakdown
  const elHealthy = document.getElementById("resHealthyCount");
  const elDamaged = document.getElementById("resDamagedCount");
  const elRotten = document.getElementById("resRottenCount");
  const elSprouted = document.getElementById("resSproutedCount");

  if (elHealthy) elHealthy.textContent = `${healthyCount} (${healthyPct}%)`;
  if (elDamaged) elDamaged.textContent = `${damagedCount} (${damagedPct}%)`;
  if (elRotten) elRotten.textContent = `${rottenCount} (${rottenPct}%)`;
  if (elSprouted) elSprouted.textContent = `${sproutedCount} (${sproutedPct}%)`;

  // Update Charts dynamically
  if (donutChart) {
    donutChart.data.datasets[0].data = [healthyCount, damagedCount, rottenCount, sproutedCount];
    donutChart.update();
  }
  if (barChart) {
    barChart.data.datasets[0].data = [gradeACount, ursCount, rejectedCount];
    barChart.update();
  }

  // Update Price Estimation Engine state
  currentPriceData.grade_a_pct = gradeAPct;
  currentPriceData.urs_pct = ursPct;
  currentPriceData.rejected_pct = rejectedPct;

  // Update Consolidated Summary Text dynamically
  const elSummary = document.getElementById("resQualitySummaryText");
  if (elSummary) {
    let gradeLabel = "Grade A - Premium Quality";
    if (gradeAPct < 75 && (gradeAPct + ursPct) >= 70) {
      gradeLabel = "URS Standard - Commercial Quality";
    } else if (gradeAPct < 75 && (gradeAPct + ursPct) < 70) {
      gradeLabel = "High Rejection - Substandard Batch";
    }
    elSummary.innerHTML = `Consolidated Officer-Verified Assessment: Batch classified as <strong>${gradeLabel}</strong>. ` +
      `Out of ${total} evaluated onions, ${gradeACount} (${gradeAPct}%) are Grade A (Healthy), ` +
      `${ursCount} (${ursPct}%) meet URS Standard (Damaged), and ${rejectedCount} (${rejectedPct}%) are Rejected (${rottenCount} Rotten, ${sproutedCount} Sprouted). ` +
      `<em>(Includes manual officer confirmations/overrides)</em>`;
  }

  updatePriceCalculationUI();
}


