/* ═══════════════════════════════════════════════════
   ProtoQol — Nomad Cyberpunk v3.8 (B2B MVP)
   Neural Integrity Flow + Live Terminal Analytics
   ═══════════════════════════════════════════════════ */

;(() => {
    'use strict';

    const CONFIG = Object.freeze({
        API_BASE: (window.location.hostname === 'localhost' || window.location.hostname === '')
            ? 'http://localhost:8000'
            : '/api',
        POLL_INTERVAL_MS: 5000,
        B2B_KEY: 'PQ_LIVE_DEMO_SECRET',
        TYPING_SPEED_MS: 15,
    });

    let protocolState = {
        totalImpact: 14208,
        isProcessing: false,
        selectedMissionId: '',
        activeCampaigns: [],
    };

    function $(id) { return document.getElementById(id); }
    function sanitize(str) { return String(str).replace(/<[^>]*>/g, '').trim(); }

    async function apiFetch(url, options = {}) {
        const headers = { ...options.headers, "X-API-Key": CONFIG.B2B_KEY };
        try {
            const resp = await fetch(url, { ...options, headers });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return await resp.json();
        } catch (err) {
            console.error("[API_ERROR]", err);
            throw err;
        }
    }

    // ═══════════════════════════════════════
    // TERMINAL & ANALYTICS
    // ═══════════════════════════════════════

    async function loadMockHistory() {
        try {
            const data = await apiFetch(`${CONFIG.API_BASE}/api/v1/dashboard/stats`);
            if (data && data.recent_activity) {
                // Populate terminal with the 5 mock transactions
                const terminal = $('live-terminal');
                if(!terminal) return;
                
                terminal.innerHTML = ''; // Clear initial
                data.recent_activity.reverse().forEach((tx, i) => {
                    const line = document.createElement('div');
                    line.className = 'lt-line';
                    const hash = tx.tx_hash ? tx.tx_hash.substring(0, 16) + '...' : 'CRYSTALLIZING...';
                    const color = tx.verdict === 'ADAL' ? 'lt-text--cyan' : 'lt-text--error';
                    
                    // Determine chain status class
                    let statusClass = 'status--confirmed';
                    if (!tx.tx_hash || tx.tx_hash === 'PENDING_CONFIRMATION') statusClass = 'status--crystallizing';
                    if (tx.verdict === 'FAILED') statusClass = 'status--failed';

                    const timeStr = tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString() : 'NOW';
                    
                    line.innerHTML = `
                        <span class="lt-prompt">></span> 
                        <span class="lt-text">[${timeStr}] | TX: <span class="${statusClass}">${hash}</span> | VERDICT: <span class="${color}">${tx.verdict}</span></span>
                        <button class="inspect-btn" data-logs='${tx.ai_dialogue || "[]"}'>INSPECT_AI</button>
                    `;
                    terminal.appendChild(line);
                });
                
                protocolState.totalImpact = data.total_impact;
                const repScore = $('rep-score');
                if(repScore) repScore.textContent = data.total_impact.toLocaleString();
            }
        } catch (err) {
            console.warn("Could not sync with B2B History. Running in offline demo mode.");
        }
    }

    function setTerminalLine(lineNum, text, cssClass = '', ai_dialogue = '[]') {
        const line = document.createElement('div');
        line.className = 'lt-line';
        const logsStr = typeof ai_dialogue === 'string' ? ai_dialogue : JSON.stringify(ai_dialogue);
        
        line.innerHTML = `
            <span class="lt-prompt">></span> 
            <span class="lt-text ${cssClass}">${sanitize(text)}</span>
            ${cssClass.includes('cyan') || cssClass.includes('error') ? `<button class="inspect-btn" data-logs='${logsStr}'>INSPECT_AI</button>` : ''}
        `;
        const terminal = $('live-terminal');
        if (terminal) {
            terminal.appendChild(line);
            terminal.scrollTop = terminal.scrollHeight;
            if (terminal.children.length > 20) terminal.removeChild(terminal.firstChild);
        }
    }

    // ═══════════════════════════════════════
    // X-RAY INSPECTOR LOGIC
    // ═══════════════════════════════════════

    async function openConsensusInspector(logs) {
        const body = $('ci-body');
        const loader = $('ci-loader');
        const inspector = $('consensus-inspector');
        const overlay = $('inspector-overlay');
        
        if (!body || !inspector || !overlay) return;
        
        // Reset and Show Loader
        inspector.classList.add('active');
        overlay.classList.add('active');
        if(loader) loader.style.display = 'flex';
        
        // Clear previous lines (keep loader)
        const lines = body.querySelectorAll('.ci-line');
        lines.forEach(l => l.remove());
        
        await new Promise(r => setTimeout(r, 800)); // Cinematic "Deciphering" delay
        if(loader) loader.style.display = 'none';

        const rawLogs = logs || "[]";
        const dialogue = Array.isArray(rawLogs) ? rawLogs : JSON.parse(rawLogs);
        
        for (const entry of dialogue) {
            const line = document.createElement('div');
            line.className = 'ci-line';
            line.innerHTML = `<span class="ci-agent">${entry.node}</span> <span class="ci-text"></span>`;
            body.appendChild(line);
            
            const textSpan = line.querySelector('.ci-text');
            const message = entry.wisdom || entry.reasoning || "Evaluation complete. Node integrity healthy.";
            
            // Typewriter effect
            for (let i = 0; i < message.length; i++) {
                textSpan.textContent += message[i];
                await new Promise(r => setTimeout(r, 8));
                body.scrollTop = body.scrollHeight;
            }
            await new Promise(r => setTimeout(r, 300)); // Pause between agents
        }
    }

    // ═══════════════════════════════════════
    // NEURAL FLOW ANIMATIONS
    // ═══════════════════════════════════════

    async function animateNode(nodeId, duration = 800) {
        const el = $(nodeId);
        if (!el) return;
        el.classList.add('active');
        el.style.transform = 'scale(1.2)';
        await new Promise(r => setTimeout(r, duration));
        el.classList.remove('active');
        el.style.transform = 'scale(1)';
    }

    async function triggerNeuralFlow(isAdal = true) {
        const chip = $('ht-chip');
        if (chip) { chip.textContent = '● JUDGING'; chip.classList.add('judging'); }

        // Start Sequence
        await animateNode('node-origin', 600);
        
        // AI Council Processing
        const council = [animateNode('biy-01', 1200), animateNode('biy-02', 1400), animateNode('biy-03', 1000)];
        setTerminalLine(0, "INITIATING_COUNCIL_CONSENSUS...", "lt-text--gold");
        await Promise.all(council);

        // Validator Finality
        await animateNode('node-validator', 800);
        
        if (isAdal) {
            await animateNode('node-solana', 1000);
            setTerminalLine(0, "ETCHING_SUCCESSFUL: ON_CHAIN_CRYSTALLIZED", "lt-text--cyan");
        } else {
            setTerminalLine(0, "ETCHING_DENIED: INTEGRITY_FILTER_ACTIVE", "lt-text--error");
        }

        if (chip) { chip.textContent = '● IDLE'; chip.classList.remove('judging'); }
    }

    // ═══════════════════════════════════════
    // SUBMIT HANDLER
    // ═══════════════════════════════════════

    async function handleSubmit() {
        if (protocolState.isProcessing) return;
        
        const description = $('deed-description')?.value.trim();
        const missionId = $('mission-select')?.value;
        const submitBtn = $('submit-deed');

        if (!description || description.length < 15) return;
        if (!missionId) {
            setTerminalLine(0, "ERROR: MISSION_MANDATE_REQUIRED", "lt-text--error");
            return;
        }

        // [GUARDRAIL] Lock UI
        protocolState.isProcessing = true;
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = "⏳ BIY CONSENSUS IN PROGRESS...";
        }

        setTerminalLine(0, "--- NEW_INTEGRITY_REQUEST ---");

        try {
            const formData = new FormData();
            formData.append('description', description);
            formData.append('mission_id', missionId);
            formData.append('api_key', CONFIG.B2B_KEY);

            // Trigger visual flow sequence
            const apiPromise = apiFetch(`${CONFIG.API_BASE}/api/v1/etch_deed`, { 
                method: 'POST', 
                body: formData 
            });
            
            await triggerNeuralFlow(true); 
            
            const result = await apiPromise;
            const success = result.status === 'crystalized' || result.status === 'ADAL' || result.status === 'success';
            
            if (success) {
                setTerminalLine(0, `CRYSTALLIZED: TX ${result.tx_hash?.substring(0,16)}...`, "lt-text--cyan", result.ai_dialogue);
                protocolState.totalImpact += result.impact_points || 0;
                
                const score = protocolState.totalImpact.toLocaleString();
                if($('rep-score')) $('rep-score').textContent = score;
                if($('stat-impact')) $('stat-impact').textContent = score;
            } else {
                setTerminalLine(0, `DENIED: ${result.verdict} | ${result.wisdom || result.auditor_wisdom}`, "lt-text--error", result.ai_dialogue);
            }
        } catch (err) {
            // [GUARDRAIL] Graceful Error Rendering
            setTerminalLine(0, "[SYSTEM ALERT] CONNECTION REFUSED - ORACLE OFFLINE", "lt-text--error");
            setTerminalLine(0, "> CONNECTION_REFUSED: FALLBACK_ENGAGED", "lt-text--gold");
        } finally {
            // [GUARDRAIL] Unlock UI
            protocolState.isProcessing = false;
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = "⟁ ETCH MORE";
            }
        }
    }

    // ═══════════════════════════════════════
    // B2B CAMPAIGN LOGIC
    // ═══════════════════════════════════════

    async function handleCampaignSubmit(e) {
        e.preventDefault();
        const fund = $('camp-fund-name').value;
        const title = $('camp-title').value;
        const reqs = $('camp-requirements').value;
        const reward = $('camp-reward').value;

        try {
            const res = await apiFetch(`${CONFIG.API_BASE}/api/v1/campaigns`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fund_name: fund, title, requirements: reqs, reward: parseInt(reward) })
            });

            if (res.status === 'success') {
                setTerminalLine(0, `CONTRACT_LAUNCHED: ${title.toUpperCase()}`, "lt-text--cyan");
                toggleModal('campaign-modal', false);
                await loadCampaigns(); // Refresh list
            }
        } catch (err) {
            alert("Campaign Creation Failed. Check console.");
        }
    }

    async function loadCampaigns() {
        try {
            const data = await apiFetch(`${CONFIG.API_BASE}/api/v1/gateway/missions`);
            const select = $('mission-select');
            if (select) {
                select.innerHTML = '<option value="">-- SELECT MANDATE --</option>';
                Object.keys(data).forEach(id => {
                    const mission = data[id];
                    const opt = document.createElement('option');
                    opt.value = id;
                    opt.textContent = `[${mission.client}] ${mission.requirements.substring(0,30)}...`;
                    select.appendChild(opt);
                });
            }
        } catch (err) { console.warn("Missions sync failed."); }
    }

    function createSparks(e) {
        const target = e.currentTarget || e.target;
        const rect = target.getBoundingClientRect();
        for (let i = 0; i < 12; i++) {
            const spark = document.createElement('div');
            spark.className = 'spark';
            spark.style.width = '1px';
            spark.style.height = '1px';
            spark.style.background = '#FFFFFF';
            spark.style.boxShadow = '0 0 5px #FFFFFF, 0 0 10px #B371FF';
            
            // Random pos within target
            spark.style.left = (rect.left + Math.random() * rect.width) + 'px';
            spark.style.top = (rect.top + Math.random() * rect.height) + 'px';
            
            const dx = (Math.random() - 0.5) * 80;
            const dy = (Math.random() - 0.5) * 80;
            spark.style.setProperty('--dx', `${dx}px`);
            spark.style.setProperty('--dy', `${dy}px`);
            
            document.body.appendChild(spark);
            setTimeout(() => spark.remove(), 600);
        }
    }

    function toggleModal(id, show) {
        const modal = $(id);
        const overlay = $(`${id}-overlay`);
        if(modal && overlay) {
            if(show) { 
                modal.classList.add('active'); 
                overlay.classList.add('active');
                // Trigger sparks on modal itself
                const rect = modal.getBoundingClientRect();
                createSparks({ currentTarget: modal });
            }
            else { modal.classList.remove('active'); overlay.classList.remove('active'); }
        }
    }

    // ═══════════════════════════════════════
    // BOOTSTRAP
    // ═══════════════════════════════════════

    document.addEventListener('DOMContentLoaded', () => {
        loadMockHistory();
        
        const submitBtn = $('submit-deed');
        const descriptionInput = $('deed-description');
        const charLimitHint = $('char-limit-hint');

        submitBtn?.addEventListener('click', handleSubmit);
        
        // [GUARDRAIL] Real-time validation
        descriptionInput?.addEventListener('input', (e) => {
            const len = e.target.value.trim().length;
            $('char-counter').textContent = `${len} / 2000`;
            
            if (len >= 15) {
                if(submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.style.opacity = "1";
                    submitBtn.style.cursor = "pointer";
                }
                if(charLimitHint) charLimitHint.style.opacity = "0";
            } else {
                if(submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = "0.5";
                    submitBtn.style.cursor = "not-allowed";
                }
                if(charLimitHint) charLimitHint.style.opacity = "1";
            }
        });

        $('mission-select')?.addEventListener('change', (e) => {
            setTerminalLine(0, `MISSION_LOCKED: ${e.target.value.toUpperCase()}`, "lt-text--gold");
        });

        // B2B Event Handlers
        $('nav-create-campaign')?.addEventListener('click', () => toggleModal('campaign-modal', true));
        $('close-campaign-modal')?.addEventListener('click', () => toggleModal('campaign-modal', false));
        $('campaign-modal-overlay')?.addEventListener('click', () => toggleModal('campaign-modal', false));
        $('campaign-form')?.addEventListener('submit', handleCampaignSubmit);

        // Nomad Terminal Handlers
        const terminalModal = $('nomad-terminal');
        $('launch-app-btn')?.addEventListener('click', (e) => {
            toggleModal('nomad-terminal', true);
            loadCampaigns();
        });
        
        terminalModal?.addEventListener('mouseleave', () => {
            toggleModal('nomad-terminal', false);
        });

        $('close-nomad-terminal')?.addEventListener('click', () => toggleModal('nomad-terminal', false));
        $('nomad-terminal-overlay')?.addEventListener('click', () => toggleModal('nomad-terminal', false));

        // Iridescent Cards Handled in index.html for high-perf GSAP

        // Protocol Pillars Detail Logic
        const pillarData = {
            ingestion: {
                title: "Seamless Ingestion",
                text: "ProtoQol's Nomad API ensures effortless connectivity. ESG reports, carbon metrics, and IoT sensor streams are ingested with zero latency, utilizing AES-256 encryption at the edge before hitting our verification nodes.",
                icon: "⚛️"
            },
            audit: {
                title: "AI–Biy Consensus",
                text: "The decentralized AI Council, powered by Gemini 2.0 Ultra, performs deep ethical audits. Every deed is cross-referenced against mission mandates to ensure absolute integrity and prevent fraudulent claims.",
                icon: "🧠"
            },
            solana: {
                title: "On-Chain Finality",
                text: "Once verified, proofs are crystallized on the Solana mainnet. This stage provides immutable on-chain finality, generating a public integrity hash that serves as permanent proof of your ESG impact.",
                icon: "⛓️"
            },
            // Keep previous for safety if references exist
            biy: { icon: "⚖️", title: "Суд Биев", text: "Мультиагентный ИИ-консенсус." },
            web3: { icon: "⚡", title: "Zero-Friction", text: "Web3 без кошельков." },
            law: { icon: "🏢", title: "Степное Право", text: "Традиции в API." }
        };

        const pillarOverlay = $('pillar-modal-overlay');
        const pillarModal = $('pillar-modal');
        const pillarContent = $('pillar-content');

        function togglePillarModal(show, type = null) {
            if (show && type && pillarData[type]) {
                const data = pillarData[type];
                pillarContent.innerHTML = `
                    <div style="font-size: 4rem; margin-bottom: 2rem;">${data.icon}</div>
                    <h3 class="about-title">${data.title}</h3>
                    <p class="about-text">${data.text}</p>
                    <div style="margin-top: 2rem; opacity: 0.5; font-size: 0.8rem;">PROTOCOL_MODULE_ID: ${type.toUpperCase()}_v1.0</div>
                `;
                pillarModal.classList.add('active');
                pillarOverlay.classList.add('active');
            } else {
                pillarModal.classList.remove('active');
                pillarOverlay.classList.remove('active');
            }
        }

        document.querySelectorAll('.open-pillar-detail').forEach(btn => {
            btn.addEventListener('click', () => {
                togglePillarModal(true, btn.getAttribute('data-pillar'));
            });
        });

        $('close-pillar-modal')?.addEventListener('click', () => togglePillarModal(false));
        pillarOverlay?.addEventListener('click', () => togglePillarModal(false));

        // Mobile Menu Logic
        const menuBtn = $('menu-btn-v6');
        const mobileMenu = $('mobile-menu-v6');
        
        function toggleMenu(show) {
            if (show) {
                menuBtn.classList.add('active');
                mobileMenu.classList.add('active');
            } else {
                menuBtn.classList.remove('active');
                mobileMenu.classList.remove('active');
            }
        }

        menuBtn?.addEventListener('click', () => {
            const isActive = mobileMenu.classList.contains('active');
            toggleMenu(!isActive);
        });

        // Close menu on link click
        document.querySelectorAll('.mobile-nav-links-v6 a').forEach(link => {
            link.addEventListener('click', () => toggleMenu(false));
        });

        document.addEventListener('keydown', (e) => { 
            if (e.key === 'Escape') {
                togglePillarModal(false);
                toggleMenu(false);
            }
        });
        // X-Ray Inspector Handlers
        $('live-terminal')?.addEventListener('click', (e) => {
            if (e.target.classList.contains('inspect-btn')) {
                const logs = e.target.getAttribute('data-logs');
                openConsensusInspector(logs);
            }
        });

        $('close-inspector')?.addEventListener('click', () => {
            $('consensus-inspector')?.classList.remove('active');
            $('inspector-overlay')?.classList.remove('active');
        });

        $('inspector-overlay')?.addEventListener('click', () => {
            $('consensus-inspector')?.classList.remove('active');
            $('inspector-overlay')?.classList.remove('active');
        });

        console.log("%c⟡ ProtoQol B2B MVP Bridge Active", "color: #00E5FF; font-weight: bold;");
    });

})();
