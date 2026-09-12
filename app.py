# -*- coding: utf-8 -*-
"""
🚢 동화엔텍 MUSV 통합 업무 관리 대시보드
=====================================================
- 캘린더(월/주/리스트) + 태그/분류/이메일 연동
- 주간보고 자동 생성 + 편집 + 저장
- 관리자 페이지에서 모든 설정
- 사용자 편의 UX 다수 적용

Author: Genspark AI (for 대마왕)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import calendar as pycal
import os
import json
import imaplib
import email as email_lib
from email.header import decode_header
import re
import io
import uuid
import urllib.request
import urllib.error

# =====================================================
# 0. 페이지 설정 & 전역 CSS
# =====================================================
st.set_page_config(
    page_title="MUSV 통합 업무 대시보드",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
/* ---------- 전역 폰트/여백 ---------- */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Malgun Gothic",
                 "Apple SD Gothic Neo", "Noto Sans KR", Roboto, sans-serif;
}
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; }

/* ---------- 헤더 카드 ---------- */
.hero {
    background: linear-gradient(120deg, #0f2b5b 0%, #1e40af 50%, #0891b2 100%);
    color: #fff;
    padding: 18px 24px;
    border-radius: 14px;
    margin-bottom: 16px;
    box-shadow: 0 6px 20px rgba(15, 43, 91, 0.18);
}
.hero h1 { color:#fff; margin:0; font-size: 1.55rem; }
.hero p  { color:#dbeafe; margin:6px 0 0 0; font-size: 0.9rem; }

/* ---------- KPI 카드 ---------- */
.kpi {
    border-radius: 12px;
    padding: 14px 16px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.kpi .label { color:#6b7280; font-size:12px; margin-bottom:4px; }
.kpi .value { font-size:26px; font-weight:700; color:#111827; }
.kpi .sub   { color:#9ca3af; font-size:11px; margin-top:2px; }
.kpi.warn  { border-left: 4px solid #ef4444; }
.kpi.good  { border-left: 4px solid #10b981; }
.kpi.info  { border-left: 4px solid #3b82f6; }
.kpi.hold  { border-left: 4px solid #f59e0b; }

/* ---------- 캘린더 ---------- */
.cal-wrap { border-radius: 12px; overflow: hidden; border:1px solid #e5e7eb; }
table.cal { width:100%; border-collapse: collapse; font-size:12.5px; }
table.cal th {
    background: #f8fafc; color:#374151; font-weight:600;
    padding: 10px 6px; border-bottom:1px solid #e5e7eb;
    text-align:center;
}
table.cal th.sun { color:#ef4444; }
table.cal th.sat { color:#2563eb; }
table.cal td {
    border-top: 1px solid #f1f5f9;
    border-right: 1px solid #f1f5f9;
    vertical-align: top;
    height: 118px;
    padding: 5px;
    background:#fff;
    position: relative;
}
table.cal td.today { background: #fffbeb; }
table.cal td.other { background: #fafafa; }
table.cal td .day {
    font-weight: 600; font-size: 12px; margin-bottom: 4px;
    display:flex; justify-content: space-between; align-items:center;
}
table.cal td.today .day .num {
    background:#f59e0b; color:#fff; border-radius:999px;
    width:22px; height:22px; display:inline-flex; align-items:center; justify-content:center;
    font-size:11px;
}
table.cal td .day .weeknum { color:#9ca3af; font-size:10px; font-weight:400; }
table.cal td .day .sun { color:#ef4444; }
table.cal td .day .sat { color:#2563eb; }
.chip {
    display:block; border-radius: 4px; padding: 2px 6px;
    margin-bottom: 2px; font-size: 11px; line-height: 1.3;
    white-space: nowrap; overflow:hidden; text-overflow: ellipsis;
    text-decoration:none !important; cursor:pointer;
    border-left: 3px solid transparent;
}
.chip.done { opacity: 0.55; text-decoration: line-through !important; }
.chip:hover { filter: brightness(0.96); }

/* ---------- 태그 배지 ---------- */
.tag-badge {
    display:inline-block; padding: 2px 8px; margin: 2px 3px 2px 0;
    border-radius: 999px; font-size: 11px;
    background:#eef2ff; color:#3730a3; border:1px solid #e0e7ff;
}
.status-dot {
    display:inline-block; width:8px; height:8px; border-radius:50%;
    margin-right:6px; vertical-align:middle;
}
.status-진행중 { background:#3b82f6; }
.status-완료   { background:#10b981; }
.status-지연   { background:#ef4444; }
.status-미정   { background:#6b7280; }
.status-보류   { background:#f59e0b; }

/* ---------- 알림 배너 ---------- */
.alert {
    background: #fef2f2; border: 1px solid #fecaca; color:#991b1b;
    padding: 10px 14px; border-radius: 10px; margin: 6px 0 12px 0;
    font-size: 13px;
}

/* ---------- 사이드바 ---------- */
section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

/* ---------- 스크롤바 얇게 ---------- */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =====================================================
# 1. 상수 및 기본 설정
# =====================================================
DATA_FILE = "all_tasks_v2.csv"
SETTINGS_FILE = "settings.json"

STATUS_LIST = ["진행중", "미정", "보류", "완료", "지연"]
PRIORITY_LIST = ["🟢 낮음", "🔵 보통", "🟠 높음", "🔴 긴급"]

# 업무유형별 색상 (배경/글자) — 진행중 vs 완료
TYPE_COLORS = {
    "회의 진행":            {"bg": "#3b82f6", "fg": "#ffffff", "bg_done": "#dbeafe", "fg_done": "#1e40af"},
    "메일/자료 송수신":     {"bg": "#10b981", "fg": "#ffffff", "bg_done": "#d1fae5", "fg_done": "#065f46"},
    "일반 업무 (설계/검토 등)":{"bg": "#8b5cf6", "fg": "#ffffff", "bg_done": "#ede9fe", "fg_done": "#5b21b6"},
    "주간보고":             {"bg": "#0f2b5b", "fg": "#ffffff", "bg_done": "#c7d2fe", "fg_done": "#312e81"},
}
FALLBACK_PALETTE = [
    {"bg": "#f59e0b", "fg": "#ffffff", "bg_done": "#fef3c7", "fg_done": "#92400e"},
    {"bg": "#ec4899", "fg": "#ffffff", "bg_done": "#fce7f3", "fg_done": "#9d174d"},
    {"bg": "#06b6d4", "fg": "#ffffff", "bg_done": "#cffafe", "fg_done": "#155e75"},
    {"bg": "#f43f5e", "fg": "#ffffff", "bg_done": "#ffe4e6", "fg_done": "#9f1239"},
]
DELAY_COLOR = {"bg": "#ef4444", "fg": "#ffffff"}
HOLD_COLOR  = {"bg": "#f59e0b", "fg": "#111827"}

DEFAULT_SETTINGS = {
    "MUSV-2": {
        "activity_types": ["회의 진행", "메일/자료 송수신", "일반 업무 (설계/검토 등)", "주간보고"],
        "categories": {
            "1. 개요": ["1-1. 일정", "1-2. 회의"],
            "2. BCC": ["2-1. BCC", "2-2. 사급자재", "2-3. ECS PC", "2-4. 모니터"],
            "3. DAU": ["3-1. DAU PANEL", "3-2. DAU & HISTORIAN", "3-3. UPS", "3-4. ECS PLC 프로그램"],
            "4. KR":  ["4-1. 제출자료"],
            "5. 프로그램": ["5-1. 컨셉 다이어그램", "5-2. ECS PLC", "5-3. ECS PC",
                        "5-4. ECS HMI", "5-5. 임무콘솔", "5-6. DAU & HISTORIAN", "5-7. ETC."]
        },
        "tags": ["DAU", "BCC", "사급자재", "UPS", "ECS PC", "ECS PLC", "ECS 모니터", "DAU PANEL",
                 "히스토리안서버", "극동선박설계", "유일조선소", "한화시스템", "한화엔진",
                 "한화오션", "KR선급", "MS산전", "주간보고"],
        "weekly_reports": {}
    },
    "gmail_settings": {
        "email": "lhb8606@gmail.com",
        "app_password": "",
        "target_sender": "hblee@dh.co.kr, 이헌범"
    },
    "ui": {"theme": "라이트", "week_start": "월요일"}
}

TASK_COLS = ["ID", "프로젝트", "업무유형", "대분류", "중분류", "우선순위",
             "시작일", "목표일", "실제완료일", "장소", "관련자(참석자/송수신자)",
             "제목", "내용", "태그", "상태", "드라이브_링크", "연관업무ID", "생성일시", "수정일시"]

# AI 기본 설정
DEFAULT_SETTINGS["ai"] = {
    "enabled": False,
    "provider": "openai",   # openai / gemini / anthropic
    "api_key": "",
    "model": "gpt-4o-mini", # gpt-4o-mini / gemini-3.5-flash / claude-3-5-haiku-20241022
    "auto_classify_on_email": True,
    "auto_suggest_tags": True,
}


# =====================================================
# 1-A. AI 헬퍼 (OpenAI / Gemini / Anthropic 3사 지원)
# =====================================================
def ai_available(settings):
    ai = settings.get("ai", {})
    return bool(ai.get("enabled") and ai.get("api_key") and ai.get("provider"))


def _ai_call_openai(api_key, model, system, user, temperature=0.3, max_tokens=1500):
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        obj = json.loads(r.read().decode("utf-8"))
    return obj["choices"][0]["message"]["content"]


def _ai_call_gemini(api_key, model, system, user, temperature=0.3, max_tokens=1500):
    # 사용자가 models/ 접두어를 입력했다면 제거
    model = (model or "").strip()
    if model.startswith("models/"):
        model = model[len("models/"):]
    if not model:
        model = "gemini-3.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    # AQ. 프리픽스 신형 키와 AIza 구형 키 모두 x-goog-api-key 헤더 방식으로 통일
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            obj = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            err_body = ""
        raise RuntimeError(f"Gemini API HTTP {e.code}: {err_body[:500]}")
    # 응답 파싱
    try:
        return obj["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        # 안전성 차단 등 특수 케이스
        if "promptFeedback" in obj:
            return f"[Gemini blocked] {json.dumps(obj['promptFeedback'], ensure_ascii=False)}"
        return json.dumps(obj, ensure_ascii=False)[:800]


def _ai_call_anthropic(api_key, model, system, user, temperature=0.3, max_tokens=1500):
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        obj = json.loads(r.read().decode("utf-8"))
    try:
        return obj["content"][0]["text"]
    except Exception:
        return json.dumps(obj)


def ai_call(settings, system, user, temperature=0.3, max_tokens=1500):
    """provider별 라우팅. 실패 시 예외 raise."""
    ai = settings.get("ai", {})
    provider = ai.get("provider", "openai")
    api_key  = ai.get("api_key", "")
    model    = ai.get("model", "")
    if not api_key:
        raise RuntimeError("AI API 키가 설정되지 않았습니다.")
    if provider == "openai":
        return _ai_call_openai(api_key, model or "gpt-4o-mini", system, user, temperature, max_tokens)
    if provider == "gemini":
        return _ai_call_gemini(api_key, model or "gemini-3.5-flash", system, user, temperature, max_tokens)
    if provider == "anthropic":
        return _ai_call_anthropic(api_key, model or "claude-3-5-haiku-20241022", system, user, temperature, max_tokens)
    raise RuntimeError(f"알 수 없는 AI provider: {provider}")


def ai_json(settings, system, user, temperature=0.2, max_tokens=1500):
    """AI 응답에서 JSON 블록만 추출."""
    raw = ai_call(settings, system, user, temperature, max_tokens)
    # ```json ... ``` 또는 순수 JSON 대응
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", raw, re.DOTALL)
    if m:
        raw = m.group(1)
    else:
        m2 = re.search(r"(\{.*\}|\[.*\])", raw, re.DOTALL)
        if m2: raw = m2.group(1)
    try:
        return json.loads(raw)
    except Exception:
        return {"_raw": raw, "_error": "JSON 파싱 실패"}


def ai_classify_task(settings, title, body, activity_types, categories, tags):
    """제목/본문 → 업무유형/대분류/중분류/태그/우선순위/추천제목 자동 분류."""
    cats_desc = json.dumps(categories, ensure_ascii=False)
    tags_desc = json.dumps(tags, ensure_ascii=False)
    acts_desc = json.dumps(activity_types, ensure_ascii=False)
    system = (
        "당신은 조선/해양 방산 프로젝트(MUSV, 무인수상정)의 업무 분류 도우미입니다. "
        "동화엔텍 전기제어설계팀의 협력사(한화시스템, 한화엔진, 한화오션, 유일조선소, 극동선박설계, KR선급, MS산전 등) "
        "관련 업무를 정확히 분류하세요. 반드시 유효한 JSON만 응답하세요."
    )
    user = f"""다음 업무를 분류해주세요.

