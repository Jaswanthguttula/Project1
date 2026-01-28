(() => {
  const API_BASE = ""; // same origin when served by Flask

  const el = (id) => document.getElementById(id);
  
  // ══════════════════════════════════════════════════════════════════════════════
  // SETTINGS & THEME MANAGEMENT
  // ══════════════════════════════════════════════════════════════════════════════
  
  const settingsBtn = el("settingsBtn");
  const settingsModal = el("settingsModal");
  const closeSettings = el("closeSettings");
  const saveSettings = el("saveSettings");
  const languageSelect = el("languageSelect");
  const themeOptions = document.querySelectorAll(".theme-option");
  
  const PREFS_KEY = "clause-detection-prefs";
  
  const translations = {
    en: {
      app_title: "Clause Detection",
      app_subtitle: "AI-Powered Contract Analysis",
      settings_title: "Settings",
      appearance: "Appearance",
      theme_dark: "Dark",
      theme_light: "Light",
      language_pref: "Language Preference",
      language_desc: "Preferred language for UI and extraction highlights.",
      save_changes: "Save Changes",
      upload_section_title: "Upload Contract",
      label_select_file: "Select File",
      label_contract_name: "Contract Name",
      label_version: "Version",
      label_is_amendment: "Is Amendment?",
      amendment_no: "No - Original Contract",
      amendment_yes: "Yes - Amendment",
      label_parent_id: "Parent Contract ID (for amendments)",
      btn_upload: "Upload & Process",
      contracts_section_title: "Your Contracts",
      btn_refresh: "Refresh",
      no_contracts: "No contracts uploaded yet. Upload your first contract above!",
      ask_section_title: "Ask a Question",
      label_contract_id: "Contract ID",
      label_question: "Your Question",
      btn_ask: "Ask AI",
      answer_title: "AI Answer",
      evidence_title: "Supporting Evidence",
      footer_tip: "💡 Tip: For best results, upload contracts in PDF, DOCX, or TXT format. The AI analyzes clauses and can answer questions about obligations, risks, and terms.",
      chat_assistant: "Legal Assistant",
      chat_online: "Online",
      chat_welcome: "Hello! I'm your AI contract assistant. Select a contract and ask me anything about its clauses.",
      chat_placeholder: "Ask about clauses...",
      chat_thinking: "Thinking..."
    },
    es: {
      app_title: "Detección de Cláusulas",
      app_subtitle: "Análisis de Contratos con IA",
      settings_title: "Configuración",
      appearance: "Apariencia",
      theme_dark: "Oscuro",
      theme_light: "Claro",
      language_pref: "Preferencia de Idioma",
      language_desc: "Idioma preferido para la interfaz y los resultados.",
      save_changes: "Guardar Cambios",
      upload_section_title: "Cargar Contrato",
      label_select_file: "Seleccionar Archivo",
      label_contract_name: "Nombre del Contrato",
      label_version: "Versión",
      label_is_amendment: "¿Es una Enmienda?",
      amendment_no: "No - Contrato Original",
      amendment_yes: "Sí - Enmienda",
      label_parent_id: "ID del Contrato Principal (para enmiendas)",
      btn_upload: "Cargar y Procesar",
      contracts_section_title: "Sus Contratos",
      btn_refresh: "Actualizar",
      no_contracts: "Aún no se han cargado contratos. ¡Cargue su primer contrato arriba!",
      ask_section_title: "Hacer una Pregunta",
      label_contract_id: "ID del Contrato",
      label_question: "Su Pregunta",
      btn_ask: "Preguntar a la IA",
      answer_title: "Respuesta de la IA",
      evidence_title: "Evidencia de Apoyo",
      footer_tip: "💡 Sugerencia: Para obtener mejores resultados, cargue contratos en formato PDF, DOCX o TXT.",
      chat_assistant: "Asistente Legal",
      chat_online: "En línea",
      chat_welcome: "¡Hola! Soy su asistente de IA para contratos. Seleccione un contrato y pregúnteme cualquier cosa.",
      chat_placeholder: "Preguntar sobre cláusulas...",
      chat_thinking: "Pensando..."
    },
    fr: {
      app_title: "Détection de Clauses",
      app_subtitle: "Analyse de Contrats par IA",
      settings_title: "Paramètres",
      appearance: "Apparence",
      theme_dark: "Sombre",
      theme_light: "Clair",
      language_pref: "Préférence de Langue",
      language_desc: "Langue préférée pour l'interface et l'extraction.",
      save_changes: "Enregistrer",
      upload_section_title: "Charger un Contrat",
      label_select_file: "Choisir un Fichier",
      label_contract_name: "Nom du Contrat",
      label_version: "Version",
      label_is_amendment: "Est-ce un Avenant ?",
      amendment_no: "Non - Contrat Original",
      amendment_yes: "Oui - Avenant",
      label_parent_id: "ID du Contrat Parent (pour les avenants)",
      btn_upload: "Charger et Traiter",
      contracts_section_title: "Vos Contrats",
      btn_refresh: "Actualiser",
      no_contracts: "Aucun contrat chargé. Chargez votre premier contrat ci-dessus !",
      ask_section_title: "Poser une Question",
      label_contract_id: "ID du Contrat",
      label_question: "Votre Question",
      btn_ask: "Demander à l'IA",
      answer_title: "Réponse de l'IA",
      evidence_title: "Preuves à l'Appui",
      footer_tip: "💡 Conseil : Pour de meilleurs résultats, chargez des contrats au format PDF, DOCX ou TXT.",
      chat_assistant: "Assistant Juridique",
      chat_online: "En ligne",
      chat_welcome: "Bonjour ! Je suis votre assistant IA. Sélectionnez un contrat et posez-moi vos questions.",
      chat_placeholder: "Posez votre question...",
      chat_thinking: "Réflexion..."
    },
    de: {
      app_title: "Klauselerkennung",
      app_subtitle: "KI-gestützte Vertragsanalyse",
      settings_title: "Einstellungen",
      appearance: "Erscheinungsbild",
      theme_dark: "Dunkel",
      theme_light: "Hell",
      language_pref: "Spracheinstellung",
      language_desc: "Bevorzugte Sprache für UI und Extraktion.",
      save_changes: "Speichern",
      upload_section_title: "Vertrag Hochladen",
      label_select_file: "Datei Auswählen",
      label_contract_name: "Vertragsname",
      label_version: "Version",
      label_is_amendment: "Ist es ein Nachtrag?",
      amendment_no: "Nein - Originalvertrag",
      amendment_yes: "Ja - Nachtrag",
      label_parent_id: "Parent-Vertrags-ID (für Nachträge)",
      btn_upload: "Hochladen & Verarbeiten",
      contracts_section_title: "Ihre Verträge",
      btn_refresh: "Aktualisieren",
      no_contracts: "Noch keine Verträge hochgeladen. Laden Sie Ihren ersten Vertrag hoch!",
      ask_section_title: "Eine Frage Stellen",
      label_contract_id: "Vertrags-ID",
      label_question: "Ihre Frage",
      btn_ask: "KI Fragen",
      answer_title: "KI-Antwort",
      evidence_title: "Unterstützende Belege",
      footer_tip: "💡 Tipp: Für beste Ergebnisse laden Sie Verträge im PDF-, DOCX- oder TXT-Format hoch.",
      chat_assistant: "Rechtsassistent",
      chat_online: "Online",
      chat_welcome: "Hallo! Ich bin Ihr KI-Vertragsassistent. Wählen Sie einen Vertrag aus und stellen Sie Fragen.",
      chat_placeholder: "Fragen stellen...",
      chat_thinking: "Nachdenken..."
    },
    hi: {
      app_title: "क्लॉज डिटेक्शन",
      app_subtitle: "AI-संचालित अनुबंध विश्लेषण",
      settings_title: "सेटिंग्स",
      appearance: "दिखावट",
      theme_dark: "डार्क",
      theme_light: "लाइट",
      language_pref: "भाषा वरीयता",
      language_desc: "UI और एक्सट्रैक्शन के लिए पसंदीदा भाषा।",
      save_changes: "परिवर्तन सहेजें",
      upload_section_title: "अनुबंध अपलोड करें",
      label_select_file: "फ़ाइल चुनें",
      label_contract_name: "अनुबंध का नाम",
      label_version: "संस्करण",
      label_is_amendment: "क्या यह संशोधन है?",
      amendment_no: "नहीं - मूल अनुबंध",
      amendment_yes: "हाँ - संशोधन",
      label_parent_id: "पैरेंट अनुबंध ID (संशोधन के लिए)",
      btn_upload: "अपलोड और प्रोसेस",
      contracts_section_title: "आपके अनुबंध",
      btn_refresh: "रिफ्रेश",
      no_contracts: "अभी तक कोई अनुबंध अपलोड नहीं किया गया है। ऊपर अपना पहला अनुबंध अपलोड करें!",
      ask_section_title: "एक प्रश्न पूछें",
      label_contract_id: "अनुबंध ID",
      label_question: "आपका प्रश्न",
      btn_ask: "AI से पूछें",
      answer_title: "AI उत्तर",
      evidence_title: "सहायक साक्ष्य",
      footer_tip: "💡 टिप: सर्वोत्तम परिणामों के लिए, PDF, DOCX, या TXT प्रारूप में अनुबंध अपलोड करें।",
      chat_assistant: "कानूनी सहायक",
      chat_online: "ऑनलाइन",
      chat_welcome: "नमस्ते! मैं आपका अनुबंध सहायक हूँ। एक अनुबंध चुनें और मुझसे कुछ भी पूछें।",
      chat_placeholder: "पूछें...",
      chat_thinking: "सोच रहा हूँ..."
    }
  };

  let currentPrefs = {
    theme: "dark",
    language: "en"
  };

  // Load preferences from localStorage
  function loadPrefs() {
    const saved = localStorage.getItem(PREFS_KEY);
    if (saved) {
      try {
        currentPrefs = { ...currentPrefs, ...JSON.parse(saved) };
      } catch (e) {
        console.error("Failed to parse saved preferences", e);
      }
    } else {
      // Auto-detect theme if no saved preference
      if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
        currentPrefs.theme = "light";
      }
    }
    applyPrefs();
  }

  // Update UI Text based on language
  function updateUITranslations() {
    const lang = currentPrefs.language;
    const langData = translations[lang] || translations.en;
    
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.dataset.i18n;
      if (langData[key]) {
        el.textContent = langData[key];
      }
    });

    // Update placeholders
    const placeholders = {
      en: {
        name: "e.g., Service Agreement 2024",
        parent_id: "Enter parent contract ID if this is an amendment",
        ask_id: "Enter contract ID from list above",
        question: "e.g., What are the termination conditions?"
      },
      es: {
        name: "ej., Acuerdo de Servicio 2024",
        parent_id: "Ingrese el ID del contrato principal",
        ask_id: "Ingrese el ID del contrato de la lista",
        question: "ej., ¿Cuáles son las condiciones de terminación?"
      },
      fr: {
        name: "ex., Contrat de Service 2024",
        parent_id: "Entrez l'ID du contrat parent",
        ask_id: "Entrez l'ID du contrat dans la liste",
        question: "ex., Quelles sont les conditions de résiliation ?"
      },
      de: {
        name: "z.B. Servicevereinbarung 2024",
        parent_id: "Parent-Vertrags-ID eingeben",
        ask_id: "Vertrags-ID aus der Liste eingeben",
        question: "z.B. Was sind die Kündigungsbedingungen?"
      },
      hi: {
        name: "जैसे, सेवा अनुबंध 2024",
        parent_id: "पैरेंट अनुबंध ID दर्ज करें",
        ask_id: "सूची से अनुबंध ID दर्ज करें",
        question: "जैसे, समाप्ति की शर्तें क्या हैं?"
      }
    };

    const pData = placeholders[lang] || placeholders.en;
    if (el("name")) el("name").placeholder = pData.name;
    if (el("parent_contract_id")) el("parent_contract_id").placeholder = pData.parent_id;
    if (el("askContractId")) el("askContractId").placeholder = pData.ask_id;
    if (el("question")) el("question").placeholder = pData.question;

    // Update chatbot placeholder
    if (el("chatInput")) {
      const chatPlaceholder = langData.chat_placeholder || "Ask about clauses...";
      el("chatInput").placeholder = chatPlaceholder;
    }
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // CHATBOT LOGIC
  // ══════════════════════════════════════════════════════════════════════════════

  const chatTrigger = el("chatTrigger");
  const chatWindow = el("chatWindow");
  const closeChat = el("closeChat");
  const chatInput = el("chatInput");
  const sendChat = el("sendChat");
  const chatMessages = el("chatMessages");

  function addMessage(text, type = "system") {
    const div = document.createElement("div");
    div.className = `message ${type}`;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
  }

  if (chatTrigger) {
    chatTrigger.addEventListener("click", () => {
      chatWindow.classList.toggle("active");
    });
  }

  if (closeChat) {
    closeChat.addEventListener("click", () => {
      chatWindow.classList.remove("active");
    });
  }

  async function handleChat() {
    const question = chatInput.value.trim();
    const contractId = Number(el("askContractId").value);
    
    if (!question) return;
    
    // Add user message
    addMessage(question, "user");
    chatInput.value = "";
    
    if (!contractId) {
      addMessage("Please select a contract first by clicking 'Use for questions' in the list above.", "system");
      return;
    }
    
    const thinkingMsg = addMessage(translations[currentPrefs.language]?.chat_thinking || "Thinking...", "system");
    
    try {
      const payload = { question, contract_id: contractId, asked_by: "chatbot" };
      const res = await api("/api/questions/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      thinkingMsg.textContent = res.answer || "I couldn't find a clear answer for that.";
      
      // If there's high confidence, show a small hint about evidence
      if (res.confidence > 0.7 && res.evidence_clauses?.length > 0) {
        const hint = document.createElement("div");
        hint.style.fontSize = "11px";
        hint.style.marginTop = "5px";
        hint.style.opacity = "0.7";
        hint.textContent = `(Found in ${res.evidence_clauses[0].document_name})`;
        thinkingMsg.appendChild(hint);
      }
    } catch (err) {
      thinkingMsg.textContent = `Error: ${err.message}`;
    }
  }

  if (sendChat) {
    sendChat.addEventListener("click", handleChat);
  }

  if (chatInput) {
    chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") handleChat();
    });
  }

  // Apply preferences to UI
  function applyPrefs() {
    document.documentElement.setAttribute("data-theme", currentPrefs.theme);
    languageSelect.value = currentPrefs.language;
    
    // Update theme option active state
    themeOptions.forEach(opt => {
      opt.classList.toggle("active", opt.dataset.themeChoice === currentPrefs.theme);
    });

    // Update UI text
    updateUITranslations();

    // Save to localStorage
    localStorage.setItem(PREFS_KEY, JSON.stringify(currentPrefs));
  }

  // Open settings modal
  if (settingsBtn) {
    settingsBtn.addEventListener("click", () => {
      settingsModal.classList.add("active");
    });
  }

  // Close settings modal
  if (closeSettings) {
    closeSettings.addEventListener("click", () => {
      settingsModal.classList.remove("active");
    });
  }

  // Click outside to close modal
  settingsModal.addEventListener("click", (e) => {
    if (e.target === settingsModal) {
      settingsModal.classList.remove("active");
    }
  });

  // Theme selection
  themeOptions.forEach(opt => {
    opt.addEventListener("click", () => {
      currentPrefs.theme = opt.dataset.themeChoice;
      applyPrefs();
    });
  });

  // Save changes
  if (saveSettings) {
    saveSettings.addEventListener("click", () => {
      currentPrefs.language = languageSelect.value;
      applyPrefs();
      settingsModal.classList.remove("active");
      
      // Visual feedback
      const originalText = saveSettings.textContent;
      saveSettings.textContent = "Saved!";
      setTimeout(() => { saveSettings.textContent = originalText; }, 1500);
    });
  }

  // Initialize
  loadPrefs();
  
  // ══════════════════════════════════════════════════════════════════════════════
  // APP LOGIC
  // ══════════════════════════════════════════════════════════════════════════════
  
  const healthStatus = el("healthStatus");
  const uploadForm = el("uploadForm");
  const uploadMsg = el("uploadMsg");
  const contractsList = el("contractsList");
  const refreshContracts = el("refreshContracts");

  // Dashboard charts
  let riskChartInstance = null;
  let typeChartInstance = null;

  async function updateDashboard(contractId) {
    if (!contractId) return;
    
    const dashboardSection = el("dashboardSection");
    if (dashboardSection) dashboardSection.style.display = "block";
    if (el("dashboardContractName")) el("dashboardContractName").textContent = `Loading Contract #${contractId}...`;

    try {
      const contract = await api(`/api/contracts/${contractId}`, { method: "GET" });
      if (el("dashboardContractName")) el("dashboardContractName").textContent = contract.name || `Contract #${contractId}`;

      const clauses = contract.clauses || [];
      
      // Calculate Risk Distribution
      const riskCounts = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
      clauses.forEach(c => {
        const r = String(c.risk_level || "LOW").toUpperCase();
        if (riskCounts[r] !== undefined) riskCounts[r]++;
        else riskCounts.LOW++;
      });

      // Update Stat Cards (New)
      if (el("criticalCount")) el("criticalCount").textContent = riskCounts.CRITICAL;
      if (el("highCount")) el("highCount").textContent = riskCounts.HIGH;
      if (el("mediumCount")) el("mediumCount").textContent = riskCounts.MEDIUM;
      if (el("lowCount")) el("lowCount").textContent = riskCounts.LOW;

      // Calculate Type Distribution
      const typeCounts = {};
      clauses.forEach(c => {
        const t = c.clause_type || "GENERAL";
        typeCounts[t] = (typeCounts[t] || 0) + 1;
      });

      // Calculate Health Score (100 - weighted risks)
      // Scoring formula: Critical=-25, High=-15, Medium=-5, Low=0
      // Normalizing based on total clauses to avoid score plummeting for small documents
      let penalty = 0;
      penalty += riskCounts.CRITICAL * 25;
      penalty += riskCounts.HIGH * 15;
      penalty += riskCounts.MEDIUM * 5;
      
      const maxPossiblePenalty = Math.max(1, clauses.length * 15); // Assume average high risk as "bad"
      const scoreRatio = penalty / maxPossiblePenalty;
      const healthScore = Math.max(0, Math.min(100, 100 - (scoreRatio * 100)));
      const roundedScore = Math.round(healthScore);
      
      const scoreValueEl = el("healthScoreValue");
      const progressBar = el("healthProgressBar");
      const scoreDesc = el("healthScoreDesc");

      if (scoreValueEl) {
        scoreValueEl.textContent = roundedScore;
      }

      // Progress bar animation
      if (progressBar) {
        const circumference = 2 * Math.PI * 80;
        const offset = circumference - (roundedScore / 100) * circumference;
        progressBar.style.strokeDashoffset = offset;

        // Color adjustment based on score
        let color = "var(--accent-blue)";
        let desc = "Excellent health with minimal risk exposure.";
        
        if (roundedScore < 40) {
          color = "var(--accent-pink)";
          desc = "Critical risks detected. Immediate legal review recommended.";
        } else if (roundedScore < 70) {
          color = "var(--accent-orange)";
          desc = "Moderate risk exposure. Review high-risk clauses carefully.";
        } else if (roundedScore < 90) {
          color = "var(--accent-green)";
          desc = "Good health. Some minor improvements possible.";
        }

        progressBar.style.stroke = color;
        if (scoreValueEl) scoreValueEl.style.color = color;
        if (scoreDesc) scoreDesc.textContent = desc;
      }

      renderRiskChart(riskCounts);
      renderTypeChart(typeCounts);

    } catch (e) {
      console.error("Dashboard update failed", e);
    }
  }

  function renderRiskChart(counts) {
    const canvas = el("riskChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (riskChartInstance) riskChartInstance.destroy();

    riskChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: Object.keys(counts),
        datasets: [{
          data: Object.values(counts),
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#ec4899'],
          borderWidth: 0,
          hoverOffset: 15
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { 
            position: 'bottom', 
            labels: { 
              color: '#94a3b8', 
              padding: 20,
              font: { size: 11, weight: '500' },
              usePointStyle: true
            } 
          }
        },
        cutout: '75%'
      }
    });
  }

  function renderTypeChart(counts) {
    const canvas = el("typeChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (typeChartInstance) typeChartInstance.destroy();

    typeChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(counts),
        datasets: [{
          label: 'Clauses',
          data: Object.values(counts),
          backgroundColor: 'rgba(0, 212, 255, 0.4)',
          borderColor: '#00d4ff',
          borderWidth: 2,
          borderRadius: 8,
          barThickness: 20
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { 
            beginAtZero: true, 
            grid: { color: 'rgba(148, 163, 184, 0.1)', drawBorder: false }, 
            ticks: { color: '#94a3b8', font: { size: 10 } } 
          },
          x: { 
            grid: { display: false }, 
            ticks: { color: '#94a3b8', font: { size: 9 }, maxRotation: 45, minRotation: 45 } 
          }
        }
      }
    });
  }

  const askForm = el("askForm");
  const askMsg = el("askMsg");
  const answerCard = el("answerCard");
  const answerEl = el("answer");
  const evidenceEl = el("evidence");
  const confidenceEl = el("confidence");

  async function api(path, options) {
    const res = await fetch(API_BASE + path, options);
    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");

    let body;
    if (isJson) body = await res.json();
    else body = await res.text();

    if (!res.ok) {
      const msg = (body && body.error) ? body.error : (typeof body === "string" ? body : JSON.stringify(body));
      throw new Error(msg || `Request failed: ${res.status}`);
    }
    return body;
  }

  function setStatus(ok, text) {
    healthStatus.textContent = text;
    healthStatus.style.color = ok ? "#9ff3c7" : "#ffb3b3";
    healthStatus.style.borderColor = ok ? "rgba(159,243,199,.25)" : "rgba(255,179,179,.25)";
  }

  async function checkHealth() {
    try {
      const data = await api("/health", { method: "GET" });
      setStatus(true, `API healthy • ${new Date(data.timestamp).toLocaleString()}`);
    } catch (e) {
      setStatus(false, `API not reachable • ${e.message}`);
    }
  }

  function renderContracts(items) {
    contractsList.innerHTML = "";
    if (!items || items.length === 0) {
      contractsList.innerHTML = `<div class="muted">No contracts yet. Upload one above.</div>`;
      return;
    }

    for (const c of items) {
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML = `
        <div class="row space">
          <div>
            <div style="font-size: 16px; font-weight: 700;">📄 ${escapeHtml(c.name || "(unnamed)")}</div>
            <div class="meta" style="margin-top: 4px;">ID: #${c.id} • v${escapeHtml(String(c.version || "1.0"))}</div>
          </div>
          <div class="pill" style="background: ${c.is_amendment ? 'rgba(139, 92, 246, 0.15)' : 'rgba(16, 185, 129, 0.15)'}; color: ${c.is_amendment ? 'var(--accent-purple)' : 'var(--accent-green)'}; border-color: ${c.is_amendment ? 'var(--accent-purple)' : 'var(--accent-green)'}">
            ${c.is_amendment ? 'Amendment' : 'Original'}
          </div>
        </div>
        <div class="meta" style="margin: 12px 0; padding: 8px; background: rgba(0,0,0,0.2); border-radius: 6px;">
          📅 Created: ${c.created_at ? new Date(c.created_at).toLocaleDateString() : 'N/A'} • 📁 ${c.clause_count || 0} Clauses
        </div>
        <div class="row" style="gap: 12px;">
          <button class="btn" style="flex: 1; padding: 10px;" data-select="${c.id}">
            📊 Analyze & Ask
          </button>
          <button class="btn secondary" style="flex: 1; padding: 10px; border-color: var(--accent-blue); color: var(--accent-blue);" data-history="${c.id}">
            🕰️ Time Machine
          </button>
        </div>
      `;
      contractsList.appendChild(div);
    }

    contractsList.querySelectorAll("button[data-select]").forEach(btn => {
      btn.addEventListener("click", () => {
        const cid = btn.getAttribute("data-select");
        el("askContractId").value = cid;
        el("question").focus();
        updateDashboard(cid);
      });
    });

    contractsList.querySelectorAll("button[data-history]").forEach(btn => {
      btn.addEventListener("click", () => {
        showHistory(btn.getAttribute("data-history"));
      });
    });
  }

  async function loadContracts() {
    try {
      const data = await api("/api/contracts", { method: "GET" });
      const items = Array.isArray(data) ? data : (data.contracts || []);
      renderContracts(items);
    } catch (e) {
      contractsList.innerHTML = `<div class="muted">Failed to load contracts: ${escapeHtml(e.message)}</div>`;
    }
  }

  function renderEvidence(evidence) {
    evidenceEl.innerHTML = "";
    if (!evidence || evidence.length === 0) {
      evidenceEl.innerHTML = `<div class="muted">No evidence returned.</div>`;
      return;
    }

    for (const ev of evidence) {
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML = `
        <div class="row space">
          <div><strong>${escapeHtml(ev.document_name || "Document")}</strong> • clause #${ev.clause_id} • score ${Number(ev.relevance_score || 0).toFixed(3)}</div>
          <button class="btn" style="padding: 6px 12px; font-size: 11px; background: var(--gradient-secondary);" data-fix="${ev.clause_id}"> ✨ Fix Clause</button>
        </div>
        <div class="meta">type: ${escapeHtml(ev.clause_type || "")}${ev.section_number ? ` • section: ${escapeHtml(ev.section_number)}` : ""}${ev.page_number ? ` • page: ${ev.page_number}` : ""}</div>
        <div style="margin-top:8px" class="pre">${escapeHtml(ev.text || "")}</div>
      `;
      evidenceEl.appendChild(div);
    }

    evidenceEl.querySelectorAll("[data-fix]").forEach(btn => {
      btn.addEventListener("click", () => fixClause(btn.dataset.fix));
    });
  }

  function escapeHtml(str) {
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    uploadMsg.textContent = "Uploading…";

    const fileInput = el("file");
    const file = fileInput.files?.[0];
    if (!file) {
      uploadMsg.textContent = "Please select a file.";
      return;
    }

    const form = new FormData();
    form.append("file", file);

    const name = el("name").value.trim();
    const version = el("version").value.trim();
    const is_amendment = el("is_amendment").value;
    const parent_contract_id = el("parent_contract_id").value.trim();

    if (name) form.append("name", name);
    if (version) form.append("version", version);
    form.append("is_amendment", is_amendment);
    if (parent_contract_id) form.append("parent_contract_id", parent_contract_id);

    try {
      const result = await api("/api/contracts/upload", { method: "POST", body: form });
      uploadMsg.textContent = `Done. Contract id: ${result.contract_id}. Total clauses: ${result.total_clauses}.`;
      await loadContracts();
      el("askContractId").value = result.contract_id;
      updateDashboard(result.contract_id);
    } catch (err) {
      uploadMsg.textContent = `Upload failed: ${err.message}`;
    }
  });

  askForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    askMsg.textContent = "Thinking…";
    answerCard.style.display = "none";

    const contractId = Number(el("askContractId").value);
    const question = el("question").value.trim();
    if (!contractId || !question) {
      askMsg.textContent = "Please provide contract id and a question.";
      return;
    }

    try {
      const payload = { question, contract_id: contractId, top_k: 5, asked_by: "frontend" };
      const res = await api("/api/questions/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      confidenceEl.textContent = `confidence ${(Number(res.confidence || 0) * 100).toFixed(1)}%`;
      answerEl.textContent = res.answer || "";
      renderEvidence(res.evidence_clauses || []);
      answerCard.style.display = "block";
      askMsg.textContent = "";
    } catch (err) {
      askMsg.textContent = `Ask failed: ${err.message}`;
    }
  });

  refreshContracts.addEventListener("click", loadContracts);

  // ══════════════════════════════════════════════════════════════════════════════
  // TIME MACHINE & FIXER LOGIC
  // ══════════════════════════════════════════════════════════════════════════════

  const historyModal = el("historyModal");
  const contractTimeline = el("contractTimeline");
  const diffView = el("diffView");
  const diffResults = el("diffResults");
  
  const fixerModal = el("fixerModal");
  const originalClauseText = el("originalClauseText");
  const suggestedClauseText = el("suggestedClauseText");
  const fixRationale = el("fixRationale");

  // Close handlers
  el("closeHistory").addEventListener("click", () => historyModal.classList.remove("active"));
  el("closeFixer").addEventListener("click", () => fixerModal.classList.remove("active"));
  el("backToTimeline").addEventListener("click", () => {
    diffView.style.display = "none";
    contractTimeline.style.display = "block";
  });

  async function showHistory(contractId) {
    try {
      const history = await api(`/api/contracts/${contractId}/history`, { method: "GET" });
      contractTimeline.innerHTML = "";
      diffView.style.display = "none";
      contractTimeline.style.display = "block";

      history.forEach((item, index) => {
        const div = document.createElement("div");
        div.className = "timeline-item";
        div.innerHTML = `
          <div class="timeline-dot ${item.id == contractId ? 'active' : ''}"></div>
          <div class="item" style="cursor: default;">
            <div class="row space">
              <div>
                <strong>${item.name}</strong> 
                <span class="pill" style="margin-left: 10px; font-size: 10px;">v${item.version}</span>
              </div>
              <div class="meta">${new Date(item.created_at).toLocaleDateString()}</div>
            </div>
            <div class="meta">${item.is_amendment ? 'Amendment' : 'Original Contract'} • ${item.clause_count} clauses</div>
            <div class="row" style="margin-top: 15px;">
              ${index > 0 ? `<button class="btn secondary" style="padding: 6px 12px; font-size: 11px;" data-compare="${item.id}" data-prev="${history[index-1].id}">Compare with Previous</button>` : ''}
            </div>
          </div>
        `;
        contractTimeline.appendChild(div);
      });

      contractTimeline.querySelectorAll("[data-compare]").forEach(btn => {
        btn.addEventListener("click", () => {
          compareVersions(btn.dataset.prev, btn.dataset.compare);
        });
      });

      historyModal.classList.add("active");
    } catch (e) {
      alert("Failed to load history: " + e.message);
    }
  }

  async function compareVersions(id1, id2) {
    try {
      const data = await api(`/api/contracts/compare/${id1}/${id2}`, { method: "GET" });
      diffResults.innerHTML = "";
      el("diffTitle").textContent = `Changes: ${data.contract1.name} → ${data.contract2.name}`;

      if (data.changes.length === 0) {
        diffResults.innerHTML = `<div class="muted" style="padding: 20px; text-align: center;">No changes detected between these versions.</div>`;
      } else {
        data.changes.forEach(change => {
          const div = document.createElement("div");
          div.className = "item";
          div.innerHTML = `
            <div class="row space">
              <strong>Section ${change.path}</strong>
              <span class="pill" style="font-size: 10px; text-transform: uppercase;">${change.status}</span>
            </div>
            <div class="pre" style="margin-top: 10px; font-size: 13px;">${change.diff_visual}</div>
          `;
          diffResults.appendChild(div);
        });
      }

      contractTimeline.style.display = "none";
      diffView.style.display = "block";
    } catch (e) {
      alert("Comparison failed: " + e.message);
    }
  }

  async function fixClause(clauseId) {
    try {
      fixerModal.classList.add("active");
      originalClauseText.textContent = "Loading original...";
      suggestedClauseText.textContent = "Analyzing for optimization...";
      fixRationale.textContent = "AI is thinking...";

      const data = await api(`/api/clauses/${clauseId}/fix`, { method: "POST" });
      
      originalClauseText.textContent = data.original;
      suggestedClauseText.textContent = data.suggestion;
      fixRationale.textContent = data.rationale;
      
      el("copyFixBtn").onclick = () => {
        navigator.clipboard.writeText(data.suggestion);
        const originalText = el("copyFixBtn").textContent;
        el("copyFixBtn").textContent = "Copied!";
        setTimeout(() => el("copyFixBtn").textContent = originalText, 2000);
      };

    } catch (e) {
      alert("Fix failed: " + e.message);
      fixerModal.classList.remove("active");
    }
  }

  // initial load
  checkHealth();
  loadContracts();
})();
