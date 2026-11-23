/**
 * RingTrace — Frontend Client Controller
 * Manages interactive graph visualization, adversarial trace rendering,
 * real-time sensitivity perturbation, and benchmark comparisons.
 */

let CURRENT_CASE_ID = "RT-1042";
let CURRENT_GRAPH_DATA = null;
let CURRENT_CASE_DATA = null;

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    loadSelectedCase();
});

async function loadSelectedCase() {
    const select = document.getElementById("caseSelect");
    CURRENT_CASE_ID = select.value;

    try {
        // Fetch case metadata & transactions
        const caseRes = await fetch(`/api/cases/${CURRENT_CASE_ID}`);
        CURRENT_CASE_DATA = await caseRes.json();

        // Update header & banner
        document.getElementById("caseIdBadge").textContent = `CASE: ${CURRENT_CASE_ID}`;
        document.getElementById("caseTitleDisplay").textContent = CURRENT_CASE_DATA.title;
        document.getElementById("caseDescDisplay").textContent = CURRENT_CASE_DATA.description;

        // Fetch graph data
        const graphRes = await fetch(`/api/cases/${CURRENT_CASE_ID}/graph`);
        CURRENT_GRAPH_DATA = await graphRes.json();

        // Update stats
        const txs = CURRENT_CASE_DATA.transactions;
        const totalVol = txs.reduce((sum, t) => sum + t.amount, 0);
        document.getElementById("statVolume").textContent = `₹ ${totalVol.toLocaleString("en-IN")}`;
        document.getElementById("statTxCount").textContent = `${txs.length} Records`;
        document.getElementById("statAccCount").textContent = `${CURRENT_GRAPH_DATA.nodes.length} Accounts`;

        // Render table
        renderTransactionTable(txs);

        // Render SVG Graph
        renderSvgGraph(CURRENT_GRAPH_DATA);

        // Populate perturbation select
        populatePerturbSelect(txs);

        // Reset CERP & Adversarial trace to clean state
        resetInvestigationViews();

    } catch (err) {
        console.error("Failed to load case data:", err);
    }
}

function renderTransactionTable(transactions) {
    const tbody = document.getElementById("transactionTableBody");
    tbody.innerHTML = "";
    document.getElementById("ledgerCountBadge").textContent = `${transactions.length} Records`;

    transactions.forEach(tx => {
        const tr = document.createElement("tr");
        if (tx.is_planted_defect) {
            tr.style.backgroundColor = "rgba(244, 63, 94, 0.15)";
        }
        tr.innerHTML = `
            <td><code>${tx.transaction_id}</code></td>
            <td>${formatTime(tx.timestamp)}</td>
            <td><strong>${tx.source_account}</strong></td>
            <td><strong>${tx.destination_account}</strong></td>
            <td>₹ ${tx.amount.toLocaleString("en-IN")}</td>
            <td>${tx.narrative_memo || "—"}</td>
        `;
        tbody.appendChild(tr);
    });
}

function populatePerturbSelect(transactions) {
    const select = document.getElementById("perturbSelect");
    select.innerHTML = '<option value="">Select transaction to exclude...</option>';
    transactions.forEach(tx => {
        const opt = document.createElement("option");
        opt.value = tx.transaction_id;
        opt.textContent = `${tx.transaction_id} (₹ ${tx.amount.toLocaleString("en-IN")} | ${tx.source_account} → ${tx.destination_account})`;
        select.appendChild(opt);
    });
    document.getElementById("perturbResultBox").style.display = "none";
}

function resetInvestigationViews() {
    const pill = document.getElementById("workflowStatusPill");
    pill.className = "status-pill status-pill-pending";
    pill.textContent = "AWAITING RUN";

    // Reset CERP Badges
    const badgeIds = ["badgeProv", "badgeChrono", "badgeHypo", "badgeGaps", "badgeSens"];
    badgeIds.forEach(id => {
        const b = document.getElementById(id);
        b.className = "dim-badge badge-neutral";
        b.textContent = "UNTESTED";
    });

    document.getElementById("descProv").textContent = "Record IDs, amounts, and source hashes verified against frozen ledger.";
    document.getElementById("descChrono").textContent = "Time order t_i ≤ t_{i+1} verified along all directed fund paths.";
    document.getElementById("descHypo").textContent = "Defender read-only tools test recurring payments & commercial memos.";
    document.getElementById("descGaps").textContent = "Contradictory evidence surfaced; uncollected fields kept as UNKNOWN.";
    document.getElementById("descSens").textContent = "Exclusion test identifies if conclusion relies heavily on a single bridge transaction.";

    document.getElementById("unknownsListText").textContent = "Run investigation to catalog unverified contextual fields.";
    document.getElementById("prosecutorClaimsList").innerHTML = '<div class="empty-state">Click "Run Adversarial Investigation" to start...</div>';
    document.getElementById("defenderClaimsList").innerHTML = '<div class="empty-state">Click "Run Adversarial Investigation" to start...</div>';
    document.getElementById("rejectionsContainer").style.display = "none";
    document.getElementById("reviewTimestampText").textContent = "Status: Awaiting human action";
}