[제목]
{title}

[내용]
{body[:3000]}

[허용된 업무유형 목록]
{acts_desc}

[허용된 대분류 → 중분류 매핑]
{cats_desc}

[허용된 태그 목록]
{tags_desc}

다음 형식의 JSON으로만 응답 (설명 금지):
{{
  "업무유형": "위 목록 중 하나",
  "대분류": "위 매핑의 대분류 중 하나",
  "중분류": "선택한 대분류 하위의 중분류 중 하나",
  "태그": ["관련 태그 1~5개, 위 목록에서만"],
  "우선순위": "🟢 낮음 | 🔵 보통 | 🟠 높음 | 🔴 긴급 중 하나",
  "제안제목": "핵심을 담은 50자 이내 요약 제목",
  "요약": "업무 내용을 3~5줄로 정리"
}}"""
    return ai_json(settings, system, user)


def ai_write_weekly_report(settings, project_name, week_label, tasks_summary):
    """AI가 주간보고서 초안 자동 작성."""
    system = (
        "당신은 조선/해양 방산 PM의 주간보고 어시스턴트입니다. "
        "건조하고 명확한 한국어로, 관리자가 5분 안에 읽을 수 있는 주간보고를 작성합니다. "
        "숫자와 사실 위주로, 불필요한 수식어와 감사 인사는 넣지 마세요."
    )
    user = f"""{project_name} 프로젝트의 {week_label} 주간보고를 작성해주세요.

[이번 주 업무 데이터]
{tasks_summary}

다음 구조로 마크다운 형식 응답:

## 📌 이번 주 핵심 성과
(3~5개 bullet)

## ✅ 완료 업무
(항목별로 [업무유형] 제목 — 결과/산출물 한 줄)

## 🏃 진행 및 예정 업무
(항목별로 [업무유형] 제목 — 다음 액션 아이템)

## ⚠️ 지연/이슈
(있으면 원인과 대응방안까지)

## 📅 다음 주 계획
(3~5개 bullet, 우선순위 높은 순)

## 🤝 협력사 관련 특이사항
(한화시스템/한화엔진/한화오션/유일조선소/KR선급 등 관련 이슈)"""
    return ai_call(settings, system, user, temperature=0.4, max_tokens=2500)


def ai_summarize_email(settings, subject, sender, body):
    """이메일 → 3줄 요약 + 액션아이템."""
    system = "이메일을 간결하게 요약하는 한국어 업무 도우미입니다. 반드시 JSON으로만 응답하세요."
    user = f"""[제목] {subject}
[보낸이] {sender}
[본문]
{body[:3000]}

응답 JSON:
{{
  "요약": "핵심 3줄 이내",
  "액션아이템": ["해야할 일 목록, 없으면 빈 배열"],
  "마감일자": "YYYY-MM-DD 또는 빈 문자열",
  "긴급도": "🟢 낮음 | 🔵 보통 | 🟠 높음 | 🔴 긴급"
}}"""
    return ai_json(settings, system, user)


def ai_polish_task_note(settings, raw_text):
    """지저분한 메모를 업무일지 스타일로 정리."""
    system = "지저분한 회의 메모/업무 메모를 깔끔한 업무일지 형태로 다듬는 한국어 어시스턴트입니다."
    user = f"""아래 원문 메모를 업무일지에 그대로 붙여넣을 수 있게 정리해주세요.
- 불필요한 감탄사·중복 제거
- 결정사항 / 액션아이템 / 참고사항으로 구조화
- 원본 사실 왜곡 금지

[원문]
{raw_text}
"""
    return ai_call(settings, system, user, temperature=0.3, max_tokens=1500)


# =====================================================
# 2. 데이터 IO 계층
# =====================================================
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = json.loads(json.dumps(DEFAULT_SETTINGS))
    else:
        data = json.loads(json.dumps(DEFAULT_SETTINGS))
        save_settings(data)

    # 보정
    if "gmail_settings" not in data:
        data["gmail_settings"] = DEFAULT_SETTINGS["gmail_settings"].copy()
    for k in ("email", "app_password", "target_sender"):
        data["gmail_settings"].setdefault(k, DEFAULT_SETTINGS["gmail_settings"][k])
    data.setdefault("ui", {"theme": "라이트", "week_start": "월요일"})
    data.setdefault("ai", json.loads(json.dumps(DEFAULT_SETTINGS["ai"])))
    for k, v in DEFAULT_SETTINGS["ai"].items():
        data["ai"].setdefault(k, v)

    for proj, cfg in list(data.items()):
        if proj in ("gmail_settings", "ui", "ai"): continue
        cfg.setdefault("activity_types", ["회의 진행", "메일/자료 송수신", "일반 업무 (설계/검토 등)", "주간보고"])
        if "주간보고" not in cfg["activity_types"]:
            cfg["activity_types"].append("주간보고")
        cfg.setdefault("categories", {})
        cfg.setdefault("tags", [])
        cfg.setdefault("weekly_reports", {})
    return data


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
        except Exception:
            df = pd.DataFrame(columns=TASK_COLS)
        # 구버전 컬럼명 호환
        rename_map = {"내용(주제)": "제목", "회의록_및_비고": "내용"}
        df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
        for c in TASK_COLS:
            if c not in df.columns:
                df[c] = ""
        # ID 자동 부여
        if df["ID"].isna().any() or (df["ID"] == "").any():
            df.loc[df["ID"].isna() | (df["ID"] == ""), "ID"] = [
                str(uuid.uuid4())[:8] for _ in range((df["ID"].isna() | (df["ID"] == "")).sum())
            ]
        # 우선순위 기본값
        df["우선순위"] = df["우선순위"].fillna("🔵 보통").replace("", "🔵 보통")
    else:
        df = pd.DataFrame(columns=TASK_COLS)

    # 👇👇👇 [추가된 부분] 에러 방지를 위해 텍스트 컬럼을 명시적으로 문자열(str)로 변환 👇👇👇
    text_cols = [
        "ID", "프로젝트", "업무유형", "대분류", "중분류", "우선순위",
        "장소", "관련자(참석자/송수신자)", "제목", "내용", "태그", "상태",
        "드라이브_링크", "연관업무ID"
    ]
    for c in text_cols:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str)
    # 👆👆👆 ------------------------------------------------------------- 👆👆👆

    # 날짜 파싱
    for c in ("시작일", "목표일", "실제완료일", "생성일시", "수정일시"):
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df[TASK_COLS]


def save_data(df):
    df.to_csv(DATA_FILE, index=False)


def new_id():
    return str(uuid.uuid4())[:8]


# =====================================================
# 3. 이메일 연동
# =====================================================
def _decode(s):
    if not s: return ""
    parts = decode_header(s)
    out = ""
    for w, enc in parts:
        if isinstance(w, bytes):
            try:
                out += w.decode(enc or "utf-8", errors="ignore")
            except Exception:
                out += w.decode("utf-8", errors="ignore")
        else:
            out += str(w)
    return out


def _get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp  = str(part.get("Content-Disposition", ""))
            if ctype == "text/plain" and "attachment" not in disp:
                try:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="ignore"
                    )
                except Exception:
                    pass
    else:
        try:
            return msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="ignore"
            )
        except Exception:
            pass
    return ""


def _company_from_email(addr):
    m = re.search(r"@([a-zA-Z0-9-]+)\.", str(addr))
    return m.group(1) if m else str(addr)


def fetch_musv_emails(email_user, app_password, target_sender, limit=15, scan=200):
    """Gmail IMAP에서 최근 scan건 중 지정 발신자 필터에 걸리는 최대 limit건 반환."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, app_password)

        # All Mail 라벨 찾기 (없으면 INBOX)
        status, folders = mail.list()
        all_mail = "INBOX"
        if status == "OK" and folders:
            for f in folders:
                if b"\\All" in f:
                    parts = f.decode("utf-8", errors="ignore").split(' "/" ')
                    if len(parts) == 2:
                        all_mail = parts[1]
                        break
        try:
            mail.select(all_mail, readonly=True)
        except Exception:
            mail.select("INBOX", readonly=True)

        status, messages = mail.search(None, "ALL")
        results = []
        if status == "OK" and messages[0]:
            ids = messages[0].split()
            targets = [t.strip().lower() for t in target_sender.replace("OR", ",").split(",") if t.strip()]

            for msg_id in reversed(ids[-scan:]):
                res, data = mail.fetch(msg_id, "(RFC822)")
                if res != "OK": continue
                msg = email_lib.message_from_bytes(data[0][1])
                sender = _decode(msg.get("From", ""))
                lower = sender.lower()
                if not any(t in lower for t in targets):
                    continue
                subject = _decode(msg.get("Subject", ""))
                date_h  = msg.get("Date", "")
                body    = _get_body(msg)
                short   = (body[:200] + "…") if len(body) > 200 else body
                results.append({
                    "id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                    "날짜": date_h,
                    "회사명": _company_from_email(sender),
                    "보낸이": sender,
                    "제목": subject,
                    "본문": body.strip(),
                    "본문요약": short.strip(),
                })
                if len(results) >= limit:
                    break
        mail.logout()
        return results
    except Exception as e:
        st.error(f"메일 연동 실패: {e}")
        return []


# =====================================================
# 4. 헬퍼: 날짜/필터/색상
# =====================================================
def week_range(any_date, start_monday=True):
    """해당 날짜가 포함된 주의 (시작, 끝)."""
    d = pd.Timestamp(any_date).normalize()
    if start_monday:
        start = d - pd.Timedelta(days=d.weekday())
        end   = start + pd.Timedelta(days=6)
    else:
        # 일요일 시작
        idx = (d.weekday() + 1) % 7
        start = d - pd.Timedelta(days=idx)
        end   = start + pd.Timedelta(days=6)
    return start, end


def get_type_color(ttype, activity_types, status):
    if status == "지연":
        return DELAY_COLOR["bg"], DELAY_COLOR["fg"], False
    if status == "보류":
        return HOLD_COLOR["bg"], HOLD_COLOR["fg"], False
    done = (status == "완료")
    if ttype in TYPE_COLORS:
        c = TYPE_COLORS[ttype]
    else:
        try:
            idx = activity_types.index(ttype) % len(FALLBACK_PALETTE)
        except Exception:
            idx = 0
        c = FALLBACK_PALETTE[idx]
    if done:
        return c["bg_done"], c["fg_done"], True
    return c["bg"], c["fg"], False


def task_active_on(task, day_ts, today_ts):
    """해당 날짜 셀에 이 업무를 표시해야 하는지."""
    start = task["시작일"]
    if pd.isna(start): return False
    end    = task["목표일"]
    status = task["상태"]
    if pd.notna(end):
        return start <= day_ts <= end
    # 목표일 없는 경우: 진행중/미정/보류이면 오늘까지 지속, 그 외는 시작일에만
    if status in ("진행중", "미정", "보류"):
        return start <= day_ts <= today_ts
    return start == day_ts


def compute_overdue(df):
    """목표일 지났는데 완료 아닌 업무 → 지연 표시용 마스크."""
    today = pd.Timestamp(date.today())
    mask = (
        df["목표일"].notna() & (df["목표일"] < today)
        & (~df["상태"].isin(["완료"]))
    )
    return mask


