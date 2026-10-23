import React, { useState, useEffect } from 'react';

interface InteractiveHeadlineProps {
  text: string;
  highlightWords?: string[];
  className?: string;
}

export const InteractiveHeadline: React.FC<InteractiveHeadlineProps> = ({
  text,
  highlightWords = [],
  className = '',
}) => {
  const [reducedMotion, setReducedMotion] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(media.matches);
    const listener = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, []);

  const words = text.split(' ');
  let charCounter = 0;

  return (
    <h1
      className={`text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-niyam-text leading-[1.12] ${className}`}
      aria-label={text}
    >
      {words.map((word, wordIdx) => {
        const isHighlight = highlightWords.some(
          (hw) => hw.toLowerCase() === word.replace(/[^a-zA-Z]/g, '').toLowerCase()
        );

        return (
          <span key={wordIdx} className="inline-block whitespace-nowrap mr-[0.3em]">
            {word.split('').map((char, charIdx) => {
              const currentGlobalIndex = charCounter++;
              const isHovered = hoveredIndex === currentGlobalIndex;
              const isNeighbor =
                hoveredIndex !== null && Math.abs(hoveredIndex - currentGlobalIndex) === 1;

              // Calculate interactive slice / lift displacement
              let transformStyle = '';
              if (!reducedMotion && isHovered) {
                transformStyle = 'translateY(-6px) scale(1.08) rotate(-2deg)';
              } else if (!reducedMotion && isNeighbor) {
                transformStyle = 'translateY(-2px) scale(1.03) rotate(1deg)';
              }

              return (
                <span
                  key={charIdx}
                  onMouseEnter={() => setHoveredIndex(currentGlobalIndex)}
                  onMouseLeave={() => setHoveredIndex(null)}
                  className={`inline-block transition-transform duration-200 ease-out select-none cursor-default ${
                    isHighlight
                      ? 'bg-gradient-to-r from-niyam-primary via-niyam-focus to-[#7C3AED] bg-clip-text text-transparent drop-shadow-xs font-black'
                      : 'text-niyam-text hover:text-niyam-primary'
                  }`}
                  style={{
                    transform: transformStyle,
                    willChange: 'transform',
                  }}
                  aria-hidden="true"
                >
                  {char}
                </span>
              );
            })}
          </span>
        );
      })}
    </h1>
  );
};
