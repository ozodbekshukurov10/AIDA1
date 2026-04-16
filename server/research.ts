export type FetchWithTimeout = (
  url: string,
  init?: RequestInit,
  timeoutMs?: number,
) => Promise<Response>;

export type ResearchSource = {
  title: string;
  url: string;
  snippet: string;
  content: string;
  provider: 'duckduckgo' | 'wikipedia' | 'webpage';
};

export type ResearchReport = {
  query: string;
  summary: string;
  sources: ResearchSource[];
  synthesis: 'extractive' | 'ollama';
};

type ResearchOptions = {
  maxSources?: number;
  pageFetchCount?: number;
  synthesize?: (prompt: string) => Promise<string>;
};

const STOPWORDS = new Set([
  'agar', 'ammo', 'bilan', 'biroq', 'bolib', 'bo‘lib', 'boshqa', 'bu', 'da', 'dan', 'deb',
  'edi', 'ekan', 'eng', 'esa', 'ham', 'haqida', 'hozir', 'uchun', 'uning', 'ular', 'yoki',
  'yuzasidan', 'kim', 'nima', 'qanday', 'qachon', 'qayerda', 'what', 'when', 'where', 'who',
  'why', 'how', 'the', 'and', 'for', 'with', 'that', 'this', 'from', 'are', 'was', 'were',
  'have', 'has', 'had', 'you', 'your', 'into', 'about', 'than', 'then', 'they', 'their',
]);

function decodeHtml(input: string) {
  return input
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&#x27;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&nbsp;/g, ' ')
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)));
}

function stripHtml(input: string) {
  return decodeHtml(
    input
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<noscript[\s\S]*?<\/noscript>/gi, ' ')
      .replace(/<svg[\s\S]*?<\/svg>/gi, ' ')
      .replace(/<[^>]+>/g, ' '),
  )
    .replace(/\s+/g, ' ')
    .trim();
}

function cleanText(input: string, maxLength = 900) {
  const compact = input.replace(/\s+/g, ' ').trim();
  if (compact.length <= maxLength) {
    return compact;
  }
  return `${compact.slice(0, maxLength - 3).trim()}...`;
}

function tokenize(input: string) {
  return input
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .split(/\s+/)
    .filter((token) => token.length > 2 && !STOPWORDS.has(token));
}

