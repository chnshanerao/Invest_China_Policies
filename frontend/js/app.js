const API = "";
let currentTab = "dashboard";

const STAGE_ORDER = ["规划期","启动期","扩张期","验证期","成熟期","调整期","衰退期"];
const STAGE_COLORS = {
    "规划期": "#6b7280", "启动期": "#3b82f6", "扩张期": "#10b981",
    "验证期": "#f59e0b", "成熟期": "#8b5cf6", "调整期": "#f97316", "衰退期": "#ef4444"
};
const MOMENTUM_COLORS = { "加速": "#10b981", "平稳": "#f59e0b", "减速": "#ef4444" };
const MOMENTUM_ARROWS = { "加速": "▲", "平稳": "●", "减速": "▼" };
const RISK_COLORS = { "低": "#10b981", "中": "#f59e0b", "高": "#ef4444" };
const CHART_COLORS = ["#3b82f6","#10b981","#f59e0b","#8b5cf6","#ef4444","#06b6d4","#f97316","#ec4899","#14b8a6","#6366f1","#84cc16","#f43f5e"];
const VERIFY_LABELS = { 0: "未验证", 1: "部分验证", 2: "已验证" };

async function api(path) {
    const res = await fetch(API + path);
    if (!res.ok) throw new Error(`API ${res.status}`);
    return res.json();
}

const TAB_NAMES = ["dashboard","lifecycle","detail","policies","opportunities","news","settings"];
function switchTab(tab) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".tab").forEach(el => el.classList.remove("active"));
    document.getElementById("tab-" + tab).classList.add("active");
    document.querySelectorAll(".tab")[TAB_NAMES.indexOf(tab)].classList.add("active");
    currentTab = tab;
    const loaders = { dashboard: loadDashboard, lifecycle: loadLifecycleView, detail: loadDetailTable, policies: loadPolicies, opportunities: loadOpportunities, news: loadNews, settings: loadSettings };
    if (loaders[tab]) loaders[tab]();
}

function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
const debouncedLoadPolicies = debounce(loadPolicies, 300);
const debouncedLoadOpps = debounce(loadOpportunities, 300);

function stageTag(s) { return s ? `<span class="tag tag-stage tag-stage-${s}">${s}</span>` : ""; }
function riskTag(r) { return `<span class="tag tag-risk-${r}">${r}风险</span>`; }
function momentumTag(m) { return m ? `<span class="tag tag-momentum-${m}">${MOMENTUM_ARROWS[m]||""} ${m}</span>` : ""; }
function sentimentTag(s) { return `<span class="tag tag-sentiment-${s}">${s}</span>`; }
function v(val) { return (val !== null && val !== undefined && val !== "") ? val : "-"; }

function meterHtml(label, value, max, color) {
    const pct = Math.min((value / max) * 100, 100);
    return `<div class="meter">
        <div class="meter-label"><span>${label}</span><span>${value}/${max}</span></div>
        <div class="meter-track"><div class="meter-fill" style="width:${pct}%;background:${color}"></div></div>
    </div>`;
}

function scoreCell(val, max) {
    if (val === null || val === undefined) return '<span class="cell-na">-</span>';
    const pct = (val / max) * 100;
    const color = val >= 7 ? "#10b981" : val >= 5 ? "#f59e0b" : "#ef4444";
    return `<span class="cell-score">${val}<span class="score-bar"><span class="score-fill" style="width:${pct}%;background:${color}"></span></span></span>`;
}

function intensityColor(v) { return v >= 7 ? "#10b981" : v >= 5 ? "#f59e0b" : "#ef4444"; }
function effectivenessColor(v) { return v >= 7 ? "#10b981" : v >= 5 ? "#f59e0b" : "#ef4444"; }

