import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

interface StoryTextProps {
  active: boolean;
}

export default function StoryText({ active }: StoryTextProps) {
  const [step, setStep] = useState(0); // 0: first message, 1: second message

  useEffect(() => {
    if (!active) {
      setStep(0);
      return;
    }

    const timer = setTimeout(() => {
      setStep(1);
    }, 1500);

    return () => clearTimeout(timer);
  }, [active]);

  if (!active) return null;

  const message1 = ["WE LIVE IN", "A WORLD OF", "INFORMATION."];
  const message2 = ["BUT INFORMATION", "ISN’T INTELLIGENCE."];

  const lineVariants = {
    hidden: { opacity: 0, y: 22, filter: "blur(8px)" },
    visible: (i: number) => ({
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      transition: {
        duration: 0.8,
        delay: i * 0.18,
        ease: [0.16, 1, 0.3, 1],
      },
    }),
    exit: {
      opacity: 0,
      y: -15,
      filter: "blur(10px)",
      transition: { duration: 0.5 },
    },
  };

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-transparent z-25 px-6 md:px-12 pointer-events-none select-none">
      <AnimatePresence mode="wait">
        {step === 0 ? (
          <motion.div
            key="msg1"
            initial="hidden"
            animate="visible"
            exit="exit"
            className="text-center max-w-4xl flex flex-col gap-1 items-center"
          >
            {message1.map((line, idx) => (
              <div key={idx} className="overflow-hidden py-1">
                <motion.h2
                  custom={idx}
                  variants={lineVariants}
                  className="font-['Space_Grotesk'] font-bold text-[#F5F7FF]/90 text-3xl md:text-5xl lg:text-6xl tracking-wider leading-tight"
                >
                  {line}
                </motion.h2>
              </div>
            ))}
          </motion.div>
        ) : (
          <motion.div
            key="msg2"
            initial="hidden"
            animate="visible"
            exit="exit"
            className="text-center max-w-4xl flex flex-col gap-1 items-center"
          >
            {message2.map((line, idx) => (
              <div key={idx} className="overflow-hidden py-1">
                <motion.h2
                  custom={idx}
                  variants={lineVariants}
                  className="font-['Space_Grotesk'] font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-[#F5F7FF] via-[#5DE8FF] to-[#7C5CFF] text-3xl md:text-6xl lg:text-7xl tracking-wider leading-tight filter drop-shadow-[0_0_25px_rgba(93,232,255,0.2)]"
                >
                  {line}
                </motion.h2>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