function normalizeForCompare(input: string) {
  return input
    .toLowerCase()
    .replace(/[ʻʼ'‘’`´]/g, '')
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizeTitleForDedupe(input: string) {
  return normalizeForCompare(input).replace(/\b(vikipediya|wikipedia)\b/g, '').replace(/\s+/g, ' ').trim();
}

function splitSentences(input: string) {
  return input
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter((sentence) => sentence.length > 40);
}

function isWikipediaUrl(url: string) {
  return /:\/\/([a-z]+\.)?wikipedia\.org\/wiki\//i.test(url);
}

function dedupeByUrl(sources: ResearchSource[]) {
  const seen = new Set<string>();
  const seenTitles = new Set<string>();
  return sources.filter((source) => {
    const key = source.url.toLowerCase();
    const titleKey = normalizeTitleForDedupe(source.title);
    if (seen.has(key) || (titleKey && seenTitles.has(titleKey))) {
      return false;
    }
    seen.add(key);
    if (titleKey) {
      seenTitles.add(titleKey);
    }
    return true;
  });
}

function sourceRelevanceScore(query: string, source: ResearchSource) {
  const queryTokens = tokenize(query);
  const normalizedQuery = normalizeForCompare(query);
  const normalizedTitle = normalizeForCompare(source.title);
  const titleTokens = tokenize(source.title);
  const content = `${source.title} ${source.snippet} ${source.content}`.toLowerCase();
  const overlap = queryTokens.reduce((sum, token) => sum + (content.includes(token) ? 1 : 0), 0);
  const titleOverlap = queryTokens.reduce((sum, token) => sum + (normalizedTitle.includes(token) ? 1 : 0), 0);
  const exact = normalizedTitle === normalizedQuery ? 8 : 0;
  const phraseBoost = normalizedTitle.includes(normalizedQuery) ? 4 : 0;
  const conciseTitleBoost = titleTokens.length <= queryTokens.length + 2 ? 1 : 0;
  const parenthesesPenalty = /[()]/.test(source.title) ? 2 : 0;
  const wikipediaSubtopicPenalty = source.provider === 'wikipedia'
    && normalizedTitle !== normalizedQuery
    && normalizedTitle.includes(normalizedQuery)
    ? 4
    : 0;
  return exact + phraseBoost + overlap + titleOverlap * 1.5 + conciseTitleBoost - parenthesesPenalty - wikipediaSubtopicPenalty;
}

function unwrapDuckDuckGoUrl(rawUrl: string) {
  const absolute = rawUrl.startsWith('//')
    ? `https:${rawUrl}`
    : rawUrl.startsWith('/')
      ? `https://duckduckgo.com${rawUrl}`
      : rawUrl;

  try {
    const parsed = new URL(absolute);
    const target = parsed.searchParams.get('uddg');
    return target ? decodeURIComponent(target) : absolute;
  } catch {
    return absolute;
  }
}

function sentenceScore(sentence: string, queryTokens: string, queryTokenList: string[], rankBoost: number) {
  const lowered = sentence.toLowerCase();
  const overlap = queryTokenList.reduce(
    (sum, token) => sum + (lowered.includes(token) ? 1 : 0),
    0,
  );
  const density = Math.min(sentence.length / 180, 1);
  const directPhrase = lowered.includes(queryTokens) ? 2 : 0;
  return overlap * 2 + density + directPhrase + rankBoost;
}

function rankSentences(query: string, sources: ResearchSource[], limit: number) {
  const queryTokenList = tokenize(query);
  const queryTokens = queryTokenList.join(' ');
  const scored: Array<{ sentence: string; score: number }> = [];

  sources.forEach((source, index) => {
    const rankBoost = Math.max(0, 1.5 - index * 0.2);
    splitSentences(source.content || source.snippet).forEach((sentence) => {
      scored.push({
        sentence: cleanText(sentence, 240),
        score: sentenceScore(sentence, queryTokens, queryTokenList, rankBoost),
      });
    });
  });

  const seen = new Set<string>();
  return scored
    .sort((a, b) => b.score - a.score)
    .filter((item) => {
      const key = item.sentence.toLowerCase();
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    })
    .slice(0, limit)
    .map((item) => item.sentence);
}

function buildExtractiveSummary(query: string, sources: ResearchSource[]) {
  const topSentences = rankSentences(query, sources, 3);
  const highlights = sources
    .slice(0, 3)
    .map((source, index) => {
      const bestSentence = rankSentences(query, [source], 1)[0] || source.snippet || source.content;
      return `- [${index + 1}] ${source.title}: ${cleanText(bestSentence, 180)}`;
    });
  const sourceLines = sources
    .slice(0, 4)
    .map((source, index) => `${index + 1}. ${source.title} — ${source.url}`);

  return [
    'Qisqa xulosa:',
    topSentences.join(' ') || 'Mos internet manbadan qisqa xulosa tuzib bo‘lmadi.',
    '',
    'Asosiy topilmalar:',
    ...highlights,
    '',
    'Manbalar:',
    ...sourceLines,
  ].join('\n');
}

function buildSynthesisPrompt(query: string, sources: ResearchSource[], extractiveSummary: string) {
  const compactSources = sources
    .slice(0, 5)
    .map((source, index) => [
      `[${index + 1}] ${source.title}`,
      `URL: ${source.url}`,
      `Snippet: ${cleanText(source.snippet || source.content, 220)}`,
      `Content: ${cleanText(source.content, 700)}`,
    ].join('\n'))
    .join('\n\n');

  return [
    "Sen AIDA research yadro'san.",
    "O'zbek tilida aniq, xolis va ixcham javob ber.",
    "Faqat berilgan manbalarga tayangan holda umumlashtir.",
    "Taxmin va faktni aralashtirma.",
    "Javob oxirida 2-4 ta manbani [1], [2] ko'rinishida eslat.",
    '',
    `So'rov: ${query}`,
    '',
    'Avvalgi extractive xulosa:',
    extractiveSummary,
    '',
    'Manba materiali:',
    compactSources,
  ].join('\n');
}

async function searchWikipedia(query: string, fetchWithTimeout: FetchWithTimeout) {
  return [
    ...(await searchWikipediaSite('uz', query, fetchWithTimeout)),
    ...(await searchWikipediaSite('en', query, fetchWithTimeout)),
  ]
    .filter((source, index, list) => list.findIndex((item) => item.url === source.url) === index)
    .slice(0, 4);
}

async function searchWikipediaSite(
  language: 'uz' | 'en',
  query: string,
  fetchWithTimeout: FetchWithTimeout,
) {
  const url = `https://${language}.wikipedia.org/w/api.php?action=opensearch&search=${encodeURIComponent(query)}&limit=4&namespace=0&format=json`;
  const response = await fetchWithTimeout(url, {
    headers: {
      'user-agent': 'AIDA-AgentOS/1.0',
      accept: 'application/json',
    },
  });

  if (!response.ok) {
    return [] as ResearchSource[];
  }

  const data = await response.json() as [string, string[], string[], string[]];
  const titles = Array.isArray(data[1]) ? data[1] : [];

  const summaries = await Promise.all(
    titles.map(async (title) => {
      const summaryUrl = `https://${language}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title.replace(/\s+/g, '_'))}`;
      try {
        const summaryResponse = await fetchWithTimeout(summaryUrl, {
          headers: {
            'user-agent': 'AIDA-AgentOS/1.0',
            accept: 'application/json',
          },
        }, 12_000);

        if (!summaryResponse.ok) {
          return null;
        }

        const summary = await summaryResponse.json() as {
          title?: string;
          extract?: string;
          content_urls?: {
            desktop?: { page?: string };
          };
        };

        if (!summary.extract || !summary.content_urls?.desktop?.page) {
          return null;
        }

        return {
          title: summary.title || title,
          url: summary.content_urls.desktop.page,
          snippet: cleanText(summary.extract, 220),
          content: cleanText(summary.extract, 900),
          provider: 'wikipedia' as const,
        };
      } catch {
        return null;
      }
    }),
  );

  return summaries.filter(Boolean) as ResearchSource[];
}

async function fetchWikipediaSummaryByUrl(url: string, fetchWithTimeout: FetchWithTimeout) {
  try {
    const parsed = new URL(url);
    const title = parsed.pathname.split('/wiki/')[1];

    if (!title) {
      return null;
    }

    const summaryUrl = `${parsed.protocol}//${parsed.host}/api/rest_v1/page/summary/${title}`;
    const response = await fetchWithTimeout(summaryUrl, {
      headers: {
        'user-agent': 'AIDA-AgentOS/1.0',
        accept: 'application/json',
      },
    }, 12_000);

    if (!response.ok) {
      return null;
    }

    const data = await response.json() as { extract?: string };
    return data.extract ? cleanText(data.extract, 900) : null;
  } catch {
    return null;
  }
}

async function searchDuckDuckGo(query: string, fetchWithTimeout: FetchWithTimeout) {
  const url = `https://duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
  const response = await fetchWithTimeout(url, {
    headers: {
      'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
      accept: 'text/html,application/xhtml+xml',
    },
  }, 15_000);

  if (!response.ok) {
    return [] as ResearchSource[];
  }

  const html = await response.text();
  const results: ResearchSource[] = [];
  const linkRegex = /class="result__a" href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/g;
  let match: RegExpExecArray | null;

  while ((match = linkRegex.exec(html)) !== null && results.length < 5) {
    const rawUrl = match[1];
    const title = cleanText(stripHtml(match[2]), 120);
    const localSlice = html.slice(match.index, match.index + 2500);
    const snippetMatch = localSlice.match(/class="result__snippet"[^>]*>([\s\S]*?)<\/a>/);
    const snippet = cleanText(stripHtml(snippetMatch?.[1] || ''), 220);
    const urlValue = unwrapDuckDuckGoUrl(rawUrl);

    if (!title || !urlValue.startsWith('http')) {
      continue;
    }

    results.push({
      title,
      url: urlValue,
      snippet,
      content: snippet,
      provider: isWikipediaUrl(urlValue) ? 'wikipedia' : 'duckduckgo',
    });
  }

  return results;
}

async function fetchWebPageContent(url: string, fetchWithTimeout: FetchWithTimeout) {
  try {
    const response = await fetchWithTimeout(url, {
      headers: {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        accept: 'text/html,application/xhtml+xml,text/plain',
      },
    }, 12_000);

    if (!response.ok) {
      return null;
    }

    const contentType = response.headers.get('content-type') || '';
    if (!/text\/html|text\/plain|application\/xhtml\+xml/i.test(contentType)) {
      return null;
    }

    const raw = await response.text();
    const metaDescription = raw.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)["']/i)?.[1];
    const text = cleanText(stripHtml(raw), 2400);
    const combined = [metaDescription ? cleanText(metaDescription, 220) : '', text]
      .filter(Boolean)
      .join(' ');

    return combined || null;
  } catch {
    return null;
  }
}

export async function researchTopic(
  query: string,
  fetchWithTimeout: FetchWithTimeout,
  options: ResearchOptions = {},
): Promise<ResearchReport> {
  const maxSources = options.maxSources ?? 5;
  const pageFetchCount = options.pageFetchCount ?? 2;

  const [wikipediaSources, duckSources] = await Promise.all([
    searchWikipedia(query, fetchWithTimeout),
    searchDuckDuckGo(query, fetchWithTimeout),
  ]);

  const normalizedQuery = normalizeForCompare(query);
  const deduped = dedupeByUrl([...wikipediaSources, ...duckSources]);
  const hasExactPrimary = deduped.some(
    (source) => normalizeTitleForDedupe(source.title) === normalizedQuery,
  );
  const focused = hasExactPrimary
    ? deduped.filter((source) => {
      const titleKey = normalizeTitleForDedupe(source.title);
      if (source.provider !== 'wikipedia') {
        return true;
      }
      return titleKey === normalizedQuery || !titleKey.includes(normalizedQuery);
    })
    : deduped;

  const merged = focused
    .sort((a, b) => sourceRelevanceScore(query, b) - sourceRelevanceScore(query, a))
    .slice(0, maxSources);

  const enriched = await Promise.all(
    merged.map(async (source, index) => {
      if (source.provider === 'wikipedia' || isWikipediaUrl(source.url)) {
        const summary = await fetchWikipediaSummaryByUrl(source.url, fetchWithTimeout);
        if (!summary) {
          return {
            ...source,
            provider: 'wikipedia' as const,
          };
        }

        return {
          ...source,
          content: summary,
          snippet: cleanText(source.snippet || summary, 220),
          provider: 'wikipedia' as const,
        };
      }

      if (index >= pageFetchCount) {
        return source;
      }

      const pageContent = await fetchWebPageContent(source.url, fetchWithTimeout);
      if (!pageContent) {
        return source;
      }

      return {
        ...source,
        content: cleanText(pageContent, 1200),
        provider: 'webpage' as const,
      };
    }),
  );

  const usableSources = enriched.filter((source) => source.content || source.snippet);
  const extractiveSummary = buildExtractiveSummary(query, usableSources);

  if (options.synthesize && usableSources.length > 0) {
    try {
      const summary = await options.synthesize(
        buildSynthesisPrompt(query, usableSources, extractiveSummary),
      );

      if (summary.trim()) {
        return {
          query,
          summary: summary.trim(),
          sources: usableSources,
          synthesis: 'ollama',
        };
      }
    } catch {
      // Fall back to extractive summary.
    }
  }

  return {
    query,
    summary: extractiveSummary,
    sources: usableSources,
    synthesis: 'extractive',
  };
}
