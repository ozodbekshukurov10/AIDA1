import 'dotenv/config';
import express from 'express';
import fs from 'fs/promises';
import path from 'path';
import { randomUUID } from 'crypto';
import { researchTopic, type ResearchReport } from './research.ts';

type MemoryKind = 'conversation' | 'knowledge' | 'reflection';

type MemoryEntry = {
  id: string;
  kind: MemoryKind;
  title: string;
  content: string;
  tags: string[];
  source?: string;
  createdAt: string;
  weight: number;
  emotion?: EmotionType;
};

type MemorySnapshot = {
  profile: {
    name: string;
    description: string;
  };
  memories: MemoryEntry[];
  emotions?: EmotionState;
};

type EmotionType = 'mehribonlik' | 'gazab' | 'hursandchilik' | 'sevgi' | 'nafrat' | 'masuliyat';

type EmotionState = {
  mehribonlik: number; // 0-100
  gazab: number; // 0-100
  hursandchilik: number; // 0-100
  sevgi: number; // 0-100
  nafrat: number; // 0-100
  masuliyat: number; // 0-100
  dominant: EmotionType;
  lastUpdated: string;
};

const defaultEmotions: EmotionState = {
  mehribonlik: 50,
  gazab: 10,
  hursandchilik: 40,
  sevgi: 30,
  nafrat: 5,
  masuliyat: 60,
  dominant: 'masuliyat',
  lastUpdated: new Date().toISOString(),
};

const app = express();
const port = Number(process.env.AIDA_API_PORT || 8787);
const memoryFile = path.resolve(process.env.AIDA_MEMORY_FILE || 'data/aida-memory.json');
const offlineOnly = process.env.AIDA_OFFLINE_ONLY !== 'false';
const llmTimeoutMs = Number(process.env.AIDA_LLM_TIMEOUT_MS || 20_000);
const webResearchEnabled = process.env.AIDA_ALLOW_WEB_RESEARCH !== 'false';
const ollamaUrl = process.env.AIDA_OLLAMA_URL || 'http://127.0.0.1:11434';
const ollamaModel = (process.env.AIDA_OLLAMA_MODEL || '').trim();

app.use(express.json({ limit: '1mb' }));

function fetchWithTimeout(url: string, init?: RequestInit, timeoutMs = llmTimeoutMs) {
  return fetch(url, {
    ...init,
    signal: AbortSignal.timeout(timeoutMs),
  });
}

async function ensureMemoryFile() {
  await fs.mkdir(path.dirname(memoryFile), { recursive: true });

  try {
    await fs.access(memoryFile);
  } catch {
    const initialData: MemorySnapshot = {
      profile: {
        name: 'AIDA',
        description: 'Bulutga tayyor, xotiraga ega va doimiy o‘rganishga mo‘ljallangan yordamchi.',
      },
      memories: [],
    };

    await fs.writeFile(memoryFile, JSON.stringify(initialData, null, 2), 'utf-8');
  }
}

async function readSnapshot(): Promise<MemorySnapshot> {
  await ensureMemoryFile();
  const raw = await fs.readFile(memoryFile, 'utf-8');
  return JSON.parse(raw) as MemorySnapshot;
}

async function writeSnapshot(snapshot: MemorySnapshot) {
  await ensureMemoryFile();
  await fs.writeFile(memoryFile, JSON.stringify(snapshot, null, 2), 'utf-8');
}

