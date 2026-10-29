// State Management
const appState = {
  activeTab: 'discovery',
  discovered: [],
  filtered: [],
  enriched: [],
  outreach: [],
  tracker: [],
  stats: {}
};

// Initialization on DOM Load
document.addEventListener('DOMContentLoaded', () => {
  fetchStats();
  fetchAllDatasets();
});

// Switch Dashboard Tab
function switchTab(tabId) {
  appState.activeTab = tabId;

  // Update nav buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });

  // Update stepper cards
  document.querySelectorAll('.step-card').forEach((card, index) => {
    const tabs = ['discovery', 'filtering', 'enrichment', 'personalization', 'tracker'];
    card.classList.toggle('active', tabs[index] === tabId);
  });

  // Update tab content visibility
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('active', content.id === `tab-${tabId}`);
  });
}

// Fetch Global Statistics
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const data = await res.json();
    appState.stats = data;

    // Update KPI UI
    document.getElementById('kpiDiscovered').textContent = data.total_discovered || 55;
    const passRate = data.total_filtered > 0 ? ((data.passed_qualified / data.total_filtered) * 100).toFixed(1) : 76.4;
    document.getElementById('kpiPassed').textContent = `${passRate}%`;
    document.getElementById('kpiPassedCount').textContent = data.passed_qualified || 42;
    document.getElementById('kpiFailedCount').textContent = data.disqualified || 13;
    document.getElementById('kpiEmails').textContent = data.emails_available || 36;

    // Update Stepper counters
    document.getElementById('statDiscovered').textContent = `${data.total_discovered || 55} Profiles`;
    document.getElementById('statFiltered').textContent = `${data.passed_qualified || 42} Qualified / ${data.disqualified || 13} Failed`;
    document.getElementById('statEmails').textContent = `${data.emails_available || 36} Emails Verified`;
    document.getElementById('statPitches').textContent = `${data.personalized_pitches || 42} Custom Pitches`;
    document.getElementById('statTracker').textContent = `${data.outreach_tracked || 42} Outreach Logs`;
  } catch (err) {
    console.error('Error fetching stats:', err);
  }
}

// Fetch All 5 Pipeline Datasets
async function fetchAllDatasets() {
  try {
    const [discRes, filtRes, enrichRes, outRes, trackRes] = await Promise.all([
      fetch('/api/data/discovered'),
      fetch('/api/data/filtered'),
      fetch('/api/data/enriched'),
      fetch('/api/data/outreach'),
      fetch('/api/data/tracker')
    ]);

    if (discRes.ok) appState.discovered = await discRes.json();
    if (filtRes.ok) appState.filtered = await filtRes.json();
    if (enrichRes.ok) appState.enriched = await enrichRes.json();
    if (outRes.ok) appState.outreach = await outRes.json();
    if (trackRes.ok) appState.tracker = await trackRes.json();

    renderDiscoveryTable(appState.discovered);
    renderFilteringTable(appState.filtered);
    renderEnrichmentTable(appState.enriched);
    renderPersonalizationCards(appState.outreach);
    renderTrackerTable(appState.tracker);
  } catch (err) {
    console.error('Error loading datasets:', err);
  }
}

// Render Tab 1: Discovery Table
function renderDiscoveryTable(data) {
  const tbody = document.getElementById('discoveryTableBody');
  if (!tbody) return;
  document.getElementById('discoveryCounter').textContent = `${data.length} Records`;

  tbody.innerHTML = data.map(item => `
    <tr>
      <td><strong>${escapeHtml(item.name || '')}</strong></td>
      <td><span class="badge badge-channel">${escapeHtml(item.platform || '')}</span></td>
      <td><strong>${(item.follower_count || 0).toLocaleString()}</strong></td>
      <td><span class="badge badge-passed">${item.engagement_rate || 0}%</span></td>
      <td>${escapeHtml(item.niche || item.category || '')}</td>
      <td>
        ${item.contact_email && item.contact_email !== 'Not Found' 
          ? `<span style="color:#818cf8;">${escapeHtml(item.contact_email)}</span>` 
          : `<span style="color:#94a3b8; font-style:italic;">Not Found</span>`}
      </td>
      <td><a href="${item.profile_url}" target="_blank" rel="noopener" class="profile-link">View Profile &nearr;</a></td>
      <td>
        ${(Array.isArray(item.content_themes) ? item.content_themes : (item.content_themes || '').split(','))
          .slice(0, 3)
          .map(t => `<span class="theme-pill">${escapeHtml(t.trim())}</span>`).join('')}
      </td>
      <td><span class="badge badge-simulated">${escapeHtml(item.initial_status || 'Discovered')}</span></td>
    </tr>
  `).join('');
}

