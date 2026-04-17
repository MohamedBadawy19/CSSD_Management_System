// StatusBadge.jsx — shows a colored pill for request status

const styles = {
  pending:    { background: "#fef3c7", color: "#92400e", label: "Pending" },
  processing: { background: "#dbeafe", color: "#1e40af", label: "Processing" },
  ready:      { background: "#d1fae5", color: "#065f46", label: "Ready" },
  delivered:  { background: "#ede9fe", color: "#4c1d95", label: "Delivered" },
  rejected:   { background: "#fee2e2", color: "#991b1b", label: "Rejected" },
};

export default function StatusBadge({ status }) {
  const s = styles[status] || { background: "#f3f4f6", color: "#374151", label: status };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.35rem",
        padding: "0.25rem 0.7rem",
        borderRadius: "999px",
        fontSize: "0.75rem",
        fontWeight: 600,
        background: s.background,
        color: s.color,
        whiteSpace: "nowrap",
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: s.color,
          flexShrink: 0,
        }}
      />
      {s.label}
    </span>
  );
}
