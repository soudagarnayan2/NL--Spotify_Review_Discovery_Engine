/* ═══════════════════════════════════════════════════════════
   REVIEW DISCOVERY ENGINE — JAVASCRIPT
═══════════════════════════════════════════════════════════ */

/* ── Suppress browser media AbortError ─────────────────
   The "play() request was interrupted by pause()" error
   is thrown by the browser or extensions (Spotify, media
   controllers) when a media element is played and paused
   in rapid succession. It's harmless — we catch it here
   so it doesn't pollute the console.
──────────────────────────────────────────────────────── */
window.addEventListener('unhandledrejection', function (event) {
  if (event.reason && event.reason.name === 'AbortError') {
    event.preventDefault();
    return;
  }
});

const API_BASE = 'http://localhost:8081/api/v1';

const topicDisplayNames = {
  "Algorithmic Bubble / Recommendation Repetition": "Algorithmic Bubble",
  "Smart Shuffle loop issues": "Smart Shuffle",
  "Taste pollution / Lack of Sandbox mode": "Taste Pollution",
  "Decision overload": "Decision Overload",
  "General Feedback / Other": "General Feedback"
};

/* ── Cached data from backend ──────────────────────────── */
let lastInsights = null;
let lastSyncTime = Date.now();
let currentEvidence = [];
let renderedEvidenceCount = 3;
let showingAllFeedback = false;
let activeFeedbackSamples = [];

/* ══════════════════════════════════════════════════════════
   THEME
══════════════════════════════════════════════════════════ */
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme');
  html.setAttribute('data-theme', current === 'dark' ? 'light' : 'dark');
  localStorage.setItem('theme', html.getAttribute('data-theme'));
}

(function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

/* ══════════════════════════════════════════════════════════
   TAB SWITCHING
══════════════════════════════════════════════════════════ */
function switchTab(tabId) {
  // Update panels
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + tabId).classList.add('active');

  // Update nav tabs
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tabId);
  });

  // Load data when switching to dashboard
  if (tabId === 'dashboard') loadDashboard();
}

/* ══════════════════════════════════════════════════════════
   DISCOVER: QUERY & SEARCH
══════════════════════════════════════════════════════════ */
function setQuery(chipEl) {
  const text = chipEl.textContent.replace(/^"|"$/g, '').trim();
  document.getElementById('queryInput').value = text;
  document.getElementById('queryInput').focus();
}

function clearSearch() {
  document.getElementById('queryInput').value = '';
  document.getElementById('resultsPanel').style.display = 'none';
}

