import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Menu, X, ArrowRight, User } from 'lucide-react';
import { useAuth } from '../../../app/AuthContext';

export const Navbar: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Overview', href: '#overview' },
    { name: 'Capabilities', href: '#capabilities' },
    { name: 'Workflow', href: '#workflow' },
    { name: 'Security & Governance', href: '#security' },
    { name: 'Stakeholders', href: '#stakeholders' },
    { name: 'FAQ', href: '#faq' },
  ];

  const handleNavClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    const target = document.querySelector(href);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-white/85 backdrop-blur-md border-b border-niyam-border/80 shadow-xs py-3'
          : 'bg-transparent border-b border-transparent py-4'
      }`}
      role="navigation"
      aria-label="Main Navigation"
    >
      <div className="liquid-container !py-0 flex items-center justify-between">
        {/* Brand */}
        <Link
          to="/landing"
          className="flex items-center gap-3 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-niyam-focus rounded-lg p-1"
          aria-label="NiyamSetu Home"
        >
          <div className="w-9 h-9 rounded-lg bg-niyam-primary flex items-center justify-center shadow-xs overflow-hidden border border-white/20 transition-transform group-hover:scale-105">
            <img
              src="/logo.png"
              alt="NiyamSetu Logo"
              className="w-full h-full object-contain p-1"
              onError={(e) => {
                // Fallback to text initials if image fails to load
                (e.currentTarget as HTMLElement).style.display = 'none';
                e.currentTarget.parentElement!.innerHTML = '<span class="text-white font-black text-sm">NS</span>';
              }}
            />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-extrabold text-niyam-primary tracking-tight leading-none group-hover:text-niyam-focus transition-colors">
              NiyamSetu
            </span>
            <span className="text-[10px] font-semibold text-niyam-text-muted tracking-wider uppercase mt-0.5">
              AICTE Compliance Platform
            </span>
          </div>
        </Link>

        {/* Desktop Links */}
        <div className="hidden lg:flex items-center gap-7">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              onClick={(e) => handleNavClick(e, link.href)}
              className="text-sm font-semibold text-niyam-text-muted hover:text-niyam-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-niyam-focus rounded px-1.5 py-0.5"
            >
              {link.name}
            </a>
          ))}
        </div>

        {/* Actions / Auth */}
        <div className="hidden sm:flex items-center gap-3">
          {isAuthenticated ? (
            <button
              onClick={() => navigate('/')}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-niyam-primary text-white text-sm font-bold shadow-xs hover:bg-niyam-primary-hover transition-all focus-visible:ring-2 focus-visible:ring-niyam-focus"
            >
              <User className="w-4 h-4" />
              <span>Go to Dashboard</span>
              <ArrowRight className="w-4 h-4 ml-0.5" />
            </button>
          ) : (
            <>
              <Link
                to="/login"
                className="px-4 py-2 text-sm font-bold text-niyam-primary hover:text-niyam-primary-hover hover:bg-niyam-primary-tint/60 rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-niyam-focus"
              >
                Sign In
              </Link>
              <a
                href="#overview"
                onClick={(e) => handleNavClick(e, '#overview')}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-niyam-primary text-white text-sm font-bold shadow-xs hover:bg-niyam-primary-hover transition-all focus-visible:ring-2 focus-visible:ring-niyam-focus hover:shadow-md"
              >
                <span>Explore Platform</span>
                <ArrowRight className="w-4 h-4" />
              </a>
            </>
          )}
        </div>

        {/* Mobile Hamburger Toggle */}
        <div className="flex sm:hidden items-center gap-2">
          {isAuthenticated && (
            <button
              onClick={() => navigate('/')}
              className="px-3 py-1.5 text-xs font-bold bg-niyam-primary text-white rounded-md"
            >
              Portal
            </button>
          )}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-niyam-text-muted hover:text-niyam-text hover:bg-niyam-surface-alt transition-colors focus-visible:ring-2 focus-visible:ring-niyam-focus"
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-menu"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div
          id="mobile-menu"
          className="lg:hidden bg-white/95 backdrop-blur-xl border-b border-niyam-border px-6 py-6 shadow-xl animate-in slide-in-from-top-2 duration-200"
        >
          <div className="flex flex-col gap-4">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                onClick={(e) => handleNavClick(e, link.href)}
                className="text-base font-semibold text-niyam-text hover:text-niyam-primary py-2 border-b border-niyam-border/40"
              >
                {link.name}
              </a>
            ))}
            <div className="pt-2 flex flex-col gap-2.5">
              {isAuthenticated ? (
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    navigate('/dashboard');
                  }}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-lg bg-niyam-primary text-white font-bold text-sm"
                >
                  <User className="w-4 h-4" />
                  <span>Go to Authorized Dashboard</span>
                </button>
              ) : (
                <>
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-2.5 rounded-lg border border-niyam-border font-bold text-sm text-niyam-primary hover:bg-niyam-surface-alt"
                  >
                    Sign In
                  </Link>
                  <a
                    href="#overview"
                    onClick={(e) => handleNavClick(e, '#overview')}
                    className="w-full text-center py-2.5 rounded-lg bg-niyam-primary text-white font-bold text-sm hover:bg-niyam-primary-hover shadow-xs"
                  >
                    Explore Platform
                  </a>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};
