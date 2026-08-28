import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';

export default function AnimatedHeaderCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);
    let target = { x: width / 2, y: height / 2 };
    let animateHeader = true;
    let points: any[] = [];
    let animationFrameId: number;

    const getDistance = (p1: { x: number; y: number }, p2: { x: number; y: number }) => {
      return Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2);
    };

    class Circle {
      pos: { x: number; y: number };
      radius: number;
      color: string;
      active: number = 0;

      constructor(pos: { x: number; y: number }, radius: number, color: string) {
        this.pos = pos;
        this.radius = radius;
        this.color = color;
      }

      draw() {
        if (!ctx) return;
        if (!this.active) return;
        ctx.beginPath();
        ctx.arc(this.pos.x, this.pos.y, this.radius, 0, 2 * Math.PI, false);
        ctx.fillStyle = `rgba(93, 232, 255, ${this.active})`;
        ctx.fill();
      }
    }

    const initHeader = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      target = { x: width / 2, y: height / 2 };

      points = [];
      const step = Math.max(width / 20, 60);
      for (let x = 0; x < width; x += step) {
        for (let y = 0; y < height; y += step) {
          const px = x + Math.random() * step;
          const py = y + Math.random() * step;
          const p = { x: px, originX: px, y: py, originY: py, closest: [] as any[], active: 0, circle: null as any };
          points.push(p);
        }
      }

      for (let i = 0; i < points.length; i++) {
        const closest: any[] = [];
        const p1 = points[i];
        for (let j = 0; j < points.length; j++) {
          const p2 = points[j];
          if (p1 !== p2) {
            let placed = false;
            for (let k = 0; k < 5; k++) {
              if (!placed && closest[k] === undefined) {
                closest[k] = p2;
                placed = true;
              }
            }
            for (let k = 0; k < 5; k++) {
              if (!placed && getDistance(p1, p2) < getDistance(p1, closest[k])) {
                closest[k] = p2;
                placed = true;
              }
            }
          }
        }
        p1.closest = closest;
      }

      for (let i = 0; i < points.length; i++) {
        const c = new Circle(points[i], 2 + Math.random() * 2.5, 'rgba(93,232,255,0.4)');
        points[i].circle = c;
      }
    };

    const mouseMove = (e: MouseEvent) => {
      target.x = e.clientX;
      target.y = e.clientY;
    };

    const resize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const shiftPoint = (p: any) => {
      gsap.to(p, {
        duration: 1 + Math.random(),
        x: p.originX - 50 + Math.random() * 100,
        y: p.originY - 50 + Math.random() * 100,
        ease: 'power1.inOut',
        onComplete: () => shiftPoint(p),
      });
    };

    const drawLines = (p: any) => {
      if (!p.active || !ctx) return;
      for (let i = 0; i < p.closest.length; i++) {
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.closest[i].x, p.closest[i].y);
        ctx.strokeStyle = `rgba(93, 232, 255, ${p.active})`;
        ctx.stroke();
      }
    };

    const animate = () => {
      if (animateHeader && ctx) {
        ctx.clearRect(0, 0, width, height);
        for (let i = 0; i < points.length; i++) {
          const dist = getDistance(target, points[i]);
          if (dist < 10000) {
            points[i].active = 0.5;
            points[i].circle.active = 0.8;
          } else if (dist < 40000) {
            points[i].active = 0.25;
            points[i].circle.active = 0.4;
          } else if (dist < 90000) {
            points[i].active = 0.08;
            points[i].circle.active = 0.15;
          } else {
            points[i].active = 0.02;
            points[i].circle.active = 0.05;
          }

          drawLines(points[i]);
          points[i].circle.draw();
        }
      }
      animationFrameId = requestAnimationFrame(animate);
    };

    initHeader();
    animate();
    for (let i = 0; i < points.length; i++) {
      shiftPoint(points[i]);
    }

    window.addEventListener('mousemove', mouseMove);
    window.addEventListener('resize', resize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', mouseMove);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none z-0"
    />
  );
}
