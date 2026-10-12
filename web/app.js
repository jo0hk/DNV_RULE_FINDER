/*
 * app.js — 화면 동작
 *
 *   문장 입력 → /api/search → 출처 카드 표시 → /api/answer → 답변 표시
 *   (검색은 바로 끝나고 LLM 답변은 몇 초 걸리므로, 출처를 먼저 보여 준다)
 */
const $ = (id) => document.getElementById(id);

const HANGUL = /[ㄱ-ㅎㅏ-ㅣ가-힣]/;
const ENGLISH_ONLY = "English only. Please enter the sentence in English.";
const HISTORY_KEY = "dnv-rule-finder-history";
const HISTORY_MAX = 15;
const EXAMPLES = [
  "Emergency towing arrangement SWL changed to 1,000 kN for a 60,000 dwt oil tanker",
  "Bilge plate thickness modified to be thinner than the adjacent bottom plate",
  "Inner bottom plate below a vertically corrugated bulkhead without lower stool is not Z-grade steel",
  "Non-destructive testing omitted after weld repair of a copper alloy casting",
];

let llm = null;          // 서버가 쓰는 LLM 이름. 없으면 검색 결과만 보여 준다
let controller = null;   // 진행 중인 요청. 새 문장을 보내면 취소한다
let answerText = "";     // Copy 버튼이 복사할 답변 원문


// ---------- 서버 호출 ----------
async function api(path, body, signal) {
  const options = body
    ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal }
    : { signal };
  let response;
  try {
    response = await fetch(path, options);
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error("Cannot reach the server. Check that it is still running.");
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data && typeof data.detail === "string" ? data.detail : `Request failed (${response.status}).`;
    throw new Error(detail);
  }
  return data;
}


// ---------- 글자 처리 ----------
function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

/* 한 줄 안의 **굵게**, `코드`, [1] 같은 출처 번호를 HTML로 바꾼다 */
function inline(text, count) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\[(\d{1,2})\]/g, (match, n, offset, whole) => {
      // "Sec.4 [2]"처럼 조항 번호로 쓰인 것은 출처 번호가 아니다
      const isClause = /(Sec|App)\.\s?\w+\s$/.test(whole.slice(Math.max(0, offset - 14), offset));
      if (isClause || n < 1 || n > count) return match;
      return `<button type="button" class="cite" data-n="${n}" title="Show source ${n}">${n}</button>`;
    });
}

/* LLM 답변(간단한 마크다운)을 HTML로 바꾼다. 제목, 번호·글머리 목록, 문단만 다룬다 */
function renderAnswer(text, count) {
  const blocks = [];
  let last = null;     // 바로 앞 블록. 이어지는 줄을 여기에 붙인다
  for (const raw of text.replace(/\r/g, "").split("\n")) {
    const line = raw.replace(/\t/g, "    ");
    if (!line.trim()) { last = null; continue; }

    const heading = line.match(/^\s{0,3}#{1,6}\s+(.*)$/);
    const item = line.match(/^(\s*)(\d{1,2}[.)]|[-*•])\s+(.*)$/);
    if (heading) {
      blocks.push({ type: "h3", lines: [heading[1]] });
      last = null;
    } else if (item) {
      const numbered = /\d/.test(item[2]);
      last = {
        type: "item", lines: [item[3]],
        depth: Math.min(3, Math.floor(item[1].length / 2)),
        marker: numbered ? item[2] : "",
      };
      blocks.push(last);
    } else if (last && (last.type === "p" || /^\s/.test(line))) {
      last.lines.push(line.trim());
    } else {
      last = { type: "p", lines: [line.trim()] };
      blocks.push(last);
    }
  }

  return blocks.map((block) => {
    const body = block.lines.map((line) => inline(line, count)).join("<br>");
    if (block.type === "h3") return `<h3>${body}</h3>`;
    if (block.type === "p") return `<p>${body}</p>`;
    const numbered = block.marker ? " numbered" : "";
    return `<div class="item d${block.depth}${numbered}">`
         + `<span class="marker">${escapeHtml(block.marker)}</span><div>${body}</div></div>`;
  }).join("");
}

function skeleton(lines) {
  return `<div class="skeleton">${"<span></span>".repeat(lines)}</div>`;
}


