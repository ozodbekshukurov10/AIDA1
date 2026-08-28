/**
 * useScrollBrain.ts
 *
 * Observes scroll position across named sections using IntersectionObserver
 * and returns the current active BrainRegion for the AIBrain component.
 * Zero scroll event listeners — fully passive via observer API.
 */

import { useEffect, useState } from 'react';
import { BrainRegion } from '../components/ai/AIBrain';

// Mapping of section IDs → BrainRegion
const SECTION_MAP: { id: string; region: BrainRegion }[] = [
  { id: 'hero',         region: 'idle' },
  { id: 'features',     region: 'perception' },
  { id: 'capabilities', region: 'context' },
  { id: 'technology',   region: 'reasoning' },
  { id: 'demo',         region: 'tools' },
  { id: 'intelligence', region: 'verification' },
  { id: 'cta',          region: 'response' },
];

export function useScrollBrain(): BrainRegion {
  const [region, setRegion] = useState<BrainRegion>('idle');

  useEffect(() => {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      return;
    }

    const observers: IntersectionObserver[] = [];

    SECTION_MAP.forEach(({ id, region: sectionRegion }) => {
      const el = document.getElementById(id);
      if (!el) return;

      const observer = new IntersectionObserver(
        entries => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              setRegion(sectionRegion);
            }
          });
        },
        {
          root: null,
          rootMargin: '-30% 0px -30% 0px', // trigger when 30% from top & bottom
          threshold: 0,
        }
      );

      observer.observe(el);
      observers.push(observer);
    });

    return () => {
      observers.forEach(o => o.disconnect());
    };
  }, []);

  return region;
}
