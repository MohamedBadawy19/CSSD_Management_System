const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Device Integration with Hospital Information Systems";
pres.author = "Team 9 — Cairo University";

// ── Color Palette ──────────────────────────────
const C = {
    teal: "0D7377",
    tealLight: "D6F0F1",
    tealMid: "A8D8DA",
    navy: "14213D",
    white: "FFFFFF",
    offWhite: "F7FAFA",
    red: "DC2626",
    amber: "B45309",
    green: "16A34A",
    textGray: "555555",
    darkBg: "0A1628",
};

const makeShadow = () => ({ type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.12 });

// ════════════════════════════════════════════════
// SLIDE 1 — TITLE
// ════════════════════════════════════════════════
{
    const s = pres.addSlide();
    s.background = { color: C.darkBg };

    // Big teal top accent block
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.teal }, line: { color: C.teal } });

    // Left teal vertical bar
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0.08, w: 0.12, h: 5.545, fill: { color: C.teal }, line: { color: C.teal } });

    // Course badge
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
        x: 0.5, y: 0.45, w: 2.8, h: 0.42, fill: { color: C.teal, transparency: 30 },
        line: { color: C.teal, width: 1 }, rectRadius: 0.05
    });
    s.addText("SBEG202 — Clinical Engineering", {
        x: 0.5, y: 0.45, w: 2.8, h: 0.42, fontSize: 9.5, color: C.tealMid,
        bold: true, align: "center", valign: "middle", margin: 0
    });

    // Main title
    s.addText("Device Integration with\nHospital Information Systems", {
        x: 0.5, y: 1.1, w: 8.8, h: 1.8,
        fontSize: 36, bold: true, color: C.white,
        fontFace: "Trebuchet MS", align: "left", valign: "middle"
    });

    // Subtitle tag
    s.addText("ClinEng Dashboard — Web-Based Asset Management System", {
        x: 0.5, y: 2.85, w: 8, h: 0.4,
        fontSize: 14, color: C.tealMid, italic: true, align: "left"
    });

    // Divider line
    s.addShape(pres.shapes.LINE, { x: 0.5, y: 3.35, w: 9, h: 0, line: { color: C.teal, width: 1 } });

    // Team & supervisors
    s.addText([
        { text: "Team 9  |  ", options: { bold: true, color: C.white } },
        { text: "Ibrahim Abdelqader • Mohamed Badawy • Jana Nour • Malak El Hamshary\nMohamed Ward • Mohamed Sayed • Rowida Mohamed", options: { color: "AAAAAA" } }
    ], { x: 0.5, y: 3.5, w: 9, h: 0.8, fontSize: 11, align: "left" });

    s.addText([
        { text: "Supervised by  ", options: { color: "AAAAAA" } },
        { text: "Dr. Manal Abdelwahed  •  Eng. Ghaidaa W. Eldeeb", options: { bold: true, color: C.tealMid } }
    ], { x: 0.5, y: 4.3, w: 9, h: 0.4, fontSize: 11, align: "left" });

    s.addText("Faculty of Engineering — Biomedical Engineering Dept.  |  Cairo University  |  May 2026", {
        x: 0.5, y: 4.9, w: 9, h: 0.35, fontSize: 9.5, color: "666666", align: "left"
    });
}

