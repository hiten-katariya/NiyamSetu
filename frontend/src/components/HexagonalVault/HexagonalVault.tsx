import React, { useEffect, useRef, CSSProperties, ReactNode } from 'react';
import './HexagonalVault.css';

export interface HexagonalVaultProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
  hexRadius?: number; // Size of each hexagon in px (default: 32)
  lightRadius?: number; // Radius of illumination in px (default: 180)
  lightColor?: string; // Color of the soft light (default: '#0284c7')
  baseBorderColor?: string; // Idle border color (default: '#e2e8f0')
  glowBorderColor?: string; // Lit border color (default: '#38bdf8')
  ambientGlow?: boolean; // Soft background ambient glow
  clickPulse?: boolean; // Ripple shockwave on click
  className?: string;
  style?: CSSProperties;
}

export const HexagonalVault: React.FC<HexagonalVaultProps> = ({
  children,
  hexRadius = 32,
  lightRadius = 180,
  lightColor = '#0284c7',
  baseBorderColor = 'rgba(226, 232, 240, 0.7)',
  glowBorderColor = 'rgba(56, 189, 248, 0.9)',
  ambientGlow = true,
  clickPulse = true,
  className = '',
  style,
  ...rest
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef<{ x: number; y: number; active: boolean }>({ x: -1000, y: -1000, active: false });
  const ripplesRef = useRef<Array<{ x: number; y: number; radius: number; maxRadius: number; alpha: number }>>([]);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId = 0;
    const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

    const resize = () => {
      const rect = container.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.round(rect.width * dpr));
      canvas.height = Math.max(1, Math.round(rect.height * dpr));
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(container);

    // Flat-topped hexagon drawing helper
    const drawHexagon = (cx: number, cy: number, r: number) => {
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const angle = (Math.PI / 3) * i;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
    };

    const horizDistance = hexRadius * 1.5;
    const vertDistance = hexRadius * Math.sqrt(3);

    const render = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const width = canvas.width;
      const height = canvas.height;
      const cssWidth = width / dpr;
      const cssHeight = height / dpr;

      ctx.clearRect(0, 0, width, height);
      ctx.save();
      ctx.scale(dpr, dpr);

      const mx = mouseRef.current.active ? mouseRef.current.x : cssWidth * 0.5;
      const my = mouseRef.current.active ? mouseRef.current.y : cssHeight * 0.5;

      // Soft ambient radial spotlight following cursor
      if (ambientGlow) {
        const ambientGrad = ctx.createRadialGradient(mx, my, 0, mx, my, lightRadius * 1.3);
        ambientGrad.addColorStop(0, lightColor.replace(')', ', 0.12)').replace('rgb', 'rgba'));
        ambientGrad.addColorStop(0.5, lightColor.replace(')', ', 0.04)').replace('rgb', 'rgba'));
        ambientGrad.addColorStop(1, 'transparent');
        ctx.fillStyle = ambientGrad;
        ctx.fillRect(0, 0, cssWidth, cssHeight);
      }

      // Calculate hex grid bounds
      const cols = Math.ceil(cssWidth / horizDistance) + 2;
      const rows = Math.ceil(cssHeight / vertDistance) + 2;

      for (let col = -1; col < cols; col++) {
        for (let row = -1; row < rows; row++) {
          const cx = col * horizDistance;
          const cy = row * vertDistance + (col % 2 === 0 ? 0 : vertDistance * 0.5);

          const distToMouse = Math.hypot(cx - mx, cy - my);
          const intensity = Math.max(0, 1 - distToMouse / lightRadius);

          // Check ripple impact
          let rippleBoost = 0;
          for (let rIdx = 0; rIdx < ripplesRef.current.length; rIdx++) {
            const rip = ripplesRef.current[rIdx];
            const distToRip = Math.hypot(cx - rip.x, cy - rip.y);
            const delta = Math.abs(distToRip - rip.radius);
            if (delta < 40) {
              rippleBoost += (1 - delta / 40) * rip.alpha;
            }
          }

          const combinedGlow = Math.min(1, intensity * intensity + rippleBoost);

          // Draw hexagon tile
          drawHexagon(cx, cy, hexRadius - 2);

          if (combinedGlow > 0.01) {
            // Lit cell fill
            ctx.fillStyle = lightColor.replace(')', `, ${(combinedGlow * 0.16).toFixed(3)})`).replace('rgb', 'rgba');
            ctx.fill();

            // Lit border
            ctx.strokeStyle = glowBorderColor.replace(')', `, ${(0.2 + combinedGlow * 0.8).toFixed(3)})`).replace('rgb', 'rgba');
            ctx.lineWidth = 1 + combinedGlow * 1.5;
            ctx.stroke();

            // Specular center node
            if (combinedGlow > 0.4) {
              ctx.beginPath();
              ctx.arc(cx, cy, combinedGlow * 2.2, 0, Math.PI * 2);
              ctx.fillStyle = '#ffffff';
              ctx.fill();
            }
          } else {
            // Idle background cell
            ctx.strokeStyle = baseBorderColor;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }

      // Update active ripples
      if (!reduceMotion && ripplesRef.current.length > 0) {
        for (let i = ripplesRef.current.length - 1; i >= 0; i--) {
          const rip = ripplesRef.current[i];
          rip.radius += 5;
          rip.alpha *= 0.94;
          if (rip.alpha < 0.02 || rip.radius > rip.maxRadius) {
            ripplesRef.current.splice(i, 1);
          }
        }
      }

      ctx.restore();
      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
      ro.disconnect();
    };
  }, [hexRadius, lightRadius, lightColor, baseBorderColor, glowBorderColor, ambientGlow]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    mouseRef.current = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      active: true,
    };
  };

  const handleMouseLeave = () => {
    mouseRef.current.active = false;
  };

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!clickPulse || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    ripplesRef.current.push({
      x,
      y,
      radius: 10,
      maxRadius: Math.max(rect.width, rect.height) * 0.8,
      alpha: 1.0,
    });
  };

  return (
    <div
      ref={containerRef}
      className={`hex-vault-container ${className}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={handleClick}
      style={style}
      {...rest}
    >
      <canvas ref={canvasRef} className="hex-vault-canvas" aria-hidden="true" />
      {children && <div className="hex-vault-content">{children}</div>}
    </div>
  );
};

export default HexagonalVault;