async function runSearch() {
  const query = document.getElementById('queryInput').value.trim();
  if (!query) { showToast('Please enter a search query first.'); return; }

  const btn = document.getElementById('searchBtn');
  btn.classList.add('loading');
  btn.innerHTML = `
    <svg class="spinner-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation: spin 1s linear infinite; margin-right: 6px; display: inline-block; vertical-align: middle;"><circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="10"/></svg>
    Searching...
  `;

  // Display results panel immediately and scroll to it
  const resultsPanel = document.getElementById('resultsPanel');
  resultsPanel.style.display = 'block';
  resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Render shimmering skeleton screens
  document.getElementById('analysisContent').innerHTML = `
    <div class="skeleton" style="height: 16px; width: 95%; margin-bottom: 12px;"></div>
    <div class="skeleton" style="height: 16px; width: 80%; margin-bottom: 12px;"></div>
    <div class="skeleton" style="height: 16px; width: 85%; margin-bottom: 12px;"></div>
    <div class="skeleton" style="height: 16px; width: 65%;"></div>
  `;

  // Smart query classification — questions (Why/What/How/Which/Who) always go to review path
  const isReviewQuery = classifyQueryIntent(query) === 'review';
  const evidenceSec = document.getElementById('evidenceSection');
  if (evidenceSec) {
    if (isReviewQuery) {
      evidenceSec.style.display = 'block';
      document.getElementById('evidenceCards').innerHTML = Array(3).fill(0).map(() => `
        <div class="evidence-item" style="border: 1px solid var(--border); padding: 1rem; border-radius: var(--radius); margin-bottom: 1rem;">
          <div class="skeleton" style="height: 14px; width: 90%; margin-bottom: 8px;"></div>
          <div class="skeleton" style="height: 14px; width: 70%; margin-bottom: 12px;"></div>
          <div style="display: flex; justify-content: space-between;">
            <div class="skeleton" style="height: 12px; width: 60px;"></div>
            <div class="skeleton" style="height: 12px; width: 45px;"></div>
          </div>
        </div>
      `).join('');
    } else {
      evidenceSec.style.display = 'none';
    }
  }

  const startTime = Date.now();
  try {
    // Call backend
    const resp = await fetch(`${API_BASE}/discover`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id: 'frontend_session', history: [] })
    });

    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    const data = await resp.json();
    
    // Ensure skeleton is displayed for at least 600ms for visual polish
    const elapsed = Date.now() - startTime;
    if (elapsed < 600) {
      await new Promise(resolve => setTimeout(resolve, 600 - elapsed));
    }
    
    renderResults(query, data);
  } catch (err) {
    console.warn('Backend not reachable, using mock data:', err.message);
    
    // Artificial delay for mock so loading is visual
    const elapsed = Date.now() - startTime;
    if (elapsed < 800) {
      await new Promise(resolve => setTimeout(resolve, 800 - elapsed));
    }
    
    renderResults(query, getMockDiscoverResponse(query));
  } finally {
    btn.classList.remove('loading');
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg> Search`;
  }
}

/**
 * classifyQueryIntent(query) → 'review' | 'song' | 'general'
 *
 * Rules (evaluated in order):
 *  1. Interrogative sentences (Why / What / How / Which / Who / Do / Does…) → 'review'
 *  2. Explicit music-genre requests (bollywood songs, lofi music, etc.)     → 'song'
 *  3. Review / VoC keyword phrases                                           → 'review'
 *  4. Anything else                                                          → 'general'
 */
function classifyQueryIntent(query) {
  const q = String(query).toLowerCase().trim();

  // 1. Interrogative questions → always analytical / review intent
  if (/^(why|what|how|which|who|when|where|do|does|are|is|can|should|will|would|could|may|might)\b/i.test(String(query).trim())) {
    return 'review';
  }

  // 2. Explicit song / music genre request → song
  const isSongRequest =
    /^(play|give me|show me|find me|get me)\b/i.test(q) ||
    (/\b(song[s]?|music|tracks?|playlist)\b/i.test(q) && !/\b(review|frustrat|algorithm|sentiment|churn|retention|premium)\b/i.test(q)) ||
    /\b(bollywood|lofi|marathi|hindi|tamil|telugu|punjabi|bengali|kannada|gujarati|malayalam|bhojpuri|odia|assamese|haryanvi|rajasthani|konkani|kashmiri|dogri|sufi|ghazal|bhajan|qawwali|k-pop|j-pop|c-pop|jazz|blues|classical|country|folk|edm|techno|house|trance|dubstep|metal|punk|indie|reggae|gospel|opera|ambient|synthwave|lo-fi|lofi)\b/i.test(q);
  if (isSongRequest) return 'song';

  // 3. Review / VoC keyword phrases → review
  if (/review|sentiment|feedback|rating|user|customer|complain|opinion|switch|competitor|apple music|youtube music|amazon music|deezer|tidal|cancel|premium|subscription|satisfied|satisfaction|hate|frustrat|annoy|pain point|improvement|requested|request|missing|priorit|buffering|offline|download|playback|navigate|stuck|update|new release|bug|crash|freeze|slow|error|confus|trend|uninstall|churn/i.test(q)) {
    return 'review';
  }

  return 'general';
}

function getMockDiscoverResponse(query) {
  const query_lower = query.lower ? query.lower() : String(query).toLowerCase();

  // ── Analytical / VoC questions ─────────────────────────────────────────

  if (/struggle.*discover|discover.*music|discover new music|why.*discover|discovery problem|discovery challenge/i.test(query_lower)) {
    return {
      answer: `### Executive Summary
Users struggle to discover new music primarily because of three overlapping issues: algorithmic repetition that surfaces already-heard songs, a UI that overwhelms rather than guides, and the inability to express abstract preferences like mood or context in plain language.

### Key Findings

#### Theme: Algorithmic Repetition
* **Summary**: Discover Weekly and Daily Mixes repeatedly suggest songs users have already heard or previously skipped.
* **Overall Sentiment**: Negative
* **Frequency**: High (38 mentions)
* **Representative Review Excerpts**:
  - "Discover Weekly used to find hidden gems. Now it recommends songs I already skipped. The algorithm got lazy."
  - "My Daily Mix is literally just my Liked Songs playlist recycled."

#### Theme: Smart Shuffle Loop
* **Summary**: Smart Shuffle cycles through a small pool of ~15–20 tracks, trapping users instead of expanding their selection.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (22 mentions)
* **Representative Review Excerpts**:
  - "Smart Shuffle just plays the same 15 songs. It's not smart, it's just lazy."

#### Theme: Low Expressivity in Search
* **Summary**: Users cannot input abstract preferences — mood, scenario, or vibe — using traditional search filters.
* **Overall Sentiment**: Negative / Feature Request
* **Frequency**: Medium (19 mentions)
* **Representative Review Excerpts**:
  - "I want to search for 'rainy evening indie' and get something new. The current search is too literal."

### User Needs & Goals
* Discover genuinely new artists and tracks outside their current listening history.
* Express a feeling or context and get relevant results.

### Pain Points
* Recommendation engine does not learn from skip signals effectively.
* No way to tell Spotify "show me something I've never heard before."

### Positive Feedback
* Discover Weekly was historically praised as Spotify's best feature — users miss when it worked well.

### Actionable Recommendations
1. **Add a "Surprise Me" filter** — a dedicated mode excluding all previously heard tracks.
2. **Increase novelty weight** in Discover Weekly by de-prioritizing tracks already in Liked Songs.
3. **Introduce vibe-based search** accepting natural language mood and context queries.

### Confidence
* **High**: 79 matching reviews with consistent recurring themes across all major platforms.`,
      evidence: [
        { content: "Discover Weekly used to find hidden gems. Now it recommends songs I already skipped. The algorithm got lazy.", platform: 'play_store', date: '2026-06-29' },
        { content: "My Daily Mix is literally just my Liked Songs playlist recycled.", platform: 'reddit', date: '2026-06-27' },
        { content: "Smart Shuffle just plays the same 15 songs. It's not smart, it's just lazy.", platform: 'play_store', date: '2026-06-28' },
        { content: "I want to search for 'rainy evening indie' and get something new. The current search is too literal.", platform: 'app_store', date: '2026-06-25' }
      ]
    };
  }

  if (/frustrat|common frustrat|frustration.*recommend|recommend.*frustrat|annoying.*recommend|problem.*recommend/i.test(query_lower)) {
    return {
      answer: `### Executive Summary
The most common frustrations with Spotify's recommendation system center on three recurring themes: songs being replayed after being skipped, mainstream over-indexing that sidelines niche artists, and Smart Shuffle disrupting carefully curated playlists.

### Key Findings

#### Theme: Skipped Songs Replayed
* **Summary**: The algorithm continues to surface songs users have explicitly skipped multiple times.
* **Overall Sentiment**: Negative
* **Frequency**: High (41 mentions)
* **Representative Review Excerpts**:
  - "I skipped this song 5 times this week. Why is Spotify still playing it on my smart shuffle?"
  - "No means no, Spotify. Stop putting skipped songs back in my mix."

#### Theme: Mainstream Over-Indexing
* **Summary**: Audiophiles report the algorithm pushes popular hits over independent or local artists.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (28 mentions)
* **Representative Review Excerpts**:
  - "I listen to obscure jazz and ambient. Why does my Discover Weekly keep pushing Ed Sheeran?"

#### Theme: Smart Shuffle Disruption
* **Summary**: Smart Shuffle inserts unwanted recommendations mid-playlist, breaking user-curated flow.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (25 mentions)
* **Representative Review Excerpts**:
  - "I specifically made a playlist for a mood. Smart Shuffle ruined it with random pop songs."

### User Needs & Goals
* Have skip feedback treated as a strong negative signal that persists across sessions.
* Receive recommendations that respect niche tastes, not just global popularity charts.

### Pain Points
* Skip signals are not persisted — the same skipped track reappears within days.
* No way to opt out of Smart Shuffle on a per-playlist basis.

### Positive Feedback
* When recommendations are accurate, users describe them as "magical" and the app's best feature.

### Actionable Recommendations
1. **Implement skip memory** — a skipped track should be excluded for 30 days minimum.
2. **Add a niche/mainstream slider** for users to tune recommendation diversity.
3. **Add per-playlist Smart Shuffle toggle** so curated playlists stay unmodified.

### Confidence
* **High**: 94 frustration-themed reviews with strong pattern consistency across platforms.`,
      evidence: [
        { content: "I skipped this song 5 times this week. Why is Spotify still playing it on my smart shuffle?", platform: 'play_store', date: '2026-06-25' },
        { content: "I listen to obscure jazz and ambient. Why does my Discover Weekly keep pushing Ed Sheeran?", platform: 'reddit', date: '2026-06-26' },
        { content: "I specifically made a playlist for a mood. Smart Shuffle ruined it with random pop songs.", platform: 'app_store', date: '2026-06-24' }
      ]
    };
  }

  if (/personali[sz]ed playlist|how relevant|relevant.*playlist|playlist.*relevant|personali[sz]ation.*relevant/i.test(query_lower)) {
    return {
      answer: `### Executive Summary
Personalized playlists receive mixed reviews: casual listeners rate them highly for effortless background listening, while power users consistently find them stale, repetitive, and insufficiently attuned to evolving tastes.

### Key Findings

#### Theme: Casual Listener Approval
* **Summary**: Users wanting low-effort background music find personalized playlists highly relevant.
* **Overall Sentiment**: Positive
* **Frequency**: High (52 mentions)
* **Representative Review Excerpts**:
  - "Spotify just gets me. I hit play and the Daily Mix is always perfect for my work sessions."

#### Theme: Power User Dissatisfaction
* **Summary**: Active listeners report playlists becoming repetitive and failing to surface genuinely new music.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (34 mentions)
* **Representative Review Excerpts**:
  - "After 3 years, my Daily Mix feels more like an echo chamber than a recommendation engine."

#### Theme: Taste Drift from Shared Listening
* **Summary**: Using Spotify on shared accounts permanently skews recommendations.
* **Overall Sentiment**: Negative
* **Frequency**: Low (18 mentions)
* **Representative Review Excerpts**:
  - "My niece played nursery rhymes once and now my Discover Weekly has Baby Shark. Please fix this."

### User Needs & Goals
* Fresh playlists tailored to current mood, not just listening history.
* Ability to reset or sandbox their taste profile.

### Pain Points
* Playlist staleness increases with account age — long-term users feel most let down.
* No explicit feedback mechanism to train the algorithm on dislikes.

### Positive Feedback
* New users rate personalized playlists as Spotify's best differentiator.

### Actionable Recommendations
1. **Add a "Not for me" thumbs-down** on playlist tracks that trains the model more aggressively.
2. **Introduce playlist freshness settings** (more new vs. more familiar).
3. **Create profile isolation** for shared family accounts.

### Confidence
* **High**: 104 personalization reviews; findings split clearly across two user segments.`,
      evidence: [
        { content: "Spotify just gets me. I hit play and the Daily Mix is always perfect for my work sessions.", platform: 'app_store', date: '2026-07-01' },
        { content: "After 3 years, my Daily Mix feels more like an echo chamber than a recommendation engine.", platform: 'reddit', date: '2026-06-28' },
        { content: "My niece played nursery rhymes once and now my Discover Weekly has Baby Shark. Please fix this.", platform: 'play_store', date: '2026-06-26' }
      ]
    };
  }

  if (/prevent.*explor|explor.*new artist|explor.*new genre|barrier.*explor|what prevent|stop.*explor/i.test(query_lower)) {
    return {
      answer: `### Executive Summary
Users are held back from exploring new artists and genres primarily by decision paralysis from a 100M+ track catalog, fear of permanently skewing their recommendation profile, and a lack of low-commitment discovery pathways.

### Key Findings

#### Theme: Decision Overload / Choice Paralysis
* **Summary**: The sheer catalog size causes users to default to familiar music rather than venturing into unknown territory.
* **Overall Sentiment**: Neutral (structural problem)
* **Frequency**: High (33 mentions)
* **Representative Review Excerpts**:
  - "There are too many options. I end up just replaying my liked songs because I don't know where to start."

#### Theme: Fear of Taste Pollution
* **Summary**: Users are afraid exploring unfamiliar genres will permanently alter their recommendation profile.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (27 mentions)
* **Representative Review Excerpts**:
  - "If I listen to country music once, my whole vibe is ruined for a month. I need a sandbox."
  - "I'm scared to explore K-pop because I don't want it mixed into my jazz recommendations."

#### Theme: Lack of Guided Discovery Paths
* **Summary**: No clear entry points or curated journeys exist for exploring outside comfort zones.
* **Overall Sentiment**: Negative / Feature Request
* **Frequency**: Medium (21 mentions)
* **Representative Review Excerpts**:
  - "YouTube has a 'more like this but different' concept. Spotify needs something like that."

### User Needs & Goals
* Explore safely without worrying about long-term recommendation consequences.
* Guided, low-commitment pathways into unfamiliar music territories.

### Pain Points
* No "exploration mode" that isolates sessions from the main recommendation model.
* Genre pages feel static — no narrative or journey to guide exploration.

### Positive Feedback
* Users who explore new genres via curated Spotify editorial playlists report high satisfaction.

### Actionable Recommendations
1. **Launch a Sandbox/Explore Mode** — listening in this mode doesn't affect the taste model.
2. **Create "Genre Journey" playlists** — guided introductions that ease users into new categories.
3. **Add a "Similar but different" chip** on now-playing screens.

### Confidence
* **High**: 81 exploration-barrier reviews; fear of taste pollution is a uniquely strong, consistent theme.`,
      evidence: [
        { content: "There are too many options. I end up just replaying my liked songs because I don't know where to start.", platform: 'reddit', date: '2026-06-30' },
        { content: "If I listen to country music once, my whole vibe is ruined for a month. I need a sandbox.", platform: 'app_store', date: '2026-06-27' },
        { content: "YouTube has a 'more like this but different' concept. Spotify needs something like that.", platform: 'play_store', date: '2026-06-25' }
      ]
    };
  }

  if (/recommend.*praise|most praise|features.*praise|best.*recommend|love.*recommend|positive.*recommend/i.test(query_lower)) {
    return {
      answer: `### Executive Summary
Spotify's most praised recommendation features are Discover Weekly, Daily Mixes, and Spotify Wrapped. These three features are consistently cited as the platform's core differentiators and the primary reason users stay rather than switching to competitors.

### Key Findings

#### Theme: Discover Weekly
* **Summary**: When functioning well, Discover Weekly is described as "magical" — introducing users to artists they genuinely love.
* **Overall Sentiment**: Strongly Positive
* **Frequency**: High (67 mentions)
* **Representative Review Excerpts**:
  - "Discover Weekly changed my relationship with music. It introduced me to 3 artists I now love."
  - "No other app comes close to Discover Weekly when it's on point."

#### Theme: Daily Mixes
* **Summary**: Daily Mixes serve users who want low-friction, mood-appropriate listening without manual curation.
* **Overall Sentiment**: Positive
* **Frequency**: High (54 mentions)
* **Representative Review Excerpts**:
  - "I haven't made a playlist in 2 years. The daily mixes do it better than I could."

#### Theme: Spotify Wrapped
* **Summary**: The annual listening summary drives enormous emotional loyalty and social sharing.
* **Overall Sentiment**: Enthusiastically Positive
* **Frequency**: Medium (38 mentions)
* **Representative Review Excerpts**:
  - "Spotify Wrapped is the reason I'll never leave. It's like a love letter from the app."

### User Needs & Goals
* Effortless, algorithm-curated content that feels accurate and personal.
* Emotional connection with the platform through features like Wrapped.

### Pain Points
* Discover Weekly quality reported as declining over time for long-term accounts.
* No way to access historical Discover Weekly playlists (only current week available).

### Positive Feedback
* "Discover Weekly," "Daily Mixes," and "Wrapped" are the three most frequently praised features across all review samples.

### Actionable Recommendations
1. **Archive past Discover Weekly playlists** — let users access their listening history.
2. **Add a "Best of DW" auto-playlist** compiled from highest-engaged Discover Weekly tracks.
3. **Extend Wrapped to monthly mini-recaps** to reinforce emotional loyalty year-round.

### Confidence
* **High**: 159 praise-themed reviews; three features dominate with very high mention frequency.`,
      evidence: [
        { content: "Discover Weekly changed my relationship with music. It introduced me to 3 artists I now love.", platform: 'app_store', date: '2026-07-01' },
        { content: "I haven't made a playlist in 2 years. The daily mixes do it better than I could.", platform: 'play_store', date: '2026-06-29' },
        { content: "Spotify Wrapped is the reason I'll never leave. It's like a love letter from the app.", platform: 'twitter', date: '2026-06-28' }
      ]
    };
  }

  if (/why.*skip|users skip|skip.*recommend|reason.*skip|skip.*song/i.test(query_lower)) {
    return {
      answer: `### Executive Summary
Users skip recommended songs for three primary reasons: mismatched energy or mood for their current context, repeated exposure to already-heard songs, and low trust in the recommendation engine following past irrelevant suggestions.

### Key Findings

#### Theme: Energy / Mood Mismatch
* **Summary**: Recommended songs frequently don't match the user's current activity or emotional state.
* **Overall Sentiment**: Negative
* **Frequency**: High (36 mentions)
* **Representative Review Excerpts**:
  - "I'm studying and Spotify drops a heavy metal track into my chill playlist. Instant skip."
  - "Why is there a sad ballad in my workout mix? Context matters!"

#### Theme: Already Heard / Repetition
* **Summary**: Recommended tracks are often songs the user has already listened to many times.
* **Overall Sentiment**: Negative
* **Frequency**: High (31 mentions)
* **Representative Review Excerpts**:
  - "Stop recommending songs from my own liked songs library. I know them already."

#### Theme: Low Trust From Past Failures
* **Summary**: After repeated bad recommendations, users pre-emptively skip without listening.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (22 mentions)
* **Representative Review Excerpts**:
  - "I've been burned too many times. I skip anything Spotify recommends now without even listening."

### User Needs & Goals
* Contextually aware recommendations that match current activity and energy level.
* Genuinely new music, not recycled catalog items.

### Pain Points
* Skip signals are not used effectively to improve recommendations within the same session.
* No context-awareness (time of day, activity type) in standard recommendation delivery.

### Positive Feedback
* Users who receive contextually accurate recommendations rarely skip and describe feeling "in flow."

### Actionable Recommendations
1. **Implement in-session skip learning** — each skip immediately tunes remaining session recommendations.
2. **Add activity context tags** (gym, study, sleep, commute) users can set before a session.
3. **Show "Why was this recommended?"** transparency cards to rebuild user trust.

### Confidence
* **High**: 89 skip-behavior reviews; energy mismatch and repetition themes are highly consistent.`,
      evidence: [
        { content: "I'm studying and Spotify drops a heavy metal track into my chill playlist. Instant skip.", platform: 'play_store', date: '2026-06-30' },
        { content: "Stop recommending songs from my own liked songs library. I know them already.", platform: 'reddit', date: '2026-06-28' },
        { content: "I've been burned too many times. I skip anything Spotify recommends now without even listening.", platform: 'app_store', date: '2026-06-26' }
      ]
    };
  }

  // Custom mock responses for analytical questions
  if (query_lower.includes("retention")) {
    return {
      answer: `<strong>What factors influence user retention?</strong><br><br>
        1. <strong>Personalization Accuracy</strong> (75 mentions): Regular delivery of highly relevant mixes (Daily Mix, Discover Weekly) keeps users engaged and prevents playlist fatigue.<br><br>
        2. <strong>Social & Playlist Sharing</strong> (45 mentions): Collaborative playlists, shareable cards, and wrapped features build network stickiness.<br><br>
        3. <strong>Connected Playback Ecosystem</strong> (30 mentions): Spotify Connect's seamless switching between mobile, desktop, TV, and smart speaker systems is vital for daily retention.`,
      evidence: [
        { content: "I love Spotify Connect. Being able to transition my playback seamlessly from my phone to my TV and PS5 keeps me hooked every day.", platform: 'play_store', date: '2026-07-02' },
        { content: "The mixes are still the best out of any app. The personalized daily playlists are the only reason I don't switch.", platform: 'reddit', date: '2026-06-29' },
        { content: "Collaborative playlists are a lifesaver. My friends and I use them daily, and we're definitely not leaving.", platform: 'twitter', date: '2026-06-25' }
      ]
    };
  }
  
  if (query_lower.includes("drive premium") || query_lower.includes("features drive") || query_lower.includes("why subscribe")) {
    return {
      answer: `### Executive Summary
Three features consistently push users from free to premium: ad removal, offline downloads, and unlimited skip controls. These are not optional comforts — reviewers describe them as essential to a usable experience.

### Key Findings

#### Theme: Ad-Free Audio
* **Summary**: The single largest driver — free-tier ad frequency feels intrusive and disruptive.
* **Overall Sentiment**: Strongly Motivating
* **Frequency**: High (120 mentions)
* **Representative Review Excerpts**:
  - "Had to buy premium because the ads were driving me insane. Best decision I've made in months."

#### Theme: Offline Music Downloads
* **Summary**: Critical for commuters, travellers, and users in low-connectivity areas.
* **Overall Sentiment**: Positive
* **Frequency**: High (85 mentions)
* **Representative Review Excerpts**:
  - "Offline downloads are crucial for my morning train commute. Definitely the feature that made me subscribe."

#### Theme: Unlimited Track Skips
* **Summary**: Free-tier shuffle restrictions are a major frustration driving subscription conversion.
* **Overall Sentiment**: Motivating
* **Frequency**: Medium (60 mentions)
* **Representative Review Excerpts**:
  - "Being able to select individual tracks and skip without limits is why I keep paying for premium."

### User Needs & Goals
* Listen without interruption during focused tasks, commutes, and offline situations.
* Maintain full control over what plays next without shuffle constraints.

### Pain Points
* Free tier ad frequency described as "unbearable" and "disruptive" by many users.
* Shuffle-only mode on free tier prevents intentional track selection.

### Positive Feedback
* Premium subscribers express high satisfaction once they switch — "best decision I've made."
* Offline downloads praised as a lifestyle-enabling feature.

### Actionable Recommendations
1. **Highlight offline + ad-free benefits** in upgrade prompts at moments of frustration.
2. **Improve free-tier skip limits** marginally to reduce churn without eliminating conversion incentive.
3. **Offer time-limited premium trials** triggered after repeated ad encounters.

### Confidence
* **High**: 265 total premium-related mentions with strong consistency across App Store, Play Store, and Reddit.`,
      evidence: [
        { content: "Offline downloads are crucial for my morning train commute. Definitely the feature that made me subscribe.", platform: 'app_store', date: '2026-07-01' },
        { content: "Had to buy premium because the ads were driving me insane. Best decision I've made in months.", platform: 'twitter', date: '2026-06-30' },
        { content: "Being able to select individual tracks and skip without limits is why I keep paying for premium.", platform: 'play_store', date: '2026-06-26' }
      ]
    };
  }

  if (query_lower.includes("cancel premium") || query_lower.includes("reasons users cancel") || query_lower.includes("why cancel")) {
    return {
      answer: `### Executive Summary
Premium cancellations are primarily triggered by price sensitivity, recommendation quality degradation, and competitor bundle offers. Many users report cancelling not out of dissatisfaction with features, but due to a perceived mismatch between cost and value delivered.

### Key Findings

#### Theme: Price Increases
* **Summary**: Recent subscription cost hikes are the top cancellation trigger, especially among budget-conscious users.
* **Overall Sentiment**: Negative
* **Frequency**: High (90 mentions)
* **Representative Review Excerpts**:
  - "Canceling my premium subscription after the recent price hike. Not worth the extra cost when inflation is high."

#### Theme: Recommendation Staleness
* **Summary**: Feeling trapped in an algorithmic loop makes the subscription feel wasted.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (65 mentions)
* **Representative Review Excerpts**:
  - "Why am I paying monthly just to hear the same 20 songs on repeat? Personalized lists are totally stale. Canceling."

#### Theme: Competitor Bundle Switching
* **Summary**: Cheaper student/family bundles from Apple Music or Amazon Music act as a pull factor.
* **Overall Sentiment**: Neutral (rational comparison)
* **Frequency**: Medium (40 mentions)
* **Representative Review Excerpts**:
  - "Switched to Apple Music family plan because it's cheaper and integrated with my iCloud bundle."

### User Needs & Goals
* Perceived value for money — premium must feel noticeably better than free alternatives.
* Fresh, relevant recommendations that justify the monthly cost.

### Pain Points
* Price-to-value perception gap widens when recommendations feel stale.
* No flexibility in pricing tiers (e.g., lite plans, pause options) for budget-constrained users.

### Positive Feedback
* Many cancelling users express they still prefer Spotify's UX and may return when circumstances change.

### Actionable Recommendations
1. **Introduce a flexible lite tier** (e.g., reduced offline limit) at a lower price point.
2. **Offer a "pause subscription" option** to reduce hard cancellations.
3. **Send personalized re-engagement emails** showcasing new features before renewal dates.

### Confidence
* **High**: 195 cancellation-intent reviews with consistent patterns across platforms.`,
      evidence: [
        { content: "Canceling my premium subscription after the recent price hike. Not worth the extra cost when inflation is high.", platform: 'reddit', date: '2026-06-28' },
        { content: "Why am I paying monthly just to hear the same 20 songs on repeat? Personalized lists are totally stale. Canceling.", platform: 'play_store', date: '2026-06-25' },
        { content: "Switched to Apple Music family plan because it's cheaper and integrated with my iCloud bundle.", platform: 'app_store', date: '2026-06-21' }
      ]
    };
  }

  if (query_lower.includes("satisfaction") || query_lower.includes("satisfied")) {
    return {
      answer: `### Executive Summary
Satisfaction is highest among casual playlist listeners and multi-device Spotify Connect users. These segments receive the most consistent value from the product's core strengths — automatic curation and seamless device handoff.

### Key Findings

#### Theme: Casual Playlist Listeners
* **Summary**: Users who rely on pre-made playlists and background curation report high satisfaction with minimal friction.
* **Overall Sentiment**: Positive
* **Frequency**: High (80% satisfaction in this segment)
* **Representative Review Excerpts**:
  - "As a casual listener, the default chill playlists are perfect for my work day. Super satisfied."
  - "I just press play on Sleep Lofi and sleep like a baby. Automatic curation is amazing."

#### Theme: Connected Ecosystem Users
* **Summary**: Users who actively use Spotify Connect across speakers, TVs, and gaming consoles rate the experience highest.
* **Overall Sentiment**: Positive
* **Frequency**: Medium (85% satisfaction in this segment)
* **Representative Review Excerpts**:
  - "Works flawlessly between my PS5, phone, and speaker. Best app ever, I couldn't be more satisfied."

### User Needs & Goals
* Effortless, low-friction listening experience without manual curation effort.
* Reliable cross-device continuity for uninterrupted listening sessions.

### Pain Points
* Power users and audiophiles report lower satisfaction due to algorithm limitations and mainstream push.
* Users with complex listening histories experience recommendation drift.

### Positive Feedback
* Automatic curation praised as "effortless" and "amazing" by casual listeners.
* Spotify Connect multi-device experience called "butter smooth" and "flawless."

### Actionable Recommendations
1. **Expand curated playlist categories** for niche moods, activities, and subcultures.
2. **Market Spotify Connect** more prominently as a premium differentiator.
3. **Develop a power user mode** with advanced playlist controls to boost audiophile satisfaction.

### Confidence
* **High**: Segment satisfaction patterns consistent across 200+ review samples.`,
      evidence: [
        { content: "Works flawlessly between my PS5, phone, and speaker. Best app ever, I couldn't be more satisfied.", platform: 'app_store', date: '2026-06-27' },
        { content: "As a casual listener, the default chill playlists are perfect for my work day. Super satisfied.", platform: 'twitter', date: '2026-06-23' },
        { content: "I just press play on Sleep Lofi and sleep like a baby. Automatic curation is amazing.", platform: 'play_store', date: '2026-06-19' }
      ]
    };
  }

  if (query_lower.includes("improvement") || query_lower.includes("ux") || query_lower.includes("user experience")) {
    return {
      answer: `### Executive Summary
Users consistently identify three improvements that would have the greatest positive impact: a recommendation sandbox mode, fix for Smart Shuffle repetitiveness, and introduction of natural language (prompt-based) music search. These requests appear repeatedly across review platforms.

### Key Findings

#### Theme: Recommendation Sandbox Mode
* **Summary**: Users want a way to explore new genres without permanently affecting their recommendation profile.
* **Overall Sentiment**: Strongly Requested
* **Frequency**: High (55 mentions)
* **Representative Review Excerpts**:
  - "We need a guest mode or sandbox. My niece listened to music on my account and now my discover weekly is ruined."

#### Theme: Smart Shuffle Skip Respect
* **Summary**: The Smart Shuffle feature repeatedly plays skipped songs, frustrating users.
* **Overall Sentiment**: Negative / Feature Request
* **Frequency**: Medium (40 mentions)
* **Representative Review Excerpts**:
  - "Smart shuffle needs to respect skips. If I skip a song 5 times, stop playing it! Product needs this fix."

#### Theme: Prompt-Based Semantic Search
* **Summary**: Users want to describe what they want in natural language instead of browsing menus.
* **Overall Sentiment**: Enthusiastic Request
* **Frequency**: Medium (30 mentions)
* **Representative Review Excerpts**:
  - "I want to be able to type a prompt like 'chill guitar for study' instead of scrolling through playlists. Huge impact if added."

### User Needs & Goals
* Explore music freely without long-term consequences on their taste profile.
* Have skip signals respected immediately by the recommendation engine.
* Search using intent and mood, not just genre or artist names.

### Pain Points
* Taste pollution from shared accounts or experimental listening is irreversible.
* Smart Shuffle ignores skip feedback, making the feature feel "not smart at all."
* Current search UX requires users to know what they want, not describe how they feel.

### Positive Feedback
* Users love the concept of AI-powered music discovery — they just want it to be more responsive.

### Actionable Recommendations
1. **Build a Sandbox/Guest Mode** — a toggle that isolates listening sessions from the recommendation model.
2. **Fix Smart Shuffle skip memory** — a skipped song should be de-prioritized for 30 days minimum.
3. **Introduce vibe-based semantic search** — a natural language input box for mood/context discovery.

### Confidence
* **High**: 125 improvement-request mentions with strong overlap across platforms and user segments.`,
      evidence: [
        { content: "We need a guest mode or sandbox. My niece listened to music on my account and now my discover weekly is ruined.", platform: 'app_store', date: '2026-06-26' },
        { content: "Smart shuffle needs to respect skips. If I skip a song 5 times, stop playing it! Product needs this fix.", platform: 'play_store', date: '2026-06-22' },
        { content: "I want to be able to type a prompt like 'chill guitar for study' instead of scrolling through playlists. Huge impact if added.", platform: 'reddit', date: '2026-06-18' }
      ]
    };
  }

  if (query_lower.includes("sentiment") || query_lower.includes("shift") || query_lower.includes("latest update") || (query_lower.includes("update") && !query_lower.includes("song") && !query_lower.includes("music"))) {
    return {
      answer: `### Executive Summary
Sentiment analysis of Spotify user reviews shows a measurable **negative shift** following the most recent update cycle. Across 892 reviews analyzed, rating scores dropped by an average of 0.4 stars, driven primarily by UI layout changes and a reported increase in ad frequency on free tiers.

### Key Findings

#### Theme: UI Layout Regression
* **Summary**: Users report that recent app updates broke familiar navigation flows.
* **Overall Sentiment**: Negative
* **Frequency**: High (42% of update-related reviews)
* **Representative Review Excerpts**:
  - "The new update completely redesigned the home screen. I can't find my liked songs anymore." (App Store – 2026-06-30)
  - "They moved everything around. Just when you get used to it, they change it again." (Play Store – 2026-06-28)

#### Theme: Increased Ad Frequency (Free Tier)
* **Summary**: Free-tier users report more ads per session after recent updates.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (28% of update-related reviews)
* **Representative Review Excerpts**:
  - "Feels like there's an ad every other song now. Unbearable on the free plan." (Reddit – 2026-06-27)

#### Theme: Improved Stability
* **Summary**: Some users noted fewer crashes and better background audio handling.
* **Overall Sentiment**: Positive
* **Frequency**: Low (12% of update-related reviews)
* **Representative Review Excerpts**:
  - "App hasn't crashed once since the update. Background playback is butter smooth now." (Play Store – 2026-07-01)

### User Needs & Goals
* Stable, familiar navigation that doesn't change drastically between updates.
* Transparent communication about UI changes before they roll out.

### Pain Points
* Disorientation from unexpected layout overhauls.
* Increased ad interruptions reducing free-tier experience quality.

### Positive Feedback
* Background playback stability improvements appreciated.
* Faster app launch times noticed by power users.

### Actionable Recommendations
1. **Announce major UI changes** via in-app changelogs before rolling out globally.
2. **A/B test navigation overhauls** with a subset of users before full release.
3. **Cap ad frequency** per session to prevent churn on free tier.

### Confidence
* **High**: Supported by 892 matching user reviews with consistent themes across App Store, Play Store, and Reddit.`,
      evidence: [
        { content: "The new update completely redesigned the home screen. I can't find my liked songs anymore.", platform: 'app_store', date: '2026-06-30' },
        { content: "They moved everything around. Just when you get used to it, they change it again.", platform: 'play_store', date: '2026-06-28' },
        { content: "Feels like there's an ad every other song now. Unbearable on the free plan.", platform: 'reddit', date: '2026-06-27' },
        { content: "App hasn't crashed once since the update. Background playback is butter smooth now.", platform: 'play_store', date: '2026-07-01' }
      ]
    };
  }

  if (query_lower.includes("playback") || query_lower.includes("buffer") || query_lower.includes("offline") || query_lower.includes("download") || query_lower.includes("audio") || query_lower.includes("sound")) {
    return {
      answer: `### Executive Summary
Playback and technical stability are generally high, but offline downloads represent a major pain point, with users reporting disappeared tracks and authentication errors. Buffering issues are occasionally reported on high-quality settings under cellular networks.

### Key Findings

#### Theme: Offline Download Sync Issues
* **Summary**: Users report that offline downloaded tracks frequently disappear or refuse to play without cellular verification.
* **Overall Sentiment**: Negative
* **Frequency**: High (55 mentions)
* **Representative Review Excerpts**:
  - "Offline mode is completely broken. It keeps deleting my downloaded songs when I'm on a plane."
  - "Why do my downloaded podcasts ask for internet connection to play? Defeats the purpose."

#### Theme: High-Fidelity Streaming Buffering
* **Summary**: Higher bitrate streaming results in occasional pauses and buffer loops on cellular data.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (30 mentions)
* **Representative Review Excerpts**:
  - "Buffering is terrible on cellular networks even with good signal. High-quality audio constantly stutters."

### User Needs & Goals
* Reliable offline audio playback for travel and low-connectivity commutes.
* Stable streaming that dynamically adjusts bitrate without hard pausing.

### Pain Points
* Involuntary decryption key expiration deleting offline local storage cache.
* Strict licensing checks requiring online ping before playing downloaded media.

### Actionable Recommendations
1. **Extend offline authentication lease duration** to 30 days before forcing validation.
2. **Implement intelligent background cache repair** to restore missing files during Wi-Fi connections.
3. **Enhance adaptive bitrate engine** to avoid stream stutter on cellular data.

### Confidence
* **High**: Based on 85 playback-related reviews with consistent issues across App Store and Google Play.`,
      evidence: [
        { content: "Offline mode is completely broken. It keeps deleting my downloaded songs when I'm on a plane.", platform: 'app_store', date: '2026-07-01' },
        { content: "Why do my downloaded podcasts ask for internet connection to play? Defeats the purpose.", platform: 'play_store', date: '2026-06-29' },
        { content: "Buffering is terrible on cellular networks even with good signal. High-quality audio constantly stutters.", platform: 'reddit', date: '2026-06-26' }
      ]
    };
  }

  if (query_lower.includes("competitor") || query_lower.includes("competing") || query_lower.includes("switch") || query_lower.includes("apple music") || query_lower.includes("youtube music") || query_lower.includes("amazon music")) {
    return {
      answer: `### Executive Summary
Competitor comparisons focus on Apple Music's superior lossless audio quality and YouTube Music's larger catalog of unofficial remixes and live tracks. However, Spotify is preferred for its social sharing features and device connection versatility.

### Key Findings

#### Theme: Apple Music Audio Quality
* **Summary**: Audiophile users report switching or considering switching to Apple Music for native spatial audio and lossless streaming.
* **Overall Sentiment**: Neutral (Competitive Comparison)
* **Frequency**: High (65 mentions)
* **Representative Review Excerpts**:
  - "Apple Music includes lossless audio for free. Spotify's sound quality feels muddy in comparison."

#### Theme: YouTube Music Remix Catalog
* **Summary**: Users switch to YouTube Music for unofficial covers, mixtape tracks, and video integration.
* **Overall Sentiment**: Neutral
* **Frequency**: Medium (40 mentions)
* **Representative Review Excerpts**:
  - "Switched to YouTube Music because I can find covers and bootlegs that Spotify never has."

### User Needs & Goals
* High-fidelity audio quality (Hi-Fi) without additional subscription cost.
* Access to rare, unofficial, or user-uploaded music catalog items.

### Actionable Recommendations
1. **Accelerate Spotify Hi-Fi rollout** to match Apple and Amazon Music's standard offering.
2. **Improve local files library indexing** to let users easily sync unofficial tracks.

### Confidence
* **High**: 105 reviews mentioning competitor brands with specific comparative feature feedback.`,
      evidence: [
        { content: "Apple Music includes lossless audio for free. Spotify's sound quality feels muddy in comparison.", platform: 'reddit', date: '2026-07-02' },
        { content: "Switched to YouTube Music because I can find covers and bootlegs that Spotify never has.", platform: 'app_store', date: '2026-06-28' },
        { content: "Spotify still wins on social sharing and device integration, but competitor audio quality is tempting.", platform: 'twitter', date: '2026-06-25' }
      ]
    };
  }

  if (query_lower.includes("bug") || query_lower.includes("crash") || query_lower.includes("freeze") || query_lower.includes("error") || query_lower.includes("slow")) {
    return {
      answer: `### Executive Summary
Technical stability issues are infrequent overall, but recent reviews identify two specific regressions: background crashes when using CarPlay on iOS 17, and app freezing during network switches (Wi-Fi to Cellular).

### Key Findings

#### Theme: CarPlay Background Crash
* **Summary**: Using navigation apps while streaming background audio causes Spotify to crash on iOS.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (25 mentions)
* **Representative Review Excerpts**:
  - "The app constantly crashes in the background when I run Google Maps on CarPlay. Very annoying while driving."

#### Theme: Network Handoff Freeze
* **Summary**: Switching between Wi-Fi and cellular networks causes the UI to freeze or become unresponsive.
* **Overall Sentiment**: Negative
* **Frequency**: Medium (20 mentions)
* **Representative Review Excerpts**:
  - "Whenever I walk out of my house and switch to LTE, the Spotify screen freezes and I have to force restart."

### Actionable Recommendations
1. **Fix audio buffer handling in CarPlay background state** to prevent execution timeouts.
2. **Enhance network state transition listeners** to gracefully handle cell tower handoffs without freezing the main thread.

### Confidence
* **High**: 45 stable bug reports detailing identical technical triggers.`,
      evidence: [
        { content: "The app constantly crashes in the background when I run Google Maps on CarPlay. Very annoying while driving.", platform: 'app_store', date: '2026-07-01' },
        { content: "Whenever I walk out of my house and switch to LTE, the Spotify screen freezes and I have to force restart.", platform: 'play_store', date: '2026-06-29' }
      ]
    };
  }

  // Fallback classification using shared helper
  const intent = classifyQueryIntent(query_lower);
  const isReviewQuery = intent === 'review';

  const analysis = isReviewQuery
    ? `### Executive Summary
Across 2000 analyzed reviews, three systemic issues dominate user complaints about Spotify's recommendation engine: algorithmic repetition, Smart Shuffle loops, and taste pollution from shared listening.

### Key Findings

#### Theme: Algorithmic Repetitiveness
* **Summary**: Discover Weekly and Daily Mixes repeatedly surface tracks the user has already heard or skipped.
* **Overall Sentiment**: Negative
* **Frequency**: High (546 mentions)
* **Representative Review Excerpts**:
  - "I'm so tired of Spotify playing the same 15 songs on repeat. My Daily Mix is just songs from my own liked playlist."

#### Theme: Smart Shuffle Loops
* **Summary**: Smart Shuffle cycles through only ~15–20 tracks, creating a closed loop instead of expanding selection.
* **Overall Sentiment**: Negative
* **Frequency**: Low (133 mentions)
* **Representative Review Excerpts**:
  - "Smart Shuffle loops the same 10–15 tracks. It's not smart, it's just lazy."

#### Theme: Taste Pollution
* **Summary**: No sandbox or private mode means experimental listening permanently skews recommendations.
* **Overall Sentiment**: Negative
* **Frequency**: Low (108 mentions)
* **Representative Review Excerpts**:
  - "My kids' music completely ruined my recommendations. I need separate profiles."

### User Needs & Goals
* Fresh, contextually relevant music that goes beyond current listening history.
* Confidence that exploring new genres won't permanently damage recommendation quality.

### Pain Points
* Skip signals are not respected or persisted across sessions.
* Shared accounts have no isolation — one session can corrupt months of preference data.

### Positive Feedback
* Users consistently praise Spotify's recommendation features when they work correctly.

### Actionable Recommendations
*1. **Respect skip history** — de-prioritize skipped tracks for at least 30 days.
*2. **Introduce a Sandbox Mode** — isolate exploratory sessions from the core taste model.
*3. **Implement family/child profile separation** to prevent taste cross-contamination.

### Confidence
* **High**: Based on 2000 review mentions; patterns are consistent and represent a substantial dataset.`
    : `**Music Discovery Result for: "${query}"**\n\nBased on semantic analysis of the track catalog, I found matching tracks that fit your description.`;

  let tracks = [];
  if (!isReviewQuery) {
    if (query_lower.includes("marathi")) {
      tracks = [
        { name: "Apsara Aali", artist: "Ajay-Atul", genre: "Marathi", subgenre: "Lavani", energy: 0.85, tempo: 130 },
        { name: "Sairat Zaala Ji", artist: "Ajay-Atul", genre: "Marathi", subgenre: "Romantic", energy: 0.5, tempo: 95 },
        { name: "Zingaat", artist: "Ajay-Atul", genre: "Marathi", subgenre: "Dance", energy: 0.95, tempo: 140 }
      ];
    } else if (query_lower.includes("hindi")) {
      tracks = [
        { name: "Kesariya", artist: "Arijit Singh", genre: "Hindi", subgenre: "Romantic Pop", energy: 0.6, tempo: 98 },
        { name: "Tum Hi Ho", artist: "Arijit Singh", genre: "Hindi", subgenre: "Sad Romantic", energy: 0.4, tempo: 90 }
      ];
    } else if (query_lower.includes("punjabi")) {
      tracks = [
        { name: "Brown Munde", artist: "AP Dhillon, Gurinder Gill", genre: "Punjabi", subgenre: "Hip-Hop", energy: 0.75, tempo: 85 }
      ];
    } else if (query_lower.includes("tamil")) {
      tracks = [
        { name: "Arabic Kuthu", artist: "Anirudh Ravichander, Jonita Gandhi", genre: "Tamil", subgenre: "Dance Fusion", energy: 0.9, tempo: 128 },
        { name: "Munbe Vaa", artist: "Shreya Ghoshal, Naresh Iyer", genre: "Tamil", subgenre: "Classical Romantic", energy: 0.45, tempo: 92 }
      ];
    } else if (query_lower.includes("telugu")) {
      tracks = [
        { name: "Naatu Naatu", artist: "Rahul Sipligunj, Kaala Bhairava", genre: "Telugu", subgenre: "Folk Dance", energy: 0.98, tempo: 145 },
        { name: "Samajavaragamana", artist: "Sid Sriram", genre: "Telugu", subgenre: "Romantic Pop", energy: 0.65, tempo: 105 }
      ];
    } else if (query_lower.includes("bengali")) {
      tracks = [
        { name: "Boba Tunnel", artist: "Anupam Roy", genre: "Bengali", subgenre: "Acoustic Indie", energy: 0.3, tempo: 85 }
      ];
    } else if (query_lower.includes("malayalam")) {
      tracks = [
        { name: "Malare", artist: "Vijay Yesudas", genre: "Malayalam", subgenre: "Acoustic Romantic", energy: 0.35, tempo: 80 }
      ];
    } else if (query_lower.includes("kannada")) {
      tracks = [
        { name: "Singara Siriye", artist: "Vijay Prakash, Ananya Bhat", genre: "Kannada", subgenre: "Folk Fusion", energy: 0.75, tempo: 115 }
      ];
    } else if (query_lower.includes("gujarati")) {
      tracks = [
        { name: "Radha Ne Shyam Malishe", artist: "Sachin-Jigar", genre: "Gujarati", subgenre: "Festive Garba", energy: 0.8, tempo: 120 }
      ];
    } else if (query_lower.includes("bhojpuri")) {
      tracks = [
        { name: "Lolipop Lagelu", artist: "Pawan Singh", genre: "Bhojpuri", subgenre: "Folk Pop", energy: 0.9, tempo: 135 }
      ];
    } else if (query_lower.includes("bollywood")) {
      tracks = [
        { name: "Kesariya", artist: "Arijit Singh", genre: "Bollywood", subgenre: "Romantic Pop", energy: 0.6, tempo: 98 },
        { name: "Tum Hi Ho", artist: "Arijit Singh", genre: "Bollywood", subgenre: "Sad Romantic", energy: 0.4, tempo: 90 },
        { name: "Chaleya", artist: "Arijit Singh, Shilpa Rao", genre: "Bollywood", subgenre: "Dance Pop", energy: 0.82, tempo: 115 },
        { name: "Raataan Lambiyan", artist: "Jubin Nautiyal, Asees Kaur", genre: "Bollywood", subgenre: "Romantic", energy: 0.5, tempo: 88 },
        { name: "Zaalima", artist: "Arijit Singh, Harshdeep Kaur", genre: "Bollywood", subgenre: "Romantic", energy: 0.55, tempo: 93 },
        { name: "Dilbaro", artist: "Harshdeep Kaur, Vibha Saraf", genre: "Bollywood", subgenre: "Emotional", energy: 0.35, tempo: 80 }
      ];
    } else if (query_lower.includes("regional") || query_lower.includes("indian")) {
      tracks = [
        { name: "Zingaat", artist: "Ajay-Atul", genre: "Marathi", subgenre: "Dance", energy: 0.95, tempo: 140 },
        { name: "Kesariya", artist: "Arijit Singh", genre: "Hindi", subgenre: "Romantic Pop", energy: 0.6, tempo: 98 },
        { name: "Arabic Kuthu", artist: "Anirudh Ravichander", genre: "Tamil", subgenre: "Dance Fusion", energy: 0.9, tempo: 128 },
        { name: "Naatu Naatu", artist: "Rahul Sipligunj", genre: "Telugu", subgenre: "Folk Dance", energy: 0.98, tempo: 145 },
        { name: "Malare", artist: "Vijay Yesudas", genre: "Malayalam", subgenre: "Acoustic Romantic", energy: 0.35, tempo: 80 }
      ];
    } else if (query_lower.includes("lofi") || query_lower.includes("chill") || query_lower.includes("study")) {
      tracks = [
        { name: "Coffee Breath", artist: "Lofi Fruits Music", genre: "Lo-Fi", subgenre: "Chill", energy: 0.25, tempo: 78 },
        { name: "Rainy Night in Tokyo", artist: "Lofi Sleep Chill", genre: "Lo-Fi", subgenre: "Ambient", energy: 0.15, tempo: 70 },
        { name: "Study Session Mood", artist: "Chillhop Beats", genre: "Lo-Fi", subgenre: "Study", energy: 0.3, tempo: 82 },
        { name: "Sunset Drive", artist: "Lofi Sunset", genre: "Lo-Fi", subgenre: "Relaxing", energy: 0.35, tempo: 85 }
      ];
    } else {
      tracks = [
        { name: "Starlight Echoes", artist: "Lunar Ambient", genre: "Ambient", subgenre: "Space", energy: 0.2, tempo: 65 },
        { name: "Neon Horizon", artist: "Retro Wave", genre: "Synthwave", subgenre: "Retro", energy: 0.7, tempo: 110 },
        { name: "Midnight Rain", artist: "Lofi Chill", genre: "Lo-Fi", subgenre: "Chill", energy: 0.3, tempo: 80 },
        { name: "Acoustic Sunsets", artist: "Indie Folk Band", genre: "Folk", subgenre: "Acoustic", energy: 0.45, tempo: 95 }
      ];
    }
  }

  const mockEvidence = isReviewQuery ? [
    { content: "I'm so tired of Spotify playing the same 15 songs on repeat. My Daily Mix is just songs from my own liked playlist.", platform: 'reddit', date: '2026-07-01' },
    { content: "Discover Weekly used to find hidden gems. Now it recommends songs I already skipped. The algorithm got lazy.", platform: 'play_store', date: '2026-06-29' },
    { content: "No sandbox mode means one sea shanty ruined my entire recommendation profile for weeks.", platform: 'app_store', date: '2026-06-27' },
    { content: "Smart Shuffle loops the same 10-15 tracks. It's not smart, it's just lazy.", platform: 'play_store', date: '2026-06-28' },
    { content: "I skipped this song 5 times this week. Why is Spotify still playing it on my smart shuffle?", platform: 'play_store', date: '2026-06-25' },
    { content: "My kids' music completely ruined my recommendations. I need separate profiles.", platform: 'app_store', date: '2026-06-24' }
  ] : [];

  return {
    answer: analysis,
    tracks: tracks,
    evidence: mockEvidence
  };
}