// ---------- 출처 카드 ----------
function renderSources(sources) {
  const list = $("sources");
  list.innerHTML = "";
  $("source-count").textContent = sources.length;

  for (const source of sources) {
    const parts = source.path.split(" > ").map(escapeHtml);
    const leaf = parts.pop();
    const path = [...parts, `<b>${leaf}</b>`].join("<i>›</i>");
    const href = `/api/pdf/${encodeURIComponent(source.file)}#page=${source.pdf_page}`;

    const card = document.createElement("li");
    card.className = "source";
    card.id = `source-${source.number}`;
    card.innerHTML = `
      <div class="source-head">
        <span class="badge">${source.number}</span>
        <div>
          <div class="ref">${escapeHtml(source.ref)}</div>
          <div class="path">${path}</div>
        </div>
      </div>
      <p class="excerpt">${escapeHtml(source.text)}</p>
      <div class="source-foot">
        <span class="meta">Edition ${escapeHtml(source.edition)} · p.${escapeHtml(source.page)}</span>
        <button type="button" class="link toggle">Show more</button>
        <a class="link" href="${href}" target="_blank" rel="noopener" title="${escapeHtml(source.file)}">Open PDF</a>
      </div>`;
    list.appendChild(card);

    // 발췌문이 5줄 안에 다 들어오면 "Show more"가 필요 없다
    const excerpt = card.querySelector(".excerpt");
    const toggle = card.querySelector(".toggle");
    toggle.hidden = excerpt.scrollHeight <= excerpt.clientHeight + 2;
    toggle.addEventListener("click", () => {
      toggle.textContent = card.classList.toggle("open") ? "Show less" : "Show more";
    });
  }
}

function sourcesLoading() {
  $("source-count").textContent = "";
  $("sources").innerHTML = `<li class="source">${skeleton(4)}</li>`.repeat(3);
}

/* 답변의 [n]을 눌렀을 때: 해당 출처 카드로 이동하고 잠깐 강조한다 */
function focusSource(number) {
  const card = $(`source-${number}`);
  if (!card) return;
  card.scrollIntoView({ behavior: "smooth", block: "nearest" });
  card.classList.remove("flash");
  void card.offsetWidth;            // 애니메이션을 처음부터 다시 돌리기 위해
  card.classList.add("flash");
}


// ---------- 질문 기록 (이 브라우저에만 저장) ----------
function loadHistory() {
  try {
    const saved = JSON.parse(localStorage.getItem(HISTORY_KEY));
    return Array.isArray(saved) ? saved.filter((q) => typeof q === "string") : [];
  } catch {
    return [];
  }
}

function saveHistory(items) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(items));
  } catch {
    // 저장이 막혀 있으면(사생활 보호 모드 등) 기록 없이 쓴다
  }
}

function renderHistory(items) {
  const list = $("history");
  list.innerHTML = "";
  for (const question of items) {
    const row = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = question;
    button.title = question;
    button.addEventListener("click", () => submit(question));
    row.appendChild(button);
    list.appendChild(row);
  }
  $("history-empty").hidden = items.length > 0;
  $("clear-history").hidden = items.length === 0;
}

function remember(question) {
  const items = [question, ...loadHistory().filter((q) => q !== question)].slice(0, HISTORY_MAX);
  saveHistory(items);
  renderHistory(items);
}


// ---------- 화면 상태 ----------
function showNotice(message) {
  $("notice").textContent = message;
  $("notice").hidden = !message;
}

function setBusy(busy) {
  $("submit").disabled = busy;
  $("submit").textContent = busy ? "Checking…" : "Check rules";
}

function showResult(question) {
  $("page").classList.add("has-result");
  $("examples").hidden = true;
  $("result").hidden = false;
  $("asked").textContent = question;
  $("copy").hidden = true;
  answerText = "";
}

function reset() {
  if (controller) controller.abort();
  setBusy(false);
  showNotice("");
  $("page").classList.remove("has-result");
  $("examples").hidden = false;
  $("result").hidden = true;
  $("question").value = "";
  resize();
  $("question").focus();
}

function resize() {
  const box = $("question");
  box.style.height = "auto";
  box.style.height = `${Math.min(box.scrollHeight, 220)}px`;
}


