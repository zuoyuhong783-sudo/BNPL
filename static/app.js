"use strict";

const steps = ["选择用户", "基本信息", "平台行为", "信用与额度", "确认资料"];
const labels = {
  identity_verified: "实名认证", age: "年龄", linked_card_type: "绑卡类型",
  account_age_months: "注册月数", device_stability: "设备稳定性",
  repayment_fulfilment_rate: "按时履约率", average_monthly_spending: "月均消费",
  completed_order_count: "完成订单数", consecutive_on_time_repayments: "连续按时还款次数",
  adverse_credit_incidents_6m: "近半年失信次数", current_credit_limit: "当前额度",
  available_credit_limit: "可用额度", external_credit_score: "外部信用分",
  external_overdue_record: "外部逾期记录"
};
const ruleText = {
  "SR-01": "实名且绑定信用卡", "SR-02": "实名且绑定借记卡", "SR-03": "未绑定银行卡",
  "SR-04": "注册满 12 个月", "SR-05": "注册 6–11 个月", "SR-06": "注册不足 1 个月",
  "SR-07": "履约率达到 98%", "SR-08": "履约率 95%–98%", "SR-09": "履约率 90%–95%",
  "SR-10": "履约率低于 90%", "SR-11": "月均消费达到 2,000 元", "SR-12": "月均消费 1,000–2,000 元",
  "SR-13": "完成至少 100 笔订单", "SR-14": "完成 50–99 笔订单", "SR-15": "连续按时还款至少 6 次",
  "SR-16": "连续按时还款 3–5 次", "SR-17": "近半年有 1 次失信", "SR-18": "设备稳定",
  "SR-19": "近期设备有变化", "SR-20": "外部信用分至少 800", "SR-21": "外部信用分 550–799",
  "SR-22": "外部信用分 451–549", "SR-23": "轻微外部逾期", "SR-24": "中等外部逾期",
  "SR-25": "严重外部逾期", "SR-26": "确认无外部逾期", "SR-27": "额度使用率 40%–80%",
  "SR-28": "额度使用率低于 20%", "SR-29": "额度使用率高于 90%"
};
const hardText = {
  "HR-01": "实名认证未通过", "HR-02": "年龄低于 18 岁", "HR-03": "近半年失信次数达到 2 次",
  "HR-04": "设备状态异常", "HR-05": "外部信用分不高于 450"
};
const profiles = [
  {
    id: "fresh", title: "全新用户", descriptor: "首次申请 · 正常资料",
    detail: "没有历史额度或还款记录，演示新用户审批路径。",
    data: { identity_verified: true, age: 23, linked_card_type: "Debit", account_age_months: 2,
      repayment_fulfilment_rate: null, average_monthly_spending: 650, completed_order_count: 8,
      consecutive_on_time_repayments: null, adverse_credit_incidents_6m: 0, device_stability: "Stable",
      current_credit_limit: null, available_credit_limit: null, external_credit_score: 650,
      external_overdue_record: "None" }
  },
  {
    id: "increase", title: "老用户想提额", descriptor: "额度审核 · 可做目标诊断",
    detail: "当前额度 5,000 元，查看哪些单项变化可能达到 10,000 元。",
    data: { identity_verified: true, age: 28, linked_card_type: "Credit", account_age_months: 8,
      repayment_fulfilment_rate: 0.99, average_monthly_spending: 2600, completed_order_count: 135,
      consecutive_on_time_repayments: 8, adverse_credit_incidents_6m: 0, device_stability: "Stable",
      current_credit_limit: 5000, available_credit_limit: 250, external_credit_score: 820,
      external_overdue_record: "None" }
  },
  {
    id: "risk", title: "信用风险较高", descriptor: "硬规则 · 一票否决",
    detail: "外部信用分较低，演示硬规则如何覆盖软规则得分。",
    data: { identity_verified: true, age: 31, linked_card_type: "Credit", account_age_months: 18,
      repayment_fulfilment_rate: null, average_monthly_spending: 2400, completed_order_count: 110,
      consecutive_on_time_repayments: null, adverse_credit_incidents_6m: 0, device_stability: "Stable",
      current_credit_limit: null, available_credit_limit: null, external_credit_score: 430,
      external_overdue_record: "Moderate" }
  },
  {
    id: "sparse", title: "资料不完整的新用户", descriptor: "信息覆盖率 · 额度封顶",
    detail: "已知资料表现好，但部分平台与外部信用信息缺失。",
    data: { identity_verified: true, age: 28, linked_card_type: "Credit", account_age_months: 12,
      repayment_fulfilment_rate: null, average_monthly_spending: null, completed_order_count: null,
      consecutive_on_time_repayments: null, adverse_credit_incidents_6m: 0, device_stability: "Stable",
      current_credit_limit: null, available_credit_limit: null, external_credit_score: null,
      external_overdue_record: null }
  }
];