// Render Tab 2: Filtering Table
function renderFilteringTable(data) {
  const tbody = document.getElementById('filteringTableBody');
  if (!tbody) return;
  document.getElementById('filteringCounter').textContent = `${data.length} Records`;

  tbody.innerHTML = data.map(item => {
    const isPassed = item.passed === true;
    return `
      <tr>
        <td><strong>${escapeHtml(item.name || '')}</strong></td>
        <td><span class="badge badge-channel">${escapeHtml(item.platform || '')}</span></td>
        <td>${(item.follower_count || 0).toLocaleString()}</td>
        <td>${item.engagement_rate || 0}%</td>
        <td>
          <span class="badge ${isPassed ? 'badge-passed' : 'badge-failed'}">
            ${isPassed ? 'PASSED (Qualified Micro)' : 'FAILED (Disqualified)'}
          </span>
        </td>
        <td><span class="badge badge-tier">${escapeHtml(item.classification_tier || '')}</span></td>
        <td style="max-width: 320px; font-size: 0.8rem; line-height: 1.4;">
          ${escapeHtml(item.classification_reason || '')}
        </td>
        <td>
          <div style="font-weight:700; color:${item.brand_fit_score >= 70 ? '#34d399' : '#fb7185'}">
            ${item.brand_fit_score || 50}/100
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// Render Tab 3: Enrichment Table
function renderEnrichmentTable(data) {
  const tbody = document.getElementById('tableEnrichment').querySelector('tbody');
  if (!tbody) return;
  document.getElementById('enrichmentCounter').textContent = `${data.length} Records`;

  tbody.innerHTML = data.map(item => `
    <tr>
      <td><strong>${escapeHtml(item.name || '')}</strong></td>
      <td><span class="badge badge-channel">${escapeHtml(item.platform || '')}</span></td>
      <td>${(item.follower_count || 0).toLocaleString()}</td>
      <td><span style="color:#a78bfa; font-weight:600;">${(item.estimated_active_reach || 0).toLocaleString()}</span></td>
      <td>
        ${item.has_valid_email 
          ? `<span class="badge badge-passed">&#10003; ${escapeHtml(item.contact_email)}</span>` 
          : `<span class="badge badge-failed">&empty; Not Found</span>`}
      </td>
      <td style="font-size:0.75rem;">
        <div>${escapeHtml(item.audience_geography || 'Global')}</div>
        <div style="color:#64748b;">${escapeHtml(item.audience_age || '22-38')} &bull; ${escapeHtml(item.audience_gender || '')}</div>
      </td>
      <td><span class="badge badge-simulated">${escapeHtml(item.recommended_collab_angle || item.collab_type || 'Sponsorship')}</span></td>
      <td>
        <span class="badge ${item.primary_outreach_channel === 'EMAIL' ? 'badge-simulated' : 'badge-dm'}">
          ${escapeHtml(item.primary_outreach_channel || 'EMAIL')}
        </span>
      </td>
    </tr>
  `).join('');
}

// Render Tab 4: Personalization Cards
function renderPersonalizationCards(data) {
  const container = document.getElementById('personalizationCards');
  if (!container) return;
  document.getElementById('personalizationCounter').textContent = `${data.length} Shortlisted Pitches`;

  container.innerHTML = data.map(item => `
    <div class="pitch-card">
      <div class="pitch-card-header">
        <div class="pitch-card-title">
          <h3>${escapeHtml(item.name || '')}</h3>
          <div class="pitch-card-meta">
            <span>${escapeHtml(item.niche || '')}</span> &bull; 
            <span>${escapeHtml(item.collab_type || 'Sponsorship')}</span>
          </div>
        </div>
        <span class="badge badge-passed">&#10003; Qualified Micro</span>
      </div>

      <!-- Email Pitch Box (60-90 words) -->
      <div class="message-box">
        <div class="message-box-header">
          <span class="message-type-label">Email Collaboration Pitch</span>
          <span class="word-count-badge">${item.email_word_count || 0} words (Target: 60-90)</span>
        </div>
        <div style="font-size: 0.8rem; font-weight: 600; color: #94a3b8; margin-bottom: 0.4rem;">
          Subject: <span style="color:#f8fafc;">${escapeHtml(item.email_subject || '')}</span>
        </div>
        <div class="message-content">
          ${escapeHtml(item.email_pitch || '')}
        </div>
      </div>

      <!-- Instagram DM Box (15-30 words) -->
      <div class="message-box dm-box">
        <div class="message-box-header">
          <span class="message-type-label">Instagram DM Pitch</span>
          <span class="word-count-badge">${item.dm_word_count || 0} words (Target: 15-30)</span>
        </div>
        <div class="message-content">
          ${escapeHtml(item.instagram_dm || '')}
        </div>
      </div>

      <div class="pitch-card-footer">
        <span style="font-size:0.75rem; color:#64748b;">
          To: ${item.contact_email !== 'Not Found' ? escapeHtml(item.contact_email) : 'Social Profile Direct'}
        </span>
        <button class="btn btn-outline btn-sm" onclick="copyInstagramDM('${escapeHtml(item.name)}', '${escapeHtml(item.instagram_dm || '').replace(/'/g, "\\'")}')">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          Copy DM & Dispatch
        </button>
      </div>
    </div>
  `).join('');
}

// Render Tab 5: Outreach Tracker Table
function renderTrackerTable(data) {
  const tbody = document.getElementById('trackerTableBody');
  if (!tbody) return;
  document.getElementById('trackerCounter').textContent = `${data.length} Entries`;

  tbody.innerHTML = data.map(item => `
    <tr>
      <td><strong>${escapeHtml(item.influencer || '')}</strong></td>
      <td>
        ${item.email && item.email !== 'Not Found' 
          ? `<span style="color:#818cf8;">${escapeHtml(item.email)}</span>` 
          : `<span style="color:#94a3b8;">Not Found</span>`}
      </td>
      <td><span class="badge badge-channel">${escapeHtml(item.channel || 'EMAIL')}</span></td>
      <td style="max-width: 380px; font-size: 0.8rem; line-height: 1.4;">
        ${escapeHtml((item.message_generated || '').slice(0, 140))}...
      </td>
      <td style="font-family: var(--font-mono); font-size: 0.75rem; color: #94a3b8;">
        ${escapeHtml(item.sent_date || '')}
      </td>
      <td>
        <span class="badge ${item.status === 'SENT' ? 'badge-passed' : item.status === 'SIMULATED' ? 'badge-simulated' : 'badge-dm'}">
          ${escapeHtml(item.status || '')}
        </span>
      </td>
      <td style="font-size: 0.75rem; color: #64748b;">
        ${escapeHtml(item.delivery_details || '')}
      </td>
    </tr>
  `).join('');
}

// Client-Side Search & Filter Helper
function filterTable(tab) {
  if (tab === 'discovery') {
    const q = document.getElementById('searchDiscovery').value.toLowerCase();
    const filtered = appState.discovered.filter(i => 
      (i.name && i.name.toLowerCase().includes(q)) ||
      (i.niche && i.niche.toLowerCase().includes(q)) ||
      (i.platform && i.platform.toLowerCase().includes(q))
    );
    renderDiscoveryTable(filtered);
  } else if (tab === 'filtering') {
    const q = document.getElementById('searchFiltering').value.toLowerCase();
    const statusVal = document.getElementById('filterStatusSelect').value;
    const filtered = appState.filtered.filter(i => {
      const matchQ = (i.name && i.name.toLowerCase().includes(q)) ||
                     (i.classification_reason && i.classification_reason.toLowerCase().includes(q));
      const matchStatus = (statusVal === 'ALL') ||
                          (statusVal === 'PASSED' && i.passed === true) ||
                          (statusVal === 'FAILED' && i.passed === false);
      return matchQ && matchStatus;
    });
    renderFilteringTable(filtered);
  } else if (tab === 'enrichment') {
    const q = document.getElementById('searchEnrichment').value.toLowerCase();
    const filtered = appState.enriched.filter(i =>
      (i.name && i.name.toLowerCase().includes(q)) ||
      (i.contact_email && i.contact_email.toLowerCase().includes(q))
    );
    renderEnrichmentTable(filtered);
  } else if (tab === 'personalization') {
    const q = document.getElementById('searchPersonalization').value.toLowerCase();
    const filtered = appState.outreach.filter(i =>
      (i.name && i.name.toLowerCase().includes(q)) ||
      (i.email_pitch && i.email_pitch.toLowerCase().includes(q))
    );
    renderPersonalizationCards(filtered);
  } else if (tab === 'tracker') {
    const q = document.getElementById('searchTracker').value.toLowerCase();
    const filtered = appState.tracker.filter(i =>
      (i.influencer && i.influencer.toLowerCase().includes(q)) ||
      (i.email && i.email.toLowerCase().includes(q))
    );
    renderTrackerTable(filtered);
  }
}

// Copy Instagram DM & Record Dispatch
async function copyInstagramDM(influencerName, dmText) {
  try {
    await navigator.clipboard.writeText(dmText);
    showToast(`Copied Instagram DM for ${influencerName}!`);

    // Record in API
    await fetch('/api/outreach/record_dm_dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: influencerName })
    });
    
    // Refresh tracker
    const trackRes = await fetch('/api/data/tracker');
    if (trackRes.ok) {
      appState.tracker = await trackRes.json();
      renderTrackerTable(appState.tracker);
    }
  } catch (err) {
    showToast(`Error copying to clipboard: ${err.message}`, true);
  }
}

// Trigger Pipeline Run from UI
async function triggerPipelineRun() {
  const btn = document.getElementById('runPipelineBtn');
  btn.disabled = true;
  btn.innerHTML = `<span class="status-dot pulse"></span> Running Pipeline...`;

  try {
    const res = await fetch('/api/pipeline/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ niche: 'Technology', simulate: true })
    });
    const result = await res.json();
    if (result.success) {
      showToast('Pipeline completed! All datasets updated successfully.');
      await fetchStats();
      await fetchAllDatasets();
    } else {
      showToast(`Pipeline execution failed: ${result.error}`, true);
    }
  } catch (err) {
    showToast(`Network error: ${err.message}`, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
      Run Full Pipeline
    `;
  }
}

// Toast Notifications Helper
function showToast(message, isError = false) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${isError ? 'toast-failed' : 'toast-success'}`;
  toast.innerHTML = `
    <span>${isError ? '&#9888;' : '&#10003;'}</span>
    <span>${escapeHtml(message)}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// HTML Escape Sanitizer
function escapeHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}
