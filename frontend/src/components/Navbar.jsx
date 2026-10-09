import React from "react";
import { AVAILABLE_LANGUAGES } from "../translations/translations";

export default function Navbar({
  uiLang,
  onLanguageChange,
  theme,
  onToggleTheme,
  onClearChat,
  onToggleMobileSidebar,
  t
}) {
  return (
    <header className="navbar">
      <div className="nav-container">
        {/* Brand & Mobile Hamburger: Left Aligned */}
        <div className="nav-brand-group">
          {/* Mobile Sidebar Toggle Button */}
          <button
            type="button"
            className="mobile-sidebar-toggle-btn"
            onClick={onToggleMobileSidebar}
            aria-label="Toggle navigation menu"
            title="Open Menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>

          <div className="nav-brand">
            <div className="brand-icon">
              <svg
                className="brand-shield-svg"
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="m9 12 2 2 4-4" />
              </svg>
            </div>
            <div className="brand-text">
              <h1 className="brand-title">BharatInsure AI</h1>
              <p className="brand-subtitle">{t?.tagline || "Multilingual Fintech & Insurance Assistant"}</p>
            </div>
          </div>
        </div>

        {/* Navigation Actions: Right Aligned */}
        <div className="nav-actions">
          {/* Language Selector Dropdown */}
          <div className="lang-select-wrapper">
            <select
              className="clean-select lang-select"
              value={uiLang}
              onChange={(e) => onLanguageChange(e.target.value)}
              aria-label="Select Language"
            >
              {AVAILABLE_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.native} ({lang.name})
                </option>
              ))}
            </select>
          </div>

          {/* Theme Toggle Button */}
          <button
            type="button"
            className="nav-icon-btn"
            onClick={onToggleTheme}
            title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
            aria-label="Toggle theme"
          >
            {theme === "dark" ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="12" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>

          {/* Clear Chat Button */}
          <button
            type="button"
            className="nav-icon-btn"
            onClick={onClearChat}
            title={t?.clearChat || "Clear Conversation"}
            aria-label="Clear chat"
          >
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              <line x1="10" y1="11" x2="10" y2="17" />
              <line x1="14" y1="11" x2="14" y2="17" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
