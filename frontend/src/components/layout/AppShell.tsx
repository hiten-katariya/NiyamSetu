import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export const AppShell: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-niyam-bg flex flex-col">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      <div className="lg:pl-64 flex flex-col flex-1">
        <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />
        
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <div className="liquid-container">
            <Outlet />
          </div>
        </main>

        <footer className="py-4 px-6 text-center text-xs text-niyam-text-muted border-t border-niyam-border bg-niyam-surface">
          NiyamSetu Platform — Autonomous statutory decisions are strictly disabled. Authorised human review required for all approvals.
        </footer>
      </div>
    </div>
  );
};
