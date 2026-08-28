import React from 'react';
import { motion } from 'motion/react';
import { 
  MessageSquare, 
  FolderGit2, 
  Layers, 
  Wrench, 
  History, 
  Settings, 
  Search, 
  User, 
  PenTool, 
  Code, 
  Compass, 
  BarChart4, 
  BookOpen, 
  Cpu 
} from 'lucide-react';
import Card from '../components/ui/Card';

export default function Dashboard() {
  const sidebarLinks = [
    { icon: MessageSquare, label: "Chat", active: true },
    { icon: FolderGit2, label: "Projects" },
    { icon: Layers, label: "Workspace" },
    { icon: Wrench, label: "AI Tools" },
    { icon: History, label: "History" },
    { icon: Settings, label: "Settings" }
  ];

  const quickActions = [
    { icon: PenTool, title: "Write", desc: "Draft documentation or content.", glow: "#5FE8FF" },
    { icon: Code, title: "Code", desc: "Refactor scripts or write modules.", glow: "#4D7CFF" },
    { icon: Cpu, title: "Research", desc: "Crawl web indices or parse logs.", glow: "#8B5CF6" },
    { icon: BarChart4, title: "Analyze", desc: "Graph metrics or extract patterns.", glow: "#5FE8FF" },
    { icon: Compass, title: "Create", desc: "Build workspace visual wireframes.", glow: "#4D7CFF" },
    { icon: BookOpen, title: "Learn", desc: "Explain algorithmic constraints.", glow: "#8B5CF6" }
  ];

  return (
    <section className="relative py-24 px-6 md:px-12 bg-[#05070D] z-10 overflow-hidden">
      
      {/* Background Soft Glow blobs */}
      <div className="absolute top-1/2 right-1/4 w-[400px] h-[400px] bg-[#4D7CFF]/3 blur-[140px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto flex flex-col gap-12 relative z-10">
        
        {/* Section Heading */}
        <div className="flex flex-col items-center text-center gap-4 max-w-xl mx-auto">
          <span className="text-xs font-mono tracking-[0.25em] text-[#8B5CF6] uppercase">
            Product Preview
          </span>
          <h2 className="font-['Space_Grotesk'] text-3xl sm:text-4xl font-extrabold text-[#F5F7FA] tracking-tight leading-tight">
            Intelligence Dashboard
          </h2>
          <p className="text-sm text-[#F5F7FA]/40 font-light leading-relaxed">
            A sneak peek into AIDA's workspace hub, designed to aggregate chats, key resources, and custom tools in one grid.
          </p>
        </div>

        {/* Desktop SaaS Application Preview Frame */}
        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.8 }}
          className="relative w-full min-h-[540px] rounded-3xl border border-[#F5F7FA]/5 bg-[#08111F]/15 backdrop-blur-xl shadow-[0_30px_70px_rgba(0,0,0,0.5)] grid grid-cols-1 md:grid-cols-12 overflow-hidden"
        >
          
          {/* 1. App Sidebar */}
          <div className="md:col-span-3 border-r border-[#F5F7FA]/5 bg-[#05070D]/40 p-6 flex flex-col justify-between">
            <div className="flex flex-col gap-8">
              {/* App Brand Title */}
              <div className="flex items-center gap-2 px-2">
                <svg viewBox="0 0 100 100" className="w-6 h-6 text-[#5FE8FF] filter drop-shadow-[0_0_5px_rgba(95,232,255,0.4)]">
                  <polygon points="50,15 85,35 85,75 50,95 15,75 15,35" fill="none" stroke="currentColor" strokeWidth="8" />
                  <circle cx="50" cy="50" r="14" fill="none" stroke="currentColor" strokeWidth="10" />
                </svg>
                <span className="font-['Space_Grotesk'] font-bold text-base text-[#F5F7FA] tracking-wider">AIDA</span>
              </div>

              {/* Navigation Stack */}
              <nav className="flex flex-col gap-2">
                {sidebarLinks.map((link, idx) => (
                  <div 
                    key={idx}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold tracking-wide transition-colors cursor-pointer ${
                      link.active 
                        ? 'bg-[#5FE8FF]/10 text-[#5FE8FF] border border-[#5FE8FF]/20' 
                        : 'text-[#F5F7FA]/55 hover:bg-[#F5F7FA]/5 hover:text-[#F5F7FA]'
                    }`}
                  >
                    <link.icon className="w-4 h-4" />
                    <span>{link.label}</span>
                  </div>
                ))}
              </nav>
            </div>

            {/* Profile Avatar indicator */}
            <div className="flex items-center gap-3 border-t border-[#F5F7FA]/5 pt-4 px-2">
              <div className="w-8 h-8 rounded-full bg-[#8B5CF6]/20 border border-[#8B5CF6]/30 flex items-center justify-center text-[#8B5CF6]">
                <User className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-[11px] font-bold text-[#F5F7FA]">Ozodbek S.</span>
                <span className="text-[9px] text-[#F5F7FA]/40">Developer Tier</span>
              </div>
            </div>
          </div>

          {/* 2. Main Workspace */}
          <div className="md:col-span-9 p-6 sm:p-8 flex flex-col gap-8">
            
            {/* Header bar */}
            <div className="flex justify-between items-center border-b border-[#F5F7FA]/5 pb-4">
              <div className="relative w-full max-w-xs">
                <input 
                  type="text" 
                  placeholder="Search projects..." 
                  disabled
                  className="w-full pl-9 pr-4 py-2 bg-[#05070D]/40 border border-[#F5F7FA]/5 rounded-lg text-[11px] placeholder-[#F5F7FA]/20 outline-none"
                />
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#F5F7FA]/20" />
              </div>
              <span className="text-[10px] font-mono text-[#F5F7FA]/30 uppercase">WORKSPACE_ID: 0x2A9C</span>
            </div>

            {/* Welcome messages */}
            <div className="flex flex-col gap-2">
              <h3 className="font-['Space_Grotesk'] text-2xl md:text-3xl font-bold text-[#F5F7FA]">
                Good evening, Ozodbek.
              </h3>
              <p className="text-xs sm:text-sm text-[#F5F7FA]/40 font-light">
                What would you like to accomplish today? Choose an action card below to load the workspace context.
              </p>
            </div>

            {/* Quick Action Cards Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mt-2">
              {quickActions.map((action, idx) => (
                <div 
                  key={idx}
                  className="relative p-5 rounded-xl border border-[#F5F7FA]/5 bg-[#05070D]/40 flex flex-col gap-3 transition-all duration-300 hover:border-[#5FE8FF]/20 hover:translate-y-[-2px] group cursor-pointer"
                >
                  <div className="w-8 h-8 rounded-lg bg-[#5FE8FF]/5 flex items-center justify-center text-[#5FE8FF] group-hover:bg-[#5FE8FF]/15 group-hover:text-white transition-all duration-300">
                    <action.icon className="w-4 h-4" />
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-bold text-[#F5F7FA]">{action.title}</span>
                    <span className="text-[9px] text-[#F5F7FA]/40 font-light leading-relaxed">{action.desc}</span>
                  </div>
                </div>
              ))}
            </div>

          </div>

        </motion.div>

      </div>
    </section>
  );
}
