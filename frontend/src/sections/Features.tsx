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

interface FeatureCardProps {
  key?: number;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  points: string[];
  delay: number;
}

function FeatureCard({ icon: Icon, title, points, delay }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.7, delay }}
      whileHover={{ y: -6, scale: 1.02 }}
      className="relative p-8 rounded-2xl border border-[#5FE8FF]/10 bg-[#08111F]/20 backdrop-blur-xl flex flex-col items-start gap-4 transition-all duration-300 group hover:border-[#5FE8FF]/30 hover:shadow-[0_15px_40px_rgba(95,232,255,0.08)] overflow-hidden"
    >
      
      {/* Background Soft Hover Glow */}
      <div className="absolute -top-16 -right-16 w-32 h-32 bg-gradient-to-tr from-[#5FE8FF]/10 to-[#8B5CF6]/5 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-500 pointer-events-none" />

      {/* Glowing Floating Icon */}
      <div className="w-12 h-12 flex items-center justify-center bg-[#5FE8FF]/5 rounded-xl border border-[#5FE8FF]/10 text-[#5FE8FF] group-hover:text-[#F5F7FA] group-hover:bg-[#5FE8FF]/20 group-hover:border-[#5FE8FF]/30 transition-all duration-300 shadow-[0_0_15px_rgba(95,232,255,0.05)] group-hover:shadow-[0_0_20px_rgba(95,232,255,0.2)]">
        <Icon className="w-6 h-6 animate-pulse" />
      </div>

      {/* Card Content */}
      <h3 className="font-['Space_Grotesk'] text-xl font-bold text-[#F5F7FA] tracking-wide mt-2">
        {title}
      </h3>

      <ul className="flex flex-col gap-2">
        {points.map((point, index) => (
          <li key={index} className="flex items-center gap-2 text-sm text-[#F5F7FA]/50 font-light leading-relaxed">
            <span className="w-1 h-1 bg-[#5FE8FF] rounded-full" />
            <span>{point}</span>
          </li>
        ))}
      </ul>

      {/* Light bottom bar indicators */}
      <div className="absolute bottom-0 left-0 h-[2px] w-0 bg-gradient-to-r from-[#5FE8FF] to-[#8B5CF6] transition-all duration-500 group-hover:w-full" />

    </motion.div>
  );
}

export default function Features() {
  const featureList = [
    {
      icon: MessageSquare,
      title: "AI Chat",
      points: ["Intelligent conversations", "Real-time answers"],
      delay: 0.1
    },
    {
      icon: Code2,
      title: "Code Assistant",
      points: ["Generate clean code", "Debug applications"],
      delay: 0.2
    },
    {
      icon: Sparkles,
      title: "Creative Studio",
      points: ["Write professional copies", "Design & create content"],
      delay: 0.3
    },
    {
      icon: Search,
      title: "Smart Search",
      points: ["Find precise information", "Understand context"],
      delay: 0.4
    },
    {
      icon: Cpu,
      title: "Automation",
      points: ["Automate repetitive workflows", "Custom agent scripting"],
      delay: 0.5
    },
    {
      icon: GraduationCap,
      title: "Learning AI",
      points: ["Learn faster & comprehend", "Explain complex topics"],
      delay: 0.6
    }
  ];

  return (
    <section id="features" className="relative py-24 px-6 md:px-12 bg-[#05070D] z-10">
      
      {/* Background Soft Glow blobs */}
      <div className="absolute top-1/3 right-10 w-[350px] h-[350px] bg-[#8B5CF6]/3 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-[300px] h-[300px] bg-[#5FE8FF]/3 blur-[100px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto flex flex-col gap-16 relative z-10">
        
        {/* Section Heading */}
        <div className="flex flex-col items-center text-center gap-4 max-w-xl mx-auto">
          <span className="text-xs font-mono tracking-[0.25em] text-[#8B5CF6] uppercase">
            Capabilities
          </span>
          <h2 className="font-['Space_Grotesk'] text-3xl sm:text-4xl md:text-5xl font-extrabold text-[#F5F7FA] tracking-tight">
            What <span className="text-[#5FE8FF] filter drop-shadow-[0_0_10px_rgba(95,232,255,0.2)]">AIDA</span> Can Do
          </h2>
          <p className="text-sm sm:text-base text-[#F5F7FA]/40 font-light leading-relaxed">
            Equipped with state-of-the-art neural architectures to handle conversation, coding, analysis, and custom automated scripting seamlessly.
          </p>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {featureList.map((feat, idx) => (
            <FeatureCard 
              key={idx}
              icon={feat.icon}
              title={feat.title}
              points={feat.points}
              delay={feat.delay}
            />
          ))}
        </div>

      </div>

    </section>
  );
}
