let config = {};
let editMode = 'none'; // 'none', 'lines', 'area'
let canvas, ctx;
let dragPoint = null; // {line: 1/2, point: 0/2 (start/end index)}
let areaDragStart = null;
let scaleX = 1, scaleY = 1;

document.addEventListener("DOMContentLoaded", () => {
    fetchConfig().then(() => {
        setupCanvas();
        populateConfigForm();
    });
    loadHistory();
    
    // Config form
    const form = document.getElementById("config-form");
    if(form) form.addEventListener("submit", saveConfig);
    
    // Resize observer
    window.addEventListener("resize", () => {
        if(canvas) setupCanvas();
    });
});

function showTab(tabName) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("d-none"));
    const target = document.getElementById("tab-" + tabName);
    if(target) target.classList.remove("d-none");
    
    if (tabName === "settings") populateConfigForm();
    if (tabName === "history") loadFullHistory();
}

async function fetchConfig() {
    try {
        const res = await fetch("/api/config");
        config = await res.json();
        updateLineInputs();
    } catch(e) {
        console.error("Failed to fetch config", e);
    }
}

function setupCanvas() {
    canvas = document.getElementById("overlay-canvas");
    const img = document.getElementById("stream-img");
    if(!canvas || !img) return;
    
    ctx = canvas.getContext("2d");
    
    // Wait for image to load to get dimensions
    if (img.complete && img.naturalHeight !== 0) {
        updateCanvasSize(img);
    } else {
        img.onload = () => updateCanvasSize(img);
    }
    
    canvas.addEventListener("mousedown", onMouseDown);
    canvas.addEventListener("mousemove", onMouseMove);
    canvas.addEventListener("mouseup", onMouseUp);
    canvas.addEventListener("touchstart", onTouchStart, {passive: false});
    canvas.addEventListener("touchmove", onTouchMove, {passive: false});
    canvas.addEventListener("touchend", onMouseUp);
}

function updateCanvasSize(img) {
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    
    if (config.camera) {
        scaleX = canvas.width / config.camera.width;
        scaleY = canvas.height / config.camera.height;
    }
    drawOverlay();
}

// Mode Switching
window.setEditMode = function(mode) {
    editMode = mode;
    drawOverlay();

    // UI Helpers
    const linePanel = document.getElementById("line-calibration-panel");
    const areaPanel = document.getElementById("area-calibration-panel");

    if (linePanel) linePanel.classList.toggle("d-none", mode !== 'lines');
    if (areaPanel) areaPanel.classList.toggle("d-none", mode !== 'area');
};

function drawOverlay() {
    if (!config.detection || !ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const l1 = config.detection.line1;
    const l2 = config.detection.line2;
    
    drawLine(l1, "blue", "Line 1 (Start)");
    drawLine(l2, "red", "Line 2 (End)");
    
    if (editMode === 'lines') {
        drawHandles(l1, 1);
        drawHandles(l2, 3);
    }

    if (editMode === 'area' && areaDragStart && dragPoint) {
        const x = areaDragStart.x;
        const y = areaDragStart.y;
        const w = dragPoint.x - x;
        const h = dragPoint.y - y;

        ctx.strokeStyle = "yellow";
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, w, h);
        ctx.fillStyle = "rgba(255, 255, 0, 0.3)";
        ctx.fillRect(x, y, w, h);
    }
}

function drawLine(line, color, label) {
    ctx.beginPath();
    ctx.moveTo(line[0] * scaleX, line[1] * scaleY);
    ctx.lineTo(line[2] * scaleX, line[3] * scaleY);
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.stroke();
    
    ctx.fillStyle = color;
    ctx.font = "14px Arial";
    ctx.fillText(label, line[0] * scaleX, line[1] * scaleY - 10);
}

function drawHandles(line, startIndex) {
    ctx.font = "bold 14px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    // Point 1
    let x1 = line[0]*scaleX;
    let y1 = line[1]*scaleY;

    ctx.fillStyle = "yellow";
    ctx.strokeStyle = "black";
    ctx.beginPath(); ctx.arc(x1, y1, 10, 0, 2*Math.PI);
    ctx.fill(); ctx.stroke();
    
    ctx.fillStyle = "black";
    ctx.fillText(startIndex.toString(), x1, y1);

    // Point 2
    let x2 = line[2]*scaleX;
    let y2 = line[3]*scaleY;

    ctx.fillStyle = "yellow";
    ctx.strokeStyle = "black";
    ctx.beginPath(); ctx.arc(x2, y2, 10, 0, 2*Math.PI);
    ctx.fill(); ctx.stroke();

    ctx.fillStyle = "black";
    ctx.fillText((startIndex+1).toString(), x2, y2);
}

function getClickPos(e) {
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left);
    const y = (e.clientY - rect.top);
    return {x, y};
}

function onMouseDown(e) {
    if (editMode === 'none') return;
    const pos = getClickPos(e);

    if (editMode === 'lines') {
        checkDrag(pos.x, pos.y);
    } else if (editMode === 'area') {
        areaDragStart = pos;
        dragPoint = pos;
    }
}