const basicFields = [
  { key: "identity_verified", type: "select", label: "实名认证", required: true,
    options: [["true", "已通过"], ["false", "未通过"]] },
  { key: "age", type: "number", label: "年龄", required: true, min: 0, max: 120, step: 1, unit: "岁" },
  { key: "linked_card_type", type: "select", label: "绑卡类型", required: true,
    options: [["Credit", "信用卡"], ["Debit", "借记卡"], ["Prepaid", "预付卡"], ["None", "未绑卡"]] },
  { key: "account_age_months", type: "number", label: "平台注册时长", required: true, min: 0, step: 1, unit: "个月" },
  { key: "device_stability", type: "select", label: "设备稳定性", required: true,
    options: [["Stable", "稳定"], ["Changing", "近期有变化"], ["Abnormal", "异常"]] }
];
const behaviorFields = [
  { key: "average_monthly_spending", type: "number", label: "月均消费", min: 0, step: 0.01, unit: "元", hint: "留空表示未取得，不代表 0 元。" },
  { key: "completed_order_count", type: "number", label: "完成订单数", min: 0, step: 1, unit: "笔" },
  { key: "repayment_fulfilment_rate", type: "number", label: "按时履约率", min: 0, max: 100, step: 0.01, unit: "%", hint: "老用户适用；输入 98 表示 98%。" },
  { key: "consecutive_on_time_repayments", type: "number", label: "连续按时还款次数", min: 0, step: 1, unit: "次", hint: "老用户适用。" },
  { key: "adverse_credit_incidents_6m", type: "number", label: "近半年失信次数", min: 0, step: 1, unit: "次", hint: "填 0 表示确认无失信；留空表示未知。" }
];
const creditFields = [
  { key: "current_credit_limit", type: "number", label: "当前额度", min: 0, step: 0.01, unit: "元", hint: "新用户不适用。" },
  { key: "available_credit_limit", type: "number", label: "可用额度", min: 0, step: 0.01, unit: "元", hint: "不可高于当前额度。" },
  { key: "external_credit_score", type: "number", label: "外部信用分", min: 350, max: 950, step: 1, unit: "分", hint: "留空表示未取得。" },
  { key: "external_overdue_record", type: "select", label: "外部逾期记录", optional: true,
    options: [["", "未取得"], ["None", "确认无逾期"], ["Minor", "轻微"], ["Moderate", "中等"], ["Serious", "严重"]] }
];

const state = {
  step: 0, selectedProfile: profiles[0].id, applicant: { ...profiles[0].data },
  mode: "new", result: null, returnToReview: false, busy: false
};
const content = document.getElementById("step-content");
const actions = document.getElementById("step-actions");
const errorBox = document.getElementById("form-error");

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}
function money(value) { return Number(value).toLocaleString("zh-CN", { maximumFractionDigits: 2 }); }
function currentMode() { return state.mode === "old" ? "老用户额度审核" : "新用户申请"; }
function showError(message) { errorBox.textContent = message; errorBox.hidden = false; }
function clearError() { errorBox.hidden = true; errorBox.textContent = ""; }
function scrollPanel() { document.querySelector(".panel").scrollIntoView({ behavior: "smooth", block: "start" }); }

function renderProgress() {
  const list = document.getElementById("progress-list");
  list.innerHTML = steps.map((label, index) => {
    const current = state.step === index;
    const done = state.step > index;
    return `<li class="progress-item ${current ? "is-current" : done ? "is-done" : ""}" ${current ? 'aria-current="step"' : ""}>
      <span class="progress-number">${done ? "✓" : index + 1}</span><span>${label}</span></li>`;
  }).join("");
  document.getElementById("step-count").textContent = state.step === 5 ? "审批结果" : `步骤 ${state.step + 1} / 5`;
  const pill = document.getElementById("profile-pill");
  pill.hidden = state.step === 0;
  pill.textContent = profiles.find(profile => profile.id === state.selectedProfile)?.title || "自定义用户";
}

