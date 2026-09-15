// =========================================================
// AIShield - Frontend Controller
// =========================================================

let latestScan = null;
let scanTimer = null;


// =========================================================
// PAGE NAVIGATION
// =========================================================

function showPage(pageId, button) {

    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active");
    });

    const page = document.getElementById(pageId);

    if (page) {
        page.classList.add("active");
    }

    document.querySelectorAll(".side-btn").forEach(btn => {
        btn.classList.remove("active");
    });

    if (button) {
        button.classList.add("active");
    }

    if (pageId === "history") {
        loadHistory();
    }

    if (pageId === "analytics") {
        loadStats();
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


// =========================================================
// OPEN SCANNER
// =========================================================

function openScanner() {

    const scannerButton =
        document.querySelector(
            '.side-btn[onclick*="scanner"]'
        );

    showPage("scanner", scannerButton);
}


// =========================================================
// OPEN SPECIFIC SCANNER
// =========================================================

function openScannerType(type) {

    openScanner();

    setTimeout(() => {
        selectScannerByType(type);
    }, 100);
}


// =========================================================
// SELECT SCANNER
// =========================================================

function selectScanner(type, button) {

    document.querySelectorAll(".scanner-type").forEach(btn => {
        btn.classList.remove("active");
    });

    if (button) {
        button.classList.add("active");
    }

    document.querySelectorAll(".scan-panel").forEach(panel => {
        panel.classList.remove("active");
    });

    if (type === "url") {
        document.getElementById("urlPanel")?.classList.add("active");
    }

    if (type === "sms") {
        document.getElementById("smsPanel")?.classList.add("active");
    }

    if (type === "email") {
        document.getElementById("emailPanel")?.classList.add("active");
    }

    const result =
        document.getElementById("resultSection");

    if (result) {
        result.classList.remove("show");
        result.style.display = "none";
    }
}


function selectScannerByType(type) {

    const buttons =
        document.querySelectorAll(".scanner-type");

    let target = null;

    buttons.forEach(button => {

        const onclick = button.getAttribute("onclick") || "";

        if (onclick.includes("'" + type + "'")) {
            target = button;
        }
    });

    selectScanner(type, target);
}


// =========================================================
// ESCAPE HTML
// =========================================================

function escapeHTML(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// =====================================================
// AI SCANNING ANIMATION
// =====================================================

function startAIScan() {
    const scanOverlay = document.getElementById("scanOverlay");
    const scanSection = document.getElementById("scanAnimation");
    const resultSection = document.getElementById("resultSection");

    if (scanOverlay) {
        scanOverlay.classList.add("active");
    }

    if (scanSection) {
        scanSection.classList.add("active");
    }

    if (resultSection) {
        resultSection.classList.remove("show");
        resultSection.style.display = "none";
    }

    document.body.classList.add("is-scanning");
}


function stopAIScan() {
    const scanOverlay = document.getElementById("scanOverlay");
    const scanSection = document.getElementById("scanAnimation");

    if (scanOverlay) {
        scanOverlay.classList.remove("active");
    }

    if (scanSection) {
        scanSection.classList.remove("active");
    }

    document.body.classList.remove("is-scanning");
}


function showResult(data) {
    latestScan = data;

    const resultSection = document.getElementById("resultSection");
    const resultLabel = document.getElementById("resultLabel");
    const confidenceValue = document.getElementById("confidenceValue");

    if (resultSection) {
        resultSection.style.display = "block";

        // Restart result animation every time
        resultSection.classList.remove("show");
        void resultSection.offsetWidth;
        resultSection.classList.add("show");
    }

    if (resultLabel) {
        resultLabel.textContent = data.label || "Unknown";
        resultLabel.className = "result-status";

        if (data.label === "High Risk") {
            resultLabel.classList.add("danger");
        } else if (data.label === "Suspicious") {
            resultLabel.classList.add("warning");
        } else {
            resultLabel.classList.add("safe");
        }
    }

    if (confidenceValue) {
        confidenceValue.textContent =
            `${Number(data.confidence || 0).toFixed(1)}%`;
    }

    updateRiskMeter(Number(data.risk || 0));
    showReasons(data.reasons || []);
}


// =========================================================
// RISK METER
// =========================================================

function updateRiskMeter(risk) {

    const circle =
        document.getElementById("riskCircle");

    const valueElement =
        document.getElementById("riskValue");

    if (!circle || !valueElement) return;

    risk = Number(risk) || 0;

    risk = Math.max(0, Math.min(100, risk));

    let color = "#34a853";

    if (risk >= 70) {
        color = "#ea4335";
    }
    else if (risk >= 40) {
        color = "#f9ab00";
    }

    const degrees = risk * 3.6;

    circle.style.background =
        `conic-gradient(
            ${color} 0deg,
            ${color} ${degrees}deg,
            #e8eaed ${degrees}deg,
            #e8eaed 360deg
        )`;

    animateNumber(
        valueElement,
        0,
        risk,
        900
    );

    valueElement.style.color = color;
}


// =========================================================
// NUMBER ANIMATION
// =========================================================

function animateNumber(element, start, end, duration) {

    const startTime = performance.now();

    function update(currentTime) {

        const elapsed =
            currentTime - startTime;

        const progress =
            Math.min(elapsed / duration, 1);

        const eased =
            1 - Math.pow(1 - progress, 3);

        const current =
            start + (end - start) * eased;

        element.textContent =
            Math.round(current) + "%";

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}


// =========================================================
// SHOW REASONS
// =========================================================

function showReasons(reasons) {

    const list =
        document.getElementById("reasonsList");

    if (!list) return;

    list.innerHTML = "";

    if (!Array.isArray(reasons) || reasons.length === 0) {

        list.innerHTML = `
            <div class="reason-item">
                <div class="reason-icon">✓</div>
                <span>No major suspicious indicators detected.</span>
            </div>
        `;

        return;
    }

    reasons.forEach((reason, index) => {

        const item =
            document.createElement("div");

        item.className = "reason-item";

        item.style.animationDelay =
            `${index * 80}ms`;

        item.innerHTML = `
            <div class="reason-icon">!</div>
            <span>${escapeHTML(reason)}</span>
        `;

        list.appendChild(item);
    });
}


// =========================================================
// SHOW RESULT
// =========================================================

function showResult(data) {

    latestScan = data;

    const section =
        document.getElementById("resultSection");

    const label =
        document.getElementById("resultLabel");

    const confidence =
        document.getElementById("confidenceValue");

    if (!section) return;

    section.classList.add("show");
    section.style.display = "block";

    const risk =
        Number(data.risk) || 0;

    const resultLabel =
        data.label || "Unknown";

    if (label) {

        label.textContent =
            resultLabel;

        if (resultLabel === "High Risk") {

            label.style.background = "#fce8e6";
            label.style.color = "#ea4335";
        }
        else if (resultLabel === "Suspicious") {

            label.style.background = "#fef7e0";
            label.style.color = "#b06000";
        }
        else {

            label.style.background = "#e6f4ea";
            label.style.color = "#34a853";
        }
    }

    if (confidence) {
        confidence.textContent =
            Math.round(Number(data.confidence) || 0) + "%";
    }

    updateRiskMeter(risk);

    showReasons(data.reasons || []);

    section.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// =========================================================
// URL SCANNER
// =========================================================

async function scanURL() {

    const input =
        document.getElementById("urlInput");

    if (!input) {
        alert("URL input not found.");
        return;
    }

    const url =
        input.value.trim();

    if (!url) {
        alert("Please enter a URL.");
        input.focus();
        return;
    }

    startAIScan();

    try {

        console.log("Sending URL to AIShield:", url);

        const response =
            await fetch("/api/scan", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    url: url
                })
            });

        const data =
            await response.json();

        console.log("AIShield response:", data);

        stopAIScan();

        if (!response.ok) {

            alert(
                data.error ||
                "URL analysis failed."
            );

            return;
        }

        showResult(data);

        loadHistory();
        loadStats();

    }
    catch (error) {

        console.error(
            "URL SCAN ERROR:",
            error
        );

        stopAIScan();

        alert(
            "Cannot connect to AIShield server. " +
            "Check the Flask terminal."
        );
    }
}


// =========================================================
// TEXT SCANNER
// =========================================================

async function scanText(type) {

    let text = "";

    if (type === "sms") {

        const input =
            document.getElementById("smsInput");

        text =
            input ? input.value.trim() : "";
    }

    if (type === "email") {

        const input =
            document.getElementById("emailInput");

        text =
            input ? input.value.trim() : "";
    }

    if (!text) {

        alert(
            "Please enter some content to analyze."
        );

        return;
    }

    startAIScan();

    try {

        console.log(
            "Sending text to AIShield:",
            type
        );

        const response =
            await fetch("/api/scan-text", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    type: type.toUpperCase(),
                    text: text
                })
            });

        const data =
            await response.json();

        console.log(
            "AIShield text response:",
            data
        );

        stopAIScan();

        if (!response.ok) {

            alert(
                data.error ||
                "Text analysis failed."
            );

            return;
        }

        showResult(data);

        loadHistory();
        loadStats();

    }
    catch (error) {

        console.error(
            "TEXT SCAN ERROR:",
            error
        );

        stopAIScan();

        alert(
            "Cannot connect to AIShield server."
        );
    }
}