// ════════════════════════════════════════════════
// SLIDE 2 — PROJECT OVERVIEW
// ════════════════════════════════════════════════
{
    const s = pres.addSlide();
    s.background = { color: C.white };

    // Title bar
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy }, line: { color: C.navy } });
    s.addText("Project Overview", { x: 0.4, y: 0, w: 9, h: 1.0, fontSize: 30, bold: true, color: C.white, fontFace: "Trebuchet MS", valign: "middle" });

    // Slide number
    s.addText("02 / 10", { x: 8.5, y: 0.1, w: 1.2, h: 0.4, fontSize: 9, color: C.tealMid, align: "right" });

    // Left column — objective
    s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 1.2, w: 4.4, h: 3.9, fill: { color: C.offWhite }, line: { color: C.tealMid, width: 1 }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.35, y: 1.2, w: 4.4, h: 0.45, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("🎯  What We Built", { x: 0.35, y: 1.2, w: 4.4, h: 0.45, fontSize: 13, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
    s.addText([
        { text: "A web-based Clinical Engineering Dashboard to manage 33 medical devices across 12 hospital departments.\n\n", options: { breakLine: false } },
        { text: "Built with HTML5, CSS3, JavaScript + Chart.js — runs entirely in the browser with no server needed.", options: {} }
    ], { x: 0.5, y: 1.75, w: 4.1, h: 3.2, fontSize: 13, color: C.navy, align: "left", valign: "top" });

    // Right column — 3 objectives
    s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.2, w: 4.4, h: 3.9, fill: { color: C.offWhite }, line: { color: C.tealMid, width: 1 }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.2, w: 4.4, h: 0.45, fill: { color: C.navy }, line: { color: C.navy } });
    s.addText("📋  3 Core Objectives", { x: 5.2, y: 1.2, w: 4.4, h: 0.45, fontSize: 13, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });

    const objectives = [
        ["1", "EHR Integration", "Connect devices to Electronic Health Records using HL7 FHIR & DICOM"],
        ["2", "Data Flow Simulation", "Model how data moves between devices and hospital IT networks"],
        ["3", "Cybersecurity", "Apply best practices to keep networked medical devices secure"],
    ];
    objectives.forEach(([n, title, desc], i) => {
        const y = 1.78 + i * 1.1;
        s.addShape(pres.shapes.OVAL, { x: 5.3, y: y, w: 0.38, h: 0.38, fill: { color: C.teal }, line: { color: C.teal } });
        s.addText(n, { x: 5.3, y: y, w: 0.38, h: 0.38, fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
        s.addText(title, { x: 5.75, y: y - 0.03, w: 3.7, h: 0.28, fontSize: 12, bold: true, color: C.navy, align: "left" });
        s.addText(desc, { x: 5.75, y: y + 0.28, w: 3.7, h: 0.45, fontSize: 10, color: C.textGray, align: "left" });
    });
}

// ════════════════════════════════════════════════
// SLIDE 3 — KEY NUMBERS AT A GLANCE
// ════════════════════════════════════════════════
{
    const s = pres.addSlide();
    s.background = { color: C.navy };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Key Numbers at a Glance", { x: 0.4, y: 0.15, w: 9, h: 0.75, fontSize: 30, bold: true, color: C.white, fontFace: "Trebuchet MS", valign: "middle" });
    s.addText("03 / 10", { x: 8.5, y: 0.15, w: 1.2, h: 0.4, fontSize: 9, color: C.tealMid, align: "right" });

    // 5 KPI cards
    const kpis = [
        { val: "33", label: "Medical Devices", sub: "across 12 departments" },
        { val: "$5.06M", label: "Fleet Value", sub: "total acquisition cost" },
        { val: "94.8%", label: "Avg Availability", sub: "fleet-wide uptime" },
        { val: "41.2 mo", label: "Avg MTBF", sub: "mean time between failures" },
        { val: "85.6%", label: "Avg Performance", sub: "efficiency fleet-wide" },
    ];

    kpis.forEach((k, i) => {
        const x = 0.3 + i * 1.9;
        s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 1.75, h: 1.8, fill: { color: "0D2240" }, line: { color: C.teal, width: 1.5 }, shadow: makeShadow() });
        s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 1.75, h: 0.08, fill: { color: C.teal }, line: { color: C.teal } });
        s.addText(k.val, { x, y: 1.3, w: 1.75, h: 0.7, fontSize: 22, bold: true, color: C.teal, align: "center", fontFace: "Consolas" });
        s.addText(k.label, { x, y: 2.0, w: 1.75, h: 0.35, fontSize: 10, bold: true, color: C.white, align: "center" });
        s.addText(k.sub, { x, y: 2.35, w: 1.75, h: 0.5, fontSize: 8.5, color: C.tealMid, align: "center", italic: true });
    });

    // Status row
    const statuses = [
        { val: "29", label: "Operational / Active", color: C.green },
        { val: "2", label: "Under Maintenance", color: C.amber },
        { val: "2", label: "Failed", color: C.red },
        { val: "20", label: "Open Repair Jobs", color: C.teal },
        { val: "6", label: "Overdue IPM", color: C.red },
    ];
    s.addText("Device Status Breakdown", { x: 0.4, y: 3.15, w: 9, h: 0.4, fontSize: 13, bold: true, color: C.tealMid, align: "left" });
    statuses.forEach((st, i) => {
        const x = 0.3 + i * 1.9;
        s.addShape(pres.shapes.RECTANGLE, { x, y: 3.6, w: 1.75, h: 1.5, fill: { color: "0D2240" }, line: { color: st.color, width: 1.5 } });
        s.addText(st.val, { x, y: 3.7, w: 1.75, h: 0.65, fontSize: 28, bold: true, color: st.color, align: "center", fontFace: "Consolas" });
        s.addText(st.label, { x, y: 4.35, w: 1.75, h: 0.6, fontSize: 9.5, color: C.white, align: "center" });
    });
}