function renderProfileStep() {
  content.innerHTML = `<h2>选一个用户情景开始</h2>
    <p class="section-lead">四类示例覆盖首次申请、提额、硬规则拒绝和资料不足。选择后，所有资料都可以修改。</p>
    <div class="persona-grid">${profiles.map((profile, index) => `
      <button type="button" class="persona-card ${state.selectedProfile === profile.id ? "is-selected" : ""}"
        data-profile="${profile.id}" aria-pressed="${state.selectedProfile === profile.id}">
        <span class="persona-index">情景 0${index + 1} · ${escapeHTML(profile.descriptor)}</span>
        <span class="persona-title">${escapeHTML(profile.title)}</span>
        <span class="persona-desc">${escapeHTML(profile.detail)}</span>
      </button>`).join("")}</div>
    <div class="tip-strip"><span>提示</span> 示例数据完全虚构，只用于观察规则推理过程。</div>`;
  content.querySelectorAll("[data-profile]").forEach(button => button.addEventListener("click", () => {
    const profile = profiles.find(item => item.id === button.dataset.profile);
    state.selectedProfile = profile.id;
    state.applicant = { ...profile.data };
    state.mode = profile.data.current_credit_limit === null ? "new" : "old";
    render();
  }));
  actions.innerHTML = `<span class="muted" style="font-size:12px">下一步可编辑所有字段</span>
    <button type="button" class="button button-primary action-right" id="next-button">下一步 <span aria-hidden="true">→</span></button>`;
  document.getElementById("next-button").addEventListener("click", () => navigate(1));
}

function fieldHTML(config) {
  const value = state.applicant[config.key];
  const uiValue = value === null || value === undefined ? "" :
    config.key === "repayment_fulfilment_rate" ? String(Math.round(value * 10000) / 100) : String(value);
  const required = config.required ? "required" : "";
  let control;
  if (config.type === "select") {
    const options = config.options.map(([optionValue, label]) =>
      `<option value="${escapeHTML(optionValue)}" ${uiValue === optionValue ? "selected" : ""}>${escapeHTML(label)}</option>`).join("");
    control = `<select id="${config.key}" data-field="${config.key}" ${required}>${options}</select>`;
  } else {
    const min = config.min === undefined ? "" : `min="${config.min}"`;
    const max = config.max === undefined ? "" : `max="${config.max}"`;
    control = `<input id="${config.key}" data-field="${config.key}" type="number" inputmode="decimal"
      value="${escapeHTML(uiValue)}" ${min} ${max} step="${config.step || "any"}" ${required} placeholder="未取得">`;
  }
  return `<div class="field"><label class="field-label" for="${config.key}">${config.label}
      <small>${config.unit || (config.required ? "必填" : "可选")}</small></label>${control}
    ${config.hint ? `<span class="field-help">${config.hint}</span>` : ""}</div>`;
}