function onTouchStart(e) {
    if (editMode === 'none') return;
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const x = e.touches[0].clientX - rect.left;
    const y = e.touches[0].clientY - rect.top;

    if (editMode === 'lines') {
        checkDrag(x, y);
    } else if (editMode === 'area') {
        areaDragStart = {x, y};
        dragPoint = {x, y};
    }
}

function checkDrag(mx, my) {
    const lines = [
        {id: 1, data: config.detection.line1},
        {id: 2, data: config.detection.line2}
    ];
    
    const thresh = 20; // Increased threshold
    
    for (let l of lines) {
        // Point 1
        let x1 = l.data[0] * scaleX;
        let y1 = l.data[1] * scaleY;
        if (Math.abs(mx - x1) < thresh && Math.abs(my - y1) < thresh) {
            dragPoint = {line: l.data, idx: 0};
            return;
        }
        // Point 2
        let x2 = l.data[2] * scaleX;
        let y2 = l.data[3] * scaleY;
        if (Math.abs(mx - x2) < thresh && Math.abs(my - y2) < thresh) {
            dragPoint = {line: l.data, idx: 2};
            return;
        }
    }
}

function onMouseMove(e) {
    const pos = getClickPos(e);
    if (editMode === 'lines' && dragPoint) {
         updateDrag(pos.x, pos.y);
    } else if (editMode === 'area' && areaDragStart) {
         dragPoint = pos;
         drawOverlay();
    }
}

function onTouchMove(e) {
    if ((editMode === 'lines' && !dragPoint) || (editMode === 'area' && !areaDragStart)) return;
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const x = e.touches[0].clientX - rect.left;
    const y = e.touches[0].clientY - rect.top;

    if (editMode === 'lines') updateDrag(x, y);
    else if (editMode === 'area') {
        dragPoint = {x, y};
        drawOverlay();
    }
}

function updateDrag(mx, my) {
    // Map back to config coordinates
    let cx = Math.round(mx / scaleX);
    let cy = Math.round(my / scaleY);
    
    // Clamp
    cx = Math.max(0, Math.min(cx, config.camera.width));
    cy = Math.max(0, Math.min(cy, config.camera.height));
    
    dragPoint.line[dragPoint.idx] = cx;
    dragPoint.line[dragPoint.idx+1] = cy;
    
    updateLineInputs();
    drawOverlay();
}

function onMouseUp() {
    if (editMode === 'lines') {
        if (dragPoint) {
            dragPoint = null;
            // updateLineInputs called during drag
        }
    } else if (editMode === 'area') {
        if (areaDragStart && dragPoint) {
            // Calculate Area
            const p1 = areaDragStart;
            const p2 = dragPoint;

            const c1x = p1.x / scaleX;
            const c1y = p1.y / scaleY;
            const c2x = p2.x / scaleX;
            const c2y = p2.y / scaleY;

            const area = Math.abs(c2x - c1x) * Math.abs(c2y - c1y);
            const roundedArea = Math.round(area);

            const input = document.getElementById("conf-min-area");
            if (input) input.value = roundedArea;

            alert(`Area set to ${roundedArea} pixels.`);

            areaDragStart = null;
            dragPoint = null;
            setEditMode('none');
        }
    }
}

// Helpers
function updateLineInputs() {
    if (!config.detection) return;
    const set = (id, val) => {
        const el = document.getElementById(id);
        if(el) el.value = Math.round(val);
    };

    set("l1-x1", config.detection.line1[0]);
    set("l1-y1", config.detection.line1[1]);
    set("l1-x2", config.detection.line1[2]);
    set("l1-y2", config.detection.line1[3]);

    set("l2-x1", config.detection.line2[0]);
    set("l2-y1", config.detection.line2[1]);
    set("l2-x2", config.detection.line2[2]);
    set("l2-y2", config.detection.line2[3]);
}

window.onLineInputChange = function() {
    const get = (id) => {
        const el = document.getElementById(id);
        return el ? parseInt(el.value) : 0;
    };

    config.detection.line1 = [get("l1-x1"), get("l1-y1"), get("l1-x2"), get("l1-y2")];
    config.detection.line2 = [get("l2-x1"), get("l2-y1"), get("l2-x2"), get("l2-y2")];

    drawOverlay();
}

// History
async function loadHistory() {
    const res = await fetch("/api/history?limit=10");
    const data = await res.json();
    const list = document.getElementById("recent-events-list");
    if(!list) return;
    list.innerHTML = "";
    data.events.forEach(ev => {
        const item = document.createElement("div");
        item.className = "alert alert-secondary py-1 mb-1 d-flex justify-content-between";
        const time = new Date(ev.timestamp*1000).toLocaleTimeString();
        item.innerHTML = `<span><b>${ev.speed} km/h</b></span> <span class="text-muted small">${time}</span>`;
        item.onclick = () => window.open("/images/" + ev.image_path, "_blank");
        item.style.cursor = "pointer";
        list.appendChild(item);
    });
}