// -------------------------------------------------------------
// Interactive SVG Graph Renderer
// -------------------------------------------------------------
function renderSvgGraph(graphData, highlightedTxId = null) {
    const svg = document.getElementById("transactionGraphSvg");
    svg.innerHTML = "";

    const width = svg.clientWidth || 550;
    const height = 340;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.38;

    const nodes = graphData.nodes;
    const edges = graphData.edges;

    // Calculate circular positions for nodes
    const nodePositions = {};
    const totalNodes = nodes.length;

    nodes.forEach((node, idx) => {
        const angle = (idx / totalNodes) * 2 * Math.PI - Math.PI / 2;
        nodePositions[node.id] = {
            x: centerX + radius * Math.cos(angle),
            y: centerY + radius * Math.sin(angle)
        };
    });

    // Create defs for arrow markers
    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    defs.innerHTML = `
        <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#38bdf8" />
        </marker>
        <marker id="arrow-pivotal" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#c084fc" />
        </marker>
        <marker id="arrow-defect" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#f43f5e" />
        </marker>
    `;
    svg.appendChild(defs);

    // Draw Edges (Curves)
    edges.forEach(edge => {
        const p1 = nodePositions[edge.source];
        const p2 = nodePositions[edge.target];
        if (!p1 || !p2) return;

        const isPivotal = (edge.id === "TX-RING-004" || edge.id === highlightedTxId);
        const isDefect = edge.is_planted_defect;

        let strokeColor = "#38bdf8";
        let markerId = "url(#arrow)";

        if (isPivotal) {
            strokeColor = "#c084fc";
            markerId = "url(#arrow-pivotal)";
        } else if (isDefect) {
            strokeColor = "#f43f5e";
            markerId = "url(#arrow-defect)";
        }

        // Draw curved quadratic Bezier
        const midX = (p1.x + p2.x) / 2;
        const midY = (p1.y + p2.y) / 2;
        // Offset perpendicular curve
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const curveFactor = 0.15;
        const ctrlX = midX - dy * curveFactor;
        const ctrlY = midY + dx * curveFactor;

        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", `M ${p1.x} ${p1.y} Q ${ctrlX} ${ctrlY} ${p2.x} ${p2.y}`);
        path.setAttribute("fill", "none");
        path.setAttribute("stroke", strokeColor);
        path.setAttribute("stroke-width", isPivotal ? "3" : "2");
        path.setAttribute("stroke-opacity", isPivotal ? "1" : "0.7");
        path.setAttribute("marker-end", markerId);
        svg.appendChild(path);

        // Edge amount label
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", ctrlX);
        text.setAttribute("y", ctrlY);
        text.setAttribute("fill", strokeColor);
        text.setAttribute("font-size", "10px");
        text.setAttribute("font-family", "JetBrains Mono");
        text.setAttribute("text-anchor", "middle");
        text.textContent = `₹${(edge.amount / 1000).toFixed(0)}k`;
        svg.appendChild(text);
    });

    // Draw Nodes
    nodes.forEach(node => {
        const pos = nodePositions[node.id];
        if (!pos) return;

        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");

        let nodeColor = "#38bdf8";
        if (node.account_type === "aggregator_sink") nodeColor = "#fbbf24";
        if (node.id.includes("ORIGIN")) nodeColor = "#f43f5e";

        // Circle
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", pos.x);
        circle.setAttribute("cy", pos.y);
        circle.setAttribute("r", "16");
        circle.setAttribute("fill", "#111827");
        circle.setAttribute("stroke", nodeColor);
        circle.setAttribute("stroke-width", "2.5");
        g.appendChild(circle);

        // Node Label
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("x", pos.x);
        label.setAttribute("y", pos.y + 28);
        label.setAttribute("fill", "#f8fafc");
        label.setAttribute("font-size", "10px");
        label.setAttribute("font-weight", "600");
        label.setAttribute("text-anchor", "middle");
        label.textContent = node.id;
        g.appendChild(label);

        // Center dot
        const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        dot.setAttribute("cx", pos.x);
        dot.setAttribute("cy", pos.y);
        dot.setAttribute("r", "5");
        dot.setAttribute("fill", nodeColor);
        g.appendChild(dot);

        svg.appendChild(g);
    });
}

