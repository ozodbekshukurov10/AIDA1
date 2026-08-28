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
    // Attract the button towards cursor, capped at 12px
    setCoords({ x: x * 0.3, y: y * 0.3 });
  };

  const handleMouseLeave = () => {
    setCoords({ x: 0, y: 0 });
  };

  const baseStyles = "relative px-7 py-3.5 font-bold text-sm tracking-wider rounded-2xl cursor-pointer select-none overflow-hidden magnetic-target flex items-center justify-center gap-2 outline-none transition-all duration-300 disabled:opacity-45 disabled:cursor-not-allowed disabled:transform-none";
  
  const variants = {
    primary: "bg-gradient-to-r from-[#4C7DFF] to-[#7C5CFF] text-[#F5F7FF] shadow-[0_0_20px_rgba(76,125,255,0.15)] hover:shadow-[0_0_30px_rgba(93,232,255,0.35)] border border-transparent hover:from-[#5DE8FF] hover:to-[#4C7DFF] hover:text-[#03050A]",
    secondary: "bg-white/[0.03] border border-white/8 text-[#F5F7FF] hover:bg-[rgba(76,125,255,0.05)] hover:border-[#4C7DFF]/50",
    ghost: "bg-transparent text-[#9CA9BC] hover:text-[#F5F7FF] hover:bg-white/5 border border-transparent"
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
      transition={{ type: 'spring', stiffness: 200, damping: 15, mass: 0.5 }}
      className={`${baseStyles} ${variants[variant]} ${className}`}
    >
      {/* Visual background sweep overlay */}
      {variant === 'primary' && (
        <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-out pointer-events-none" />
      )}
      <span className="relative z-10 flex items-center gap-2">
        {children}
      </span>
    </motion.button>
  );
}