function populateConfigForm() {
    const set = (id, val) => {
        const el = document.getElementById(id);
        if(el) {
            if(el.type === 'checkbox') el.checked = val;
            else el.value = val;
        }
    };

    if(!config.detection) return;

    set("conf-distance", config.detection.real_distance_meters);
    set("conf-min-area", config.detection.min_area);
    set("conf-speed-limit", config.limits.speed_limit_kmh);
    set("conf-disk-usage", config.limits.max_disk_usage_percent);

    set("conf-notif-enabled", config.notifications.enabled);
    set("conf-telegram-enabled", config.notifications.telegram.enabled);
    set("conf-telegram-token", config.notifications.telegram.bot_token);
    set("conf-telegram-chat", config.notifications.telegram.chat_id);

    set("conf-webhook-enabled", config.notifications.webhook.enabled);
    set("conf-webhook-url", config.notifications.webhook.url);
    
    updateLineInputs();
}

async function saveConfig(e) {
    if(e && e.preventDefault) e.preventDefault();
    
    config.detection.real_distance_meters = parseFloat(document.getElementById("conf-distance").value);
    config.detection.min_area = parseInt(document.getElementById("conf-min-area").value);
    config.limits.speed_limit_kmh = parseInt(document.getElementById("conf-speed-limit").value);
    config.limits.max_disk_usage_percent = parseInt(document.getElementById("conf-disk-usage").value);
    
    config.notifications.enabled = document.getElementById("conf-notif-enabled").checked;
    config.notifications.telegram.enabled = document.getElementById("conf-telegram-enabled").checked;
    config.notifications.telegram.bot_token = document.getElementById("conf-telegram-token").value;
    config.notifications.telegram.chat_id = document.getElementById("conf-telegram-chat").value;
    
    config.notifications.webhook.enabled = document.getElementById("conf-webhook-enabled").checked;
    config.notifications.webhook.url = document.getElementById("conf-webhook-url").value;

    try {
        await sendConfig(config);
        alert("Configuration saved!");
    } catch(e) {
        alert("Failed to save configuration.");
    }
}

async function sendConfig(cfg) {
    const res = await fetch("/api/config", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(cfg)
    });
    if (!res.ok) throw new Error(res.statusText);
}

// Distance Calibration Logic
window.fetchCalibrationEvents = async function() {
    const list = document.getElementById("cal-events-list");
    if(!list) return;
    list.innerHTML = "Loading...";

    try {
        const res = await fetch("/api/calibration/events");
        const events = await res.json();
        list.innerHTML = "";

        if (events.length === 0) {
            list.innerHTML = "<div class='text-muted p-2'>No recent passages found. Drive past the camera!</div>";
            return;
        }

        events.forEach(ev => {
            const row = document.createElement("button");
            row.className = "list-group-item list-group-item-action";
            const time = new Date(ev.timestamp*1000).toLocaleTimeString();
            const duration = ev.time_diff.toFixed(3);
            const currSpeed = ev.speed;

            row.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">Passage at ${time}</h6>
                    <small>${duration}s</small>
                </div>
                <p class="mb-1 small">Calc Speed: ${currSpeed} km/h</p>
            `;

            row.onclick = () => {
                document.querySelectorAll("#cal-events-list .active").forEach(el => el.classList.remove("active"));
                row.classList.add("active");
                document.getElementById("cal-selected-duration").value = duration;
            };

            list.appendChild(row);
        });
    } catch(e) {
        console.error(e);
        list.innerHTML = "Error loading events.";
    }
};

window.calculateCalibration = async function() {
    const duration = parseFloat(document.getElementById("cal-selected-duration").value);
    const realSpeed = parseFloat(document.getElementById("cal-real-speed").value);

    if (!duration || !realSpeed) {
        alert("Please select a passage and enter real speed.");
        return;
    }

    // Speed (m/s) = Distance / Time
    // Distance = Speed (m/s) * Time
    const speedMps = realSpeed / 3.6;
    const distance = speedMps * duration;

    if(confirm(`Calculated distance: ${distance.toFixed(2)} meters. Apply this setting?`)) {
        document.getElementById("conf-distance").value = distance.toFixed(2);
        config.detection.real_distance_meters = distance;
        await saveConfig({preventDefault: ()=>{}});
    }
};

window.movePoint = function(dx, dy) {
    if (!config.detection) return;
    const sel = document.getElementById("cal-point-select").value;
    const step = 2;

    let line, idx;
    if (sel === "0") { line = config.detection.line1; idx = 0; }
    else if (sel === "1") { line = config.detection.line1; idx = 2; }
    else if (sel === "2") { line = config.detection.line2; idx = 0; }
    else if (sel === "3") { line = config.detection.line2; idx = 2; }
    else return;

    line[idx] += dx * step;
    line[idx+1] += dy * step;

    if (config.camera) {
        line[idx] = Math.max(0, Math.min(line[idx], config.camera.width));
        line[idx+1] = Math.max(0, Math.min(line[idx+1], config.camera.height));
    }

    drawOverlay();
    updateLineInputs();
};

window.toggleCalibrationPanel = function() {
    const el = document.getElementById('calibration-tools');
    if (el.classList.contains('d-none')) {
        el.classList.remove('d-none');
        setEditMode('lines');
    } else {
        el.classList.add('d-none');
        setEditMode('none');
    }
};