// ==================== Dashboard ====================
async function loadDashboard() {
    try {
        const d = await api("/api/dashboard/summary");
        document.getElementById("totalPolicies").textContent = d.total_policies;
        document.getElementById("totalOpportunities").textContent = d.total_opportunities;
        document.getElementById("avgIntensity").textContent = d.avg_intensity + "/10";
        document.getElementById("avgEffectiveness").textContent = d.avg_effectiveness + "/10";

        // Sort lifecycle by stage order
        const lcData = (d.by_lifecycle || []).sort((a, b) =>
            STAGE_ORDER.indexOf(a.lifecycle_stage) - STAGE_ORDER.indexOf(b.lifecycle_stage));
        const lcDiv = document.getElementById("lifecycleChart");
        lcDiv.innerHTML = lcData.map(s => `
            <div class="lc-ring-item" onclick="switchTab('lifecycle');document.getElementById('lcFilterStage').value='${s.lifecycle_stage}';loadLifecycleView()">
                <div class="lc-ring-dot" style="background:${STAGE_COLORS[s.lifecycle_stage]||'#666'}"></div>
                <span class="lc-ring-count" style="color:${STAGE_COLORS[s.lifecycle_stage]||'#666'}">${s.count}</span>
                <span class="lc-ring-label">${s.lifecycle_stage}</span>
            </div>
        `).join("") || '<div class="empty-state">暂无数据</div>';

        const momDiv = document.getElementById("momentumChart");
        const totalMom = (d.by_momentum || []).reduce((s, m) => s + m.count, 0) || 1;
        const momOrder = ["加速","平稳","减速"];
        const momData = momOrder.map(m => (d.by_momentum || []).find(x => x.policy_momentum === m) || { policy_momentum: m, count: 0 });
        momDiv.innerHTML = momData.map(m => `
            <div class="momentum-item">
                <div class="momentum-label" style="color:${MOMENTUM_COLORS[m.policy_momentum]||'#999'}">${MOMENTUM_ARROWS[m.policy_momentum]||""} ${m.policy_momentum}</div>
                <div class="momentum-bar-track">
                    <div class="momentum-bar-fill" style="width:${(m.count/totalMom*100)}%;background:${MOMENTUM_COLORS[m.policy_momentum]||'#666'}">${m.count}项 (${(m.count/totalMom*100).toFixed(0)}%)</div>
                </div>
            </div>
        `).join("");

        const riskDiv = document.getElementById("riskChart2");
        const riskOrder = ["低","中","高"];
        riskDiv.innerHTML = riskOrder.map(r => {
            const item = (d.by_risk || []).find(x => x.risk_level === r) || { count: 0 };
            return `<div class="risk-block"><div class="risk-count" style="color:${RISK_COLORS[r]}">${item.count}</div><div class="risk-name">${r}风险</div></div>`;
        }).join("");

        renderBarChart("categoryChart2", d.by_category, "name", "count");

        const secDiv = document.getElementById("sectorChart2");
        const maxSec = Math.max(...(d.by_sector || []).map(s => s.count), 1);
        secDiv.innerHTML = (d.by_sector || []).map((s, i) => {
            const size = 0.85 + (s.count / maxSec) * 0.5;
            const c = CHART_COLORS[i % CHART_COLORS.length];
            return `<div class="sector-bubble" style="background:${c}18;color:${c};border-color:${c}30;font-size:${12*size}px;padding:${6*size}px ${14*size}px">${s.sector} <b>${s.count}</b></div>`;
        }).join("") || '<div class="empty-state">暂无数据</div>';
    } catch (e) { console.error("Dashboard error:", e); }
}

function renderBarChart(id, data, lk, vk, max = 10) {
    const el = document.getElementById(id);
    if (!data || !data.length) { el.innerHTML = '<div class="empty-state">暂无数据</div>'; return; }
    const items = data.slice(0, max);
    const mx = Math.max(...items.map(d => d[vk]));
    el.innerHTML = items.map((d, i) => `
        <div class="bar-item">
            <div class="bar-label" title="${d[lk]}">${d[lk]}</div>
            <div class="bar-track">
                <div class="bar-fill" style="width:${(d[vk]/mx*100)}%;background:${CHART_COLORS[i%CHART_COLORS.length]}">${d[vk]}</div>
            </div>
        </div>
    `).join("");
}

// ==================== Lifecycle View ====================
const STAGE_EN = {"规划期":"Planning","启动期":"Launch","扩张期":"Expansion","验证期":"Validation","成熟期":"Maturity","调整期":"Adjustment","衰退期":"Decline"};

function renderLcCard(p) {
    const age = p.established_year ? (new Date().getFullYear() - p.established_year) : 0;
    return `
    <div class="lc-card" onclick="showPolicyDetail(${p.id})" style="border-left: 4px solid ${STAGE_COLORS[p.lifecycle_stage]||'#666'}">
        <div class="lc-card-header">
            <span class="lc-card-name">${p.name}</span>
            <span class="lc-card-year">${p.established_year ? p.established_year + "年 · " + age + "年" : ""}</span>
        </div>
        <div class="lc-card-tags">
            ${momentumTag(p.policy_momentum)}
            ${riskTag(p.risk_level)}
            <span class="tag tag-category">${p.category_name}</span>
            ${p.region ? `<span class="tag tag-region">${p.region}</span>` : ""}
        </div>
        <div class="lc-card-meters">
            ${meterHtml("力度", p.execution_intensity||0, 10, intensityColor(p.execution_intensity||0))}
            ${meterHtml("效果", p.execution_effectiveness||0, 10, effectivenessColor(p.execution_effectiveness||0))}
        </div>
        <div class="lc-card-bottom">
            <span>投资机会 ${p.opportunity_count}</span>
            ${p.expected_end_year ? `<span>预计${p.expected_end_year}年</span>` : "<span>长期持续</span>"}
            ${p.total_investment_billion ? `<span>${p.total_investment_billion}亿</span>` : ""}
        </div>
    </div>`;
}

