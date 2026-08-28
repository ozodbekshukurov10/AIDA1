import React, { createContext, useContext, useState, useEffect } from 'react';

export type Language = 'uz' | 'en' | 'ru';

export const translations = {
  uz: {
    nav: {
      home: 'Bosh sahifa',
      capabilities: 'Imkoniyatlar',
      technology: 'Texnologiyalar',
      demo: 'AI Demo',
      replayIntro: 'Replay Intro',
      getStarted: 'Boshlash',
    },
    hero: {
      badge: 'AIDA 2.0 // NEYRON ENGINE ONLINE',
      title: 'A I D A',
      subtitle: 'Sun\'iy Ong va Avtonom Intellekt Tizimi',
      startBtn: 'AIDA bilan boshlash â†’',
      exploreBtn: '3D Olamni o\'rganish',
      scrollHint: '3D Kinetic Slayder uchun pastga scroll qiling',
    },
    slides: {
      discoverMore: '+ KO\'PROQ BILISH',
      engineOnline: 'AIDA 2.0 // NEYRON ENGINE ONLINE â†’',
      scrollOrClick: 'â†“ SCROLL QILING YOKI BOSING â†“',
      scrollForNext: 'â†“ KEYINGI BO\'LIM UCHUN SCROLL QILING â†“',
      slideshow: 'SLAYDSHOW',
      goBack: 'â†- ORQAGA QAYTISH',
      operational: '100% ISHLAMOQDA',
      swarmStatus: 'SWARM TIZIMI HOLATI',
      latencyIndex: 'TEZLIK INDEKSI',
      fastLatency: '1.2ms O\'TA TEZKOR',
      discoverMoreBtn: 'KO\'PROQ BILISH â†’',
    },
    cta: {
      onlineBadge: 'AIDA 2.0 ONLINE',
      contextBadge: '2M+ KONTEKST TOKENLAR',
      speedBadge: '1.2ms SWARM TEZLIGI',
      title: 'Kelajak intellekti shu yerdan boshlanadi.',
      subtitle: 'AIDA 2.0 bilan kelajak loyihalaringizni 1,024 ta avtonom neyron agentlar va 2M+ kontekst sig\'imi bilan boshlang.',
      startBtn: 'AIDA bilan boshlash',
    },
    footer: {
      rights: 'Barcha huquqlar himoyalangan.',
      platform: 'AIDA 2.0 Sun\'iy Intellekt Platformasi',
    }
  },
  en: {
    nav: {
      home: 'Home',
      capabilities: 'Capabilities',
      technology: 'Technology',
      demo: 'AI Demo',
      replayIntro: 'Replay Intro',
      getStarted: 'Get Started',
    },
    hero: {
      badge: 'AIDA 2.0 // NEURAL ENGINE ONLINE',
      title: 'A I D A',
      subtitle: 'Artificial Cognition & Autonomous Intelligence System',
      startBtn: 'Start with AIDA â†’',
      exploreBtn: 'Explore 3D World',
      scrollHint: 'Scroll for 3D Kinetic Showcase',
    },
    slides: {
      discoverMore: '+ DISCOVER MORE',
      engineOnline: 'AIDA 2.0 // NEURAL ENGINE ONLINE â†’',
      scrollOrClick: 'â†“ SCROLL OR CLICK â†“',
      scrollForNext: 'â†“ SCROLL FOR NEXT SECTION â†“',
      slideshow: 'SLIDESHOW',
      goBack: 'â†- GO BACK',
      operational: '100% OPERATIONAL',
      swarmStatus: 'SWARM PIPELINE STATUS',
      latencyIndex: 'LATENCY INDEX',
      fastLatency: '1.2ms ULTRA-FAST',
      discoverMoreBtn: 'DISCOVER MORE â†’',
    },
    cta: {
      onlineBadge: 'AIDA 2.0 ONLINE',
      contextBadge: '2M+ CONTEXT TOKENS',
      speedBadge: '1.2ms SWARM SPEED',
      title: 'The future of intelligence starts here.',
      subtitle: 'Launch your next-generation AI projects with AIDA 2.0 featuring 1,024 autonomous neural agents and 2M+ context window capacity.',
      startBtn: 'Start with AIDA',
    },
    footer: {
      rights: 'All rights reserved.',
      platform: 'AIDA 2.0 Artificial Intelligence Platform',
    }
  },
  ru: {
    nav: {
      home: 'Ð“Ð»Ð°Ð²Ð½Ð°Ñ-',
      capabilities: 'Ð’Ð¾Ð·Ð¼Ð¾Ð¶Ð½Ð¾Ñ-Ñ‚Ð¸',
      technology: 'Ð¢ÐµÑ…Ð½Ð¾Ð»Ð¾Ð³Ð¸Ð¸',
      demo: 'Ð˜Ð˜ Ð”ÐµÐ¼Ð¾',
      replayIntro: 'ÐŸÐµÑ€ÐµÑ-Ð¼Ð¾Ñ‚Ñ€ÐµÑ‚ÑŒ Ð¸Ð½Ñ‚Ñ€Ð¾',
      getStarted: 'Ð-Ð°Ñ‡Ð°Ñ‚ÑŒ Ñ€Ð°Ð±Ð¾Ñ‚Ñƒ',
    },
    hero: {
      badge: 'AIDA 2.0 // Ð-Ð•Ð™Ð ÐžÐ¡Ð•Ð¢Ð•Ð’ÐžÐ™ Ð”Ð’Ð˜Ð–ÐžÐš ÐžÐ-Ð›Ð-Ð™Ð-',
      title: 'A I D A',
      subtitle: 'Ð¡Ð¸Ñ-Ñ‚ÐµÐ¼Ð° Ð¸Ñ-ÐºÑƒÑ-Ñ-Ñ‚Ð²ÐµÐ½Ð½Ð¾Ð³Ð¾ Ñ€Ð°Ð·ÑƒÐ¼Ð° Ð¸ Ð°Ð²Ñ‚Ð¾Ð½Ð¾Ð¼Ð½Ð¾Ð³Ð¾ Ð¸Ð½Ñ‚ÐµÐ»Ð»ÐµÐºÑ‚Ð°',
      startBtn: 'Ð-Ð°Ñ‡Ð°Ñ‚ÑŒ Ñ- AIDA â†’',
      exploreBtn: 'Ð˜Ñ-Ñ-Ð»ÐµÐ´Ð¾Ð²Ð°Ñ‚ÑŒ 3D Ð¼Ð¸Ñ€',
      scrollHint: 'ÐŸÑ€Ð¾ÐºÑ€ÑƒÑ‚Ð¸Ñ‚Ðµ Ð´Ð»Ñ- 3D Kinetic Ñ-Ð»Ð°Ð¹Ð´-ÑˆÐ¾Ñƒ',
    },
    slides: {
      discoverMore: '+ Ð£Ð—Ð-Ð-Ð¢Ð¬ Ð‘ÐžÐ›Ð¬Ð¨Ð•',
      engineOnline: 'AIDA 2.0 // Ð-Ð•Ð™Ð ÐžÐ¡Ð•Ð¢Ð•Ð’ÐžÐ™ Ð”Ð’Ð˜Ð–ÐžÐš ÐžÐ-Ð›Ð-Ð™Ð- â†’',
      scrollOrClick: 'â†“ ÐŸÐ ÐžÐšÐ Ð£Ð¢Ð˜Ð¢Ð• Ð˜Ð›Ð˜ Ð-Ð-Ð–ÐœÐ˜Ð¢Ð• â†“',
      scrollForNext: 'â†“ ÐŸÐ ÐžÐšÐ Ð£Ð¢Ð˜Ð¢Ð• Ð”Ð›Ð¯ Ð¡Ð›Ð•Ð”Ð£Ð®Ð©Ð•Ð™ Ð¡Ð•ÐšÐ¦Ð˜Ð˜ â†“',
      slideshow: 'Ð¡Ð›Ð-Ð™Ð”-Ð¨ÐžÐ£',
      goBack: 'â†- Ð-Ð-Ð—Ð-Ð”',
      operational: '100% Ð Ð-Ð‘ÐžÐ¢Ð-Ð•Ð¢',
      swarmStatus: 'Ð¡Ð¢Ð-Ð¢Ð£Ð¡ Ð¡Ð˜Ð¡Ð¢Ð•ÐœÐ« SWARM',
      latencyIndex: 'Ð˜Ð-Ð”Ð•ÐšÐ¡ Ð—Ð-Ð”Ð•Ð Ð–ÐšÐ˜',
      fastLatency: '1.2Ð¼Ñ- Ð¡Ð’Ð•Ð Ð¥Ð‘Ð«Ð¡Ð¢Ð Ðž',
      discoverMoreBtn: 'Ð£Ð—Ð-Ð-Ð¢Ð¬ Ð‘ÐžÐ›Ð¬Ð¨Ð• â†’',
    },
    cta: {
      onlineBadge: 'AIDA 2.0 ÐžÐ-Ð›Ð-Ð™Ð-',
      contextBadge: '2M+ ÐšÐžÐ-Ð¢Ð•ÐšÐ¡Ð¢Ð-Ð«Ð¥ Ð¢ÐžÐšÐ•Ð-ÐžÐ’',
      speedBadge: '1.2Ð¼Ñ- Ð¡ÐšÐžÐ ÐžÐ¡Ð¢Ð¬ SWARM',
      title: 'Ð‘ÑƒÐ´ÑƒÑ‰ÐµÐµ Ð¸Ð½Ñ‚ÐµÐ»Ð»ÐµÐºÑ‚Ð° Ð½Ð°Ñ‡Ð¸Ð½Ð°ÐµÑ‚Ñ-Ñ- Ð·Ð´ÐµÑ-ÑŒ.',
      subtitle: 'Ð—Ð°Ð¿ÑƒÑ-ÐºÐ°Ð¹Ñ‚Ðµ Ð¿Ñ€Ð¾ÐµÐºÑ‚Ñ‹ Ð±ÑƒÐ´ÑƒÑ‰ÐµÐ³Ð¾ Ñ- AIDA 2.0, Ð¾Ñ-Ð½Ð°Ñ‰ÐµÐ½Ð½Ð¾Ð¹ 1,024 Ð°Ð²Ñ‚Ð¾Ð½Ð¾Ð¼Ð½Ñ‹Ð¼Ð¸ Ð½ÐµÐ¹Ñ€Ð¾Ð°Ð³ÐµÐ½Ñ‚Ð°Ð¼Ð¸ Ð¸ Ð¾Ð±ÑŠÐµÐ¼Ð¾Ð¼ ÐºÐ¾Ð½Ñ‚ÐµÐºÑ-Ñ‚Ð° 2M+ Ñ‚Ð¾ÐºÐµÐ½Ð¾Ð².',
      startBtn: 'Ð-Ð°Ñ‡Ð°Ñ‚ÑŒ Ñ- AIDA',
    },
    footer: {
      rights: 'Ð’Ñ-Ðµ Ð¿Ñ€Ð°Ð²Ð° Ð·Ð°Ñ‰Ð¸Ñ‰ÐµÐ½Ñ‹.',
      platform: 'ÐŸÐ»Ð°Ñ‚Ñ„Ð¾Ñ€Ð¼Ð° Ð¸Ñ-ÐºÑƒÑ-Ñ-Ñ‚Ð²ÐµÐ½Ð½Ð¾Ð³Ð¾ Ð¸Ð½Ñ‚ÐµÐ»Ð»ÐµÐºÑ‚Ð° AIDA 2.0',
    }
  }
};

interface LanguageContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: typeof translations.uz;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<Language>(() => {
    const saved = localStorage.getItem('aida_lang');
    return (saved === 'en' || saved === 'ru' || saved === 'uz') ? saved : 'uz';
  });

  const setLang = (newLang: Language) => {
    setLangState(newLang);
    localStorage.setItem('aida_lang', newLang);
  };

  const t = translations[lang] || translations.uz;

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
