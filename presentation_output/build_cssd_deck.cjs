const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Team 5";
pptx.company = "Software Engineering";
pptx.subject = "CSSD Management System project journey";
pptx.title = "CSSD Management System";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  lang: "en-US",
};
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";

const C = {
  ink: "102033",
  navy: "0E2A47",
  teal: "0E9384",
  tealDark: "08756D",
  blue: "2563EB",
  sky: "DDF4FF",
  mint: "DFF8F1",
  bg: "F7FAFC",
  white: "FFFFFF",
  slate: "475569",
  gray: "E2E8F0",
  amber: "F59E0B",
  red: "DC2626",
  green: "16A34A",
};

function addBg(slide, color = C.bg) {
  slide.background = { color };
}

function addTopBar(slide, eyebrow, page) {
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 0.18,
    fill: { color: C.teal },
    line: { color: C.teal },
  });
  slide.addText(eyebrow, {
    x: 0.55,
    y: 0.28,
    w: 9.6,
    h: 0.24,
    fontFace: "Aptos",
    fontSize: 9,
    bold: true,
    color: C.tealDark,
    margin: 0,
    breakLine: false,
    fit: "shrink",
  });
  slide.addText(String(page).padStart(2, "0"), {
    x: 12.35,
    y: 0.28,
    w: 0.45,
    h: 0.24,
    fontFace: "Aptos",
    fontSize: 9,
    bold: true,
    color: "94A3B8",
    align: "right",
    margin: 0,
  });
}

function addTitle(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.55,
    y: 0.66,
    w: 8.2,
    h: 0.58,
    fontFace: "Aptos Display",
    fontSize: 28,
    bold: true,
    color: C.ink,
    margin: 0,
    breakLine: false,
    fit: "shrink",
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.57,
      y: 1.24,
      w: 8.9,
      h: 0.34,
      fontFace: "Aptos",
      fontSize: 12.5,
      color: C.slate,
      margin: 0,
      breakLine: false,
      fit: "shrink",
    });
  }
}

function addBullets(slide, lines, x, y, w, h, opts = {}) {
  const runs = [];
  for (const line of lines) {
    runs.push({
      text: line,
      options: {
        bullet: opts.numbered ? undefined : { type: "bullet" },
        breakLine: true,
        hanging: 4,
      },
    });
  }
  slide.addText(runs, {
    x,
    y,
    w,
    h,
    fontFace: "Aptos",
    fontSize: opts.fontSize || 15,
    color: opts.color || C.ink,
    margin: opts.margin ?? 0.04,
    breakLine: false,
    fit: "shrink",
    paraSpaceAfterPt: opts.paraSpaceAfterPt ?? 5,
    valign: "top",
  });
}

function addNumbered(slide, lines, x, y, w, h, opts = {}) {
  const runs = [];
  lines.forEach((line, i) => {
    runs.push({
      text: `${i + 1}. ${line}`,
      options: { breakLine: true },
    });
  });
  slide.addText(runs, {
    x,
    y,
    w,
    h,
    fontFace: "Aptos",
    fontSize: opts.fontSize || 14,
    color: opts.color || C.ink,
    margin: 0.04,
    fit: "shrink",
    paraSpaceAfterPt: 5,
    valign: "top",
  });
}

function addSectionLabel(slide, label, x, y, w, color = C.tealDark) {
  slide.addText(label.toUpperCase(), {
    x,
    y,
    w,
    h: 0.22,
    fontFace: "Aptos",
    fontSize: 8.5,
    bold: true,
    color,
    margin: 0,
    charSpace: 0.5,
    fit: "shrink",
  });
}

function addPlaceholder(slide, label, x, y, w, h) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    fill: { color: "FFFFFF", transparency: 8 },
    line: { color: "94A3B8", width: 1.25, dash: "dash" },
  });
  slide.addText(label, {
    x: x + 0.25,
    y: y + h / 2 - 0.24,
    w: w - 0.5,
    h: 0.48,
    fontFace: "Aptos",
    fontSize: 14,
    bold: true,
    color: "64748B",
    align: "center",
    valign: "mid",
    margin: 0,
    fit: "shrink",
  });
}

