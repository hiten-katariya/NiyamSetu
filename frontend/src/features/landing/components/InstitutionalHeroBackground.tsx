import React, { useEffect, useRef } from 'react';
import AeroShards from '../../../components/AeroShards';

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  label?: string;
  color: string;
  pulsePhase: number;
}

interface Pulse {
  fromNode: number;
  toNode: number;
  progress: number;
  speed: number;
}

const INSTITUTION_TAGS = [
  'Univ Portal',
  'Scrutiny Desk',
  'Regional RO',
  'EVC Visit',
  'Council Board',
  'Audit Ledger',
  'SLA Clock',
  'Doc Vault',
];

export const InstitutionalHeroBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = 0;
    let height = 0;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const mouse = {
      x: -1000,
      y: -1000,
      radius: 160,
    };

    const handleResize = () => {
      if (!canvas || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    handleResize();
    const ro = new ResizeObserver(handleResize);
    if (containerRef.current) ro.observe(containerRef.current);

    // Initialize network nodes
    const nodeCount = Math.max(16, Math.min(32, Math.floor(window.innerWidth / 55)));
    const nodes: Node[] = [];

    const palette = [
      'rgba(2, 132, 199, 0.75)',   // Niyam primary cyan/blue
      'rgba(99, 102, 241, 0.7)',   // Indigo scrutiny
      'rgba(14, 165, 233, 0.65)',  // Sky blue
      'rgba(16, 185, 129, 0.7)',   // Emerald verification
    ];

    for (let i = 0; i < nodeCount; i++) {
      nodes.push({
        x: Math.random() * (width || window.innerWidth),
        y: Math.random() * (height || 700),
        vx: (Math.random() - 0.5) * 0.45,
        vy: (Math.random() - 0.5) * 0.45,
        radius: 2 + Math.random() * 2.2,
        label: i < INSTITUTION_TAGS.length ? INSTITUTION_TAGS[i] : undefined,
        color: palette[i % palette.length],
        pulsePhase: Math.random() * Math.PI * 2,
      });
    }

    const pulses: Pulse[] = [];
    let lastPulseTime = 0;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };

    const handleMouseLeave = () => {
      mouse.x = -1000;
      mouse.y = -1000;
    };

    window.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);

    const maxDistance = 140;

    const render = (time: number) => {
      if (!ctx || width === 0 || height === 0) {
        animationFrameId = requestAnimationFrame(render);
        return;
      }

      ctx.clearRect(0, 0, width, height);

      // Periodically trigger a data packet pulse across connected nodes
      if (time - lastPulseTime > 1200 && pulses.length < 8) {
        const fromIdx = Math.floor(Math.random() * nodes.length);
        // Find a nearby node
        let closestIdx = -1;
        let minD = maxDistance;
        for (let j = 0; j < nodes.length; j++) {
          if (j === fromIdx) continue;
          const dx = nodes[fromIdx].x - nodes[j].x;
          const dy = nodes[fromIdx].y - nodes[j].y;
          const d = Math.hypot(dx, dy);
          if (d < minD) {
            minD = d;
            closestIdx = j;
          }
        }
        if (closestIdx !== -1) {
          pulses.push({
            fromNode: fromIdx,
            toNode: closestIdx,
            progress: 0,
            speed: 0.015 + Math.random() * 0.015,
          });
          lastPulseTime = time;
        }
      }

      // 1. Draw connections
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.hypot(dx, dy);

          if (dist < maxDistance) {
            const alpha = (1 - dist / maxDistance) * 0.28;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = `rgba(14, 165, 233, ${alpha})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }

      // 2. Draw traveling pulses (data packets)
      for (let p = pulses.length - 1; p >= 0; p--) {
        const pulse = pulses[p];
        pulse.progress += pulse.speed;
        if (pulse.progress >= 1) {
          pulses.splice(p, 1);
          continue;
        }

        const n1 = nodes[pulse.fromNode];
        const n2 = nodes[pulse.toNode];
        if (!n1 || !n2) continue;

        const px = n1.x + (n2.x - n1.x) * pulse.progress;
        const py = n1.y + (n2.y - n1.y) * pulse.progress;

        ctx.beginPath();
        ctx.arc(px, py, 2.2, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(2, 132, 199, 0.85)';
        ctx.shadowColor = 'rgba(2, 132, 199, 0.6)';
        ctx.shadowBlur = 4;
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      // 3. Update & draw nodes
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];

        // Soft drift
        n.x += n.vx;
        n.y += n.vy;

        // Bounce within canvas boundaries with padding
        if (n.x < 15) {
          n.x = 15;
          n.vx *= -1;
        } else if (n.x > width - 15) {
          n.x = width - 15;
          n.vx *= -1;
        }
        if (n.y < 15) {
          n.y = 15;
          n.vy *= -1;
        } else if (n.y > height - 15) {
          n.y = height - 15;
          n.vy *= -1;
        }

        // Gentle interactive mouse repulsion/connection
        const mdx = n.x - mouse.x;
        const mdy = n.y - mouse.y;
        const mDist = Math.hypot(mdx, mdy);
        if (mDist < mouse.radius && mDist > 0) {
          const force = (1 - mDist / mouse.radius) * 1.5;
          n.x += (mdx / mDist) * force;
          n.y += (mdy / mDist) * force;

          // Draw faint interaction tether to mouse
          ctx.beginPath();
          ctx.moveTo(n.x, n.y);
          ctx.lineTo(mouse.x, mouse.y);
          ctx.strokeStyle = `rgba(2, 132, 199, ${(1 - mDist / mouse.radius) * 0.22})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }

        n.pulsePhase += 0.035;
        const currentR = n.radius + Math.sin(n.pulsePhase) * 0.4;

        // Outer glow circle
        ctx.beginPath();
        ctx.arc(n.x, n.y, currentR + 2, 0, Math.PI * 2);
        ctx.fillStyle = n.color.replace(/[\d.]+\)$/, '0.12)');
        ctx.fill();

        // Node center
        ctx.beginPath();
        ctx.arc(n.x, n.y, currentR, 0, Math.PI * 2);
        ctx.fillStyle = n.color;
        ctx.fill();

        // Node label (if statutory landmark node)
        if (n.label) {
          ctx.font = '500 10px system-ui, -apple-system, sans-serif';
          ctx.fillStyle = 'rgba(71, 85, 105, 0.7)';
          ctx.fillText(n.label, n.x + 7, n.y + 3);
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId);
      ro.disconnect();
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full overflow-hidden pointer-events-none select-none z-0"
      aria-hidden="true"
    >
      {/* LAYER 1: WebGPU AeroShards in Light Mode (Depth & Reflections) */}
      <div className="absolute inset-0 w-full h-full opacity-55 transition-opacity duration-700">
        <AeroShards
          shardColor="#0284c7"
          accentColor="#6366f1"
          backgroundColor="transparent"
          lightMode={true}
          placement="full"
          material="glass"
          markers="plus"
          count={850}
          depthOfField={0.7}
          vignette={0.15}
          mouseInteraction={true}
          pulseOnClick={true}
          holdToGather={true}
          className="w-full h-full"
        />
      </div>

      {/* LAYER 2: Connected Compliance & Workflow Network Canvas */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
      />

      {/* LAYER 3: Subtle bottom fade to seamlessly blend into next section */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#EEF2F7] to-transparent pointer-events-none" />
    </div>
  );
};