// -------------------------------------------------------------
// Run Bounded Investigation Workflow
// -------------------------------------------------------------
async function runInvestigation() {
    const btn = document.getElementById("btnInvestigate");
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon">⏳</span> Investigating...';

    try {
        const res = await fetch(`/api/cases/${CURRENT_CASE_ID}/investigate`, {
            method: "POST"
        });
        const data = await res.json();

        // 1. Update Workflow Status Pill
        const pill = document.getElementById("workflowStatusPill");
        const status = data.cerp.suggested_workflow_status;

        pill.textContent = status.replace(/_/g, " ");
        if (status === "ESCALATE_FOR_HUMAN_REVIEW") {
            pill.className = "status-pill status-pill-escalate";
        } else if (status === "REQUEST_MORE_INFORMATION") {
            pill.className = "status-pill status-pill-info";
        } else if (status === "CLOSURE_REVIEW") {
            pill.className = "status-pill status-pill-closure";
        } else {
            pill.className = "status-pill status-pill-pending";
        }

        // 2. Update CERP Cards
        updateCerpCards(data.cerp, data.stress_test_results);

        // 3. Render Adversarial Claims
        renderClaims(data.prosecutor_claims, "prosecutorClaimsList", "pros");
        renderClaims(data.defender_claims, "defenderClaimsList", "def");

        // 4. Render Rejections if any
        if (data.rejected_claims && data.rejected_claims.length > 0) {
            const container = document.getElementById("rejectionsContainer");
            const list = document.getElementById("rejectionsList");
            list.innerHTML = "";
            data.rejected_claims.forEach(c => {
                const li = document.createElement("li");
                li.innerHTML = `<strong>${c.claim_id}:</strong> ${c.rejection_reason}`;
                list.appendChild(li);
            });
            container.style.display = "block";
        } else {
            document.getElementById("rejectionsContainer").style.display = "none";
        }

        // Highlight pivotal transaction in graph
        if (data.cerp.pivotal_dependency) {
            renderSvgGraph(CURRENT_GRAPH_DATA, data.cerp.pivotal_dependency);
        }

    } catch (err) {
        console.error("Investigation failed:", err);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon">⚡</span> Run Adversarial Investigation';
    }
}

function updateCerpCards(cerp, stressTests) {
    // 1. Provenance
    const badgeProv = document.getElementById("badgeProv");
    badgeProv.textContent = cerp.provenance_status;
    badgeProv.className = `dim-badge ${cerp.provenance_status === "VERIFIED" ? "badge-passed" : "badge-failed"}`;
    document.getElementById("descProv").textContent = 
        cerp.provenance_status === "VERIFIED" 
        ? "All transaction IDs, amounts, and timestamps match frozen source ledger."
        : "Corrupted records or non-positive amounts detected.";

    // 2. Chronology
    const badgeChrono = document.getElementById("badgeChrono");
    badgeChrono.textContent = cerp.chronology_status;
    badgeChrono.className = `dim-badge ${cerp.chronology_status === "VERIFIED" ? "badge-passed" : "badge-failed"}`;
    document.getElementById("descChrono").textContent = 
        cerp.chronology_status === "VERIFIED"
        ? "Strict forward causality verified along all paths (t_i ≤ t_{i+1})."
        : "Impossible time travel sequence detected in transaction chain.";

    // 3. Alternative Hypotheses
    const badgeHypo = document.getElementById("badgeHypo");
    badgeHypo.textContent = cerp.alternative_hypothesis_status;
    badgeHypo.className = `dim-badge ${cerp.alternative_hypothesis_status === "PLAUSIBLE" ? "badge-challenged" : "badge-neutral"}`;
    document.getElementById("descHypo").textContent = cerp.alternative_hypothesis;

    // 4. Contradictions & Gaps
    const badgeGaps = document.getElementById("badgeGaps");
    const hasContradictions = cerp.contradictions && cerp.contradictions.length > 0;
    badgeGaps.textContent = hasContradictions ? "CHALLENGED" : "PASSED";
    badgeGaps.className = `dim-badge ${hasContradictions ? "badge-challenged" : "badge-passed"}`;
    document.getElementById("descGaps").textContent = 
        hasContradictions 
        ? cerp.contradictions[0] 
        : "No contradictory records found in available transaction files.";

    // Unknowns
    document.getElementById("unknownsListText").textContent = cerp.missing_context_unknowns.join(", ");

    // 5. Sensitivity
    const badgeSens = document.getElementById("badgeSens");
    const isSens = cerp.sensitivity_result.includes("SENSITIVE");
    badgeSens.textContent = isSens ? "SENSITIVE" : "ROBUST";
    badgeSens.className = `dim-badge ${isSens ? "badge-sensitive" : "badge-passed"}`;
    document.getElementById("descSens").textContent = cerp.sensitivity_result;
}