// =========================================================
// SMS
// =========================================================

function analyzeSMS() {

    scanText("sms");
}


// =========================================================
// EMAIL
// =========================================================

function analyzeEmail() {

    scanText("email");
}


// =========================================================
// DOWNLOAD SECURITY REPORT
// =========================================================

async function downloadReport() {

    if (!latestScan) {

        alert(
            "Please perform a scan first."
        );

        return;
    }

    try {

        const response =
            await fetch("/api/report", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    type:
                        latestScan.type,

                    content:
                        latestScan.content || "",

                    label:
                        latestScan.label,

                    risk:
                        latestScan.risk,

                    confidence:
                        latestScan.confidence,

                    reasons:
                        latestScan.reasons || []
                })
            });

        if (!response.ok) {

            const error =
                await response.json();

            alert(
                error.error ||
                "Report generation failed."
            );

            return;
        }

        const blob =
            await response.blob();

        const downloadURL =
            window.URL.createObjectURL(blob);

        const link =
            document.createElement("a");

        link.href = downloadURL;

        link.download =
            "AIShield_Security_Report.pdf";

        document.body.appendChild(link);

        link.click();

        link.remove();

        window.URL.revokeObjectURL(
            downloadURL
        );

    }
    catch (error) {

        console.error(
            "REPORT ERROR:",
            error
        );

        alert(
            "Unable to generate security report."
        );
    }
}


