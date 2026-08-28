import React from 'react';

interface GlassPanelProps {
  children: React.ReactNode;
  className?: string;
  intensity?: 'low' | 'medium' | 'high';
}

export default function GlassPanel({ 
  children, 
  className = '', 
  intensity = 'medium' 
}: GlassPanelProps) {
  
  const blurStyles = {
    low: 'bg-[#08111F]/10 backdrop-blur-sm border-[#F5F7FA]/5',
    medium: 'bg-[#08111F]/20 backdrop-blur-md border-[#5FE8FF]/10',
    high: 'bg-[#08111F]/35 backdrop-blur-xl border-[#5FE8FF]/15'
  };

  return (
    <div className={`rounded-2xl border ${blurStyles[intensity]} shadow-[0_12px_40px_rgba(0,0,0,0.35)] ${className}`}>
      {children}
    </div>
  );
}
