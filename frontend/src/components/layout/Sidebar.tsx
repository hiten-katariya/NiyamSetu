import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileSpreadsheet,
  CalendarClock,
  ShieldCheck,
  FolderLock,
  BellRing,
  FileBarChart2,
  Sliders,
  LogOut,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Applications', path: '/applications', icon: FileSpreadsheet },
  { name: 'EVC Queue', path: '/evc', icon: CalendarClock },
  { name: 'Compliance & Undertakings', path: '/compliance', icon: ShieldCheck },
  { name: 'Document Validity', path: '/documents', icon: FolderLock },
  { name: 'Notifications & Alerts', path: '/notifications', icon: BellRing },
  { name: 'Reports & Audit', path: '/reports', icon: FileBarChart2 },
  { name: 'Admin Configuration', path: '/admin', icon: Sliders },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-niyam-surface border-r border-niyam-border flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-16 flex items-center justify-between px-6 border-b border-niyam-border">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-niyam-primary text-white font-bold flex items-center justify-center text-xs">
              NS
            </div>
            <span className="font-bold text-niyam-text text-base">NiyamSetu</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-niyam-text-muted hover:text-niyam-text lg:hidden"
            aria-label="Close menu"
          >
            ✕
          </button>
        </div>

        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => onClose()}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-niyam-primary text-white shadow-xs'
                      : 'text-niyam-text hover:bg-niyam-surface-alt hover:text-niyam-primary'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="p-4 border-t border-niyam-border">
          <div className="p-3 rounded-md bg-niyam-surface-alt border border-niyam-border mb-3">
            <p className="text-xs font-semibold text-niyam-text">Demonstration Build</p>
            <p className="text-[11px] text-niyam-text-muted mt-0.5">Phase 1 Foundation Setup</p>
          </div>
          <NavLink
            to="/login"
            className="flex items-center gap-2 text-xs font-semibold text-niyam-text-muted hover:text-niyam-status-danger px-2 py-1.5 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Switch / Sign Out</span>
          </NavLink>
        </div>
      </aside>
    </>
  );
};
