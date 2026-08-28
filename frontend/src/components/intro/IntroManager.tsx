import React from 'react';
import OpeningSequenceIntro from './OpeningSequenceIntro';

interface IntroManagerProps {
  onComplete: () => void;
}

export default function IntroManager({ onComplete }: IntroManagerProps) {
  return <OpeningSequenceIntro onComplete={onComplete} />;
}
