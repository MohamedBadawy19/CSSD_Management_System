import { useNavigate } from "react-router-dom";

export default function NotFound() {
  const navigate = useNavigate();
  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      background: "#f3f4f6",
      gap: "1rem",
      padding: "2rem",
      textAlign: "center"
    }}>
      <h1 style={{ fontSize: "5rem", fontWeight: 800, color: "#1a56db", lineHeight: 1 }}>404</h1>
      <h2 style={{ fontSize: "1.5rem", color: "#111827" }}>Page Not Found</h2>
      <p style={{ color: "#6b7280", maxWidth: 360 }}>
        The page you're looking for doesn't exist or you don't have permission to view it.
      </p>
      <button
        onClick={() => navigate("/login")}
        style={{
          marginTop: "0.5rem",
          padding: "0.75rem 1.5rem",
          background: "#1a56db",
          color: "white",
          border: "none",
          borderRadius: "10px",
          fontSize: "0.95rem",
          fontWeight: 600,
          cursor: "pointer"
        }}
      >
        Back to Login
      </button>
    </div>
  );
}