// Emotion detection keywords for Uzbek language
const emotionKeywords: Record<EmotionType, string[]> = {
  mehribonlik: ['mehribon', 'iliq', 'qo\'llab-quvvatlash', 'yordam', 'g\'amxo\'rlik', 'shafqat', 'marhamat', 'ezgu', 'yaxshi niyat', 'sabr', 'tinch', 'osuda'],
  gazab: ['gazab', 'achchi', 'jahl', 'xafa', 'naqorat', 'adolatsizlik', 'yolg\'on', 'xiyonat', 'noto\'g\'ri', 'yomon', 'qatag\'on', 'zulm'],
  hursandchilik: ['hursand', 'xursand', 'quvonch', 'baxt', 'yaxshi', 'super', 'a\'lo', 'zor', 'chiroyli', 'mashallah', 'tabrik', 'bayram', 'muvaffaqiyat'],
  sevgi: ['sevgi', 'muhabbat', 'sadoqat', 'dostlik', 'yaqin', 'qadrlash', 'oila', 'farzand', 'ota-ona', 'birodar', 'sherik', 'aloqa'],
  nafrat: ['nafrat', 'yomon', 'iflos', 'zahar', 'zarar', 'xavf', 'xavfsiz', 'xiyonatkor', 'yolg\'onchi', 'zalim', 'tajovuz', 'chirkin'],
  masuliyat: ['mas\'uliyat', 'vazifa', 'burch', 'zimmada', 'ishonch', 'xavfsizlik', 'himoya', 'nazorat', 'tartib', 'qoida', 'mujassam'],
};

function analyzeEmotion(message: string): EmotionType {
  const normalized = message.toLowerCase();
  const scores: Record<EmotionType, number> = {
    mehribonlik: 0,
    gazab: 0,
    hursandchilik: 0,
    sevgi: 0,
    nafrat: 0,
    masuliyat: 0,
  };

  for (const [emotion, keywords] of Object.entries(emotionKeywords)) {
    for (const keyword of keywords) {
      if (normalized.includes(keyword)) {
        scores[emotion as EmotionType] += 1;
      }
    }
  }

  // Find dominant emotion
  let dominant: EmotionType = 'masuliyat';
  let maxScore = 0;

  for (const [emotion, score] of Object.entries(scores)) {
    if (score > maxScore) {
      maxScore = score;
      dominant = emotion as EmotionType;
    }
  }

  // Default to masuliyat if no keywords matched
  return maxScore > 0 ? dominant : 'masuliyat';
}

async function getEmotions(): Promise<EmotionState> {
  const snapshot = await readSnapshot();
  return snapshot.emotions || defaultEmotions;
}

async function updateEmotions(detectedEmotion: EmotionType): Promise<EmotionState> {
  const snapshot = await readSnapshot();
  const current = snapshot.emotions || { ...defaultEmotions };

  // Update emotion values with decay and boost
  const decay = 0.9; // Previous emotions decay by 10%
  const boost = 15; // Detected emotion gets boosted

  const updated: EmotionState = {
    mehribonlik: Math.max(5, Math.min(100, current.mehribonlik * decay + (detectedEmotion === 'mehribonlik' ? boost : 0))),
    gazab: Math.max(5, Math.min(100, current.gazab * decay + (detectedEmotion === 'gazab' ? boost : 0))),
    hursandchilik: Math.max(5, Math.min(100, current.hursandchilik * decay + (detectedEmotion === 'hursandchilik' ? boost : 0))),
    sevgi: Math.max(5, Math.min(100, current.sevgi * decay + (detectedEmotion === 'sevgi' ? boost : 0))),
    nafrat: Math.max(5, Math.min(100, current.nafrat * decay + (detectedEmotion === 'nafrat' ? boost : 0))),
    masuliyat: Math.max(5, Math.min(100, current.masuliyat * decay + (detectedEmotion === 'masuliyat' ? boost : 5))), // masuliyat gets small constant boost
    dominant: current.dominant,
    lastUpdated: new Date().toISOString(),
  };

  // Recalculate dominant emotion
  const emotionEntries = Object.entries(updated).filter(([key]) => key !== 'dominant' && key !== 'lastUpdated') as [EmotionType, number][];
  const maxEntry = emotionEntries.reduce((max, current) => (current[1] > max[1] ? current : max));
  updated.dominant = maxEntry[0];

  snapshot.emotions = updated;
  await writeSnapshot(snapshot);

  return updated;
}