function renderFormStep(step) {
  const config = {
    1: { title: "先确认基本信息", lead: "身份、年龄和设备状态会参与硬规则判断。", fields: basicFields },
    2: { title: "查看平台行为", lead: "消费与订单表现参与软规则；老用户的还款历史也在此填写。", fields: behaviorFields },
    3: { title: "补充信用与额度", lead: "外部信用和现有额度会影响审批及提额判断。", fields: creditFields }
  }[step];
  const modeControl = step === 1 ? `<div class="field span-2">
    <label class="field-label" for="application_mode">申请类型 <small>影响适用规则</small></label>
    <select id="application_mode"><option value="new" ${state.mode === "new" ? "selected" : ""}>新用户申请</option>
      <option value="old" ${state.mode === "old" ? "selected" : ""}>老用户额度审核</option></select></div>` : "";
  const banner = step === 3 ? `<div class="mode-banner"><strong>${currentMode()}</strong>
    <span>${state.mode === "new" ? "新用户的当前额度、可用额度应为空；系统会根据资料计算首批额度。" : "老用户需提供当前额度与可用额度，系统会判断维持、增加或降低。"}</span></div>` : "";
  content.innerHTML = `<h2>${config.title}</h2><p class="section-lead">${config.lead}</p>${banner}
    <form id="step-form" novalidate><div class="form-grid">${modeControl}${config.fields.map(fieldHTML).join("")}</div></form>`;
  if (step === 1) {
    document.getElementById("application_mode").addEventListener("change", event => {
      state.mode = event.target.value;
      if (state.mode === "new") {
        state.applicant.current_credit_limit = null;
        state.applicant.available_credit_limit = null;
        state.applicant.repayment_fulfilment_rate = null;
        state.applicant.consecutive_on_time_repayments = null;
      } else if (state.applicant.current_credit_limit === null) {
        state.applicant.current_credit_limit = 5000;
        state.applicant.available_credit_limit = 5000;
      }
    });
  }
  if (step === 3) {
    for (const key of ["current_credit_limit", "available_credit_limit"]) {
      document.getElementById(key).disabled = state.mode === "new";
    }
  }
  if (step === 2 && state.mode === "new") {
    for (const key of ["repayment_fulfilment_rate", "consecutive_on_time_repayments"]) {
      document.getElementById(key).disabled = true;
    }
  }
  actions.innerHTML = `<button type="button" class="button button-secondary" id="back-button">← 返回</button>
    <button type="button" class="button button-primary action-right" id="next-button">${state.returnToReview ? "保存并返回确认" : "下一步"} →</button>`;
  document.getElementById("back-button").addEventListener("click", () => {
    if (state.returnToReview) { state.returnToReview = false; navigate(4); }
    else navigate(step - 1);
  });
  document.getElementById("next-button").addEventListener("click", () => {
    if (!saveForm(config.fields)) return;
    if (state.returnToReview) { state.returnToReview = false; navigate(4); }
    else navigate(step + 1);
  });
}

function saveForm(fields) {
  const form = document.getElementById("step-form");
  if (!form.reportValidity()) { showError("请检查必填项及数值范围。"); return false; }
  const next = { ...state.applicant };
  for (const field of fields) {
    const input = document.getElementById(field.key);
    if (input.disabled) continue;
    let value = input.value;
    if (field.key === "identity_verified") value = value === "true";
    else if (field.type === "number") value = value.trim() === "" ? null : Number(value);
    else if (field.optional && value === "") value = null;
    if (field.key === "repayment_fulfilment_rate" && value !== null) value /= 100;
    next[field.key] = value;
  }
  if (state.step === 1 && state.mode === "new") {
    next.current_credit_limit = null;
    next.available_credit_limit = null;
  }
  if (state.step === 3 && state.mode === "old") {
    if (next.current_credit_limit === null || next.available_credit_limit === null) {
      showError("老用户必须同时填写当前额度和可用额度。"); return false;
    }
    if (next.available_credit_limit > next.current_credit_limit) {
      showError("可用额度不能高于当前额度。"); return false;
    }
  }
  state.applicant = next;
  clearError();
  return true;
}

function displayValue(key, value) {
  if (value === null || value === undefined) return "未取得／不适用";
  if (key === "identity_verified") return value ? "已通过" : "未通过";
  if (key === "linked_card_type") return ({ Credit: "信用卡", Debit: "借记卡", Prepaid: "预付卡", None: "未绑卡" })[value] || value;
  if (key === "device_stability") return ({ Stable: "稳定", Changing: "近期有变化", Abnormal: "异常" })[value] || value;
  if (key === "external_overdue_record") return ({ None: "确认无逾期", Minor: "轻微", Moderate: "中等", Serious: "严重" })[value] || value;
  if (key === "repayment_fulfilment_rate") return `${Math.round(value * 10000) / 100}%`;
  const unit = ({ age: " 岁", account_age_months: " 个月", average_monthly_spending: " 元",
    completed_order_count: " 笔", consecutive_on_time_repayments: " 次",
    adverse_credit_incidents_6m: " 次", current_credit_limit: " 元",
    available_credit_limit: " 元", external_credit_score: " 分" })[key] || "";
  return `${money(value)}${unit}`;
}
function reviewGroup(title, fields, editStep) {
  return `<div class="review-section"><div class="review-heading"><h3>${title}</h3>
    <button type="button" class="text-button" data-edit-step="${editStep}">修改这部分</button></div>
    <div class="review-grid">${fields.map(field => `<div class="review-item"><span>${escapeHTML(labels[field.key])}</span>
      <strong>${escapeHTML(displayValue(field.key, state.applicant[field.key]))}</strong></div>`).join("")}</div></div>`;
}