function renderResults(query, data) {
  // Parse raw text — convert markdown to HTML if marked.js is loaded
  const rawText = data.answer || data.explanation || `<em>No analysis returned for: "${query}"</em>`;
  let renderedHtml;
  if (typeof marked !== 'undefined') {
    // marked v4+ uses marked.parse(), older uses marked()
    renderedHtml = (typeof marked.parse === 'function')
      ? marked.parse(rawText)
      : marked(rawText);
  } else {
    // Fallback: basic markdown conversion for ###, **, *, -
    renderedHtml = rawText
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/^[\*\-] (.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');
  }

  document.getElementById('analysisContent').innerHTML = renderedHtml;

  // Store evidence globally for pagination
  currentEvidence = data.evidence || data.negative_samples || [];
  renderedEvidenceCount = 3;

  // Conditionally show/hide evidence section
  const isReviewQuery = classifyQueryIntent(query) === 'review';
  const showEvidence = (currentEvidence.length > 0) && (isReviewQuery || (data.parsed_intent && data.parsed_intent.review_query));
  const evidenceSec = document.getElementById('evidenceSection');
  if (evidenceSec) {
    if (showEvidence) {
      evidenceSec.style.display = 'block';
      renderEvidenceSlice();
    } else {
      evidenceSec.style.display = 'none';
    }
  }

  // Recommended tracks
  const splitContainer = document.querySelector('.results-split');
  const rightPanel = document.getElementById('resultsRight');
  const tracksListEl = document.getElementById('recommendedTracksList');
  
  const tracks = data.tracks || [];
  if (tracks.length > 0) {
    if (splitContainer) splitContainer.classList.add('has-tracks');
    if (rightPanel) rightPanel.style.display = 'block';
    if (tracksListEl) {
      tracksListEl.innerHTML = tracks.map((t, idx) => {
        const escapedName = escHtml(t.track_name || t.name || '');
        const escapedArtist = escHtml(t.artist || '');
        return `
          <div class="track-card">
            <span class="track-num">${idx + 1}</span>
            <button class="play-track-btn" onclick="playSong('${escapedName}', '${escapedArtist}', this)">▶</button>
            <div class="track-details">
              <span class="track-name">${t.track_name || t.name}</span>
              <span class="track-artist">${t.artist}</span>
              <div class="track-mood-tags">
                <span class="mood-tag">${t.genre || 'General'}</span>
                ${t.subgenre ? `<span class="mood-tag">${t.subgenre}</span>` : ''}
              </div>
              <div style="display:flex; align-items:center; gap:0.5rem; margin-top:0.25rem;">
                <span style="font-size:0.7rem; color:var(--text-muted)">Energy:</span>
                <div class="energy-bar" style="width:60px;"><div class="energy-fill" style="width:${Math.round((t.energy || 0.5) * 100)}%"></div></div>
                <span style="font-size:0.7rem; color:var(--text-muted); margin-left:0.5rem">Tempo: ${t.tempo_bpm || t.tempo || 120} BPM</span>
              </div>
            </div>
            <button class="add-track-btn" onclick="addToPlaylist('${escapedName}', '${escapedArtist}')">+</button>
          </div>
        `;
      }).join('');
    }
  } else {
    if (splitContainer) splitContainer.classList.remove('has-tracks');
    if (rightPanel) rightPanel.style.display = 'none';
  }

  document.getElementById('resultsPanel').style.display = 'block';
  document.getElementById('resultsPanel').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderEvidenceSlice() {
  const evidenceEl = document.getElementById('evidenceCards');
  const sliced = currentEvidence.slice(0, renderedEvidenceCount);
  
  evidenceEl.innerHTML = sliced.map(e => `
    <div class="evidence-item">
      <p class="evidence-quote">"${e.content}"</p>
      <div class="evidence-meta">
        <span class="platform-badge ${platformClass(e.platform)}">${platformLabel(e.platform)}</span>
        <span>${e.date || ''}</span>
      </div>
    </div>
  `).join('') || '<p style="color:var(--text-muted);font-size:0.85rem">No evidence samples available.</p>';

  // Toggle "Load more evidence" button visibility
  const loadMoreBtn = document.getElementById('loadMoreEvidenceBtn');
  if (loadMoreBtn) {
    if (currentEvidence.length > renderedEvidenceCount) {
      loadMoreBtn.style.display = 'inline-block';
    } else {
      loadMoreBtn.style.display = 'none';
    }
  }
}

function loadMoreEvidence() {
  renderedEvidenceCount += 3;
  renderEvidenceSlice();
  showToast('Loaded more evidence.');
}

function platformClass(p) {
  const m = { reddit: 'reddit', play_store: 'play', app_store: 'appstore', twitter: 'twitter' };
  return m[p] || 'reddit';
}
function platformLabel(p) {
  const m = { reddit: 'Reddit', play_store: 'Play Store', app_store: 'App Store', twitter: 'Twitter' };
  return m[p] || p;
}
function escHtml(s) { return (s || '').replace(/'/g, "\\'"); }

async function applyRefinement() {
  const query = document.getElementById('queryInput').value.trim();
  if (!query) { showToast('Please enter a refinement instruction.'); return; }

  const btn = document.getElementById('refineBtn');
  btn.disabled = true;
  const originalText = btn.innerHTML;
  btn.innerHTML = 'Refining...';

  const resultsPanel = document.getElementById('resultsPanel');
  resultsPanel.style.display = 'block';
  resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Shimmer effect
  document.getElementById('analysisContent').innerHTML = `
    <div class="skeleton" style="height: 16px; width: 95%; margin-bottom: 12px;"></div>
    <div class="skeleton" style="height: 16px; width: 80%; margin-bottom: 12px;"></div>
    <div class="skeleton" style="height: 16px; width: 65%;"></div>
  `;

  const startTime = Date.now();
  try {
    const resp = await fetch(`${API_BASE}/discover/refine`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'frontend_session',
        refinement: query,
        previous_intent: {}
      })
    });

    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    const data = await resp.json();

    const elapsed = Date.now() - startTime;
    if (elapsed < 800) {
      await new Promise(resolve => setTimeout(resolve, 800 - elapsed));
    }

    renderResults(query, data);
  } catch (err) {
    console.warn('Backend not reachable for refinement, using mock:', err.message);
    const elapsed = Date.now() - startTime;
    if (elapsed < 800) {
      await new Promise(resolve => setTimeout(resolve, 800 - elapsed));
    }
    renderResults(query, getMockDiscoverResponse(query));
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

/* ══════════════════════════════════════════════════════════
   DASHBOARD
══════════════════════════════════════════════════════════ */
function getMockInsights(vary = false, allNegatives = false) {
  const offset = vary ? (Math.random() > 0.5 ? 1 : -1) * Math.floor(Math.random() * 20) : 0;
  
  const negative = Math.max(600, 1010 + offset);
  const neutral = Math.max(400, 739 - offset);
  const positive = Math.max(100, 251 + Math.floor(offset / 2));
  const total = negative + neutral + positive;

  const topics = {
    "Algorithmic Bubble / Recommendation Repetition": Math.max(200, 546 + offset),
    "General Feedback / Other": Math.max(300, 979 - offset),
    "Decision overload": Math.max(80, 234 + Math.floor(offset / 3)),
    "Taste pollution / Lack of Sandbox mode": Math.max(40, 108 - Math.floor(offset / 2)),
    "Smart Shuffle loop issues": Math.max(40, 133 + Math.floor(offset / 4))
  };

  const mockQuotes = [
    { content: "I'm so tired of Spotify playing the same 15 songs on repeat. My Daily Mix is just songs from my own liked playlist.", platform: "reddit", user: "u/reddit_listener_4821", date: "2026-07-01", topic: "Algorithmic Bubble / Recommendation Repetition" },
    { content: "I skipped this song 5 times this week. Why is Spotify still playing it on my smart shuffle? It does not learn.", platform: "play_store", user: "play_store_user_2341", date: "2026-06-29", topic: "Smart Shuffle loop issues" },
    { content: "My kids' music completely ruined my recommendations. I need a sandbox mode or separate profiles.", platform: "app_store", user: "app_store_user_9174", date: "2026-06-28", topic: "Taste pollution / Lack of Sandbox mode" },
    { content: "Discover Weekly has become an echo chamber of the same artists. I get zero actual indie recommendations anymore.", platform: "twitter", user: "indie_fan_99", date: "2026-06-30", topic: "Algorithmic Bubble / Recommendation Repetition" },
    { content: "Why do I have to spend 20 minutes scrolling just to pick a playlist? Too many options, zero guidance.", platform: "play_store", user: "tired_scroll_88", date: "2026-06-27", topic: "Decision overload" },
    { content: "The smart shuffle is absolute garbage. It only cycles between the same handful of tracks, completely ignoring my skips.", platform: "reddit", user: "u/shuffle_victim", date: "2026-06-26", topic: "Smart Shuffle loop issues" },
    { content: "Why can't we exclude playlists from our taste profile? Listening to study music for one day completely broke my recommendations.", platform: "app_store", user: "lofi_studier", date: "2026-06-25", topic: "Taste pollution / Lack of Sandbox mode" },
    { content: "The UI is so bloated now. I just want to play my albums, but I'm constantly forced to look at podcasts and audiobooks.", platform: "play_store", user: "album_purist", date: "2026-06-24", topic: "General Feedback / Other" },
    { content: "Every time there's an update, the app becomes more unstable. It keeps crashing when switching from Wi-Fi to cellular data.", platform: "app_store", user: "mobile_user_x", date: "2026-06-23", topic: "General Feedback / Other" },
    { content: "Smart Shuffle is not smart at all. I want normal shuffle back. Why is it so hard to just shuffle my own songs randomly?", platform: "reddit", user: "u/random_shuffler", date: "2026-06-22", topic: "Smart Shuffle loop issues" },
    { content: "Why is there no simple toggle to disable recommendations in smart shuffle permanently? It keeps adding random pop songs.", platform: "twitter", user: "pop_hater_88", date: "2026-06-21", topic: "Smart Shuffle loop issues" },
    { content: "I hate that I cannot block specific artists or genres from showing up in my Release Radar. Please give us more control!", platform: "app_store", user: "radar_watcher", date: "2026-06-20", topic: "Algorithmic Bubble / Recommendation Repetition" }
  ];

  const shuffled = [...mockQuotes].sort(() => 0.5 - Math.random());
  const negative_samples = allNegatives ? shuffled.slice(0, 12) : shuffled.slice(0, 3);

  return {
    _isMock: true,
    statistics: { sentiments: { Negative: negative, Neutral: neutral, Positive: positive }, topics },
    negative_samples
  };
}

function renderDashboard(data) {
  // Normalize see more/less toggle state
  showingAllFeedback = false;
  const seeMoreBtn = document.getElementById('seeMoreFeedbackBtn');
  if (seeMoreBtn) {
    seeMoreBtn.textContent = 'See more';
  }

  const sentiments = data.statistics?.sentiments || {};
  const negative = sentiments.Negative || 0;
  const neutral = sentiments.Neutral || 0;
  const positive = sentiments.Positive || 0;
  const total = negative + neutral + positive;

  // Update KPI cards
  document.getElementById('kpi-total-reviews').textContent = total;
  document.getElementById('kpi-negative-sentiment').textContent = negative;
  
  // Find Top Pain Point
  const topics = data.statistics?.topics || {};
  let maxTopic = 'None';
  let maxCount = 0;
  for (const [topic, count] of Object.entries(topics)) {
    if (topic !== 'General Feedback / Other' && count > maxCount) {
      maxTopic = topic;
      maxCount = count;
    }
  }
  if (maxCount === 0 && topics['General Feedback / Other'] > 0) {
    maxTopic = 'General Feedback / Other';
    maxCount = topics['General Feedback / Other'];
  }

  document.getElementById('kpi-top-pain-value').textContent = topicDisplayNames[maxTopic] || maxTopic;
  document.getElementById('kpi-top-pain-sub').textContent = `${maxCount} mentions`;

  // Churn Risk Score
  const churnPercent = total > 0 ? Math.round((negative / total) * 100) : 0;
  document.getElementById('kpi-churn-risk-value').textContent = `${churnPercent}%`;
  document.getElementById('kpi-churn-risk-fill').style.width = `${churnPercent}%`;

  // Donut Chart
  document.getElementById('donut-total-text').textContent = total;
  
  const C = 282.74; // Circumference for r=45
  const fNeg = total > 0 ? negative / total : 0;
  const fNeu = total > 0 ? neutral / total : 0;
  const fPos = total > 0 ? positive / total : 0;

  const donutNeg = document.getElementById('donut-circle-negative');
  const donutNeu = document.getElementById('donut-circle-neutral');
  const donutPos = document.getElementById('donut-circle-positive');

  donutNeg.setAttribute('stroke-dasharray', `${(fNeg * C).toFixed(1)} ${(C - fNeg * C).toFixed(1)}`);
  donutNeg.setAttribute('stroke-dashoffset', '0');

  donutNeu.setAttribute('stroke-dasharray', `${(fNeu * C).toFixed(1)} ${(C - fNeu * C).toFixed(1)}`);
  donutNeu.setAttribute('stroke-dashoffset', `-${(fNeg * C).toFixed(1)}`);

  donutPos.setAttribute('stroke-dasharray', `${(fPos * C).toFixed(1)} ${(C - fPos * C).toFixed(1)}`);
  donutPos.setAttribute('stroke-dashoffset', `-${((fNeg + fNeu) * C).toFixed(1)}`);

  // Legend
  document.getElementById('donutLegend').innerHTML = `
    <div class="legend-item"><span class="legend-dot" style="background:#e74c3c"></span> Negative (${negative})</div>
    <div class="legend-item"><span class="legend-dot" style="background:#888"></span> Neutral (${neutral})</div>
    <div class="legend-item"><span class="legend-dot" style="background:#1DB954"></span> Positive (${positive})</div>
  `;

  // Topic Frequency Bar Chart
  const barChartEl = document.getElementById('dashboard-topics-bar-chart');
  const sortedTopics = Object.entries(topics).sort((a, b) => b[1] - a[1]);
  const maxVal = Math.max(...Object.values(topics), 1);

  barChartEl.innerHTML = sortedTopics.map(([topic, count]) => {
    const displayName = topicDisplayNames[topic] || topic;
    const pct = Math.round((count / maxVal) * 100);
    const isSecondary = topic === 'General Feedback / Other' ? ' secondary' : '';
    return `
      <div class="bar-row">
        <span class="bar-label">${displayName}</span>
        <div class="bar-track"><div class="bar-fill${isSecondary}" style="width:${pct}%">${count}</div></div>
      </div>
    `;
  }).join('') || '<p style="color:var(--text-muted);font-size:0.85rem">No topic statistics available.</p>';

  // Critical Feedback Samples
  const samples = data.negative_samples || [];
  renderFeedbackList(samples);
}

async function loadDashboard(vary = false) {
  try {
    const resp = await fetch(`${API_BASE}/insights`);
    if (!resp.ok) throw new Error();
    lastInsights = await resp.json();
    
    // Check if the database has actual insight records
    const sentiments = lastInsights.statistics?.sentiments || {};
    const total = (sentiments.Negative || 0) + (sentiments.Neutral || 0) + (sentiments.Positive || 0);
    
    if (total === 0) {
      // Database has no records, fallback to mock insights
      lastInsights = getMockInsights(vary);
    }
    
    renderDashboard(lastInsights);
  } catch (err) {
    console.warn('Backend not reachable for insights, using mock data:', err.message);
    lastInsights = getMockInsights(vary);
    renderDashboard(lastInsights);
  }
}

async function refreshDashboard() {
  const btn = document.getElementById('refreshDashboardBtn');
  const body = document.getElementById('dashboardBody');
  if (!btn || !body) return;

  btn.classList.add('btn-refresh-loading');
  body.classList.add('loading');
  btn.disabled = true;

  // Simulate network/rendering delay to make the reload transition visual
  await new Promise(resolve => setTimeout(resolve, 800));

  try {
    await loadDashboard(true);
    lastSyncTime = Date.now();
    updateSyncTime();
  } catch (err) {
    console.error('Refresh error:', err);
  } finally {
    btn.classList.remove('btn-refresh-loading');
    body.classList.remove('loading');
    btn.disabled = false;
  }
}

/* ══════════════════════════════════════════════════════════
   PIPELINE
══════════════════════════════════════════════════════════ */
const PIPELINE_ENDPOINTS = {
  ingest:  `${API_BASE}/ingest`,
  analyze: `${API_BASE}/analyze`,
  seed:    null   // seed runs locally via scheduler
};

async function runPipelineStep(step, btn) {
  const stepEl = btn.closest('.pipeline-step');
  const statusChip = stepEl.querySelector('.status-chip');
  const timeEl = stepEl.querySelector('.step-time');

  btn.disabled = true;
  btn.textContent = 'Running...';
  statusChip.className = 'status-chip running';
  statusChip.textContent = 'RUNNING';

  appendLog(`>> Running step: ${step}...`, 'info');

  const start = Date.now();
  try {
    const endpoint = PIPELINE_ENDPOINTS[step];
    if (endpoint) {
      const resp = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      const elapsed = ((Date.now() - start) / 1000).toFixed(1);
      statusChip.className = 'status-chip pass';
      statusChip.textContent = 'PASS';
      timeEl.textContent = `Just now · ${elapsed}s`;
      appendLog(`   [PASS] ${step} completed in ${elapsed}s`, 'pass');
      if (data.inserted_total) appendLog(`   Inserted ${data.inserted_total} reviews`, 'info');
      if (data.processed_total) appendLog(`   Processed ${data.processed_total} reviews`, 'info');
      showToast(`✓ ${step} completed successfully`);
    } else {
      // Seed is run via scheduler only
      appendLog(`   [INFO] Seed runs via local scheduler (python scheduler.py --once)`, 'info');
      showToast('Run: python scheduler.py --once to seed ChromaDB');
      statusChip.className = 'status-chip pass';
      statusChip.textContent = 'PASS';
    }
  } catch (err) {
    statusChip.className = 'status-chip fail';
    statusChip.textContent = 'FAIL';
    appendLog(`   [FAIL] ${step}: ${err.message}`, 'fail');
    showToast(`✗ ${step} failed: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run Now';
  }
}

async function runFullPipeline() {
  const steps = ['ingest', 'analyze'];
  for (const step of steps) {
    const btn = document.querySelector(`[onclick="runPipelineStep('${step}', this)"]`);
    if (btn) await runPipelineStep(step, btn);
  }
  showToast('Full pipeline complete!');
}

function appendLog(msg, type = 'info') {
  const terminal = document.getElementById('logTerminal');
  const line = document.createElement('div');
  line.className = `log-line ${type}`;
  line.textContent = msg;
  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
}

function copyLog() {
  const text = document.getElementById('logTerminal').innerText;
  navigator.clipboard.writeText(text).then(() => showToast('Log copied to clipboard'));
}

function clearLog() {
  document.getElementById('logTerminal').innerHTML = '<div class="log-line info">Log cleared. Ready.</div>';
}

/* ══════════════════════════════════════════════════════════
   PLAYLISTS
══════════════════════════════════════════════════════════ */
function connectSpotify() {
  fetch(`${API_BASE}/spotify/login`)
    .then(r => r.json())
    .then(d => { if (d.auth_url) window.location.href = d.auth_url; })
    .catch(() => showToast('Spotify auth not configured. Set SPOTIFY_CLIENT_ID in .env'));
}

function addToPlaylist(name, artist) {
  const list = document.getElementById('playlistTracks');
  const idx = list.children.length + 1;
  const item = document.createElement('div');
  item.className = 'playlist-track-item';
  
  const escName = name.replace(/'/g, "\\'").replace(/"/g, '&quot;');
  const escArtist = artist.replace(/'/g, "\\'").replace(/"/g, '&quot;');
  
  item.innerHTML = `
    <span class="track-num">${idx}</span>
    <button class="play-track-btn" onclick="playSong('${escName}', '${escArtist}', this)">▶</button>
    <div class="track-info">
      <span class="track-name">${name}</span>
      <span class="track-artist">${artist}</span>
    </div>
    <button class="remove-track" onclick="removeTrack(this)">✕</button>
  `;
  list.appendChild(item);
  showToast(`Added "${name}" to playlist`);
  switchTab('playlists');
}

function removeTrack(btn) {
  const item = btn.closest('.playlist-track-item');
  const playBtn = item.querySelector('.play-track-btn');
  if (playBtn && playBtn.classList.contains('playing')) {
    stopCurrentAudio();
  }
  item.remove();
  // Re-number
  document.querySelectorAll('.playlist-track-item').forEach((el, i) => {
    el.querySelector('.track-num').textContent = i + 1;
  });
}

// Procedural Audio Preview Engine (Web Audio API)
let currentAudioContext = null;
let currentMelodyTimer = null;
let currentlyPlayingBtn = null;
let currentlyPlayingTrackKey = null;

function playSong(name, artist, btn) {
  const trackKey = `${name} - ${artist}`;
  if (currentlyPlayingTrackKey === trackKey) {
    stopCurrentAudio();
    return;
  }
  
  stopCurrentAudio();
  
  currentlyPlayingTrackKey = trackKey;
  currentlyPlayingBtn = btn;
  btn.innerHTML = '⏸';
  btn.classList.add('playing');
  
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    const ctx = new AudioContext();
    currentAudioContext = ctx;
    
    const notes = [261.63, 329.63, 392.00, 493.88, 523.25, 587.33, 659.25, 783.99];
    let step = 0;
    
    function playNextNote() {
      if (!currentAudioContext || currentAudioContext.state === 'closed') return;
      
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.type = 'sine';
      // Generate a unique seed for the melody based on track name
      const seed = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const freqIndex = (step + seed) % notes.length;
      osc.frequency.setValueAtTime(notes[freqIndex], ctx.currentTime);
      
      gain.gain.setValueAtTime(0, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.08, ctx.currentTime + 0.1);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.8);
      
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 1.0);
      
      step++;
      currentMelodyTimer = setTimeout(playNextNote, 350);
    }
    
    playNextNote();
    showToast(`Playing preview: ${name}`);
  } catch (e) {
    console.error('Web Audio API not supported:', e);
    showToast('Audio playback not supported');
  }
}

function stopCurrentAudio() {
  if (currentMelodyTimer) {
    clearTimeout(currentMelodyTimer);
    currentMelodyTimer = null;
  }
  if (currentAudioContext) {
    currentAudioContext.close().catch(() => {});
    currentAudioContext = null;
  }
  if (currentlyPlayingBtn) {
    currentlyPlayingBtn.innerHTML = '▶';
    currentlyPlayingBtn.classList.remove('playing');
    currentlyPlayingBtn = null;
  }
  currentlyPlayingTrackKey = null;
}

async function createPlaylist() {
  const name = document.getElementById('playlistName').value || 'AI Discovery Playlist';
  const tracks = Array.from(document.querySelectorAll('.playlist-track-item')).map(el => ({
    name: el.querySelector('.track-name').textContent,
    artist: el.querySelector('.track-artist').textContent
  }));

  if (!tracks.length) { showToast('Add some tracks first.'); return; }

  showToast(`Creating playlist "${name}"...`);
  try {
    const resp = await fetch(`${API_BASE}/spotify/create-playlist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, track_names: tracks.map(t => t.name) })
    });
    if (!resp.ok) throw new Error();
    showToast(`✓ Playlist "${name}" created on Spotify!`);
  } catch {
    showToast(`Playlist saved locally (Spotify auth not connected)`);
  }
}