// ---------- 문장 하나 처리 ----------
async function run(question) {
  showNotice("");
  if (!question) return;
  if (HANGUL.test(question)) {
    showNotice(ENGLISH_ONLY);
    return;
  }

  if (controller) controller.abort();
  const mine = controller = new AbortController();

  setBusy(true);
  showResult(question);
  sourcesLoading();
  $("answer").innerHTML = skeleton(6);

  try {
    // (1) 검색: 출처부터 보여 준다
    const found = await api("/api/search", { question }, mine.signal);
    renderSources(found.sources);
    remember(question);

    if (!llm) {
      $("answer").innerHTML = `<div class="box info"><strong>Search results only</strong>
        No LLM API key is configured, so no written answer is generated. The retrieved excerpts are
        listed under Sources. Add a key to <code>.env</code> and restart the server to get an answer.</div>`;
      return;
    }

    // (2) 답변: LLM이 발췌문을 읽고 쓰는 동안 기다린다
    $("answer").innerHTML = `<p class="waiting">Reading the excerpts and writing the answer…</p>${skeleton(6)}`;
    const data = await api("/api/answer", { question }, mine.signal);

    // 답변의 [n]이 화면의 출처 번호와 어긋나지 않게, 검색 결과가 달라졌으면 다시 그린다
    const key = (sources) => sources.map((s) => `${s.ref}|${s.pdf_page}`).join("\n");
    if (key(data.sources) !== key(found.sources)) renderSources(data.sources);

    answerText = data.answer;
    $("answer").innerHTML = renderAnswer(data.answer, data.sources.length);
    $("copy").hidden = false;
    $("copy").textContent = "Copy";
  } catch (error) {
    if (error.name === "AbortError") return;
    if (!$("sources").querySelector(".ref")) {      // 검색 단계에서 실패했으면 출처 칸도 비운다
      $("sources").innerHTML = "";
      $("source-count").textContent = "";
    }
    $("answer").innerHTML = `<div class="box error"><strong>Something went wrong</strong>${escapeHtml(error.message)}</div>`;
  } finally {
    if (controller === mine) setBusy(false);
  }
}

function submit(question) {
  $("question").value = question;
  resize();
  run(question.trim());
}


// ---------- 처음 한 번 ----------
async function loadStatus() {
  const status = $("status");
  try {
    const health = await api("/api/health");
    llm = health.llm;
    $("status-main").textContent = `${health.chunks.toLocaleString("en-US")} chunks indexed`;
    $("status-sub").textContent = llm ? `LLM: ${llm}` : "Search only (no LLM API key)";
    status.className = `status ${llm ? "ok" : "warn"}`;
  } catch (error) {
    $("status-main").textContent = "Server not reachable";
    $("status-sub").textContent = "";
    status.className = "status err";
  }
}

function init() {
  for (const example of EXAMPLES) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "example";
    button.textContent = example;
    button.addEventListener("click", () => submit(example));
    $("example-list").appendChild(button);
  }

  $("form").addEventListener("submit", (event) => {
    event.preventDefault();
    run($("question").value.trim());
  });
  $("question").addEventListener("input", resize);
  $("question").addEventListener("keydown", (event) => {
    // 엔터로 보내기. 한글 조합 중(isComposing)의 엔터는 보내지 않는다
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      $("form").requestSubmit();
    }
  });

  $("new-check").addEventListener("click", reset);
  $("clear-history").addEventListener("click", () => {
    saveHistory([]);
    renderHistory([]);
  });

  $("copy").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(answerText);
      $("copy").textContent = "Copied";
    } catch {
      $("copy").textContent = "Copy failed";
    }
  });

  // 답변의 [n]: 누르면 출처 카드로 이동, 올려 두면 카드에 테두리 표시
  $("answer").addEventListener("click", (event) => {
    const cite = event.target.closest(".cite");
    if (cite) focusSource(cite.dataset.n);
  });
  for (const [type, on] of [["mouseover", true], ["mouseout", false]]) {
    $("answer").addEventListener(type, (event) => {
      const cite = event.target.closest(".cite");
      const card = cite && $(`source-${cite.dataset.n}`);
      if (card) card.classList.toggle("active", on);
    });
  }

  renderHistory(loadHistory());
  loadStatus();
  $("question").focus();
}

init();