# =====================================================
# 5. 캘린더 렌더링
# =====================================================
def render_month_calendar(df, base_date, activity_types, week_start_monday=True):
    """월간 캘린더 (기준일 포함 6주: 이전 2주 / 이번 주 / 이후 3주)."""
    base = pd.Timestamp(base_date).normalize()
    if week_start_monday:
        first_of_week = base - pd.Timedelta(days=base.weekday())
        headers = ["월", "화", "수", "목", "금", "토", "일"]
        weekend_idx = {5: "sat", 6: "sun"}
    else:
        idx = (base.weekday() + 1) % 7
        first_of_week = base - pd.Timedelta(days=idx)
        headers = ["일", "월", "화", "수", "목", "금", "토"]
        weekend_idx = {0: "sun", 6: "sat"}
    start = first_of_week - pd.Timedelta(weeks=2)
    today_ts = pd.Timestamp(date.today())

    html = ['<div class="cal-wrap"><table class="cal">']
    html.append("<colgroup>")
    html.append("<col style='width:5%;'/>")
    for _ in range(7):
        html.append("<col style='width:13.57%;'/>")
    html.append("</colgroup>")
    html.append("<tr><th>주</th>")
    for i, h in enumerate(headers):
        cls = weekend_idx.get(i, "")
        html.append(f"<th class='{cls}'>{h}</th>")
    html.append("</tr>")

    curr = start
    for _ in range(6):
        thu = curr + pd.Timedelta(days=3)
        wk = thu.isocalendar()[1]
        html.append(f"<tr><td style='background:#f8fafc;text-align:center;color:#6b7280;font-size:11px;font-weight:600;'>{wk}W</td>")
        for i in range(7):
            is_today = (curr.date() == today_ts.date())
            in_month = (curr.month == base.month)
            classes = []
            if is_today: classes.append("today")
            elif not in_month: classes.append("other")
            cls = " ".join(classes)
            day_cls = weekend_idx.get(i, "")

            html.append(f"<td class='{cls}'>")
            num_html = f"<span class='num {day_cls}'>{curr.day}</span>"
            html.append(f"<div class='day'>{num_html}<span class='weeknum'></span></div>")

            if not df.empty:
                for _, task in df.iterrows():
                    if not task_active_on(task, curr, today_ts): continue
                    bg, fg, done = get_type_color(task["업무유형"], activity_types, task["상태"])
                    done_cls = " done" if done else ""
                    prio = str(task.get("우선순위", "")) or ""
                    prio_mark = ""
                    if "긴급" in prio: prio_mark = "🔴 "
                    elif "높음" in prio: prio_mark = "🟠 "
                    title = str(task["제목"]).replace("'", "&apos;").replace('"', "&quot;")
                    tid = task["ID"]
                    border_col = bg if not done else fg
                    html.append(
                        f"<a class='chip{done_cls}' href='?task_id={tid}' target='_self' "
                        f"style='background:{bg};color:{fg};border-left-color:{border_col};' "
                        f"title='[{task['업무유형']}] {title}'>"
                        f"{prio_mark}{title}</a>"
                    )
            html.append("</td>")
            curr = curr + pd.Timedelta(days=1)
        html.append("</tr>")
    html.append("</table></div>")
    return "".join(html)


def render_week_agenda(df, base_date, activity_types, week_start_monday=True):
    """주간 어젠다(리스트) 뷰."""
    ws, we = week_range(base_date, start_monday=week_start_monday)
    today_ts = pd.Timestamp(date.today())
    html = ["<div style='border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;'>"]
    for i in range(7):
        d = ws + pd.Timedelta(days=i)
        weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][d.weekday()]
        color = "#ef4444" if d.weekday() == 6 else ("#2563eb" if d.weekday() == 5 else "#374151")
        is_today = (d.date() == today_ts.date())
        bg = "#fffbeb" if is_today else "#ffffff"
        html.append(
            f"<div style='display:flex;background:{bg};border-top:1px solid #f1f5f9;padding:10px 14px;'>"
            f"<div style='width:110px;color:{color};font-weight:600;font-size:13px;'>"
            f"{d.month}/{d.day} ({weekday_kr}){' · 오늘' if is_today else ''}"
            f"</div><div style='flex:1;'>"
        )
        day_tasks = []
        for _, task in df.iterrows():
            if task_active_on(task, d, today_ts):
                day_tasks.append(task)
        if not day_tasks:
            html.append("<span style='color:#9ca3af;font-size:12px;'>일정 없음</span>")
        else:
            for task in day_tasks:
                bgc, fg, done = get_type_color(task["업무유형"], activity_types, task["상태"])
                done_style = "opacity:0.55;text-decoration:line-through;" if done else ""
                tid = task["ID"]
                title = str(task["제목"]).replace("'", "&apos;").replace('"', "&quot;")
                html.append(
                    f"<a href='?task_id={tid}' target='_self' "
                    f"style='display:inline-block;margin:2px 4px 2px 0;padding:3px 10px;"
                    f"border-radius:14px;background:{bgc};color:{fg};font-size:12px;{done_style}"
                    f"text-decoration:none;'>[{task['업무유형']}] {title}</a>"
                )
        html.append("</div></div>")
    html.append("</div>")
    return "".join(html)


# =====================================================
# 6. 세션 초기화 & 쿼리 파라미터
# =====================================================
if "cal_base_date" not in st.session_state:
    st.session_state.cal_base_date = date.today()
if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "월간"
if "cal_offset" not in st.session_state:
    st.session_state.cal_offset = 0
if "fetched_emails" not in st.session_state:
    st.session_state.fetched_emails = []
if "last_deleted" not in st.session_state:
    st.session_state.last_deleted = None
if "notice_dismiss" not in st.session_state:
    st.session_state.notice_dismiss = False

# ?task_id=xxx 로 캘린더에서 클릭 시 상세보기 오픈
qp = st.query_params.get("task_id")
if qp:
    st.session_state.selected_task_id = qp
    del st.query_params["task_id"]


# =====================================================
# 7. 데이터 로드
# =====================================================
settings = load_settings()
df = load_data()


# =====================================================
# 8. 상단 헤더 (Hero + 프로젝트/메뉴)
# =====================================================
st.markdown(
    '<div class="hero">'
    '<h1>🚢 MUSV 통합 업무 관리 대시보드</h1>'
    '<p>한 화면에서 캘린더 · 태그 · 이메일 · 주간보고까지 — 동화엔텍 전기제어설계팀</p>'
    '</div>',
    unsafe_allow_html=True
)

head_c1, head_c2, head_c3, head_c4 = st.columns([2.2, 2.2, 2.2, 3.4])
with head_c1:
    project_list = [p for p in settings.keys() if p not in ("gmail_settings", "ui", "ai")]
    if not project_list:
        settings["MUSV-2"] = json.loads(json.dumps(DEFAULT_SETTINGS["MUSV-2"]))
        save_settings(settings)
        project_list = ["MUSV-2"]
    selected_project = st.selectbox("📁 프로젝트", project_list, key="cur_project")
with head_c2:
    menu = st.selectbox("🧭 메뉴", [
        "📊 대시보드",
        "🗓️ 캘린더 (월/주/리스트)",
        "📩 이메일 연동함",
        "🗂️ 전체 항목 · 검색",
        "📈 통계",
        "⚙️ 관리자 설정",
    ], key="cur_menu")
with head_c3:
    global_search = st.text_input("🔍 통합 검색", placeholder="제목·내용·태그·관련자...", key="global_search")
with head_c4:
    st.write("")
    proj_df_all = df[df["프로젝트"] == selected_project].copy()
    overdue_mask = compute_overdue(proj_df_all)
    n_overdue = int(overdue_mask.sum())
    n_today = int(sum(
        task_active_on(t, pd.Timestamp(date.today()), pd.Timestamp(date.today()))
        for _, t in proj_df_all.iterrows()
    )) if not proj_df_all.empty else 0
    st.markdown(
        f"<div style='text-align:right;padding-top:6px;color:#4b5563;font-size:13px;'>"
        f"📅 오늘 진행 <b style='color:#111'>{n_today}건</b> · "
        f"⚠️ 지연 <b style='color:#ef4444'>{n_overdue}건</b>"
        f"</div>",
        unsafe_allow_html=True
    )

# 지연/오늘 알림 배너
if n_overdue > 0 and not st.session_state.notice_dismiss:
    st.markdown(
        f"<div class='alert'>⚠️ <b>지연된 업무가 {n_overdue}건</b> 있습니다. "
        f"[전체 항목 · 검색]에서 확인하거나, 대시보드 표에서 상태를 업데이트하세요.</div>",
        unsafe_allow_html=True
    )

# 프로젝트별 설정 로드
proj_cfg = settings[selected_project]
proj_act_types = proj_cfg.get("activity_types", ["일반 업무"])
if "주간보고" not in proj_act_types:
    proj_act_types.append("주간보고")
proj_categories = proj_cfg.get("categories", {})
proj_tags = proj_cfg.get("tags", [])
week_start_monday = (settings.get("ui", {}).get("week_start", "월요일") == "월요일")

project_df = df[df["프로젝트"] == selected_project].copy()

# 통합 검색 필터 (모든 메뉴에 반영)
if global_search:
    q = global_search.strip().lower()
    def _hit(row):
        for c in ("제목", "내용", "태그", "관련자(참석자/송수신자)", "장소", "업무유형", "대분류", "중분류"):
            if q in str(row.get(c, "")).lower():
                return True
        return False
    project_df = project_df[project_df.apply(_hit, axis=1)]