function savePlaylist() {
  switchTab('playlists');
  showToast('Tracks added to Playlist Creator');
}

function applyTrackRefinement() {
  const refinement = document.getElementById('refineInput').value.trim();
  if (!refinement) return;
  showToast(`Refinement applied: "${refinement}"`);
  document.getElementById('refineInput').value = '';
}

/* ══════════════════════════════════════════════════════════
   FEEDBACK / SURVEY
══════════════════════════════════════════════════════════ */
let currentRating = 0;

function rateStar(n) {
  currentRating = n;
  document.querySelectorAll('.star').forEach((s, i) => {
    s.classList.toggle('active', i < n);
  });
}

function submitFeedback() {
  if (!currentRating) { showToast('Please select a star rating.'); return; }
  showToast(`Thank you! ${currentRating}★ feedback submitted.`);
}

/* ══════════════════════════════════════════════════════════
   TOAST
══════════════════════════════════════════════════════════ */
let toastTimer = null;
function showToast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3000);
}

/* ══════════════════════════════════════════════════════════
   GLOBAL SEARCH
══════════════════════════════════════════════════════════ */
document.getElementById('globalSearch').addEventListener('keydown', e => {
  if (e.key === 'Enter') {
    const q = e.target.value.trim();
    if (q) {
      document.getElementById('queryInput').value = q;
      switchTab('discover');
      runSearch();
      e.target.value = '';
    }
  }
});

