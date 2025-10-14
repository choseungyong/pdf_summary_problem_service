#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local PDF → Quiz & Summary Web App
==================================

A single-file Flask app you can run locally. It lets you upload a PDF, then calls
OpenAI's API to generate:
  • 연습문제(기초) + 심화문제(고급) — 4지선다, 정답/해설 포함
  • 요약 정리본 (Markdown)

UI는 좌/우 2분할:
  • 왼쪽: 문제 풀이(기초/심화 탭, 실시간 정답 체크)
  • 오른쪽: 요약 미리보기 (Markdown 렌더)

또한 생성된 문제와 요약은 /problems, /summaries 에 각기 별도 페이지로 저장/열람 가능.

---
Quickstart
----------
1) Python 3.10+ 권장
2) pip install -r requirements.txt  (필요 패키지: Flask, pypdf, markdown, openai, python-dotenv)
3) 환경변수 설정:  set OPENAI_API_KEY=...  (Windows)  /  export OPENAI_API_KEY=...  (macOS/Linux)
4) python app.py 실행 → 브라우저에서 http://127.0.0.1:5000

파일 구조는 자동 생성됩니다:
  .
  ├─ app.py (이 파일)
  ├─ data/
  │   ├─ problems/  (생성된 문제 JSON들)
  │   └─ summaries/ (생성된 요약 .md들)

메모: OpenAI 요금이 발생하므로, 긴 PDF는 비용이 큼. 필요 시 페이지 제한, 발췌 등으로 줄이세요.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from flask import Flask, request, jsonify, Response, render_template_string, send_from_directory, url_for, redirect
from pypdf import PdfReader
from markdown import markdown

# OpenAI SDK (>=1.40.0)
from openai import OpenAI

# ---------------------------
# Config
# ---------------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PROBLEMS_DIR = DATA_DIR / "problems"
SUMMARIES_DIR = DATA_DIR / "summaries"
for p in [DATA_DIR, PROBLEMS_DIR, SUMMARIES_DIR]:
    p.mkdir(parents=True, exist_ok=True)

MODEL_DEFAULT = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    print("[WARN] OPENAI_API_KEY 가 설정되지 않았습니다. 생성 기능은 동작하지 않습니다.")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ---------------------------
# Helpers
# ---------------------------

def extract_text_from_pdf(fp) -> str:
    """Extract raw text from a PDF file-like object."""
    reader = PdfReader(fp)
    texts: List[str] = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            texts.append("")
    return "\n\n".join(texts).strip()


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def save_json(obj: Any, path: Path) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def sanitize_filename(title: str) -> str:
    title = re.sub(r"[\\/:*?\"<>|]", "_", title).strip()
    return title or now_tag()


# ---------------------------
# Prompting
# ---------------------------

def build_prompt_for_generation(pdf_text: str) -> str:
    return f"""
당신은 대학 수준의 교수 겸 출제위원입니다. 아래 PDF 본문을 바탕으로 다음을 한국어로 생성하세요.

1️⃣ **요약 정리본**
   - 가능한 한 자세하게, 문단 단위로 정리하세요.
   - 구성:
     - (1) 전체 개요 요약 (핵심 주제 3~5줄)
     - (2) 주요 개념 / 정의 / 공식 / 예시를 세부 항목으로 나열
     - (3) 각 단원별 요점, 핵심 키워드 목록
     - (4) 자주 나오는 시험 포인트, 오개념(헷갈리기 쉬운 부분) 정리
     - (5) 관련 용어 정리표 (필요 시 Markdown 표 형태)
   - Markdown 형식(h2/h3, 목록, 표, 수식은 $...$ 또는 ```...```)으로 깔끔하게 작성하세요.

2️⃣ **연습문제 및 심화문제**
   - 총 30문항 (기초 15문항, 심화 15문항)의 4지선다형 문제를 생성하세요.
   - 각 문항은 아래 JSON 구조를 따르세요:
     {{
       "question": "문제 내용",
       "choices": ["보기1","보기2","보기3","보기4"],
       "answer_index": 0,
       "explanation": "정답 이유 또는 개념 요약"
     }}
   - 조건:
     - 보기 문장은 간결하고 모두 실제 학습 내용 기반이어야 함
     - 오답은 헷갈리지만 틀린 선택지로 구성
     - 중복 표현 금지
     - 정답은 균등하게 분포하도록 구성 (0~3 고르게)
     - 기초: 정의, 개념, 이해 중심
     - 심화: 응용, 비교, 계산, 상황 판단 문제 중심

반드시 아래 JSON 구조로만 출력하세요(키 이름/타입 엄수):
{{
  "summary_markdown": "...여기에 Markdown...",
  "problems": {{
    "basic": [
      {{"question":"...","choices":["...","...","...","..."],"answer_index":0,"explanation":"..."}},
      ... (총 15문항)
    ],
    "advanced": [
      {{"question":"...","choices":["...","...","...","..."],"answer_index":0,"explanation":"..."}},
      ... (총 15문항)
    ]
  }}
}}

PDF 본문:
====
{pdf_text[:120000]}
====
""".strip()


