// ═══════════════════════════════════════════
//  Stay — Script.js
//  Light Purple / Meetio-style theme
// ═══════════════════════════════════════════

// Backend API URL (change this to your deployed backend URL)
// const API_BASE_URL = 'http://localhost:8000';
const API_BASE_URL = 'https://medical-alzhiemer.onrender.com';

// Avatar images (recommended location: frontend/assets/)
const AVATAR_PATHS = {
  female: 'assets/female-clinician.png',
  male: 'assets/male-clinician.png',
  bot: 'assets/ai-bot.png.png',
};

// ── Authentication ──────────────────────────────────────
let selectedGender = null;
let authMode = 'signup'; // 'signup' or 'login'
let userData = {
  email: '',
  name: '',
  gender: '',
  profileImage: ''
};

let typingAudioContext = null;
let typingSoundInterval = null;

function ensureToastRoot() {
  let toastRoot = document.getElementById('toast-root');
  if (!toastRoot) {
    toastRoot = document.createElement('div');
    toastRoot.id = 'toast-root';
    document.body.appendChild(toastRoot);
  }
  return toastRoot;
}

function showToast(message, type = 'error') {
  const toastRoot = ensureToastRoot();
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toastRoot.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add('show'));

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 220);
  }, 2600);
}

function setFieldError(fieldId, message) {
  const errorEl = document.getElementById(`${fieldId}-error`);
  const inputEl = document.getElementById(fieldId);
  if (errorEl) errorEl.textContent = message || '';
  if (inputEl) {
    inputEl.style.borderColor = message ? '#dc2626' : '';
    inputEl.style.boxShadow = message ? '0 0 0 3px rgba(220, 38, 38, 0.12)' : '';
  }
}

function clearAnalysisFieldErrors() {
  setFieldError('f-image', '');
  setFieldError('f-age', '');
  setFieldError('f-mmse', '');
  setFieldError('f-symptoms', '');
}

function getClinicianAvatarHTML() {
  if (userData.gender === 'female') {
    return `<img src="${AVATAR_PATHS.female}" alt="Female clinician avatar" onerror="this.style.display='none'; this.parentElement.textContent='👩';">`;
  }
  if (userData.gender === 'male') {
    return `<img src="${AVATAR_PATHS.male}" alt="Male clinician avatar" onerror="this.style.display='none'; this.parentElement.textContent='👨';">`;
  }
  return '👤';
}

function getBotAvatarHTML() {
  return `<img src="${AVATAR_PATHS.bot}" alt="AI avatar" onerror="this.style.display='none'; this.parentElement.textContent='🤖';">`;
}

function startTypingSound() {
  stopTypingSound();
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return;

  try {
    typingAudioContext = new AudioCtx();

    const playPulse = () => {
      if (!typingAudioContext || typingAudioContext.state === 'closed') return;
      const osc = typingAudioContext.createOscillator();
      const gain = typingAudioContext.createGain();
      osc.type = 'sine';
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.0001, typingAudioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.02, typingAudioContext.currentTime + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.0001, typingAudioContext.currentTime + 0.08);
      osc.connect(gain);
      gain.connect(typingAudioContext.destination);
      osc.start();
      osc.stop(typingAudioContext.currentTime + 0.09);
    };

    playPulse();
    typingSoundInterval = setInterval(playPulse, 320);
  } catch (err) {
    console.warn('Typing sound unavailable:', err);
  }
}

function stopTypingSound() {
  if (typingSoundInterval) {
    clearInterval(typingSoundInterval);
    typingSoundInterval = null;
  }
  if (typingAudioContext) {
    typingAudioContext.close().catch(() => {});
    typingAudioContext = null;
  }
}

function selectGender(gender) {
  console.log('selectGender called with:', gender);
  selectedGender = gender;
  userData.gender = gender;

  document.querySelectorAll('.gender-btn').forEach(btn => {
    btn.classList.remove('selected');
  });

  const selectedBtn = document.querySelector(`.gender-btn[data-gender="${gender}"]`);
  if (selectedBtn) {
    selectedBtn.classList.add('selected');
  }
}

