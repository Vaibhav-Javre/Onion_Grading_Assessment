// Onion Evaluation Workflow Engine - Multi-Image & Multi-Angle Batch Processing

let selectedFarmer = null;
let uploadedFiles = []; // Array of File objects
let currentEvaluationId = null;
let currentEvaluationData = null;
let donutChart = null;
let barChart = null;

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
  initAddFarmerModal();
  initCameraCapture();
  initEvaluationActions();
});

// Step 1: Farmer Search & Selection
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

  // Load initial list
  loadRecentFarmers();
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
      <div style="padding: 1rem; text-align: center; color: var(--text-muted);">
        No farmers found matching query. 
        <button type="button" class="btn btn-sm btn-primary" onclick="openAddFarmerModal()" style="margin-top: 0.5rem;">
          + Add New Farmer
        </button>
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
      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
          <h4 style="color: var(--primary-green); font-size: 1.1rem; margin-bottom: 0.25rem;">${farmer.name}</h4>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.25rem;">
            <b>ID:</b> <span class="badge badge-info">${farmer.farmer_id}</span> • <b>Mobile:</b> ${farmer.phone}
          </p>
          <p style="font-size: 0.85rem; color: var(--text-dark);">
            <b>Location:</b> ${farmer.village}, Taluka: ${farmer.taluka}, District: ${farmer.district}, State: ${farmer.state}
          </p>
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
      showToast(data.error || "AI evaluation could not be completed. Please try again.", "error");
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

  // Detections Table
  const tbody = document.getElementById("detectionsTableBody");
  const countBadge = document.getElementById("tableDetectionsCountBadge");
  if (countBadge) countBadge.textContent = `${res.detections.length} Detected Bulbs`;

  tbody.innerHTML = res.detections.map(d => {
    let badgeClass = "badge-grade-a";
    if (d.class_name === "Damaged") badgeClass = "badge-grade-urs";
    else if (d.class_name === "Rotten" || d.class_name === "Sprouted") badgeClass = "badge-grade-rej";
    else if (d.class_name === "Uncertain") badgeClass = "badge-info";

    return `
      <tr>
        <td><b>#${d.onion_number}</b></td>
        <td><span class="badge badge-info" style="font-size: 0.75rem;">Angle #${d.image_order || 1}</span></td>
        <td><span class="badge ${badgeClass}">${d.class_name}</span></td>
        <td>${Math.round(d.classification_confidence * 100)}%</td>
        <td>${Math.round(d.detection_confidence * 100)}%</td>
        <td style="font-family: monospace; font-size: 0.75rem; color: var(--text-muted);">
          [${d.bounding_box.join(", ")}]
        </td>
      </tr>
    `;
  }).join("");
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
    const payload = {
      quantity_quintals: currentPriceData.quantity_quintals || 0,
      mandi_modal_price: currentPriceData.modal_price,
      estimated_price_per_quintal: currentPriceData.estimated_price_per_quintal,
      quality_score: currentPriceData.quality_score_pct,
      total_payout: currentPriceData.total_payout,
      mandi_name: currentPriceData.mandi_name,
      mandi_price_date: currentPriceData.price_date,
      mandi_api_source: currentPriceData.source,
      urs_multiplier: currentPriceData.urs_multiplier !== undefined ? currentPriceData.urs_multiplier : 0.8
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

    // Success! Show confirmation modal
    document.getElementById("confirmedReportId").textContent = data.report_id;
    const filename = `Onion_Report_${data.report_id}.pdf`;
    const downloadUrl = `/reports/download/${filename}`;

    const downloadBtn = document.getElementById("pdfDownloadLink");
    if (downloadBtn) {
      downloadBtn.href = downloadUrl;
      downloadBtn.setAttribute("download", filename);
      downloadBtn.target = "_blank";
      downloadBtn.onclick = null;
    }
    
    const viewBtn = document.getElementById("pdfViewLink");
    if (viewBtn) {
      viewBtn.href = `${downloadUrl}?inline=1`;
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

// Modal for quick adding new farmer

function initAddFarmerModal() {
  const modal = document.getElementById("addFarmerModal");
  if (!modal) return;

  const form = document.getElementById("addFarmerForm");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById("newFarmerName").value,
      phone: document.getElementById("newFarmerPhone").value,
      village: document.getElementById("newFarmerVillage").value,
      taluka: document.getElementById("newFarmerTaluka").value,
      district: document.getElementById("newFarmerDistrict").value,
      state: document.getElementById("newFarmerState").value
    };

    try {
      const res = await fetch("/api/officer/farmers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success && data.farmer) {
        showToast(data.message, "success");
        closeAddFarmerModal();
        selectFarmer(data.farmer);
      } else {
        showToast(data.error || "Failed to add farmer", "error");
      }
    } catch (err) {
      showToast("Network error: " + err.message, "error");
    }
  });
}

function openAddFarmerModal() {
  document.getElementById("addFarmerModal").style.display = "flex";
}

function closeAddFarmerModal() {
  document.getElementById("addFarmerModal").style.display = "none";
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