function addPill(slide, text, x, y, w, color, fill) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.32,
    rectRadius: 0.1,
    fill: { color: fill || "FFFFFF" },
    line: { color, width: 1 },
  });
  slide.addText(text, {
    x: x + 0.08,
    y: y + 0.075,
    w: w - 0.16,
    h: 0.16,
    fontFace: "Aptos",
    fontSize: 8.5,
    bold: true,
    color,
    align: "center",
    margin: 0,
    fit: "shrink",
  });
}

function addFooter(slide) {
  slide.addText("CSSD Management System | Team 5", {
    x: 0.55,
    y: 7.12,
    w: 3.6,
    h: 0.18,
    fontFace: "Aptos",
    fontSize: 8,
    color: "94A3B8",
    margin: 0,
    fit: "shrink",
  });
}

function addCard(slide, title, body, x, y, w, h, accent = C.teal) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    fill: { color: "FFFFFF" },
    line: { color: "E2E8F0", width: 1 },
    shadow: { type: "outer", color: "CBD5E1", opacity: 0.16, blur: 1, angle: 45, distance: 1 },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y,
    w: 0.08,
    h,
    fill: { color: accent },
    line: { color: accent },
  });
  slide.addText(title, {
    x: x + 0.22,
    y: y + 0.18,
    w: w - 0.36,
    h: 0.28,
    fontFace: "Aptos Display",
    fontSize: 13,
    bold: true,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
  slide.addText(body, {
    x: x + 0.22,
    y: y + 0.55,
    w: w - 0.36,
    h: h - 0.72,
    fontFace: "Aptos",
    fontSize: 10.8,
    color: C.slate,
    margin: 0,
    fit: "shrink",
    valign: "top",
    breakLine: false,
  });
}

function addSlideTitleOnly(idx, eyebrow, title, subtitle) {
  const slide = pptx.addSlide();
  addBg(slide);
  addTopBar(slide, eyebrow, idx);
  addTitle(slide, title, subtitle);
  addFooter(slide);
  return slide;
}

// Slide 1
{
  const slide = pptx.addSlide();
  slide.background = { color: C.navy };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 4.2, h: 7.5, fill: { color: C.teal }, line: { color: C.teal } });
  slide.addShape(pptx.ShapeType.arc, { x: 8.65, y: -0.5, w: 4.6, h: 4.6, line: { color: "2DD4BF", transparency: 68, width: 7 }, adjustPoint: 0.35 });
  slide.addText("CSSD", {
    x: 0.62,
    y: 0.78,
    w: 2.9,
    h: 0.62,
    fontFace: "Aptos Display",
    fontSize: 33,
    bold: true,
    color: C.white,
    margin: 0,
    fit: "shrink",
  });
  slide.addText("MANAGEMENT\nSYSTEM", {
    x: 4.78,
    y: 1.28,
    w: 6.7,
    h: 1.55,
    fontFace: "Aptos Display",
    fontSize: 37,
    bold: true,
    color: C.white,
    margin: 0,
    breakLine: false,
    fit: "shrink",
  });
  slide.addText("Central Sterile Services Department workflow platform", {
    x: 4.84,
    y: 3.04,
    w: 6.8,
    h: 0.36,
    fontFace: "Aptos",
    fontSize: 17,
    color: "D7ECF4",
    margin: 0,
    fit: "shrink",
  });
  slide.addText("A role-based system for instrument requests, sterilization stages, inventory alerts, reports, and audit history.", {
    x: 4.84,
    y: 3.72,
    w: 6.75,
    h: 0.66,
    fontFace: "Aptos",
    fontSize: 15,
    color: "BFD5E0",
    margin: 0,
    fit: "shrink",
  });
  addPill(slide, "Software Engineering", 4.84, 5.18, 1.85, C.white, "183B5A");
  addPill(slide, "Team 5", 6.86, 5.18, 0.95, C.white, "183B5A");
  slide.addText("Screenshot placeholder: home page or login selection", {
    x: 0.62,
    y: 5.95,
    w: 2.8,
    h: 0.42,
    fontFace: "Aptos",
    fontSize: 10,
    color: "DFF8F1",
    margin: 0,
    fit: "shrink",
  });
  slide.addNotes("Open with the overall project promise: a hospital CSSD workflow moved from manual tracking to a traceable digital flow.");
}