function toggleAuthMode(mode) {
  authMode = mode;
  const signupToggle = document.getElementById('signup-toggle');
  const loginToggle = document.getElementById('login-toggle');
  const nameGroup = document.getElementById('name-group');
  const genderGroup = document.getElementById('gender-group');
  const sendOtpBtn = document.getElementById('send-otp-btn');

  if (mode === 'signup') {
    signupToggle.classList.add('active');
    loginToggle.classList.remove('active');
    nameGroup.style.display = 'block';
    genderGroup.style.display = 'block';
    sendOtpBtn.textContent = 'Send OTP';
  } else {
    loginToggle.classList.add('active');
    signupToggle.classList.remove('active');
    nameGroup.style.display = 'none';
    genderGroup.style.display = 'none';
    sendOtpBtn.textContent = 'Login';
  }
}

async function sendOTP() {
  const email = document.getElementById('email-input').value;
  const name = document.getElementById('name-input').value;

  if (!email) {
    showToast('Please enter your email.');
    return;
  }

  if (authMode === 'signup' && (!name || !selectedGender)) {
    showToast('Please fill all fields and select a gender.');
    return;
  }

  userData.email = email;
  if (authMode === 'signup') {
    userData.name = name;
    userData.gender = selectedGender;
  }

  // If login mode, call direct login endpoint
  if (authMode === 'login') {
    try {
      const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email })
      });

      const data = await response.json();

      if (data.success) {
        // Update user data from server
        userData.name = data.user.name;
        userData.gender = data.user.gender;
        userData.email = data.user.email;
        userData.profileImage = data.user.profile_image || '';

        // Show welcome animation
        showWelcomeAnimation();
      } else {
        showToast(data.message || 'Login failed. Please try again.');
      }
    } catch (error) {
      console.error('Error during login:', error);
      showToast('Error during login. Please try again.');
    }
    return;
  }

  // Signup mode - send OTP
  try {
    const response = await fetch(`${API_BASE_URL}/api/send-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        name: name,
        gender: selectedGender
      })
    });

    const data = await response.json();

    if (data.success) {
      // Show OTP form
      document.getElementById('auth-form').style.display = 'none';
      document.getElementById('otp-form').style.display = 'block';
      document.getElementById('otp-input').value = '';
      document.getElementById('otp-input').focus();
    } else {
      showToast('Failed to send OTP. Please try again.');
    }
  } catch (error) {
    console.error('Error sending OTP:', error);
    showToast('Error sending OTP. Please try again.');
  }
}

async function verifyOTP() {
  const otp = document.getElementById('otp-input').value;
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: userData.email, otp })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Update user data from server
      userData.name = data.user.name;
      userData.gender = data.user.gender;
      userData.email = data.user.email;
      userData.profileImage = data.user.profile_image || '';
      
      // Show welcome animation
      showWelcomeAnimation();
    } else {
      showToast('Invalid or expired OTP. Please try again.');
    }
  } catch (error) {
    console.error('Error verifying OTP:', error);
    showToast('Error verifying OTP. Please try again.');
  }
}

function backToAuth() {
  document.getElementById('auth-form').style.display = 'block';
  document.getElementById('otp-form').style.display = 'none';
}

function showWelcomeAnimation() {
  document.getElementById('auth-page').style.display = 'none';
  document.getElementById('welcome-overlay').style.display = 'flex';
  
  // Update welcome message with user name
  document.querySelector('.welcome-message').textContent = `Welcome back, ${userData.name}`;
  
  // Update user avatar in sidebar
  updateUserAvatar();
  loadProfileSettings();
  
  // Hide welcome and show main app after animation
  setTimeout(() => {
    document.getElementById('welcome-overlay').style.display = 'none';
    document.getElementById('main-app').style.display = 'flex';
  }, 2500);
}

function updateUserAvatar() {
  const avatarEl = document.getElementById('user-avatar');
  if (avatarEl) {
    if (userData.profileImage) {
      avatarEl.innerHTML = `<img src="${userData.profileImage}" alt="Profile image">`;
    } else if (userData.gender === 'male') {
      avatarEl.textContent = '♂';
    } else if (userData.gender === 'female') {
      avatarEl.textContent = '♀';
    } else {
      // Use initials
      const initials = userData.name.split(' ').map(n => n[0]).join('').toUpperCase();
      avatarEl.textContent = initials;
    }
  }
  
  // Update user name
  const nameEl = document.getElementById('user-name');
  if (nameEl) {
    nameEl.textContent = userData.name;
  }
  
  // Update user email
  const emailEl = document.getElementById('user-email');
  if (emailEl) {
    emailEl.textContent = userData.email;
  }

  const previewEl = document.getElementById('settings-avatar-preview');
  if (previewEl) {
    if (userData.profileImage) {
      previewEl.innerHTML = `<img src="${userData.profileImage}" alt="Profile image">`;
    } else if (userData.gender === 'male') {
      previewEl.textContent = '♂';
    } else if (userData.gender === 'female') {
      previewEl.textContent = '♀';
    } else {
      previewEl.textContent = userData.name?.[0]?.toUpperCase() || '?';
    }
  }
}

// ── Page Navigation ──────────────────────────────────────
const PAGE_TITLES = {
  dashboard: 'Clinical Intelligence',
  chat:      'Clinical Intelligence',
  analysis:  'MRI Image <em>Analysis</em>',
  settings:  'Profile <em>Settings</em>',
};

function switchPage(id, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + id)?.classList.add('active');

  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (el) el.classList.add('active');

  const titleEl = document.getElementById('topbar-title');
  if (titleEl) titleEl.innerHTML = PAGE_TITLES[id] || id;

  if (id === 'settings') {
    loadProfileSettings();
  }
}

function goToSettings() {
  switchPage('settings');
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const settingsNav = Array.from(document.querySelectorAll('.nav-item'))
    .find((node) => node.textContent.includes('Settings'));
  if (settingsNav) settingsNav.classList.add('active');
}

function loadProfileSettings() {
  const nameEl = document.getElementById('settings-name');
  const emailEl = document.getElementById('settings-email');
  const genderEl = document.getElementById('settings-gender');

  if (nameEl) nameEl.value = userData.name || '';
  if (emailEl) emailEl.value = userData.email || '';
  if (genderEl) genderEl.value = userData.gender || '';
  updateUserAvatar();
}

function handleProfileImageUpload(input) {
  if (!input.files || !input.files[0]) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    userData.profileImage = e.target.result;
    updateUserAvatar();
    showToast('Profile image updated.', 'success');
  };
  reader.readAsDataURL(input.files[0]);
}

async function saveProfileSettings() {
  const nameEl = document.getElementById('settings-name');
  const emailEl = document.getElementById('settings-email');
  const genderEl = document.getElementById('settings-gender');

  const name = nameEl?.value?.trim();
  const email = emailEl?.value?.trim();
  const gender = genderEl?.value;

  if (!name || !email || !gender) {
    showToast('Please fill name, email, and gender.');
    return;
  }

  const previousEmail = userData.email;

  try {
    const response = await fetch(`${API_BASE_URL}/api/profile/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_email: previousEmail,
        email: email,
        name: name,
        gender: gender,
        profile_image: userData.profileImage || ''
      })
    });

    const data = await response.json();
    if (!response.ok || !data.success) {
      throw new Error(data.message || 'Failed to update profile');
    }

    userData.name = data.user.name;
    userData.email = data.user.email;
    userData.gender = data.user.gender;
    userData.profileImage = data.user.profile_image || '';
    updateUserAvatar();
    showToast('Profile updated successfully.', 'success');
  } catch (error) {
    console.error('Profile update error:', error);
    showToast(error.message || 'Failed to update profile.');
  }
}