// ════════════════════════════════════════════════
// SLIDE 4 — DASHBOARD FEATURES
// ════════════════════════════════════════════════
{
    const s = pres.addSlide();
    s.background = { color: C.white };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy }, line: { color: C.navy } });
    s.addText("Dashboard Features", { x: 0.4, y: 0, w: 9, h: 1.0, fontSize: 30, bold: true, color: C.white, fontFace: "Trebuchet MS", valign: "middle" });
    s.addText("04 / 10", { x: 8.5, y: 0.1, w: 1.2, h: 0.4, fontSize: 9, color: C.tealMid, align: "right" });

    const modules = [
        { icon: "📊", name: "Dashboard View", desc: "KPI cards, device status chart, IPM compliance summary, fleet availability at a glance" },
        { icon: "📋", name: "All Devices", desc: "Full 33-device inventory table with filters by department, status, and IPM — with color-coded badges" },
        { icon: "🔧", name: "IPM Tracker", desc: "Preventive maintenance calendar, compliance percentages, overdue alerts with priority flags" },
        { icon: "🛠️", name: "Work Orders", desc: "Open repair jobs, problem codes, technician assignment, repair timeline, and cost tracking" },
        { icon: "🏥", name: "EHR Integration", desc: "Device-to-EHR data mapping interface — connects devices to patient records (Phase 2)" },
        { icon: "🔒", name: "Cybersecurity", desc: "Security event monitoring, hazard notifications, patch status tracking (Phase 2)" },
    ];

    modules.forEach((m, i) => {
        const col = i % 3;
        const row = Math.floor(i / 3);
        const x = 0.3 + col * 3.2;
        const y = 1.15 + row * 2.1;
        s.addShape(pres.shapes.RECTANGLE, { x, y, w: 3.0, h: 1.85, fill: { color: C.offWhite }, line: { color: C.tealMid, width: 1 }, shadow: makeShadow() });
        s.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.08, h: 1.85, fill: { color: C.teal }, line: { color: C.teal } });
        s.addText(m.icon + "  " + m.name, { x: x + 0.15, y: y + 0.1, w: 2.75, h: 0.4, fontSize: 12, bold: true, color: C.navy, align: "left" });
        s.addText(m.desc, { x: x + 0.15, y: y + 0.52, w: 2.75, h: 1.2, fontSize: 10.5, color: C.textGray, align: "left", valign: "top" });
    });
}