// Slide 2
{
  const slide = addSlideTitleOnly(2, "Idea and problem statement", "The problem is visibility across a critical hospital workflow", "The project focuses on the path from nurse request to sterile instrument delivery.");
  slide.addText("Hospitals need a reliable way to know where each surgical instrument request stands, who handled it, and what still needs to happen.", {
    x: 0.65,
    y: 1.98,
    w: 6.3,
    h: 1.0,
    fontFace: "Aptos Display",
    fontSize: 25,
    bold: true,
    color: C.ink,
    margin: 0,
    fit: "shrink",
  });
  addBullets(slide, [
    "Manual tracking makes request status hard to verify.",
    "Nurses need visibility without calling CSSD repeatedly.",
    "CSSD staff need a structured processing queue.",
    "Hospital administrators need reporting and audit visibility.",
    "Unclear responsibility can create delays and missed updates.",
  ], 0.72, 3.45, 5.9, 2.3, { fontSize: 14.5 });
  addPlaceholder(slide, "Add screenshot: home/login page", 7.45, 1.9, 4.85, 3.35);
  slide.addShape(pptx.ShapeType.rect, { x: 7.45, y: 5.55, w: 4.85, h: 0.07, fill: { color: C.teal }, line: { color: C.teal } });
  slide.addText("Project idea: connect nurses, CSSD technicians, and hospital administrators in one digital workflow.", {
    x: 7.45,
    y: 5.84,
    w: 4.85,
    h: 0.58,
    fontFace: "Aptos",
    fontSize: 14.5,
    bold: true,
    color: C.tealDark,
    margin: 0,
    fit: "shrink",
  });
}

// Slide 3
{
  const slide = addSlideTitleOnly(3, "Project objectives", "The goal: a working end-to-end CSSD prototype", "The release prioritized core workflow coverage over unfinished feature breadth.");
  const objectives = [
    ["Digitize", "Move the instrument lifecycle into one traceable system."],
    ["Separate roles", "Give nurses, CSSD technicians, and admins role-specific views."],
    ["Control access", "Protect pages and actions with role-based permissions."],
    ["Track stages", "Record every request through the sterilization pipeline."],
    ["Improve oversight", "Provide alerts, reports, notifications, and audit history."],
    ["Deliver stability", "Build a tested academic prototype by semester end."],
  ];
  objectives.forEach((o, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    addCard(slide, o[0], o[1], 0.72 + col * 4.1, 2.0 + row * 1.75, 3.55, 1.24, [C.teal, C.blue, C.green, C.amber, C.tealDark, C.navy][i]);
  });
  addPlaceholder(slide, "Add screenshot: dashboard overview", 4.05, 5.68, 5.2, 0.78);
}

// Slide 4
{
  const slide = addSlideTitleOnly(4, "Requirements", "What the system needed to do", "Requirements were split between functional hospital workflow behavior and non-functional quality expectations.");
  addSectionLabel(slide, "Functional requirements", 0.72, 1.88, 3.5);
  addBullets(slide, [
    "Nurse and staff login flows.",
    "Nurse submits instrument requests.",
    "CSSD processes lifecycle stages.",
    "Requests move through Requested, Collected, Cleaned, Sterilized, Packed, Delivered.",
    "Batches can be created and assigned to operators.",
    "Inventory shows shortage alerts.",
    "Hospital admin views reports and audit history.",
  ], 0.72, 2.22, 5.7, 3.6, { fontSize: 13.3 });
  addSectionLabel(slide, "Non-functional requirements", 7.0, 1.88, 3.5, C.blue);
  addBullets(slide, [
    "Secure role separation.",
    "Reliable database updates.",
    "Clear UI for hospital workflow.",
    "No HTTP 500 errors during expected use.",
    "Testable and maintainable Django codebase.",
  ], 7.0, 2.22, 4.9, 2.35, { fontSize: 14.5 });
  slide.addShape(pptx.ShapeType.roundRect, { x: 7.0, y: 5.1, w: 4.8, h: 0.74, rectRadius: 0.08, fill: { color: C.mint }, line: { color: "B6EAD8" } });
  slide.addText("Requirement theme: every feature supports traceability, accountability, or operational visibility.", {
    x: 7.25,
    y: 5.32,
    w: 4.3,
    h: 0.26,
    fontFace: "Aptos",
    fontSize: 12.5,
    bold: true,
    color: C.tealDark,
    margin: 0,
    fit: "shrink",
  });
}

