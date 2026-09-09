import { useRef, useEffect, useCallback, useState } from 'react';
import { useReducedMotion } from '../../hooks/useReducedMotion';

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  label: string;
  connections: number[];
}

const COLORS = ['#38bdf8', '#a855f7', '#6366f1', '#34d399', '#fbbf24'];

function createNodes(count: number, w: number, h: number): Node[] {
  const labels = ['Age', 'Income', 'Score', 'Class', 'Feature', 'Target', 'Model', 'Data', 'Metric', 'Value'];
  return Array.from({ length: count }, (_, i) => ({
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.3,
    vy: (Math.random() - 0.5) * 0.3,
    radius: 3 + Math.random() * 4,
    label: labels[i % labels.length],
    connections: [],
  }));
}

function generateConnections(nodes: Node[], maxDist: number) {
  nodes.forEach((a, i) => {
    a.connections = [];
    nodes.forEach((b, j) => {
      if (i >= j) return;
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      if (Math.sqrt(dx * dx + dy * dy) < maxDist) {
        a.connections.push(j);
      }
    });
  });
}

export default function DataIntelligenceVisual() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const mouseRef = useRef({ x: 0, y: 0 });
  const nodesRef = useRef<Node[]>([]);
  const [dimensions, setDimensions] = useState({ w: 600, h: 400 });
  const reducedMotion = useReducedMotion();

  const init = useCallback((w: number, h: number) => {
    nodesRef.current = createNodes(reducedMotion ? 12 : 24, w, h);
    generateConnections(nodesRef.current, reducedMotion ? 120 : 160);
    setDimensions({ w, h });
  }, [reducedMotion]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      const rect = canvas.parentElement?.getBoundingClientRect();
      if (!rect) return;
      const dpr = window.devicePixelRatio || 1;
      const w = rect.width;
      const h = rect.height;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      ctx.scale(dpr, dpr);
      init(w, h);
    };

    resize();
    window.addEventListener('resize', resize);

    const handleMouse = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };
    canvas.addEventListener('mousemove', handleMouse);

    let time = 0;
    const animate = () => {
      time += 1;
      const { w, h } = dimensions;
      ctx.clearRect(0, 0, w, h);

      const nodes = nodesRef.current;

      nodes.forEach((node) => {
        if (!reducedMotion) {
          node.x += node.vx;
          node.y += node.vy;

          const mx = mouseRef.current.x;
          const my = mouseRef.current.y;
          const dx = mx - node.x;
          const dy = my - node.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 200 && dist > 0) {
            node.vx += (dx / dist) * 0.02;
            node.vy += (dy / dist) * 0.02;
          }

          node.vx *= 0.99;
          node.vy *= 0.99;

          if (node.x < 0 || node.x > w) node.vx *= -1;
          if (node.y < 0 || node.y > h) node.vy *= -1;
          node.x = Math.max(0, Math.min(w, node.x));
          node.y = Math.max(0, Math.min(h, node.y));
        }
      });

      // Draw connections
      nodes.forEach((node) => {
        node.connections.forEach((j) => {
          const other = nodes[j];
          const dx = node.x - other.x;
          const dy = node.y - other.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const alpha = Math.max(0, 1 - dist / 200) * 0.3;
          ctx.beginPath();
          ctx.moveTo(node.x, node.y);
          ctx.lineTo(other.x, other.y);
          ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        });
      });

      // Draw nodes
      nodes.forEach((node, i) => {
        const color = COLORS[i % COLORS.length];
        const pulse = reducedMotion ? 0 : Math.sin(time * 0.02 + i) * 0.3;

        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + pulse, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 4 + pulse, 0, Math.PI * 2);
        ctx.fillStyle = color.replace(')', ', 0.1)').replace('rgb', 'rgba');
        ctx.fill();
      });

      animRef.current = requestAnimationFrame(animate);
    };

    animRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', resize);
      canvas.removeEventListener('mousemove', handleMouse);
    };
  }, [dimensions, init, reducedMotion]);

  return (
    <div className="relative w-full h-full min-h-[300px]">
      <canvas ref={canvasRef} className="w-full h-full" />
      <div className="absolute inset-0 bg-gradient-to-t from-bg-primary via-transparent to-transparent pointer-events-none" />
    </div>
  );
}