async function loadLifecycleView() {
    const stageFilter = document.getElementById("lcFilterStage").value;
    const momentum = document.getElementById("lcFilterMomentum").value;
    const cat = document.getElementById("lcFilterCategory").value;
    const sort = document.getElementById("lcSort").value;

    let url = `/api/policies?sort_by=${sort}`;
    if (stageFilter) url += `&lifecycle_stage=${encodeURIComponent(stageFilter)}`;
    if (momentum) url += `&momentum=${encodeURIComponent(momentum)}`;
    if (cat) url += `&category_id=${cat}`;

    try {
        const policies = await api(url);
        const container = document.getElementById("lifecycleList");

        const grouped = {};
        STAGE_ORDER.forEach(s => grouped[s] = []);
        policies.forEach(p => {
            const s = p.lifecycle_stage || "未分类";
            if (!grouped[s]) grouped[s] = [];
            grouped[s].push(p);
        });

        const stagesToShow = stageFilter ? [stageFilter] : STAGE_ORDER.filter(s => grouped[s] && grouped[s].length > 0);

        container.innerHTML = stagesToShow.map(stage => {
            const items = grouped[stage] || [];
            const color = STAGE_COLORS[stage] || "#666";
            const avgI = items.length ? (items.reduce((s,p) => s + (p.execution_intensity||0), 0) / items.length).toFixed(1) : 0;
            const avgE = items.length ? (items.reduce((s,p) => s + (p.execution_effectiveness||0), 0) / items.length).toFixed(1) : 0;
            return `
            <div class="swimlane" style="--lane-color: ${color}">
                <div class="swimlane-header">
                    <div class="swimlane-title">
                        <span class="swimlane-dot" style="background:${color}"></span>
                        <span class="swimlane-stage">${stage}</span>
                        <span class="swimlane-en">${STAGE_EN[stage]||""}</span>
                        <span class="swimlane-count">${items.length} 项</span>
                    </div>
                    <div class="swimlane-stats">
                        <span>avg 力度 <b style="color:${intensityColor(avgI)}">${avgI}</b></span>
                        <span>avg 效果 <b style="color:${effectivenessColor(avgE)}">${avgE}</b></span>
                    </div>
                </div>
                <div class="swimlane-cards">
                    ${items.map(renderLcCard).join("")}
                </div>
            </div>`;
        }).join("") || '<div class="empty-state">没有匹配的政策</div>';
    } catch (e) { console.error("Lifecycle error:", e); }
}

// ==================== Detail Table ====================
let methodologyLoaded = false;

async function toggleMethodology() {
    const panel = document.getElementById("methodologyPanel");
    if (panel.style.display === "none") {
        if (!methodologyLoaded) {
            try {
                const m = await api("/api/scoring-methodology");
                panel.innerHTML = renderMethodology(m);
                methodologyLoaded = true;
            } catch (e) { panel.innerHTML = "加载失败"; }
        }
        panel.style.display = "block";
    } else {
        panel.style.display = "none";
    }
}

function renderMethodology(m) {
    let html = `<h3>一、生命周期阶段定义（7阶段模型）</h3><table>
        <tr><th>阶段</th><th>英文</th><th>定义</th><th>典型时长</th></tr>
        ${m.lifecycle_stages.map(s => `<tr><td><span class="tag tag-stage tag-stage-${s.stage}">${s.stage}</span></td><td>${s.stage_en}</td><td>${s.definition}</td><td>${s.typical_duration}</td></tr>`).join("")}
    </table>`;

    html += `<h3>二、执行力度评分 (1-10分)</h3><p>${m.intensity_scoring.description}</p><table>
        <tr><th>评估维度</th><th>权重</th><th>说明</th></tr>
        ${m.intensity_scoring.criteria.map(c => `<tr><td>${c.factor}</td><td>${c.weight}</td><td>${c.description}</td></tr>`).join("")}
    </table>
    <div class="scale-bar">
        <div class="scale-segment" style="flex:3;background:#ef4444">1-3 低力度</div>
        <div class="scale-segment" style="flex:3;background:#f59e0b">4-6 中力度</div>
        <div class="scale-segment" style="flex:2;background:#10b981">7-8 高力度</div>
        <div class="scale-segment" style="flex:2;background:#3b82f6">9-10 极高</div>
    </div>`;

    html += `<h3>三、执行效果评分 (1-10分)</h3><p>${m.effectiveness_scoring.description}</p><table>
        <tr><th>评估维度</th><th>权重</th><th>说明</th></tr>
        ${m.effectiveness_scoring.criteria.map(c => `<tr><td>${c.factor}</td><td>${c.weight}</td><td>${c.description}</td></tr>`).join("")}
    </table>
    <div class="scale-bar">
        <div class="scale-segment" style="flex:3;background:#ef4444">1-3 效果差</div>
        <div class="scale-segment" style="flex:3;background:#f59e0b">4-6 一般</div>
        <div class="scale-segment" style="flex:2;background:#10b981">7-8 效果好</div>
        <div class="scale-segment" style="flex:2;background:#3b82f6">9-10 卓越</div>
    </div>`;

    html += `<h3>四、政策动量定义</h3><table>
        <tr><th>动量</th><th>定义</th></tr>
        ${Object.entries(m.momentum_definition.criteria).map(([k,v]) => `<tr><td>${momentumTag(k)}</td><td>${v}</td></tr>`).join("")}
    </table>`;

    html += `<h3>五、数据完整性规则</h3><ol class="rule-list">
        ${m.data_integrity_rules.map(r => `<li>${r}</li>`).join("")}
    </ol>`;

    return html;
}