# =====================================================
# 9. 사이드바 — 빠른 업무 등록 (모든 메뉴에서 사용 가능)
# =====================================================
with st.sidebar:
    st.markdown("### ➕ 빠른 업무 등록")
    st.caption("대분류를 바꾸면 중분류가 즉시 반영됩니다.")

    q_type = st.selectbox("업무유형", proj_act_types, key="qadd_type")

    cats_keys = list(proj_categories.keys()) or ["없음"]
    q_main = st.selectbox("대분류", cats_keys, key="qadd_main")
    # 대분류 변경 시 중분류 자동 초기화
    if st.session_state.get("qadd_prev_main") != q_main:
        st.session_state["qadd_prev_main"] = q_main
        if "qadd_sub" in st.session_state:
            del st.session_state["qadd_sub"]
    sub_opts = proj_categories.get(q_main, ["없음"]) or ["없음"]
    q_sub = st.selectbox("중분류", sub_opts, key="qadd_sub")

    q_prio = st.selectbox("우선순위", PRIORITY_LIST, index=1, key="qadd_prio")

    col_qd1, col_qd2 = st.columns(2)
    q_start = col_qd1.date_input("시작일", date.today(), key="qadd_start")
    q_target = col_qd2.date_input("목표일", date.today(), key="qadd_target")
    q_no_target = st.checkbox("🕒 목표일 미정 (지속 업무)", key="qadd_no_target")

    q_title = st.text_input("제목 *", placeholder="필수", key="qadd_title")
    q_content = st.text_area("내용", height=80, key="qadd_content")

    # 🤖 AI 자동 분류 버튼 (제목/내용 기반)
    ai_on = ai_available(settings)
    ac1, ac2 = st.columns([1, 1])
    with ac1:
        ai_autoclassify = st.button(
            "🤖 AI 자동 분류",
            disabled=(not ai_on) or (not q_title.strip() and not q_content.strip()),
            help=("AI가 제목/내용을 보고 업무유형·분류·태그·우선순위를 자동 세팅합니다."
                  if ai_on else "관리자 설정 → AI 탭에서 API 키를 등록하세요."),
            use_container_width=True,
            key="qadd_ai_btn",
        )
    if ai_autoclassify:
        try:
            with st.spinner("AI 분류 중..."):
                res = ai_classify_task(settings, q_title, q_content, proj_act_types, proj_categories, proj_tags)
            if isinstance(res, dict) and "업무유형" in res:
                # 세션 상태 덮어쓰기
                if res.get("업무유형") in proj_act_types:
                    st.session_state["qadd_type"] = res["업무유형"]
                if res.get("대분류") in proj_categories:
                    st.session_state["qadd_main"] = res["대분류"]
                    st.session_state["qadd_prev_main"] = res["대분류"]
                    sub_cand = res.get("중분류")
                    if sub_cand in proj_categories.get(res["대분류"], []):
                        st.session_state["qadd_sub"] = sub_cand
                if res.get("우선순위") in PRIORITY_LIST:
                    st.session_state["qadd_prio"] = res["우선순위"]
                if res.get("제안제목"):
                    st.session_state["qadd_title"] = res["제안제목"]
                st.session_state["qadd_ai_tags"] = [t for t in (res.get("태그") or []) if t in proj_tags]
                st.success("AI 분류 반영됨. 필요시 수정 후 등록하세요.")
                st.rerun()
            else:
                st.warning(f"AI 응답 파싱 실패: {res}")
        except Exception as e:
            st.error(f"AI 호출 실패: {e}")

    default_ai_tags = st.session_state.get("qadd_ai_tags", [])
    q_people = st.text_input("참석자/관련자", placeholder="쉼표로 구분", key="qadd_people")
    q_place  = st.text_input("장소", key="qadd_place")
    q_tags   = st.multiselect("태그", proj_tags, default=default_ai_tags, key="qadd_tags")
    q_link   = st.text_input("자료 링크", key="qadd_link")

    if st.button("✅ 등록", use_container_width=True, type="primary", key="qadd_submit"):
        if not q_title.strip():
            st.error("제목은 필수입니다.")
        else:
            now = pd.Timestamp.now()
            new_row = {
                "ID": new_id(),
                "프로젝트": selected_project,
                "업무유형": q_type,
                "대분류": q_main,
                "중분류": q_sub,
                "우선순위": q_prio,
                "시작일": pd.to_datetime(q_start),
                "목표일": pd.NaT if q_no_target else pd.to_datetime(q_target),
                "실제완료일": pd.NaT,
                "장소": q_place,
                "관련자(참석자/송수신자)": q_people,
                "제목": q_title.strip(),
                "내용": q_content,
                "태그": ", ".join(q_tags),
                "상태": "미정" if q_no_target else "진행중",
                "드라이브_링크": q_link,
                "연관업무ID": "",
                "생성일시": now, "수정일시": now,
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            # 폼 입력값 초기화
            for k in ("qadd_title", "qadd_content", "qadd_people", "qadd_place",
                      "qadd_link", "qadd_tags", "qadd_ai_tags"):
                if k in st.session_state:
                    del st.session_state[k]
            st.success(f"등록 완료: {q_title}")
            st.rerun()

    st.markdown("---")
    st.caption("💡 캘린더 항목을 **클릭**하면 하단에 상세 편집 창이 열립니다.")
    if st.session_state.last_deleted is not None:
        if st.button("↩️ 마지막 삭제 되돌리기", use_container_width=True):
            row = st.session_state.last_deleted
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_data(df)
            st.session_state.last_deleted = None
            st.success("복구 완료")
            st.rerun()


# =====================================================
# 10. 상세 편집 팬 (모든 메뉴에서 재사용)
# =====================================================
def render_detail_editor(df, task_id):
    row_idx = df.index[df["ID"] == task_id]
    if len(row_idx) == 0:
        st.warning("선택된 업무를 찾을 수 없습니다.")
        return df
    idx = row_idx[0]
    task = df.loc[idx]

    st.markdown("---")
    hc1, hc2, hc3 = st.columns([7.5, 1.2, 1.3])
    with hc1:
        st.subheader(f"📝 상세 보기 및 수정 — {task['제목']}")
        st.caption(f"ID: `{task['ID']}` · 생성 {pd.to_datetime(task['생성일시']).strftime('%Y-%m-%d %H:%M') if pd.notna(task['생성일시']) else '-'}")
    with hc2:
        if st.button("🗑️ 삭제", key=f"del_{task_id}", use_container_width=True):
            st.session_state.last_deleted = df.loc[idx].to_dict()
            df = df.drop(idx).reset_index(drop=True)
            save_data(df)
            st.session_state.selected_task_id = None
            st.success("삭제되었습니다. (사이드바에서 되돌리기 가능)")
            st.rerun()
    with hc3:
        if st.button("✖️ 닫기", key=f"close_{task_id}", use_container_width=True):
            st.session_state.selected_task_id = None
            st.rerun()

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        stat_idx = STATUS_LIST.index(task["상태"]) if task["상태"] in STATUS_LIST else 0
        e_status = c1.selectbox("상태", STATUS_LIST, index=stat_idx, key=f"st_{task_id}")
        typ_idx = proj_act_types.index(task["업무유형"]) if task["업무유형"] in proj_act_types else 0
        e_type = c2.selectbox("업무유형", proj_act_types, index=typ_idx, key=f"tp_{task_id}")
        prio_idx = PRIORITY_LIST.index(task["우선순위"]) if task["우선순위"] in PRIORITY_LIST else 1
        e_prio = c3.selectbox("우선순위", PRIORITY_LIST, index=prio_idx, key=f"pr_{task_id}")

        # 빠른 완료 처리 버튼
        with c4:
            st.write("")
            if st.button("✅ 지금 완료 처리", key=f"done_{task_id}", use_container_width=True):
                df.at[idx, "상태"] = "완료"
                df.at[idx, "실제완료일"] = pd.Timestamp.now()
                df.at[idx, "수정일시"] = pd.Timestamp.now()
                save_data(df)
                st.success("완료 처리되었습니다.")
                st.rerun()

        c1, c2, c3 = st.columns(3)
        s_date = task["시작일"] if pd.notna(task["시작일"]) else date.today()
        t_date = task["목표일"] if pd.notna(task["목표일"]) else None
        r_date = task["실제완료일"] if pd.notna(task["실제완료일"]) else None

        e_s = c1.date_input("시작일", pd.Timestamp(s_date).date() if pd.notna(s_date) else date.today(), key=f"sd_{task_id}")
        e_no_target = c2.checkbox("목표일 미정", value=(t_date is None), key=f"nt_{task_id}")
        if e_no_target:
            e_t = None
            c2.write("—")
        else:
            e_t = c2.date_input("목표일", pd.Timestamp(t_date).date() if t_date is not None else date.today(), key=f"td_{task_id}")
        e_r = c3.date_input("실제완료일", value=(pd.Timestamp(r_date).date() if r_date is not None else None), key=f"rd_{task_id}")

        c1, c2 = st.columns(2)
        cats = list(proj_categories.keys()) or ["없음"]
        main_key = f"mc_{task_id}"
        sub_key  = f"sc_{task_id}"
        # 초기 진입 시 원본 값으로 세션에 셋업
        if main_key not in st.session_state:
            st.session_state[main_key] = task["대분류"] if task["대분류"] in cats else cats[0]
        # 대분류가 바뀌면 중분류 값을 삭제하여 새 리스트의 첫 항목이 잡히도록
        prev_main_key = f"mc_prev_{task_id}"
        if st.session_state.get(prev_main_key) != st.session_state[main_key]:
            if sub_key in st.session_state:
                del st.session_state[sub_key]
            st.session_state[prev_main_key] = st.session_state[main_key]

        e_main = c1.selectbox("대분류", cats, key=main_key)
        subs = proj_categories.get(e_main, ["없음"]) or ["없음"]
        if sub_key not in st.session_state:
            st.session_state[sub_key] = task["중분류"] if task["중분류"] in subs else subs[0]
        elif st.session_state[sub_key] not in subs:
            st.session_state[sub_key] = subs[0]
        e_sub = c2.selectbox("중분류", subs, key=sub_key)

        e_title = st.text_input("제목", str(task["제목"]) if pd.notna(task["제목"]) else "", key=f"ti_{task_id}")
        e_content = st.text_area("내용", str(task["내용"]) if pd.notna(task["내용"]) else "", height=180, key=f"co_{task_id}")

        c1, c2 = st.columns(2)
        e_ppl = c1.text_input("관련자 (참석자/송수신자)",
                              str(task["관련자(참석자/송수신자)"]) if pd.notna(task["관련자(참석자/송수신자)"]) else "",
                              key=f"pp_{task_id}")
        e_loc = c2.text_input("장소", str(task["장소"]) if pd.notna(task["장소"]) else "", key=f"lo_{task_id}")

        cur_tags = [t.strip() for t in str(task["태그"]).split(",") if t.strip()] if pd.notna(task["태그"]) else []
        # 새 태그가 목록에 없어도 우선 표시하기 위해 union
        tag_options = list(dict.fromkeys(proj_tags + cur_tags))
        e_tags = st.multiselect("태그", tag_options, default=[t for t in cur_tags if t in tag_options], key=f"tg_{task_id}")
        e_link = st.text_input("자료 링크", str(task["드라이브_링크"]) if pd.notna(task["드라이브_링크"]) else "", key=f"lk_{task_id}")

        save_c1, save_c2, save_c3 = st.columns([1, 1, 4])
        with save_c1:
            if st.button("💾 저장", key=f"sv_{task_id}", type="primary", use_container_width=True):
                df.at[idx, "상태"] = e_status
                df.at[idx, "업무유형"] = e_type
                df.at[idx, "우선순위"] = e_prio
                df.at[idx, "대분류"] = e_main
                df.at[idx, "중분류"] = e_sub
                df.at[idx, "시작일"] = pd.to_datetime(e_s)
                df.at[idx, "목표일"] = pd.NaT if e_no_target else pd.to_datetime(e_t)
                df.at[idx, "실제완료일"] = pd.to_datetime(e_r) if e_r else pd.NaT
                df.at[idx, "제목"] = e_title
                df.at[idx, "내용"] = e_content
                df.at[idx, "관련자(참석자/송수신자)"] = e_ppl
                df.at[idx, "장소"] = e_loc
                df.at[idx, "태그"] = ", ".join(e_tags)
                df.at[idx, "드라이브_링크"] = e_link
                df.at[idx, "수정일시"] = pd.Timestamp.now()
                save_data(df)
                # 편집 관련 session_state 정리 (다음 진입 시 최신 값으로 초기화)
                for k in list(st.session_state.keys()):
                    if k.endswith(f"_{task_id}"):
                        del st.session_state[k]
                st.success("저장 완료")
                st.rerun()
        with save_c2:
            # 🤖 AI 내용 정리 버튼
            ai_on = ai_available(settings)
            if st.button("🤖 AI 내용 다듬기", key=f"ai_polish_{task_id}",
                         disabled=(not ai_on) or (not e_content.strip()),
                         help=("지저분한 메모를 업무일지 형태로 정리합니다."
                               if ai_on else "관리자 → AI 탭에서 API 키를 등록하세요."),
                         use_container_width=True):
                try:
                    with st.spinner("AI 정리 중..."):
                        polished = ai_polish_task_note(settings, e_content)
                    df.at[idx, "내용"] = polished
                    df.at[idx, "수정일시"] = pd.Timestamp.now()
                    save_data(df)
                    # 내용 필드 세션값 제거하여 새 값 로드
                    if f"co_{task_id}" in st.session_state:
                        del st.session_state[f"co_{task_id}"]
                    st.success("내용을 다듬어 저장했습니다.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"AI 실패: {ex}")
        with save_c3:
            st.caption("💡 완료 상태로 저장하면 캘린더에서 취소선/흐린 색으로 표시됩니다.")

    return df


# =====================================================
# 11. 메뉴: 📊 대시보드
# =====================================================
if menu == "📊 대시보드":
    # ---- KPI ----
    total   = len(project_df)
    ongoing = int((project_df["상태"] == "진행중").sum())
    hold    = int((project_df["상태"] == "보류").sum())
    delayed = int(compute_overdue(project_df).sum())
    done_this_week = 0
    if not project_df.empty:
        ws_kpi, we_kpi = week_range(date.today(), start_monday=week_start_monday)
        _done_dates = pd.to_datetime(project_df["실제완료일"], errors="coerce")
        done_this_week = int(
            ((project_df["상태"] == "완료") & (_done_dates >= ws_kpi) & (_done_dates <= we_kpi)).sum()
        )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(f"<div class='kpi info'><div class='label'>전체 업무</div><div class='value'>{total}</div><div class='sub'>{selected_project}</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi'><div class='label'>진행중</div><div class='value'>{ongoing}</div><div class='sub'>진행 상태</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi hold'><div class='label'>보류</div><div class='value'>{hold}</div><div class='sub'>일시 중지</div></div>", unsafe_allow_html=True)
    k4.markdown(f"<div class='kpi warn'><div class='label'>지연</div><div class='value'>{delayed}</div><div class='sub'>목표일 초과</div></div>", unsafe_allow_html=True)
    k5.markdown(f"<div class='kpi good'><div class='label'>이번주 완료</div><div class='value'>{done_this_week}</div><div class='sub'>주간 성과</div></div>", unsafe_allow_html=True)

    st.markdown("### 🗓️ 업무 일정 캘린더")
    # 캘린더 네비게이션
    nav1, nav2, nav3, nav4, nav5, nav6 = st.columns([1, 1, 1.2, 2, 1, 1])
    with nav1:
        if st.button("◀ 이전"):
            st.session_state.cal_base_date = st.session_state.cal_base_date - timedelta(weeks=4)
            st.rerun()
    with nav2:
        if st.button("다음 ▶"):
            st.session_state.cal_base_date = st.session_state.cal_base_date + timedelta(weeks=4)
            st.rerun()
    with nav3:
        if st.button("🎯 오늘로", use_container_width=True):
            st.session_state.cal_base_date = date.today()
            st.rerun()
    with nav4:
        picked_date = st.date_input(
            "조회 기준일", value=st.session_state.cal_base_date, label_visibility="collapsed"
        )
        st.session_state.cal_base_date = picked_date
    with nav5:
        st.session_state.view_mode = st.selectbox(
            "뷰", ["월간", "주간", "리스트"],
            index=["월간", "주간", "리스트"].index(st.session_state.view_mode),
            label_visibility="collapsed"
        )
    with nav6:
        cal_status_filter = st.selectbox("필터", ["전체", "진행중만", "미완료만"], label_visibility="collapsed")

    cal_df = project_df.copy()
    if cal_status_filter == "진행중만":
        cal_df = cal_df[cal_df["상태"] == "진행중"]
    elif cal_status_filter == "미완료만":
        cal_df = cal_df[cal_df["상태"] != "완료"]

    if st.session_state.view_mode == "월간":
        st.markdown(
            render_month_calendar(cal_df, st.session_state.cal_base_date, proj_act_types, week_start_monday),
            unsafe_allow_html=True
        )
    elif st.session_state.view_mode == "주간":
        st.markdown(
            render_week_agenda(cal_df, st.session_state.cal_base_date, proj_act_types, week_start_monday),
            unsafe_allow_html=True
        )
    else:
        # 리스트 뷰 (오늘 이후 예정 업무)
        upcoming = cal_df[cal_df["시작일"].notna()].copy()
        upcoming = upcoming.sort_values("시작일")
        show_cols = ["상태", "업무유형", "우선순위", "시작일", "목표일", "제목", "태그"]
        st.dataframe(
            upcoming[show_cols],
            use_container_width=True, hide_index=True,
            column_config={
                "시작일": st.column_config.DateColumn(format="YYYY-MM-DD"),
                "목표일": st.column_config.DateColumn(format="YYYY-MM-DD"),
            }
        )

    # 컬러 범례
    with st.expander("🎨 색상 범례", expanded=False):
        legend_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;'>"
        for name, c in TYPE_COLORS.items():
            legend_html += (
                f"<span style='background:{c['bg']};color:{c['fg']};padding:3px 10px;border-radius:12px;font-size:12px;'>{name} · 진행</span>"
                f"<span style='background:{c['bg_done']};color:{c['fg_done']};padding:3px 10px;border-radius:12px;font-size:12px;'>{name} · 완료</span>"
            )
        legend_html += f"<span style='background:{DELAY_COLOR['bg']};color:{DELAY_COLOR['fg']};padding:3px 10px;border-radius:12px;font-size:12px;'>지연</span>"
        legend_html += f"<span style='background:{HOLD_COLOR['bg']};color:{HOLD_COLOR['fg']};padding:3px 10px;border-radius:12px;font-size:12px;'>보류</span>"
        legend_html += "</div>"
        st.markdown(legend_html, unsafe_allow_html=True)

    # ---------- 주간보고 자동 생성 ----------
    st.markdown("### 📊 주간 업무 요약 보고서")
    with st.container(border=True):
        curr_date = pd.Timestamp(st.session_state.cal_base_date)
        year, week_num, _ = curr_date.isocalendar()
        ws, we = week_range(curr_date, start_monday=week_start_monday)
        sunday_date = we
        report_title = f"[{year}-W{week_num:02d}] 주간보고"

        rc1, rc2, rc3, rc4 = st.columns([4, 3, 2, 2])
        with rc1:
            st.markdown(f"**기준 주차:** {year}년 {week_num}주 ({ws.strftime('%Y-%m-%d')} ~ {we.strftime('%Y-%m-%d')})")
        with rc2:
            report_scope = st.selectbox(
                "요약 범위",
                ["이번 주 (모든 업무)", "이번 주 (완료만)", "이번 주 (진행+지연)"],
                key="report_scope"
            )
        with rc3:
            auto_btn = st.button("✨ 규칙 요약", use_container_width=True)
        with rc4:
            ai_on_rep = ai_available(settings)
            ai_report_btn = st.button(
                "🤖 AI 보고서 작성",
                use_container_width=True, type="primary",
                disabled=(not ai_on_rep),
                help=("AI가 문장형 주간보고를 작성합니다." if ai_on_rep else "관리자 → AI 탭에서 API 키를 등록하세요."),
            )

        if ai_report_btn:
            mask = (
                (project_df["시작일"] <= we) &
                (project_df["목표일"].isna() | (project_df["목표일"] >= ws)) &
                (project_df["업무유형"] != "주간보고")
            )
            wk = project_df[mask]
            lines = []
            for _, t in wk.iterrows():
                start = pd.Timestamp(t["시작일"]).strftime("%m/%d") if pd.notna(t["시작일"]) else "-"
                end   = pd.Timestamp(t["목표일"]).strftime("%m/%d") if pd.notna(t["목표일"]) else "미정"
                ppl   = t["관련자(참석자/송수신자)"] if pd.notna(t["관련자(참석자/송수신자)"]) else ""
                tags  = t["태그"] if pd.notna(t["태그"]) else ""
                content = (str(t["내용"])[:200] if pd.notna(t["내용"]) else "")
                lines.append(
                    f"- [{t['상태']}][{t['업무유형']}][{t['대분류']}/{t['중분류']}] "
                    f"{t['제목']} ({start}~{end}, 관련: {ppl}, 태그: {tags}) :: {content}"
                )
            tasks_summary = "\n".join(lines) if lines else "(이번 주 업무 없음)"
            try:
                with st.spinner("AI가 주간보고를 작성 중..."):
                    ai_report = ai_write_weekly_report(
                        settings, selected_project,
                        f"{year}년 {week_num}주차 ({ws.strftime('%m/%d')}~{we.strftime('%m/%d')})",
                        tasks_summary
                    )
                st.session_state[f"temp_report_{selected_project}_{week_num}"] = ai_report
                st.success("AI 주간보고서 초안이 생성되었습니다.")
                st.rerun()
            except Exception as ex:
                st.error(f"AI 실패: {ex}")

        if auto_btn:
            mask = (
                (project_df["시작일"] <= we) &
                (project_df["목표일"].isna() | (project_df["목표일"] >= ws)) &
                (project_df["업무유형"] != "주간보고")
            )
            wk = project_df[mask]

            summary = [f"📌 {selected_project} 주간 업무 보고 — {year}년 {week_num}주차"]
            summary.append(f"📅 기간: {ws.strftime('%Y-%m-%d')} ~ {we.strftime('%Y-%m-%d')}")
            summary.append("")

            completed = wk[wk["상태"] == "완료"]
            ongoing_w = wk[wk["상태"].isin(["진행중", "미정"])]
            delayed_w = wk[wk["상태"] == "지연"]
            held_w    = wk[wk["상태"] == "보류"]

            if report_scope != "이번 주 (진행+지연)":
                summary.append(f"✅ 완료 업무 ({len(completed)}건)")
                if completed.empty:
                    summary.append("  · 없음")
                else:
                    for _, t in completed.iterrows():
                        ppl = f" ({t['관련자(참석자/송수신자)']})" if pd.notna(t['관련자(참석자/송수신자)']) and str(t['관련자(참석자/송수신자)']).strip() else ""
                        tags = f" [태그: {t['태그']}]" if pd.notna(t['태그']) and t['태그'] else ""
                        summary.append(f"  · [{t['업무유형']}] {t['제목']}{ppl}{tags}")
                summary.append("")

            if report_scope != "이번 주 (완료만)":
                summary.append(f"🏃 진행/예정 업무 ({len(ongoing_w)}건)")
                if ongoing_w.empty:
                    summary.append("  · 없음")
                else:
                    for _, t in ongoing_w.iterrows():
                        due = f" (~{pd.Timestamp(t['목표일']).strftime('%m/%d')})" if pd.notna(t['목표일']) else " (목표일 미정)"
                        summary.append(f"  · [{t['업무유형']}] {t['제목']}{due}")
                summary.append("")

                if not delayed_w.empty:
                    summary.append(f"⚠️ 지연 업무 ({len(delayed_w)}건)")
                    for _, t in delayed_w.iterrows():
                        summary.append(f"  · [{t['업무유형']}] {t['제목']}")
                    summary.append("")
                if not held_w.empty:
                    summary.append(f"⏸️ 보류 업무 ({len(held_w)}건)")
                    for _, t in held_w.iterrows():
                        summary.append(f"  · [{t['업무유형']}] {t['제목']}")
                    summary.append("")

            summary.append("📝 특이사항 / 다음 주 계획:")
            summary.append("  · ")
            st.session_state[f"temp_report_{selected_project}_{week_num}"] = "\n".join(summary)
            st.rerun()

        existing = df[(df["프로젝트"] == selected_project)
                      & (df["제목"] == report_title)
                      & (df["업무유형"] == "주간보고")]
        default_text = existing["내용"].iloc[0] if not existing.empty else ""
        cached_key = f"temp_report_{selected_project}_{week_num}"
        report_text = st.session_state.get(cached_key, default_text)

        edited = st.text_area("보고서 내용 (자동 요약 후 자유롭게 편집)", value=report_text, height=260)

        rb1, rb2, rb3 = st.columns([1, 1, 4])
        with rb1:
            if st.button("💾 보고서 저장", type="primary", use_container_width=True):
                now = pd.Timestamp.now()
                if not existing.empty:
                    df.at[existing.index[0], "내용"] = edited
                    df.at[existing.index[0], "시작일"] = pd.to_datetime(sunday_date)
                    df.at[existing.index[0], "목표일"] = pd.to_datetime(sunday_date)
                    df.at[existing.index[0], "수정일시"] = now
                else:
                    row = {
                        "ID": new_id(),
                        "프로젝트": selected_project, "업무유형": "주간보고",
                        "대분류": (list(proj_categories.keys())[0] if proj_categories else "없음"),
                        "중분류": "없음", "우선순위": "🔵 보통",
                        "시작일": pd.to_datetime(sunday_date),
                        "목표일": pd.to_datetime(sunday_date),
                        "실제완료일": now,
                        "장소": "-", "관련자(참석자/송수신자)": "-",
                        "제목": report_title, "내용": edited,
                        "태그": "주간보고", "상태": "완료",
                        "드라이브_링크": "", "연관업무ID": "",
                        "생성일시": now, "수정일시": now,
                    }
                    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                save_data(df)
                st.success(f"{report_title} 저장 완료 (해당 주 일요일 캘린더에 표시)")
                if cached_key in st.session_state:
                    del st.session_state[cached_key]
                st.rerun()
        with rb2:
            st.download_button(
                "⬇️ 보고서 다운로드 (.txt)",
                data=edited.encode("utf-8"),
                file_name=f"{report_title}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with rb3:
            st.caption("💡 저장된 보고서는 캘린더에서 클릭하여 재편집할 수 있습니다.")

    # ---------- 집중 업무표 ----------
    st.markdown("### 📋 집중 업무표 (완료 제외)")
    fc1, fc2, fc3 = st.columns([3, 3, 3])
    with fc1:
        tag_filter = st.multiselect("태그 필터", proj_tags)
    with fc2:
        type_filter = st.multiselect("업무유형 필터", proj_act_types)
    with fc3:
        prio_filter = st.multiselect("우선순위 필터", PRIORITY_LIST)

    disp = project_df[project_df["상태"].isin(["진행중", "미정", "지연", "보류"])].copy()
    if tag_filter:
        pat = "|".join(map(re.escape, tag_filter))
        disp = disp[disp["태그"].fillna("").str.contains(pat, na=False)]
    if type_filter:
        disp = disp[disp["업무유형"].isin(type_filter)]
    if prio_filter:
        disp = disp[disp["우선순위"].isin(prio_filter)]

    # 지연 여부 자동 반영 (표시용)
    show_cols = ["상태", "업무유형", "우선순위", "시작일", "목표일", "제목", "내용", "태그", "관련자(참석자/송수신자)"]
    if disp.empty:
        st.info("현재 조건에 맞는 업무가 없습니다. 사이드바에서 새 업무를 등록해 보세요.")
    else:
        event = st.dataframe(
            disp[show_cols].sort_values(by=["우선순위", "목표일"], ascending=[False, True], na_position="last"),
            use_container_width=True, hide_index=True,
            on_select="rerun", selection_mode="single-row",
            column_config={
                "시작일": st.column_config.DateColumn(format="YYYY-MM-DD"),
                "목표일": st.column_config.DateColumn(format="YYYY-MM-DD"),
            },
            key="focus_table"
        )
        if event.selection.rows:
            selected_row = disp.iloc[event.selection.rows[0]]
            st.session_state.selected_task_id = selected_row["ID"]

    # 상세 편집
    if st.session_state.selected_task_id:
        df = render_detail_editor(df, st.session_state.selected_task_id)


# =====================================================
# 12. 메뉴: 🗓️ 캘린더 (독립 페이지)
# =====================================================
elif menu == "🗓️ 캘린더 (월/주/리스트)":
    st.markdown("### 🗓️ 캘린더")
    nav1, nav2, nav3, nav4, nav5 = st.columns([1, 1, 1.2, 2.5, 1.3])
    with nav1:
        if st.button("◀ 이전"):
            st.session_state.cal_base_date = st.session_state.cal_base_date - timedelta(weeks=4)
            st.rerun()
    with nav2:
        if st.button("다음 ▶"):
            st.session_state.cal_base_date = st.session_state.cal_base_date + timedelta(weeks=4)
            st.rerun()
    with nav3:
        if st.button("🎯 오늘로 복귀", use_container_width=True):
            st.session_state.cal_base_date = date.today()
            st.rerun()
    with nav4:
        picked_date2 = st.date_input(
            "조회 기준일", value=st.session_state.cal_base_date, label_visibility="collapsed",
            key="cal_date_page"
        )
        st.session_state.cal_base_date = picked_date2
    with nav5:
        st.session_state.view_mode = st.selectbox(
            "뷰", ["월간", "주간", "리스트"],
            index=["월간", "주간", "리스트"].index(st.session_state.view_mode),
            label_visibility="collapsed",
            key="view_mode_page"
        )
    if st.session_state.view_mode == "월간":
        st.markdown(render_month_calendar(project_df, st.session_state.cal_base_date, proj_act_types, week_start_monday),
                    unsafe_allow_html=True)
    elif st.session_state.view_mode == "주간":
        st.markdown(render_week_agenda(project_df, st.session_state.cal_base_date, proj_act_types, week_start_monday),
                    unsafe_allow_html=True)
    else:
        upcoming = project_df[project_df["시작일"].notna()].sort_values("시작일")
        st.dataframe(upcoming[["상태", "업무유형", "우선순위", "시작일", "목표일", "제목", "태그"]],
                     use_container_width=True, hide_index=True,
                     column_config={
                         "시작일": st.column_config.DateColumn(format="YYYY-MM-DD"),
                         "목표일": st.column_config.DateColumn(format="YYYY-MM-DD"),
                     })
    if st.session_state.selected_task_id:
        df = render_detail_editor(df, st.session_state.selected_task_id)


# =====================================================
# 13. 메뉴: 📩 이메일 연동함
# =====================================================
elif menu == "📩 이메일 연동함":
    st.markdown("### 📩 Gmail 연동 & 업무 자동 등록")

    g = settings.get("gmail_settings", {})
    with st.expander("⚙️ Gmail 연동 설정 (한 번만 입력, 앱 비밀번호 사용)", expanded=not bool(g.get("app_password"))):
        cg1, cg2 = st.columns(2)
        g_email  = cg1.text_input("Gmail 주소", value=g.get("email", ""))
        g_pw     = cg2.text_input("앱 비밀번호 (16자리, 공백 제거)", value=g.get("app_password", ""), type="password")
        g_target = st.text_input("고정 발신자 필터 (쉼표 구분)",
                                 value=g.get("target_sender", "hblee@dh.co.kr, 이헌범"))
        st.caption("💡 Google 계정 → 보안 → 2단계 인증 활성화 → '앱 비밀번호'에서 발급받으세요.")
        if st.button("💾 설정 저장", type="primary"):
            settings["gmail_settings"] = {
                "email": g_email.strip(),
                "app_password": g_pw.strip().replace(" ", ""),
                "target_sender": g_target.strip(),
            }
            save_settings(settings)
            st.success("메일 설정이 저장되었습니다.")
            st.rerun()

    fetch_c1, fetch_c2 = st.columns([1, 4])
    with fetch_c1:
        do_fetch = st.button("🔄 새 메일 불러오기", type="primary", use_container_width=True)
    with fetch_c2:
        st.caption(f"필터: **{g.get('target_sender', '')}** · 최근 200통 스캔 → 최대 15통")

    if do_fetch:
        if g.get("email") and g.get("app_password") and g.get("target_sender"):
            with st.spinner("Gmail에서 메일을 검색 중..."):
                emails = fetch_musv_emails(g["email"], g["app_password"], g["target_sender"], limit=15, scan=200)
            if emails:
                st.session_state.fetched_emails = emails
                # 이전 AI 결과 초기화
                for k in list(st.session_state.keys()):
                    if k.startswith("mail_ai_") or k.startswith("mcat_") or k.startswith("msub_") \
                            or k.startswith("mtype_") or k.startswith("mprio_") or k.startswith("mtags_") \
                            or k.startswith("mdate_") or k.startswith("mstat_"):
                        del st.session_state[k]
                # 옵션: 자동 AI 분류
                if ai_available(settings) and settings.get("ai", {}).get("auto_classify_on_email", True):
                    prog = st.progress(0.0, text="AI 자동 분류 중...")
                    for i, m in enumerate(emails):
                        try:
                            cls = ai_classify_task(
                                settings, m["제목"], (m.get("본문") or m["본문요약"] or ""),
                                proj_act_types, proj_categories, proj_tags
                            )
                            if isinstance(cls, dict) and "업무유형" in cls:
                                st.session_state[f"mail_ai_{i}"] = cls
                                st.session_state[f"mail_ai_done_{i}"] = True
                        except Exception:
                            pass
                        prog.progress((i+1)/len(emails), text=f"AI 자동 분류 중... ({i+1}/{len(emails)})")
                    prog.empty()
                st.success(f"{len(emails)}통을 불러왔습니다.")
            else:
                st.warning("조건에 맞는 메일이 없거나 로그인에 실패했습니다.")
        else:
            st.error("설정 값을 먼저 입력하고 저장해 주세요.")

    emails = st.session_state.get("fetched_emails", [])
    if emails:
        ai_on = ai_available(settings)
        st.markdown(f"#### 📥 수신된 메일 ({len(emails)}통)")
        if ai_on:
            batch_c1, batch_c2 = st.columns([1, 5])
            with batch_c1:
                if st.button("🤖 전체 AI 자동 분석", use_container_width=True, type="primary"):
                    prog = st.progress(0.0)
                    for i, m in enumerate(emails):
                        if st.session_state.get(f"mail_ai_done_{i}"):
                            prog.progress((i+1)/len(emails)); continue
                        try:
                            cls = ai_classify_task(
                                settings, m["제목"], (m.get("본문") or m["본문요약"] or ""),
                                proj_act_types, proj_categories, proj_tags
                            )
                            if isinstance(cls, dict) and "업무유형" in cls:
                                st.session_state[f"mail_ai_{i}"] = cls
                                st.session_state[f"mail_ai_done_{i}"] = True
                        except Exception:
                            pass
                        prog.progress((i+1)/len(emails))
                    st.success("일괄 AI 분석 완료. 각 카드 값이 자동 채워졌습니다.")
                    st.rerun()
            with batch_c2:
                st.caption("💡 버튼을 누르면 모든 메일의 업무유형·분류·태그·우선순위·마감일을 AI가 한번에 세팅합니다. 확인 후 [등록]만 눌러주세요.")

        for idx, mail in enumerate(emails):
            ai_res = st.session_state.get(f"mail_ai_{idx}", {})
            with st.container(border=True):
                mc1, mc2 = st.columns([3, 2])
                with mc1:
                    st.markdown(f"**[{mail['회사명'].upper()}]** {mail['제목']}")
                    st.caption(f"보낸이: {mail['보낸이']} · {mail['날짜']}")
                    with st.expander("본문 미리보기"):
                        st.write(mail["본문요약"] or "(본문 없음)")
                    if ai_res:
                        with st.expander("🤖 AI 요약", expanded=True):
                            st.write(ai_res.get("요약", "-"))
                    ai_single = st.button(
                        "🤖 이 메일만 AI 분석", key=f"mail_ai_btn_{idx}",
                        disabled=(not ai_on),
                        help=("이 메일 한 건에 대해 자동분류·요약을 실행"
                              if ai_on else "관리자 → AI 탭에서 API 키를 등록하세요."),
                    )
                    if ai_single:
                        try:
                            with st.spinner("AI 분석 중..."):
                                cls = ai_classify_task(
                                    settings, mail["제목"], (mail.get("본문") or mail["본문요약"] or ""),
                                    proj_act_types, proj_categories, proj_tags
                                )
                            if isinstance(cls, dict) and "업무유형" in cls:
                                st.session_state[f"mail_ai_{idx}"] = cls
                                st.session_state[f"mail_ai_done_{idx}"] = True
                                st.rerun()
                            else:
                                st.warning(f"AI 응답 이상: {cls}")
                        except Exception as ex:
                            st.error(f"AI 실패: {ex}")

                with mc2:
                    # AI 추천값을 기본값으로
                    ai_type = ai_res.get("업무유형") if ai_res.get("업무유형") in proj_act_types else None
                    default_type = ai_type or ("메일/자료 송수신" if "메일/자료 송수신" in proj_act_types else proj_act_types[0])
                    m_type = st.selectbox("업무유형", proj_act_types,
                                          index=proj_act_types.index(default_type),
                                          key=f"mtype_{idx}")

                    default_stat = "진행중"
                    m_stat = st.selectbox("상태", ["진행중", "미정", "완료"],
                                          index=["진행중", "미정", "완료"].index(default_stat),
                                          key=f"mstat_{idx}")

                    # AI 마감일 파싱
                    default_due = date.today() + timedelta(days=7)
                    ai_due = ai_res.get("마감일자") or ""
                    if ai_due:
                        try:
                            default_due = pd.to_datetime(ai_due).date()
                        except Exception:
                            pass
                    m_date = st.date_input("마감 일정", default_due, key=f"mdate_{idx}")

                    ai_prio = ai_res.get("우선순위") if ai_res.get("우선순위") in PRIORITY_LIST else None
                    m_prio = st.selectbox("우선순위", PRIORITY_LIST,
                                          index=PRIORITY_LIST.index(ai_prio) if ai_prio else 1,
                                          key=f"mprio_{idx}")

                    ai_tags = [t for t in (ai_res.get("태그") or []) if t in proj_tags]
                    m_tags = st.multiselect("태그", proj_tags, default=ai_tags, key=f"mtags_{idx}")

                    m_cats = list(proj_categories.keys()) or ["없음"]
                    # AI 대분류 세션 초기값
                    mcat_key = f"mcat_{idx}"
                    if mcat_key not in st.session_state:
                        if ai_res.get("대분류") in m_cats:
                            st.session_state[mcat_key] = ai_res["대분류"]
                        else:
                            st.session_state[mcat_key] = m_cats[0]
                    # 대분류 변경 시 중분류 초기화
                    prev_key = f"mcat_prev_{idx}"
                    if st.session_state.get(prev_key) != st.session_state[mcat_key]:
                        if f"msub_{idx}" in st.session_state:
                            del st.session_state[f"msub_{idx}"]
                        st.session_state[prev_key] = st.session_state[mcat_key]
                    m_cat  = st.selectbox("대분류", m_cats, key=mcat_key)
                    m_subs = proj_categories.get(m_cat, ["없음"]) or ["없음"]
                    msub_key = f"msub_{idx}"
                    if msub_key not in st.session_state:
                        ai_sub = ai_res.get("중분류")
                        st.session_state[msub_key] = ai_sub if ai_sub in m_subs else m_subs[0]
                    elif st.session_state[msub_key] not in m_subs:
                        st.session_state[msub_key] = m_subs[0]
                    m_sub  = st.selectbox("중분류", m_subs, key=msub_key)

                    if st.button("📌 캘린더에 등록", key=f"mreg_{idx}", use_container_width=True, type="primary"):
                        now = pd.Timestamp.now()
                        # AI 요약이 있으면 제목/내용에 반영
                        ai_title = ai_res.get("제안제목") or mail["제목"][:150]
                        body_prefix = ""
                        if ai_res.get("요약"):
                            body_prefix = f"📌 AI 요약\n{ai_res['요약']}\n\n"
                            if ai_res.get("액션아이템"):
                                body_prefix += "✅ 액션아이템\n" + "\n".join(f"- {a}" for a in ai_res['액션아이템']) + "\n\n"
                            body_prefix += "───────\n📩 원문\n"
                        row = {
                            "ID": new_id(),
                            "프로젝트": selected_project, "업무유형": m_type,
                            "대분류": m_cat, "중분류": m_sub, "우선순위": m_prio,
                            "시작일": pd.to_datetime(date.today()),
                            "목표일": pd.NaT if m_stat == "미정" else pd.to_datetime(m_date),
                            "실제완료일": now if m_stat == "완료" else pd.NaT,
                            "장소": "-",
                            "관련자(참석자/송수신자)": mail["회사명"],
                            "제목": ai_title[:150],
                            "내용": (body_prefix + (mail.get("본문") or mail["본문요약"]))[:3000],
                            "태그": ", ".join(m_tags),
                            "상태": m_stat,
                            "드라이브_링크": "",
                            "연관업무ID": "",
                            "생성일시": now, "수정일시": now,
                        }
                        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                        save_data(df)
                        # 이 메일은 처리됨 표시
                        st.success("등록 완료")
    else:
        st.info("'새 메일 불러오기'를 눌러 시작하세요.")


# =====================================================
# 14. 메뉴: 🗂️ 전체 항목 · 검색
# =====================================================
elif menu == "🗂️ 전체 항목 · 검색":
    st.markdown("### 🗂️ 전체 업무 내역 · 검색")

    fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
    q = fc1.text_input("🔍 검색어", placeholder="제목·내용·태그·관련자·장소")
    s_filter = fc2.multiselect("상태", STATUS_LIST)
    t_filter = fc3.multiselect("업무유형", proj_act_types)
    tag_flt  = fc4.multiselect("태그", proj_tags)

    d1, d2, d3 = st.columns([2, 2, 6])
    date_from = d1.date_input("시작일 이후", value=None, key="df_from")
    date_to   = d2.date_input("시작일 이전", value=None, key="df_to")

    filtered = project_df.copy()
    if q:
        qq = q.lower()
        m = pd.Series(False, index=filtered.index)
        for c in ("제목", "내용", "태그", "관련자(참석자/송수신자)", "장소", "업무유형", "대분류", "중분류"):
            m = m | filtered[c].fillna("").astype(str).str.lower().str.contains(re.escape(qq))
        filtered = filtered[m]
    if s_filter: filtered = filtered[filtered["상태"].isin(s_filter)]
    if t_filter: filtered = filtered[filtered["업무유형"].isin(t_filter)]
    if tag_flt:
        pat = "|".join(map(re.escape, tag_flt))
        filtered = filtered[filtered["태그"].fillna("").str.contains(pat, na=False)]
    if date_from:
        filtered = filtered[filtered["시작일"] >= pd.to_datetime(date_from)]
    if date_to:
        filtered = filtered[filtered["시작일"] <= pd.to_datetime(date_to)]

    st.caption(f"📊 총 **{len(filtered)}건** 조회됨")

    show_cols = ["상태", "업무유형", "우선순위", "시작일", "목표일", "실제완료일",
                 "관련자(참석자/송수신자)", "제목", "태그", "드라이브_링크"]
    event = st.dataframe(
        filtered[show_cols].sort_values("시작일", ascending=False),
        use_container_width=True, hide_index=True,
        on_select="rerun", selection_mode="single-row",
        column_config={
            "시작일": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "목표일": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "실제완료일": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "드라이브_링크": st.column_config.LinkColumn("자료 링크"),
        },
        key="all_table"
    )
    if event.selection.rows:
        row_sel = filtered.iloc[event.selection.rows[0]]
        st.session_state.selected_task_id = row_sel["ID"]

    # 내보내기
    st.download_button(
        "⬇️ 현재 조회 결과 CSV 다운로드",
        data=filtered.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"업무내역_{selected_project}_{date.today()}.csv",
        mime="text/csv",
    )

    if st.session_state.selected_task_id:
        df = render_detail_editor(df, st.session_state.selected_task_id)


# =====================================================
# 15. 메뉴: 📈 통계
# =====================================================
elif menu == "📈 통계":
    st.markdown("### 📈 업무 통계 대시보드")
    if project_df.empty:
        st.info("표시할 데이터가 없습니다.")
    else:
        # 상태별 파이
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**상태별 분포**")
            s_cnt = project_df["상태"].value_counts().reset_index()
            s_cnt.columns = ["상태", "건수"]
            color_map = {"진행중": "#3b82f6", "완료": "#10b981", "지연": "#ef4444",
                         "미정": "#6b7280", "보류": "#f59e0b"}
            fig = px.pie(s_cnt, names="상태", values="건수", hole=0.45,
                         color="상태", color_discrete_map=color_map)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("**업무유형별 분포**")
            t_cnt = project_df["업무유형"].value_counts().reset_index()
            t_cnt.columns = ["업무유형", "건수"]
            fig2 = px.bar(t_cnt, x="업무유형", y="건수", color="업무유형", text="건수")
            fig2.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig2, use_container_width=True)

        # 주별 완료 추이
        st.markdown("**주별 완료 건수 (최근 12주)**")
        done_df = project_df[project_df["상태"] == "완료"].copy()
        done_df["완료일"] = pd.to_datetime(done_df["실제완료일"], errors="coerce")
        done_df = done_df.dropna(subset=["완료일"])
        if not done_df.empty:
            done_df["주"] = done_df["완료일"].dt.to_period("W-MON").dt.start_time
            weekly = done_df.groupby("주").size().reset_index(name="완료건수").sort_values("주").tail(12)
            fig3 = px.bar(weekly, x="주", y="완료건수", text="완료건수", color_discrete_sequence=["#10b981"])
            fig3.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.caption("아직 완료된 업무가 없습니다.")

        # 대분류별
        st.markdown("**대분류 × 상태 히트맵**")
        pivot = project_df.pivot_table(index="대분류", columns="상태", values="ID",
                                       aggfunc="count", fill_value=0)
        if not pivot.empty:
            fig4 = go.Figure(data=go.Heatmap(
                z=pivot.values, x=pivot.columns, y=pivot.index,
                colorscale="Blues", text=pivot.values, texttemplate="%{text}",
            ))
            fig4.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340)
            st.plotly_chart(fig4, use_container_width=True)

        # 태그 클라우드 (막대)
        st.markdown("**태그별 사용 빈도 Top 15**")
        tag_series = project_df["태그"].fillna("").astype(str).str.split(",").explode().str.strip()
        tag_series = tag_series[tag_series != ""]
        if not tag_series.empty:
            tag_cnt = tag_series.value_counts().head(15).reset_index()
            tag_cnt.columns = ["태그", "건수"]
            fig5 = px.bar(tag_cnt, x="건수", y="태그", orientation="h", color="건수",
                          color_continuous_scale="Blues")
            fig5.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=380, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig5, use_container_width=True)