function renderReview() {
  content.innerHTML = `<h2>提交前，再核对一次</h2>
    <p class="section-lead">当前为${currentMode()}。可点击各部分的“修改”返回编辑；只有点击提交后才会运行规则。</p>
    ${reviewGroup("基本信息", basicFields, 1)}
    ${reviewGroup("平台行为", behaviorFields, 2)}
    ${reviewGroup("信用与额度", creditFields, 3)}
    <p class="consent-line">提示：外部逾期“确认无逾期”和“未取得”含义不同；请按真实数据选择。</p>`;
  content.querySelectorAll("[data-edit-step]").forEach(button => button.addEventListener("click", () => {
    state.returnToReview = true;
    navigate(Number(button.dataset.editStep));
  }));
  actions.innerHTML = `<button type="button" class="button button-secondary" id="back-button">← 返回修改</button>
    <button type="button" class="button button-primary action-right" id="submit-button">提交并查看结果 →</button>`;
  document.getElementById("back-button").addEventListener("click", () => navigate(3));
  document.getElementById("submit-button").addEventListener("click", submitApplicant);
}

function formatPercent(value) { return value === null ? "—" : `${Math.round(value * 10000) / 100}%`; }
function resultDecision(result) {
  if (result.decision === "reject") return "硬规则拒绝";
  if (result.decision === "suspend") return "硬规则暂停";
  if (result.decision === "rejected") return "未获批";
  if (result.decision === "conditional-approval") return "有条件批准";
  return "审批通过";
}
function renderResult() {
  const result = state.result;
  const negative = result.approved_limit === 0;
  const trace = result.hard_decision
    ? `<div class="explain-row"><strong>${escapeHTML(result.hard_decision.rule_id)}</strong><span>${escapeHTML(hardText[result.hard_decision.rule_id] || result.hard_decision.reason)}。硬规则优先，额度归零。</span></div>`
    : `<div class="metric-row">
        <div class="metric"><label>最终 CF</label><strong>${result.combined_cf.toFixed(4)}</strong></div>
        <div class="metric"><label>原始 CF / 适用满分</label><strong>${result.raw_cf_sum.toFixed(2)} / ${result.applicable_positive_cf_max.toFixed(2)}</strong></div>
        <div class="metric"><label>信息覆盖率</label><strong>${formatPercent(result.evidence_coverage)}</strong></div>
      </div>
      ${result.tier_cap ? `<div class="explain-row"><strong>${escapeHTML(result.tier_cap.rule_id)}</strong><span>CF 对应额度 ${money(result.cf_based_limit)} 元；新用户信息覆盖率最高允许 ${money(result.tier_cap.maximum_limit)} 元。${result.cap_applied ? "本次已触发封顶。" : "本次未压低额度。"}</span></div>` : ""}
      <div class="divider"></div><h3 class="minor-title">本次触发的软规则</h3>
      ${result.triggered_soft_rules.length ? `<ul class="rules-list">${result.triggered_soft_rules.map(rule => `
        <li><span class="rule-id">${escapeHTML(rule.rule_id)}</span><span>${escapeHTML(ruleText[rule.rule_id] || rule.reason)}</span>
        <span class="rule-cf ${rule.cf < 0 ? "negative" : ""}">${rule.cf > 0 ? "+" : ""}${rule.cf.toFixed(2)}</span></li>`).join("")}</ul>` : `<p class="muted">本次没有软规则贡献。</p>`}`;
  content.innerHTML = `<h2>规则已完成评估</h2><p class="section-lead">结果来自当前输入与课堂规则库，可返回修改资料重新计算。</p>
    <div class="result-head"><div><div class="result-kicker">最终额度 · CNY</div>
      <div class="result-value">${money(result.approved_limit)} <span>元</span></div></div>
      <span class="decision-badge ${negative ? "is-negative" : ""}">${resultDecision(result)}</span></div>
    ${trace}
    <div class="diagnosis-panel"><h3 class="minor-title">目标额度诊断</h3>
      <p class="section-lead">选择期望额度，查看目前的阻断因素。下方每项结果都假设只改变该项条件，其他资料保持不变；模拟不是当前达标状态或提额承诺。</p>
      <div class="diagnosis-toolbar"><label for="target-limit">目标额度</label>
        <select id="target-limit"><option value="1000">1,000 元</option><option value="5000">5,000 元</option>
          <option value="10000" ${result.approved_limit !== 1000 ? "selected" : ""}>10,000 元</option></select>
        <button type="button" class="button button-secondary" id="diagnose-button">查看诊断</button></div>
      <div id="diagnosis-output" class="diagnosis-output" aria-live="polite"></div></div>`;
  actions.innerHTML = `<button type="button" class="button button-secondary" id="edit-button">← 修改资料并重算</button>
    <button type="button" class="button button-quiet action-right" id="restart-button">选择其他示例</button>`;
  document.getElementById("edit-button").addEventListener("click", () => navigate(4));
  document.getElementById("restart-button").addEventListener("click", () => navigate(0));
  document.getElementById("diagnose-button").addEventListener("click", runDiagnosis);
}