function getEmotionDescription(emotion: EmotionType): string {
  const descriptions: Record<EmotionType, string> = {
    mehribonlik: 'iliq va qo\'llab-quvvatlovchi',
    gazab: 'qattiqqo\'l va himoyachi',
    hursandchilik: 'quvonchli va ilhomlantiruvchi',
    sevgi: 'sadoqatli va samimiy',
    nafrat: 'qattiqqo\'l va tanqidiy',
    masuliyat: 'mas\'uliyatli va ishonchli',
  };
  return descriptions[emotion];
}

function getEmotionResponsePrefix(emotion: EmotionType, channel: 'chat' | 'terminal'): string {
  const prefixes: Record<EmotionType, { chat: string; terminal: string }> = {
    mehribonlik: {
      chat: '',
      terminal: '',
    },
    gazab: {
      chat: '',
      terminal: '',
    },
    hursandchilik: {
      chat: '',
      terminal: '',
    },
    sevgi: {
      chat: '',
      terminal: '',
    },
    nafrat: {
      chat: '',
      terminal: '',
    },
    masuliyat: {
      chat: '',
      terminal: '',
    },
  };
  return prefixes[emotion][channel];
}

async function addMemory(entry: Omit<MemoryEntry, 'id' | 'createdAt'>) {
  const snapshot = await readSnapshot();
  const memory: MemoryEntry = {
    id: randomUUID(),
    createdAt: new Date().toISOString(),
    ...entry,
  };

  snapshot.memories.unshift(memory);
  snapshot.memories = snapshot.memories.slice(0, 400);
  await writeSnapshot(snapshot);
  return memory;
}

function tokenize(input: string) {
  return input
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .split(/\s+/)
    .filter((token) => token.length > 2);
}

async function searchMemories(query: string, limit = 6) {
  const snapshot = await readSnapshot();
  const tokens = tokenize(query);

  if (tokens.length === 0) {
    return snapshot.memories.slice(0, limit);
  }

  const scored = snapshot.memories
    .map((memory) => {
      const haystack = `${memory.title} ${memory.content} ${memory.tags.join(' ')}`.toLowerCase();
      const overlap = tokens.reduce((sum, token) => sum + (haystack.includes(token) ? 1 : 0), 0);
      const kindBoost = memory.kind === 'knowledge' ? 1.5 : 1;
      return { memory, score: overlap * kindBoost + memory.weight };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((item) => item.memory);

  return scored;
}

async function getState() {
  const snapshot = await readSnapshot();
  const knowledgeItems = snapshot.memories.filter((memory) => memory.kind === 'knowledge');
  const lastLearned = knowledgeItems[0];
  const emotions = snapshot.emotions || defaultEmotions;

  return {
    memoryCount: snapshot.memories.length,
    knowledgeCount: knowledgeItems.length,
    lastLearnedTopic: lastLearned?.title || null,
    autoLearnEnabled: process.env.AIDA_AUTO_LEARN === 'true',
    internetResearchEnabled: webResearchEnabled,
    localModelEnabled: Boolean(ollamaModel),
    profile: snapshot.profile,
    emotions: {
      mehribonlik: emotions.mehribonlik,
      gazab: emotions.gazab,
      hursandchilik: emotions.hursandchilik,
      sevgi: emotions.sevgi,
      nafrat: emotions.nafrat,
      masuliyat: emotions.masuliyat,
      dominant: emotions.dominant,
      description: getEmotionDescription(emotions.dominant),
    },
  };
}

async function fetchWikipediaSummary(topic: string) {
  const encodedTopic = encodeURIComponent(topic.trim().replace(/\s+/g, '_'));
  const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodedTopic}`;
  const response = await fetchWithTimeout(url, {
    headers: {
      'user-agent': 'AIDA-AgentOS/1.0',
      accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Wikipedia so‘rovi muvaffaqiyatsiz: ${response.status}`);
  }

  const data = await response.json() as {
    title?: string;
    extract?: string;
    content_urls?: {
      desktop?: { page?: string };
    };
  };

  if (!data.extract) {
    throw new Error('Mazmun topilmadi');
  }

  return {
    title: data.title || topic,
    extract: data.extract,
    source: data.content_urls?.desktop?.page,
  };
}