// ════════════════════════════════════════════════
// SLIDE 5 — DEVICE INVENTORY BY DEPARTMENT
// ════════════════════════════════════════════════
{
    const s = pres.addSlide();
    s.background = { color: C.white };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Device Inventory by Department", { x: 0.4, y: 0, w: 9, h: 1.0, fontSize: 28, bold: true, color: C.white, fontFace: "Trebuchet MS", valign: "middle" });
    s.addText("05 / 10", { x: 8.5, y: 0.1, w: 1.2, h: 0.4, fontSize: 9, color: C.tealLight, align: "right" });

    // Department chart (left)
    const deptData = [{
        name: "Devices",
        labels: ["Radiology", "ICU", "OR", "Laboratory", "Cardiology", "ER", "Others"],
        values: [7, 6, 5, 5, 2, 2, 6]
    }];
    s.addChart(pres.charts.BAR, deptData, {
        x: 0.3, y: 1.1, w: 5.2, h: 4.0, barDir: "bar",
        chartColors: ["0D7377"],
        chartArea: { fill: { color: "F7FAFA" }, roundedCorners: true },
        catAxisLabelColor: "333333", valAxisLabelColor: "555555",
        valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
        showValue: true, dataLabelColor: "FFFFFF",
        showLegend: false, showTitle: false,
        barGapWidthPct: 35,
    });

    // Right — key types
    s.addText("Key Device Types", { x: 5.8, y: 1.1, w: 3.9, h: 0.4, fontSize: 14, bold: true, color: C.navy });
    const types = [
        { name: "X-Ray / MRI / CT Scanners", dept: "Radiology", count: "7 devices", color: C.teal },
        { name: "Anesthesia Machines + ESUs", dept: "Operating Room", count: "5 devices", color: C.navy },
        { name: "Ventilators + ECG + Infusion Pumps", dept: "ICU", count: "6 devices", color: C.teal },
        { name: "Centrifuges + Blood Analyzers", dept: "Laboratory", count: "5 devices", color: C.navy },
        { name: "ECG Machines + Defibrillators", dept: "Cardiology / ER", count: "4 devices", color: C.teal },
    ];
    types.forEach((t, i) => {
        const y = 1.65 + i * 0.8;
        s.addShape(pres.shapes.RECTANGLE, { x: 5.8, y, w: 3.9, h: 0.65, fill: { color: C.offWhite }, line: { color: C.tealMid, width: 0.75 } });
        s.addShape(pres.shapes.RECTANGLE, { x: 5.8, y, w: 0.07, h: 0.65, fill: { color: t.color }, line: { color: t.color } });
        s.addText(t.name, { x: 5.95, y: y + 0.04, w: 2.5, h: 0.28, fontSize: 10, bold: true, color: C.navy });
        s.addText(t.dept, { x: 5.95, y: y + 0.33, w: 2.0, h: 0.24, fontSize: 9, color: C.textGray });
        s.addText(t.count, { x: 8.4, y: y + 0.18, w: 1.1, h: 0.28, fontSize: 10, bold: true, color: t.color, align: "right" });
    });
}

// ════════════════════════════════════════════════
// SLIDE 6 — IPM TRACKING
// ════════════════════════════════════════════════
{
    const s = pres.addSlide();
    s.background = { color: C.white };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy }, line: { color: C.navy } });
    s.addText("Inspection & Preventive Maintenance (IPM)", { x: 0.4, y: 0, w: 9.2, h: 1.0, fontSize: 26, bold: true, color: C.white, fontFace: "Trebuchet MS", valign: "middle" });
    s.addText("06 / 10", { x: 8.5, y: 0.1, w: 1.2, h: 0.4, fontSize: 9, color: C.tealMid, align: "right" });

    // Donut chart
    s.addChart(pres.charts.DOUGHNUT, [{
        name: "IPM Status",
        labels: ["Compliant (15)", "Upcoming (11)", "Overdue (6)", "Pending (1)"],
        values: [15, 11, 6, 1]
    }], {
        x: 0.3, y: 1.05, w: 4.0, h: 3.8,
        chartColors: [C.green, "0D7377", C.red, C.amber],
        showPercent: true, showLegend: true, legendPos: "b",
        chartArea: { fill: { color: C.white } },
        showTitle: true, title: "IPM Status Distribution",
        titleColor: C.navy, titleFontSize: 12,
    });

    // Warning box
    s.addShape(pres.shapes.RECTANGLE, { x: 4.6, y: 1.05, w: 5.1, h: 0.65, fill: { color: "FFF8E7" }, line: { color: C.amber, width: 1.5 } });
    s.addText("⚠️  18.2% of devices have OVERDUE IPM — concentrated in Radiology & Laboratory", {
        x: 4.7, y: 1.05, w: 4.9, h: 0.65, fontSize: 10.5, color: "7C4A00", bold: true, align: "left", valign: "middle"
    });

    // Overdue table
    s.addText("Overdue Devices — Priority Action Required", { x: 4.6, y: 1.85, w: 5.1, h: 0.38, fontSize: 12, bold: true, color: C.navy });

    const overdueRows = [
        [{ text: "X-Ray Machine 2", options: { bold: true } }, { text: "Radiology", options: {} }, { text: "Power issue", options: { color: C.amber } }],
        [{ text: "MRI Scanner 1", options: { bold: true } }, { text: "Radiology", options: {} }, { text: "Overdue 4 months", options: { color: C.red } }],
        [{ text: "CT Scanner 2", options: { bold: true } }, { text: "Radiology", options: {} }, { text: "FAILED — parts pend.", options: { color: C.red } }],
        [{ text: "ESU 1", options: { bold: true } }, { text: "OR", options: {} }, { text: "Overdue", options: { color: C.amber } }],
        [{ text: "Centrifuge 2", options: { bold: true } }, { text: "Laboratory", options: {} }, { text: "Under maintenance", options: { color: C.amber } }],
        [{ text: "Blood Analyzer 2", options: { bold: true } }, { text: "Laboratory", options: {} }, { text: "FAILED", options: { color: C.red } }],
    ];

    const tableData = [
        [
            { text: "Device", options: { bold: true, color: C.white, fill: { color: C.teal }, align: "left" } },
            { text: "Department", options: { bold: true, color: C.white, fill: { color: C.teal }, align: "left" } },
            { text: "Status", options: { bold: true, color: C.white, fill: { color: C.teal }, align: "left" } },
        ],
        ...overdueRows.map(r => [
            { text: r[0].text, options: { bold: r[0].options.bold || false, color: C.navy, fill: { color: "FEF2F2" }, align: "left" } },
            { text: r[1].text, options: { color: C.textGray, fill: { color: "FEF2F2" }, align: "left" } },
            { text: r[2].text, options: { bold: true, color: r[2].options.color || C.navy, fill: { color: "FEF2F2" }, align: "left" } },
        ])
    ];

    s.addTable(tableData, {
        x: 4.6, y: 2.28, w: 5.1, h: 2.9,
        colW: [2.0, 1.2, 1.9],
        fontSize: 10, border: { pt: 0.5, color: "E5E7EB" },
        rowH: 0.4,
    });
}

