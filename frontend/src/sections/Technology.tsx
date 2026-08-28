import React from 'react';
import { motion } from 'motion/react';
import NeuralNetwork from '../components/ai/NeuralNetwork';

interface MetricBarProps {
  key?: number;
  label: string;
  value: number;
  color: string;
  delay: number;
}

function MetricBar({ label, value, color, delay }: MetricBarProps) {
  return (
    <div className="flex flex-col gap-2 w-full">
      <div className="flex justify-between text-xs font-mono tracking-widest uppercase">
        <span className="text-[#9CA9BC]/70">{label}</span>
        <span style={{ color }}>{value}%</span>
      </div>
      
      {/* Outer progress frame */}
      <div className="h-2.5 w-full bg-[#03050A] border border-white/8 rounded-full overflow-hidden relative p-[1px]">
        {/* Glowing Progress bar fill */}
        <motion.div
          initial={{ width: 0 }}
          whileInView={{ width: `${value}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1.2, delay, ease: "easeOut" }}
          style={{ 
            background: `linear-gradient(90deg, ${color}, #4C7DFF)`,
            boxShadow: `0 0 10px ${color}40`
          }}
          className="h-full rounded-full"
        />
      </div>
    </div>
  );
}

export default function Technology() {
  const metrics = [
    { label: "Intelligence", value: 94, color: "#5DE8FF", delay: 0.1 },
    { label: "Reasoning", value: 89, color: "#7C5CFF", delay: 0.25 },
    { label: "Creative", value: 92, color: "#D56BFF", delay: 0.4 },
    { label: "Context", value: 97, color: "#4C7DFF", delay: 0.55 }
  ];

  const techList = [
    { name: "Neural Networks", desc: "Multi-layered architectures for deep contextual mapping." },
    { name: "Natural Language", desc: "Parsing, sentiment alignment, and multi-dialect synthesis." },
    { name: "Automation Pipelines", desc: "Autonomously schedules workflows and acts on server metrics." }
  ];

  return (
    <section id="technology" className="relative py-24 px-6 md:px-12 bg-[#07101A] z-10 overflow-hidden">
      
      {/* Background plexus dynamic connections */}
      <div className="absolute inset-0 opacity-15 pointer-events-none">
        <NeuralNetwork mode="ambient" />
      </div>

      {/* Background Soft Glow blobs */}
      <div className="absolute bottom-1/4 left-10 w-[400px] h-[400px] bg-[#7C5CFF]/3 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute top-1/4 right-10 w-[350px] h-[350px] bg-[#D56BFF]/3 blur-[100px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-16 relative z-10 items-center">
        
        {/* Left Column: Tech Stack & Metric visualization */}
        <div className="lg:col-span-6 flex flex-col gap-8 text-left">
          <div className="flex flex-col gap-4">
            <span className="text-xs font-mono tracking-[0.25em] text-[#5DE8FF] uppercase">
              Operational Statistics
            </span>
            <h2 className="font-['Space_Grotesk'] text-3xl sm:text-4xl font-extrabold text-[#F5F7FF] tracking-tight">
              Built for the Future
            </h2>
            <p className="text-sm text-[#9CA9BC] font-light leading-relaxed">
              Equipped with deep learning and reinforcement compilers to ensure accurate reasoning and contextual understanding.
            </p>
          </div>

          {/* Interactive Metric progress bars */}
          <div className="flex flex-col gap-6 w-full max-w-md bg-white/[0.03] border border-white/8 p-6 rounded-2xl backdrop-blur-xl">
            {metrics.map((m, idx) => (
              <MetricBar 
                key={idx}
                label={m.label}
                value={m.value}
                color={m.color}
                delay={m.delay}
              />
            ))}
          </div>
        </div>

        {/* Right Column: Cards Grid layout */}
        <div className="lg:col-span-6 flex flex-col gap-6">
          {techList.map((tech, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.7, delay: idx * 0.15 }}
              whileHover={{ x: 6 }}
              className="relative p-6 rounded-2xl border border-white/8 bg-white/[0.03] backdrop-blur-md flex flex-col gap-2 transition-all duration-300 group hover:border-[#5DE8FF]/30 shadow-[0_8px_30px_rgba(0,0,0,0.3)] overflow-hidden"
            >
              <div className="absolute top-4 left-4 w-2 h-2 rounded-full bg-[#5DE8FF]/40 group-hover:bg-[#5DE8FF] transition-colors duration-300 animate-pulse" />
              <h3 className="font-['Space_Grotesk'] text-lg font-bold text-[#F5F7FF] tracking-wide ml-4">
                {tech.name}
              </h3>
              <p className="text-xs sm:text-sm text-[#9CA9BC] font-light leading-relaxed ml-4">
                {tech.desc}
              </p>
            </motion.div>
          ))}
        </div>

      </div>

    </section>
  );
}