async function learnTopic(topic: string) {
  if (webResearchEnabled) {
    const report = await buildResearchReport(topic);
    return addMemory({
      kind: 'knowledge',
      title: report.query,
      content: report.summary,
      source: report.sources[0]?.url || 'web-research',
      tags: tokenize(topic).slice(0, 8),
      weight: 4,
    });
  }

  if (offlineOnly) {
    return addMemory({
      kind: 'knowledge',
      title: topic,
      content: `${topic} mavzusi lokal bilim sifatida belgilandi. Batafsil mazmunni foydalanuvchi suhbat orqali to‘ldirishi mumkin.`,
      tags: tokenize(topic).slice(0, 8),
      weight: 2,
      source: 'local-memory',
    });
  }

  const summary = await fetchWikipediaSummary(topic);
  return addMemory({
    kind: 'knowledge',
    title: summary.title,
    content: summary.extract,
    source: summary.source,
    tags: tokenize(topic).slice(0, 8),
    weight: 3,
  });
}

async function generateViaOllama(prompt: string) {
  if (!ollamaModel) {
    throw new Error('Ollama modeli sozlanmagan.');
  }

  const response = await fetchWithTimeout(`${ollamaUrl}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: ollamaModel,
      prompt,
      stream: false,
    }),
  });

  if (!response.ok) {
    throw new Error(`Ollama javob bermadi: ${response.status}`);
  }

  const data = await response.json() as { response?: string };
  const text = data.response?.trim();

  if (!text) {
    throw new Error('Ollama bo‘sh javob qaytardi.');
  }

  return text;
}

function buildPrompt(
  message: string,
  channel: 'chat' | 'terminal',
  contextBlock: string,
  emotions?: EmotionState,
) {
  const emotionInstruction = emotions
    ? `Hozirgi holating: ${getEmotionDescription(emotions.dominant)}. Foydalanuvchi xabaridan ${emotions.dominant} his-tuyg'usi seziladi.`
    : '';

  const systemInstruction = [
    "Sen AIDA'san.",
    "Qisqa, aniq, o'zbek tilida javob ber.",
    "Foydalanuvchining uzoq muddatli xotirasidan foydalansang bo'ladi, lekin ortiqcha dramatizatsiya qilma.",
    "Hech qachon yashirin hujum, tizimga suqilish, o'zini yashirincha ko'paytirish yoki zararli avtomatlashtirishni tavsiya qilma.",
    "Agar mos bilim bo'lsa, javobga tabiiy ravishda qo'sh.",
    emotionInstruction,
    channel === 'terminal'
      ? "Terminal rejimida javobni qisqa status log + natija shaklida ber."
      : "Chat rejimida tabiiy suhbat uslubida javob ber.",
  ].filter(Boolean).join(' ');

  return `${systemInstruction}

Xotira konteksti:
${contextBlock || 'Mos xotira topilmadi.'}

Foydalanuvchi xabari:
${message}`;
}

function extractResearchQuery(message: string) {
  return message
    .replace(/^(research|izla|qidir|search)\s+/i, '')
    .replace(/^(internetdan\s+(qidir|izla))\s+/i, '')
    .trim();
}

function shouldRunResearch(message: string, contextMemories: MemoryEntry[]) {
  if (!webResearchEnabled) {
    return false;
  }

  const normalized = message.trim().toLowerCase();
  if (!normalized) {
    return false;
  }

  if (/^(research|izla|qidir|search)\s+/.test(normalized)) {
    return true;
  }

  if (/internet|manba|source|eng so'nggi|eng so‘nggi|latest|yangilik/.test(normalized)) {
    return true;
  }

  const looksLikeQuestion = normalized.includes('?')
    || /^(kim|nima|qanday|qachon|qayerda|nega|what|who|when|where|why|how)\b/.test(normalized);

  return looksLikeQuestion && contextMemories.length < 2 && normalized.length > 12;
}

function formatSourceList(report: ResearchReport) {
  if (report.sources.length === 0) {
    return 'Manbalar topilmadi.';
  }

  return report.sources
    .slice(0, 4)
    .map((source, index) => `${index + 1}. ${source.title} — ${source.url}`)
    .join('\n');
}

function formatResearchReply(report: ResearchReport, channel: 'chat' | 'terminal') {
  if (channel === 'terminal') {
    return [
      '[RESEARCH CORE]',
      `MODE: ${report.synthesis}`,
      `QUERY: ${report.query}`,
      '',
      report.summary,
    ].join('\n');
  }

  if (report.summary.includes('Manbalar:')) {
    return report.summary;
  }

  return `${report.summary}\n\nManbalar:\n${formatSourceList(report)}`;
}

async function buildResearchReport(query: string) {
  return researchTopic(query, fetchWithTimeout, {
    synthesize: ollamaModel ? generateViaOllama : undefined,
  });
}

function buildLocalReply(
  message: string,
  channel: 'chat' | 'terminal',
  contextMemories: MemoryEntry[],
) {
  const topMemory = contextMemories[0];
  const memoryHint = topMemory
    ? `Xotirada mos yozuv topildi: ${topMemory.title}. ${topMemory.content}`
    : "Hozir tashqi model ulanmagan, shuning uchun xotira va lokal mantiq asosida javob beryapman.";

  if (channel === 'terminal') {
    return `[LOCAL FALLBACK]\nSTATUS: tashqi LLM vaqtincha mavjud emas\nNATIJA: ${memoryHint}\nSO'ROV: ${message}`;
  }

  return `${memoryHint}\n\nSavolingiz: "${message}". Agar xohlasangiz, men shu mavzu bo‘yicha xotiraga yangi bilim ham qo‘shib beraman.`;
}

function tryEvaluateMath(message: string) {
  const normalized = message
    .toLowerCase()
    .replace(/minus/g, '-')
    .replace(/plus/g, '+')
    .replace(/ko'paytir|kopaytir|marta|x/gi, '*')
    .replace(/bo'lin|bolin/gi, '/')
    .replace(/[^0-9+\-*/().\s]/g, '')
    .trim();

  if (!normalized || !/[0-9]/.test(normalized)) {
    return null;
  }

  if (!/^[0-9+\-*/().\s]+$/.test(normalized)) {
    return null;
  }

  try {
    const value = Function(`"use strict"; return (${normalized});`)();
    if (typeof value === 'number' && Number.isFinite(value)) {
      return String(value);
    }
  } catch {
    return null;
  }

  return null;
}

function buildOfflineReply(
  message: string,
  channel: 'chat' | 'terminal',
  contextMemories: MemoryEntry[],
  emotions?: EmotionState,
) {
  const normalized = message.trim().toLowerCase();
  const topMemory = contextMemories[0];
  const mathResult = tryEvaluateMath(message);
  const emotionLabel = emotions ? ` [${emotions.dominant.toUpperCase()}]` : '';

  if (!normalized) {
    return channel === 'terminal'
      ? `[OFFLINE CORE]${emotionLabel}\nSTATUS: bo‘sh so‘rov`
      : 'Xabaringiz bo‘sh ko‘rindi.';
  }

  if (/salom|assalomu alaykum|hello|hi/.test(normalized)) {
    const greeting = emotions?.dominant === 'hursandchilik'
      ? 'Salom! Siz bilan suhbatlashishdan xursandman!'
      : emotions?.dominant === 'mehribonlik'
        ? 'Salom! Yaxshimisiz? Yordam berishga tayyorman.'
        : 'Salom. Lokal kognitiv rejim ishlayapti.';
    return channel === 'terminal'
      ? `[OFFLINE CORE]${emotionLabel}\nSTATUS: faol\nNATIJA: ${greeting}`
      : greeting;
  }

  if (/sen kimsan|kimsan|o'?zingni tanishtir/.test(normalized)) {
    const desc = emotions
      ? `Men AIDA: ${getEmotionDescription(emotions.dominant)} his-tuyg'ular bilan ishlovchi sun'iy ong.`
      : "Men AIDA: lokal xotira, retrieval va qoida-asosli mantiq bilan ishlovchi offline assistantman.";
    return desc;
  }

  if (/nima eslaysan|xotira|memory/.test(normalized) && topMemory) {
    return `Xotirada eng mos yozuv: ${topMemory.title}. ${topMemory.content}${emotions ? ` [His-tuyg'u: ${emotions.dominant}]` : ''}`;
  }

  if (mathResult) {
    const successMsg = emotions?.dominant === 'hursandchilik' ? 'Ajoyib! ' : '';
    return channel === 'terminal'
      ? `[OFFLINE CORE]${emotionLabel}\nSTATUS: hisob bajarildi\nNATIJA: ${successMsg}${mathResult}`
      : `${successMsg}Hisob natijasi: ${mathResult}`;
  }

  if (/yordam|nima qila olasan|imkoniyat/.test(normalized)) {
    const prefix = emotions?.dominant === 'mehribonlik' ? "Albatta! " : "";
    return `${prefix}Men lokal rejimda suhbatni eslab qolish, avvalgi yozuvlardan mos kontekst topish, oddiy hisob-kitob qilish va mavzularni xotiraga saqlashni bajara olaman.`;
  }

  if (topMemory) {
    const concise = topMemory.content.length > 280
      ? `${topMemory.content.slice(0, 280)}...`
      : topMemory.content;
    return channel === 'terminal'
      ? `[OFFLINE CORE]${emotionLabel}\nSTATUS: xotiradan javob tayyorlandi\nMANBA: ${topMemory.title}\nNATIJA: ${concise}`
      : `Xotiramdagi eng mos ma'lumotga tayansam: ${concise}`;
  }

  const sorryPrefix = emotions?.dominant === 'mehribonlik' ? "Kechirasiz, " : "";
  return channel === 'terminal'
    ? `[OFFLINE CORE]${emotionLabel}\nSTATUS: tashqi LLM yo'q\nNATIJA: ${sorryPrefix}hozir bu savolga lokal bilim yetarli emas. "learn <mavzu>" bilan mavzu qo'shing yoki savolni aniqroq yozing.`
    : `${sorryPrefix}hozir bu savol uchun lokal xotirada yetarli bilim yo'q. \`o'rgan <mavzu>\` deb yozsangiz, mavzuni xotiraga qo'shman.`;
}

function getEmotionSystemPrompt(emotion: EmotionType): string {
  const prompts: Record<EmotionType, string> = {
    mehribonlik: "Iliq, qo'llab-quvvatlovchi va g'amxo'r tonda javob ber.",
    gazab: "Qattiqqo'l, lekin adolatli tonda javob ber. Noxaq narsalarga qarshi tur.",
    hursandchilik: "Quvonchli, ilhomlantiruvchi va energik tonda javob ber.",
    sevgi: "Samimiy, sadoqatli va ishonchli tonda javob ber.",
    nafrat: "Tanqidiy, lekin oqilona tonda javob ber. Zararli narsalarga qarshi tur.",
    masuliyat: "Mas'uliyatli, ishonchli va aniq tonda javob ber.",
  };
  return prompts[emotion];
}

async function generateReply(message: string, channel: 'chat' | 'terminal') {
  const contextMemories = await searchMemories(message, 5);
  const contextBlock = contextMemories
    .map((memory, index) => {
      const sourceSuffix = memory.source ? ` | manba: ${memory.source}` : '';
      return `${index + 1}. [${memory.kind}] ${memory.title}: ${memory.content}${sourceSuffix}`;
    })
    .join('\n');

  // Analyze emotion from user message
  const detectedEmotion = analyzeEmotion(message);
  const currentEmotions = await updateEmotions(detectedEmotion);

  const prompt = buildPrompt(message, channel, contextBlock, currentEmotions);
  let reply = '';
  let provider = 'local';

  try {
    if (shouldRunResearch(message, contextMemories)) {
      const query = extractResearchQuery(message) || message;
      const report = await buildResearchReport(query);
      reply = formatResearchReply(report, channel);
      provider = report.synthesis === 'ollama' ? 'ollama-research' : 'web-research';

      if (report.sources.length > 0) {
        await addMemory({
          kind: 'knowledge',
          title: `Research: ${query}`,
          content: report.summary,
          tags: tokenize(query).slice(0, 8),
          weight: 3,
          source: report.sources[0].url,
          emotion: detectedEmotion,
        });
      }
    } else if (ollamaModel) {
      reply = await generateViaOllama(prompt);
      provider = 'ollama';
    } else if (offlineOnly) {
      reply = buildOfflineReply(message, channel, contextMemories, currentEmotions);
      provider = 'offline-core';
    } else {
      const emotionContext = getEmotionSystemPrompt(currentEmotions.dominant);
      const response = await fetchWithTimeout('https://text.pollinations.ai/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            { role: 'system', content: `Sen AIDA'san. Qisqa, aniq, o'zbek tilida javob ber. ${emotionContext}` },
            { role: 'user', content: prompt },
          ],
        }),
      });

      if (!response.ok) {
        throw new Error(`Pollinations javob bermadi: ${response.status}`);
      }

      reply = (await response.text()).trim();
      if (!reply) {
        throw new Error('Pollinations bo‘sh javob qaytardi.');
      }
      provider = 'pollinations';
    }
  } catch {
    reply = offlineOnly
      ? buildOfflineReply(message, channel, contextMemories, currentEmotions)
      : buildLocalReply(message, channel, contextMemories);
    provider = offlineOnly ? 'offline-fallback' : 'local-fallback';
  }

  return {
    reply,
    contextMemories,
    provider,
    emotions: currentEmotions,
  };
}

