(function () {
  "use strict";

  const data = window.MINISO_DEMO_DATA;
  const validViews = ["overview", "trends", "candidates", "validation", "decision", "evidence"];
  const state = {
    view: "overview",
    signal: data.signals[0].id,
    candidate: data.candidates[0].id,
    filter: "all",
    compare: new Set(),
    audits: loadSessionAudits()
  };

  const byId = (id) => document.getElementById(id);
  const candidateById = (id) => data.candidates.find((item) => item.id === id) || data.candidates[0];
  const signalById = (id) => data.signals.find((item) => item.id === id) || data.signals[0];

  function refreshIcons() {
    if (window.lucide) {
      window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function loadSessionAudits() {
    try {
      const stored = sessionStorage.getItem("miniso-demo-audits");
      return stored ? JSON.parse(stored) : [...data.audit];
    } catch (_error) {
      return [...data.audit];
    }
  }

  function saveSessionAudits() {
    try {
      sessionStorage.setItem("miniso-demo-audits", JSON.stringify(state.audits));
    } catch (_error) {
      // Session persistence is optional for this static demonstration.
    }
  }

  function showToast(message) {
    const toast = byId("toast");
    byId("toast-text").textContent = message;
    toast.classList.add("visible");
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 3200);
  }

  function switchView(view, updateHash = true) {
    if (!validViews.includes(view)) return;
    state.view = view;
    document.querySelectorAll(".view").forEach((section) => {
      section.classList.toggle("active", section.id === `view-${view}`);
    });
    document.querySelectorAll(".nav-item").forEach((button) => {
      button.classList.toggle("active", button.dataset.view === view);
    });
    const active = byId(`view-${view}`);
    byId("topbar-title").textContent = active.dataset.title;
    document.body.classList.remove("nav-open");
    if (updateHash && window.location.hash !== `#${view}`) {
      history.replaceState(null, "", `#${view}`);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function statusPill(label, stateClass) {
    return `<span class="state-pill ${stateClass}">${escapeHtml(label)}</span>`;
  }

  function renderSignals() {
    const list = byId("signal-list");
    list.innerHTML = data.signals.map((signal) => `
      <button class="signal-item ${signal.id === state.signal ? "active" : ""}" data-signal="${signal.id}" type="button">
        <span class="signal-icon"><i data-lucide="${signal.state === "success" ? "trending-up" : signal.state === "review" ? "activity" : "minus"}" aria-hidden="true"></i></span>
        <span>
          <strong>${escapeHtml(signal.name)}</strong>
          <small>${escapeHtml(signal.alias)} · ${escapeHtml(signal.decision)}</small>
        </span>
        <span class="signal-score">
          <strong>${signal.momentum}</strong>
          <small>动量</small>
        </span>
      </button>
    `).join("");
    list.querySelectorAll("[data-signal]").forEach((button) => {
      button.addEventListener("click", () => {
        state.signal = button.dataset.signal;
        renderSignals();
        renderSignalDetail();
      });
    });
    refreshIcons();
  }

  function renderSignalDetail() {
    const signal = signalById(state.signal);
    const maxCorrelation = Math.max(...signal.correlations);
    byId("signal-detail").innerHTML = `
      <div class="signal-headline">
        <div>
          <span class="panel-kicker">${escapeHtml(signal.id)} · ${escapeHtml(signal.alias)}</span>
          <h2>${escapeHtml(signal.name)}</h2>
          <p>${escapeHtml(signal.description)}</p>
        </div>
        ${statusPill(signal.decision, signal.state)}
      </div>
      <div class="signal-stat-grid">
        <div><span>趋势动量</span><strong>${signal.momentum}</strong><small>${escapeHtml(signal.change)} / 30 天</small></div>
        <div><span>最优滞后</span><strong>${signal.bestLag || "—"}</strong><small>${signal.bestLag ? "天" : "未通过"}</small></div>
        <div><span>最小 p 值</span><strong>${escapeHtml(signal.pValue)}</strong><small>预测领先性检验</small></div>
        <div><span>方向复核</span><strong>${signal.state === "success" ? "双向" : signal.state === "review" ? "单期" : "未通过"}</strong><small>${escapeHtml(signal.direction)}</small></div>
      </div>
      <span class="panel-kicker">滞后相关性 · lag 1-7</span>
      <div class="lag-chart" role="img" aria-label="${escapeHtml(signal.name)}在 1 到 7 天滞后下的相关性柱状图">
        ${signal.correlations.map((value, index) => `
          <div class="lag-bar ${index + 1 === signal.bestLag ? "best" : ""}">
            <i style="height:${Math.max(8, Math.round((value / maxCorrelation) * 100))}%" title="lag ${index + 1}: ${value.toFixed(2)}"></i>
            <span>L${index + 1}</span>
          </div>
        `).join("")}
      </div>
      <p class="signal-footnote"><i data-lucide="info" aria-hidden="true"></i>Granger 结果只表示所设模型与样本内的预测领先性，不等于结构因果。真实验证仍需反向检验、多重比较修正和业务事件分析。</p>
    `;
    refreshIcons();
  }

  function filteredCandidates() {
    if (state.filter === "pareto") return data.candidates.filter((item) => item.status === "pareto");
    if (state.filter === "risk") return data.candidates.filter((item) => item.riskLevel === "risk");
    return data.candidates;
  }

  function scoreCell(value, type) {
    return `
      <td class="score-cell">
        <div class="score-inline ${type}">
          <div class="bar-track"><i style="width:${Math.round(value * 100)}%"></i></div>
          <strong>${value.toFixed(2)}</strong>
        </div>
      </td>
    `;
  }

  function renderCandidateTable() {
    const candidates = filteredCandidates();
    byId("candidate-count").textContent = `${candidates.length} 个候选 · ${candidates.filter((item) => item.status === "pareto").length} 个非支配解`;
    byId("candidate-table-body").innerHTML = candidates.map((candidate) => `
      <tr class="${candidate.id === state.candidate ? "active" : ""}" data-candidate-row="${candidate.id}">
        <td><input class="compare-check" type="checkbox" data-compare="${candidate.id}" aria-label="将${escapeHtml(candidate.name)}加入对比" ${state.compare.has(candidate.id) ? "checked" : ""}></td>
        <td>
          <div class="candidate-cell">
            <span class="concept-thumb ${candidate.color}"><i data-lucide="${candidate.icon}" aria-hidden="true"></i></span>
            <span><strong>${escapeHtml(candidate.name)}</strong><small>${escapeHtml(candidate.short)} · ${candidate.id}</small></span>
          </div>
        </td>
        ${scoreCell(candidate.objectives.demand, "demand")}
        ${scoreCell(candidate.objectives.dfm, "dfm")}
        ${scoreCell(candidate.objectives.novelty, "novelty")}
        <td>${candidate.status === "pareto" ? statusPill("前沿候选", "success") : statusPill("对照候选", candidate.riskLevel === "risk" ? "danger" : "neutral")}</td>
        <td><button class="row-action" data-open-candidate="${candidate.id}" type="button" aria-label="查看${escapeHtml(candidate.name)}"><i data-lucide="chevron-right" aria-hidden="true"></i></button></td>
      </tr>
    `).join("");

    byId("candidate-table-body").querySelectorAll("[data-candidate-row]").forEach((row) => {
      row.addEventListener("click", (event) => {
        if (event.target.closest("input") || event.target.closest("button")) return;
        selectCandidate(row.dataset.candidateRow);
      });
    });

    byId("candidate-table-body").querySelectorAll("[data-open-candidate]").forEach((button) => {
      button.addEventListener("click", () => selectCandidate(button.dataset.openCandidate));
    });

    byId("candidate-table-body").querySelectorAll("[data-compare]").forEach((checkbox) => {
      checkbox.addEventListener("change", () => toggleCompare(checkbox.dataset.compare, checkbox.checked, checkbox));
    });
    refreshIcons();
  }

  function renderCandidateDetail() {
    const candidate = candidateById(state.candidate);
    const riskState = candidate.riskLevel === "risk" ? "danger" : "review";
    byId("candidate-detail").innerHTML = `
      <div class="candidate-detail-grid">
        <div>
          <div class="candidate-title-block">
            <span class="concept-thumb ${candidate.color}"><i data-lucide="${candidate.icon}" aria-hidden="true"></i></span>
            <div>
              <span class="panel-kicker">${candidate.id} · ${candidate.status === "pareto" ? "PARETO FRONT" : "REFERENCE"}</span>
              <h2>${escapeHtml(candidate.name)}</h2>
              <p>${escapeHtml(candidate.short)} · ${escapeHtml(candidate.material)}</p>
            </div>
          </div>
          <div class="attribute-tags">
            ${candidate.features.map((feature) => `<span>${escapeHtml(feature)}</span>`).join("")}
          </div>
          <div class="candidate-source"><i data-lucide="database" aria-hidden="true"></i><span>${escapeHtml(candidate.source)}</span></div>
        </div>
        <div>
          <div class="objective-list">
            ${objectiveRow("需求潜力", candidate.objectives.demand, "var(--red)")}
            ${objectiveRow("可制造性", candidate.objectives.dfm, "var(--green)")}
            ${objectiveRow("新颖性", candidate.objectives.novelty, "var(--purple)")}
          </div>
          <div class="risk-list">
            ${candidate.risks.map((risk) => `
              <div class="risk-item">
                <i data-lucide="${risk.level === "success" ? "circle-check" : risk.level === "danger" ? "circle-alert" : "triangle-alert"}" aria-hidden="true"></i>
                <span><strong>${escapeHtml(risk.title)}</strong><small>${escapeHtml(risk.detail)}</small></span>
                ${statusPill(risk.level === "success" ? "通过" : risk.level === "danger" ? "阻断" : "待核验", risk.level === "success" ? "success" : riskState)}
              </div>
            `).join("")}
          </div>
        </div>
      </div>
    `;
    refreshIcons();
  }

  function objectiveRow(label, value, color) {
    return `
      <div class="objective-row">
        <span>${label}</span>
        <div class="bar-track"><i style="width:${Math.round(value * 100)}%;background:${color}"></i></div>
        <strong>${value.toFixed(2)}</strong>
      </div>
    `;
  }

  function selectCandidate(id) {
    state.candidate = candidateById(id).id;
    renderCandidateTable();
    renderCandidateDetail();
    renderValidationSelect();
    renderValidation();
    renderDecision();
  }

  function toggleCompare(id, checked, checkbox) {
    if (checked && state.compare.size >= 2) {
      checkbox.checked = false;
      showToast("最多同时比较 2 个候选");
      return;
    }
    if (checked) state.compare.add(id);
    else state.compare.delete(id);
    renderCompareBar();
  }

  function renderCompareBar() {
    const bar = byId("compare-bar");
    const selected = [...state.compare].map(candidateById);
    bar.classList.toggle("visible", selected.length > 0);
    byId("compare-count").textContent = String(selected.length);
    byId("compare-items").innerHTML = selected.map((candidate) => `<span class="compare-item">${escapeHtml(candidate.name)}</span>`).join("");
    byId("compare-button").disabled = selected.length !== 2;
  }

  function openComparison() {
    const selected = [...state.compare].map(candidateById);
    if (selected.length !== 2) return;
    const dialog = document.createElement("dialog");
    dialog.className = "compare-dialog-content";
    dialog.innerHTML = `
      <div class="dialog-heading">
        <div><span class="panel-kicker">候选权衡</span><h2>非单一分数比较</h2></div>
        <button class="icon-button" type="button" data-close-dynamic aria-label="关闭"><i data-lucide="x" aria-hidden="true"></i></button>
      </div>
      <div class="compare-grid">
        ${selected.map((candidate) => `
          <section class="compare-column">
            <h3>${escapeHtml(candidate.name)}</h3>
            <dl>
              <div><dt>需求潜力</dt><dd>${candidate.objectives.demand.toFixed(2)}</dd></div>
              <div><dt>可制造性</dt><dd>${candidate.objectives.dfm.toFixed(2)}</dd></div>
              <div><dt>新颖性</dt><dd>${candidate.objectives.novelty.toFixed(2)}</dd></div>
              <div><dt>弱信号区间</dt><dd>${candidate.validation.lower.toFixed(2)}-${candidate.validation.upper.toFixed(2)}</dd></div>
              <div><dt>主要风险</dt><dd>${escapeHtml(candidate.risks[0].title)}</dd></div>
            </dl>
          </section>
        `).join("")}
      </div>
    `;
    document.body.appendChild(dialog);
    dialog.querySelector("[data-close-dynamic]").addEventListener("click", () => dialog.close());
    dialog.addEventListener("close", () => dialog.remove(), { once: true });
    dialog.showModal();
    refreshIcons();
  }

  function renderValidationSelect() {
    const select = byId("validation-candidate");
    select.innerHTML = data.candidates.map((candidate) => `<option value="${candidate.id}" ${candidate.id === state.candidate ? "selected" : ""}>${escapeHtml(candidate.name)}</option>`).join("");
  }

  function renderValidation() {
    const candidate = candidateById(state.candidate);
    const validation = candidate.validation;
    byId("validation-summary").innerHTML = `
      <div class="panel-heading">
        <div><span class="panel-kicker">聚合弱信号</span><h2>${escapeHtml(candidate.name)}</h2></div>
        ${statusPill("待真实锚定", "review")}
      </div>
      <div class="validation-score">
        <div><strong>${validation.score.toFixed(2)}</strong><small>校准后的演示弱信号</small></div>
        <span class="state-pill neutral">90% 区间</span>
      </div>
      <div class="interval-track" aria-label="弱信号区间 ${validation.lower.toFixed(2)} 到 ${validation.upper.toFixed(2)}，点估计 ${validation.score.toFixed(2)}">
        <span class="interval-range" style="left:${validation.lower * 100}%;width:${(validation.upper - validation.lower) * 100}%"></span>
        <span class="interval-point" style="left:calc(${validation.score * 100}% - 2px)"></span>
      </div>
      <div class="interval-labels"><span>${validation.lower.toFixed(2)} 下界</span><span>${validation.upper.toFixed(2)} 上界</span></div>
      <p class="validation-note">${escapeHtml(validation.summary)}</p>
    `;
    byId("segment-list").innerHTML = validation.segments.map((segment) => `
      <div class="segment-row">
        <div><strong>${escapeHtml(segment.name)}</strong><small>${escapeHtml(segment.note)}</small></div>
        <div class="segment-range" aria-label="${escapeHtml(segment.name)}区间 ${segment.lower.toFixed(2)} 到 ${segment.upper.toFixed(2)}">
          <i style="left:${segment.lower * 100}%;width:${(segment.upper - segment.lower) * 100}%"></i>
          <b style="left:calc(${segment.score * 100}% - 1px)"></b>
        </div>
        <span>${segment.score.toFixed(2)}</span>
      </div>
    `).join("");
    refreshIcons();
  }

  function renderDecision() {
    const candidate = candidateById(state.candidate);
    byId("decision-package").innerHTML = `
      <div class="decision-package-header">
        <span class="concept-thumb ${candidate.color}"><i data-lucide="${candidate.icon}" aria-hidden="true"></i></span>
        <div><h2>${escapeHtml(candidate.name)}</h2><p>${candidate.id} · demo-v2 · ${escapeHtml(candidate.short)}</p></div>
        ${candidate.status === "pareto" ? statusPill("前沿候选", "success") : statusPill("风险候选", "danger")}
      </div>
      <div class="evidence-checks">
        <div class="evidence-check"><i data-lucide="badge-check" aria-hidden="true"></i>趋势证据已关联</div>
        <div class="evidence-check"><i data-lucide="badge-check" aria-hidden="true"></i>多目标分数已版本化</div>
        <div class="evidence-check"><i data-lucide="badge-check" aria-hidden="true"></i>不确定性区间已展示</div>
        <div class="evidence-check"><i data-lucide="badge-check" aria-hidden="true"></i>DFM 风险已生成待办</div>
      </div>
      <div class="decision-form">
        <label for="decision-note">决策理由</label>
        <textarea id="decision-note">综合需求潜力、可制造性与不确定性，建议进入企业历史数据盲测，不直接进入打样。</textarea>
        <div class="decision-actions">
          <button class="decision-action approve" data-decision="approve" type="button"><i data-lucide="check" aria-hidden="true"></i>进入盲测</button>
          <button class="decision-action hold" data-decision="hold" type="button"><i data-lucide="pause" aria-hidden="true"></i>补充证据</button>
          <button class="decision-action reject" data-decision="reject" type="button"><i data-lucide="x" aria-hidden="true"></i>本轮驳回</button>
        </div>
      </div>
    `;
    byId("decision-package").querySelectorAll("[data-decision]").forEach((button) => {
      button.addEventListener("click", () => handleDecision(button.dataset.decision));
    });
    refreshIcons();
  }

  function handleDecision(action) {
    const note = byId("decision-note").value.trim();
    if (!note) {
      showToast("请填写决策理由后再记录");
      byId("decision-note").focus();
      return;
    }
    const candidate = candidateById(state.candidate);
    const labels = {
      approve: ["人工建议进入历史盲测", "进入盲测"],
      hold: ["人工要求补充证据", "补充证据"],
      reject: ["人工驳回本轮候选", "本轮驳回"]
    };
    state.audits.unshift({
      type: action,
      title: labels[action][0],
      detail: `${candidate.name}：${note}`,
      time: new Intl.DateTimeFormat("zh-CN", { dateStyle: "short", timeStyle: "short", hour12: false }).format(new Date())
    });
    saveSessionAudits();
    renderAudit();
    showToast(`已记录“${labels[action][1]}”，未触发任何生产动作`);
  }

  function renderAudit() {
    const iconMap = {
      system: "package-check",
      evidence: "shield-check",
      model: "scan-search",
      approve: "check",
      hold: "pause",
      reject: "x"
    };
    byId("audit-list").innerHTML = state.audits.slice(0, 7).map((entry) => `
      <li class="audit-entry">
        <span class="audit-icon"><i data-lucide="${iconMap[entry.type] || "history"}" aria-hidden="true"></i></span>
        <div class="audit-copy"><strong>${escapeHtml(entry.title)}</strong><span>${escapeHtml(entry.detail)}</span><small>${escapeHtml(entry.time)}</small></div>
      </li>
    `).join("");
    refreshIcons();
  }

  function clearSessionAudits() {
    state.audits = [...data.audit];
    saveSessionAudits();
    renderAudit();
    showToast("本次演示决策记录已重置");
  }

  function openImage(src, alt) {
    const dialog = byId("image-dialog");
    const image = byId("dialog-image");
    image.src = src;
    image.alt = alt;
    dialog.showModal();
  }

  function bindStaticEvents() {
    document.querySelectorAll(".nav-item").forEach((button) => {
      button.addEventListener("click", () => switchView(button.dataset.view));
    });
    document.querySelectorAll("[data-jump]").forEach((button) => {
      button.addEventListener("click", () => switchView(button.dataset.jump));
    });
    document.querySelectorAll("[data-candidate]").forEach((button) => {
      button.addEventListener("click", () => {
        selectCandidate(button.dataset.candidate);
        switchView("candidates");
      });
    });
    document.querySelectorAll(".segmented-control [data-filter]").forEach((button) => {
      button.addEventListener("click", () => {
        state.filter = button.dataset.filter;
        document.querySelectorAll(".segmented-control [data-filter]").forEach((item) => item.classList.toggle("active", item === button));
        renderCandidateTable();
      });
    });
    byId("validation-candidate").addEventListener("change", (event) => selectCandidate(event.target.value));
    byId("compare-button").addEventListener("click", openComparison);
    byId("clear-session").addEventListener("click", clearSessionAudits);
    byId("mobile-menu").addEventListener("click", () => document.body.classList.add("nav-open"));
    byId("sidebar-scrim").addEventListener("click", () => document.body.classList.remove("nav-open"));
    byId("source-button").addEventListener("click", () => byId("source-dialog").showModal());
    byId("expand-architecture").addEventListener("click", () => openImage("assets/architecture.png", "企业级 AI 产品研发决策架构"));
    byId("chart-button").addEventListener("click", () => openImage("assets/backtest_metrics.png", "15 个滚动窗口的回测对比图"));
    document.querySelectorAll("[data-close-dialog]").forEach((button) => {
      button.addEventListener("click", () => button.closest("dialog").close());
    });
    window.addEventListener("hashchange", () => {
      const view = window.location.hash.slice(1);
      if (validViews.includes(view)) switchView(view, false);
    });
  }

  function init() {
    renderSignals();
    renderSignalDetail();
    renderCandidateTable();
    renderCandidateDetail();
    renderCompareBar();
    renderValidationSelect();
    renderValidation();
    renderDecision();
    renderAudit();
    bindStaticEvents();
    const initialView = window.location.hash.slice(1);
    switchView(validViews.includes(initialView) ? initialView : "overview", false);
    refreshIcons();
  }

  init();
}());