// Slide 5
{
  const slide = addSlideTitleOnly(5, "Users and roles", "Role-specific dashboards keep the workflow safe and understandable", "Each user type sees only the actions needed for their part of the lifecycle.");
  const roles = [
    ["Department Nurse", "Creates requests\nTracks status\nViews notifications\nConfirms delivery", C.teal],
    ["CSSD Technician", "Processes requests\nUpdates stages\nCreates batches\nHandles shortage alerts", C.blue],
    ["Hospital Administrator", "Views daily reports\nSearches audit history\nReviews lifecycle records", C.amber],
    ["System Administrator", "Manages system-level access\nSupports administration\nControls backend setup", C.navy],
  ];
  roles.forEach((r, i) => {
    addCard(slide, r[0], r[1], 0.75 + (i % 2) * 6.1, 1.95 + Math.floor(i / 2) * 2.05, 5.35, 1.48, r[2]);
  });
  addPlaceholder(slide, "Add screenshot: login or role dashboard", 4.08, 6.05, 5.2, 0.6);
}

// Slide 6
{
  const slide = addSlideTitleOnly(6, "Design and architecture", "A Django application organized around roles, views, models, and templates", "The architecture stays simple enough for a semester project while supporting real workflow behavior.");
  const xs = [0.9, 3.25, 5.75, 8.2, 10.6];
  const labels = ["Users", "Django Views", "Models", "SQLite DB", "Templates"];
  const subtitles = ["Nurse\nCSSD\nAdmin", "Routing\nPermissions\nActions", "Requests\nInventory\nBatches", "Users\nRequests\nTimeline", "Dashboards\nForms\nReports"];
  xs.forEach((x, i) => {
    slide.addShape(pptx.ShapeType.roundRect, { x, y: 2.15, w: 1.72, h: 1.15, rectRadius: 0.08, fill: { color: i % 2 === 0 ? C.mint : C.sky }, line: { color: "BFD8E6" } });
    slide.addText(labels[i], { x: x + 0.1, y: 2.37, w: 1.52, h: 0.24, fontFace: "Aptos Display", fontSize: 12, bold: true, color: C.ink, align: "center", margin: 0, fit: "shrink" });
    slide.addText(subtitles[i], { x: x + 0.1, y: 2.68, w: 1.52, h: 0.38, fontFace: "Aptos", fontSize: 8.2, color: C.slate, align: "center", margin: 0, fit: "shrink" });
    if (i < xs.length - 1) {
      slide.addShape(pptx.ShapeType.rightArrow, { x: x + 1.78, y: 2.48, w: 0.55, h: 0.35, fill: { color: C.teal }, line: { color: C.teal } });
    }
  });
  addSectionLabel(slide, "Main modules", 0.8, 4.28, 2.2);
  addBullets(slide, [
    "Authentication and role routing",
    "Instrument request management",
    "CSSD workflow transitions",
    "Sterilization batch management",
    "Inventory tracking and alerts",
    "Notifications, reports, and audit history",
  ], 0.8, 4.62, 5.2, 1.8, { fontSize: 12.8 });
  addSectionLabel(slide, "Technology stack", 7.0, 4.28, 2.2, C.blue);
  addBullets(slide, [
    "Django backend",
    "SQLite development database",
    "Django templates, HTML, CSS, JavaScript",
    "Custom email-based user model",
    "Role decorators and dashboard routing",
  ], 7.0, 4.62, 4.9, 1.65, { fontSize: 12.8 });
}

// Slide 7
{
  const slide = addSlideTitleOnly(7, "Core workflow", "One controlled lifecycle from request to delivery", "Every stage stores timestamps and operator information for traceability.");
  const stages = ["Requested", "Collected", "Cleaned", "Sterilized", "Packed", "Delivered"];
  stages.forEach((stage, i) => {
    const x = 0.75 + i * 2.05;
    slide.addShape(pptx.ShapeType.chevron, { x, y: 2.15, w: 1.72, h: 0.78, fill: { color: i === 0 ? C.teal : i === 5 ? C.green : C.blue }, line: { color: i === 0 ? C.teal : i === 5 ? C.green : C.blue } });
    slide.addText(stage, { x: x + 0.1, y: 2.39, w: 1.38, h: 0.22, fontFace: "Aptos", fontSize: 10.3, bold: true, color: C.white, align: "center", margin: 0, fit: "shrink" });
  });
  addNumbered(slide, [
    "Nurse submits request.",
    "CSSD staff collects instruments.",
    "Instruments are cleaned.",
    "Instruments are sterilized and linked to a batch.",
    "Instruments are packed.",
    "Nurse receives or marks final delivery.",
    "Hospital admin can audit the full history.",
  ], 0.9, 3.8, 5.5, 1.95, { fontSize: 13.3 });
  addPlaceholder(slide, "Add screenshot: request detail or lifecycle timeline", 7.0, 3.7, 5.0, 1.95);
}