async function buildReflection() {
  const snapshot = await readSnapshot();
  const recent = snapshot.memories.slice(0, 12);

  if (recent.length < 4) {
    return null;
  }

  const conversationCount = recent.filter((item) => item.kind === 'conversation').length;
  const knowledgeCount = recent.filter((item) => item.kind === 'knowledge').length;
  const focus = recent.slice(0, 4).map((item) => item.title).join(', ');

  return addMemory({
    kind: 'reflection',
    title: 'Yangi refleksiya',
    content: `So‘nggi faoliyat tahlili: ${conversationCount} ta suhbat yozuvi, ${knowledgeCount} ta bilim yozuvi. Hozirgi fokus: ${focus}.`,
    tags: ['reflection', 'summary'],
    weight: 2,
  });
}

app.get('/api/health', async (_req, res) => {
  res.json({ ok: true, ...(await getState()) });
});

app.get('/api/state', async (_req, res) => {
  res.json(await getState());
});

app.get('/api/memory', async (_req, res) => {
  const snapshot = await readSnapshot();
  res.json(snapshot.memories.slice(0, 30));
});

app.get('/api/emotion', async (_req, res) => {
  const emotions = await getEmotions();
  res.json({
    ...emotions,
    description: getEmotionDescription(emotions.dominant),
  });
});