function renderClaims(claims, containerId, role) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (!claims || claims.length === 0) {
        container.innerHTML = '<div class="empty-state">No claims generated.</div>';
        return;
    }

    claims.forEach(c => {
        const box = document.createElement("div");
        box.className = "claim-box";
        box.innerHTML = `
            <div class="claim-header">
                <span><strong>${c.claim_id}</strong> (${c.claim_type})</span>
                <span class="badge ${c.is_interpretation ? "badge-info" : "badge-passed"}">${c.is_interpretation ? "Interpretation" : "Verified Fact"}</span>
            </div>
            <div class="claim-text">${c.statement}</div>
            <div class="claim-citations">Citations: ${c.transaction_ids.length > 0 ? c.transaction_ids.join(", ") : "None (Tool Query)"}</div>
        `;
        container.appendChild(box);
    });
}

// -------------------------------------------------------------
// Interactive Sensitivity Diagnostic Simulation
// -------------------------------------------------------------
async function simulatePerturbation() {
    const select = document.getElementById("perturbSelect");
    const txId = select.value;
    if (!txId) {
        alert("Please select a transaction to simulate exclusion.");
        return;
    }

    try {
        const res = await fetch(`/api/cases/${CURRENT_CASE_ID}/perturb`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ excluded_tx_id: txId })
        });
        const data = await res.json();

        const resultBox = document.getElementById("perturbResultBox");
        const summaryText = document.getElementById("perturbSummaryText");

        if (data.patterns_broken.length > 0) {
            summaryText.innerHTML = `<strong>⚠️ FRAGILE DEPENDENCY:</strong> Excluding <code>${txId}</code> completely broke <strong>${data.patterns_broken.join(", ")}</strong>. Case narrative collapses without this pivotal record!`;
            resultBox.style.borderColor = "var(--accent-purple)";
        } else {
            summaryText.innerHTML = `<strong>✅ ROBUST:</strong> Excluding <code>${txId}</code> did not break the primary anomaly. Pattern persists across independent flow branches.`;
            resultBox.style.borderColor = "var(--accent-green)";
        }
        resultBox.style.display = "block";

    } catch (err) {
        console.error("Perturbation simulation failed:", err);
    }
}

function resetPerturbation() {
    document.getElementById("perturbSelect").value = "";
    document.getElementById("perturbResultBox").style.display = "none";
    renderSvgGraph(CURRENT_GRAPH_DATA);
}

// -------------------------------------------------------------
// Human Review Action
// -------------------------------------------------------------
async function submitHumanReview() {
    const name = document.getElementById("analystNameInput").value.trim();
    const decision = document.getElementById("analystDecisionSelect").value;
    const notes = document.getElementById("analystNotesInput").value.trim();

    if (!name) {
        alert("Please provide an analyst ID/name.");
        return;
    }

    try {
        const res = await fetch(`/api/cases/${CURRENT_CASE_ID}/review`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                analyst_name: name,
                decision: decision,
                analyst_notes: notes || "Standard review determination."
            })
        });
        const data = await res.json();

        document.getElementById("reviewTimestampText").textContent = 
            `Recorded: ${decision} by ${name} at ${new Date().toLocaleTimeString()}`;
        alert(`Analyst determination recorded: ${decision}`);

    } catch (err) {
        console.error("Failed to submit review:", err);
    }
}

// -------------------------------------------------------------
// Benchmark Modal View
// -------------------------------------------------------------
async function openBenchmarkModal() {
    const modal = document.getElementById("benchmarkModal");
    modal.style.display = "flex";

    try {
        const res = await fetch("/api/benchmark/run");
        const data = await res.json();

        const tbody = document.getElementById("benchmarkTableBody");
        tbody.innerHTML = "";

        data.comparative_metrics_table.forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${row.metric}</strong></td>
                <td>${row.detector_only}</td>
                <td>${row.single_agent}</td>
                <td>${row.ringtrace}</td>
            `;
            tbody.appendChild(tr);
        });

    } catch (err) {
        console.error("Failed to load benchmark:", err);
    }
}

function closeBenchmarkModal() {
    document.getElementById("benchmarkModal").style.display = "none";
}

function formatTime(isoStr) {
    if (!isoStr) return "—";
    const d = new Date(isoStr);
    return d.toLocaleDateString("en-GB", {
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    });
}
