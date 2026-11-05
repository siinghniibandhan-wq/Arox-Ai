import { useState } from "react";
import { APPROVALS, AUDIT, BRANDS, TASKS } from "./sample.js";

const STATUS_LABEL = {
  waiting_approval: "Waiting for approval",
  running: "Running",
  completed: "Completed",
  rejected: "Rejected",
  pending: "Waiting for approval",
  approved: "Approved",
};

const ACTION_LABEL = {
  task_created: "Task created",
  approval_approved: "Approved",
  approval_rejected: "Rejected",
};

function when(ms) {
  const mins = Math.max(1, Math.round((Date.now() - ms) / 60000));
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours} hr ago`;
  return `${Math.round(hours / 24)} days ago`;
}

export default function App() {
  const [tab, setTab] = useState("approvals");
  const [tasks, setTasks] = useState(TASKS);
  const [approvals, setApprovals] = useState(APPROVALS);
  const [audit, setAudit] = useState(AUDIT);
  const [toast, setToast] = useState("");

  const taskById = (id) => tasks.find((t) => t.id === id);
  const pending = approvals.filter((a) => a.status === "pending");

  function decide(approval, approve) {
    const status = approve ? "approved" : "rejected";
    const task = taskById(approval.taskId);
    const now = Date.now();
    setApprovals((list) =>
      list.map((a) => (a.id === approval.id ? { ...a, status, decidedAt: now } : a))
    );
    setTasks((list) =>
      list.map((t) =>
        t.id === approval.taskId ? { ...t, status: approve ? "running" : "rejected" } : t
      )
    );
    setAudit((list) => [
      { id: `l${now}`, action: `approval_${status}`, target: `task:${approval.taskId}`, brandId: task.brandId, at: now },
      ...list,
    ]);
    setToast(approve ? "Approved. This was sample data." : "Rejected. This was sample data.");
    window.setTimeout(() => setToast(""), 3000);
  }

  return (
    <div className="shell">
      <header className="top">
        <h1>KPMC Chief of Staff</h1>
        <p className="sub">Approvals for the owner</p>
      </header>

      <p className="notice" role="note">
        Sample data. This page is not connected to your server yet, so nothing you
        tap here changes anything real.
      </p>

      <nav className="tabs" aria-label="Sections">
        {[
          ["approvals", `Approvals${pending.length ? ` (${pending.length})` : ""}`],
          ["tasks", "Tasks"],
          ["audit", "Audit log"],
        ].map(([key, label]) => (
          <button
            key={key}
            className={tab === key ? "tab on" : "tab"}
            aria-current={tab === key ? "page" : undefined}
            onClick={() => setTab(key)}
          >
            {label}
          </button>
        ))}
      </nav>

      <main>
        {tab === "approvals" && (
          <section aria-label="Approvals">
            {approvals.length === 0 && (
              <p className="empty">Nothing waiting. Tasks you send with /task in Telegram appear here.</p>
            )}
            {approvals.map((a) => {
              const task = taskById(a.taskId);
              const open = a.status === "pending";
              return (
                <article key={a.id} className={`card ${a.status}`}>
                  <p className="text">{task.text}</p>
                  <p className="meta">Tool: {a.tool}</p>
                  <p className="meta">{BRANDS[task.brandId]}</p>
                  <p className="meta">Sent {when(task.at)}</p>
                  {open ? (
                    <div className="actions">
                      <button className="btn yes" onClick={() => decide(a, true)}>
                        Approve
                      </button>
                      <button className="btn no" onClick={() => decide(a, false)}>
                        Reject
                      </button>
                    </div>
                  ) : (
                    <p className="decided">
                      {STATUS_LABEL[a.status]} by owner, {when(a.decidedAt)}. Decisions are final.
                    </p>
                  )}
                </article>
              );
            })}
          </section>
        )}

        {tab === "tasks" && (
          <section aria-label="Tasks">
            {tasks.map((t) => (
              <article key={t.id} className={`card ${t.status}`}>
                <p className="text">{t.text}</p>
                <p className="meta">{STATUS_LABEL[t.status]}</p>
                <p className="meta">{BRANDS[t.brandId]}</p>
                <p className="meta">{when(t.at)}</p>
              </article>
            ))}
          </section>
        )}

        {tab === "audit" && (
          <section aria-label="Audit log">
            {audit.map((l) => (
              <article key={l.id} className="card plain">
                <p className="text">{ACTION_LABEL[l.action] || l.action}</p>
                <p className="meta">{l.target}</p>
                <p className="meta">Brand: {BRANDS[l.brandId]}</p>
                <p className="meta">{when(l.at)}</p>
              </article>
            ))}
          </section>
        )}
      </main>

      {toast && (
        <div className="toast" role="status">
          {toast}
        </div>
      )}
    </div>
  );
}
