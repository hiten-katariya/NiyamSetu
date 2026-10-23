import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, ShieldCheck, Lock } from 'lucide-react';
import { useAuth } from '../../../app/AuthContext';

export const FinalCta: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <section className="py-24 bg-gradient-to-br from-[#1F4E8C] via-[#173D70] to-[#0F284B] text-white relative overflow-hidden">
      {/* Decorative background glows */}
      <div className="absolute inset-0 pointer-events-none select-none opacity-20">
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-blue-400 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-teal-400 rounded-full blur-3xl" />
      </div>

      <div className="liquid-container relative z-10 text-center max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 border border-white/20 backdrop-blur-sm text-xs font-semibold text-blue-200 mb-6">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Strict Server-Side Authorization &bull; Verified Institutional Access</span>
        </div>

        <h2 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight">
          Bring Clarity to Every Stage.
        </h2>

        <p className="mt-5 text-base sm:text-lg text-blue-100 max-w-2xl mx-auto font-normal leading-relaxed">
          Explore a more structured way to manage approval workflows, compliance activity, and institutional records across every regional directorate.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={() => navigate(isAuthenticated ? '/dashboard' : '/login')}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-xl bg-white text-niyam-primary text-base font-extrabold shadow-lg hover:bg-blue-50 transition-all hover:scale-105 focus-visible:ring-2 focus-visible:ring-white"
          >
            <span>{isAuthenticated ? 'Open Authorized Dashboard' : 'Access Authorized Portal'}</span>
            <ArrowRight className="w-5 h-5 text-niyam-primary" />
          </button>
          <a
            href="#security"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-4 rounded-xl bg-white/10 text-white border border-white/20 text-base font-bold hover:bg-white/20 transition-all backdrop-blur-xs"
          >
            <Lock className="w-4 h-4" />
            <span>Security Architecture</span>
          </a>
        </div>

        <p className="mt-6 text-xs text-blue-200/80">
          * Account access is provisioned by participating institutions and authorized regional offices.
        </p>
      </div>
    </section>
  );
};
