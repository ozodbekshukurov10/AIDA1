import React from 'react';
import { motion } from 'motion/react';

interface GlowBorderProps {
  children: React.ReactNode;
  className?: string;
  glowColor?: string;
}

export default function GlowBorder({ 
  children, 
  className = '', 
  glowColor = 'rgba(95, 232, 255, 0.25)' 
}: GlowBorderProps) {
  return (
    <div className={`relative p-[1px] rounded-2xl overflow-hidden group ${className}`}>
      
      {/* Animating gradient border lines behind the container */}
      <motion.div 
        className="absolute inset-0 bg-gradient-to-r from-[#5FE8FF] via-[#4D7CFF] to-[#8B5CF6]"
        animate={{ 
          backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'] 
        }}
        transition={{ 
          duration: 6, 
          repeat: Infinity, 
          ease: "linear" 
        }}
        style={{
          backgroundSize: '200% 200%',
          filter: `drop-shadow(0 0 8px ${glowColor})`
        }}
      />

      {/* Main Inner Content container */}
      <div className="relative w-full h-full bg-[#05070D] rounded-[15px] z-10">
        {children}
      </div>

    </div>
  );
}
