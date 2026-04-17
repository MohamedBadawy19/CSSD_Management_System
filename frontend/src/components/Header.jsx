import React from 'react';

export default function Header({ title, subtitle }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-title">
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        <div className="system-status">
          <div className="status-dot"></div>
          <span>System Online</span>
        </div>
      </div>
    </header>
  );
}