// ════════════════════════════════════════════════
// SLIDE 7 — REPAIRS & COST ANALYSIS
// ════════════════════════════════════════════════
{
    const s = pres.addSlide();
    s.background = { color: C.white };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Work Orders & Cost Analysis", { x: 0.4, y: 0, w: 9, h: 1.0, fontSize: 28, bold: true, color: C.white, fontFace: "Trebuchet MS", valign: "middle" });
    s.addText("07 / 10", { x: 8.5, y: 0.1, w: 1.2, h: 0.4, fontSize: 9, color: C.tealLight, align: "right" });

    // 4 KPI mini-cards
    const kpis = [
        { v: "20", l: "Open Repair Jobs", c: C.teal },
        { v: "$37,410", l: "Total Repair Cost", c: C.navy },
        { v: "$4,149", l: "In-House Labor", c: C.green },
        { v: "$18/hr", l: "Technician Rate", c: C.teal },
    ];
    kpis.forEach((k, i) => {
        const x = 0.3 + i * 2.35;
        s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 2.1, h: 1.0, fill: { color: C.offWhite }, line: { color: C.tealMid, width: 1 }, shadow: makeShadow() });
        s.addText(k.v, { x, y: 1.15, w: 2.1, h: 0.52, fontSize: 20, bold: true, color: k.c, align: "center", fontFace: "Consolas" });
        s.addText(k.l, { x, y: 1.67, w: 2.1, h: 0.38, fontSize: 9.5, color: C.textGray, align: "center" });
    });

    // Chart — top 5 repairs
    s.addChart(pres.charts.BAR, [{
        name: "Total Cost (USD)",
        labels: ["CT Scanner 2", "Blood Analyzer 2", "MRI Scanner 1", "X-Ray Machine 2", "Centrifuge 2"],
        values: [12130, 8594, 5780, 2312, 1940]
    }], {
        x: 0.3, y: 2.3, w: 5.5, h: 2.9, barDir: "bar",
        chartColors: [C.red, C.red, C.amber, C.amber, C.teal],
        chartArea: { fill: { color: "F7FAFA" }, roundedCorners: true },
        catAxisLabelColor: "333333", valAxisLabelColor: "555555",
        valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
        showValue: true, dataLabelColor: "FFFFFF",
        showLegend: false, showTitle: true, title: "Top 5 Repair Costs (USD)",
        titleColor: C.navy, titleFontSize: 11,
    });

    // Right callouts
    s.addText("Cost Insights", { x: 6.1, y: 2.3, w: 3.6, h: 0.4, fontSize: 13, bold: true, color: C.navy });
    const insights = [
        { icon: "🔴", text: "Top 3 repairs = 71% of total fleet repair costs ($26,504)" },
        { icon: "🏥", text: "Imaging devices (CT, MRI, X-Ray) rely heavily on expensive vendor service" },
        { icon: "✅", text: "In-house rate $18/hr vs vendor $55–65/hr — 3–4× cost difference" },
        { icon: "⚠️", text: "CT Scanner 2 & Blood Analyzer 2 have >10% COS — evaluate for replacement" },
    ];
    insights.forEach((ins, i) => {
        const y = 2.8 + i * 0.65;
        s.addShape(pres.shapes.RECTANGLE, { x: 6.1, y, w: 3.6, h: 0.55, fill: { color: C.offWhite }, line: { color: C.tealMid, width: 0.75 } });
        s.addText(ins.icon + "  " + ins.text, { x: 6.2, y, w: 3.4, h: 0.55, fontSize: 10, color: C.navy, align: "left", valign: "middle" });
    });
}