function renderDiagnosis(diagnosis) {
  const output = document.getElementById("diagnosis-output");
  if (diagnosis.status === "blocked-by-hard-rule") {
    output.innerHTML = `<div class="explain-row"><strong>硬规则阻断</strong><span>${escapeHTML(hardText[diagnosis.blocking_rule.rule_id] || diagnosis.message)}。本次不进行提额模拟。</span></div>`;
    return;
  }
  if (diagnosis.status === "goal-achieved") {
    output.innerHTML = `<div class="explain-row"><strong>已达到目标</strong><span>当前评估额度已达到或超过所选目标。</span></div>`;
    return;
  }
  if (diagnosis.status === "blocked-by-evidence-cap") {
    const missing = diagnosis.missing_evidence_fields.map(key => labels[key] || key).join("、") || "相关信息";
    output.innerHTML = `<div class="explain-row"><strong>信息封顶</strong><span>当前最高档位为 ${money(diagnosis.tier_cap.maximum_limit)} 元。缺失：${escapeHTML(missing)}。请补充真实资料后重新评估；补齐不保证提额。</span></div>`;
    return;
  }
  const scenarios = diagnosis.single_change_scenarios || [];
  const success = scenarios.filter(scenario => scenario.reaches_goal);
  output.innerHTML = `<p>当前距目标 CF 仍差 <strong>${diagnosis.raw_cf_gap.toFixed(4)}</strong> 原始 CF。${success.length ? `分别模拟下列变化后，其中 ${success.length} 项可达到目标。` : "已测试的单项变化均不足以达到目标。"}</p>
    <div class="scenario-list">${scenarios.map(scenario => `<div class="scenario ${scenario.reaches_goal ? "is-success" : ""}">
      <span>${escapeHTML(scenario.description)}<br><span class="muted">模拟 CF ${scenario.simulated_cf.toFixed(4)} · 额度 ${money(scenario.simulated_limit)} 元</span></span>
      <strong>${scenario.reaches_goal ? "单项改善后可达标" : "单项改善后仍未达标"}</strong></div>`).join("")}</div>`;
}

async function submitApplicant() {
  if (state.busy) return;
  state.busy = true;
  const button = document.getElementById("submit-button");
  button.disabled = true; button.textContent = "正在运行规则…";
  clearError();
  try {
    const response = await fetch("/api/evaluate", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ applicant: state.applicant }) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "评估失败，请检查输入。");
    state.result = payload.result;
    navigate(5);
  } catch (error) {
    showError(error.message || "无法连接本地服务，请重试。");
    button.disabled = false; button.textContent = "提交并查看结果 →";
  } finally { state.busy = false; }
}

async function runDiagnosis() {
  const button = document.getElementById("diagnose-button");
  button.disabled = true; button.textContent = "正在诊断…";
  const output = document.getElementById("diagnosis-output");
  output.textContent = "正在逐项重跑规则，请稍候。";
  try {
    const target = Number(document.getElementById("target-limit").value);
    const response = await fetch("/api/diagnose", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ applicant: state.applicant, target_limit: target }) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "诊断失败。");
    renderDiagnosis(payload.result);
  } catch (error) {
    output.textContent = error.message || "诊断失败，请重试。";
  } finally { button.disabled = false; button.textContent = "查看诊断"; }
}

function navigate(step) {
  state.step = step;
  clearError();
  render();
  scrollPanel();
}
function render() {
  renderProgress();
  if (state.step === 0) renderProfileStep();
  else if (state.step >= 1 && state.step <= 3) renderFormStep(state.step);
  else if (state.step === 4) renderReview();
  else renderResult();
}
render();
