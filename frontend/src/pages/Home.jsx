import React from "react";
import { useNavigate } from "react-router-dom";
import { Stethoscope, Shield, ArrowRight, Activity, ShieldAlert } from "lucide-react";
import Header from "../components/Header";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="page-wrapper">
      <Header 
        title="Hospital Management System" 
        subtitle="Central Sterile Supply Department" 
      />

      <main className="main-content">
        <div className="container-wrapper">
          
          <div className="welcome-section">
            <div className="app-icon">
              <Activity size={36} />
            </div>
            <h2 className="welcome-title">Welcome to CSSD Management</h2>
            <p className="welcome-subtitle">Please select your role to continue</p>
          </div>

          <div className="role-cards">
            
            <button 
              className="role-card"
              onClick={() => navigate("/nurse/login")}
            >
              <div className="card-header">
                <div className="card-icon teal">
                  <Stethoscope size={28} />
                </div>
                <ArrowRight className="card-arrow" size={24} />
              </div>
              <h3 className="card-title">Nurse Portal</h3>
              <p className="card-desc">
                Submit instrument requests, track status, and manage
                urgent requests for patient care.
              </p>
              <ul className="card-features teal">
                <li>Create instrument requests</li>
                <li>Track request status</li>
                <li>View request history</li>
              </ul>
            </button>

            <button 
              className="role-card"
              onClick={() => navigate("/cssd/login")}
            >
              <div className="card-header">
                <div className="card-icon blue">
                  <Shield size={28} />
                </div>
                <ArrowRight className="card-arrow" size={24} />
              </div>
              <h3 className="card-title">CSSD Staff Portal</h3>
              <p className="card-desc">
                Process requests, update instrument status, manage
                inventory, and track workflow stages.
              </p>
              <ul className="card-features blue">
                <li>Process instrument requests</li>
                <li>Update workflow status</li>
                <li>Monitor inventory alerts</li>
              </ul>
            </button>

          </div>

          <div className="security-notice notice-warning">
            <ShieldAlert className="security-icon" size={20} />
            <div className="security-content">
              <h4>Security Notice</h4>
              <p>
                This system contains confidential patient and medical information. Access is restricted to authorized hospital personnel only. Unauthorized access is prohibited and will be prosecuted.
              </p>
            </div>
          </div>

        </div>
      </main>

      <footer className="footer">
        <p>Need help? Contact IT support: <a href="tel:1-800-123-4567">1-800-123-4567</a></p>
      </footer>
    </div>
  );
}