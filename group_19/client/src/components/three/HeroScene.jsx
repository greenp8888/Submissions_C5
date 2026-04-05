import { useEffect, useRef } from "react";

export default function HeroScene() {
  const canvasRef = useRef(null);
  const animRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let W, H;
    const particles = [];
    const PARTICLE_COUNT = 90;
    let t = 0;

    function resize() {
      W = canvas.width = canvas.offsetWidth;
      H = canvas.height = canvas.offsetHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    // Init particles
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * W,
        y: Math.random() * H,
        r: Math.random() * 1.5 + 0.3,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        alpha: Math.random() * 0.5 + 0.1,
        hue: Math.floor(Math.random() * 60) + 240, // purple-blue range
      });
    }

    // 3D wireframe icosahedron vertices projected to 2D
    const PHI = (1 + Math.sqrt(5)) / 2;
    const icoVerts = [
      [-1, PHI, 0], [1, PHI, 0], [-1, -PHI, 0], [1, -PHI, 0],
      [0, -1, PHI], [0, 1, PHI], [0, -1, -PHI], [0, 1, -PHI],
      [PHI, 0, -1], [PHI, 0, 1], [-PHI, 0, -1], [-PHI, 0, 1],
    ].map(([x, y, z]) => {
      const len = Math.sqrt(x*x+y*y+z*z);
      return [x/len, y/len, z/len];
    });
    const icoEdges = [
      [0,1],[0,5],[0,7],[0,10],[0,11],
      [1,5],[1,7],[1,8],[1,9],
      [2,3],[2,4],[2,6],[2,10],[2,11],
      [3,4],[3,6],[3,8],[3,9],
      [4,5],[4,9],[4,11],
      [5,9],[5,11],
      [6,7],[6,8],[6,10],
      [7,8],[7,10],
      [8,9],[10,11],
    ];

    function rotateY(v, a) {
      const c = Math.cos(a), s = Math.sin(a);
      return [c*v[0]+s*v[2], v[1], -s*v[0]+c*v[2]];
    }
    function rotateX(v, a) {
      const c = Math.cos(a), s = Math.sin(a);
      return [v[0], c*v[1]-s*v[2], s*v[1]+c*v[2]];
    }
    function project(v, cx, cy, scale, fov=3) {
      const z = v[2] + fov;
      const px = (v[0] / z) * scale + cx;
      const py = (v[1] / z) * scale + cy;
      return [px, py, v[2]];
    }

    function draw() {
      ctx.clearRect(0, 0, W, H);
      t += 0.004;

      // ── Particles ───────────────────────────────────────────────────────
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = W;
        if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H;
        if (p.y > H) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${p.hue},80%,70%,${p.alpha})`;
        ctx.fill();
      });

      // ── Connect nearby particles ────────────────────────────────────────
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx*dx + dy*dy);
          if (dist < 100) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(139,92,246,${0.15 * (1 - dist/100)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }

      // ── Icosahedron ──────────────────────────────────────────────────────
      const cx = W * 0.75, cy = H * 0.4;
      const scale = Math.min(W, H) * 0.18;
      const rotated = icoVerts.map((v) => rotateX(rotateY(v, t), t * 0.6));
      const proj = rotated.map((v) => project(v, cx, cy, scale));

      icoEdges.forEach(([a, b]) => {
        const [x1, y1, z1] = proj[a];
        const [x2, y2, z2] = proj[b];
        const depth = (z1 + z2) / 2;
        const alpha = 0.1 + (depth + 1) * 0.2;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.strokeStyle = `rgba(139,92,246,${clamp(alpha, 0.05, 0.6)})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      });

      // Vertex dots
      proj.forEach(([x, y, z]) => {
        const alpha = 0.3 + (z + 1) * 0.2;
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(139,92,246,${clamp(alpha, 0.1, 0.9)})`;
        ctx.fill();
      });

      // ── Second smaller icosahedron ────────────────────────────────────────
      const cx2 = W * 0.15, cy2 = H * 0.65;
      const scale2 = Math.min(W, H) * 0.08;
      const rot2 = icoVerts.map((v) => rotateX(rotateY(v, -t * 1.3), t * 0.8));
      const proj2 = rot2.map((v) => project(v, cx2, cy2, scale2));
      icoEdges.forEach(([a, b]) => {
        const [x1, y1] = proj2[a];
        const [x2, y2] = proj2[b];
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.strokeStyle = "rgba(6,182,212,0.25)";
        ctx.lineWidth = 0.6;
        ctx.stroke();
      });

      animRef.current = requestAnimationFrame(draw);
    }

    draw();
    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
      }}
    />
  );
}

function clamp(v, min, max) {
  return Math.min(Math.max(v, min), max);
}
