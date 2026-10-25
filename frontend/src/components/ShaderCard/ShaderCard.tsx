import React, { useEffect, useRef, useState, CSSProperties, ReactNode } from 'react';
import './ShaderCard.css';

export type FlamePalette = 'amber' | 'blue' | 'cyan' | 'purple' | 'emerald';

export interface ShaderCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
  palette?: FlamePalette;
  intensity?: number; // 0.2 to 2.0
  flameSpeed?: number; // 0.5 to 3.0
  tilt?: boolean;
  className?: string;
  innerClassName?: string;
  style?: CSSProperties;
}

const PALETTES: Record<FlamePalette, { core: string; mid: string; edge: string; glow: string }> = {
  amber: {
    core: '#fffbeb',
    mid: '#f59e0b',
    edge: '#b45309',
    glow: 'rgba(245, 158, 11, 0.45)',
  },
  blue: {
    core: '#f0f9ff',
    mid: '#0284c7',
    edge: '#1e40af',
    glow: 'rgba(2, 132, 199, 0.45)',
  },
  cyan: {
    core: '#ecfeff',
    mid: '#06b6d4',
    edge: '#0f766e',
    glow: 'rgba(6, 182, 212, 0.45)',
  },
  purple: {
    core: '#faf5ff',
    mid: '#9333ea',
    edge: '#6b21a8',
    glow: 'rgba(147, 51, 234, 0.45)',
  },
  emerald: {
    core: '#f0fdf4',
    mid: '#10b981',
    edge: '#047857',
    glow: 'rgba(16, 185, 129, 0.45)',
  },
};

export const ShaderCard: React.FC<ShaderCardProps> = ({
  children,
  palette = 'amber',
  intensity = 1.0,
  flameSpeed = 1.0,
  tilt = true,
  className = '',
  innerClassName = '',
  style,
  ...rest
}) => {
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [tiltStyle, setTiltStyle] = useState<CSSProperties>({});
  const mousePos = useRef({ x: 0.5, y: 0.5, isHovered: false });

  // Flame simulation via Canvas 2D procedural heat convection & noise
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId = 0;
    let time = 0;
    const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

    // Sizing
    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.max(1, Math.round(rect.width * dpr));
      canvas.height = Math.max(1, Math.round(rect.height * dpr));
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    // Particle flame plume definition
    const PARTICLE_COUNT = 65;
    interface FlameParticle {
      x: number;
      y: number;
      vx: number;
      vy: number;
      size: number;
      life: number;
      maxLife: number;
      baseX: number;
      offset: number;
    }

    const particles: FlameParticle[] = [];
    const colors = PALETTES[palette] || PALETTES.amber;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random(),
        y: 0.8 + Math.random() * 0.25,
        vx: (Math.random() - 0.5) * 0.003,
        vy: -(0.005 + Math.random() * 0.009),
        size: 18 + Math.random() * 26,
        life: Math.random() * 80,
        maxLife: 60 + Math.random() * 40,
        baseX: 0.15 + Math.random() * 0.7,
        offset: Math.random() * Math.PI * 2,
      });
    }

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      if (reduceMotion) {
        // Static ambient luminous glow
        const grad = ctx.createRadialGradient(
          width * 0.5,
          height * 0.4,
          10,
          width * 0.5,
          height * 0.4,
          width * 0.5
        );
        grad.addColorStop(0, colors.core);
        grad.addColorStop(0.35, colors.mid);
        grad.addColorStop(0.8, colors.edge);
        grad.addColorStop(1, 'transparent');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, width, height);
        return;
      }

      time += 0.025 * flameSpeed;

      // Base rising fire glow at the bottom
      const baseGrad = ctx.createRadialGradient(
        width * (0.3 + 0.4 * mousePos.current.x),
        height * 0.85,
        20,
        width * 0.5,
        height * 0.5,
        width * 0.65
      );
      baseGrad.addColorStop(0, colors.glow);
      baseGrad.addColorStop(0.5, colors.edge);
      baseGrad.addColorStop(1, 'transparent');
      ctx.globalCompositeOperation = 'screen';
      ctx.fillStyle = baseGrad;
      ctx.fillRect(0, 0, width, height);

      // Render interactive flame plumes
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const p = particles[i];
        p.life += 1;
        if (p.life > p.maxLife) {
          p.life = 0;
          p.x = p.baseX + (Math.random() - 0.5) * 0.2;
          p.y = 0.88 + Math.random() * 0.15;
          p.vy = -(0.006 + Math.random() * 0.012) * intensity;
        }

        // Rising swirl physics with cursor pull
        const progress = p.life / p.maxLife;
        const wave = Math.sin(time * 3 + p.offset + progress * 5) * 0.008;
        const attraction = mousePos.current.isHovered ? (mousePos.current.x - p.x) * 0.003 : 0;
        p.x += p.vx + wave + attraction;
        p.y += p.vy;

        // Size expansion and dissipation
        const currentSize = p.size * (1 + progress * 1.5) * (width / 380);
        const alpha = Math.sin(progress * Math.PI) * 0.45 * intensity;

        const px = p.x * width;
        const py = p.y * height;

        const pGrad = ctx.createRadialGradient(px, py, 0, px, py, currentSize);
        if (progress < 0.25) {
          pGrad.addColorStop(0, colors.core);
          pGrad.addColorStop(0.6, colors.mid);
        } else if (progress < 0.65) {
          pGrad.addColorStop(0, colors.mid);
          pGrad.addColorStop(0.8, colors.edge);
        } else {
          pGrad.addColorStop(0, colors.edge);
          pGrad.addColorStop(1, 'transparent');
        }
        pGrad.addColorStop(1, 'transparent');

        ctx.globalAlpha = alpha;
        ctx.fillStyle = pGrad;
        ctx.beginPath();
        ctx.arc(px, py, currentSize, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.globalAlpha = 1.0;
      ctx.globalCompositeOperation = 'source-over';
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      ro.disconnect();
    };
  }, [palette, intensity, flameSpeed]);

  // Mouse tilt tracking
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!wrapperRef.current) return;
    const rect = wrapperRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    mousePos.current = { x, y, isHovered: true };

    if (tilt) {
      const tiltX = (y - 0.5) * -12;
      const tiltY = (x - 0.5) * 14;
      setTiltStyle({
        transform: `rotateX(${tiltX.toFixed(2)}deg) rotateY(${tiltY.toFixed(2)}deg) scale3d(1.02, 1.02, 1.02)`,
      });
    }
  };

  const handleMouseLeave = () => {
    mousePos.current.isHovered = false;
    if (tilt) {
      setTiltStyle({
        transform: 'rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)',
      });
    }
  };

  return (
    <div
      ref={wrapperRef}
      className={`shader-card-wrapper ${className}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={style}
      {...rest}
    >
      {/* Background Luminous Rising Flame Canvas */}
      <canvas ref={canvasRef} className="shader-card-flame-canvas" aria-hidden="true" />

      {/* Foreground Content Card */}
      <div className={`shader-card-inner ${innerClassName}`} style={tiltStyle}>
        {children}
      </div>
    </div>
  );
};

export default ShaderCard;
