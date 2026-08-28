import React from 'react';
import { motion } from 'motion/react';
import { 
  MessageSquare, 
  Code2, 
  Sparkles, 
  Search, 
  Cpu, 
  GraduationCap 
} from 'lucide-react';
import Card from '../components/ui/Card';

export default function Capabilities() {
  const capabilitiesList = [
    {
      icon: MessageSquare,
      title: "AI Chat",
      desc: "Engage in intelligent, contextual conversations with real-time semantic analysis.",
      delay: 0.1,
      accent: "cyan" as const,
      color: "#5DE8FF"
    },
    {
      icon: Code2,
      title: "Code Assistant",
      desc: "Autonomously compile, write, refactor, and debug high-performance applications.",
      delay: 0.2,
      accent: "electric-blue" as const,
      color: "#4C7DFF"
    },
    {
      icon: Sparkles,
      title: "Creative Studio",
      desc: "Synthesize marketing copy, visual frameworks, and content outlines instantly.",
      delay: 0.3,
      accent: "violet" as const,
      color: "#7C5CFF"
    },
    {
      icon: Search,
      title: "Smart Search",
      desc: "Crawl documentation and directories to gather contextual answers instantly.",
      delay: 0.4,
      accent: "purple" as const,
      color: "#A78BFA"
    },
    {
      icon: Cpu,
      title: "Automation",
      desc: "Deploy agents, automate repetitive cron tasks, and control server operations.",
      delay: 0.5,
      accent: "magenta" as const,
      color: "#D56BFF"
    },
    {
      icon: GraduationCap,
      title: "Learning AI",
      desc: "Deconstruct complex topics, outline concepts, and train in specific domains.",
      delay: 0.6,
      accent: "blue" as const,
      color: "#4C7DFF"
    }
  ];

  return (
    <section id="capabilities" className="relative py-24 px-6 md:px-12 bg-[#07101A] z-10">
      
      {/* Background Soft Glow blobs */}
      <div className="absolute top-1/4 left-10 w-[350px] h-[350px] bg-[#7C5CFF]/3 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-1/4 right-10 w-[350px] h-[350px] bg-[#4C7DFF]/3 blur-[120px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto flex flex-col gap-16 relative z-10">
        
        {/* Section Heading */}
        <div className="flex flex-col items-center text-center gap-4 max-w-xl mx-auto">
          <span className="text-xs font-mono tracking-[0.25em] text-[#7C5CFF] uppercase">
            Platform Capabilities
          </span>
          <h2 className="font-['Space_Grotesk'] text-3xl sm:text-4xl md:text-5xl font-extrabold text-[#F5F7FF] tracking-tight leading-tight">
            What <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#5DE8FF] via-[#4C7DFF] to-[#7C5CFF] filter drop-shadow-[0_0_10px_rgba(93,232,255,0.2)]">AIDA</span> Can Do
          </h2>
          <p className="text-sm sm:text-base text-[#9CA9BC] font-light leading-relaxed">
            Equipped with modular engines designed to compute, write, research, and execute tasks autonomously.
          </p>
        </div>

        {/* Capabilities Card Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {capabilitiesList.map((item, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 25 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.7, delay: item.delay }}
            >
              <Card className="group h-full flex flex-col gap-4" accentColor={item.accent}>
                {/* Floating Glowing Icon */}
                <div 
                  style={{ 
                    color: item.color,
                    borderColor: `${item.color}25`,
                    backgroundColor: `${item.color}05` 
                  }}
                  className="w-12 h-12 flex items-center justify-center rounded-xl border transition-all duration-300 group-hover:bg-opacity-20 group-hover:border-opacity-40 shadow-[0_0_10px_rgba(255,255,255,0.01)]"
                >
                  <item.icon className="w-5.5 h-5.5 transition-transform duration-300 group-hover:scale-110" />
                </div>
                
                {/* Title */}
                <h3 className="font-['Space_Grotesk'] text-lg font-bold text-[#F5F7FF] tracking-wide mt-2">
                  {item.title}
                </h3>
                
                {/* Description */}
                <p className="text-sm text-[#9CA9BC] font-light leading-relaxed">
                  {item.desc}
                </p>

                {/* Bottom line indicator */}
                <div 
                  style={{ backgroundColor: item.color }}
                  className="absolute bottom-0 left-0 h-[2.5px] w-0 transition-all duration-500 group-hover:w-full" 
                />
              </Card>
            </motion.div>
          ))}
        </div>

      </div>

    </section>
  );
}