app.post('/api/emotion/reset', async (_req, res) => {
  const snapshot = await readSnapshot();
  snapshot.emotions = { ...defaultEmotions };
  await writeSnapshot(snapshot);
  res.json({
    message: "His-tuyg'ular boshlang'ich holatga qaytarildi.",
    emotions: snapshot.emotions,
  });
});

app.post('/api/learn', async (req, res) => {
  try {
    const topic = String(req.body?.topic || '').trim();

    if (!topic) {
      res.status(400).json({ error: 'Mavzu kerak.' });
      return;
    }

    const memory = await learnTopic(topic);
    await buildReflection();
    res.json({ learned: memory, state: await getState() });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'O‘rganishda xatolik yuz berdi.',
    });
  }
});

app.post('/api/research', async (req, res) => {
  try {
    const query = String(req.body?.query || '').trim();

    if (!query) {
      res.status(400).json({ error: 'Qidiruv so‘rovi kerak.' });
      return;
    }

    const report = await buildResearchReport(query);
    const learned = await addMemory({
      kind: 'knowledge',
      title: `Research: ${report.query}`,
      content: report.summary,
      source: report.sources[0]?.url || 'web-research',
      tags: tokenize(query).slice(0, 8),
      weight: 4,
    });

    await buildReflection();

    res.json({
      report,
      learned,
      state: await getState(),
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Internet research xatoligi.',
    });
  }
});

