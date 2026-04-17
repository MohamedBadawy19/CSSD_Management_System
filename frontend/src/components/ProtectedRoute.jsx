import { Navigate } from "react-router-dom";

/**
 * ProtectedRoute
 * - Redirects to /login if no token in localStorage
 * - Redirects to /login if role doesn't match allowedRole
 */
export default function ProtectedRoute({ children, allowedRole }) {
  const token = localStorage.getItem("token");
  const role  = localStorage.getItem("role");

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole && role !== allowedRole) {
    // Wrong role → send them to their correct dashboard
    if (role === "cssd")  return <Navigate to="/cssd"  replace />;
    if (role === "nurse") return <Navigate to="/nurse" replace />;
    return <Navigate to="/login" replace />;
  }

  return children;
}
