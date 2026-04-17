import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Mail, Lock, Eye, EyeOff, LogIn, ShieldAlert, ArrowLeft, Stethoscope, Activity } from "lucide-react";
import Header from "../components/Header";

export default function LoginPage({ role = "nurse" }) {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const isNurse = role === "nurse";

  // Dynamic content based on role
  const pageContent = {
    headerTitle: isNurse ? "Nurse Portal" : "CSSD Management System",
    headerSubtitle: isNurse ? "Instrument Request Management" : "Central Sterile Supply Department",
    icon: isNurse ? <Stethoscope size={32} /> : <Activity size={32} />, // Using Activity since it matched the blue icon better visually
    themeClass: isNurse ? "teal" : "blue",
    cardTitle: isNurse ? "Nurse Login" : "Staff Login",
    cardSubtitle: isNurse ? "Enter your credentials to access the portal" : "Enter your credentials to access CSSD",
    emailPlaceholder: isNurse ? "nurse@hospital.com" : "staff@hospital.com",
    buttonText: isNurse ? "Sign In to Portal" : "Sign In to CSSD"
  };

  const handleLogin = (e) => {
    e.preventDefault();
    setIsLoading(true);

    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      // Navigate somewhere or show success
      // navigate(isNurse ? "/nurse/dashboard" : "/cssd/dashboard");
      alert(`${pageContent.cardTitle} Successful`);
    }, 1500);
  };

  return (
    <>
      <Header 
        title={pageContent.headerTitle} 
        subtitle={pageContent.headerSubtitle} 
      />

      <main className="main-content">
        <div className="login-container-wrapper">
          
          <button 
            className="back-link" 
            onClick={() => navigate("/")}
            type="button"
          >
            <ArrowLeft size={16} />
             Back to role selection
          </button>

          <div className="login-card">
            
            <div className="login-header">
              <div className={`app-icon ${pageContent.themeClass}`}>
                {pageContent.icon}
              </div>
              <h2 className="login-title">{pageContent.cardTitle}</h2>
              <p className="login-subtitle">{pageContent.cardSubtitle}</p>
            </div>

            <form onSubmit={handleLogin}>
              
              <div className="form-group">
                <label htmlFor="email" className="form-label">Email Address</label>
                <div className="input-wrapper">
                  <Mail className="input-icon" size={18} />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={pageContent.emailPlaceholder}
                    className="form-input"
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="password" className="form-label">Password</label>
                <div className="input-wrapper">
                  <Lock className="input-icon" size={18} />
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="form-input"
                    required
                  />
                  <button
                    type="button"
                    className="btn-toggle-password"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <div className="form-actions">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    className="checkbox-input"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  Remember me
                </label>
                <a href="#" className="forgot-link">Forgot Password?</a>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className={`btn-submit ${pageContent.themeClass}`}
              >
                {isLoading ? (
                  <>
                    <div className="spinner"></div>
                    Signing In...
                  </>
                ) : (
                  <>
                    {pageContent.buttonText}
                    <LogIn size={18} />
                  </>
                )}
              </button>
            </form>

            <div className="security-notice notice-warning login-security-notice">
              <ShieldAlert className="security-icon" size={20} />
              <div className="security-content">
                <h4>Security Notice</h4>
                <p>
                  This system contains confidential patient information. Unauthorized access is prohibited and will be prosecuted.
                </p>
              </div>
            </div>

          </div>
        </div>
      </main>
    </>
  );
}