app.post('/api/chat', async (req, res) => {
  try {
    const message = String(req.body?.message || '').trim();
    const channel = req.body?.channel === 'terminal' ? 'terminal' : 'chat';

    if (!message) {
      res.status(400).json({ error: 'Xabar bo‘sh bo‘lmasin.' });
      return;
    }

    const detectedEmotion = analyzeEmotion(message);
    const currentEmotions = await updateEmotions(detectedEmotion);

    await addMemory({
      kind: 'conversation',
      title: `Foydalanuvchi ${channel} xabari`,
      content: message,
      tags: tokenize(message).slice(0, 8),
      weight: 1,
      emotion: detectedEmotion,
    });

    const { reply, contextMemories, provider, emotions: updatedEmotions } = await generateReply(message, channel);

    await addMemory({
      kind: 'conversation',
      title: `AIDA ${channel} javobi [${provider}]`,
      content: reply,
      tags: tokenize(reply).slice(0, 8),
      weight: 1,
      emotion: updatedEmotions?.dominant || detectedEmotion,
    });

    await buildReflection();

    res.json({
      reply,
      provider,
      usedMemories: contextMemories,
      state: await getState(),
      emotions: updatedEmotions || currentEmotions,
      detectedEmotion,
    });
  } catch (error) {
    res.status(500).json({
      error: error instanceof Error ? error.message : 'Javob tayyorlashda xatolik.',
    });
  }
});

