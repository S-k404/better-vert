/**
 * Better VERT · Universal Studio Client Logic
 * Handles Minimalist Universal Converter, Advanced Encoding Options,
 * Persistent Settings Manager, Markdown Studio, and Batch Automation.
 */

document.addEventListener("DOMContentLoaded", () => {
  // ---------------------------------------------------------------------------
  // Global & Persistent State
  // ---------------------------------------------------------------------------
  const SETTINGS_STORAGE_KEY = "better_vert_settings_v2";

  const DEFAULT_SETTINGS = {
    defaultVideo: "mp4",
    defaultAudio: "mp3",
    defaultImage: "webp",
    defaultDoc: "pdf",
    defaultCrf: "22",
    defaultCodec: "",
    defaultAudioBitrate: "192k",
    defaultImgQuality: "85",
    autoDownload: false,
    autoCopyMarkdown: false,
    preserveMetadata: true,
  };

  let userSettings = { ...DEFAULT_SETTINGS };
  let systemInfo = null;
  let formatsCatalog = null;
  let stagedUniversalFiles = [];
  let currentSearchQuery = "";
  let currentFilterCategory = "all";
  let currentMediaBlobUrl = null;
  let stagedMarkdownFiles = [];
  let currentModalMarkdown = "";
  let currentModalFilename = "";
  let toastTimer = null;

  // ---------------------------------------------------------------------------
  // DOM Elements: Navigation & Full-Page Drag Drop
  // ---------------------------------------------------------------------------
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  const fullPageDropOverlay = document.getElementById("fullPageDropOverlay");

  // ---------------------------------------------------------------------------
  // DOM Elements: Universal Converter (Home View & Active Studio)
  // ---------------------------------------------------------------------------
  const dropzoneUniversal = document.getElementById("dropzoneUniversal");
  const fileInputUniversal = document.getElementById("fileInputUniversal");
  const universalHomeHero = document.getElementById("universalHomeHero");
  const universalControls = document.getElementById("universalControls");
  const singleFileBanner = document.getElementById("singleFileBanner") || document.querySelector(".flow-header-banner");
  const selectedFileName = document.getElementById("selectedFileName");
  const selectedFileSize = document.getElementById("selectedFileSize");
  const selectedFileExt = document.getElementById("selectedFileExt");
  const flowTargetExtBadge = document.getElementById("flowTargetExtBadge");
  const flowTargetName = document.getElementById("flowTargetName");
  const formatCardsGrid = document.getElementById("formatCardsGrid");
  const formatGridCount = document.getElementById("formatGridCount");
  const bottomConvertDock = document.getElementById("bottomConvertDock");
  const dockStagedChips = document.getElementById("dockStagedChips");
  const btnDockAddMore = document.getElementById("btnDockAddMore");
  const btnClearUniversal = document.getElementById("btnClearUniversal");

  // Multi-File Queue
  const multiFileQueueContainer = document.getElementById("multiFileQueueContainer");
  const multiFileCount = document.getElementById("multiFileCount");
  const btnClearMultiQueue = document.getElementById("btnClearMultiQueue");
  const multiFileList = document.getElementById("multiFileList");

  // Format Search & Toolbar
  const formatSearchInput = document.getElementById("formatSearchInput");
  const btnClearSearch = document.getElementById("btnClearSearch");
  const selectTargetFormat = document.getElementById("selectTargetFormat");
  const categoryPills = document.querySelectorAll("#categoryPills .cat-pill");
  const btnConvertUniversal = document.getElementById("btnConvertUniversal");
  const btnConvertText = document.getElementById("btnConvertText");

  // Results & Route Badges
  const routeBadgeContainer = document.getElementById("routeBadgeContainer");
  const routeBadgeText = document.getElementById("routeBadgeText");
  const mediaPreviewContainer = document.getElementById("mediaPreviewContainer");
  const universalResult = document.getElementById("universalResult");
  const universalResultTitle = document.getElementById("universalResultTitle");
  const btnDownloadUniversal = document.getElementById("btnDownloadUniversal");

  // macOS Studio Developer Terminal Console Dropdown
  const terminalConsole = document.getElementById("terminalConsole");
  const terminalTitlebar = document.getElementById("terminalTitlebar");
  const terminalBody = document.getElementById("terminalBody");
  const terminalStatusBadge = document.getElementById("terminalStatusBadge");
  const terminalStatusText = document.getElementById("terminalStatusText");
  const btnCopyTerminalLogs = document.getElementById("btnCopyTerminalLogs");
  const btnClearTerminalLogs = document.getElementById("btnClearTerminalLogs");
  const terminalChevron = document.getElementById("terminalChevron");
  const terminalProgressPanel = document.getElementById("terminalProgressPanel");
  const termStepDesc = document.getElementById("termStepDesc");
  const termPctNum = document.getElementById("termPctNum");
  const termProgressFill = document.getElementById("termProgressFill");
  const terminalStream = document.getElementById("terminalStream");

  // Advanced Options Drawer Elements
  const btnToggleAdvanced = document.getElementById("btnToggleAdvanced");
  const advancedPanel = document.getElementById("advancedPanel");
  const advIndicator = document.getElementById("advIndicator");
  const advCrf = document.getElementById("advCrf");
  const advResolution = document.getElementById("advResolution");
  const advVideoCodec = document.getElementById("advVideoCodec");
  const advAudioBitrate = document.getElementById("advAudioBitrate");
  const advFps = document.getElementById("advFps");
  const advQuality = document.getElementById("advQuality");
  const advTrimStart = document.getElementById("advTrimStart");
  const advTrimDuration = document.getElementById("advTrimDuration");
  const advPlaybackSpeed = document.getElementById("advPlaybackSpeed");
  const advAudioChannels = document.getElementById("advAudioChannels");
  const advLoudnorm = document.getElementById("advLoudnorm");
  const advColorFilter = document.getElementById("advColorFilter");
  const advDpi = document.getElementById("advDpi");
  const btnResetAdvanced = document.getElementById("btnResetAdvanced");
  const btnInspectStagedFile = document.getElementById("btnInspectStagedFile");

  // Smart Actions Hub Elements
  const smartActionsHub = document.getElementById("smartActionsHub");
  const smartActionsChips = document.getElementById("smartActionsChips");
  const smartHubTargetName = document.getElementById("smartHubTargetName");

  // ---------------------------------------------------------------------------
  // DOM Elements: Settings & Studio Tab
  // ---------------------------------------------------------------------------
  const prefDefaultVideo = document.getElementById("prefDefaultVideo");
  const prefDefaultAudio = document.getElementById("prefDefaultAudio");
  const prefDefaultImage = document.getElementById("prefDefaultImage");
  const prefDefaultDoc = document.getElementById("prefDefaultDoc");
  const prefDefaultCrf = document.getElementById("prefDefaultCrf");
  const prefDefaultCodec = document.getElementById("prefDefaultCodec");
  const prefDefaultAudioBitrate = document.getElementById("prefDefaultAudioBitrate");
  const prefDefaultImgQuality = document.getElementById("prefDefaultImgQuality");
  const prefAutoDownload = document.getElementById("prefAutoDownload");
  const prefAutoCopyMarkdown = document.getElementById("prefAutoCopyMarkdown");
  const prefPreserveMetadata = document.getElementById("prefPreserveMetadata");
  const btnResetAllSettings = document.getElementById("btnResetAllSettings");
  const settingsToast = document.getElementById("settingsToast");
  const btnCopyVtb = document.getElementById("btnCopyVtb");
  const videoToolboxCommand = document.getElementById("videoToolboxCommand");

  // ---------------------------------------------------------------------------
  // DOM Elements: Markdown Studio
  // ---------------------------------------------------------------------------
  const dropzoneMarkdown = document.getElementById("dropzoneMarkdown");
  const fileInputMarkdown = document.getElementById("fileInputMarkdown");
  const btnBrowseMarkdown = document.getElementById("btnBrowseMarkdown");
  const btnConvertMarkdown = document.getElementById("btnConvertMarkdown");
  const btnConvertZip = document.getElementById("btnConvertZip");
  const btnClearMarkdown = document.getElementById("btnClearMarkdown");
  const markdownFileCount = document.getElementById("markdownFileCount");
  const markdownResultsList = document.getElementById("markdownResultsList");
  const chkMarkdownFrontmatter = document.getElementById("chkMarkdownFrontmatter");

  // ---------------------------------------------------------------------------
  // DOM Elements: PDF Studio (Merge & Split)
  // ---------------------------------------------------------------------------
  const dropzonePdfMerge = document.getElementById("dropzonePdfMerge");
  const fileInputPdfMerge = document.getElementById("fileInputPdfMerge");
  const pdfMergeList = document.getElementById("pdfMergeList");
  const pdfMergeOutName = document.getElementById("pdfMergeOutName");
  const btnTriggerPdfMerge = document.getElementById("btnTriggerPdfMerge");
  const btnClearPdfMerge = document.getElementById("btnClearPdfMerge");
  const pdfMergeResult = document.getElementById("pdfMergeResult");
  const pdfMergeResultText = document.getElementById("pdfMergeResultText");
  const btnDownloadPdfMerge = document.getElementById("btnDownloadPdfMerge");

  const dropzonePdfSplit = document.getElementById("dropzonePdfSplit");
  const fileInputPdfSplit = document.getElementById("fileInputPdfSplit");
  const pdfSplitStaged = document.getElementById("pdfSplitStaged");
  const pdfSplitStagedName = document.getElementById("pdfSplitStagedName");
  const pdfSplitStagedMeta = document.getElementById("pdfSplitStagedMeta");
  const btnRemovePdfSplit = document.getElementById("btnRemovePdfSplit");
  const pdfSplitRange = document.getElementById("pdfSplitRange");
  const btnTriggerPdfSplit = document.getElementById("btnTriggerPdfSplit");
  const pdfSplitResult = document.getElementById("pdfSplitResult");
  const pdfSplitResultText = document.getElementById("pdfSplitResultText");
  const btnDownloadPdfSplit = document.getElementById("btnDownloadPdfSplit");

  // ---------------------------------------------------------------------------
  // DOM Elements: Media Telemetry & Inspector Modal
  // ---------------------------------------------------------------------------
  const mediaInspectorModal = document.getElementById("mediaInspectorModal");
  const inspectorCategoryBadge = document.getElementById("inspectorCategoryBadge");
  const inspectorModalTitle = document.getElementById("inspectorModalTitle");
  const btnCloseInspector = document.getElementById("btnCloseInspector");
  const btnCloseInspectorFooter = document.getElementById("btnCloseInspectorFooter");
  const inspectorLoading = document.getElementById("inspectorLoading");
  const inspectorContent = document.getElementById("inspectorContent");
  const inspectorStatsGrid = document.getElementById("inspectorStatsGrid");
  const inspectorSectionTitle = document.getElementById("inspectorSectionTitle");
  const inspectorStreamsList = document.getElementById("inspectorStreamsList");
  const inspectorRawCode = document.getElementById("inspectorRawCode");
  const btnCopyInspectorJson = document.getElementById("btnCopyInspectorJson");

  // ---------------------------------------------------------------------------
  // DOM Elements: Batch Mode
  // ---------------------------------------------------------------------------
  const batchInputCount = document.getElementById("batchInputCount");
  const batchOutputCount = document.getElementById("batchOutputCount");
  const batchInputList = document.getElementById("batchInputList");
  const batchOutputList = document.getElementById("batchOutputList");
  const btnTriggerBatch = document.getElementById("btnTriggerBatch");
  const btnRefreshBatch = document.getElementById("btnRefreshBatch");

  // ---------------------------------------------------------------------------
  // DOM Elements: Modal Preview
  // ---------------------------------------------------------------------------
  const markdownModal = document.getElementById("markdownModal");
  const modalTitle = document.getElementById("modalTitle");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const modalRenderedContent = document.getElementById("modalRenderedContent");
  const modalRawContent = document.getElementById("modalRawContent");
  const btnToggleRendered = document.getElementById("btnToggleRendered");
  const btnToggleRaw = document.getElementById("btnToggleRaw");
  const btnCopyMarkdown = document.getElementById("btnCopyMarkdown");
  const copyText = document.getElementById("copyText");
  const btnDownloadModal = document.getElementById("btnDownloadModal");
  const btnExportHtml = document.getElementById("btnExportHtml");

  // ---------------------------------------------------------------------------
  // 1. Persistent Settings Manager
  // ---------------------------------------------------------------------------
  function loadSettings() {
    try {
      const raw = localStorage.getItem(SETTINGS_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        userSettings = { ...DEFAULT_SETTINGS, ...parsed };
      }
    } catch (e) {
      console.warn("Error loading settings from localStorage:", e);
      userSettings = { ...DEFAULT_SETTINGS };
    }

    // Populate Settings tab inputs
    if (prefDefaultVideo) prefDefaultVideo.value = userSettings.defaultVideo;
    if (prefDefaultAudio) prefDefaultAudio.value = userSettings.defaultAudio;
    if (prefDefaultImage) prefDefaultImage.value = userSettings.defaultImage;
    if (prefDefaultDoc) prefDefaultDoc.value = userSettings.defaultDoc;
    if (prefDefaultCrf) prefDefaultCrf.value = userSettings.defaultCrf;
    if (prefDefaultCodec) prefDefaultCodec.value = userSettings.defaultCodec;
    if (prefDefaultAudioBitrate) prefDefaultAudioBitrate.value = userSettings.defaultAudioBitrate;
    if (prefDefaultImgQuality) prefDefaultImgQuality.value = userSettings.defaultImgQuality;
    if (prefAutoDownload) prefAutoDownload.checked = userSettings.autoDownload;
    if (prefAutoCopyMarkdown) prefAutoCopyMarkdown.checked = userSettings.autoCopyMarkdown;
    if (prefPreserveMetadata) prefPreserveMetadata.checked = userSettings.preserveMetadata;

    // Apply defaults to Advanced Options panel
    syncAdvancedOptionsWithDefaults();
  }

  function saveSettings() {
    if (prefDefaultVideo) userSettings.defaultVideo = prefDefaultVideo.value;
    if (prefDefaultAudio) userSettings.defaultAudio = prefDefaultAudio.value;
    if (prefDefaultImage) userSettings.defaultImage = prefDefaultImage.value;
    if (prefDefaultDoc) userSettings.defaultDoc = prefDefaultDoc.value;
    if (prefDefaultCrf) userSettings.defaultCrf = prefDefaultCrf.value;
    if (prefDefaultCodec) userSettings.defaultCodec = prefDefaultCodec.value;
    if (prefDefaultAudioBitrate) userSettings.defaultAudioBitrate = prefDefaultAudioBitrate.value;
    if (prefDefaultImgQuality) userSettings.defaultImgQuality = prefDefaultImgQuality.value;
    if (prefAutoDownload) userSettings.autoDownload = prefAutoDownload.checked;
    if (prefAutoCopyMarkdown) userSettings.autoCopyMarkdown = prefAutoCopyMarkdown.checked;
    if (prefPreserveMetadata) userSettings.preserveMetadata = prefPreserveMetadata.checked;

    try {
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(userSettings));
      showSettingsToast("Preferences saved");
      syncAdvancedOptionsWithDefaults();
    } catch (e) {
      console.error("Error saving settings:", e);
    }
  }

  function resetSettings() {
    userSettings = { ...DEFAULT_SETTINGS };
    localStorage.removeItem(SETTINGS_STORAGE_KEY);
    loadSettings();
    showSettingsToast("Reset to factory defaults");
  }

  function showSettingsToast(msg = "Preferences saved") {
    if (!settingsToast) return;
    const textSpan = settingsToast.querySelector("span:last-child");
    if (textSpan) textSpan.textContent = msg;
    settingsToast.style.opacity = "1";
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      settingsToast.style.opacity = "0";
    }, 2200);
  }

  function syncAdvancedOptionsWithDefaults() {
    if (advCrf) advCrf.value = userSettings.defaultCrf;
    if (advVideoCodec) advVideoCodec.value = userSettings.defaultCodec;
    if (advAudioBitrate) advAudioBitrate.value = userSettings.defaultAudioBitrate;
    if (advQuality) advQuality.value = userSettings.defaultImgQuality;
    if (advResolution) advResolution.value = "original";
    if (advFps) advFps.value = "original";
    if (advTrimStart) advTrimStart.value = "";
    if (advTrimDuration) advTrimDuration.value = "";
    if (advPlaybackSpeed) advPlaybackSpeed.value = "1.0";
    if (advAudioChannels) advAudioChannels.value = "";
    if (advLoudnorm) advLoudnorm.checked = false;
    if (advColorFilter) advColorFilter.value = "";
    if (advDpi) advDpi.value = "150";
    updateAdvIndicator();
  }

  function updateAdvIndicator() {
    if (!advIndicator) return;
    const isCustomized =
      (advCrf && advCrf.value !== userSettings.defaultCrf) ||
      (advVideoCodec && advVideoCodec.value !== userSettings.defaultCodec) ||
      (advAudioBitrate && advAudioBitrate.value !== userSettings.defaultAudioBitrate) ||
      (advQuality && advQuality.value !== userSettings.defaultImgQuality) ||
      (advResolution && advResolution.value !== "original") ||
      (advFps && advFps.value !== "original") ||
      (advTrimStart && advTrimStart.value.trim() !== "") ||
      (advTrimDuration && advTrimDuration.value.trim() !== "") ||
      (advPlaybackSpeed && advPlaybackSpeed.value !== "1.0") ||
      (advAudioChannels && advAudioChannels.value !== "") ||
      (advLoudnorm && advLoudnorm.checked) ||
      (advColorFilter && advColorFilter.value !== "") ||
      (advDpi && advDpi.value !== "150");

    if (isCustomized) {
      advIndicator.textContent = "Customized";
      advIndicator.style.color = "var(--blue-accent)";
      advIndicator.style.borderColor = "var(--blue-accent)";
    } else {
      advIndicator.textContent = "Default";
      advIndicator.style.color = "var(--text-dim)";
      advIndicator.style.borderColor = "var(--border)";
    }
  }

  // Bind change listeners to auto-save in Settings tab
  const settingsInputs = [
    prefDefaultVideo,
    prefDefaultAudio,
    prefDefaultImage,
    prefDefaultDoc,
    prefDefaultCrf,
    prefDefaultCodec,
    prefDefaultAudioBitrate,
    prefDefaultImgQuality,
    prefAutoDownload,
    prefAutoCopyMarkdown,
    prefPreserveMetadata,
  ];

  settingsInputs.forEach((input) => {
    if (input) {
      input.addEventListener("change", () => {
        saveSettings();
      });
    }
  });

  if (btnResetAllSettings) {
    btnResetAllSettings.addEventListener("click", () => {
      if (confirm("Reset all settings to default values?")) {
        resetSettings();
      }
    });
  }

  if (btnCopyVtb && videoToolboxCommand) {
    btnCopyVtb.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(videoToolboxCommand.textContent.trim());
        btnCopyVtb.textContent = "Copied!";
        setTimeout(() => (btnCopyVtb.textContent = "Copy"), 2000);
      } catch (e) {
        alert("Copy failed");
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 2. Navigation Tabs
  // ---------------------------------------------------------------------------
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      const activeContent = document.getElementById(targetTab);
      if (activeContent) activeContent.classList.add("active");

      if (targetTab === "tab-batch") {
        fetchBatchStatus();
      }
    });
  });

  // ---------------------------------------------------------------------------
  // 3. Telemetry & Hardware Info
  // ---------------------------------------------------------------------------
  // The container is always Linux, so it cannot tell a Mac from a Windows PC or a
  // Linux box. The stack only listens on loopback, so the browser's own OS is the
  // Docker host's OS; use it to describe the machine and to pick the right GPU tip.
  function detectClientOS() {
    const nav = typeof navigator !== "undefined" ? navigator : {};
    const hint = (nav.userAgentData && nav.userAgentData.platform) || nav.platform || nav.userAgent || "";
    if (/mac/i.test(hint)) return "macOS";
    if (/win/i.test(hint)) return "Windows";
    if (/linux|x11|cros/i.test(hint)) return "Linux";
    return "";
  }

  function describeHost(info) {
    const arch = (info && info.architecture) || "";
    const isArm = /^(arm64|aarch64)$/i.test(arch);
    const archName = isArm ? "ARM64" : /^(x86_64|amd64)$/i.test(arch) ? "x86-64" : arch;
    const os = detectClientOS();
    let label = (info && info.host) || "Unknown host";
    if (isArm && os === "macOS") label = "Apple Silicon (macOS)";
    else if (archName && os) label = `${archName} (${os})`;
    const simd = info && info.acceleration && info.acceleration.simd;
    return { label, archName, simd };
  }

  const HOST_GPU_HINTS = {
    macOS: {
      title: "Native macOS VideoToolbox GPU Acceleration",
      intro: "For 4K/8K jobs where you want native Apple VideoToolbox GPU encoding directly on macOS, without container virtualization overhead:",
      note: "Uses hevc_videotoolbox / h264_videotoolbox from your host Homebrew FFmpeg (brew install ffmpeg).",
    },
    Windows: {
      title: "Native GPU Acceleration (NVIDIA / Intel / AMD)",
      intro: "Docker Desktop cannot reach your GPU, so for 4K/8K jobs run the helper on the host instead. Use Git Bash or a WSL2 shell:",
      note: "Uses NVENC, Quick Sync or AMF from the FFmpeg on your PATH (winget install Gyan.FFmpeg).",
    },
    Linux: {
      title: "Native GPU Acceleration (NVIDIA / Intel / AMD)",
      intro: "For 4K/8K jobs where you want hardware GPU encoding directly on the host, outside the container:",
      note: "Uses NVENC, Quick Sync or VAAPI from the FFmpeg on your PATH. Falls back to software if no GPU encoder works.",
    },
  };

  function applyHostGpuHints() {
    const hint = HOST_GPU_HINTS[detectClientOS()];
    if (!hint) return;
    const set = (id, text) => {
      const el = document.getElementById(id);
      if (el) el.textContent = text;
    };
    set("hostGpuTitle", hint.title);
    set("hostGpuIntro", hint.intro);
    set("hostGpuNote", hint.note);
  }

  async function fetchTelemetry() {
    applyHostGpuHints();
    try {
      const [sysRes, catRes] = await Promise.all([
        fetch("/api/system-info").catch(() => null),
        fetch("/api/formats-catalog").catch(() => null),
      ]);

      if (sysRes && sysRes.ok) {
        systemInfo = await sysRes.json();

        const hostInfo = describeHost(systemInfo);
        const simdSuffix = hostInfo.simd ? ` · ${hostInfo.simd}` : "";

        // Header telemetry pill
        const pillText = document.getElementById("telemetryText");
        if (pillText && systemInfo.cores_logical) {
          pillText.textContent = `${hostInfo.label} · ${systemInfo.cores_logical} Cores Active${simdSuffix}`;
        }

        // Settings tab telemetry cards
        const statHost = document.getElementById("statHost");
        const statCores = document.getElementById("statCores");
        const statRam = document.getElementById("statRam");
        const statArch = document.getElementById("statArch");
        const statAccel = document.getElementById("statAccel");
        if (statHost) statHost.textContent = hostInfo.label;
        if (statArch) statArch.textContent = `Architecture: ${systemInfo.architecture || "unknown"}`;
        if (statAccel) statAccel.textContent = hostInfo.simd ? `${hostInfo.simd} SIMD + browser GPU` : "Browser GPU";
        if (statCores) statCores.textContent = `${systemInfo.cores_logical} CPU Threads`;
        if (statRam) statRam.textContent = `${systemInfo.memory_available_gb} GB Free / ${systemInfo.memory_total_gb} GB`;

        // Home hero badge & terminal hardware tag
        const heroBadgeCores = document.getElementById("heroBadgeCores");
        const termHwTag = document.getElementById("termHwTag");
        if (heroBadgeCores && systemInfo.cores_logical) {
          heroBadgeCores.textContent = `${systemInfo.cores_logical} Cores Active`;
        }
        if (termHwTag && systemInfo.cores_logical) {
          termHwTag.textContent = `${systemInfo.cores_logical} CORES${hostInfo.simd ? ` · ${hostInfo.simd} SIMD` : ""}`;
        }
      }

      if (catRes && catRes.ok) {
        formatsCatalog = await catRes.json();
      }

      populateFormats(currentFilterCategory, currentSearchQuery);
    } catch (e) {
      console.warn("System telemetry fetch error:", e);
    }
  }

  // ---------------------------------------------------------------------------
  // 4. Universal Converter & Advanced Options (Inspired by p2r3/convert)
  // ---------------------------------------------------------------------------
  function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  function getFileCategory(filename) {
    const ext = filename.split(".").pop().toLowerCase();
    const videoExts = ["mp4", "mkv", "webm", "mov", "avi", "gif", "wmv", "flv", "m4v", "ts", "mts", "m2ts", "vob", "ogv", "3gp", "asf", "av1"];
    const audioExts = ["mp3", "wav", "aac", "flac", "m4a", "m4b", "ogg", "opus", "wma", "aiff", "aif", "alac", "ac3", "caf", "mp2"];
    const imageExts = ["png", "jpg", "jpeg", "webp", "avif", "gif", "tiff", "bmp", "ico", "svg"];
    const docExts = ["pdf", "docx", "md", "html", "epub", "txt", "rtf", "odt"];
    const dataExts = ["json", "csv", "yaml", "yml", "xml", "tsv"];

    if (videoExts.includes(ext)) return "video";
    if (audioExts.includes(ext)) return "audio";
    if (imageExts.includes(ext)) return "image";
    if (dataExts.includes(ext)) return "data";
    if (docExts.includes(ext)) return "document";
    return "all";
  }

  // Cross-medium format definitions
  const CROSS_FORMAT_OPTIONS = [
    { id: "pdf_storyboard", label: "PDF Storyboard (Video → PDF)", category: "cross", matchExts: ["video"] },
    { id: "waveform_video", label: "Waveform Video (Audio → MP4)", category: "cross", matchExts: ["audio"] },
    { id: "transcript_md", label: "Speech Transcript (Audio → MD)", category: "cross", matchExts: ["audio", "video"] },
    { id: "images_zip", label: "Extracted Images & Pages (.ZIP) (Doc/MD → Images ZIP)", category: "cross", matchExts: ["document"] },
    { id: "svg", label: "Vector Graphic (Raster → SVG)", category: "cross", matchExts: ["image"] },
    { id: "gif", label: "High-FPS GIF (2-Pass Palette) (Video → GIF)", category: "cross", matchExts: ["video"] },
    { id: "xlsx", label: "Excel Workbook (Data → XLSX)", category: "cross", matchExts: ["data"] },
  ];

  // Comprehensive Format Metadata Dictionary for Visual Cards Grid
  const FORMAT_METADATA = {
    // Images
    png: { ext: "PNG", name: "Portable Network Graphics", cat: "image", color: "#0ea5e9", bg: "rgba(14, 165, 233, 0.15)" },
    webp: { ext: "WEBP", name: "Google WebP Modern Image", cat: "image", color: "#14b8a6", bg: "rgba(20, 184, 166, 0.15)" },
    jpg: { ext: "JPG", name: "Joint Photographic Experts", cat: "image", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
    jpeg: { ext: "JPEG", name: "JPEG Image", cat: "image", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
    avif: { ext: "AVIF", name: "AV1 Image File Format", cat: "image", color: "#8b5cf6", bg: "rgba(139, 92, 246, 0.15)" },
    svg: { ext: "SVG", name: "Scalable Vector Graphics", cat: "image", color: "#eab308", bg: "rgba(234, 179, 8, 0.15)" },
    gif: { ext: "GIF", name: "2-Pass Lanczos Animated GIF", cat: "image", color: "#10b981", bg: "rgba(16, 185, 129, 0.15)" },
    bmp: { ext: "BMP", name: "Windows Bitmap Image", cat: "image", color: "#64748b", bg: "rgba(100, 116, 139, 0.15)" },
    ico: { ext: "ICO", name: "Windows Icon Format", cat: "image", color: "#38bdf8", bg: "rgba(56, 189, 248, 0.15)" },
    tiff: { ext: "TIFF", name: "Tagged Image File Format", cat: "image", color: "#a855f7", bg: "rgba(168, 85, 247, 0.15)" },
    pbm: { ext: "PBM", name: "Portable Bitmap Format", cat: "image", color: "#94a3b8", bg: "rgba(148, 163, 184, 0.15)" },

    // Video
    mp4: { ext: "MP4", name: "MPEG-4 Part 14 FastStart", cat: "video", color: "#3b82f6", bg: "rgba(59, 130, 246, 0.15)" },
    av1: { ext: "AV1", name: "SVT-AV1 10-Bit Next-Gen", cat: "video", color: "#a855f7", bg: "rgba(168, 85, 247, 0.15)" },
    mkv: { ext: "MKV", name: "Matroska Multi-Stream", cat: "video", color: "#6366f1", bg: "rgba(99, 102, 241, 0.15)" },
    webm: { ext: "WEBM", name: "WebM Open Media Format", cat: "video", color: "#0284c7", bg: "rgba(2, 132, 199, 0.15)" },
    mov: { ext: "MOV", name: "Apple QuickTime Movie", cat: "video", color: "#ec4899", bg: "rgba(236, 72, 153, 0.15)" },
    avi: { ext: "AVI", name: "Audio Video Interleave", cat: "video", color: "#f97316", bg: "rgba(249, 115, 22, 0.15)" },
    wmv: { ext: "WMV", name: "Windows Media Video", cat: "video", color: "#0ea5e9", bg: "rgba(14, 165, 233, 0.15)" },
    flv: { ext: "FLV", name: "Flash Live Video", cat: "video", color: "#ef4444", bg: "rgba(239, 68, 68, 0.15)" },
    m4v: { ext: "M4V", name: "Apple MPEG-4 Video", cat: "video", color: "#8b5cf6", bg: "rgba(139, 92, 246, 0.15)" },
    ts: { ext: "TS", name: "MPEG Transport Stream", cat: "video", color: "#14b8a6", bg: "rgba(20, 184, 166, 0.15)" },
    mts: { ext: "MTS", name: "AVCHD High Definition", cat: "video", color: "#64748b", bg: "rgba(100, 116, 139, 0.15)" },
    m2ts: { ext: "M2TS", name: "Blu-ray BDAV Stream", cat: "video", color: "#06b6d4", bg: "rgba(6, 182, 212, 0.15)" },
    vob: { ext: "VOB", name: "DVD Video Object", cat: "video", color: "#8b5cf6", bg: "rgba(139, 92, 246, 0.15)" },
    ogv: { ext: "OGV", name: "Ogg Theora Video", cat: "video", color: "#10b981", bg: "rgba(16, 185, 129, 0.15)" },
    "3gp": { ext: "3GP", name: "3GPP Mobile Media", cat: "video", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
    asf: { ext: "ASF", name: "Advanced Systems Format", cat: "video", color: "#64748b", bg: "rgba(100, 116, 139, 0.15)" },

    // Audio
    mp3: { ext: "MP3", name: "MPEG-3 Audio Layer", cat: "audio", color: "#f43f5e", bg: "rgba(244, 63, 94, 0.15)" },
    wav: { ext: "WAV", name: "Waveform Audio Format", cat: "audio", color: "#06b6d4", bg: "rgba(6, 182, 212, 0.15)" },
    flac: { ext: "FLAC", name: "Free Lossless Audio Codec", cat: "audio", color: "#d946ef", bg: "rgba(217, 70, 239, 0.15)" },
    aac: { ext: "AAC", name: "Advanced Audio Coding", cat: "audio", color: "#fb7185", bg: "rgba(251, 113, 133, 0.15)" },
    m4a: { ext: "M4A", name: "Apple Audio AAC / Lossless", cat: "audio", color: "#8b5cf6", bg: "rgba(139, 92, 246, 0.15)" },
    m4b: { ext: "M4B", name: "Apple Audiobook AAC", cat: "audio", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
    ogg: { ext: "OGG", name: "Ogg Vorbis Audio", cat: "audio", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
    opus: { ext: "OPUS", name: "Opus Interactive Audio", cat: "audio", color: "#10b981", bg: "rgba(16, 185, 129, 0.15)" },
    aiff: { ext: "AIFF", name: "Audio Interchange Format", cat: "audio", color: "#38bdf8", bg: "rgba(56, 189, 248, 0.15)" },
    aif: { ext: "AIF", name: "Audio Interchange Format", cat: "audio", color: "#38bdf8", bg: "rgba(56, 189, 248, 0.15)" },
    wma: { ext: "WMA", name: "Windows Media Audio", cat: "audio", color: "#6366f1", bg: "rgba(99, 102, 241, 0.15)" },
    ac3: { ext: "AC3", name: "Dolby Digital Audio", cat: "audio", color: "#06b6d4", bg: "rgba(6, 182, 212, 0.15)" },
    alac: { ext: "ALAC", name: "Apple Lossless Audio", cat: "audio", color: "#a855f7", bg: "rgba(168, 85, 247, 0.15)" },
    caf: { ext: "CAF", name: "Apple Core Audio Format", cat: "audio", color: "#38bdf8", bg: "rgba(56, 189, 248, 0.15)" },
    mp2: { ext: "MP2", name: "MPEG Audio Layer II", cat: "audio", color: "#f43f5e", bg: "rgba(244, 63, 94, 0.15)" },

    // Documents
    pdf: { ext: "PDF", name: "Portable Document Format", cat: "document", color: "#ef4444", bg: "rgba(239, 68, 68, 0.15)" },
    docx: { ext: "DOCX", name: "WordprocessingML Document", cat: "document", color: "#2563eb", bg: "rgba(37, 99, 235, 0.15)" },
    md: { ext: "MD", name: "GitHub-Flavored Markdown", cat: "document", color: "#38bdf8", bg: "rgba(56, 189, 248, 0.15)" },
    html: { ext: "HTML", name: "HyperText Markup Language", cat: "document", color: "#f97316", bg: "rgba(249, 115, 22, 0.15)" },
    epub: { ext: "EPUB", name: "Electronic Publication eBook", cat: "document", color: "#10b981", bg: "rgba(16, 185, 129, 0.15)" },
    txt: { ext: "TXT", name: "Plain Text Document", cat: "document", color: "#94a3b8", bg: "rgba(148, 163, 184, 0.15)" },
    rtf: { ext: "RTF", name: "Rich Text Format", cat: "document", color: "#c084fc", bg: "rgba(192, 132, 252, 0.15)" },
    odt: { ext: "ODT", name: "OpenDocument Text Document", cat: "document", color: "#3b82f6", bg: "rgba(59, 130, 246, 0.15)" },
    latex: { ext: "TEX", name: "LaTeX Mathematical Typeset", cat: "document", color: "#8b5cf6", bg: "rgba(139, 92, 246, 0.15)" },
    typst: { ext: "TYP", name: "Typst Modern Typesetting", cat: "document", color: "#06b6d4", bg: "rgba(6, 182, 212, 0.15)" },

    // Data
    xlsx: { ext: "XLSX", name: "Excel Workbook (OpenPyXL)", cat: "data", color: "#22c55e", bg: "rgba(34, 197, 94, 0.15)" },
    csv: { ext: "CSV", name: "Comma-Separated Values", cat: "data", color: "#10b981", bg: "rgba(16, 185, 129, 0.15)" },
    tsv: { ext: "TSV", name: "Tab-Separated Values", cat: "data", color: "#14b8a6", bg: "rgba(20, 184, 166, 0.15)" },
    json: { ext: "JSON", name: "JavaScript Object Notation", cat: "data", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)" },
    yaml: { ext: "YAML", name: "YAML Serialization", cat: "data", color: "#eab308", bg: "rgba(234, 179, 8, 0.15)" },
    xml: { ext: "XML", name: "Extensible Markup Language", cat: "data", color: "#f97316", bg: "rgba(249, 115, 22, 0.15)" },

    // Cross-Medium
    pdf_storyboard: { ext: "STORYBOARD", name: "Video → Storyboard PDF", cat: "cross", color: "#ec4899", bg: "rgba(236, 72, 153, 0.15)" },
    waveform_video: { ext: "WAVEFORM", name: "Audio → Peak Waveform MP4", cat: "cross", color: "#06b6d4", bg: "rgba(6, 182, 212, 0.15)" },
    transcript_md: { ext: "TRANSCRIPT", name: "Audio → Speech Markdown", cat: "cross", color: "#38bdf8", bg: "rgba(56, 189, 248, 0.15)" },
    images_zip: { ext: "IMAGES.ZIP", name: "Doc/MD → Extracted Images & Pages", cat: "cross", color: "#a855f7", bg: "rgba(168, 85, 247, 0.15)" },
  };

  function updateFlowTargetDisplay(targetId) {
    if (!targetId) return;
    const meta = FORMAT_METADATA[targetId] || {
      ext: targetId.toUpperCase(),
      name: `${targetId.toUpperCase()} Output`,
      color: "#38bdf8",
      bg: "rgba(56, 189, 248, 0.15)"
    };

    if (flowTargetExtBadge) {
      flowTargetExtBadge.textContent = "." + meta.ext;
      flowTargetExtBadge.style.color = meta.color;
      flowTargetExtBadge.style.borderColor = meta.color + "55";
      flowTargetExtBadge.style.background = meta.bg;
    }
    if (flowTargetName) {
      flowTargetName.textContent = meta.name;
    }

    // Also update route badge if cross-medium
    const isCross = CROSS_FORMAT_OPTIONS.some((c) => c.id === targetId);
    if (routeBadgeContainer && routeBadgeText) {
      if (isCross) {
        const item = CROSS_FORMAT_OPTIONS.find((c) => c.id === targetId);
        routeBadgeText.textContent = item?.label || targetId;
        routeBadgeContainer.style.display = "flex";
      } else {
        routeBadgeContainer.style.display = "none";
      }
    }
  }

  function renderFormatCards(category = "all", searchQuery = "") {
    if (!formatCardsGrid) return;
    formatCardsGrid.innerHTML = "";

    const query = searchQuery.trim().toLowerCase();
    const fmts = formatsCatalog?.categories || systemInfo?.supported_formats || {
      video: ["mp4", "mkv", "webm", "mov", "avi", "gif", "av1"],
      audio: ["mp3", "wav", "aac", "flac", "m4a", "ogg", "opus"],
      image: ["png", "jpg", "jpeg", "webp", "avif", "gif", "svg"],
      document: ["pdf", "docx", "md", "html", "epub", "txt", "rtf", "odt"],
      data: ["json", "csv", "tsv", "yaml", "yml", "xml", "xlsx", "html"],
    };

    let itemsToRender = [];

    // 1. Cross-medium items
    if (category === "all" || category === "cross") {
      CROSS_FORMAT_OPTIONS.forEach((c) => {
        if (!query || c.label.toLowerCase().includes(query) || c.id.toLowerCase().includes(query)) {
          itemsToRender.push({ id: c.id, label: c.label, cat: "cross" });
        }
      });
    }

    // 2. Standard formats
    const catKeys = category === "all" ? Object.keys(fmts) : (fmts[category] ? [category] : []);
    catKeys.forEach((catKey) => {
      let list = fmts[catKey] || [];
      list.forEach((fmtId) => {
        if (!itemsToRender.some((x) => x.id === fmtId)) {
          const meta = FORMAT_METADATA[fmtId];
          const name = meta?.name || `${fmtId.toUpperCase()} format`;
          if (!query || fmtId.toLowerCase().includes(query) || name.toLowerCase().includes(query)) {
            itemsToRender.push({ id: fmtId, label: name, cat: catKey });
          }
        }
      });
    });

    // Update count in header
    if (formatGridCount) {
      formatGridCount.textContent = `${itemsToRender.length} OUTPUT FORMATS`;
    }

    if (itemsToRender.length === 0) {
      formatCardsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 24px; text-align: center; color: var(--text-dim); font-size: 0.9rem;">
          No matching output formats found for "${query}"
        </div>
      `;
      return;
    }

    const currentSelected = selectTargetFormat ? selectTargetFormat.value : "mp4";

    itemsToRender.forEach((item) => {
      const meta = FORMAT_METADATA[item.id] || {
        ext: item.id.toUpperCase(),
        name: item.label,
        color: "#38bdf8",
        bg: "rgba(56, 189, 248, 0.15)"
      };

      const card = document.createElement("div");
      card.className = `format-card ${item.id === currentSelected ? "selected" : ""}`;
      card.setAttribute("data-format", item.id);
      card.title = `${meta.name} (Click to select)`;
      card.innerHTML = `
        <div class="format-card-badge" style="color: ${meta.color}; background: ${meta.bg}; border: 1px solid ${meta.color}40;">
          .${meta.ext.slice(0, 4)}
        </div>
        <div class="format-card-info">
          <span class="format-card-ext">.${meta.ext}</span>
          <span class="format-card-label" title="${meta.name}">${meta.name}</span>
        </div>
      `;

      card.addEventListener("click", () => {
        if (selectTargetFormat) {
          selectTargetFormat.value = item.id;
        }
        formatCardsGrid.querySelectorAll(".format-card").forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");
        updateFlowTargetDisplay(item.id);
      });

      formatCardsGrid.appendChild(card);
    });

    // Sync flow target display with current format
    updateFlowTargetDisplay(currentSelected);
  }

  function populateFormats(category = "all", searchQuery = "") {
    if (!selectTargetFormat) return;

    const query = searchQuery.trim().toLowerCase();
    const fmts = formatsCatalog?.categories || systemInfo?.supported_formats || {
      video: ["mp4", "mkv", "webm", "mov", "avi", "gif", "av1"],
      audio: ["mp3", "wav", "aac", "flac", "m4a", "ogg", "opus"],
      image: ["png", "jpg", "jpeg", "webp", "avif", "gif", "svg"],
      document: ["pdf", "docx", "md", "html", "epub", "txt", "rtf", "odt"],
      data: ["json", "csv", "tsv", "yaml", "yml", "xml", "xlsx", "html"],
    };

    let crossItems = [...CROSS_FORMAT_OPTIONS];
    if (category !== "all" && category !== "cross") {
      // Filter cross items relevant to selected category
      crossItems = crossItems.filter((c) => c.matchExts.includes(category) || c.id === category);
    }

    if (query) {
      crossItems = crossItems.filter((c) =>
        c.label.toLowerCase().includes(query) || c.id.toLowerCase().includes(query)
      );
    }

    let standardFormats = {};
    const catKeys = category === "all" ? Object.keys(fmts) : (fmts[category] ? [category] : []);

    catKeys.forEach((catKey) => {
      let list = fmts[catKey] || [];
      if (query) {
        list = list.filter((f) => f.toLowerCase().includes(query));
      }
      if (list.length > 0) {
        standardFormats[catKey] = list;
      }
    });

    // Build Option Groups
    let html = "";

    // 1. Cross-Medium Pipelines Group
    if (crossItems.length > 0 && (category === "all" || category === "cross")) {
      html += `<optgroup label="Cross-Medium Pipelines">`;
      crossItems.forEach((item) => {
        html += `<option value="${item.id}">${item.label}</option>`;
      });
      html += `</optgroup>`;
    }

    // 2. Standard Category Groups
    Object.entries(standardFormats).forEach(([catName, list]) => {
      const groupLabel = `${catName.toUpperCase()} Formats (${list.length})`;
      html += `<optgroup label="${groupLabel}">`;
      list.forEach((f) => {
        html += `<option value="${f}">${f.toUpperCase()}</option>`;
      });
      html += `</optgroup>`;
    });

    if (!html) {
      html = `<option value="" disabled>No matching formats found</option>`;
    }

    selectTargetFormat.innerHTML = html;

    // Render interactive visual cards grid (inspired by Convert to it!)
    renderFormatCards(category, searchQuery);
  }

  // Format Select Change Handler (sync visual grid & flow target banner)
  if (selectTargetFormat) {
    selectTargetFormat.addEventListener("change", () => {
      const val = selectTargetFormat.value;
      if (formatCardsGrid) {
        formatCardsGrid.querySelectorAll(".format-card").forEach((c) => {
          if (c.getAttribute("data-format") === val) {
            c.classList.add("selected");
            c.scrollIntoView({ behavior: "smooth", block: "nearest" });
          } else {
            c.classList.remove("selected");
          }
        });
      }
      updateFlowTargetDisplay(val);
    });
  }

  // Format Search Input Handler
  if (formatSearchInput) {
    formatSearchInput.addEventListener("input", (e) => {
      currentSearchQuery = e.target.value;
      if (btnClearSearch) {
        btnClearSearch.style.display = currentSearchQuery ? "block" : "none";
      }
      populateFormats(currentFilterCategory, currentSearchQuery);
    });
  }

  if (btnClearSearch) {
    btnClearSearch.addEventListener("click", () => {
      if (formatSearchInput) formatSearchInput.value = "";
      currentSearchQuery = "";
      btnClearSearch.style.display = "none";
      populateFormats(currentFilterCategory, "");
    });
  }

  // Category Pills Filter Handler
  categoryPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      categoryPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      currentFilterCategory = pill.getAttribute("data-cat");
      populateFormats(currentFilterCategory, currentSearchQuery);
    });
  });

  // Advanced Options Drawer Toggle
  if (btnToggleAdvanced && advancedPanel) {
    btnToggleAdvanced.addEventListener("click", () => {
      const isClosed = advancedPanel.style.display === "none" || !advancedPanel.style.display;
      if (isClosed) {
        advancedPanel.style.display = "block";
        btnToggleAdvanced.classList.add("open");
        btnToggleAdvanced.setAttribute("aria-expanded", "true");
      } else {
        advancedPanel.style.display = "none";
        btnToggleAdvanced.classList.remove("open");
        btnToggleAdvanced.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Reset Advanced Options Button
  if (btnResetAdvanced) {
    btnResetAdvanced.addEventListener("click", () => {
      syncAdvancedOptionsWithDefaults();
      showSettingsToast("Advanced options reset to defaults");
    });
  }

  // Update indicator when user modifies any advanced field
  [
    advCrf, advResolution, advVideoCodec, advAudioBitrate, advFps, advQuality,
    advTrimStart, advTrimDuration, advPlaybackSpeed, advAudioChannels, advLoudnorm,
    advColorFilter, advDpi
  ].forEach((el) => {
    if (el) {
      el.addEventListener("change", updateAdvIndicator);
      el.addEventListener("input", updateAdvIndicator);
    }
  });

  // ---------------------------------------------------------------------------
  // Developer Terminal Console Controller (macOS Studio Style)
  // ---------------------------------------------------------------------------
  const TerminalConsole = {
    isOpen: false,

    init() {
      if (!terminalTitlebar || !terminalConsole) return;

      // Click titlebar to toggle dropdown
      terminalTitlebar.addEventListener("click", (e) => {
        // Prevent toggle if clicking on action buttons or traffic lights
        if (e.target.closest("#btnCopyTerminalLogs") || e.target.closest("#btnClearTerminalLogs") || e.target.closest(".terminal-controls")) {
          return;
        }
        this.toggle();
      });

      // Keyboard accessibility (Enter / Space)
      terminalTitlebar.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          this.toggle();
        }
      });

      // Copy Logs button
      if (btnCopyTerminalLogs) {
        btnCopyTerminalLogs.addEventListener("click", (e) => {
          e.stopPropagation();
          this.copy();
        });
      }

      // Clear Logs button
      if (btnClearTerminalLogs) {
        btnClearTerminalLogs.addEventListener("click", (e) => {
          e.stopPropagation();
          this.clear();
        });
      }

      // macOS Traffic Light Dot Controls
      const dotClose = terminalConsole.querySelector(".term-dot-close");
      const dotMin = terminalConsole.querySelector(".term-dot-min");
      const dotMax = terminalConsole.querySelector(".term-dot-max");

      if (dotClose) {
        dotClose.addEventListener("click", (e) => {
          e.stopPropagation();
          this.close();
        });
      }
      if (dotMin) {
        dotMin.addEventListener("click", (e) => {
          e.stopPropagation();
          this.close();
        });
      }
      if (dotMax) {
        dotMax.addEventListener("click", (e) => {
          e.stopPropagation();
          this.open();
        });
      }
    },

    open() {
      if (!terminalBody || !terminalConsole) return;
      terminalBody.style.display = "block";
      terminalConsole.classList.add("is-open");
      if (terminalTitlebar) terminalTitlebar.setAttribute("aria-expanded", "true");
      this.isOpen = true;
      this.scrollToBottom();
    },

    close() {
      if (!terminalBody || !terminalConsole) return;
      terminalBody.style.display = "none";
      terminalConsole.classList.remove("is-open");
      if (terminalTitlebar) terminalTitlebar.setAttribute("aria-expanded", "false");
      this.isOpen = false;
    },

    toggle() {
      if (this.isOpen || (terminalBody && terminalBody.style.display !== "none")) {
        this.close();
      } else {
        this.open();
      }
    },

    setStatus(type, text) {
      if (!terminalStatusBadge || !terminalStatusText) return;
      terminalStatusBadge.className = "term-status-badge";
      if (type && type !== "ready") {
        terminalStatusBadge.classList.add(type);
      }
      terminalStatusText.textContent = text || type.toUpperCase();
    },

    setProgress(pct, stepDesc) {
      const clamped = Math.max(0, Math.min(100, Math.round(pct)));
      if (termProgressFill) termProgressFill.style.width = `${clamped}%`;
      if (termPctNum) termPctNum.textContent = `${clamped}%`;
      if (stepDesc && termStepDesc) termStepDesc.textContent = stepDesc;

      // Synchronize Titlebar Progress Track (always visible across terminal)
      const titlebarFill = document.getElementById("termTitlebarFill");
      if (titlebarFill) titlebarFill.style.width = `${clamped}%`;

      // Synchronize Bottom Staged Dock Progress Track
      const dockTrack = document.getElementById("dockProgressTrack");
      const dockFill = document.getElementById("dockProgressFill");
      if (dockFill) dockFill.style.width = `${clamped}%`;
      if (dockTrack) {
        dockTrack.style.opacity = clamped > 0 && clamped < 100 ? "1" : "0";
      }

      // Update Convert button label during processing
      if (btnConvertText) {
        if (clamped > 0 && clamped < 100) {
          btnConvertText.textContent = `Converting ${clamped}%...`;
        } else if (clamped >= 100) {
          btnConvertText.textContent = "Done";
          setTimeout(() => {
            if (btnConvertText) btnConvertText.textContent = "Convert";
          }, 2500);
        }
      }
    },

    escapeHtml(str) {
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    },

    formatLine(line) {
      const escaped = this.escapeHtml(line);
      const tagged = escaped
        .replace(/\[INIT\]/g, '<span class="log-token-init">[INIT]</span>')
        .replace(/\[ROUTE\]/g, '<span class="log-token-route">[ROUTE]</span>')
        .replace(/\[EXEC\]/g, '<span class="log-token-exec">[EXEC]</span>')
        .replace(/\[INFO\]/g, '<span class="log-token-info">[INFO]</span>')
        .replace(/\[DONE\]/g, '<span class="log-token-done">[DONE]</span>')
        .replace(/\[WARN\]/g, '<span class="log-token-warn">[WARN]</span>')
        .replace(/\[ERROR\]/g, '<span class="log-token-error">[ERROR]</span>')
        .replace(/^(\d{4}-\d{2}-\d{2}T[\d:.]+Z?)/g, '<span class="log-token-time">$1</span>');

      return `<div class="log-line">${tagged}</div>`;
    },

    appendLog(line) {
      if (!terminalStream) return;
      const div = document.createElement("div");
      div.className = "log-line";
      const escaped = this.escapeHtml(line);
      div.innerHTML = escaped
        .replace(/\[INIT\]/g, '<span class="log-token-init">[INIT]</span>')
        .replace(/\[ROUTE\]/g, '<span class="log-token-route">[ROUTE]</span>')
        .replace(/\[EXEC\]/g, '<span class="log-token-exec">[EXEC]</span>')
        .replace(/\[INFO\]/g, '<span class="log-token-info">[INFO]</span>')
        .replace(/\[DONE\]/g, '<span class="log-token-done">[DONE]</span>')
        .replace(/\[WARN\]/g, '<span class="log-token-warn">[WARN]</span>')
        .replace(/\[ERROR\]/g, '<span class="log-token-error">[ERROR]</span>')
        .replace(/^(\d{4}-\d{2}-\d{2}T[\d:.]+Z?)/g, '<span class="log-token-time">$1</span>');
      terminalStream.appendChild(div);
      this.scrollToBottom();
    },

    setLogs(logArray) {
      if (!terminalStream) return;
      terminalStream.innerHTML = "";
      if (Array.isArray(logArray)) {
        const html = logArray.map((l) => this.formatLine(l)).join("");
        terminalStream.innerHTML = html;
      }
      this.scrollToBottom();
    },

    clear() {
      if (!terminalStream) return;
      terminalStream.innerHTML = `<div class="log-line"><span class="log-token-init">[INIT]</span> Console cleared. Ready for next command.</div>`;
    },

    reset() {
      this.setProgress(0, "Awaiting conversion trigger...");
      this.setStatus("ready", "READY");
      const dockTrack = document.getElementById("dockProgressTrack");
      if (dockTrack) dockTrack.style.opacity = "0";
      const titlebarFill = document.getElementById("termTitlebarFill");
      if (titlebarFill) titlebarFill.style.width = "0%";
      if (btnConvertText) btnConvertText.textContent = "Convert";
    },

    scrollToBottom() {
      if (!terminalStream) return;
      terminalStream.scrollTop = terminalStream.scrollHeight;
    },

    async copy() {
      if (!terminalStream) return;
      const text = terminalStream.innerText || terminalStream.textContent || "";
      try {
        await navigator.clipboard.writeText(text);
        if (btnCopyTerminalLogs) {
          const original = btnCopyTerminalLogs.innerHTML;
          btnCopyTerminalLogs.innerHTML = `<span>Copied!</span>`;
          setTimeout(() => {
            btnCopyTerminalLogs.innerHTML = original;
          }, 1800);
        }
      } catch (err) {
        console.warn("Failed to copy logs to clipboard:", err);
      }
    }
  };

  // Initialize Terminal Console
  TerminalConsole.init();

  // ---------------------------------------------------------------------------
  // Full-Page Window Drag & Drop (Inspired by p2r3/convert)
  // ---------------------------------------------------------------------------
  let windowDragCounter = 0;

  window.addEventListener("dragenter", (e) => {
    e.preventDefault();
    windowDragCounter++;
    if (fullPageDropOverlay) fullPageDropOverlay.classList.add("active");
  });

  window.addEventListener("dragleave", (e) => {
    e.preventDefault();
    windowDragCounter--;
    if (windowDragCounter <= 0) {
      windowDragCounter = 0;
      if (fullPageDropOverlay) fullPageDropOverlay.classList.remove("active");
    }
  });

  window.addEventListener("dragover", (e) => {
    e.preventDefault();
  });

  window.addEventListener("drop", (e) => {
    e.preventDefault();
    windowDragCounter = 0;
    if (fullPageDropOverlay) fullPageDropOverlay.classList.remove("active");

    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      // Auto-switch to Converter tab
      const tabBtn = document.getElementById("btnTabUniversal");
      if (tabBtn) tabBtn.click();
      handleUniversalFiles(Array.from(e.dataTransfer.files));
    }
  });

  // Universal Dropzone & File Input Setup
  function setupUniversalDragDrop() {
    if (!dropzoneUniversal) return;

    dropzoneUniversal.addEventListener("click", () => fileInputUniversal.click());

    fileInputUniversal.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleUniversalFiles(Array.from(e.target.files));
      }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      dropzoneUniversal.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzoneUniversal.classList.add("hot");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzoneUniversal.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzoneUniversal.classList.remove("hot");
      });
    });

    dropzoneUniversal.addEventListener("drop", (e) => {
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleUniversalFiles(Array.from(e.dataTransfer.files));
      }
    });
  }

  function handleUniversalFiles(files) {
    if (!files || files.length === 0) return;

    // Append files (avoid exact duplicates by name and size)
    files.forEach((f) => {
      if (!stagedUniversalFiles.some((x) => x.name === f.name && x.size === f.size)) {
        stagedUniversalFiles.push(f);
      }
    });

    updateUniversalStagedUI();
  }

  function renderDockStagedChips() {
    if (!dockStagedChips) return;
    dockStagedChips.innerHTML = "";

    stagedUniversalFiles.forEach((file, idx) => {
      const chip = document.createElement("div");
      chip.className = "dock-chip";
      chip.innerHTML = `
        <span class="dock-chip-icon">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
        </span>
        <span class="dock-chip-name" title="${file.name}">${file.name}</span>
        <span class="dock-chip-size">${formatBytes(file.size)}</span>
        <button type="button" class="dock-chip-remove" data-idx="${idx}" title="Remove file">&times;</button>
      `;
      dockStagedChips.appendChild(chip);
    });

    dockStagedChips.querySelectorAll(".dock-chip-remove").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const idx = parseInt(btn.getAttribute("data-idx"), 10);
        stagedUniversalFiles.splice(idx, 1);
        updateUniversalStagedUI();
      });
    });
  }

  function updateUniversalStagedUI() {
    if (stagedUniversalFiles.length === 0) {
      if (universalHomeHero) universalHomeHero.style.display = "block";
      if (universalControls) universalControls.style.display = "none";
      if (dockStagedChips) dockStagedChips.innerHTML = "";
      if (smartActionsHub) smartActionsHub.style.display = "none";
      return;
    }

    if (universalHomeHero) universalHomeHero.style.display = "none";
    if (universalControls) universalControls.style.display = "flex";
    if (universalResult) universalResult.style.display = "none";
    if (routeBadgeContainer) routeBadgeContainer.style.display = "none";
    if (mediaPreviewContainer) mediaPreviewContainer.style.display = "none";
    TerminalConsole.reset();
    TerminalConsole.close();

    renderDockStagedChips();

    const isSingle = stagedUniversalFiles.length === 1;

    if (isSingle) {
      const file = stagedUniversalFiles[0];
      const ext = file.name.split(".").pop().toLowerCase();
      if (singleFileBanner) singleFileBanner.style.display = "flex";
      if (multiFileQueueContainer) multiFileQueueContainer.style.display = "none";

      if (selectedFileName) selectedFileName.textContent = file.name;
      if (selectedFileSize) selectedFileSize.textContent = formatBytes(file.size);
      if (selectedFileExt) selectedFileExt.textContent = ext.toUpperCase();
      if (btnConvertText) btnConvertText.textContent = "Convert";

      // Detect category and auto-select format using user's persistent preferences
      const category = getFileCategory(file.name);
      currentFilterCategory = category;

      // Sync category pills
      categoryPills.forEach((p) => {
        if (p.getAttribute("data-cat") === category) {
          p.classList.add("active");
        } else {
          p.classList.remove("active");
        }
      });

      // Auto-select smart format
      if (category === "video" && userSettings.defaultVideo) {
        selectTargetFormat.value = userSettings.defaultVideo;
      } else if (category === "audio" && userSettings.defaultAudio) {
        selectTargetFormat.value = userSettings.defaultAudio;
      } else if (category === "image" && userSettings.defaultImage) {
        selectTargetFormat.value = userSettings.defaultImage;
      } else if (category === "document" && userSettings.defaultDoc) {
        selectTargetFormat.value = userSettings.defaultDoc;
      } else if (category === "data") {
        selectTargetFormat.value = ext === "json" ? "csv" : "json";
      }

      populateFormats(category, currentSearchQuery);
      updateFlowTargetDisplay(selectTargetFormat.value);
      renderSmartActions(file);
    } else {
      // Multi-file Queue View
      if (singleFileBanner) singleFileBanner.style.display = "flex";
      if (multiFileQueueContainer) multiFileQueueContainer.style.display = "block";
      if (multiFileCount) multiFileCount.textContent = `${stagedUniversalFiles.length} files`;
      if (selectedFileExt) selectedFileExt.textContent = `${stagedUniversalFiles.length} FILES`;
      if (selectedFileName) selectedFileName.textContent = `Batch conversion queue (${stagedUniversalFiles.length} items)`;
      const totalBytes = stagedUniversalFiles.reduce((acc, f) => acc + f.size, 0);
      if (selectedFileSize) selectedFileSize.textContent = formatBytes(totalBytes);
      if (btnConvertText) btnConvertText.textContent = `Convert All (${stagedUniversalFiles.length}) & Download .ZIP`;
      if (smartActionsHub) smartActionsHub.style.display = "none";

      renderMultiFileList();
      populateFormats(currentFilterCategory, currentSearchQuery);
      updateFlowTargetDisplay(selectTargetFormat.value);
    }
  }

  function renderMultiFileList() {
    if (!multiFileList) return;
    multiFileList.innerHTML = "";

    stagedUniversalFiles.forEach((f, idx) => {
      const ext = f.name.split(".").pop().toUpperCase();
      const item = document.createElement("div");
      item.className = "queue-item";
      item.innerHTML = `
        <div class="queue-item-info">
          <span class="queue-item-ext">${ext}</span>
          <span class="queue-item-name" title="${f.name}">${f.name}</span>
          <span class="queue-item-size">(${formatBytes(f.size)})</span>
        </div>
        <button class="btn-remove-queue-item" data-idx="${idx}" title="Remove file">&times;</button>
      `;
      multiFileList.appendChild(item);
    });

    // Wire individual remove buttons
    multiFileList.querySelectorAll(".btn-remove-queue-item").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const idx = parseInt(e.target.getAttribute("data-idx"), 10);
        stagedUniversalFiles.splice(idx, 1);
        updateUniversalStagedUI();
      });
    });
  }

  // Clear / Back Handlers (Returns to VERT Hero Home View)
  if (btnClearUniversal) {
    btnClearUniversal.addEventListener("click", () => {
      stagedUniversalFiles = [];
      fileInputUniversal.value = "";
      updateUniversalStagedUI();
    });
  }

  if (btnClearMultiQueue) {
    btnClearMultiQueue.addEventListener("click", () => {
      stagedUniversalFiles = [];
      fileInputUniversal.value = "";
      updateUniversalStagedUI();
    });
  }

  // Bottom Dock Add More button
  if (btnDockAddMore && fileInputUniversal) {
    btnDockAddMore.addEventListener("click", () => {
      fileInputUniversal.click();
    });
  }

  // Home Screen VERT Supports Cards Click Handler
  document.querySelectorAll(".support-card[data-cat-trigger]").forEach((card) => {
    card.addEventListener("click", () => {
      const cat = card.getAttribute("data-cat-trigger");
      currentFilterCategory = cat;
      categoryPills.forEach((p) => {
        if (p.getAttribute("data-cat") === cat) {
          p.classList.add("active");
        } else {
          p.classList.remove("active");
        }
      });
      if (fileInputUniversal) fileInputUniversal.click();
    });
  });

  // ---------------------------------------------------------------------------
  // Studio Pro: Smart Actions Hub & Media Telemetry Inspector
  // ---------------------------------------------------------------------------
  function selectFormatProgrammatically(formatId) {
    if (selectTargetFormat) selectTargetFormat.value = formatId;
    updateFlowTargetDisplay(formatId);
    if (formatCardsGrid) {
      formatCardsGrid.querySelectorAll(".format-card").forEach((c) => {
        if (c.getAttribute("data-id") === formatId) {
          c.classList.add("selected");
          c.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } else {
          c.classList.remove("selected");
        }
      });
    }
  }

  function renderSmartActions(file) {
    if (!smartActionsHub || !smartActionsChips) return;
    const ext = file.name.split(".").pop().toLowerCase();
    const cat = getFileCategory(file.name);

    if (smartHubTargetName) {
      smartHubTargetName.textContent = file.name;
    }

    smartActionsChips.innerHTML = "";
    smartActionsHub.style.display = "block";

    let actions = [];

    if (cat === "video") {
      actions = [
        {
          label: "Extract MP3 (320k)",
          tag: "Audio",
          apply: () => {
            selectFormatProgrammatically("mp3");
            if (advAudioBitrate) advAudioBitrate.value = "320k";
            updateAdvIndicator();
            TerminalConsole.appendLog(`[RECIPE] Applied Extract MP3 320k for ${file.name}`);
          }
        },
        {
          label: "Create 2-Pass GIF",
          tag: "Animation",
          apply: () => {
            selectFormatProgrammatically("gif");
            if (advResolution) advResolution.value = "720p";
            if (advFps) advFps.value = "24";
            updateAdvIndicator();
            TerminalConsole.appendLog(`[RECIPE] Applied 2-Pass Lanczos GIF for ${file.name}`);
          }
        },
        {
          label: "PDF Storyboard Grid",
          tag: "Poppler",
          apply: () => {
            selectFormatProgrammatically("storyboard_pdf");
            TerminalConsole.appendLog(`[RECIPE] Applied PDF Storyboard contact-sheet recipe for ${file.name}`);
          }
        },
        {
          label: "Web FastStart MP4",
          tag: "H.264",
          apply: () => {
            selectFormatProgrammatically("mp4");
            if (advVideoCodec) advVideoCodec.value = "libx264";
            if (advCrf) advCrf.value = "22";
            updateAdvIndicator();
            TerminalConsole.appendLog(`[RECIPE] Applied Web FastStart H.264 for ${file.name}`);
          }
        }
      ];
    } else if (cat === "audio") {
      actions = [
        {
          label: "Lossless FLAC",
          tag: "Hi-Res",
          apply: () => {
            selectFormatProgrammatically("flac");
            TerminalConsole.appendLog(`[RECIPE] Applied Studio Lossless FLAC recipe for ${file.name}`);
          }
        },
        {
          label: "EBU Loudnorm MP3",
          tag: "Broadcast",
          apply: () => {
            selectFormatProgrammatically("mp3");
            if (advAudioBitrate) advAudioBitrate.value = "320k";
            if (advLoudnorm) advLoudnorm.checked = true;
            updateAdvIndicator();
            TerminalConsole.appendLog(`[RECIPE] Applied EBU R128 Loudness Normalization recipe for ${file.name}`);
          }
        },
        {
          label: "Voice Waveform MP4",
          tag: "Visual",
          apply: () => {
            selectFormatProgrammatically("waveform_mp4");
            TerminalConsole.appendLog(`[RECIPE] Applied High-Res Audio Waveform Visualizer recipe for ${file.name}`);
          }
        },
        {
          label: "Clean 48kHz WAV",
          tag: "PCM",
          apply: () => {
            selectFormatProgrammatically("wav");
            TerminalConsole.appendLog(`[RECIPE] Applied Uncompressed PCM WAV recipe for ${file.name}`);
          }
        }
      ];
    } else if (cat === "image") {
      actions = [
        {
          label: "Modern WebP (85%)",
          tag: "Next-Gen",
          apply: () => {
            selectFormatProgrammatically("webp");
            if (advQuality) advQuality.value = "85";
            updateAdvIndicator();
            TerminalConsole.appendLog(`[RECIPE] Applied Next-Gen WebP 85% compression for ${file.name}`);
          }
        },
        {
          label: "Grayscale B&W",
          tag: "Filter",
          apply: () => {
            selectFormatProgrammatically("png");
            if (advColorFilter) advColorFilter.value = "grayscale";
            updateAdvIndicator();
            TerminalConsole.appendLog(`[RECIPE] Applied High-Dynamic Range Grayscale filter for ${file.name}`);
          }
        },
        {
          label: "Favicon (.ico)",
          tag: "Icon",
          apply: () => {
            selectFormatProgrammatically("ico");
            TerminalConsole.appendLog(`[RECIPE] Applied Multi-Resolution Favicon recipe for ${file.name}`);
          }
        },
        {
          label: "Print PDF",
          tag: "Vector",
          apply: () => {
            selectFormatProgrammatically("pdf");
            TerminalConsole.appendLog(`[RECIPE] Applied Lossless Image-to-PDF packaging for ${file.name}`);
          }
        }
      ];
    } else if (cat === "document") {
      actions = [
        {
          label: "Extract Images (.zip)",
          tag: "Poppler",
          apply: () => {
            selectFormatProgrammatically("images_zip");
            TerminalConsole.appendLog(`[RECIPE] Applied Document Embedded Images Extractor recipe for ${file.name}`);
          }
        },
        {
          label: "Render Pages PNG (300 DPI)",
          tag: "High-Res",
          apply: () => {
            selectFormatProgrammatically("png");
            if (advDpi) advDpi.value = "300";
            updateAdvIndicator();
            TerminalConsole.appendLog(`[RECIPE] Applied 300 DPI Vector Page Rasterizer recipe for ${file.name}`);
          }
        },
        {
          label: "Markdown OCR Studio",
          tag: "MarkItDown",
          apply: () => {
            const btnTab = document.getElementById("btnTabMarkdown");
            if (btnTab) {
              btnTab.click();
              stagedMarkdownFiles = [file];
              syncMarkdownState();
              TerminalConsole.appendLog(`[RECIPE] Forwarded ${file.name} to MarkItDown OCR Studio`);
            }
          }
        }
      ];
      if (ext === "pdf") {
        actions.push({
          label: "Split / Merge in PDF Studio",
          tag: "Poppler",
          apply: () => {
            const btnTab = document.getElementById("btnTabPdf");
            if (btnTab) {
              btnTab.click();
              stagePdfSplit(file);
            }
          }
        });
      }
    } else if (cat === "data") {
      actions = [
        {
          label: "Excel Spreadsheet (.xlsx)",
          tag: "OpenPyXL",
          apply: () => {
            selectFormatProgrammatically("xlsx");
            TerminalConsole.appendLog(`[RECIPE] Applied OpenPyXL Excel Workbook conversion for ${file.name}`);
          }
        },
        {
          label: "Clean CSV",
          tag: "Data",
          apply: () => {
            selectFormatProgrammatically("csv");
            TerminalConsole.appendLog(`[RECIPE] Applied Clean Delimited CSV export for ${file.name}`);
          }
        },
        {
          label: "Pretty JSON",
          tag: "Structure",
          apply: () => {
            selectFormatProgrammatically("json");
            TerminalConsole.appendLog(`[RECIPE] Applied Structured JSON formatting for ${file.name}`);
          }
        },
        {
          label: "HTML Data Table",
          tag: "Web",
          apply: () => {
            selectFormatProgrammatically("html");
            TerminalConsole.appendLog(`[RECIPE] Applied Styled HTML Table rendering for ${file.name}`);
          }
        }
      ];
    }

    actions.forEach((act) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "smart-chip";
      chip.innerHTML = `
        <span class="smart-chip-icon">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polyline>
          </svg>
        </span>
        <span>${act.label}</span>
        <span class="smart-chip-tag">${act.tag}</span>
      `;
      chip.addEventListener("click", () => {
        act.apply();
        chip.style.borderColor = "var(--blue-accent)";
        chip.style.background = "rgba(56, 189, 248, 0.2)";
        setTimeout(() => {
          chip.style.borderColor = "";
          chip.style.background = "";
        }, 1200);
      });
      smartActionsChips.appendChild(chip);
    });
  }

  // Media Telemetry Inspector Logic
  async function openMediaInspector(file) {
    if (!mediaInspectorModal) return;
    mediaInspectorModal.style.display = "flex";
    if (inspectorLoading) inspectorLoading.style.display = "flex";
    if (inspectorContent) inspectorContent.style.display = "none";
    if (inspectorModalTitle) inspectorModalTitle.textContent = `Inspector · ${file.name}`;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/inspect-media", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Probe failed with status ${res.status}`);
      }

      const data = await res.json();
      renderInspectorData(data);
    } catch (err) {
      if (inspectorStatsGrid) {
        inspectorStatsGrid.innerHTML = `
          <div class="stat-tile" style="grid-column: 1 / -1; border-color: var(--rose-accent);">
            <div class="stat-tile-label" style="color: var(--rose-accent);">Inspection Error</div>
            <div class="stat-tile-val" style="font-size: 0.9rem;">${err.message || "Failed to inspect file telemetry"}</div>
          </div>
        `;
      }
      if (inspectorStreamsList) inspectorStreamsList.innerHTML = "";
      if (inspectorRawCode) inspectorRawCode.textContent = "";
      if (inspectorLoading) inspectorLoading.style.display = "none";
      if (inspectorContent) inspectorContent.style.display = "block";
    }
  }

  function renderInspectorData(data) {
    if (inspectorCategoryBadge) {
      inspectorCategoryBadge.textContent = (data.category || "PROBE").toUpperCase();
    }

    if (inspectorStatsGrid) {
      const tiles = [
        { label: "Detected Format", val: (data.format || "Unknown").toUpperCase() },
        { label: "File Size", val: formatBytes(data.size_bytes || 0) },
      ];

      if (data.duration) {
        tiles.push({ label: "Duration", val: `${Number(data.duration).toFixed(1)}s` });
      }
      if (data.pages) {
        tiles.push({ label: "Page Count", val: `${data.pages} page${data.pages > 1 ? "s" : ""}` });
      }
      if (data.words) {
        tiles.push({ label: "Word Count", val: `${data.words.toLocaleString()} words` });
      }
      if (data.streams && data.streams.length > 0) {
        tiles.push({ label: "Hardware Streams", val: `${data.streams.length} detected` });
      }
      if (data.general && data.general.bit_rate) {
        const kbps = Math.round(data.general.bit_rate / 1000);
        tiles.push({ label: "Overall Bitrate", val: `${kbps} kbps` });
      }

      inspectorStatsGrid.innerHTML = tiles.map(t => `
        <div class="stat-tile">
          <div class="stat-tile-label">${t.label}</div>
          <div class="stat-tile-val" title="${t.val}">${t.val}</div>
        </div>
      `).join("");
    }

    if (inspectorStreamsList) {
      if (data.streams && data.streams.length > 0) {
        inspectorStreamsList.innerHTML = data.streams.map(s => {
          const type = (s.type || "STREAM").toUpperCase();
          const codec = (s.codec || "unknown").toUpperCase();
          const details = [];
          if (s.resolution) details.push(s.resolution);
          if (s.fps) details.push(`${s.fps} FPS`);
          if (s.sample_rate) details.push(`${s.sample_rate} Hz`);
          if (s.channels) details.push(`${s.channels} Ch`);
          if (s.bitrate) details.push(`${Math.round(s.bitrate / 1000)} kbps`);
          if (s.pix_fmt) details.push(s.pix_fmt);

          return `
            <div class="stream-item-card">
              <div class="stream-item-left">
                <span class="stream-type-pill">${type}</span>
                <div>
                  <div class="stream-info-main">${codec}</div>
                  <div class="stream-info-sub">Index #${s.index !== undefined ? s.index : 0}</div>
                </div>
              </div>
              <div class="stream-badges-row">
                ${details.map(d => `<span class="stream-detail-badge">${d}</span>`).join("")}
              </div>
            </div>
          `;
        }).join("");
      } else if (data.pdf_info && Object.keys(data.pdf_info).length > 0) {
        const doc = data.pdf_info;
        const details = [];
        if (doc.title) details.push(`Title: ${doc.title}`);
        if (doc.author) details.push(`Author: ${doc.author}`);
        if (doc.producer) details.push(`Producer: ${doc.producer}`);
        if (doc.page_size) details.push(`Page Size: ${doc.page_size}`);

        inspectorStreamsList.innerHTML = `
          <div class="stream-item-card">
            <div class="stream-item-left">
              <span class="stream-type-pill">DOC</span>
              <div>
                <div class="stream-info-main">${doc.title || "Document Stream"}</div>
                <div class="stream-info-sub">${doc.author ? 'By ' + doc.author : 'No author metadata'}</div>
              </div>
            </div>
            <div class="stream-badges-row">
              ${details.map(d => `<span class="stream-detail-badge">${d}</span>`).join("")}
            </div>
          </div>
        `;
      } else {
        inspectorStreamsList.innerHTML = `<p style="font-size: 0.82rem; color: var(--text-dim); padding: 8px 0;">No low-level container streams detected.</p>`;
      }
    }

    if (inspectorRawCode) {
      inspectorRawCode.textContent = JSON.stringify(data, null, 2);
    }

    if (inspectorLoading) inspectorLoading.style.display = "none";
    if (inspectorContent) inspectorContent.style.display = "block";
  }

  // Standalone Inspector Tab: drop/browse a file and probe it directly
  const dropzoneInspector = document.getElementById("dropzoneInspector");
  const fileInputInspector = document.getElementById("fileInputInspector");
  const btnBrowseInspector = document.getElementById("btnBrowseInspector");

  if (dropzoneInspector && fileInputInspector) {
    dropzoneInspector.addEventListener("click", () => fileInputInspector.click());
    dropzoneInspector.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzoneInspector.classList.add("drag-over");
    });
    dropzoneInspector.addEventListener("dragleave", () => dropzoneInspector.classList.remove("drag-over"));
    dropzoneInspector.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzoneInspector.classList.remove("drag-over");
      if (e.dataTransfer.files && e.dataTransfer.files[0]) openMediaInspector(e.dataTransfer.files[0]);
    });
    fileInputInspector.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) openMediaInspector(e.target.files[0]);
      fileInputInspector.value = "";
    });
  }

  if (btnBrowseInspector && fileInputInspector) {
    btnBrowseInspector.addEventListener("click", (e) => {
      e.stopPropagation();
      fileInputInspector.click();
    });
  }

  // Wire Inspect Button & Modal Events
  if (btnInspectStagedFile) {
    btnInspectStagedFile.addEventListener("click", () => {
      if (stagedUniversalFiles.length > 0) {
        openMediaInspector(stagedUniversalFiles[0]);
      } else if (fileInputUniversal) {
        fileInputUniversal.click();
      }
    });
  }

  if (btnCloseInspector) {
    btnCloseInspector.addEventListener("click", () => {
      if (mediaInspectorModal) mediaInspectorModal.style.display = "none";
    });
  }

  if (btnCloseInspectorFooter) {
    btnCloseInspectorFooter.addEventListener("click", () => {
      if (mediaInspectorModal) mediaInspectorModal.style.display = "none";
    });
  }

  if (mediaInspectorModal) {
    mediaInspectorModal.addEventListener("click", (e) => {
      if (e.target === mediaInspectorModal) {
        mediaInspectorModal.style.display = "none";
      }
    });
  }

  if (btnCopyInspectorJson && inspectorRawCode) {
    btnCopyInspectorJson.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(inspectorRawCode.textContent);
        btnCopyInspectorJson.textContent = "Copied JSON!";
        setTimeout(() => (btnCopyInspectorJson.textContent = "Copy Telemetry JSON"), 2000);
      } catch (err) {
        alert("Copy failed");
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Universal Conversion Execution (Single & Multi-File Batch)
  // ---------------------------------------------------------------------------
  if (btnConvertUniversal) {
    btnConvertUniversal.addEventListener("click", async () => {
      if (stagedUniversalFiles.length === 0) return;

      btnConvertUniversal.disabled = true;
      TerminalConsole.open();
      TerminalConsole.clear();
      TerminalConsole.setStatus("running", "RUNNING · 15%");
      const simdName = systemInfo?.acceleration?.simd;
      TerminalConsole.setProgress(15, `Initializing ${systemInfo?.cores_logical || "all available"} cores${simdName ? ` (${simdName} SIMD)` : ""}...`);
      TerminalConsole.appendLog(`[INIT] Conversion task initiated with ${systemInfo?.cores_logical || "all available"} hardware threads`);
      universalResult.style.display = "none";
      if (routeBadgeContainer) routeBadgeContainer.style.display = "none";
      if (mediaPreviewContainer) mediaPreviewContainer.style.display = "none";

      const targetFormat = selectTargetFormat.value || "mp4";
      const isBatch = stagedUniversalFiles.length > 1;
      let progressTicker = null;

      // Revoke previous blob URL if exists
      if (currentMediaBlobUrl) {
        URL.revokeObjectURL(currentMediaBlobUrl);
        currentMediaBlobUrl = null;
      }

      try {
        if (!isBatch) {
          // Single file conversion
          const file = stagedUniversalFiles[0];
          const formData = new FormData();
          formData.append("file", file);
          formData.append("target_format", targetFormat);

          // Append Advanced Options
          if (advCrf?.value) formData.append("crf", advCrf.value);
          if (advResolution?.value && advResolution.value !== "original") formData.append("resolution", advResolution.value);
          if (advVideoCodec?.value) formData.append("video_codec", advVideoCodec.value);
          if (advAudioBitrate?.value) formData.append("audio_bitrate", advAudioBitrate.value);
          if (advFps?.value && advFps.value !== "original") formData.append("fps", advFps.value);
          if (advQuality?.value) formData.append("quality", advQuality.value);
          if (advTrimStart?.value) formData.append("trim_start", advTrimStart.value.trim());
          if (advTrimDuration?.value) formData.append("trim_duration", advTrimDuration.value.trim());
          if (advLoudnorm?.checked) formData.append("loudnorm", "true");
          if (advAudioChannels?.value) formData.append("audio_channels", advAudioChannels.value);
          if (advPlaybackSpeed?.value && advPlaybackSpeed.value !== "1.0") formData.append("playback_speed", advPlaybackSpeed.value);
          if (advColorFilter?.value) formData.append("color_filter", advColorFilter.value);
          if (advDpi?.value) formData.append("dpi", advDpi.value);

          let progressVal = 40;
          TerminalConsole.setProgress(progressVal, `Transcoding ${file.name} to ${targetFormat.toUpperCase()}...`);
          TerminalConsole.setStatus("running", `ENCODING · ${progressVal}%`);
          TerminalConsole.appendLog(`[EXEC] Transcoding ${file.name} → ${targetFormat.toUpperCase()} using hardware acceleration`);

          progressTicker = setInterval(() => {
            if (progressVal < 90) {
              progressVal += Math.random() > 0.4 ? 3 : 2;
              if (progressVal > 90) progressVal = 90;
              TerminalConsole.setProgress(progressVal, `Processing ${file.name} (${progressVal}%)...`);
              TerminalConsole.setStatus("running", `ENCODING · ${progressVal}%`);
            }
          }, 450);

          const res = await fetch("/api/convert-universal", {
            method: "POST",
            body: formData,
          });

          if (progressTicker) {
            clearInterval(progressTicker);
            progressTicker = null;
          }

          if (!res.ok) {
            const errJson = await res.json().catch(() => ({ detail: "Conversion failed" }));
            throw new Error(errJson.detail || "Conversion error");
          }

          TerminalConsole.setProgress(95, "Receiving encoded media buffer...");
          TerminalConsole.setStatus("running", "FINALIZING · 95%");
          const blob = await res.blob();
          TerminalConsole.setProgress(100, "Conversion complete!");
          TerminalConsole.setStatus("completed", "COMPLETED · 100%");

          // Extract response headers
          const contentDisposition = res.headers.get("Content-Disposition");
          let filename = `${file.name.split(".")[0]}.${targetFormat}`;
          if (contentDisposition && contentDisposition.includes("filename=")) {
            filename = contentDisposition.split("filename=")[1].replace(/"/g, "");
          }

          const routeHeader = res.headers.get("X-Conversion-Route");
          const logsHeader = res.headers.get("X-Conversion-Logs");

          const routeStr = routeHeader ? decodeURIComponent(routeHeader) : `${file.name.split('.').pop().toUpperCase()} → ${targetFormat.toUpperCase()}`;
          let logEntries = [];
          try {
            if (logsHeader) logEntries = JSON.parse(decodeURIComponent(logsHeader));
          } catch (e) {
            logEntries = logsHeader ? [logsHeader] : [];
          }

          currentMediaBlobUrl = URL.createObjectURL(blob);
          btnDownloadUniversal.href = currentMediaBlobUrl;
          btnDownloadUniversal.download = filename;
          universalResultTitle.textContent = `Successfully converted to ${filename} (${formatBytes(blob.size)})`;
          universalResult.style.display = "flex";

          // Display Traversion Route Badge
          if (routeBadgeContainer && routeBadgeText) {
            routeBadgeText.textContent = routeStr;
            routeBadgeContainer.style.display = "flex";
          }

          // Render In-Browser Media Preview
          renderMediaPreview(filename, blob, currentMediaBlobUrl);

          // Populate Terminal Console stream
          if (logEntries.length > 0) {
            TerminalConsole.setLogs(logEntries);
          } else {
            TerminalConsole.appendLog(`[DONE] Conversion succeeded: ${filename} (${formatBytes(blob.size)})`);
          }

          // Auto-download if enabled in persistent user settings
          if (userSettings.autoDownload) {
            btnDownloadUniversal.click();
          }
        } else {
          // Multi-File Batch Conversion
          TerminalConsole.setProgress(35, `Staging ${stagedUniversalFiles.length} files for parallel batch transform...`);
          TerminalConsole.setStatus("running", "BATCH STAGING · 35%");
          TerminalConsole.appendLog(`[EXEC] Multi-file batch dispatching: ${stagedUniversalFiles.length} items`);

          const formData = new FormData();
          stagedUniversalFiles.forEach((f) => formData.append("files", f));
          formData.append("target_format", targetFormat);

          if (advCrf?.value) formData.append("crf", advCrf.value);
          if (advResolution?.value && advResolution.value !== "original") formData.append("resolution", advResolution.value);
          if (advVideoCodec?.value) formData.append("video_codec", advVideoCodec.value);
          if (advAudioBitrate?.value) formData.append("audio_bitrate", advAudioBitrate.value);
          if (advFps?.value && advFps.value !== "original") formData.append("fps", advFps.value);
          if (advQuality?.value) formData.append("quality", advQuality.value);
          if (advTrimStart?.value) formData.append("trim_start", advTrimStart.value.trim());
          if (advTrimDuration?.value) formData.append("trim_duration", advTrimDuration.value.trim());
          if (advLoudnorm?.checked) formData.append("loudnorm", "true");
          if (advAudioChannels?.value) formData.append("audio_channels", advAudioChannels.value);
          if (advPlaybackSpeed?.value && advPlaybackSpeed.value !== "1.0") formData.append("playback_speed", advPlaybackSpeed.value);
          if (advColorFilter?.value) formData.append("color_filter", advColorFilter.value);
          if (advDpi?.value) formData.append("dpi", advDpi.value);

          let batchVal = 40;
          TerminalConsole.setProgress(batchVal, `Parallel batch processing across CPU cores...`);
          TerminalConsole.setStatus("running", `PROCESSING · ${batchVal}%`);

          progressTicker = setInterval(() => {
            if (batchVal < 90) {
              batchVal += Math.random() > 0.4 ? 4 : 2;
              if (batchVal > 90) batchVal = 90;
              TerminalConsole.setProgress(batchVal, `Batch processing ${stagedUniversalFiles.length} files (${batchVal}%)...`);
              TerminalConsole.setStatus("running", `PROCESSING · ${batchVal}%`);
            }
          }, 450);

          const res = await fetch("/api/convert-universal-batch", {
            method: "POST",
            body: formData,
          });

          if (progressTicker) {
            clearInterval(progressTicker);
            progressTicker = null;
          }

          if (!res.ok) {
            const errJson = await res.json().catch(() => ({ detail: "Batch conversion failed" }));
            throw new Error(errJson.detail || "Batch error");
          }

          TerminalConsole.setProgress(90, "Compressing batch output package into ZIP...");
          TerminalConsole.setStatus("running", "PACKAGING · 90%");
          const blob = await res.blob();
          TerminalConsole.setProgress(100, "Batch conversion complete!");
          TerminalConsole.setStatus("completed", "COMPLETED · 100%");

          const zipFilename = `better_vert_batch_${targetFormat}.zip`;
          currentMediaBlobUrl = URL.createObjectURL(blob);
          btnDownloadUniversal.href = currentMediaBlobUrl;
          btnDownloadUniversal.download = zipFilename;
          universalResultTitle.textContent = `Batch converted ${stagedUniversalFiles.length} files into ${zipFilename} (${formatBytes(blob.size)})`;
          universalResult.style.display = "flex";

          if (routeBadgeContainer && routeBadgeText) {
            routeBadgeText.textContent = `Batch Multi-Threaded Engine → ${stagedUniversalFiles.length} Files Processed → ${zipFilename}`;
            routeBadgeContainer.style.display = "flex";
          }

          TerminalConsole.appendLog(`[DONE] Batch conversion finished: ${stagedUniversalFiles.length} files converted to ${zipFilename} (${formatBytes(blob.size)})`);

          if (userSettings.autoDownload) {
            btnDownloadUniversal.click();
          }
        }
      } catch (err) {
        if (progressTicker) {
          clearInterval(progressTicker);
          progressTicker = null;
        }
        TerminalConsole.setStatus("failed", "FAILED");
        TerminalConsole.setProgress(100, `Failed: ${err.message}`);
        TerminalConsole.appendLog(`[ERROR] Conversion failed: ${err.message}`);
        TerminalConsole.open();
        alert(`Conversion failed: ${err.message}`);
      } finally {
        if (progressTicker) {
          clearInterval(progressTicker);
          progressTicker = null;
        }
        btnConvertUniversal.disabled = false;
      }
    });
  }

  // Media Preview Renderer
  function renderMediaPreview(filename, blob, blobUrl) {
    if (!mediaPreviewContainer) return;
    mediaPreviewContainer.innerHTML = "";
    const ext = filename.split(".").pop().toLowerCase();

    const videoExts = ["mp4", "webm", "mov", "mkv", "avi"];
    const audioExts = ["mp3", "wav", "aac", "flac", "ogg", "opus", "m4a"];
    const imageExts = ["png", "jpg", "jpeg", "webp", "gif", "svg", "bmp", "ico"];

    if (videoExts.includes(ext)) {
      const vid = document.createElement("video");
      vid.className = "preview-video";
      vid.controls = true;
      vid.autoplay = false;
      vid.src = blobUrl;
      mediaPreviewContainer.appendChild(vid);
      mediaPreviewContainer.style.display = "block";
    } else if (audioExts.includes(ext)) {
      const aud = document.createElement("audio");
      aud.className = "preview-audio";
      aud.controls = true;
      aud.autoplay = false;
      aud.src = blobUrl;
      mediaPreviewContainer.appendChild(aud);
      mediaPreviewContainer.style.display = "block";
    } else if (imageExts.includes(ext)) {
      const img = document.createElement("img");
      img.className = "preview-img";
      img.alt = filename;
      img.src = blobUrl;
      mediaPreviewContainer.appendChild(img);
      mediaPreviewContainer.style.display = "block";
    } else if (ext === "md" || ext === "txt" || ext === "json" || ext === "csv" || ext === "yaml") {
      const box = document.createElement("div");
      box.className = "preview-doc-box";
      box.innerHTML = `
        <span><strong>${filename}</strong> compiled successfully.</span>
        <button class="btn btn-secondary btn-sm" id="btnQuickViewResult">Open in Markdown Studio</button>
      `;
      mediaPreviewContainer.appendChild(box);
      mediaPreviewContainer.style.display = "block";

      const btnQuick = document.getElementById("btnQuickViewResult");
      if (btnQuick) {
        btnQuick.addEventListener("click", async () => {
          const text = await blob.text();
          currentModalMarkdown = text;
          currentModalFilename = filename;
          if (modalTitle) modalTitle.textContent = filename;
          if (modalRenderedContent && window.marked) {
            modalRenderedContent.innerHTML = marked.parse(text);
          }
          if (modalRawContent) modalRawContent.value = text;
          if (markdownModal) markdownModal.classList.add("active");
        });
      }
    }
  }

  // ---------------------------------------------------------------------------
  // 5. Anything -> Markdown Studio (File Converter)
  // ---------------------------------------------------------------------------
  function setupMarkdownDragDrop() {
    if (!dropzoneMarkdown) return;

    dropzoneMarkdown.addEventListener("click", () => fileInputMarkdown.click());
    if (btnBrowseMarkdown) {
      btnBrowseMarkdown.addEventListener("click", (e) => {
        e.stopPropagation();
        fileInputMarkdown.click();
      });
    }

    fileInputMarkdown.addEventListener("change", (e) => {
      if (e.target.files) {
        addMarkdownFiles(e.target.files);
      }
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      dropzoneMarkdown.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzoneMarkdown.classList.add("hot");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzoneMarkdown.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzoneMarkdown.classList.remove("hot");
      });
    });

    dropzoneMarkdown.addEventListener("drop", (e) => {
      if (e.dataTransfer.files) {
        addMarkdownFiles(e.dataTransfer.files);
      }
    });
  }

  function addMarkdownFiles(files) {
    for (let i = 0; i < files.length; i++) {
      stagedMarkdownFiles.push(files[i]);
    }
    syncMarkdownState();
  }

  function syncMarkdownState() {
    const count = stagedMarkdownFiles.length;
    if (markdownFileCount) {
      markdownFileCount.textContent = `${count} file${count === 1 ? "" : "s"} staged`;
    }
    if (btnConvertMarkdown) btnConvertMarkdown.disabled = count === 0;
    if (btnConvertZip) btnConvertZip.disabled = count === 0;
    if (btnClearMarkdown) btnClearMarkdown.disabled = count === 0;

    if (count > 0 && markdownResultsList && markdownResultsList.children.length === 0) {
      markdownResultsList.innerHTML = stagedMarkdownFiles
        .map(
          (f) => `
        <div class="result-item-card">
          <div class="result-item-left">
            <span class="file-badge-type">${f.name.split(".").pop()}</span>
            <div class="item-names">
              <span class="orig-name">${f.name}</span>
            </div>
          </div>
          <div class="result-item-right">
            <span class="file-size">${formatBytes(f.size)}</span>
          </div>
        </div>
      `
        )
        .join("");
    }
  }

  if (btnClearMarkdown) {
    btnClearMarkdown.addEventListener("click", () => {
      stagedMarkdownFiles = [];
      fileInputMarkdown.value = "";
      if (markdownResultsList) markdownResultsList.innerHTML = "";
      syncMarkdownState();
    });
  }

  if (btnConvertMarkdown) {
    btnConvertMarkdown.addEventListener("click", async () => {
      if (stagedMarkdownFiles.length === 0) return;

      btnConvertMarkdown.disabled = true;
      btnConvertMarkdown.textContent = "Converting...";

      const formData = new FormData();
      stagedMarkdownFiles.forEach((file) => formData.append("files", file));
      if (chkMarkdownFrontmatter) {
        formData.append("add_frontmatter", chkMarkdownFrontmatter.checked ? "true" : "false");
      }

      try {
        const res = await fetch("/api/convert-markdown", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) throw new Error(`Server status ${res.status}`);
        const data = await res.json();

        renderMarkdownResults(data.results);

        // Auto-copy to clipboard if single document and enabled in settings
        if (userSettings.autoCopyMarkdown && data.results.length === 1 && data.results[0].ok) {
          try {
            await navigator.clipboard.writeText(data.results[0].markdown);
            showSettingsToast("Markdown copied to clipboard");
          } catch (clipErr) {
            console.warn("Auto-copy clipboard failed:", clipErr);
          }
        }
      } catch (e) {
        alert(`Markdown conversion error: ${e.message}`);
      } finally {
        btnConvertMarkdown.disabled = false;
        btnConvertMarkdown.textContent = "Convert to Markdown";
      }
    });
  }

  if (btnConvertZip) {
    btnConvertZip.addEventListener("click", async () => {
      if (stagedMarkdownFiles.length === 0) return;

      btnConvertZip.disabled = true;
      btnConvertZip.textContent = "Zipping...";

      const formData = new FormData();
      stagedMarkdownFiles.forEach((file) => formData.append("files", file));
      if (chkMarkdownFrontmatter) {
        formData.append("add_frontmatter", chkMarkdownFrontmatter.checked ? "true" : "false");
      }

      try {
        const res = await fetch("/api/convert-markdown-zip", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) throw new Error("Zip creation failed");
        const blob = await res.blob();
        const u = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = u;
        a.download = "better_vert_markdown.zip";
        a.click();
        setTimeout(() => URL.revokeObjectURL(u), 1500);
      } catch (e) {
        alert(`Error downloading zip: ${e.message}`);
      } finally {
        btnConvertZip.disabled = false;
        btnConvertZip.textContent = "Convert & Download .ZIP";
      }
    });
  }

  function renderMarkdownResults(results) {
    if (!markdownResultsList) return;
    markdownResultsList.innerHTML = "";

    results.forEach((item) => {
      const card = document.createElement("div");
      card.className = "result-item-card";

      if (!item.ok) {
        card.innerHTML = `
          <div class="result-item-left">
            <span class="file-badge-type" style="color: #f43f5e;">FAIL</span>
            <div class="item-names">
              <span class="orig-name">${item.name}</span>
            </div>
          </div>
          <div class="result-item-right">
            <span style="color: #f43f5e; font-size: 12px;">${item.error || "Conversion failed"}</span>
          </div>
        `;
        markdownResultsList.appendChild(card);
        return;
      }

      card.innerHTML = `
        <div class="result-item-left">
          <span class="file-badge-type">MD</span>
          <div class="item-names">
            <span class="orig-name">${item.name}</span> &rarr;
            <span class="out-name">${item.out}</span>
          </div>
        </div>
        <div class="result-item-right">
          ${item.words ? `<span class="badge-word-count">${item.words.toLocaleString()} words</span>` : ""}
          ${item.reading_time ? `<span class="badge-reading-time">${item.reading_time}</span>` : ""}
          ${item.images_count ? `<span class="badge-images-count" style="background: rgba(168, 85, 247, 0.15); color: #c084fc; font-size: 11px; padding: 2px 6px; border-radius: 4px; margin-right: 6px; font-weight: 500;">${item.images_count} image${item.images_count > 1 ? "s" : ""}</span>` : ""}
          <span class="chars-count">${(item.chars || 0).toLocaleString()} chars</span>
          <button class="btn-preview">Preview</button>
          <button class="btn-download-item">Download</button>
        </div>
      `;

      card.querySelector(".btn-preview").addEventListener("click", () => {
        openMarkdownModal(item.out, item.markdown);
      });

      card.querySelector(".btn-download-item").addEventListener("click", () => {
        const b = new Blob([item.markdown], { type: "text/markdown" });
        const u = URL.createObjectURL(b);
        const a = document.createElement("a");
        a.href = u;
        a.download = item.out;
        a.click();
        setTimeout(() => URL.revokeObjectURL(u), 1000);
      });

      markdownResultsList.appendChild(card);
    });
  }

  // ---------------------------------------------------------------------------
  // 6. Markdown Preview Modal
  // ---------------------------------------------------------------------------
  function openMarkdownModal(filename, markdown) {
    currentModalMarkdown = markdown;
    currentModalFilename = filename;
    if (modalTitle) modalTitle.textContent = filename;

    if (window.marked && modalRenderedContent) {
      modalRenderedContent.innerHTML = marked.parse(markdown);
    } else if (modalRenderedContent) {
      modalRenderedContent.textContent = markdown;
    }

    if (modalRawContent) modalRawContent.textContent = markdown;
    if (btnToggleRendered) btnToggleRendered.classList.add("active");
    if (btnToggleRaw) btnToggleRaw.classList.remove("active");
    if (modalRenderedContent) modalRenderedContent.style.display = "block";
    if (modalRawContent) modalRawContent.style.display = "none";

    if (markdownModal) markdownModal.style.display = "flex";
  }

  if (btnCloseModal) {
    btnCloseModal.addEventListener("click", () => {
      markdownModal.style.display = "none";
    });
  }

  if (markdownModal) {
    markdownModal.addEventListener("click", (e) => {
      if (e.target === markdownModal) {
        markdownModal.style.display = "none";
      }
    });
  }

  if (btnToggleRendered) {
    btnToggleRendered.addEventListener("click", () => {
      btnToggleRendered.classList.add("active");
      btnToggleRaw.classList.remove("active");
      modalRenderedContent.style.display = "block";
      modalRawContent.style.display = "none";
    });
  }

  if (btnToggleRaw) {
    btnToggleRaw.addEventListener("click", () => {
      btnToggleRaw.classList.add("active");
      btnToggleRendered.classList.remove("active");
      modalRenderedContent.style.display = "none";
      modalRawContent.style.display = "block";
    });
  }

  if (btnCopyMarkdown) {
    btnCopyMarkdown.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(currentModalMarkdown);
        if (copyText) copyText.textContent = "Copied!";
        setTimeout(() => {
          if (copyText) copyText.textContent = "Copy Markdown";
        }, 2000);
      } catch (e) {
        alert("Copy failed");
      }
    });
  }

  if (btnExportHtml) {
    btnExportHtml.addEventListener("click", () => {
      if (!currentModalMarkdown) return;
      const htmlBody = window.marked ? marked.parse(currentModalMarkdown) : `<pre>${currentModalMarkdown}</pre>`;
      const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${currentModalFilename || "Converted Document"}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.6;
      color: #1e293b;
      background: #f8fafc;
      max-width: 860px;
      margin: 40px auto;
      padding: 30px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }
    h1, h2, h3, h4 { color: #0f172a; margin-top: 1.5em; }
    code { font-family: ui-monospace, monospace; background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
    pre { background: #0f172a; color: #f8fafc; border-radius: 8px; padding: 16px; overflow-x: auto; }
    pre code { background: transparent; color: inherit; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    th, td { border: 1px solid #cbd5e1; padding: 10px 14px; text-align: left; }
    th { background: #f1f5f9; }
    blockquote { border-left: 4px solid #38bdf8; padding-left: 16px; margin: 16px 0; color: #475569; }
    img { max-width: 100%; height: auto; border-radius: 6px; }
  </style>
</head>
<body>
${htmlBody}
</body>
</html>`;

      const b = new Blob([fullHtml], { type: "text/html" });
      const u = URL.createObjectURL(b);
      const a = document.createElement("a");
      a.href = u;
      a.download = (currentModalFilename || "document").replace(/\.md$/i, "") + ".html";
      a.click();
      setTimeout(() => URL.revokeObjectURL(u), 1000);
    });
  }

  if (btnDownloadModal) {
    btnDownloadModal.addEventListener("click", () => {
      const b = new Blob([currentModalMarkdown], { type: "text/markdown" });
      const u = URL.createObjectURL(b);
      const a = document.createElement("a");
      a.href = u;
      a.download = currentModalFilename || "document.md";
      a.click();
      setTimeout(() => URL.revokeObjectURL(u), 1000);
    });
  }

  // ---------------------------------------------------------------------------
  // 7. Batch Mode Operations
  // ---------------------------------------------------------------------------
  async function fetchBatchStatus() {
    try {
      const res = await fetch("/api/batch-status");
      if (!res.ok) return;
      const data = await res.json();

      if (batchInputCount) batchInputCount.textContent = `${data.input_count} file${data.input_count === 1 ? "" : "s"}`;
      if (batchOutputCount) batchOutputCount.textContent = `${data.output_count} file${data.output_count === 1 ? "" : "s"}`;

      if (batchInputList) {
        if (data.input_files.length === 0) {
          batchInputList.innerHTML = `<p class="empty-state">No files staged in <code>./input</code></p>`;
        } else {
          batchInputList.innerHTML = data.input_files
            .map((f) => `<div class="batch-file-row"><span>${f}</span><span class="badge">staged</span></div>`)
            .join("");
        }
      }

      if (batchOutputList) {
        if (data.output_files.length === 0) {
          batchOutputList.innerHTML = `<p class="empty-state">No files converted yet</p>`;
        } else {
          batchOutputList.innerHTML = data.output_files
            .map(
              (f) => `
            <div class="batch-file-row">
              <span>${f.name}</span>
              <span style="color: #38bdf8;">${formatBytes(f.size)}</span>
            </div>
          `
            )
            .join("");
        }
      }
    } catch (e) {
      console.warn("Batch status fetch error:", e);
    }
  }

  if (btnTriggerBatch) {
    btnTriggerBatch.addEventListener("click", async () => {
      btnTriggerBatch.disabled = true;
      btnTriggerBatch.textContent = "Converting batch...";
      try {
        const res = await fetch("/api/batch-convert", { method: "POST" });
        const data = await res.json();
        alert(`Batch complete! Processed: ${data.processed_count}, Failed: ${data.failed_count}`);
        fetchBatchStatus();
      } catch (e) {
        alert(`Batch conversion failed: ${e.message}`);
      } finally {
        btnTriggerBatch.disabled = false;
        btnTriggerBatch.textContent = "Run Batch Conversion on ./input";
      }
    });
  }

  if (btnRefreshBatch) {
    btnRefreshBatch.addEventListener("click", fetchBatchStatus);
  }

  // ---------------------------------------------------------------------------
  // 8. PDF Studio (Poppler Engine: Merge & Split)
  // ---------------------------------------------------------------------------
  let stagedPdfMergeFiles = [];
  let stagedPdfSplitFile = null;

  function initPdfStudio() {
    // Dropzone merge
    if (dropzonePdfMerge && fileInputPdfMerge) {
      dropzonePdfMerge.addEventListener("click", () => fileInputPdfMerge.click());
      dropzonePdfMerge.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzonePdfMerge.classList.add("drag-over");
      });
      dropzonePdfMerge.addEventListener("dragleave", () => dropzonePdfMerge.classList.remove("drag-over"));
      dropzonePdfMerge.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzonePdfMerge.classList.remove("drag-over");
        if (e.dataTransfer.files) handlePdfMergeFiles(Array.from(e.dataTransfer.files));
      });
      fileInputPdfMerge.addEventListener("change", (e) => {
        if (e.target.files) handlePdfMergeFiles(Array.from(e.target.files));
      });
    }

    // Dropzone split
    if (dropzonePdfSplit && fileInputPdfSplit) {
      dropzonePdfSplit.addEventListener("click", () => fileInputPdfSplit.click());
      dropzonePdfSplit.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzonePdfSplit.classList.add("drag-over");
      });
      dropzonePdfSplit.addEventListener("dragleave", () => dropzonePdfSplit.classList.remove("drag-over"));
      dropzonePdfSplit.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzonePdfSplit.classList.remove("drag-over");
        if (e.dataTransfer.files && e.dataTransfer.files[0]) stagePdfSplit(e.dataTransfer.files[0]);
      });
      fileInputPdfSplit.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) stagePdfSplit(e.target.files[0]);
      });
    }

    // Merge Trigger
    if (btnTriggerPdfMerge) {
      btnTriggerPdfMerge.addEventListener("click", async () => {
        if (stagedPdfMergeFiles.length < 2) return;
        btnTriggerPdfMerge.disabled = true;
        btnTriggerPdfMerge.textContent = "Merging with Poppler...";

        const formData = new FormData();
        stagedPdfMergeFiles.forEach((f) => formData.append("files", f));
        const outName = (pdfMergeOutName?.value || "merged_document.pdf").trim();
        formData.append("output_name", outName);

        try {
          const res = await fetch("/api/pdf-merge", {
            method: "POST",
            body: formData,
          });

          if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: "Merge failed" }));
            throw new Error(err.detail || "Merge error");
          }

          const blob = await res.blob();
          const blobUrl = URL.createObjectURL(blob);
          if (btnDownloadPdfMerge) {
            btnDownloadPdfMerge.href = blobUrl;
            btnDownloadPdfMerge.download = outName.endsWith(".pdf") ? outName : `${outName}.pdf`;
          }
          if (pdfMergeResultText) {
            pdfMergeResultText.textContent = `Merged ${stagedPdfMergeFiles.length} PDFs into ${outName} (${formatBytes(blob.size)})`;
          }
          if (pdfMergeResult) pdfMergeResult.style.display = "flex";
        } catch (err) {
          alert(`PDF Merge Error: ${err.message}`);
        } finally {
          btnTriggerPdfMerge.disabled = false;
          btnTriggerPdfMerge.textContent = "Merge PDFs";
        }
      });
    }

    // Split Trigger
    if (btnTriggerPdfSplit) {
      btnTriggerPdfSplit.addEventListener("click", async () => {
        if (!stagedPdfSplitFile) return;
        btnTriggerPdfSplit.disabled = true;
        btnTriggerPdfSplit.textContent = "Extracting with Poppler...";

        const range = (pdfSplitRange?.value || "all").trim();
        const formData = new FormData();
        formData.append("file", stagedPdfSplitFile);
        formData.append("page_range", range);

        try {
          const res = await fetch("/api/pdf-split", {
            method: "POST",
            body: formData,
          });

          if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: "Split failed" }));
            throw new Error(err.detail || "Split error");
          }

          const blob = await res.blob();
          const blobUrl = URL.createObjectURL(blob);
          const isZip = blob.type.includes("zip") || range.toLowerCase() === "all";
          const outName = isZip
            ? `${stagedPdfSplitFile.name.replace(/\.pdf$/i, "")}_pages.zip`
            : `${stagedPdfSplitFile.name.replace(/\.pdf$/i, "")}_p${range}.pdf`;

          if (btnDownloadPdfSplit) {
            btnDownloadPdfSplit.href = blobUrl;
            btnDownloadPdfSplit.download = outName;
          }
          if (pdfSplitResultText) {
            pdfSplitResultText.textContent = `Extracted (${range}) to ${outName} (${formatBytes(blob.size)})`;
          }
          if (pdfSplitResult) pdfSplitResult.style.display = "flex";
        } catch (err) {
          alert(`PDF Split Error: ${err.message}`);
        } finally {
          btnTriggerPdfSplit.disabled = false;
          btnTriggerPdfSplit.textContent = "Extract / Split PDF";
        }
      });
    }

    if (btnRemovePdfSplit) {
      btnRemovePdfSplit.addEventListener("click", () => {
        stagedPdfSplitFile = null;
        if (fileInputPdfSplit) fileInputPdfSplit.value = "";
        if (pdfSplitStaged) pdfSplitStaged.style.display = "none";
        if (dropzonePdfSplit) dropzonePdfSplit.style.display = "flex";
        if (btnTriggerPdfSplit) btnTriggerPdfSplit.disabled = true;
        if (pdfSplitResult) pdfSplitResult.style.display = "none";
      });
    }

    if (btnClearPdfMerge) {
      btnClearPdfMerge.addEventListener("click", () => {
        stagedPdfMergeFiles = [];
        if (fileInputPdfMerge) fileInputPdfMerge.value = "";
        renderPdfMergeList();
        if (pdfMergeResult) pdfMergeResult.style.display = "none";
      });
    }
  }

  function handlePdfMergeFiles(files) {
    const pdfs = files.filter((f) => f.name.toLowerCase().endsWith(".pdf"));
    if (pdfs.length === 0) return;
    pdfs.forEach((f) => {
      if (!stagedPdfMergeFiles.some((x) => x.name === f.name && x.size === f.size)) {
        stagedPdfMergeFiles.push(f);
      }
    });
    renderPdfMergeList();
  }

  function renderPdfMergeList() {
    if (!pdfMergeList) return;
    if (stagedPdfMergeFiles.length === 0) {
      pdfMergeList.style.display = "none";
      if (btnClearPdfMerge) btnClearPdfMerge.style.display = "none";
      if (btnTriggerPdfMerge) btnTriggerPdfMerge.disabled = true;
      return;
    }

    pdfMergeList.style.display = "flex";
    if (btnClearPdfMerge) btnClearPdfMerge.style.display = "inline-flex";
    if (btnTriggerPdfMerge) btnTriggerPdfMerge.disabled = stagedPdfMergeFiles.length < 2;

    pdfMergeList.innerHTML = stagedPdfMergeFiles
      .map(
        (f, idx) => `
      <div class="pdf-merge-item">
        <span class="pdf-merge-item-name" title="${f.name}">${idx + 1}. ${f.name}</span>
        <div class="pdf-merge-item-right">
          <span>${formatBytes(f.size)}</span>
          <button type="button" class="btn-subtle-sm" data-idx="${idx}" title="Remove file">&times;</button>
        </div>
      </div>
    `
      )
      .join("");

    pdfMergeList.querySelectorAll(".btn-subtle-sm").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const idx = parseInt(btn.getAttribute("data-idx"), 10);
        stagedPdfMergeFiles.splice(idx, 1);
        renderPdfMergeList();
      });
    });
  }

  function stagePdfSplit(file) {
    stagedPdfSplitFile = file;
    if (pdfSplitStagedName) pdfSplitStagedName.textContent = file.name;
    if (pdfSplitStagedMeta) pdfSplitStagedMeta.textContent = formatBytes(file.size);
    if (dropzonePdfSplit) dropzonePdfSplit.style.display = "none";
    if (pdfSplitStaged) pdfSplitStaged.style.display = "flex";
    if (btnTriggerPdfSplit) btnTriggerPdfSplit.disabled = false;
    if (pdfSplitResult) pdfSplitResult.style.display = "none";
  }

  // ---------------------------------------------------------------------------
  // 9. Initialization
  // ---------------------------------------------------------------------------
  loadSettings();
  setupUniversalDragDrop();
  setupMarkdownDragDrop();
  initPdfStudio();
  fetchTelemetry();
});