// ════════════════════════════════════════════════
// SLIDE 8 — AVAILABILITY & PERFORMANCE
// ════════════════════════════════════════════════
{
    const s = pres.addSlide();
    s.background = { color: C.white };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.navy }, line: { color: C.navy } });
    s.addText("Equipment Availability & Performance", { x: 0.4, y: 0, w: 9.2, h: 1.0, fontSize: 26, bold: true, color: C.white, fontFace: "Trebuchet MS", valign: "middle" });
    s.addText("08 / 10", { x: 8.5, y: 0.1, w: 1.2, h: 0.4, fontSize: 9, color: C.tealMid, align: "right" });

    // Formula box
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 1.1, w: 9.4, h: 0.55, fill: { color: C.tealLight }, line: { color: C.tealMid, width: 1 } });
    s.addText("Availability % = (Uptime Hours ÷ Loading Time) × 100     |     Performance Efficiency % = (Operating Time ÷ Uptime) × 100", {
        x: 0.3, y: 1.1, w: 9.4, h: 0.55, fontSize: 11, color: C.navy, align: "center", valign: "middle", italic: true, bold: true
    });

    // Chart — availability by dept
    s.addChart(pres.charts.BAR, [{
        name: "Availability %",
        labels: ["ER", "NICU", "Oncology", "Cardiology", "Ambulance", "OR", "ICU", "Radiology", "Laboratory"],
        values: [100.0, 100.0, 100.0, 99.7, 99.3, 98.2, 91.5, 91.2, 90.1]
    }], {
        x: 0.3, y: 1.75, w: 5.3, h: 3.5, barDir: "bar",
        chartColors: [C.green, C.green, C.green, C.green, C.green, C.green, C.amber, C.amber, C.amber],
        chartArea: { fill: { color: "F7FAFA" }, roundedCorners: true },
        catAxisLabelColor: "333333", valAxisLabelColor: "555555",
        valAxisMinVal: 85, valAxisMaxVal: 102,
        valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
        showValue: true, dataLabelColor: "FFFFFF",
        showLegend: false, showTitle: true, title: "Average Availability by Department (%)",
        titleColor: C.navy, titleFontSize: 11,
    });

    // Critical devices right side
    s.addText("⚠️  Critical Devices", { x: 5.9, y: 1.75, w: 3.8, h: 0.42, fontSize: 13, bold: true, color: C.red });

    const crits = [
        { device: "VEN-002  Ventilator (ICU)", avail: "55.5%", color: C.red, note: "Life-critical — immediate action" },
        { device: "Blood Analyzer 2", avail: "66.7%", color: C.red, note: "FAILED — replacement required" },
        { device: "CT Scanner 2", avail: "72.2%", color: C.red, note: "FAILED — pending parts" },
        { device: "X-Ray Machine 2", avail: "84.7%", color: C.amber, note: "Under maintenance" },
        { device: "MRI Scanner 1", avail: "92.8%", color: C.amber, note: "IPM overdue" },
    ];
    crits.forEach((c, i) => {
        const y = 2.28 + i * 0.62;
        s.addShape(pres.shapes.RECTANGLE, { x: 5.9, y, w: 3.8, h: 0.54, fill: { color: i < 3 ? "FEF2F2" : "FFF8E7" }, line: { color: c.color, width: 1 } });
        s.addText(c.avail, { x: 5.9, y, w: 0.95, h: 0.54, fontSize: 14, bold: true, color: c.color, align: "center", valign: "middle", fontFace: "Consolas" });
        s.addShape(pres.shapes.LINE, { x: 6.85, y, w: 0, h: 0.54, line: { color: c.color, width: 0.75 } });
        s.addText(c.device, { x: 7.0, y: y + 0.03, w: 2.6, h: 0.25, fontSize: 9.5, bold: true, color: C.navy });
        s.addText(c.note, { x: 7.0, y: y + 0.28, w: 2.6, h: 0.22, fontSize: 8.5, color: C.textGray });
    });
}

