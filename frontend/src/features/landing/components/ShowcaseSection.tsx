import React, { useState } from 'react';
import { CircularCarousel } from '../../../components/CircularCarousel/CircularCarousel';
import { Sparkles, MoveHorizontal } from 'lucide-react';
import { CAROUSEL_MODULES } from './carouselData';

export const ShowcaseSection: React.FC = () => {
  const [activeModule, setActiveModule] = useState(0);

  return (
    <section className="py-20 bg-niyam-bg border-y border-niyam-border/70 relative overflow-hidden" id="architecture">
      <div className="liquid-container">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-niyam-primary-tint/80 border border-niyam-primary/20 text-niyam-primary text-xs font-bold uppercase tracking-wider mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Interactive 3D System Architecture</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-niyam-text tracking-tight">
            Six Interlocking Modules. One Unified Process.
          </h2>
          <p className="mt-3 text-base sm:text-lg text-niyam-text-muted">
            Explore the core architectural components of NiyamSetu. Drag or swipe the 3D ring to inspect how application routing, deadline intelligence, and compliance modules harmonize.
          </p>
        </div>

        {/* 3D Circular Carousel Container */}
        <div className="relative w-full h-[540px] sm:h-[580px] rounded-3xl bg-gradient-to-b from-white/90 via-white/40 to-transparent border border-white/60 shadow-xl backdrop-blur-md overflow-hidden p-2 sm:p-4">
          {/* Subtle instruction pill */}
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/90 border border-niyam-border/80 shadow-xs text-[11px] font-semibold text-niyam-text-muted">
            <MoveHorizontal className="w-3.5 h-3.5 text-niyam-primary" />
            <span>Drag, scroll, or use arrow keys to spin</span>
          </div>

          <CircularCarousel
            items={CAROUSEL_MODULES}
            preset="cylinder"
            intro="rise"
            cardWidth={260}
            aspectRatio={1}
            gap={28}
            speed={12}
            captions={true}
            autoplay="drift"
            fadeColor="#F6F8FB"
            cornerRadius={16}
            onChange={(idx) => setActiveModule(idx)}
          />
        </div>

        {/* Quick Module Navigation Pills */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-8">
          {CAROUSEL_MODULES.map((m, idx) => (
            <div
              key={m.title}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all border ${
                activeModule === idx
                  ? 'bg-niyam-primary text-white border-niyam-primary shadow-xs'
                  : 'bg-white text-niyam-text-muted border-niyam-border hover:bg-niyam-surface-alt'
              }`}
            >
              {m.title}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