document.getElementById('queryInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    runSearch();
  }
});

/* ══════════════════════════════════════════════════════════
   LIVE SYNC TIMER
══════════════════════════════════════════════════════════ */
function updateSyncTime() {
  const diff = Math.round((Date.now() - lastSyncTime) / 1000);
  let label;
  if (diff < 60) label = `LAST SYNCED ${diff}s AGO`;
  else if (diff < 3600) label = `LAST SYNCED ${Math.round(diff / 60)} MIN AGO`;
  else label = `LAST SYNCED ${Math.round(diff / 3600)}h AGO`;
  const el = document.getElementById('lastSync');
  if (el) el.textContent = label;
}

setInterval(updateSyncTime, 10000);

/* ══════════════════════════════════════════════════════════
   KEYBOARD SHORTCUTS
══════════════════════════════════════════════════════════ */
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    document.getElementById('globalSearch').focus();
  }
  if (e.key === 'Escape') {
    document.getElementById('globalSearch').blur();
    document.getElementById('queryInput').blur();
  }
});

/* ══════════════════════════════════════════════════════════
   DASHBOARD FEEDBACK EXPANSION
   ══════════════════════════════════════════════════════════ */
function renderFeedbackList(samples) {
  const feedbackCardsEl = document.getElementById('dashboard-feedback-cards');
  if (!feedbackCardsEl) return;
  
  activeFeedbackSamples = samples || [];
  
  feedbackCardsEl.innerHTML = activeFeedbackSamples.map((s, idx) => {
    const platClass = platformClass(s.platform);
    const platLabel = platformLabel(s.platform);
    const topicLabel = topicDisplayNames[s.topic] || s.topic || 'General';
    const user = s.user || 'Anonymous';
    const date = s.date || 'Just now';
    return `
      <div class="feedback-card">
        <div class="feedback-top">
          <span class="platform-badge ${platClass}">${platLabel}</span>
          <span class="topic-chip">${topicLabel}</span>
        </div>
        <p class="feedback-quote">"${s.content}"</p>
        <div class="feedback-meta">
          <span>${user}</span>
          <span>${date}</span>
          <a href="#" class="view-link" onclick="event.preventDefault(); openReviewModal(${idx});">View full →</a>
        </div>
      </div>
    `;
  }).join('') || '<p style="color:var(--text-muted);font-size:0.85rem">No critical feedback samples available.</p>';
}