async function loadDetailTable() {
    const stage = document.getElementById("dtFilterStage").value;
    const momentum = document.getElementById("dtFilterMomentum").value;
    const cat = document.getElementById("dtFilterCategory").value;
    const risk = document.getElementById("dtFilterRisk").value;
    const sort = document.getElementById("dtSort").value;

    let url = `/api/policies/detail-table?sort_by=${sort}`;
    if (stage) url += `&lifecycle_stage=${encodeURIComponent(stage)}`;
    if (momentum) url += `&momentum=${encodeURIComponent(momentum)}`;
    if (cat) url += `&category_id=${cat}`;
    if (risk) url += `&risk=${encodeURIComponent(risk)}`;

    try {
        const policies = await api(url);
        document.getElementById("detailCount").textContent = `共 ${policies.length} 项政策`;
        const tbody = document.getElementById("detailTableBody");
        tbody.innerHTML = policies.map(p => {
            const docLink = p.policy_document_url
                ? `<a class="cell-link" href="${p.policy_document_url}" target="_blank">${p.policy_document || "查看"}</a>`
                : (p.policy_document ? `<span class="cell-wrap">${p.policy_document}</span>` : '<span class="cell-na">-</span>');

            const verifyClass = `verify-${p.data_verified || 0}`;
            const verifyLabel = VERIFY_LABELS[p.data_verified || 0];

            return `<tr>
                <td class="sticky-col" onclick="showPolicyDetail(${p.id})" style="cursor:pointer">${p.name}</td>
                <td><span class="tag tag-category">${p.category_name}</span></td>
                <td>${v(p.established_year)}</td>
                <td>${stageTag(p.lifecycle_stage)}</td>
                <td>${momentumTag(p.policy_momentum)}</td>
                <td>${scoreCell(p.execution_intensity, 10)}</td>
                <td>${scoreCell(p.execution_effectiveness, 10)}</td>
                <td>${riskTag(p.risk_level)}</td>
                <td>${p.gdp_billion ? p.gdp_billion.toLocaleString() : '<span class="cell-na">-</span>'}</td>
                <td>${p.total_investment_billion ? p.total_investment_billion.toLocaleString() : '<span class="cell-na">-</span>'}</td>
                <td>${p.opportunity_count}</td>
                <td>${p.expected_end_year || '<span class="cell-na">长期</span>'}</td>
                <td>${docLink}</td>
                <td><div class="cell-wrap">${p.intensity_basis || '<span class="cell-na">-</span>'}</div></td>
                <td><div class="cell-wrap">${p.effectiveness_basis || '<span class="cell-na">-</span>'}</div></td>
                <td><div class="cell-wrap">${p.lifecycle_source
                    ? (p.lifecycle_source_url
                        ? `<a class="cell-link" href="${p.lifecycle_source_url}" target="_blank">${p.lifecycle_source}</a>`
                        : p.lifecycle_source)
                    : '<span class="cell-na">-</span>'}</div></td>
                <td><span class="verify-badge ${verifyClass}">${verifyLabel}</span></td>
            </tr>`;
        }).join("");
    } catch (e) { console.error("Detail table error:", e); }
}

