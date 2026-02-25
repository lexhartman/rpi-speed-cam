let config = {};
let isEditing = false;
let canvas, ctx;
let dragPoint = null; // {line: 1/2, point: 0/2 (start/end index)}
let scaleX = 1, scaleY = 1;

document.addEventListener("DOMContentLoaded", () => {
    fetchConfig().then(() => {
        setupCanvas();
    });
    loadHistory();
    
    // Config form
    document.getElementById("config-form").addEventListener("submit", saveConfig);
    
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

function toggleCalibration() {
    isEditing = !isEditing;
    drawOverlay();
}

function drawOverlay() {
    if (!config.detection || !ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const l1 = config.detection.line1;
    const l2 = config.detection.line2;
    
    drawLine(l1, "blue", "Line 1 (Start)");
    drawLine(l2, "red", "Line 2 (End)");
    
    if (isEditing) {
        drawHandles(l1);
        drawHandles(l2);
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

function drawHandles(line) {
    ctx.fillStyle = "yellow";
    ctx.strokeStyle = "black";
    
    // Point 1
    ctx.beginPath(); ctx.arc(line[0]*scaleX, line[1]*scaleY, 6, 0, 2*Math.PI); 
    ctx.fill(); ctx.stroke();
    
    // Point 2
    ctx.beginPath(); ctx.arc(line[2]*scaleX, line[3]*scaleY, 6, 0, 2*Math.PI); 
    ctx.fill(); ctx.stroke();
}

function getClickPos(e) {
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left);
    const y = (e.clientY - rect.top);
    return {x, y};
}

function onMouseDown(e) {
    if (!isEditing) return;
    const pos = getClickPos(e);
    checkDrag(pos.x, pos.y);
}

function onTouchStart(e) {
    if (!isEditing) return;
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const x = e.touches[0].clientX - rect.left;
    const y = e.touches[0].clientY - rect.top;
    checkDrag(x, y);
}

function checkDrag(mx, my) {
    const lines = [
        {id: 1, data: config.detection.line1},
        {id: 2, data: config.detection.line2}
    ];
    
    const thresh = 15;
    
    for (let l of lines) {
        // Point 1 (x1, y1) -> indices 0, 1
        let x1 = l.data[0] * scaleX;
        let y1 = l.data[1] * scaleY;
        if (Math.abs(mx - x1) < thresh && Math.abs(my - y1) < thresh) {
            dragPoint = {line: l.data, idx: 0};
            return;
        }
        
        // Point 2 (x2, y2) -> indices 2, 3
        let x2 = l.data[2] * scaleX;
        let y2 = l.data[3] * scaleY;
        if (Math.abs(mx - x2) < thresh && Math.abs(my - y2) < thresh) {
            dragPoint = {line: l.data, idx: 2};
            return;
        }
    }
}

function onMouseMove(e) {
    if (!dragPoint) return;
    const pos = getClickPos(e);
    updateDrag(pos.x, pos.y);
}

function onTouchMove(e) {
    if (!dragPoint) return;
    e.preventDefault();
    const rect = canvas.getBoundingClientRect();
    const x = e.touches[0].clientX - rect.left;
    const y = e.touches[0].clientY - rect.top;
    updateDrag(x, y);
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
    
    drawOverlay();
}

function onMouseUp() {
    if (dragPoint) {
        dragPoint = null;
        // Auto-save config? Or just let user click save?
        // Let's just update local state, user must click Save in Settings or we add a "Save Lines" button.
        // Actually, we should probably save lines immediately or provide feedback.
        // For now, simple state update.
    }
}

// History & Config Forms
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
    document.getElementById("conf-distance").value = config.detection.real_distance_meters;
    document.getElementById("conf-min-area").value = config.detection.min_area;
    document.getElementById("conf-speed-limit").value = config.limits.speed_limit_kmh;
    document.getElementById("conf-disk-usage").value = config.limits.max_disk_usage_percent;
    
    document.getElementById("conf-notif-enabled").checked = config.notifications.enabled;
    // Telegram
    document.getElementById("conf-telegram-enabled").checked = config.notifications.telegram.enabled;
    document.getElementById("conf-telegram-token").value = config.notifications.telegram.bot_token;
    document.getElementById("conf-telegram-chat").value = config.notifications.telegram.chat_id;
    // Webhook
    document.getElementById("conf-webhook-enabled").checked = config.notifications.webhook.enabled;
    document.getElementById("conf-webhook-url").value = config.notifications.webhook.url;
}

async function saveConfig(e) {
    e.preventDefault();
    
    // Update config object
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

    const res = await fetch("/api/config", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(config)
    });
    
    if (res.ok) {
        alert("Configuration saved!");
    } else {
        alert("Failed to save configuration.");
    }
}