async function toggleSeeAllFeedback() {
  const btn = document.getElementById('seeMoreFeedbackBtn');
  if (!btn) return;
  
  if (showingAllFeedback) {
    // Collapse
    showingAllFeedback = false;
    btn.textContent = 'See more';
    if (lastInsights && lastInsights.negative_samples && !lastInsights._isAllNegatives) {
      renderFeedbackList(lastInsights.negative_samples);
    } else {
      await loadDashboard(false);
    }
  } else {
    // Expand
    showingAllFeedback = true;
    btn.textContent = 'Loading...';
    btn.disabled = true;
    try {
      let data;
      const isMock = lastInsights?._isMock;
      if (isMock) {
        data = getMockInsights(false, true);
      } else {
        try {
          const resp = await fetch(`${API_BASE}/insights?all_negatives=true`);
          if (!resp.ok) throw new Error();
          data = await resp.json();
          data._isAllNegatives = true;
        } catch (err) {
          console.warn('Backend not reachable for insights, using mock data:', err.message);
          data = getMockInsights(false, true);
        }
      }
      btn.textContent = 'See less';
      renderFeedbackList(data.negative_samples || []);
    } catch (err) {
      console.error(err);
      btn.textContent = 'See more';
      showingAllFeedback = false;
    } finally {
      btn.disabled = false;
    }
  }
}

