import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import LoginPage from "./pages/LoginPage";

export default function App() {
  return (
    <div className="app-container">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/nurse/login" element={<LoginPage role="nurse" />} />
        <Route path="/cssd/login" element={<LoginPage role="staff" />} />
      </Routes>
    </div>
  );
}