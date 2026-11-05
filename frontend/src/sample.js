// Sample data shaped like the ai.tasks, ai.approvals and ai.audit_log tables.
// Replace this file with calls to the approvals API once it exists.
const ago = (minutes) => Date.now() - minutes * 60000;

export const BRANDS = { 1: "Super Bajaar", 3: "Personal" };

export const TASKS = [
  { id: "t1", text: "Send the weekly stock summary to the store managers", status: "waiting_approval", brandId: 1, at: ago(14) },
  { id: "t2", text: "Check that the n8n ping webhook is reachable", status: "waiting_approval", brandId: 1, at: ago(52) },
  { id: "t3", text: "Run the daily low stock check", status: "completed", brandId: 1, at: ago(26 * 60) },
  { id: "t4", text: "Draft the GST reconciliation note", status: "rejected", brandId: 3, at: ago(30 * 60) },
];

export const APPROVALS = [
  { id: "a1", taskId: "t1", tool: "ping", status: "pending" },
  { id: "a2", taskId: "t2", tool: "ping", status: "pending" },
];

export const AUDIT = [
  { id: "l1", action: "task_created", target: "task:t2", brandId: 1, at: ago(52) },
  { id: "l2", action: "task_created", target: "task:t1", brandId: 1, at: ago(14) },
];