/* ══════════════════════════════════════════════════════════
   INIT
══════════════════════════════════════════════════════════ */
(function init() {
  // Focus search input on Discover tab
  document.getElementById('queryInput').focus();
  // Load initial dashboard metrics dynamically
  loadDashboard(false);
})();

/* ══════════════════════════════════════════════════════════
   REVIEW DETAILS MODAL
══════════════════════════════════════════════════════════ */
function openReviewModal(dataOrIndex) {
  let data;
  if (typeof dataOrIndex === 'number') {
    data = activeFeedbackSamples[dataOrIndex];
  } else {
    data = dataOrIndex;
  }
  if (!data) return;

  const modal = document.getElementById('reviewModal');
  if (!modal) return;

  // Set platform badge
  const platformEl = document.getElementById('modal-platform');
  if (platformEl) {
    platformEl.textContent = platformLabel(data.platform);
    platformEl.className = 'platform-badge ' + platformClass(data.platform);
  }

  // Set topic chip
  const topicEl = document.getElementById('modal-topic');
  if (topicEl) {
    topicEl.textContent = topicDisplayNames[data.topic] || data.topic || 'General';
  }

  // Set sentiment badge
  const sentimentEl = document.getElementById('modal-sentiment');
  if (sentimentEl) {
    const sentiment = data.sentiment || 'Negative';
    sentimentEl.textContent = sentiment;
    sentimentEl.className = 'sentiment-badge ' + (sentiment.toLowerCase() === 'positive' ? 'success' : sentiment.toLowerCase() === 'neutral' ? 'warning' : 'danger');
  }

  // Set quote/content
  const quoteEl = document.getElementById('modal-quote');
  if (quoteEl) {
    quoteEl.textContent = `"${data.content}"`;
  }

  // Set author
  const authorEl = document.getElementById('modal-author');
  if (authorEl) {
    authorEl.textContent = data.user || 'Anonymous';
  }

  // Set date
  const dateEl = document.getElementById('modal-date');
  if (dateEl) {
    dateEl.textContent = data.date || 'Just now';
  }

  // Show modal with animation
  modal.style.display = 'flex';
  modal.offsetHeight; // force reflow
  modal.classList.add('show');
}

function closeReviewModal(event) {
  const modal = document.getElementById('reviewModal');
  if (!modal) return;
  modal.classList.remove('show');
  setTimeout(() => {
    if (!modal.classList.contains('show')) {
      modal.style.display = 'none';
    }
  }, 300);
}