# =====================================================
# 16. 메뉴: ⚙️ 관리자 설정
# =====================================================
elif menu == "⚙️ 관리자 설정":
    st.markdown("### ⚙️ 관리자 설정")

    tab1, tab2, tab3, tab_ai, tab4, tab5 = st.tabs([
        "📁 프로젝트", "🏷️ 분류·태그·업무유형", "📧 Gmail", "🤖 AI (자동화)", "🎨 UI/테마", "💾 백업·복원"
    ])

    # ---------- 프로젝트 관리 ----------
    with tab1:
        st.markdown("#### 프로젝트 목록")
        for p in list(settings.keys()):
            if p in ("gmail_settings", "ui", "ai"): continue
            pc1, pc2, pc3 = st.columns([5, 2, 2])
            pc1.write(f"**📁 {p}**  · 태그 {len(settings[p].get('tags', []))}개 · 분류 {len(settings[p].get('categories', {}))}개")
            new_name = pc2.text_input("이름 변경", value=p, key=f"rn_{p}", label_visibility="collapsed")
            if pc3.button("💾 변경", key=f"rnbtn_{p}"):
                if new_name and new_name != p and new_name not in settings:
                    settings[new_name] = settings.pop(p)
                    save_settings(settings)
                    df.loc[df["프로젝트"] == p, "프로젝트"] = new_name
                    save_data(df)
                    st.success(f"'{p}' → '{new_name}'")
                    st.rerun()
        st.markdown("---")
        st.markdown("#### ➕ 새 프로젝트 추가")
        cn1, cn2 = st.columns([4, 1])
        new_p = cn1.text_input("프로젝트 이름", key="new_proj_name")
        if cn2.button("추가", type="primary", use_container_width=True):
            if new_p and new_p not in settings:
                settings[new_p] = {
                    "activity_types": ["회의 진행", "메일/자료 송수신", "일반 업무 (설계/검토 등)", "주간보고"],
                    "categories": {}, "tags": [], "weekly_reports": {}
                }
                save_settings(settings)
                st.success(f"'{new_p}' 프로젝트가 추가되었습니다.")
                st.rerun()

    # ---------- 분류·태그·업무유형 ----------
    with tab2:
        st.markdown(f"#### 🛠️ [{selected_project}] 분류 · 태그 · 업무유형")
        st.caption("표의 빈 칸을 직접 편집·행 추가·삭제할 수 있습니다.")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**① 업무유형**")
            act_df = pd.DataFrame({"업무유형": proj_act_types})
            new_act = st.data_editor(act_df, num_rows="dynamic", key="act_editor", use_container_width=True)
            if st.button("💾 업무유형 저장", key="save_act"):
                settings[selected_project]["activity_types"] = new_act["업무유형"].dropna().astype(str).str.strip().tolist()
                # 주간보고 유지
                if "주간보고" not in settings[selected_project]["activity_types"]:
                    settings[selected_project]["activity_types"].append("주간보고")
                save_settings(settings)
                st.success("저장되었습니다.")
                st.rerun()

        with col_b:
            st.markdown("**② 태그**")
            tag_df = pd.DataFrame({"태그": proj_tags})
            new_tag = st.data_editor(tag_df, num_rows="dynamic", key="tag_editor", use_container_width=True)
            if st.button("💾 태그 저장", key="save_tag"):
                settings[selected_project]["tags"] = new_tag["태그"].dropna().astype(str).str.strip().tolist()
                save_settings(settings)
                st.success("저장되었습니다.")
                st.rerun()

        st.markdown("---")
        st.markdown("**③ 분류 체계 (대분류 → 중분류)**")
        cat_list = []
        for m_cat, subs in proj_categories.items():
            if not subs:
                cat_list.append({"대분류": m_cat, "중분류": ""})
            for s in subs:
                cat_list.append({"대분류": m_cat, "중분류": s})
        cat_df = pd.DataFrame(cat_list) if cat_list else pd.DataFrame(columns=["대분류", "중분류"])
        new_cat = st.data_editor(cat_df, num_rows="dynamic", key="cat_editor", use_container_width=True)
        if st.button("💾 분류 체계 저장", key="save_cat", type="primary"):
            new_cats = {}
            for _, row in new_cat.iterrows():
                m = str(row["대분류"]).strip() if pd.notna(row["대분류"]) else ""
                s = str(row["중분류"]).strip() if pd.notna(row["중분류"]) else ""
                if not m: continue
                new_cats.setdefault(m, [])
                if s and s not in new_cats[m]:
                    new_cats[m].append(s)
            settings[selected_project]["categories"] = new_cats
            save_settings(settings)
            st.success("저장되었습니다.")
            st.rerun()

    # ---------- Gmail 설정 ----------
    with tab3:
        g = settings.get("gmail_settings", {})
        st.markdown("#### Gmail 연동 설정")
        c1, c2 = st.columns(2)
        g_email = c1.text_input("Gmail 주소", value=g.get("email", ""), key="admin_gmail_email")
        g_pw    = c2.text_input("앱 비밀번호", value=g.get("app_password", ""), type="password", key="admin_gmail_pw")
        g_tgt   = st.text_input("고정 발신자 필터 (쉼표 구분)", value=g.get("target_sender", ""), key="admin_gmail_target")
        if st.button("💾 Gmail 설정 저장", type="primary"):
            settings["gmail_settings"] = {
                "email": g_email.strip(),
                "app_password": g_pw.strip().replace(" ", ""),
                "target_sender": g_tgt.strip(),
            }
            save_settings(settings)
            st.success("Gmail 설정이 저장되었습니다.")

        st.markdown("---")
        st.markdown("##### 📘 앱 비밀번호 발급 방법")
        st.markdown("""
1. [Google 계정 → 보안](https://myaccount.google.com/security)에서 **2단계 인증**을 켭니다.
2. [앱 비밀번호](https://myaccount.google.com/apppasswords) 페이지에서 발급받습니다.
3. 발급된 16자리를 이곳에 붙여넣으세요 (공백 무시).
""")

    # ---------- AI 자동화 ----------
    with tab_ai:
        ai_cfg = settings.get("ai", {})
        st.markdown("#### 🤖 AI 자동화 설정")
        st.caption("API 키만 넣으면 자동분류·요약·주간보고 작성이 즉시 활성화됩니다.")

        ai_enabled = st.toggle("AI 기능 활성화", value=bool(ai_cfg.get("enabled")))
        ai_provider = st.radio(
            "AI 공급자",
            ["openai", "gemini", "anthropic"],
            index=["openai", "gemini", "anthropic"].index(ai_cfg.get("provider", "openai")),
            horizontal=True,
            format_func=lambda x: {
                "openai": "OpenAI (ChatGPT)",
                "gemini": "Google Gemini",
                "anthropic": "Anthropic Claude",
            }[x],
        )

        # 2026-09 현재 신규 발급 키에서 실제 호출 가능한 모델
        model_defaults = {
            "openai":    ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
            "gemini":    ["gemini-3.5-flash", "gemini-3.5-flash-lite",
                          "gemini-flash-latest", "gemini-flash-lite-latest", "gemini-pro-latest",
                          "gemini-3.6-flash"],
            "anthropic": ["claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022", "claude-sonnet-4-20250514"],
        }
        cur_model = ai_cfg.get("model", model_defaults[ai_provider][0])
        model_opts = model_defaults[ai_provider]
        if cur_model not in model_opts:
            model_opts = [cur_model] + model_opts
        ai_model = st.selectbox("모델", model_opts, index=model_opts.index(cur_model) if cur_model in model_opts else 0)
        ai_model = st.text_input("모델명 (직접 입력 가능)", value=ai_model)

        ai_key = st.text_input("API 키", value=ai_cfg.get("api_key", ""), type="password")

        st.markdown("##### 자동 실행 옵션")
        opt_c1, opt_c2 = st.columns(2)
        auto_email = opt_c1.checkbox("메일 불러올 때 자동으로 분류/요약 실행",
                                     value=bool(ai_cfg.get("auto_classify_on_email", True)))
        auto_tags  = opt_c2.checkbox("빠른 등록 시 AI 태그 자동 추천",
                                     value=bool(ai_cfg.get("auto_suggest_tags", True)))

        b1, b2 = st.columns(2)
        with b1:
            if st.button("💾 AI 설정 저장", type="primary", use_container_width=True):
                clean_model = ai_model.strip()
                # Gemini는 models/ 접두어 자동 제거
                if ai_provider == "gemini" and clean_model.startswith("models/"):
                    clean_model = clean_model[len("models/"):]
                settings["ai"] = {
                    "enabled": ai_enabled,
                    "provider": ai_provider,
                    "api_key": ai_key.strip(),
                    "model": clean_model,
                    "auto_classify_on_email": auto_email,
                    "auto_suggest_tags": auto_tags,
                }
                save_settings(settings)
                st.success("AI 설정 저장 완료")
                st.rerun()
        with b2:
            if st.button("🧪 연결 테스트", use_container_width=True,
                         disabled=not ai_key.strip()):
                # 임시 설정으로 호출
                tmp = {"ai": {
                    "enabled": True, "provider": ai_provider,
                    "api_key": ai_key.strip(), "model": ai_model.strip(),
                }}
                try:
                    with st.spinner("호출 중..."):
                        resp = ai_call(tmp, "You are a test bot.", "한 줄로 '안녕하세요' 라고만 답하세요.", max_tokens=50)
                    st.success(f"✅ 응답: {resp[:120]}")
                except Exception as ex:
                    st.error(f"❌ 실패: {ex}")

        st.markdown("---")
        st.markdown("### 🔑 API 키 발급 안내")

        with st.expander("① OpenAI (ChatGPT / GPT-4o) 키 발급", expanded=(ai_provider == "openai")):
            st.markdown("""
1. https://platform.openai.com/api-keys 접속 (로그인 필요)
2. **`+ Create new secret key`** 클릭 → 이름 입력 → 생성
3. `sk-...` 로 시작하는 키를 복사해 이곳에 붙여넣기
4. 결제수단 등록: https://platform.openai.com/settings/organization/billing/overview
   - 소액(5$) 선불 충전 가능
   - **모델 추천**: `gpt-4o-mini` (분류/요약에 충분, 매우 저렴 · 100만 토큰당 $0.15)
""")

        with st.expander("② Google Gemini 키 발급 (무료 티어 있음)", expanded=(ai_provider == "gemini")):
            st.markdown("""
1. https://aistudio.google.com/app/apikey 접속 (Google 로그인)
2. **`Create API key`** 클릭 → 신규/기존 프로젝트에서 생성
3. 발급된 키를 복사해서 위 **API 키** 필드에 붙여넣기
   - 신형 계정: `AQ.` 로 시작 (Authentication Key)
   - 구형 계정: `AIza...` 로 시작
   - 이 앱은 **두 형식 모두 자동 지원** (`x-goog-api-key` 헤더 방식)합니다.

**✅ 2026-09 현재 신규 발급 키로 실제 호출되는 모델 (실측)**
- **`gemini-3.5-flash`** — 무료 티어 안정, 기본값 · **추천**
- `gemini-3.5-flash-lite` — 더 빠름/저렴
- `gemini-flash-latest` — 항상 최신 flash 별칭 (가끔 timeout)
- `gemini-3.6-flash` — 최신, 종종 503 UNAVAILABLE

**⚠️ 404: Not Found 가 나오는 모델 (신규 키로는 막힘 · 넣지 마세요)**
- `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash` — 완전 종료
- `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-lite` — 신규 계정 차단, 기존 사용자만 유지

**주의사항**
- 모델명에 `models/` 접두어를 붙이지 마세요 (저장 시 자동 제거되지만, `gemini-3.5-flash` 처럼만 입력).
- 429/503이 뜨면 무료 티어 쿼터 초과 또는 순간 과부하 → 잠시 후 재시도.
""")

        with st.expander("③ Anthropic Claude 키 발급", expanded=(ai_provider == "anthropic")):
            st.markdown("""
1. https://console.anthropic.com/settings/keys 접속
2. **`+ Create Key`** 클릭 → 이름 입력 → 생성
3. `sk-ant-...` 로 시작하는 키 복사
4. 결제수단 등록: https://console.anthropic.com/settings/billing (최소 $5 선불)
5. **모델 추천**: `claude-3-5-haiku-20241022` (경제적), 품질 우선 시 `claude-3-5-sonnet-20241022`
""")

        st.markdown("### 🎯 AI가 실제로 하는 일 (현재 구현됨)")
        st.markdown("""
| 기능 | 위치 | 동작 |
|---|---|---|
| **자동 분류** | 사이드바 빠른등록 → `🤖 AI 자동 분류` | 제목/내용을 분석해 업무유형·대분류·중분류·태그·우선순위·개선된 제목까지 자동 세팅 |
| **메일 일괄 분석** | 이메일 연동함 → `🤖 전체 AI 자동 분석` | 불러온 모든 메일에 분류·요약·마감일·긴급도를 한번에 매기고, 확인 후 [등록]만 누르면 됩니다 |
| **메일 단건 분석** | 이메일 카드 → `🤖 이 메일만 AI 분석` | 한 건씩 처리 |
| **AI 주간보고 작성** | 대시보드 주간보고 → `🤖 AI 보고서 작성` | 이번 주 업무 데이터를 바탕으로 문장형 보고서 초안 작성 (성과/완료/진행/이슈/다음주계획/협력사 이슈) |
| **업무 내용 다듬기** | 상세 편집 → `🤖 AI 내용 다듬기` | 지저분한 메모를 결정사항/액션아이템/참고사항 구조로 정리 |
""")

        st.markdown("### 💰 예상 비용 (실측 기준)")
        st.markdown("""
- **하루 20건 등록 + 메일 10건 분류 + 주간보고 1회** 기준:
  - OpenAI `gpt-4o-mini`: **월 $0.5~1** (매우 저렴)
  - Gemini `1.5-flash`: **무료** (일 1,500회 이내)
  - Anthropic `Claude 3.5 Haiku`: **월 $1~2**
- 처음에는 **Gemini 무료 티어**로 시작해보시길 추천합니다.
""")

    # ---------- UI/테마 ----------
    with tab4:
        st.markdown("#### 화면 설정")
        ui = settings.get("ui", {})
        week_start = st.radio(
            "주 시작 요일",
            ["월요일", "일요일"],
            index=["월요일", "일요일"].index(ui.get("week_start", "월요일")),
            horizontal=True
        )
        if st.button("💾 UI 설정 저장"):
            settings["ui"] = {"week_start": week_start, "theme": ui.get("theme", "라이트")}
            save_settings(settings)
            st.success("저장되었습니다. 새로고침 후 반영됩니다.")
            st.rerun()

    # ---------- 백업·복원 ----------
    with tab5:
        st.markdown("#### 💾 데이터 백업 · 복원")
        st.info("정기적으로 백업 파일을 다운로드해 두시길 권장합니다.")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("**① 업무 데이터 (CSV)**")
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "rb") as f:
                    st.download_button(
                        "⬇️ 업무 CSV 다운로드", data=f,
                        file_name=f"MUSV_업무데이터_{date.today()}.csv",
                        mime="text/csv", use_container_width=True
                    )
            st.markdown("**② 설정 파일 (JSON)**")
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "rb") as f:
                    st.download_button(
                        "⬇️ 설정 JSON 다운로드", data=f,
                        file_name=f"MUSV_설정_{date.today()}.json",
                        mime="application/json", use_container_width=True
                    )
        with col_b2:
            st.markdown("**업무 CSV 복원**")
            up_csv = st.file_uploader("CSV 업로드", type=["csv"], key="up_csv", label_visibility="collapsed")
            if up_csv is not None and st.button("복원 실행 (CSV)", use_container_width=True, type="primary"):
                try:
                    _df = pd.read_csv(up_csv)
                    _df.to_csv(DATA_FILE, index=False)
                    st.success("업무 데이터가 복원되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"실패: {e}")

            st.markdown("**설정 JSON 복원**")
            up_json = st.file_uploader("JSON 업로드", type=["json"], key="up_json", label_visibility="collapsed")
            if up_json is not None and st.button("복원 실행 (JSON)", use_container_width=True):
                try:
                    obj = json.load(up_json)
                    save_settings(obj)
                    st.success("설정이 복원되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"실패: {e}")

        st.markdown("---")
        st.markdown("#### ⚠️ 위험 구역")
        with st.expander("🗑️ 프로젝트 데이터 초기화"):
            st.warning(f"현재 프로젝트 **{selected_project}** 의 모든 업무를 삭제합니다. 되돌릴 수 없습니다.")
            confirm = st.text_input("확인을 위해 프로젝트명을 정확히 입력하세요", key="danger_confirm")
            if st.button("🗑️ 프로젝트 업무 전체 삭제", type="secondary"):
                if confirm == selected_project:
                    df = df[df["프로젝트"] != selected_project].reset_index(drop=True)
                    save_data(df)
                    st.success("삭제 완료")
                    st.rerun()
                else:
                    st.error("프로젝트명이 일치하지 않습니다.")


# =====================================================
# 17. 푸터
# =====================================================
st.markdown(
    "<div style='text-align:center;color:#9ca3af;font-size:12px;margin-top:32px;'>"
    "🚢 MUSV Task Dashboard · 동화엔텍 전기제어설계팀 · Built by Genspark AI"
    "</div>",
    unsafe_allow_html=True
)