// Slide 8
{
  const slide = addSlideTitleOnly(8, "Development process", "Built incrementally through feature branches", "Each feature added behavior, then tests, then integration into the shared development branch.");
  const items = [
    ["PROJ-4", "Authentication and role routing"],
    ["PROJ-6", "Department nurse requests"],
    ["PROJ-8", "Nurse and CSSD dashboards"],
    ["PROJ-17-21", "Status lifecycle transitions"],
    ["PROJ-24", "Assign operator to batch"],
    ["PROJ-27", "Inventory shortage alerts"],
    ["PROJ-29", "Estimated completion time"],
    ["PROJ-31", "Audit history and hospital reports"],
  ];
  items.forEach((it, i) => {
    const y = 1.9 + i * 0.48;
    slide.addText(it[0], { x: 0.8, y, w: 1.15, h: 0.22, fontFace: "Aptos", fontSize: 10.2, bold: true, color: C.tealDark, margin: 0, fit: "shrink" });
    slide.addShape(pptx.ShapeType.rect, { x: 2.0, y: y + 0.11, w: 0.52, h: 0.03, fill: { color: "CBD5E1" }, line: { color: "CBD5E1" } });
    slide.addText(it[1], { x: 2.65, y, w: 4.5, h: 0.22, fontFace: "Aptos", fontSize: 10.8, color: C.ink, margin: 0, fit: "shrink" });
  });
  addCard(slide, "Team process", "Build one feature at a time\nAdd tests for each feature\nMerge completed branches into dev\nFix conflicts and regressions before release", 7.75, 2.08, 3.9, 2.25, C.blue);
  addPlaceholder(slide, "Optional screenshot: GitHub PR / branch list", 7.75, 4.75, 3.9, 1.0);
}

// Slide 9
{
  const slide = addSlideTitleOnly(9, "Testing strategy", "Quality was checked at unit, integration, and system levels", "Testing focused on correctness, role enforcement, state transitions, and stability.");
  addCard(slide, "Unit testing", "Model methods\nForm validation\nUser roles\nInventory status logic\nETA calculations", 0.78, 1.95, 3.45, 2.0, C.teal);
  addCard(slide, "Integration testing", "Login and redirects\nView/model/database behavior\nRequest creation\nStatus transitions\nBatch creation\nAccess control", 4.78, 1.95, 3.45, 2.0, C.blue);
  addCard(slide, "System testing", "Full workflow in browser\nlocalhost testing\nRole verification\nInvalid input stability checks", 8.78, 1.95, 3.45, 2.0, C.green);
  slide.addText("Latest verification", { x: 0.85, y: 4.74, w: 2.5, h: 0.32, fontFace: "Aptos Display", fontSize: 16, bold: true, color: C.ink, margin: 0 });
  slide.addText("281", { x: 0.85, y: 5.18, w: 1.65, h: 0.62, fontFace: "Aptos Display", fontSize: 39, bold: true, color: C.tealDark, margin: 0 });
  slide.addText("tests passed", { x: 2.45, y: 5.39, w: 1.8, h: 0.28, fontFace: "Aptos", fontSize: 13, bold: true, color: C.slate, margin: 0 });
  slide.addText("87.27%", { x: 4.55, y: 5.18, w: 2.05, h: 0.62, fontFace: "Aptos Display", fontSize: 39, bold: true, color: C.blue, margin: 0 });
  slide.addText("coverage", { x: 6.6, y: 5.39, w: 1.2, h: 0.28, fontFace: "Aptos", fontSize: 13, bold: true, color: C.slate, margin: 0 });
  addPlaceholder(slide, "Add screenshot: pytest or coverage output", 8.35, 4.72, 3.85, 1.32);
}