// =========================================================
// LOAD HISTORY
// =========================================================

async function loadHistory() {

    try {

        const response =
            await fetch("/api/history");

        const history =
            await response.json();

        const body =
            document.getElementById("historyBody");

        if (!body) return;

        if (!Array.isArray(history) ||
            history.length === 0) {

            body.innerHTML = `
                <div class="empty">
                    No scan history available.
                </div>
            `;

            return;
        }

        body.innerHTML = "";

        history.forEach(item => {

            let statusClass = "";

            if (item.result === "Safe") {
                statusClass = "safe";
            }
            else if (item.result === "High Risk") {
                statusClass = "danger";
            }
            else {
                statusClass = "warning";
            }

            const row =
                document.createElement("div");

            row.className =
                "history-row";

            row.innerHTML = `
                <span title="${escapeHTML(item.content)}">
                    ${escapeHTML(
                        String(item.content).slice(0, 65)
                    )}
                </span>

                <span class="${statusClass}">
                    ${escapeHTML(item.result)}
                </span>

                <span>
                    ${Number(item.risk || 0).toFixed(1)}%
                </span>

                <span>
                    ${escapeHTML(item.created_at || "")}
                </span>
            `;

            body.appendChild(row);
        });

    }
    catch (error) {

        console.error(
            "HISTORY ERROR:",
            error
        );
    }
}


// =========================================================
// LOAD DASHBOARD STATS
// =========================================================

async function loadStats() {

    try {

        const response =
            await fetch("/api/stats");

        const data =
            await response.json();

        if (!response.ok) {
            return;
        }

        const total =
            Number(data.total_scans || 0);

        const safe =
            Number(data.safe_scans || 0);

        const threats =
            Number(data.threats || 0);

        const suspicious =
            Number(data.suspicious || 0);

        const totalElement =
            document.getElementById("totalScans");

        const safeElement =
            document.getElementById("safeScans");

        const dangerElement =
            document.getElementById("dangerScans");

        const analyticsTotal =
            document.getElementById("analyticsTotal");

        const legendSafe =
            document.getElementById("legendSafe");

        const legendDanger =
            document.getElementById("legendDanger");

        if (totalElement)
            totalElement.textContent = total;

        if (safeElement)
            safeElement.textContent = safe;

        if (dangerElement)
            dangerElement.textContent =
                threats + suspicious;

        if (analyticsTotal)
            analyticsTotal.textContent = total;

        if (legendSafe)
            legendSafe.textContent = safe;

        if (legendDanger)
            legendDanger.textContent =
                threats + suspicious;

        updateDonut(
            safe,
            threats + suspicious,
            total
        );

    }
    catch (error) {

        console.error(
            "STATS ERROR:",
            error
        );
    }
}


// =========================================================
// DONUT UPDATE
// =========================================================

function updateDonut(
    safe,
    threats,
    total
) {

    const donut =
        document.querySelector(".donut");

    if (!donut) return;

    if (total <= 0) {

        donut.style.background =
            "conic-gradient(#e8eaed 0 100%)";

        return;
    }

    const safePercent =
        (safe / total) * 100;

    donut.style.background =
        `conic-gradient(
            #34a853 0 ${safePercent}%,
            #ea4335 ${safePercent}% 100%
        )`;
}


// =========================================================
// INITIAL LOAD
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log(
            "AIShield frontend loaded."
        );

        loadStats();
        loadHistory();

        const urlInput =
            document.getElementById("urlInput");

        if (urlInput) {

            urlInput.addEventListener(
                "keydown",
                event => {

                    if (event.key === "Enter") {
                        scanURL();
                    }

                }
            );
        }
    }
);