function toggleFilter(btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

// ── Chat ─────────────────────────────────────────────────
const MOCK_RESPONSE = {
  sections: [
    {
      title: '1. Score / Symptom Analysis',
      body: 'An MMSE score of 19/30 places this patient in the <strong>Mild Alzheimer\'s Disease</strong> range (18–23). Deficits are typically observed in short-term recall, orientation to time and place, and visuospatial tasks, exceeding normal age-related variation.'
    },
    {
      title: '2. NIA-AA 2018 Criteria Match',
      body: 'Per NIA-AA 2018 guidelines, this profile satisfies the criteria for <em>Probable Alzheimer\'s Disease — Dementia Stage</em>. Biomarker confirmation (amyloid/tau) is required to move from probable to definitive classification.'
    },
    {
      title: '3. Risk & Functional Assessment',
      body: 'ADL performance is likely impacted at this threshold. A CDR score of 1 (Mild) is expected. Caregiver burden increases significantly beyond MMSE 20. Social and occupational functioning may be noticeably affected.'
    },
    {
      title: '4. Recommended Next Steps',
      body: 'Full neuropsychological battery · Amyloid PET or CSF biomarkers (tau/Aβ42) · MRI to rule out vascular contributions · OT assessment for ADL capacity · Caregiver support referral.'
    },
  ],
  sources: ['alzheimer_facts_2024.pdf · p.12', 'nia_aa_guidelines.pdf · p.7']
};

function buildBotHTML(data) {
  let html = `<div class="msg-bubble">`;
  data.sections.forEach(s => {
    html += `
      <div class="msg-section">
        <div class="msg-section-title">${s.title}</div>
        <div class="msg-section-body">${s.body}</div>
      </div>`;
  });
  html += `<div style="margin-top:12px;">`;
  data.sources.forEach(src => {
    html += `<span class="source-chip">📄 ${src}</span>`;
  });
  html += `</div>`;
  html += `<div style="margin-top:10px;font-size:11px;color:var(--red);opacity:0.75;font-weight:500;">⚠️ Clinical decision support only. Consult a licensed neurologist.</div>`;
  html += `</div>`;
  return html;
}

function appendMsg(avatar, name, contentHTML, isUser = false, isThinking = false) {
  const msgs = document.getElementById('chat-messages');
  if (!msgs) return; // Handle case where chat messages element doesn't exist
  
  const div  = document.createElement('div');
  div.className = 'msg' + (isUser ? ' user' : '');
  const avatarClass = `msg-avatar ${isUser ? 'user' : 'bot'}${isThinking ? ' thinking' : ''}`;
  div.innerHTML = `
    <div class="${avatarClass}">${avatar}</div>
    <div class="msg-content">
      <div class="msg-name">${name}</div>
      ${contentHTML}
    </div>`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div;
}

function showTyping() {
  startTypingSound();
  return appendMsg(getBotAvatarHTML(), 'NEURORAG AGENT · NOW',
    `<div class="msg-bubble">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>`, false, true);
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const btn   = document.getElementById('send-btn');
  const q     = input.value.trim();
  if (!q) return;

  input.value   = '';
  btn.disabled  = true;

  const sug = document.getElementById('suggestion-row');
  if (sug) sug.style.display = 'none';

  // User msg
  appendMsg(getClinicianAvatarHTML(), 'CLINICIAN · NOW',
    `<div class="msg-bubble">${q}</div>`, true);

  // Typing
  const typing = showTyping();

  try {
    // Call the FastAPI endpoint
    const response = await fetch(`${API_BASE_URL}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: q }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    typing.remove();
    stopTypingSound();

    // Parse the response and display it
    // For now, display the raw response as formatted text
    const formattedResponse = formatRAGResponse(data.response);
    appendMsg(getBotAvatarHTML(), 'NEURORAG AGENT · NOW', formattedResponse);
    
  } catch (error) {
    typing.remove();
    stopTypingSound();
    console.error('Error:', error);
    appendMsg(getBotAvatarHTML(), 'NEURORAG AGENT · NOW',
      `<div class="msg-bubble" style="color:var(--red);">
        ⚠️ Error connecting to RAG system: ${error.message}
      </div>`);
  }

  btn.disabled = false;
}

function formatRAGResponse(response) {
  // Convert Markdown to HTML
  let formatted = response;
  
  // Bold: **text** -> <strong>text</strong>
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Format the RAG response as HTML
  const lines = formatted.split('\n');
  let html = '<div class="msg-bubble">';
  
  let inSection = false;
  let currentSection = '';
  
  for (let line of lines) {
    line = line.trim();
    if (!line) continue;
    
    // Check for numbered sections
    if (line.match(/^\d+\./) || line.match(/^[A-Z]+\s*:/)) {
      if (currentSection) {
        html += `<div class="msg-section-body">${currentSection}</div>`;
        currentSection = '';
      }
      html += `<div class="msg-section-title">${line}</div>`;
      inSection = true;
    } else if (line.toLowerCase().includes('sources used') || line.toLowerCase().includes('source:')) {
      if (currentSection) {
        html += `<div class="msg-section-body">${currentSection}</div>`;
        currentSection = '';
      }
      html += `<div style="margin-top:12px;"><strong>${line}</strong></div>`;
      inSection = false;
    } else if (line.startsWith('*') || line.startsWith('-') || line.startsWith('•')) {
      // Render list text without bullet markers
      const cleanedLine = line.replace(/^[*•-]\s*/, '').trim();
      currentSection += `<div style="margin-left:20px;">${cleanedLine}</div>`;
    } else {
      currentSection += `<div>${line}</div>`;
    }
  }
  
  if (currentSection) {
    html += `<div class="msg-section-body">${currentSection}</div>`;
  }
  
  html += `<div style="margin-top:10px;font-size:11px;color:var(--red);opacity:0.75;font-weight:500;">⚠️ Clinical decision support only. Consult a licensed neurologist.</div>`;
  html += `</div>`;
  
  return html;
}

function fillSuggestion(btn) {
  const input = document.getElementById('chat-input');
  if (input) {
    input.value = btn.textContent.trim();
    input.focus();
  }
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

// ── Analysis ─────────────────────────────────────────────
let uploadedImageData = null;

function handleImageUploadAuto(input) {
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
      uploadedImageData = e.target.result;
      const preview = document.getElementById('image-preview');
      const placeholder = document.getElementById('upload-placeholder');
      const img = document.getElementById('preview-img');
      
      img.src = uploadedImageData;
      placeholder.style.display = 'none';
      preview.style.display = 'block';
      setFieldError('f-image', '');
    };
    
    reader.readAsDataURL(file);
  }
}

function handleImageUpload(input) {
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
      uploadedImageData = e.target.result;
      const preview = document.getElementById('image-preview');
      const img = document.getElementById('preview-img');
      img.src = uploadedImageData;
      preview.style.display = 'block';
    };
    
    reader.readAsDataURL(file);
  }
}

function openCamera() {
  const input = document.getElementById('f-image');
  input.setAttribute('capture', 'environment');
  input.click();
}

function clearImage() {
  uploadedImageData = null;
  document.getElementById('f-image').value = '';
  document.getElementById('image-preview').style.display = 'none';
  document.getElementById('upload-placeholder').style.display = 'block';
  document.getElementById('preview-img').src = '';
  
  // Clear results
  const empty = document.getElementById('result-empty');
  const content = document.getElementById('result-content');
  if (empty) empty.style.display = 'block';
  if (content) content.style.display = 'none';
  setFieldError('f-image', '');
}

function getSeverity(mmse) {
  if (mmse >= 24) return { label: 'Possible MCI',  cls: 'sev-normal' };
  if (mmse >= 18) return { label: 'Mild AD',        cls: 'sev-mild' };
  if (mmse >= 10) return { label: 'Moderate AD',    cls: 'sev-moderate' };
  return               { label: 'Severe AD',        cls: 'sev-moderate' };
}

async function runImageAnalysis() {
  clearAnalysisFieldErrors();

  if (!uploadedImageData) {
    setFieldError('f-image', 'Please upload an image.');
    return;
  }

  // Get required clinical data
  const age = document.getElementById('f-age')?.value;
  const mmse = document.getElementById('f-mmse')?.value;
  const symptoms = document.getElementById('f-symptoms')?.value;

  let hasError = false;
  if (!age) {
    setFieldError('f-age', 'Patient age is required.');
    hasError = true;
  }
  if (!mmse) {
    setFieldError('f-mmse', 'MMSE score is required.');
    hasError = true;
  }
  if (!symptoms || !symptoms.trim()) {
    setFieldError('f-symptoms', 'Symptoms are required.');
    hasError = true;
  }

  if (hasError) {
    return;
  }

  // Show loading state
  const empty = document.getElementById('result-empty');
  const content = document.getElementById('result-content');
  if (empty) empty.style.display = 'none';
  if (content) {
    content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-faint);">🔬 Running test and analyzing brain scan...</div>';
    content.style.display = 'block';
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        age: age,
        mmse: mmse,
        symptoms: symptoms,
        image_data: uploadedImageData
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Format and display the response
    const formattedResponse = formatRAGResponse(data.response);
    
    if (content) {
      content.innerHTML = formattedResponse;
    }
    
  } catch (error) {
    console.error('Error:', error);
    if (content) {
      content.innerHTML = `
        <div style="text-align:center;padding:40px;color:var(--red);">
          ⚠️ Error: ${error.message}
        </div>
      `;
    }
  }
}

async function runAnalysis() {
  const age      = document.getElementById('f-age')?.value;
  const education = document.getElementById('f-edu')?.value;
  const mmse     = document.getElementById('f-mmse')?.value;
  const moca     = document.getElementById('f-moca')?.value;
  const cdr      = document.getElementById('f-cdr')?.value;
  const gds      = document.getElementById('f-gds')?.value;
  const symptoms = document.getElementById('f-symptoms')?.value;

  if (!age && !mmse && !moca && !uploadedImageData) {
    showToast('Please enter age, cognitive score, or upload an MRI image.');
    return;
  }

  // Update score position markers
  if (mmse) {
    const m = document.getElementById('mmse-marker');
    if (m) m.style.left = ((parseInt(mmse) / 30) * 96) + '%';
  }
  if (moca) {
    const m = document.getElementById('moca-marker');
    if (m) m.style.left = ((parseInt(moca) / 30) * 96) + '%';
  }

  // Show loading state
  const empty   = document.getElementById('result-empty');
  const content = document.getElementById('result-content');
  if (empty)   empty.style.display   = 'none';
  if (content) {
    content.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-faint);">🔬 Analyzing patient data...</div>';
    content.style.display = 'block';
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        age: age,
        education: education,
        mmse: mmse,
        moca: moca,
        cdr: cdr,
        gds: gds,
        symptoms: symptoms,
        image_data: uploadedImageData
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Format and display the response
    const formattedResponse = formatRAGResponse(data.response);
    
    if (content) {
      content.innerHTML = formattedResponse;
    }
    
  } catch (error) {
    console.error('Error:', error);
    if (content) {
      content.innerHTML = `
        <div style="text-align:center;padding:40px;color:var(--red);">
          ⚠️ Error: ${error.message}
        </div>
      `;
    }
  }
}

// ── Animate scale bars on load ────────────────────────────
function animateScaleBars() {
  document.querySelectorAll('.scale-fill').forEach(el => {
    const target = el.style.width;
    el.style.width = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => { el.style.width = target; }, 80);
    });
  });
}

// ── Init ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  animateScaleBars();

  const ageEl = document.getElementById('f-age');
  const mmseEl = document.getElementById('f-mmse');
  const symptomsEl = document.getElementById('f-symptoms');

  ageEl?.addEventListener('input', () => setFieldError('f-age', ''));
  mmseEl?.addEventListener('input', () => setFieldError('f-mmse', ''));
  symptomsEl?.addEventListener('input', () => setFieldError('f-symptoms', ''));
});