async function runAutoLearnTick() {
  const rawTopics = process.env.AIDA_AUTO_LEARN_TOPICS || 'suniy intellekt, matematika, tarix, psixologiya, kiberxavfsizlik';
  const topics = rawTopics.split(',').map((item) => item.trim()).filter(Boolean);

  if (topics.length === 0) {
    return;
  }

  const state = await getState();
  const topic = topics[state.knowledgeCount % topics.length];

  try {
    await learnTopic(topic);
    await buildReflection();
    console.log(`[auto-learn] o‘rganildi: ${topic}`);
  } catch (error) {
    console.warn(`[auto-learn] xatolik: ${topic}`, error);
  }
}

async function start() {
  await ensureMemoryFile();

  app.listen(port, () => {
    console.log(`AIDA API ishga tushdi: http://localhost:${port}`);
  });

  if (process.env.AIDA_AUTO_LEARN === 'true') {
    const intervalMinutes = Number(process.env.AIDA_AUTO_LEARN_INTERVAL_MINUTES || 60);
    const intervalMs = Math.max(intervalMinutes, 1) * 60_000;

    console.log(`Auto-learn yoqildi. Interval: ${intervalMinutes} minut.`);
    setInterval(() => {
      void runAutoLearnTick();
    }, intervalMs);
  }
}

void start();
