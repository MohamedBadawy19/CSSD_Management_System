// ============================================================
//  CSSD Management System — Mock Data (Frontend Branch)
//  Replace this file's fetch calls with real API calls when
//  integrating with the Django backend.
// ============================================================

const MOCK = {
  currentUser: {
    id: 1,
    name: "Sara",
    email: "sara@hospital.com",
    role: "CSSD Technician",
    ward: "Central Sterile Supply",
  },

  requests: [
    { id: 1, requester: "nurse.ali@hospital.com", department: "Emergency", priority: "Urgent",   status: "Requested",   submitted_at: "2025-04-18 08:10", items: ["Surgical Scissors", "Forceps"] },
    { id: 2, requester: "nurse.mona@hospital.com", department: "ICU",       priority: "Normal",   status: "Collected",   submitted_at: "2025-04-18 07:45", items: ["Retractor", "Scalpel Handle"] },
    { id: 3, requester: "nurse.karim@hospital.com",department: "Surgery",   priority: "Urgent",   status: "Cleaned",     submitted_at: "2025-04-17 22:00", items: ["Needle Holder"] },
    { id: 4, requester: "nurse.dina@hospital.com", department: "Cardiology",priority: "Normal",   status: "Sterilized",  submitted_at: "2025-04-17 18:30", items: ["Clamp Set", "Trocar"] },
    { id: 5, requester: "nurse.sara@hospital.com", department: "Orthopedics",priority:"Normal",   status: "Packed",      submitted_at: "2025-04-17 15:00", items: ["Bone Drill Bit", "Retractor"] },
    { id: 6, requester: "nurse.hana@hospital.com", department: "Pediatrics",priority: "Normal",   status: "Delivered",   submitted_at: "2025-04-17 10:00", items: ["Forceps", "Probe"] },
    { id: 7, requester: "nurse.ramy@hospital.com", department: "General",   priority: "Urgent",   status: "Requested",   submitted_at: "2025-04-18 09:00", items: ["Electrocautery Tip"] },
    { id: 8, requester: "nurse.nour@hospital.com", department: "ICU",       priority: "Normal",   status: "Delivered",   submitted_at: "2025-04-16 14:00", items: ["Suction Tip", "Cannula"] },
    { id: 9, requester: "nurse.layla@hospital.com",department: "Emergency", priority: "Urgent",   status: "Cleaned",     submitted_at: "2025-04-18 06:30", items: ["Toothed Forceps"] },
    { id: 10,requester: "nurse.omar@hospital.com", department: "Neurology", priority: "Normal",   status: "Sterilized",  submitted_at: "2025-04-17 20:00", items: ["Micro-scissors", "Bipolar Forceps"] },
  ],

  inventory: [
    { id: 1, name: "Surgical Scissors",    category: "Cutting",    current_stock: 12, min_stock: 5 },
    { id: 2, name: "Forceps",              category: "Grasping",   current_stock: 0,  min_stock: 5 },
    { id: 3, name: "Retractor",            category: "Retracting", current_stock: 2,  min_stock: 5 },
    { id: 4, name: "Scalpel Handle",       category: "Cutting",    current_stock: 1,  min_stock: 5 },
    { id: 5, name: "Needle Holder",        category: "Suturing",   current_stock: 8,  min_stock: 5 },
    { id: 6, name: "Clamp Set",            category: "Clamping",   current_stock: 0,  min_stock: 5 },
    { id: 7, name: "Trocar",              category: "Access",     current_stock: 2,  min_stock: 3 },
    { id: 8, name: "Bone Drill Bit",       category: "Orthopedic", current_stock: 4,  min_stock: 3 },
    { id: 9, name: "Electrocautery Tip",   category: "Electro",    current_stock: 7,  min_stock: 5 },
    { id: 10,name: "Suction Tip",          category: "Suction",    current_stock: 0,  min_stock: 5 },
    { id: 11,name: "Micro-scissors",       category: "Cutting",    current_stock: 1,  min_stock: 3 },
    { id: 12,name: "Bipolar Forceps",      category: "Electro",    current_stock: 3,  min_stock: 5 },
    { id: 13,name: "Probe",                category: "Diagnostic", current_stock: 9,  min_stock: 3 },
    { id: 14,name: "Cannula",              category: "Access",     current_stock: 2,  min_stock: 5 },
    { id: 15,name: "Toothed Forceps",      category: "Grasping",   current_stock: 0,  min_stock: 5 },
  ],

  batches: [
    { id: 101, method: "Steam Autoclave", temperature: 134, duration: 18, status: "Completed", operator: "sara@hospital.com", created_at: "2025-04-18 07:00", notes: "Cycle 3 of today" },
    { id: 102, method: "ETO",             temperature: 55,  duration: 240,status: "In Progress",operator: "sara@hospital.com", created_at: "2025-04-18 09:30", notes: "Sensitive instruments" },
    { id: 103, method: "Steam Autoclave", temperature: 121, duration: 30, status: "Completed", operator: "ahmed@hospital.com",created_at: "2025-04-17 15:00", notes: "" },
  ],

  notifications: [
    { id: 1, message: "REQ-0002 has been collected by CSSD.", created_at: "2025-04-18 07:50", is_read: false },
    { id: 2, message: "REQ-0001 instruments have been cleaned.", created_at: "2025-04-18 09:00", is_read: false },
    { id: 3, message: "REQ-0006 has been delivered.", created_at: "2025-04-17 10:05", is_read: true },
  ],

  // ---- helpers ----
  getStats() {
    return {
      pending:     this.requests.filter(r => r.status === "Requested").length,
      in_progress: this.requests.filter(r => ["Collected","Cleaned","Sterilized","Packed"].includes(r.status)).length,
      completed:   this.requests.filter(r => r.status === "Delivered").length,
      alerts:      this.inventory.filter(i => i.current_stock < 3).length,
    };
  },
  getAlerts() {
    return this.inventory.filter(i => i.current_stock < 3);
  },
  pendingCount() { return this.requests.filter(r => r.status === "Requested").length; },
};