// ==================== Policies ====================
async function loadPolicies() {
    const cat = document.getElementById("filterCategory").value;
    const risk = document.getElementById("filterRisk").value;
    const stage = document.getElementById("filterStage").value;
    const momentum = document.getElementById("filterMomentum").value;
    const search = document.getElementById("filterSearch").value;

    let url = "/api/policies?sort_by=category";
    if (cat) url += `&category_id=${cat}`;
    if (risk) url += `&risk=${encodeURIComponent(risk)}`;
    if (stage) url += `&lifecycle_stage=${encodeURIComponent(stage)}`;
    if (momentum) url += `&momentum=${encodeURIComponent(momentum)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    try {
        const policies = await api(url);
        document.getElementById("policiesCount").textContent = `共 ${policies.length} 项政策`;
        document.getElementById("policiesList").innerHTML = policies.map(p => `
            <div class="policy-card" onclick="showPolicyDetail(${p.id})">
                <div class="p-header">
                    <span class="p-name">${p.name}</span>
                    <span style="font-size:11px;color:var(--text-muted)">${p.established_year||""}</span>
                </div>
                <div class="p-tags">
                    ${stageTag(p.lifecycle_stage)}
                    ${momentumTag(p.policy_momentum)}
                    ${riskTag(p.risk_level)}
                    <span class="tag tag-category">${p.category_name}</span>
                </div>
                <div class="p-desc">${p.description||""}</div>
                <div class="p-meters">
                    ${meterHtml("力度", p.execution_intensity||0, 10, intensityColor(p.execution_intensity||0))}
                    ${meterHtml("效果", p.execution_effectiveness||0, 10, effectivenessColor(p.execution_effectiveness||0))}
                </div>
                <div class="p-bottom">
                    <span>投资机会 ${p.opportunity_count}</span>
                    <span>新闻 ${p.news_count}</span>
                    ${p.region ? `<span>${p.region}</span>` : ""}
                </div>
            </div>
        `).join("") || '<div class="empty-state">没有匹配的政策</div>';
    } catch (e) { console.error("Policies error:", e); }
}

// ==================== Policy Detail Modal ====================
async function showPolicyDetail(id) {
    try {
        const p = await api(`/api/policies/${id}`);
        const modal = document.getElementById("policyModal");
        const detail = document.getElementById("policyDetail");
        const age = p.established_year ? (new Date().getFullYear() - p.established_year) : 0;
        const stageIdx = STAGE_ORDER.indexOf(p.lifecycle_stage);

        const lifecycleBarHtml = `<div class="detail-lifecycle-bar">${STAGE_ORDER.map((s, i) =>
            `<div class="stage-segment ${i<=stageIdx?'active':'inactive'}" style="flex:1;background:${STAGE_COLORS[s]}" title="${s}"></div>`
        ).join("")}</div>
        <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--text-muted);margin-bottom:12px">
            ${STAGE_ORDER.map(s => `<span style="color:${s===p.lifecycle_stage?STAGE_COLORS[s]:'var(--text-muted)'};font-weight:${s===p.lifecycle_stage?'700':'400'}">${s}</span>`).join("")}
        </div>`;

        let metricsHtml = "";
        if (p.total_investment_billion || p.gdp_billion || p.fiscal_revenue_billion || p.debt_billion) {
            metricsHtml = `<div class="detail-section"><h3>核心数据</h3><div class="detail-grid">
                ${p.total_investment_billion ? `<div class="detail-item"><div class="label">累计投资(亿)</div><div class="value">${p.total_investment_billion.toLocaleString()}</div></div>` : ""}
                ${p.gdp_billion ? `<div class="detail-item"><div class="label">GDP(亿)</div><div class="value">${p.gdp_billion.toLocaleString()}</div></div>` : ""}
                ${p.fiscal_revenue_billion ? `<div class="detail-item"><div class="label">财政收入(亿)</div><div class="value">${p.fiscal_revenue_billion.toLocaleString()}</div></div>` : ""}
                ${p.debt_billion ? `<div class="detail-item"><div class="label">债务(亿)</div><div class="value" style="color:var(--accent-red)">${p.debt_billion.toLocaleString()}</div></div>` : ""}
            </div>
            ${p.gdp_source ? `<div style="font-size:11px;color:var(--text-muted);margin-top:6px">数据来源: ${p.gdp_source_url ? `<a href="${p.gdp_source_url}" target="_blank" style="color:var(--accent-blue)">${p.gdp_source}</a>` : p.gdp_source}</div>` : ""}
            </div>`;
        }

        let sourcesHtml = "";
        if (p.policy_document || p.intensity_basis || p.effectiveness_basis || p.lifecycle_source) {
            sourcesHtml = `<div class="detail-section"><h3>数据来源与评分依据</h3>
                ${p.policy_document ? `<div style="margin-bottom:8px"><span style="font-size:11px;color:var(--text-muted)">政策文件：</span>${p.policy_document_url ? `<a href="${p.policy_document_url}" target="_blank" style="color:var(--accent-blue);font-size:12px">${p.policy_document}</a>` : `<span style="font-size:12px">${p.policy_document}</span>`}</div>` : ""}
                ${p.intensity_basis ? `<div style="margin-bottom:6px;font-size:12px;color:var(--text-secondary)"><b>力度评分依据：</b>${p.intensity_basis}</div>` : ""}
                ${p.effectiveness_basis ? `<div style="margin-bottom:6px;font-size:12px;color:var(--text-secondary)"><b>效果评分依据：</b>${p.effectiveness_basis}</div>` : ""}
                ${p.lifecycle_source ? `<div style="font-size:12px;color:var(--text-secondary)"><b>周期评估依据：</b>${p.lifecycle_source_url ? `<a href="${p.lifecycle_source_url}" target="_blank" style="color:var(--accent-blue)">${p.lifecycle_source}</a>` : p.lifecycle_source}</div>` : ""}
                <div style="margin-top:6px"><span class="verify-badge verify-${p.data_verified||0}">${VERIFY_LABELS[p.data_verified||0]}</span></div>
            </div>`;
        }

        let oppsHtml = "";
        if (p.opportunities && p.opportunities.length > 0) {
            oppsHtml = `<div class="detail-section"><h3>投资机会 (${p.opportunities.length})</h3>
                ${p.opportunities.map(o => `
                    <div style="background:var(--bg-card);border-radius:8px;padding:12px;margin-bottom:8px;border:1px solid var(--border-color)">
                        <div style="font-weight:600;font-size:14px;margin-bottom:3px">${o.title}</div>
                        <div style="font-size:12px;color:var(--text-secondary);margin-bottom:6px">${o.description||""}</div>
                        <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:4px">
                            <span class="tag tag-category">${o.sector}</span>
                            ${riskTag(o.risk_level)}
                            <span class="tag tag-return">回报:${o.potential_return}</span>
                            <span class="tag tag-horizon">${o.time_horizon}</span>
                        </div>
                        ${o.recommended_instruments ? `<div style="font-size:11px;color:var(--text-muted);font-family:monospace;background:var(--bg-primary);padding:5px 8px;border-radius:4px">${o.recommended_instruments}</div>` : ""}
                    </div>
                `).join("")}
            </div>`;
        }

        let newsHtml = "";
        if (p.news && p.news.length > 0) {
            newsHtml = `<div class="detail-section"><h3>相关新闻</h3>
                ${p.news.slice(0,8).map(n => `
                    <div style="padding:6px 0;border-bottom:1px solid var(--border-color);font-size:12px">
                        <a href="${n.url}" target="_blank" style="color:var(--text-primary);text-decoration:none">${n.title}</a>
                        <div style="display:flex;gap:6px;margin-top:2px;color:var(--text-muted);font-size:11px">${sentimentTag(n.sentiment)}<span>${n.published_at||""}</span></div>
                    </div>
                `).join("")}
            </div>`;
        }

        detail.innerHTML = `
            <div class="detail-header">
                <h2>${p.name}</h2>
                <div class="detail-en">${p.name_en||""}</div>
            </div>
            <div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:12px">
                ${stageTag(p.lifecycle_stage)}
                ${momentumTag(p.policy_momentum)}
                ${riskTag(p.risk_level)}
                <span class="tag tag-category">${p.category_name}</span>
                ${p.region ? `<span class="tag tag-region">${p.region}</span>` : ""}
                ${p.established_year ? `<span class="tag" style="background:rgba(6,182,212,0.12);color:var(--accent-cyan)">${p.established_year}年 · ${age}年</span>` : ""}
                ${p.expected_end_year ? `<span class="tag" style="background:rgba(239,68,68,0.12);color:var(--accent-red)">预计${p.expected_end_year}年</span>` : `<span class="tag" style="background:rgba(107,114,128,0.12);color:var(--text-muted)">长期持续</span>`}
            </div>
            <div class="detail-section">
                <h3>生命周期定位</h3>
                ${lifecycleBarHtml}
                <div style="display:flex;gap:12px;margin-bottom:12px">
                    ${meterHtml("执行力度", p.execution_intensity||0, 10, intensityColor(p.execution_intensity||0))}
                    ${meterHtml("执行效果", p.execution_effectiveness||0, 10, effectivenessColor(p.execution_effectiveness||0))}
                </div>
                ${p.lifecycle_note ? `<div class="detail-note">${p.lifecycle_note}</div>` : ""}
            </div>
            ${p.description ? `<div style="font-size:13px;color:var(--text-secondary);margin-bottom:10px">${p.description}</div>` : ""}
            ${p.key_goals ? `<div style="font-size:12px;color:var(--text-muted);margin-bottom:14px">目标: ${p.key_goals}</div>` : ""}
            ${metricsHtml}
            ${sourcesHtml}
            ${oppsHtml}
            ${newsHtml}
        `;
        modal.style.display = "flex";
    } catch (e) { console.error("Detail error:", e); }
}

function closeModal() { document.getElementById("policyModal").style.display = "none"; }
document.getElementById("policyModal").addEventListener("click", function(e) { if (e.target === this) closeModal(); });
document.addEventListener("keydown", function(e) { if (e.key === "Escape") closeModal(); });

// ==================== Opportunities ====================
async function loadOpportunities() {
    const risk = document.getElementById("filterOppRisk").value;
    const horizon = document.getElementById("filterHorizon").value;
    const sector = document.getElementById("filterSector").value;
    let url = "/api/opportunities?";
    if (risk) url += `risk=${encodeURIComponent(risk)}&`;
    if (horizon) url += `horizon=${encodeURIComponent(horizon)}&`;
    if (sector) url += `sector=${encodeURIComponent(sector)}&`;
    try {
        const opps = await api(url);
        document.getElementById("opportunitiesList").innerHTML = opps.map(o => `
            <div class="opp-card">
                <div class="opp-title">${o.title}</div>
                <div class="opp-policy">${o.policy_name} ${o.policy_lifecycle ? `· ${o.policy_lifecycle}` : ""}</div>
                <div class="opp-desc">${o.description||""}</div>
                <div class="opp-tags">
                    <span class="tag tag-category">${o.sector}</span>
                    ${riskTag(o.risk_level)}
                    <span class="tag tag-return">回报:${o.potential_return}</span>
                    <span class="tag tag-horizon">${o.time_horizon}</span>
                    ${o.policy_momentum ? momentumTag(o.policy_momentum) : ""}
                </div>
                ${o.recommended_instruments ? `<div class="opp-instruments">${o.recommended_instruments}</div>` : ""}
            </div>
        `).join("") || '<div class="empty-state">没有匹配的投资机会</div>';
    } catch (e) { console.error("Opps error:", e); }
}

// ==================== News ====================
async function loadNews() {
    const sentiment = document.getElementById("filterNewsSentiment").value;
    let url = "/api/news?limit=50";
    if (sentiment) url += `&sentiment=${encodeURIComponent(sentiment)}`;
    try {
        const news = await api(url);
        document.getElementById("newsList").innerHTML = news.map(n => `
            <div class="news-item">
                <div class="news-title"><a href="${n.url}" target="_blank">${n.title}</a></div>
                <div class="news-summary">${n.summary||""}</div>
                <div class="news-meta">
                    <span class="tag tag-category">${n.policy_name}</span>
                    ${sentimentTag(n.sentiment)}
                    <span>${n.published_at||""}</span>
                </div>
            </div>
        `).join("") || '<div class="empty-state">暂无新闻，点击右上角更新数据</div>';
    } catch (e) { console.error("News error:", e); }
}

// ==================== Trigger Update ====================
async function triggerUpdate() {
    if (!confirm("确定要触发数据更新？这需要几分钟。")) return;
    try {
        await fetch(API + "/api/update/trigger", {method:"POST"});
        alert("更新已在后台启动");
    } catch (e) { alert("更新失败: " + e.message); }
}

// ==================== Settings ====================
async function loadSettings() {
    try {
        const cfg = await api("/api/llm/config");
        document.getElementById("apiKeyStatus").innerHTML = cfg.api_key_configured
            ? '<span style="color:#10b981">&#10003; API Key 已配置</span>'
            : '<span style="color:#f59e0b">&#9888; 未配置 — 请输入API Key后保存</span>';
        document.getElementById("settingModel").value = cfg.anthropic_model || "claude-sonnet-4-6";
        document.getElementById("settingThreshold").value = cfg.auto_apply_threshold || "0.85";
        if (cfg.api_key_configured) {
            document.getElementById("settingApiKey").placeholder = "sk-ant-****（已配置，留空则保持不变）";
        }
    } catch (e) { console.error("Config load error:", e); }

    loadCostStats();
    loadUpdateHistory();
    loadPendingReviews();
}

async function loadCostStats() {
    try {
        const c = await api("/api/llm/costs");
        document.getElementById("costStats").innerHTML = `
            <div class="cost-row"><span>今日</span><span>${c.today.calls} 次调用</span><span>${c.today.input_tokens + c.today.output_tokens} tokens</span><span>$${c.today.cost.toFixed(4)}</span></div>
            <div class="cost-row"><span>累计</span><span>${c.total.calls} 次调用</span><span>${c.total.input_tokens + c.total.output_tokens} tokens</span><span>$${c.total.cost.toFixed(4)}</span></div>
            <div class="cost-row muted"><span>日费用上限: $${c.daily_cap_usd}</span></div>
        `;
    } catch (e) { document.getElementById("costStats").textContent = "加载失败"; }
}

async function loadUpdateHistory() {
    try {
        const rows = await api("/api/updates");
        document.getElementById("updateHistory").innerHTML = rows.slice(0, 8).map(u => `
            <div class="history-row">
                <span class="tag tag-${u.status === 'completed' ? 'momentum-加速' : 'momentum-减速'}">${u.status}</span>
                <span>${u.update_type}</span>
                <span>${u.records_updated || 0} 条</span>
                <span class="muted">${u.started_at || ""}</span>
            </div>
        `).join("") || "暂无更新记录";
    } catch (e) { document.getElementById("updateHistory").textContent = "加载失败"; }
}

async function loadPendingReviews() {
    try {
        const reviews = await api("/api/reviews/pending");
        document.getElementById("reviewBadge").textContent = reviews.length;
        if (!reviews.length) {
            document.getElementById("pendingReviews").innerHTML = "暂无待审核项";
            return;
        }
        document.getElementById("pendingReviews").innerHTML = reviews.map(r => {
            let changes = typeof r.proposed_changes === "string" ? JSON.parse(r.proposed_changes) : r.proposed_changes;
            let changeList = [];
            if (changes.lifecycle_stage_change) changeList.push(`生命周期: ${changes.lifecycle_stage_change.old} → ${changes.lifecycle_stage_change.new}`);
            if (changes.intensity_update) changeList.push(`力度: ${changes.intensity_update.old} → ${changes.intensity_update.new}`);
            if (changes.effectiveness_update) changeList.push(`效果: ${changes.effectiveness_update.old} → ${changes.effectiveness_update.new}`);
            if (changes.momentum_change) changeList.push(`动量: ${changes.momentum_change.old} → ${changes.momentum_change.new}`);
            return `
            <div class="review-item">
                <div class="review-header">
                    <strong>${r.policy_name}</strong>
                    <span class="tag tag-category">置信度 ${(r.confidence * 100).toFixed(0)}%</span>
                </div>
                <div class="review-changes">${changeList.map(c => `<div>&#8226; ${c}</div>`).join("")}</div>
                <div class="review-reasoning">${r.reasoning || ""}</div>
                <div class="review-actions">
                    <button class="btn btn-sm btn-primary" onclick="approveReview(${r.id})">批准</button>
                    <button class="btn btn-sm" onclick="rejectReview(${r.id})">拒绝</button>
                </div>
            </div>`;
        }).join("");
    } catch (e) { document.getElementById("pendingReviews").textContent = "加载失败"; }
}

async function saveSettings() {
    const keyInput = document.getElementById("settingApiKey").value.trim();
    const model = document.getElementById("settingModel").value;
    const threshold = document.getElementById("settingThreshold").value;

    try {
        if (keyInput) {
            const res = await fetch(API + "/api/llm/api-key", {
                method: "POST", headers: {"Content-Type": "application/json"},
                body: JSON.stringify({api_key: keyInput})
            });
            if (!res.ok) { const e = await res.json(); alert(e.detail || "API Key 设置失败"); return; }
        }
        await fetch(API + "/api/llm/config", {
            method: "PUT", headers: {"Content-Type": "application/json"},
            body: JSON.stringify({anthropic_model: model, auto_apply_threshold: threshold})
        });
        document.getElementById("settingApiKey").value = "";
        alert("设置已保存");
        loadSettings();
    } catch (e) { alert("保存失败: " + e.message); }
}

function toggleKeyVisibility() {
    const input = document.getElementById("settingApiKey");
    input.type = input.type === "password" ? "text" : "password";
}

function showUpdateStatus(msg, type) {
    const el = document.getElementById("updateStatus");
    el.style.display = "block";
    el.className = `update-status update-status-${type}`;
    el.textContent = msg;
}

async function triggerSignals() {
    document.getElementById("btnSignals").disabled = true;
    showUpdateStatus("信号采集中... 预计需要3-5分钟", "info");
    try {
        const res = await fetch(API + "/api/update/trigger-signals", {method: "POST"});
        const data = await res.json();
        showUpdateStatus("信号采集已在后台启动", "ok");
    } catch (e) { showUpdateStatus("触发失败: " + e.message, "error"); }
    setTimeout(() => { document.getElementById("btnSignals").disabled = false; }, 5000);
}

async function triggerLlmUpdate() {
    const cfg = await api("/api/llm/config");
    if (!cfg.api_key_configured) { alert("请先配置 API Key"); return; }
    document.getElementById("btnLlm").disabled = true;
    showUpdateStatus("AI 分析更新中... 正在采集信号 → Claude分析 → 应用变更", "info");
    try {
        await fetch(API + "/api/update/trigger-llm", {method: "POST"});
        showUpdateStatus("LLM 更新已在后台启动，完成后请刷新页面查看结果", "ok");
    } catch (e) { showUpdateStatus("触发失败: " + e.message, "error"); }
    setTimeout(() => { document.getElementById("btnLlm").disabled = false; }, 5000);
}

async function triggerNewsUpdate() {
    showUpdateStatus("新闻采集中...", "info");
    try {
        await fetch(API + "/api/update/trigger", {method: "POST"});
        showUpdateStatus("新闻采集已在后台启动", "ok");
    } catch (e) { showUpdateStatus("触发失败: " + e.message, "error"); }
}

async function approveReview(logId) {
    if (!confirm("确认批准此变更？将立即应用到数据库。")) return;
    try {
        await fetch(API + `/api/reviews/${logId}/approve`, {method: "POST"});
        loadPendingReviews();
        loadCostStats();
    } catch (e) { alert("操作失败"); }
}

async function rejectReview(logId) {
    const reason = prompt("拒绝原因（可选）：");
    try {
        await fetch(API + `/api/reviews/${logId}/reject?reason=${encodeURIComponent(reason||"")}`, {method: "POST"});
        loadPendingReviews();
    } catch (e) { alert("操作失败"); }
}

// ==================== Init ====================
async function initFilters() {
    try {
        const f = await api("/api/filters");
        const fillSelect = (id, items, valKey, labelKey) => {
            const sel = document.getElementById(id);
            if (!sel) return;
            items.forEach(item => {
                const opt = document.createElement("option");
                if (typeof item === "string") { opt.value = item; opt.textContent = item; }
                else { opt.value = item[valKey||"id"]; opt.textContent = item[labelKey||"name"]; }
                sel.appendChild(opt);
            });
        };
        fillSelect("filterCategory", f.categories);
        fillSelect("lcFilterCategory", f.categories);
        fillSelect("dtFilterCategory", f.categories);
        fillSelect("filterStage", f.stages);
        fillSelect("lcFilterStage", f.stages);
        fillSelect("dtFilterStage", f.stages);

        const legend = document.getElementById("lifecycleLegend");
        if (legend) {
            legend.innerHTML = STAGE_ORDER.map(s => `
                <div class="legend-item" onclick="document.getElementById('lcFilterStage').value='${s}';loadLifecycleView()">
                    <div class="legend-dot" style="background:${STAGE_COLORS[s]}"></div><span>${s}</span>
                </div>
            `).join("") + `<div class="legend-item" onclick="document.getElementById('lcFilterStage').value='';loadLifecycleView()">
                <div class="legend-dot" style="background:#666"></div><span>全部</span>
            </div>`;
        }
    } catch (e) { console.error("Filters error:", e); }
}

(async function() {
    await initFilters();
    await loadDashboard();
})();
