import React, { useRef, useState } from 'react';
import { motion } from 'motion/react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  variant?: 'primary' | 'secondary' | 'ghost';
  type?: 'button' | 'submit';
  disabled?: boolean;
}

export default function Button({ 
  children, 
  onClick, 
  className = '', 
  variant = 'primary', 
  type = 'button', 
  disabled = false 
}: ButtonProps) {
  const btnRef = useRef<HTMLButtonElement>(null);
  const [coords, setCoords] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent) => {
    const btn = btnRef.current;
    if (!btn) return;
    const rect = btn.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    setCoords({ x: x * 0.25, y: y * 0.25 });
  };

  const handleMouseLeave = () => {
    setCoords({ x: 0, y: 0 });
  };

  const baseStyles = "relative px-8 py-3.5 font-['Space_Grotesk'] font-bold text-sm tracking-wider rounded-2xl cursor-pointer select-none overflow-hidden flex items-center justify-center gap-2.5 outline-none transition-all duration-300 disabled:opacity-45 disabled:cursor-not-allowed disabled:transform-none backdrop-blur-md";
  
  const variants = {
    primary: "bg-gradient-to-r from-[#5B75FF] via-[#705CFF] to-[#8C52FF] text-white shadow-[0_0_25px_rgba(112,92,255,0.4)] border border-white/20 hover:shadow-[0_0_35px_rgba(93,232,255,0.5)] hover:border-[#5DE8FF]",
    secondary: "bg-[#0E0C22]/80 border border-[#7C5CFF]/50 text-[#F5F7FF] shadow-[0_0_20px_rgba(124,92,255,0.25)] hover:border-[#5DE8FF] hover:shadow-[0_0_30px_rgba(93,232,255,0.35)] hover:bg-[#0E0C22]",
    ghost: "bg-[#0B0C16]/80 border border-white/15 text-[#F5F7FF] hover:border-white/40 hover:bg-white/10 hover:shadow-[0_0_20px_rgba(255,255,255,0.15)]"
  };

  return (
    <motion.button
      ref={btnRef}
      type={type}
      onClick={onClick}
      disabled={disabled}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      animate={{ x: coords.x, y: coords.y }}
      whileHover={{ scale: 1.04 }}
      whileTap={{ scale: 0.96 }}
      transition={{ type: 'spring', stiffness: 220, damping: 16, mass: 0.5 }}
      className={`${baseStyles} ${variants[variant]} ${className}`}
    >
      <span className="relative z-10 flex items-center gap-2">
        {children}
      </span>
    </motion.button>
  );
}