// Slide 10
{
  const slide = addSlideTitleOnly(10, "Bugs found and quality improvements", "Testing exposed the most important risks: permissions and data integrity", "The biggest lesson was to test from the wrong user's perspective.");
  addSectionLabel(slide, "Important bugs discovered", 0.75, 1.86, 3.5, C.red);
  addBullets(slide, [
    "Any logged-in user could trigger CSSD status changes.",
    "Users could access CSSD request details without proper authorization.",
    "Non-nurse users could confirm delivery.",
    "Negative quantities could incorrectly increase stock.",
    "Nurse accounts could log in through the staff portal.",
  ], 0.78, 2.2, 5.55, 2.45, { fontSize: 13.2 });
  addSectionLabel(slide, "Fixes and improvements", 7.0, 1.86, 3.5, C.green);
  addBullets(slide, [
    "Added stricter role checks.",
    "Improved request ownership validation.",
    "Added quantity validation.",
    "Protected CSSD-only endpoints.",
    "Added tests to prevent regressions.",
  ], 7.0, 2.2, 4.7, 2.15, { fontSize: 13.8 });
  slide.addShape(pptx.ShapeType.roundRect, { x: 1.0, y: 5.35, w: 10.95, h: 0.7, rectRadius: 0.08, fill: { color: "FFF7ED" }, line: { color: "FED7AA" } });
  slide.addText("Key lesson: security and access control must be tested from the perspective of users who should not be allowed to perform the action.", {
    x: 1.25,
    y: 5.58,
    w: 10.45,
    h: 0.22,
    fontFace: "Aptos",
    fontSize: 12.2,
    bold: true,
    color: "9A3412",
    margin: 0,
    fit: "shrink",
  });
}

// Slide 11
{
  const slide = addSlideTitleOnly(11, "Release plan", "Version 1.0 focused on a stable demonstrable core", "The roadmap leaves clear optional enhancements for post-submission development.");
  const phases = [
    ["1", "Requirements and database design"],
    ["2", "Authentication and roles"],
    ["3", "Nurse request and CSSD modules"],
    ["4", "Sterilization workflow stages"],
    ["5", "Dashboards and monitoring"],
    ["6", "Integration testing and bug fixing"],
    ["7", "Final validation and submission"],
  ];
  phases.forEach((p, i) => {
    const x = 0.8 + i * 1.72;
    slide.addShape(pptx.ShapeType.ellipse, { x, y: 2.03, w: 0.48, h: 0.48, fill: { color: i < 5 ? C.teal : C.amber }, line: { color: i < 5 ? C.teal : C.amber } });
    slide.addText(p[0], { x, y: 2.17, w: 0.48, h: 0.13, fontFace: "Aptos", fontSize: 8.5, bold: true, color: C.white, align: "center", margin: 0 });
    slide.addText(p[1], { x: x - 0.18, y: 2.72, w: 0.85, h: 0.74, fontFace: "Aptos", fontSize: 8.1, color: C.ink, align: "center", margin: 0, fit: "shrink" });
    if (i < phases.length - 1) {
      slide.addShape(pptx.ShapeType.rect, { x: x + 0.52, y: 2.25, w: 1.05, h: 0.04, fill: { color: "CBD5E1" }, line: { color: "CBD5E1" } });
    }
  });
  addSectionLabel(slide, "Version 1.1 / post-submission enhancements", 0.9, 4.2, 4.3, C.blue);
  addBullets(slide, [
    "Estimated completion time",
    "Inventory shortage alerts",
    "Daily sterilization reports",
    "Audit history search",
    "Enhanced notifications",
    "Additional management roles",
  ], 0.9, 4.56, 5.2, 1.58, { fontSize: 12.7 });
  addPlaceholder(slide, "Optional screenshot: release plan table", 7.0, 4.28, 4.7, 1.45);
}

