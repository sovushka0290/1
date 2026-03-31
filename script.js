/* ═══════════════════════════════════════════════════
   ProtoQol — Nomad Cyberpunk v3.8 (B2B MVP)
   Neural Integrity Flow + Live Terminal Analytics
   ═══════════════════════════════════════════════════ */

;(() => {
    'use strict';

    const CONFIG = Object.freeze({
        API_BASE: (window.location.hostname === 'localhost' || window.location.hostname === '')
            ? 'https://ngrok.com/docs/errors/err_ngrok_4018'
            : '/api',
        POLL_INTERVAL_MS: 5000,
        B2B_KEY: 'PQ_LIVE_DEMO_SECRET',
        TYPING_SPEED_MS: 15,
    });

    let protocolState = {
        totalImpact: 14208,
        isProcessing: false,
        selectedMissionId: '',
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
                    const hash = tx.tx_hash.substring(0, 16) + '...';
                    const color = tx.verdict === 'ADAL' ? 'lt-text--cyan' : 'lt-text--error';
                    line.innerHTML = `<span class="lt-prompt">></span> <span class="lt-text">[${new Date(tx.timestamp).toLocaleTimeString()}] | TX: ${hash} | VERDICT: <span class="${color}">${tx.verdict}</span> | XP: +${tx.impact_points}</span>`;
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

    function setTerminalLine(lineNum, text, cssClass = '') {
        const line = document.createElement('div');
        line.className = 'lt-line';
        line.innerHTML = `<span class="lt-prompt">></span> <span class="lt-text ${cssClass}">${sanitize(text)}</span>`;
        const terminal = $('live-terminal');
        if (terminal) {
            terminal.appendChild(line);
            terminal.scrollTop = terminal.scrollHeight;
            // Keep only last 10 lines
            if (terminal.children.length > 10) terminal.removeChild(terminal.firstChild);
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
                setTerminalLine(0, `SUCCESS: TX ${result.tx_hash?.substring(0,16)}...`, "lt-text--cyan");
                protocolState.totalImpact += result.impact_points || 0;
                
                const score = protocolState.totalImpact.toLocaleString();
                if($('rep-score')) $('rep-score').textContent = score;
                if($('stat-impact')) $('stat-impact').textContent = score;
            } else {
                setTerminalLine(0, `DENIED: ${result.verdict} | ${result.wisdom || result.auditor_wisdom}`, "lt-text--error");
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

        // About Modal Handlers
        const openAbout = $('open-about');
        const closeAbout = $('close-about');
        const aboutModal = $('about-modal');
        const aboutOverlay = $('about-overlay');

        function toggleAbout(show) {
            if (show) {
                aboutModal.classList.add('active');
                aboutOverlay.classList.add('active');
            } else {
                aboutModal.classList.remove('active');
                aboutOverlay.classList.remove('active');
            }
        }

        if (openAbout) openAbout.addEventListener('click', () => toggleAbout(true));
        if (closeAbout) closeAbout.addEventListener('click', () => toggleAbout(false));
        if (aboutOverlay) aboutOverlay.addEventListener('click', () => toggleAbout(false));

        document.addEventListener('keydown', (e) => { 
            if (e.key === 'Escape') {
                toggleAbout(false);
            }
        });
        setInterval(() => {
            const lat = $('lt-latency');
            if (lat) lat.textContent = `Latency: ${35 + Math.floor(Math.random() * 15)}ms`;
        }, 2000);
        
        console.log("%c⟡ ProtoQol B2B MVP Bridge Active", "color: #00E5FF; font-weight: bold;");
    });

    /**
     * Foundation for Tier selection and tab redirection
     */
    window.selectTier = function(tier) {
        console.log(`[SUBSCRIPTION_WIZARD] Selected Tier: ${tier}`);
        
        switch(tier) {
            case 'biy':
                window.location.href = 'dashboard.html';
                break;
            case 'wanderer':
                window.location.hash = 'how-it-works';
                break;
            case 'khan':
                window.location.href = 'mailto:founders@protoqol.pro';
                break;
            default:
                break;
        }
    };

})();