// ════════════════════════════════════════════════
// SLIDE 9 — EHR INTEGRATION & CYBERSECURITY
// ════════════════════════════════════════════════
{
    const s = pres.addSlide();
    s.background = { color: C.white };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1.0, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("EHR Integration & Cybersecurity", { x: 0.4, y: 0, w: 9, h: 1.0, fontSize: 28, bold: true, color: C.white, fontFace: "Trebuchet MS", valign: "middle" });
    s.addText("09 / 10", { x: 8.5, y: 0.1, w: 1.2, h: 0.4, fontSize: 9, color: C.tealLight, align: "right" });

    // Left — EHR
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 1.1, w: 4.5, h: 4.2, fill: { color: C.offWhite }, line: { color: C.tealMid, width: 1 }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.3, y: 1.1, w: 4.5, h: 0.45, fill: { color: C.navy }, line: { color: C.navy } });
    s.addText("🏥  EHR Integration Standards", { x: 0.3, y: 1.1, w: 4.5, h: 0.45, fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });

    const ehrItems = [
        { std: "HL7 FHIR", desc: "Modern RESTful API for healthcare data — devices push observations as JSON" },
        { std: "HL7 v2.x", desc: "Legacy lab results (ORU) & ADT notifications — still widely used" },
        { std: "DICOM", desc: "Universal standard for CT, MRI & X-Ray images to PACS systems" },
        { std: "IEEE 11073", desc: "Medical device communication — bridges device protocols to IT standards" },
        { std: "IHE PCD-01", desc: "Integration profile for point-of-care device observations" },
    ];
    ehrItems.forEach((e, i) => {
        const y = 1.65 + i * 0.7;
        s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y, w: 0.85, h: 0.4, fill: { color: C.teal }, line: { color: C.teal } });
        s.addText(e.std, { x: 0.4, y, w: 0.85, h: 0.4, fontSize: 8, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
        s.addText(e.desc, { x: 1.35, y, w: 3.3, h: 0.5, fontSize: 10, color: C.navy, align: "left", valign: "middle" });
    });

    // Right — Cybersecurity
    s.addShape(pres.shapes.RECTANGLE, { x: 5.1, y: 1.1, w: 4.5, h: 4.2, fill: { color: C.offWhite }, line: { color: C.tealMid, width: 1 }, shadow: makeShadow() });
    s.addShape(pres.shapes.RECTANGLE, { x: 5.1, y: 1.1, w: 4.5, h: 0.45, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("🔒  Cybersecurity Best Practices", { x: 5.1, y: 1.1, w: 4.5, h: 0.45, fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });

    const cyberItems = [
        { icon: "🛡️", title: "Network Segmentation", desc: "Medical devices on isolated VLAN — limits spread if any device is compromised" },
        { icon: "🔑", title: "Device Authentication", desc: "Unique certificates + MAC whitelist — unauthorized devices can't connect" },
        { icon: "🔐", title: "Encrypted Comms", desc: "TLS 1.2/1.3 for all data — legacy devices routed through proxy" },
        { icon: "👥", title: "Role-Based Access", desc: "Clinical engineers: full access. Clinical staff: read-only" },
        { icon: "📢", title: "Hazard Tracking", desc: "30 notifications received — FDA MedWatch & ECRI alerts monitored" },
    ];
    cyberItems.forEach((c, i) => {
        const y = 1.65 + i * 0.7;
        s.addText(c.icon, { x: 5.2, y, w: 0.4, h: 0.4, fontSize: 14, align: "center", valign: "middle" });
        s.addText(c.title, { x: 5.65, y: y + 0.01, w: 3.8, h: 0.22, fontSize: 10, bold: true, color: C.navy });
        s.addText(c.desc, { x: 5.65, y: y + 0.24, w: 3.8, h: 0.3, fontSize: 9.5, color: C.textGray });
    });
}

// ════════════════════════════════════════════════
// SLIDE 10 — RESULTS, RECOMMENDATIONS & CONCLUSION
// ════════════════════════════════════════════════
{
    const s = pres.addSlide();
    s.background = { color: C.darkBg };

    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("Results, Recommendations & Conclusion", { x: 0.4, y: 0.1, w: 9, h: 0.8, fontSize: 26, bold: true, color: C.white, fontFace: "Trebuchet MS", valign: "middle" });
    s.addText("10 / 10", { x: 8.5, y: 0.2, w: 1.2, h: 0.4, fontSize: 9, color: C.tealMid, align: "right" });

    // Left — Key Findings
    s.addText("📊  Key Findings", { x: 0.3, y: 1.0, w: 4.5, h: 0.42, fontSize: 13, bold: true, color: C.teal });
    const findings = [
        "Fleet availability 94.8% — just below the 95% clinical target",
        "18.2% of devices have overdue IPM — focused in Radiology & Lab",
        "2 Failed devices need urgent parts procurement",
        "VEN-002 ventilator at 55.5% availability — patient safety risk",
        "Top 3 repairs = 71% of total repair costs ($26,504)",
        "30 hazard notifications — not all reviewed; process gap found",
    ];
    findings.forEach((f, i) => {
        const y = 1.48 + i * 0.51;
        s.addShape(pres.shapes.OVAL, { x: 0.3, y: y + 0.07, w: 0.22, h: 0.22, fill: { color: C.teal }, line: { color: C.teal } });
        s.addText(f, { x: 0.58, y, w: 4.0, h: 0.5, fontSize: 10, color: "DDDDDD", align: "left", valign: "middle" });
    });

    // Right — Recommendations
    s.addText("✅  Recommendations", { x: 5.1, y: 1.0, w: 4.5, h: 0.42, fontSize: 13, bold: true, color: C.teal });
    const recs = [
        ["1", "Schedule immediate IPM for all 6 overdue devices", C.red],
        ["2", "Investigate VEN-002 ventilator urgently — ICU patient risk", C.red],
        ["3", "Evaluate CT Scanner 2 & Blood Analyzer 2 for replacement", C.amber],
        ["4", "Enforce 100% hazard notification review with sign-off SLAs", C.amber],
        ["5", "Build out Phase 2: live EHR & cybersecurity monitoring", C.teal],
    ];
    recs.forEach((r, i) => {
        const y = 1.48 + i * 0.67;
        s.addShape(pres.shapes.RECTANGLE, { x: 5.1, y, w: 4.5, h: 0.57, fill: { color: "0D2240" }, line: { color: r[2], width: 1 } });
        s.addShape(pres.shapes.RECTANGLE, { x: 5.1, y, w: 0.38, h: 0.57, fill: { color: r[2] }, line: { color: r[2] } });
        s.addText(r[0], { x: 5.1, y, w: 0.38, h: 0.57, fontSize: 13, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
        s.addText(r[1], { x: 5.55, y, w: 3.95, h: 0.57, fontSize: 10, color: "DDDDDD", align: "left", valign: "middle" });
    });

    // Bottom bar
    s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.2, w: 10, h: 0.425, fill: { color: C.teal }, line: { color: C.teal } });
    s.addText("SBEG202 — Device Integration with Hospital Information Systems  |  Team 9  |  Cairo University  |  May 2026", {
        x: 0.3, y: 5.2, w: 9.4, h: 0.425, fontSize: 9.5, color: C.white, align: "center", valign: "middle"
    });
}

// ── Write file ──
pres.writeFile({ fileName: "/mnt/user-data/outputs/HIS_Team9_Presentation.pptx" })
    .then(() => console.log("✅ Done: HIS_Team9_Presentation.pptx"))
    .catch(e => { console.error("❌", e); process.exit(1); });