// Slide 12
{
  const slide = addSlideTitleOnly(12, "Challenges faced", "The hard parts were coordination, permissions, and state correctness", "Most issues came from integrating separately built features into one real workflow.");
  addBullets(slide, [
    "Managing many feature branches and merge conflicts.",
    "Keeping role permissions consistent across pages.",
    "Connecting frontend templates with real Django data.",
    "Handling state transitions without allowing invalid skips.",
    "Maintaining test coverage while adding new features.",
    "Balancing project scope with semester deadlines.",
  ], 0.82, 2.05, 5.8, 3.35, { fontSize: 15 });
  slide.addShape(pptx.ShapeType.roundRect, { x: 7.05, y: 2.08, w: 4.55, h: 2.25, rectRadius: 0.08, fill: { color: C.navy }, line: { color: C.navy } });
  slide.addText("Specific challenge", { x: 7.38, y: 2.46, w: 3.8, h: 0.28, fontFace: "Aptos Display", fontSize: 15, bold: true, color: C.white, margin: 0 });
  slide.addText("The lifecycle workflow required careful validation because every status depends on the previous status.", {
    x: 7.38,
    y: 2.94,
    w: 3.8,
    h: 0.72,
    fontFace: "Aptos",
    fontSize: 14,
    color: "D7ECF4",
    margin: 0,
    fit: "shrink",
  });
  addPlaceholder(slide, "Optional screenshot: conflict / PR / failing test", 7.05, 4.78, 4.55, 0.9);
}

// Slide 13
{
  const slide = addSlideTitleOnly(13, "Lessons learned", "The project made software engineering practices visible", "The strongest lessons came from role safety, integration testing, and scope control.");
  addCard(slide, "Technical lessons", "Role-based access must be designed early\nState machines need clear rules and tests\nIntegration tests catch issues unit tests miss\nSeed data makes demos easier\nSmall branches are easier to review", 0.85, 2.05, 5.1, 2.85, C.teal);
  addCard(slide, "Team and process lessons", "Scope control matters\nDocumentation helps handoff and debugging\nTesting should start before the final phase\nA working core is better than many unfinished features", 7.05, 2.05, 5.1, 2.85, C.blue);
  slide.addText("From prototype to process: the project was not only about building screens, but about proving behavior with tests and controlled release steps.", {
    x: 1.0,
    y: 5.65,
    w: 11.0,
    h: 0.38,
    fontFace: "Aptos",
    fontSize: 14.2,
    bold: true,
    color: C.tealDark,
    align: "center",
    margin: 0,
    fit: "shrink",
  });
}

// Slide 14
{
  const slide = pptx.addSlide();
  slide.background = { color: C.navy };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.18, fill: { color: C.teal }, line: { color: C.teal } });
  slide.addText("Final outcome", {
    x: 0.7,
    y: 0.72,
    w: 5.0,
    h: 0.62,
    fontFace: "Aptos Display",
    fontSize: 30,
    bold: true,
    color: C.white,
    margin: 0,
    fit: "shrink",
  });
  slide.addText("The final system turns a manual CSSD workflow into a traceable, role-based, and tested digital process.", {
    x: 0.72,
    y: 1.55,
    w: 7.4,
    h: 0.7,
    fontFace: "Aptos",
    fontSize: 17,
    color: "D7ECF4",
    margin: 0,
    fit: "shrink",
  });
  const outcomes = [
    "Nurse request portal",
    "CSSD workflow dashboard",
    "Full lifecycle tracking",
    "Inventory alerts",
    "Batch operator assignment",
    "Notifications",
    "Hospital reports",
    "Searchable audit history",
    "Verified tests and coverage",
  ];
  outcomes.forEach((t, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    slide.addShape(pptx.ShapeType.roundRect, { x: 0.8 + col * 3.85, y: 3.0 + row * 0.72, w: 3.2, h: 0.42, rectRadius: 0.08, fill: { color: "183B5A" }, line: { color: "2D5B7A" } });
    slide.addText(t, { x: 1.0 + col * 3.85, y: 3.125 + row * 0.72, w: 2.8, h: 0.14, fontFace: "Aptos", fontSize: 9.8, bold: true, color: C.white, align: "center", margin: 0, fit: "shrink" });
  });
  slide.addText("Thank you", { x: 0.74, y: 6.34, w: 2.7, h: 0.36, fontFace: "Aptos Display", fontSize: 21, bold: true, color: C.white, margin: 0 });
  addPlaceholder(slide, "Add final screenshot: best app view", 8.45, 0.88, 3.75, 1.6);
  slide.addNotes("Close by emphasizing that the system demonstrates requirements, architecture, development, testing, and release planning as one complete project journey.");
}

pptx.writeFile({ fileName: "presentation_output/CSSD_Management_System_Project_Journey.pptx" });