def call_openai_generate(pdf_text: str) -> Dict[str, Any]:
    if not client:
        raise RuntimeError("OPENAI_API_KEY not set")

    prompt = build_prompt_for_generation(pdf_text)

    # Use Responses API; request JSON output (loose schema via instruction)
    resp = client.responses.create(
        model=MODEL_DEFAULT,
        input=[
            {"role": "system", "content": "You are a concise, accurate teaching assistant and exam writer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_output_tokens=7000,
    )

    text = resp.output_text  # unified text

    # Try to extract JSON
    # If the model wraps code fences, strip them
    match = re.search(r"\{[\s\S]*\}\s*$", text)
    raw = match.group(0) if match else text

    try:
        data = json.loads(raw)
    except Exception as e:
        # crude fence removal fallback
        raw2 = re.sub(r"^[`\s]*json[`\s]*|^```|```$", "", raw, flags=re.MULTILINE)
        data = json.loads(raw2)

    # Validate minimal shape
    if not isinstance(data, dict) or "summary_markdown" not in data or "problems" not in data:
        raise ValueError("Model output missing required keys")

    return data


# ---------------------------
# Flask App
# ---------------------------
app = Flask(__name__)


@app.get("/")
def index():
    return render_template_string(INDEX_HTML)


@app.post("/api/process")
def api_process():
    if "pdf" not in request.files:
        return jsonify({"ok": False, "error": "PDF 파일을 업로드하세요."}), 400

    f = request.files["pdf"]
    if not f.filename.lower().endswith(".pdf"):
        return jsonify({"ok": False, "error": "확장자가 .pdf 인 파일만 허용됩니다."}), 400

    try:
        pdf_text = extract_text_from_pdf(f.stream)
        if not pdf_text.strip():
            return jsonify({"ok": False, "error": "PDF에서 텍스트를 추출하지 못했습니다."}), 400

        data = call_openai_generate(pdf_text)

        tag = now_tag()
        # Save problems JSON
        problems_path = PROBLEMS_DIR / f"problems_{tag}.json"
        save_json(data.get("problems", {}), problems_path)

        # Save summary MD
        title = f"summary_{tag}.md"
        summary_path = SUMMARIES_DIR / title
        summary_path.write_text(data.get("summary_markdown", ""), encoding="utf-8")

        # Lightweight response for immediate preview
        return jsonify({
            "ok": True,
            "problems_url": url_for("serve_problem_file", filename=problems_path.name),
            "summary_url": url_for("serve_summary_file", filename=summary_path.name),
            "problems": data.get("problems", {}),
            "summary_html": markdown(data.get("summary_markdown", ""), extensions=["fenced_code", "tables"]) ,
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.get("/api/list/problems")
def list_problems():
    files = sorted(PROBLEMS_DIR.glob("problems_*.json"), reverse=True)
    return jsonify([{ "name": p.name, "url": url_for("serve_problem_file", filename=p.name) } for p in files])


@app.get("/api/list/summaries")
def list_summaries():
    files = sorted(SUMMARIES_DIR.glob("summary_*.md"), reverse=True)
    return jsonify([{ "name": p.name, "url": url_for("serve_summary_file", filename=p.name) } for p in files])


@app.get("/problems")
def problems_page():
    return render_template_string(PROBLEMS_HTML)


@app.get("/summaries")
def summaries_page():
    return render_template_string(SUMMARIES_HTML)


@app.get("/data/problems/<path:filename>")
def serve_problem_file(filename):
    return send_from_directory(PROBLEMS_DIR, filename, as_attachment=False)


@app.get("/data/summaries/<path:filename>")
def serve_summary_file(filename):
    return send_from_directory(SUMMARIES_DIR, filename, as_attachment=False)


# ---------------------------
# HTML Templates (inline)
# ---------------------------
INDEX_HTML = r"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PDF → 연습문제·심화문제 + 요약 | Local</title>
  <script>
    // Tailwind via CDN
    // Note: for production, consider self-hosting
  </script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .choice:hover { filter: brightness(0.98); }
    .correct { outline: 2px solid #22c55e; }
    .wrong { outline: 2px solid #ef4444; }
    .scroll-smooth { scroll-behavior: smooth; }
    .prose pre { white-space: pre-wrap; word-break: break-word; }
  </style>
</head>
<body class="bg-gray-50 text-gray-900">
  <div class="max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
    <header class="mb-6 flex items-center justify-between">
      <h1 class="text-2xl md:text-3xl font-bold">PDF summary and problem making service</h1>
      <nav class="text-sm flex gap-4">
        <a href="/problems" class="text-blue-600 hover:underline">저장된 문제</a>
        <a href="/summaries" class="text-blue-600 hover:underline">저장된 요약</a>
        <a href="https://platform.openai.com/" target="_blank" class="text-gray-500 hover:underline">OpenAI</a>
      </nav>
    </header>

    <!-- Upload Panel -->
    <section class="bg-white rounded-2xl shadow p-4 md:p-6 mb-6">
      <form id="uploadForm" class="flex flex-col md:flex-row items-start md:items-center gap-4">
        <input type="file" id="pdf" name="pdf" accept="application/pdf" class="block" required />
        <button type="submit" class="px-4 py-2 rounded-xl bg-black text-white hover:bg-gray-800">PDF 업로드 & 생성</button>
        <span id="status" class="text-sm text-gray-500"></span>
      </form>
      <p class="text-xs text-gray-500 mt-2">⚠️ 최초 실행 시 OPENAI_API_KEY 환경변수를 설정해야 합니다.</p>
    </section>

    <!-- Split View -->
    <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Left: Quiz -->
      <div class="bg-white rounded-2xl shadow p-4 md:p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold">문제 풀기</h2>
          <div class="inline-flex rounded-xl bg-gray-100 p-1">
            <button id="tabBasic" class="px-3 py-1.5 text-sm rounded-lg bg-white shadow">기초</button>
            <button id="tabAdvanced" class="px-3 py-1.5 text-sm rounded-lg">심화</button>
          </div>
        </div>
        <div id="quizContainer" class="space-y-4"></div>
      </div>

      <!-- Right: Summary -->
      <div class="bg-white rounded-2xl shadow p-4 md:p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold">요약 정리</h2>
          <button id="openSummaryRaw" class="text-sm text-blue-600 hover:underline hidden">원문(MD) 열기</button>
        </div>
        <article id="summary" class="prose prose-sm md:prose lg:prose-lg max-w-none"></article>
      </div>
    </section>
  </div>

<script>
let CURRENT = { problems: {basic: [], advanced: []}, activeTab: 'basic', summary_url: null };

function renderChoices(qIdx, choices, answerIndex) {
  const groupName = `q_${qIdx}_${CURRENT.activeTab}`;
  return choices.map((c, i) => `
    <label class="block choice cursor-pointer">
      <input type="radio" name="${groupName}" value="${i}" class="hidden" onchange="onPick(${qIdx}, ${i}, ${answerIndex})" />
      <div id="${groupName}_${i}" class="rounded-xl border p-3 text-sm">${c}</div>
    </label>
  `).join('');
}

function renderQuiz() {
  const container = document.getElementById('quizContainer');
  const list = CURRENT.problems[CURRENT.activeTab] || [];
  if (!list.length) {
    container.innerHTML = `<p class="text-gray-500 text-sm">아직 생성된 문제가 없습니다. PDF를 업로드하세요.</p>`;
    return;
  }

  container.innerHTML = list.map((q, idx) => `
    <div class="border rounded-2xl p-4">
      <div class="flex items-start gap-3">
        <div class="shrink-0 w-6 h-6 rounded-full bg-gray-900 text-white grid place-items-center text-xs">${idx+1}</div>
        <div class="grow">
          <p class="font-medium mb-2">${q.question}</p>
          <div class="space-y-2">${renderChoices(idx, q.choices, q.answer_index)}</div>
          <p id="ex_${idx}" class="mt-3 text-sm hidden"></p>
        </div>
      </div>
    </div>
  `).join('');
}

window.onPick = (qIdx, picked, answerIdx) => {
  const name = `q_${qIdx}_${CURRENT.activeTab}`;
  for (let i=0;i<4;i++) {
    const el = document.getElementById(`${name}_${i}`);
    if (!el) continue;
    el.classList.remove('correct','wrong');
  }
  const target = document.getElementById(`${name}_${picked}`);
  const exp = document.getElementById(`ex_${qIdx}`);
  const correct = (picked === answerIdx);
  target.classList.add(correct ? 'correct' : 'wrong');
  exp.classList.remove('hidden');
  const item = CURRENT.problems[CURRENT.activeTab][qIdx];
  exp.textContent = (correct ? '✅ 정답입니다. ' : '❌ 오답입니다. ') + (item.explanation || '');
};

function setActiveTab(tab) {
  CURRENT.activeTab = tab;
  document.getElementById('tabBasic').className = 'px-3 py-1.5 text-sm rounded-lg ' + (tab==='basic' ? 'bg-white shadow' : '');
  document.getElementById('tabAdvanced').className = 'px-3 py-1.5 text-sm rounded-lg ' + (tab==='advanced' ? 'bg-white shadow' : '');
  renderQuiz();
}

document.getElementById('tabBasic').addEventListener('click', () => setActiveTab('basic'));
document.getElementById('tabAdvanced').addEventListener('click', () => setActiveTab('advanced'));

// Upload handler
const form = document.getElementById('uploadForm');
const statusEl = document.getElementById('status');
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  statusEl.textContent = '생성 중... (PDF 크기에 따라 수십 초 소요 가능)';
  const fd = new FormData(form);
  try {
    const res = await fetch('/api/process', { method: 'POST', body: fd });
    const j = await res.json();
    if (!j.ok) throw new Error(j.error || '생성 실패');

    CURRENT.problems = j.problems || {basic: [], advanced: []};
    document.getElementById('summary').innerHTML = j.summary_html || '';
    if (j.summary_url) {
      CURRENT.summary_url = j.summary_url;
      const btn = document.getElementById('openSummaryRaw');
      btn.classList.remove('hidden');
      btn.onclick = () => window.open(j.summary_url, '_blank');
    }

    setActiveTab('basic');
    statusEl.textContent = '완료! 좌/우에서 바로 확인하세요.';
  } catch (err) {
    console.error(err);
    statusEl.textContent = '오류: ' + err.message;
  }
});

</script>
</body>
</html>
"""

PROBLEMS_HTML = r"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>저장된 문제</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 text-gray-900">
  <div class="max-w-4xl mx-auto p-6">
    <h1 class="text-2xl font-bold mb-4">저장된 문제</h1>
    <div id="list" class="space-y-2"></div>
    <p class="mt-6"><a class="text-blue-600 hover:underline" href="/">← 돌아가기</a></p>
  </div>
<script>
(async () => {
  const res = await fetch('/api/list/problems');
  const items = await res.json();
  const list = document.getElementById('list');
  if (!items.length) {
    list.innerHTML = '<p class="text-gray-500">아직 생성된 문제가 없습니다.</p>';
    return;
  }
  list.innerHTML = items.map(it => `
    <a class="block bg-white rounded-xl border p-3 hover:bg-gray-50" href="${it.url}" target="_blank">${it.name}</a>
  `).join('');
})();
</script>
</body>
</html>
"""

SUMMARIES_HTML = r"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>저장된 요약</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 text-gray-900">
  <div class="max-w-4xl mx-auto p-6">
    <h1 class="text-2xl font-bold mb-4">저장된 요약</h1>
    <div id="list" class="space-y-2"></div>
    <p class="mt-6"><a class="text-blue-600 hover:underline" href="/">← 돌아가기</a></p>
  </div>
<script>
(async () => {
  const res = await fetch('/api/list/summaries');
  const items = await res.json();
  const list = document.getElementById('list');
  if (!items.length) {
    list.innerHTML = '<p class="text-gray-500">아직 생성된 요약이 없습니다.</p>';
    return;
  }
  list.innerHTML = items.map(it => `
    <a class="block bg-white rounded-xl border p-3 hover:bg-gray-50" href="${it.url}" target="_blank">${it.name}</a>
  `).join('');
})();
</script>
</body>
</html>
"""


# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    # Provide a tiny requirements.txt helper if missing
    req = ROOT / "requirements.txt"
    if not req.exists():
        req.write_text("""
Flask>=3.0.0
pypdf>=4.2.0
markdown>=3.6
openai>=1.40.0
python-dotenv>=1.0.1
""".strip()+"\n", encoding="utf-8")
        print("[INFO] requirements.txt 를 생성했습니다.")

    app.run(host="127.0.0.1", port=5000, debug=True)
