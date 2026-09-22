# -*- coding: utf-8 -*-
"""
🚢 통합 업무 관리 대시보드 (v3)
=====================================================
- 로그인(다중 사용자, 서버 저장)
- GitHub 영속 저장 (Streamlit 재시작·초기화에도 데이터 보존)
- 아이콘 홈 화면
- Gmail 스타일 메일함 (리스트/상세/폴더/번역/액션플랜)
- 캘린더·주간보고·업무일지·AI 자동화

Author: Genspark AI (for 대마왕)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import os, json, imaplib, re, io, uuid, hashlib, base64, secrets
import urllib.request, urllib.error, urllib.parse
import email as email_lib
from email.header import decode_header

# =====================================================
# 0. 페이지 · 전역 CSS
# =====================================================
st.set_page_config(page_title="MUSV 통합 업무 대시보드", page_icon="🚢",
                   layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
html,body,[class*="css"]{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Malgun Gothic","Apple SD Gothic Neo","Noto Sans KR",Roboto,sans-serif;}
.block-container{padding-top:1rem;padding-bottom:2.5rem;}
.hero{background:linear-gradient(120deg,#0f2b5b 0%,#1e40af 50%,#0891b2 100%);color:#fff;padding:16px 22px;border-radius:14px;margin-bottom:14px;box-shadow:0 6px 20px rgba(15,43,91,0.18);}
.hero h1{color:#fff;margin:0;font-size:1.45rem}.hero p{color:#dbeafe;margin:4px 0 0 0;font-size:.85rem}

/* 홈 아이콘 그리드 */
.home-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:14px 0}
@media (max-width:900px){.home-grid{grid-template-columns:repeat(2,1fr)}}
.home-tile{background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:26px 20px;text-align:center;transition:all .15s;cursor:pointer;text-decoration:none!important;color:#111827!important;display:block}
.home-tile:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.08);border-color:#3b82f6}
.home-tile .ico{font-size:44px;display:block;margin-bottom:10px}
.home-tile .ttl{font-size:16px;font-weight:700;margin-bottom:4px}
.home-tile .desc{font-size:12px;color:#6b7280}
.home-tile.warn{background:linear-gradient(135deg,#fef3c7,#fde68a);border-color:#f59e0b}
.home-tile.hot{background:linear-gradient(135deg,#fee2e2,#fecaca);border-color:#ef4444}

/* KPI */
.kpi{border-radius:12px;padding:14px 16px;background:#fff;border:1px solid #e5e7eb}
.kpi .label{color:#6b7280;font-size:12px}.kpi .value{font-size:24px;font-weight:700;color:#111827}
.kpi.warn{border-left:4px solid #ef4444}.kpi.good{border-left:4px solid #10b981}
.kpi.info{border-left:4px solid #3b82f6}.kpi.hold{border-left:4px solid #f59e0b}

/* 캘린더 */
.cal-wrap{border-radius:12px;overflow:hidden;border:1px solid #e5e7eb}
table.cal{width:100%;border-collapse:collapse;font-size:12.5px}
table.cal th{background:#f8fafc;color:#374151;font-weight:600;padding:10px 6px;border-bottom:1px solid #e5e7eb;text-align:center}
table.cal th.sun{color:#ef4444}table.cal th.sat{color:#2563eb}
table.cal td{border-top:1px solid #f1f5f9;border-right:1px solid #f1f5f9;vertical-align:top;height:118px;padding:5px;background:#fff}
table.cal td.today{background:#fffbeb}table.cal td.other{background:#fafafa}
table.cal td .day{font-weight:600;font-size:12px;margin-bottom:4px;display:flex;justify-content:space-between}
table.cal td.today .day .num{background:#f59e0b;color:#fff;border-radius:999px;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:11px}
table.cal td .day .sun{color:#ef4444}table.cal td .day .sat{color:#2563eb}
.chip{display:block;border-radius:4px;padding:2px 6px;margin-bottom:2px;font-size:11px;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-decoration:none!important;cursor:pointer;border-left:3px solid transparent}
.chip.done{opacity:.55;text-decoration:line-through!important}

/* 메일 리스트 (Gmail 스타일) */
.mailrow{display:grid;grid-template-columns:24px 160px 140px 1fr 90px;gap:10px;padding:10px 12px;border-bottom:1px solid #f1f5f9;background:#fff;cursor:pointer;align-items:center;text-decoration:none!important;color:#111827!important}
.mailrow:hover{background:#f9fafb}
.mailrow.unread{background:#ffffff;font-weight:600}
.mailrow.read{background:#fafafa;color:#4b5563!important}
.mailrow .sender{color:#111827;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mailrow .subject{font-size:13.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mailrow .snippet{color:#6b7280;font-weight:400;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mailrow .date{font-size:11px;color:#6b7280;text-align:right}
.folder-badge{display:inline-block;padding:1px 7px;border-radius:10px;font-size:10.5px;background:#eef2ff;color:#3730a3;border:1px solid #e0e7ff;margin-right:6px}
.tag-badge{display:inline-block;padding:2px 8px;margin:2px 3px 2px 0;border-radius:999px;font-size:11px;background:#eef2ff;color:#3730a3;border:1px solid #e0e7ff}

.alert{background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:10px 14px;border-radius:10px;margin:6px 0 12px 0;font-size:13px}
.login-card{max-width:420px;margin:60px auto;padding:32px;background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.06);border:1px solid #e5e7eb}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# =====================================================
# 1. 상수
# =====================================================
STATUS_LIST = ["진행중", "미정", "보류", "완료", "지연"]
PRIORITY_LIST = ["🟢 낮음", "🔵 보통", "🟠 높음", "🔴 긴급"]
TYPE_COLORS = {
    "회의 진행":            {"bg":"#3b82f6","fg":"#fff","bg_done":"#dbeafe","fg_done":"#1e40af"},
    "메일/자료 송수신":     {"bg":"#10b981","fg":"#fff","bg_done":"#d1fae5","fg_done":"#065f46"},
    "일반 업무 (설계/검토 등)":{"bg":"#8b5cf6","fg":"#fff","bg_done":"#ede9fe","fg_done":"#5b21b6"},
    "주간보고":             {"bg":"#0f2b5b","fg":"#fff","bg_done":"#c7d2fe","fg_done":"#312e81"},
}
FALLBACK_PALETTE = [
    {"bg":"#f59e0b","fg":"#fff","bg_done":"#fef3c7","fg_done":"#92400e"},
    {"bg":"#ec4899","fg":"#fff","bg_done":"#fce7f3","fg_done":"#9d174d"},
    {"bg":"#06b6d4","fg":"#fff","bg_done":"#cffafe","fg_done":"#155e75"},
]
DELAY_COLOR = {"bg":"#ef4444","fg":"#fff"}
HOLD_COLOR  = {"bg":"#f59e0b","fg":"#111827"}

TASK_COLS = ["ID","프로젝트","업무유형","대분류","중분류","우선순위","시작일","목표일",
             "실제완료일","장소","관련자(참석자/송수신자)","제목","내용","태그","상태",
             "드라이브_링크","연관업무ID","생성일시","수정일시"]

MAIL_COLS = ["ID","user","msg_uid","received_at","sender","sender_name","subject",
             "body","ai_summary","ai_actions","ai_translated","folder","tags",
             "read","registered_task_id","fetched_at"]

DEFAULT_USER_SETTINGS = {
    "activity_types": ["회의 진행","메일/자료 송수신","일반 업무 (설계/검토 등)","주간보고"],
    "categories": {
        "1. 개요": ["1-1. 일정","1-2. 회의"],
        "2. BCC":  ["2-1. BCC","2-2. 사급자재","2-3. ECS PC","2-4. 모니터"],
        "3. DAU":  ["3-1. DAU PANEL","3-2. DAU & HISTORIAN","3-3. UPS","3-4. ECS PLC 프로그램"],
        "4. KR":   ["4-1. 제출자료"],
        "5. 프로그램": ["5-1. 컨셉 다이어그램","5-2. ECS PLC","5-3. ECS PC","5-4. ECS HMI",
                    "5-5. 임무콘솔","5-6. DAU & HISTORIAN","5-7. ETC."]
    },
    "tags": ["DAU","BCC","사급자재","UPS","ECS PC","ECS PLC","ECS 모니터","DAU PANEL",
             "히스토리안서버","극동선박설계","유일조선소","한화시스템","한화엔진",
             "한화오션","KR선급","MS산전","주간보고"],
    "mail_folders": ["받은편지함","중요","한화시스템","한화엔진","한화오션","KR선급","극동선박설계","MS산전","보관"],
    "week_start": "월요일",
    "current_project": "MUSV-2",
    "projects": ["MUSV-2"],
    # 개인화된 자격 증명 — 로그인 후 자동 로드
    "gmail_email": "",
    "gmail_app_password": "",
    "gmail_target_sender": "hblee@dh.co.kr, 이헌범",
    "ai_enabled": False,
    "ai_provider": "gemini",
    "ai_api_key": "",
    "ai_model": "gemini-3.5-flash",
    "ai_auto_classify_mail": True,
    "ai_auto_translate": True,
    "ai_auto_action_plan": True,
}


# =====================================================
# 2. GitHub 영속 저장 계층
# =====================================================
def gh_headers():
    tok = st.secrets.get("GITHUB_TOKEN") if hasattr(st, "secrets") else None
    tok = tok or os.environ.get("GITHUB_TOKEN", "")
    if not tok:
        return None
    return {
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "musv-dashboard",
    }

def gh_conf():
    """Returns (owner, repo, branch) from st.secrets or env."""
    def _get(k, d=""):
        v = None
        if hasattr(st, "secrets"):
            v = st.secrets.get(k)
        return v or os.environ.get(k, d)
    return _get("GITHUB_OWNER"), _get("GITHUB_REPO"), _get("GITHUB_BRANCH", "main")

def gh_available():
    owner, repo, _ = gh_conf()
    return bool(gh_headers() and owner and repo)

def gh_read(path):
    """Return (text, sha) or (None, None)."""
    owner, repo, branch = gh_conf()
    h = gh_headers()
    if not (h and owner and repo): return None, None
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}?ref={branch}"
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=15) as r:
            obj = json.loads(r.read().decode("utf-8"))
        content = base64.b64decode(obj["content"]).decode("utf-8")
        return content, obj.get("sha")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None
        raise

def gh_write(path, text, message="update"):
    """Create or update a file. Handles 409 by refetching sha."""
    owner, repo, branch = gh_conf()
    h = gh_headers()
    if not (h and owner and repo): return False
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}"
    _, sha = gh_read(path)
    payload = {
        "message": f"{message} · {datetime.now().isoformat()}",
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha: payload["sha"] = sha
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={**h, "Content-Type": "application/json"}, method="PUT",
    )
    try:
        urllib.request.urlopen(req, timeout=20).read()
        return True
    except urllib.error.HTTPError as e:
        # 409 SHA mismatch → refetch and retry once
        if e.code in (409, 422):
            _, sha2 = gh_read(path)
            if sha2:
                payload["sha"] = sha2
                req = urllib.request.Request(
                    url, data=json.dumps(payload).encode("utf-8"),
                    headers={**h, "Content-Type": "application/json"}, method="PUT",
                )
                urllib.request.urlopen(req, timeout=20).read()
                return True
        raise


DATA_ROOT = "data"

def _paths(username):
    return {
        "tasks":  f"{DATA_ROOT}/{username}/tasks.csv",
        "mails":  f"{DATA_ROOT}/{username}/mails.csv",
        "settings": f"{DATA_ROOT}/{username}/settings.json",
        "users": f"{DATA_ROOT}/users.json",
    }

def load_users():
    """users.json = {username: {salt, hash, created_at, display_name}}"""
    if gh_available():
        text, _ = gh_read(_paths("_")["users"])
        if text:
            try: return json.loads(text)
            except: return {}
        return {}
    else:
        if os.path.exists("users.json"):
            return json.load(open("users.json","r",encoding="utf-8"))
        return {}

def save_users(users):
    text = json.dumps(users, ensure_ascii=False, indent=2)
    if gh_available():
        gh_write(_paths("_")["users"], text, "update users")
    else:
        open("users.json","w",encoding="utf-8").write(text)

def hash_password(pw, salt):
    return hashlib.sha256((salt + pw).encode("utf-8")).hexdigest()

def generate_random_password(length=12):
    """대문자·소문자·숫자·특수문자 조합 자동 생성"""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#$%&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def load_user_data(username):
    """Load tasks, mails, settings for a user."""
    p = _paths(username)
    # tasks
    if gh_available():
        t, _ = gh_read(p["tasks"])
        m, _ = gh_read(p["mails"])
        s, _ = gh_read(p["settings"])
    else:
        t = open(f"tasks_{username}.csv","r",encoding="utf-8").read() if os.path.exists(f"tasks_{username}.csv") else None
        m = open(f"mails_{username}.csv","r",encoding="utf-8").read() if os.path.exists(f"mails_{username}.csv") else None
        s = open(f"settings_{username}.json","r",encoding="utf-8").read() if os.path.exists(f"settings_{username}.json") else None

    if t:
        try: df = pd.read_csv(io.StringIO(t))
        except: df = pd.DataFrame(columns=TASK_COLS)
    else:
        df = pd.DataFrame(columns=TASK_COLS)
    # 컬럼 보정
    rename_map = {"내용(주제)":"제목","회의록_및_비고":"내용"}
    df.rename(columns={k:v for k,v in rename_map.items() if k in df.columns}, inplace=True)
    for c in TASK_COLS:
        if c not in df.columns: df[c] = ""
    if df["ID"].isna().any() or (df["ID"]=="").any():
        df.loc[df["ID"].isna() | (df["ID"]==""), "ID"] = [str(uuid.uuid4())[:8] for _ in range((df["ID"].isna()|(df["ID"]=="")).sum())]
    df["우선순위"] = df["우선순위"].fillna("🔵 보통").replace("","🔵 보통")
    for c in ("시작일","목표일","실제완료일","생성일시","수정일시"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    df = df[TASK_COLS]

    if m:
        try: mdf = pd.read_csv(io.StringIO(m))
        except: mdf = pd.DataFrame(columns=MAIL_COLS)
    else:
        mdf = pd.DataFrame(columns=MAIL_COLS)
    for c in MAIL_COLS:
        if c not in mdf.columns: mdf[c] = ""
    mdf["received_at"] = pd.to_datetime(mdf["received_at"], errors="coerce")
    mdf["fetched_at"]  = pd.to_datetime(mdf["fetched_at"], errors="coerce")
    mdf["read"] = mdf["read"].fillna(False).astype(bool)
    mdf = mdf[MAIL_COLS]

    settings = json.loads(json.dumps(DEFAULT_USER_SETTINGS))
    if s:
        try:
            loaded = json.loads(s)
            settings.update(loaded)
        except: pass
    # 필수 키 보정
    for k, v in DEFAULT_USER_SETTINGS.items():
        settings.setdefault(k, v)
    if isinstance(settings.get("categories"), dict) is False:
        settings["categories"] = DEFAULT_USER_SETTINGS["categories"]
    return df, mdf, settings

def save_tasks(username, df):
    csv = df.to_csv(index=False)
    p = _paths(username)
    if gh_available():
        gh_write(p["tasks"], csv, f"{username}: tasks update")
    else:
        open(f"tasks_{username}.csv","w",encoding="utf-8").write(csv)

def save_mails(username, mdf):
    csv = mdf.to_csv(index=False)
    p = _paths(username)
    if gh_available():
        gh_write(p["mails"], csv, f"{username}: mails update")
    else:
        open(f"mails_{username}.csv","w",encoding="utf-8").write(csv)

def save_user_settings(username, settings):
    p = _paths(username)
    text = json.dumps(settings, ensure_ascii=False, indent=2)
    if gh_available():
        gh_write(p["settings"], text, f"{username}: settings update")
    else:
        open(f"settings_{username}.json","w",encoding="utf-8").write(text)

def new_id():
    return str(uuid.uuid4())[:8]


# =====================================================
# 3. AI 계층 (OpenAI · Gemini · Anthropic)
# =====================================================
def ai_available(settings):
    return bool(settings.get("ai_enabled") and settings.get("ai_api_key") and settings.get("ai_provider"))

def _ai_openai(key, model, sys_p, user_p, temp=0.3, mx=1500):
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps({"model": model, "messages":[
            {"role":"system","content":sys_p},{"role":"user","content":user_p}],
            "temperature":temp, "max_tokens":mx}).encode("utf-8"),
        headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        obj = json.loads(r.read().decode("utf-8"))
    return obj["choices"][0]["message"]["content"]

def _ai_gemini(key, model, sys_p, user_p, temp=0.3, mx=1500):
    model = (model or "gemini-3.5-flash").strip()
    if model.startswith("models/"): model = model[len("models/"):]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {"systemInstruction":{"parts":[{"text":sys_p}]},
            "contents":[{"role":"user","parts":[{"text":user_p}]}],
            "generationConfig":{"temperature":temp,"maxOutputTokens":mx}}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type":"application/json","x-goog-api-key":key}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            obj = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Gemini HTTP {e.code}: {e.read().decode('utf-8','ignore')[:400]}")
    try:
        return obj["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return json.dumps(obj, ensure_ascii=False)[:800]

def _ai_anthropic(key, model, sys_p, user_p, temp=0.3, mx=1500):
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
        data=json.dumps({"model":model,"max_tokens":mx,"temperature":temp,
            "system":sys_p,"messages":[{"role":"user","content":user_p}]}).encode("utf-8"),
        headers={"x-api-key":key,"anthropic-version":"2023-06-01","Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        obj = json.loads(r.read().decode("utf-8"))
    return obj["content"][0]["text"]

def ai_call(settings, sys_p, user_p, temp=0.3, mx=1500):
    p = settings.get("ai_provider","gemini"); k = settings.get("ai_api_key",""); m = settings.get("ai_model","")
    if not k: raise RuntimeError("AI API 키가 없습니다.")
    if p == "openai":    return _ai_openai(k, m or "gpt-4o-mini", sys_p, user_p, temp, mx)
    if p == "gemini":    return _ai_gemini(k, m or "gemini-3.5-flash", sys_p, user_p, temp, mx)
    if p == "anthropic": return _ai_anthropic(k, m or "claude-3-5-haiku-20241022", sys_p, user_p, temp, mx)
    raise RuntimeError(f"알 수 없는 provider: {p}")

def ai_json(settings, sys_p, user_p, temp=0.2, mx=1500):
    raw = ai_call(settings, sys_p, user_p, temp, mx)
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", raw, re.DOTALL)
    if m: raw = m.group(1)
    else:
        m2 = re.search(r"(\{.*\}|\[.*\])", raw, re.DOTALL)
        if m2: raw = m2.group(1)
    try: return json.loads(raw)
    except: return {"_raw": raw, "_error": "JSON 파싱 실패"}

def ai_classify_task(settings, title, body, act_types, cats, tags):
    sys_p = ("당신은 조선/해양 방산(MUSV, 무인수상정) 업무 분류 도우미입니다. "
             "동화엔텍 전기제어설계팀 협력사(한화시스템/한화엔진/한화오션/유일조선소/극동선박설계/KR선급/MS산전) "
             "관련 업무를 정확히 분류하세요. 반드시 JSON만 응답.")
    user_p = f"""[제목]
{title}
[내용]
{body[:3000]}
[허용 업무유형]
{json.dumps(act_types, ensure_ascii=False)}
[허용 대분류→중분류]
{json.dumps(cats, ensure_ascii=False)}
[허용 태그]
{json.dumps(tags, ensure_ascii=False)}

JSON:
{{
  "업무유형":"위 목록 중 하나",
  "대분류":"위 매핑의 대분류",
  "중분류":"선택한 대분류의 하위 중분류",
  "태그":["관련 태그 1~5개, 위 목록에서만"],
  "우선순위":"🟢 낮음|🔵 보통|🟠 높음|🔴 긴급 중 하나",
  "제안제목":"50자 이내 요약 제목",
  "요약":"3~5줄 정리"
}}"""
    return ai_json(settings, sys_p, user_p)

def ai_action_plan(settings, subject, sender, body):
    """메일 → 액션플랜 JSON (뭐를 언제까지 어떻게)."""
    sys_p = ("이메일을 읽고 실무자가 취해야 할 액션플랜을 정리하는 도우미입니다. "
             "반드시 JSON으로만 응답하세요.")
    user_p = f"""[제목] {subject}
[보낸이] {sender}
[본문]
{body[:4000]}

JSON:
{{
  "요약":"3줄 이내 핵심",
  "긴급도":"🟢 낮음|🔵 보통|🟠 높음|🔴 긴급",
  "마감일자":"YYYY-MM-DD 또는 빈 문자열",
  "액션플랜":[
    {{"무엇":"할 일","언제까지":"YYYY-MM-DD 또는 미정","어떻게":"구체 방법","담당":"본인|타사|미정"}}
  ],
  "핵심결정사항":["결정된 사항"],
  "확인필요":["확인/검토가 필요한 것"]
}}"""
    return ai_json(settings, sys_p, user_p, temp=0.2, mx=1800)

def ai_translate(settings, text, target="ko"):
    """자동 번역 (영→한 기본, 이미 한국어면 원문 그대로)."""
    if not text.strip(): return ""
    # 한글 비율 검사
    hangul = len(re.findall(r"[가-힣]", text))
    total = len(re.findall(r"\S", text)) or 1
    if hangul / total > 0.15:  # 이미 한국어 우세
        return text
    sys_p = "당신은 조선/방산 도메인의 이메일을 자연스러운 한국어로 번역하는 전문 번역가입니다. 원문의 뉘앙스와 전문용어를 유지하세요."
    user_p = f"다음 이메일 본문을 한국어로 자연스럽게 번역하세요. 번역문만 출력 (설명 금지):\n\n{text[:4000]}"
    return ai_call(settings, sys_p, user_p, temp=0.2, mx=2500)

def ai_weekly_report(settings, project, week_label, summary):
    sys_p = "조선/방산 PM 주간보고 어시스턴트. 건조하고 명확한 한국어로, 사실·숫자 위주."
    user_p = f"""{project} {week_label} 주간보고를 마크다운으로:

[업무 데이터]
{summary}

## 📌 이번 주 핵심 성과
## ✅ 완료 업무
## 🏃 진행/예정 업무
## ⚠️ 지연·이슈
## 📅 다음 주 계획
## 🤝 협력사 특이사항
"""
    return ai_call(settings, sys_p, user_p, temp=0.4, mx=2500)


# =====================================================
# 4. Gmail IMAP
# =====================================================
def _decode(s):
    if not s: return ""
    parts = decode_header(s); out=""
    for w,e in parts:
        if isinstance(w,bytes):
            try: out += w.decode(e or "utf-8", errors="ignore")
            except: out += w.decode("utf-8", errors="ignore")
        else: out += str(w)
    return out

def _get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type()=="text/plain" and "attachment" not in str(part.get("Content-Disposition","")):
                try: return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                except: pass
    else:
        try: return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")
        except: pass
    return ""

def _company(addr):
    m = re.search(r"@([a-zA-Z0-9-]+)\.", str(addr))
    return m.group(1) if m else str(addr)

def _sender_name(sender):
    m = re.match(r'^\s*"?([^"<]+?)"?\s*<', sender)
    if m: return m.group(1).strip()
    return sender.split("@")[0]

def fetch_gmail(email_user, app_pw, target, scan=200, limit=25):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, app_pw)
        # All Mail 라벨
        status, folders = mail.list()
        all_mail = "INBOX"
        if status=="OK" and folders:
            for f in folders:
                if b"\\All" in f:
                    parts = f.decode("utf-8","ignore").split(' "/" ')
                    if len(parts)==2: all_mail = parts[1]; break
        try: mail.select(all_mail, readonly=True)
        except: mail.select("INBOX", readonly=True)
        status, messages = mail.search(None, "ALL")
        out=[]
        if status=="OK" and messages[0]:
            ids = messages[0].split()
            targets = [t.strip().lower() for t in target.replace("OR",",").split(",") if t.strip()]
            for msg_id in reversed(ids[-scan:]):
                res, data = mail.fetch(msg_id, "(RFC822)")
                if res!="OK": continue
                msg = email_lib.message_from_bytes(data[0][1])
                sender = _decode(msg.get("From",""))
                if not any(t in sender.lower() for t in targets): continue
                subject = _decode(msg.get("Subject",""))
                date_ = msg.get("Date","")
                try: recv_dt = pd.to_datetime(date_, errors="coerce")
                except: recv_dt = pd.NaT
                body = _get_body(msg)
                out.append({
                    "msg_uid": msg_id.decode() if isinstance(msg_id,bytes) else str(msg_id),
                    "received_at": recv_dt,
                    "sender": sender,
                    "sender_name": _sender_name(sender) or _company(sender),
                    "subject": subject,
                    "body": body.strip(),
                })
                if len(out)>=limit: break
        mail.logout()
        return out
    except Exception as e:
        st.error(f"메일 연동 실패: {e}")
        return []


# =====================================================
# 5. 유틸 (날짜·색상·캘린더)
# =====================================================
def week_range(any_date, start_monday=True):
    d = pd.Timestamp(any_date).normalize()
    if start_monday:
        s = d - pd.Timedelta(days=d.weekday()); return s, s + pd.Timedelta(days=6)
    idx = (d.weekday()+1)%7
    s = d - pd.Timedelta(days=idx); return s, s + pd.Timedelta(days=6)

def type_color(ttype, acts, status):
    if status=="지연": return DELAY_COLOR["bg"], DELAY_COLOR["fg"], False
    if status=="보류": return HOLD_COLOR["bg"], HOLD_COLOR["fg"], False
    done = (status=="완료")
    c = TYPE_COLORS.get(ttype)
    if not c:
        try: c = FALLBACK_PALETTE[acts.index(ttype)%len(FALLBACK_PALETTE)]
        except: c = FALLBACK_PALETTE[0]
    if done: return c["bg_done"], c["fg_done"], True
    return c["bg"], c["fg"], False

def task_active(task, day, today):
    s = task["시작일"]
    if pd.isna(s): return False
    e = task["목표일"]; st_ = task["상태"]
    if pd.notna(e): return s <= day <= e
    if st_ in ("진행중","미정","보류"): return s <= day <= today
    return s == day

def compute_overdue(df):
    today = pd.Timestamp(date.today())
    return df["목표일"].notna() & (df["목표일"] < today) & (~df["상태"].isin(["완료"]))

def render_month(df, base_date, acts, wsm=True):
    base = pd.Timestamp(base_date).normalize()
    if wsm:
        first = base - pd.Timedelta(days=base.weekday())
        headers = ["월","화","수","목","금","토","일"]; weekend={5:"sat",6:"sun"}
    else:
        idx = (base.weekday()+1)%7
        first = base - pd.Timedelta(days=idx)
        headers = ["일","월","화","수","목","금","토"]; weekend={0:"sun",6:"sat"}
    start = first - pd.Timedelta(weeks=2)
    today = pd.Timestamp(date.today())
    h = ['<div class="cal-wrap"><table class="cal"><colgroup><col style="width:5%"/>']
    for _ in range(7): h.append('<col style="width:13.57%"/>')
    h.append("</colgroup><tr><th>주</th>")
    for i,x in enumerate(headers): h.append(f'<th class="{weekend.get(i,"")}">{x}</th>')
    h.append("</tr>")
    curr = start
    for _ in range(6):
        wk = (curr + pd.Timedelta(days=3)).isocalendar()[1]
        h.append(f'<tr><td style="background:#f8fafc;text-align:center;color:#6b7280;font-size:11px;font-weight:600">{wk}W</td>')
        for i in range(7):
            is_today = (curr.date()==today.date()); in_m = (curr.month==base.month)
            cls = "today" if is_today else ("other" if not in_m else "")
            dc = weekend.get(i,"")
            h.append(f'<td class="{cls}"><div class="day"><span class="num {dc}">{curr.day}</span></div>')
            if not df.empty:
                for _,t in df.iterrows():
                    if not task_active(t, curr, today): continue
                    bg,fg,done = type_color(t["업무유형"], acts, t["상태"])
                    dcls = " done" if done else ""
                    title = str(t["제목"]).replace("'","&apos;").replace('"',"&quot;")
                    prio = str(t.get("우선순위","")); mark = "🔴 " if "긴급" in prio else ("🟠 " if "높음" in prio else "")
                    h.append(f'<a class="chip{dcls}" href="?nav=cal&task_id={t["ID"]}" target="_self" '
                             f'style="background:{bg};color:{fg};border-left-color:{bg if not done else fg}" '
                             f'title="[{t["업무유형"]}] {title}">{mark}{title}</a>')
            h.append("</td>")
            curr = curr + pd.Timedelta(days=1)
        h.append("</tr>")
    h.append("</table></div>")
    return "".join(h)


# =====================================================
# 6. 세션 초기화
# =====================================================
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None
if "nav" not in st.session_state:
    st.session_state.nav = "home"
if "cal_base_date" not in st.session_state:
    st.session_state.cal_base_date = date.today()
if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None
if "selected_mail_id" not in st.session_state:
    st.session_state.selected_mail_id = None
if "mail_folder" not in st.session_state:
    st.session_state.mail_folder = "받은편지함"

qp = st.query_params
if qp.get("nav"):
    st.session_state.nav = qp.get("nav")
    if qp.get("task_id"):
        st.session_state.selected_task_id = qp.get("task_id")
    if qp.get("mail_id"):
        st.session_state.selected_mail_id = qp.get("mail_id")
    st.query_params.clear()


# =====================================================
# 7. 로그인 게이트
# =====================================================
def render_login():
    st.markdown('<div class="hero"><h1>🚢 MUSV 업무 대시보드</h1><p>로그인하고 시작하세요 · 데이터는 서버에 안전하게 저장됩니다</p></div>', unsafe_allow_html=True)

    if not gh_available():
        st.warning("⚠️ GitHub 영속 저장이 설정되지 않았습니다. 로컬 파일로만 저장됩니다 (Streamlit 재시작 시 사라질 수 있음). 관리자 안내: README의 'GitHub 저장 설정' 참고.")

    users = load_users()
    tab_login, tab_signup = st.tabs(["🔐 로그인", "📝 회원가입"])

    with tab_login:
        with st.container():
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            u = st.text_input("아이디", key="login_id")
            p = st.text_input("비밀번호", type="password", key="login_pw")
            c1,c2 = st.columns([1,1])
            if c1.button("로그인", type="primary", use_container_width=True):
                if u in users and hash_password(p, users[u]["salt"]) == users[u]["hash"]:
                    st.session_state.auth_user = u
                    st.session_state.nav = "home"
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
            if c2.button("게스트로 둘러보기", use_container_width=True):
                # 데모 계정 자동 생성
                if "guest" not in users:
                    salt = secrets.token_hex(8)
                    users["guest"] = {"salt": salt, "hash": hash_password("guest", salt),
                                       "created_at": datetime.now().isoformat(),
                                       "display_name": "게스트"}
                    save_users(users)
                st.session_state.auth_user = "guest"
                st.session_state.nav = "home"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    with tab_signup:
        with st.container():
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            new_u = st.text_input("아이디 (영문/숫자 4자 이상)", key="sign_id")
            new_display = st.text_input("표시 이름 (닉네임)", key="sign_dn")

            pw_mode = st.radio("비밀번호 방식", ["직접 입력", "자동 발급 (12자리)"], horizontal=True, key="pw_mode")
            if pw_mode == "직접 입력":
                new_p1 = st.text_input("비밀번호", type="password", key="sign_pw1")
                new_p2 = st.text_input("비밀번호 확인", type="password", key="sign_pw2")
            else:
                if "auto_pw" not in st.session_state:
                    st.session_state.auto_pw = generate_random_password(12)
                new_p1 = new_p2 = st.session_state.auto_pw
                st.code(new_p1)
                st.warning("⚠️ 이 비밀번호를 지금 저장하세요. 다시 볼 수 없습니다.")
                if st.button("🔄 다시 발급"):
                    st.session_state.auto_pw = generate_random_password(12)
                    st.rerun()

            if st.button("회원가입", type="primary", use_container_width=True):
                if not re.match(r"^[A-Za-z0-9_]{4,}$", new_u):
                    st.error("아이디는 영문/숫자/언더스코어 4자 이상.")
                elif new_u in users:
                    st.error("이미 사용 중인 아이디입니다.")
                elif new_p1 != new_p2 or len(new_p1) < 6:
                    st.error("비밀번호 확인 실패 (6자 이상).")
                else:
                    salt = secrets.token_hex(8)
                    users[new_u] = {"salt": salt, "hash": hash_password(new_p1, salt),
                                     "created_at": datetime.now().isoformat(),
                                     "display_name": new_display or new_u}
                    save_users(users)
                    st.session_state.auth_user = new_u
                    st.session_state.nav = "home"
                    if "auto_pw" in st.session_state: del st.session_state["auto_pw"]
                    st.success("가입 완료. 자동 로그인됩니다.")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


if st.session_state.auth_user is None:
    render_login()
    st.stop()


# =====================================================
# 8. 로그인 이후 — 사용자 데이터 로드
# =====================================================
USER = st.session_state.auth_user
df, mdf, settings = load_user_data(USER)
users = load_users()
display_name = users.get(USER, {}).get("display_name", USER)

selected_project = settings.get("current_project", "MUSV-2")
if selected_project not in settings.get("projects", []):
    settings["projects"] = list(set(settings.get("projects", []) + [selected_project, "MUSV-2"]))

act_types = settings["activity_types"]
if "주간보고" not in act_types: act_types.append("주간보고")
cats = settings["categories"]
tags = settings["tags"]
week_start_monday = (settings.get("week_start","월요일")=="월요일")

# 상단 헤더
h1, h2, h3, h4 = st.columns([6,2,2,2])
with h1:
    st.markdown(f'<div class="hero"><h1>🚢 MUSV 통합 업무 대시보드</h1><p>{display_name} 님 · 프로젝트 <b>{selected_project}</b>{" · ☁️ 서버 저장 활성" if gh_available() else " · ⚠️ 로컬 저장 (임시)"}</p></div>', unsafe_allow_html=True)
with h2:
    project_list = settings.get("projects", ["MUSV-2"])
    new_proj = st.selectbox("프로젝트", project_list, index=project_list.index(selected_project) if selected_project in project_list else 0, key="hdr_proj")
    if new_proj != selected_project:
        settings["current_project"] = new_proj
        save_user_settings(USER, settings)
        st.rerun()
with h3:
    if st.button("🏠 홈으로", use_container_width=True):
        st.session_state.nav = "home"; st.session_state.selected_task_id=None; st.session_state.selected_mail_id=None
        st.rerun()
with h4:
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.auth_user = None
        st.session_state.nav = "home"
        st.rerun()

project_df = df[df["프로젝트"] == selected_project].copy()
overdue_n = int(compute_overdue(project_df).sum()) if not project_df.empty else 0
unread_n = int((~mdf["read"]).sum()) if not mdf.empty else 0


# =====================================================
# 9. 사이드바 - 요약 + 빠른 등록
# =====================================================
with st.sidebar:
    st.markdown(f"### 👤 {display_name}")
    st.caption(f"@{USER}")
    if st.button("🏠 홈 화면", use_container_width=True, key="sb_home"):
        st.session_state.nav = "home"; st.rerun()
    st.markdown("---")
    st.markdown("**빠른 이동**")
    sb_c1, sb_c2 = st.columns(2)
    if sb_c1.button("📊 대시보드", use_container_width=True): st.session_state.nav="dash"; st.rerun()
    if sb_c2.button("🗓️ 캘린더", use_container_width=True): st.session_state.nav="cal"; st.rerun()
    if sb_c1.button(f"📩 메일 ({unread_n})", use_container_width=True): st.session_state.nav="mail"; st.rerun()
    if sb_c2.button("🗂️ 전체 검색", use_container_width=True): st.session_state.nav="search"; st.rerun()
    if sb_c1.button("📈 통계", use_container_width=True): st.session_state.nav="stat"; st.rerun()
    if sb_c2.button("⚙️ 설정", use_container_width=True): st.session_state.nav="admin"; st.rerun()

    st.markdown("---")
    st.markdown("### ➕ 빠른 업무 등록")
    q_type = st.selectbox("업무유형", act_types, key="qadd_type")
    cats_keys = list(cats.keys()) or ["없음"]
    q_main = st.selectbox("대분류", cats_keys, key="qadd_main")
    if st.session_state.get("qadd_prev_main") != q_main:
        st.session_state["qadd_prev_main"] = q_main
        if "qadd_sub" in st.session_state: del st.session_state["qadd_sub"]
    sub_opts = cats.get(q_main, ["없음"]) or ["없음"]
    q_sub = st.selectbox("중분류", sub_opts, key="qadd_sub")
    q_prio = st.selectbox("우선순위", PRIORITY_LIST, index=1, key="qadd_prio")
    cd1,cd2 = st.columns(2)
    q_start = cd1.date_input("시작일", date.today(), key="qadd_s")
    q_target = cd2.date_input("목표일", date.today(), key="qadd_t")
    q_notgt = st.checkbox("목표일 미정", key="qadd_nt")
    q_title = st.text_input("제목 *", key="qadd_title")
    q_content = st.text_area("내용", height=70, key="qadd_content")
    q_tags = st.multiselect("태그", tags, key="qadd_tags")

    ai_on = ai_available(settings)
    if st.button("🤖 AI 자동 분류", use_container_width=True, disabled=(not ai_on) or (not q_title.strip() and not q_content.strip())):
        try:
            with st.spinner("AI 분류 중..."):
                r = ai_classify_task(settings, q_title, q_content, act_types, cats, tags)
            if isinstance(r,dict) and "업무유형" in r:
                if r.get("업무유형") in act_types: st.session_state["qadd_type"]=r["업무유형"]
                if r.get("대분류") in cats:
                    st.session_state["qadd_main"]=r["대분류"]; st.session_state["qadd_prev_main"]=r["대분류"]
                    if r.get("중분류") in cats.get(r["대분류"],[]): st.session_state["qadd_sub"]=r["중분류"]
                if r.get("우선순위") in PRIORITY_LIST: st.session_state["qadd_prio"]=r["우선순위"]
                if r.get("제안제목"): st.session_state["qadd_title"]=r["제안제목"]
                st.session_state["qadd_tags"]=[t for t in (r.get("태그") or []) if t in tags]
                st.success("AI 분류 반영됨"); st.rerun()
        except Exception as e:
            st.error(f"AI 실패: {e}")

    if st.button("✅ 등록", use_container_width=True, type="primary"):
        if not q_title.strip():
            st.error("제목 필수")
        else:
            now = pd.Timestamp.now()
            row = {"ID":new_id(),"프로젝트":selected_project,"업무유형":q_type,"대분류":q_main,"중분류":q_sub,
                   "우선순위":q_prio,"시작일":pd.to_datetime(q_start),
                   "목표일":pd.NaT if q_notgt else pd.to_datetime(q_target),"실제완료일":pd.NaT,
                   "장소":"","관련자(참석자/송수신자)":"","제목":q_title.strip(),"내용":q_content,
                   "태그":", ".join(q_tags),"상태":"미정" if q_notgt else "진행중",
                   "드라이브_링크":"","연관업무ID":"","생성일시":now,"수정일시":now}
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_tasks(USER, df)
            for k in ("qadd_title","qadd_content","qadd_tags"):
                if k in st.session_state: del st.session_state[k]
            st.success("등록 완료"); st.rerun()


# =====================================================
# 10. 상세 편집기 (재사용)
# =====================================================
def render_task_editor(df, task_id):
    ridx = df.index[df["ID"]==task_id]
    if len(ridx)==0:
        st.warning("업무를 찾을 수 없습니다."); return df
    idx = ridx[0]; t = df.loc[idx]
    st.markdown("---")
    hc1,hc2,hc3 = st.columns([7,1.2,1.3])
    hc1.subheader(f"📝 상세: {t['제목']}")
    hc1.caption(f"ID `{t['ID']}` · 생성 {pd.to_datetime(t['생성일시']).strftime('%Y-%m-%d %H:%M') if pd.notna(t['생성일시']) else '-'}")
    if hc2.button("🗑️ 삭제", key=f"tdel_{task_id}", use_container_width=True):
        df = df.drop(idx).reset_index(drop=True); save_tasks(USER, df); st.session_state.selected_task_id=None; st.rerun()
    if hc3.button("✖️ 닫기", key=f"tclose_{task_id}", use_container_width=True):
        st.session_state.selected_task_id=None; st.rerun()

    with st.container(border=True):
        c1,c2,c3,c4 = st.columns(4)
        stat_idx = STATUS_LIST.index(t["상태"]) if t["상태"] in STATUS_LIST else 0
        e_status = c1.selectbox("상태", STATUS_LIST, index=stat_idx, key=f"es_{task_id}")
        typ_idx = act_types.index(t["업무유형"]) if t["업무유형"] in act_types else 0
        e_type = c2.selectbox("업무유형", act_types, index=typ_idx, key=f"et_{task_id}")
        prio_idx = PRIORITY_LIST.index(t["우선순위"]) if t["우선순위"] in PRIORITY_LIST else 1
        e_prio = c3.selectbox("우선순위", PRIORITY_LIST, index=prio_idx, key=f"ep_{task_id}")
        with c4:
            st.write("")
            if st.button("✅ 완료 처리", key=f"edn_{task_id}", use_container_width=True):
                df.at[idx,"상태"]="완료"; df.at[idx,"실제완료일"]=pd.Timestamp.now(); df.at[idx,"수정일시"]=pd.Timestamp.now()
                save_tasks(USER, df); st.rerun()

        c1,c2,c3 = st.columns(3)
        s_d = t["시작일"] if pd.notna(t["시작일"]) else date.today()
        t_d = t["목표일"] if pd.notna(t["목표일"]) else None
        r_d = t["실제완료일"] if pd.notna(t["실제완료일"]) else None
        e_s = c1.date_input("시작일", pd.Timestamp(s_d).date(), key=f"eds_{task_id}")
        e_nt = c2.checkbox("목표일 미정", value=(t_d is None), key=f"ent_{task_id}")
        e_t = None if e_nt else c2.date_input("목표일", pd.Timestamp(t_d).date() if t_d is not None else date.today(), key=f"edt_{task_id}")
        e_r = c3.date_input("실제완료일", value=(pd.Timestamp(r_d).date() if r_d is not None else None), key=f"edr_{task_id}")

        c1,c2 = st.columns(2)
        cat_keys = list(cats.keys()) or ["없음"]
        mk = f"emc_{task_id}"; sk = f"esc_{task_id}"; pk = f"emcp_{task_id}"
        if mk not in st.session_state:
            st.session_state[mk] = t["대분류"] if t["대분류"] in cat_keys else cat_keys[0]
        if st.session_state.get(pk) != st.session_state[mk]:
            if sk in st.session_state: del st.session_state[sk]
            st.session_state[pk] = st.session_state[mk]
        e_main = c1.selectbox("대분류", cat_keys, key=mk)
        subs = cats.get(e_main, ["없음"]) or ["없음"]
        if sk not in st.session_state:
            st.session_state[sk] = t["중분류"] if t["중분류"] in subs else subs[0]
        elif st.session_state[sk] not in subs:
            st.session_state[sk] = subs[0]
        e_sub = c2.selectbox("중분류", subs, key=sk)

        e_title = st.text_input("제목", str(t["제목"]) if pd.notna(t["제목"]) else "", key=f"eti_{task_id}")
        e_content = st.text_area("내용", str(t["내용"]) if pd.notna(t["내용"]) else "", height=200, key=f"eco_{task_id}")

        c1,c2 = st.columns(2)
        e_ppl = c1.text_input("관련자", str(t["관련자(참석자/송수신자)"]) if pd.notna(t["관련자(참석자/송수신자)"]) else "", key=f"epp_{task_id}")
        e_loc = c2.text_input("장소", str(t["장소"]) if pd.notna(t["장소"]) else "", key=f"elc_{task_id}")

        curr_tags = [x.strip() for x in str(t["태그"]).split(",") if x.strip()] if pd.notna(t["태그"]) else []
        e_tags = st.multiselect("태그", list(dict.fromkeys(tags+curr_tags)), default=[x for x in curr_tags if x in list(dict.fromkeys(tags+curr_tags))], key=f"etg_{task_id}")
        e_link = st.text_input("자료 링크", str(t["드라이브_링크"]) if pd.notna(t["드라이브_링크"]) else "", key=f"eln_{task_id}")

        b1,b2 = st.columns([1,4])
        if b1.button("💾 저장", key=f"esv_{task_id}", type="primary", use_container_width=True):
            for k, v in [("상태",e_status),("업무유형",e_type),("우선순위",e_prio),("대분류",e_main),("중분류",e_sub),
                         ("시작일",pd.to_datetime(e_s)),("목표일",pd.NaT if e_nt else pd.to_datetime(e_t)),
                         ("실제완료일",pd.to_datetime(e_r) if e_r else pd.NaT),
                         ("제목",e_title),("내용",e_content),("관련자(참석자/송수신자)",e_ppl),
                         ("장소",e_loc),("태그",", ".join(e_tags)),("드라이브_링크",e_link),
                         ("수정일시",pd.Timestamp.now())]:
                df.at[idx,k] = v
            save_tasks(USER, df)
            for k in list(st.session_state.keys()):
                if k.endswith(f"_{task_id}"): del st.session_state[k]
            st.success("저장 완료"); st.rerun()
        b2.caption("💡 완료 처리 시 캘린더에서 취소선/흐린색으로 표시됩니다.")
    return df


# =====================================================
# 11. 라우팅
# =====================================================
NAV = st.session_state.nav


# ---------- 홈 ----------
if NAV == "home":
    st.markdown("### 원하는 작업을 선택하세요")

    total = len(project_df); ongoing = int((project_df["상태"]=="진행중").sum())
    ws,we = week_range(date.today(), start_monday=week_start_monday)
    _done = pd.to_datetime(project_df["실제완료일"], errors="coerce")
    done_week = int(((project_df["상태"]=="완료")&(_done>=ws)&(_done<=we)).sum()) if not project_df.empty else 0

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(f'<div class="kpi info"><div class="label">전체 업무</div><div class="value">{total}</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="kpi"><div class="label">진행중</div><div class="value">{ongoing}</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi warn"><div class="label">지연</div><div class="value">{overdue_n}</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi good"><div class="label">이번 주 완료</div><div class="value">{done_week}</div></div>', unsafe_allow_html=True)

    mail_cls = "hot" if unread_n>5 else ""
    overdue_cls = "warn" if overdue_n>0 else ""
    st.markdown(f"""
<div class="home-grid">
  <a class="home-tile" href="?nav=dash" target="_self">
    <span class="ico">📊</span><div class="ttl">대시보드</div><div class="desc">캘린더 · 주간보고 · 집중업무표</div>
  </a>
  <a class="home-tile" href="?nav=cal" target="_self">
    <span class="ico">🗓️</span><div class="ttl">캘린더</div><div class="desc">월/주/리스트 3-뷰</div>
  </a>
  <a class="home-tile {mail_cls}" href="?nav=mail" target="_self">
    <span class="ico">📩</span><div class="ttl">메일함 {"("+str(unread_n)+")" if unread_n else ""}</div>
    <div class="desc">AI 요약·번역·액션플랜 자동</div>
  </a>
  <a class="home-tile" href="?nav=search" target="_self">
    <span class="ico">🗂️</span><div class="ttl">전체 검색</div><div class="desc">모든 업무 · 다중 필터</div>
  </a>
  <a class="home-tile" href="?nav=stat" target="_self">
    <span class="ico">📈</span><div class="ttl">통계</div><div class="desc">상태·유형·주별 완료</div>
  </a>
  <a class="home-tile" href="?nav=admin" target="_self">
    <span class="ico">⚙️</span><div class="ttl">설정</div><div class="desc">Gmail·AI·서버 저장</div>
  </a>
</div>""", unsafe_allow_html=True)

    if overdue_n>0:
        st.markdown(f'<div class="alert">⚠️ 지연된 업무가 <b>{overdue_n}건</b> 있습니다. 대시보드에서 확인하세요.</div>', unsafe_allow_html=True)


# ---------- 대시보드 ----------
elif NAV == "dash":
    st.markdown("### 📊 대시보드")
    nc1,nc2,nc3,nc4 = st.columns([1,1,1.2,3])
    if nc1.button("◀ 이전"): st.session_state.cal_base_date -= timedelta(weeks=4); st.rerun()
    if nc2.button("다음 ▶"): st.session_state.cal_base_date += timedelta(weeks=4); st.rerun()
    if nc3.button("🎯 오늘로", use_container_width=True): st.session_state.cal_base_date=date.today(); st.rerun()
    picked = nc4.date_input("기준일", value=st.session_state.cal_base_date, label_visibility="collapsed")
    st.session_state.cal_base_date = picked

    st.markdown(render_month(project_df, st.session_state.cal_base_date, act_types, week_start_monday), unsafe_allow_html=True)

    # 주간보고
    st.markdown("### 📊 주간 업무 요약 보고서")
    with st.container(border=True):
        y,w,_ = pd.Timestamp(st.session_state.cal_base_date).isocalendar()
        ws,we = week_range(st.session_state.cal_base_date, start_monday=week_start_monday)
        title = f"[{y}-W{w:02d}] 주간보고"
        c1,c2,c3 = st.columns([5,2,2])
        c1.markdown(f"**기준 주차:** {y}년 {w}주 ({ws.strftime('%Y-%m-%d')} ~ {we.strftime('%Y-%m-%d')})")
        rule_btn = c2.button("✨ 규칙 요약", use_container_width=True)
        ai_btn = c3.button("🤖 AI 보고서", use_container_width=True, type="primary", disabled=not ai_available(settings))

        if rule_btn:
            m = ((project_df["시작일"]<=we)&(project_df["목표일"].isna()|(project_df["목표일"]>=ws))&(project_df["업무유형"]!="주간보고"))
            wk = project_df[m]
            lines = [f"📌 {selected_project} 주간보고 - {y}년 {w}주차", f"📅 {ws.strftime('%Y-%m-%d')} ~ {we.strftime('%Y-%m-%d')}", ""]
            for grp, label in [("완료","✅ 완료"),("진행중","🏃 진행/예정"),("지연","⚠️ 지연"),("보류","⏸️ 보류")]:
                sub = wk[wk["상태"]==grp] if grp!="진행중" else wk[wk["상태"].isin(["진행중","미정"])]
                lines.append(f"{label} ({len(sub)}건)")
                for _,t in sub.iterrows(): lines.append(f"  · [{t['업무유형']}] {t['제목']}")
                lines.append("")
            st.session_state[f"rep_{w}"] = "\n".join(lines); st.rerun()

        if ai_btn:
            m = ((project_df["시작일"]<=we)&(project_df["목표일"].isna()|(project_df["목표일"]>=ws))&(project_df["업무유형"]!="주간보고"))
            wk = project_df[m]
            lines = [f"- [{t['상태']}][{t['업무유형']}] {t['제목']} :: {str(t['내용'])[:200]}" for _,t in wk.iterrows()]
            summary = "\n".join(lines) or "(이번 주 업무 없음)"
            try:
                with st.spinner("AI 작성 중..."):
                    r = ai_weekly_report(settings, selected_project, f"{y}년 {w}주차", summary)
                st.session_state[f"rep_{w}"] = r; st.rerun()
            except Exception as e:
                st.error(f"AI 실패: {e}")

        existing = df[(df["프로젝트"]==selected_project)&(df["제목"]==title)&(df["업무유형"]=="주간보고")]
        default_text = existing["내용"].iloc[0] if not existing.empty else ""
        report_text = st.session_state.get(f"rep_{w}", default_text)
        edited = st.text_area("보고서 내용", value=report_text, height=280)
        rc1,rc2 = st.columns([1,5])
        if rc1.button("💾 저장", type="primary", use_container_width=True):
            now = pd.Timestamp.now()
            if not existing.empty:
                df.at[existing.index[0],"내용"] = edited; df.at[existing.index[0],"수정일시"] = now
            else:
                row = {"ID":new_id(),"프로젝트":selected_project,"업무유형":"주간보고",
                       "대분류":list(cats.keys())[0] if cats else "없음","중분류":"없음","우선순위":"🔵 보통",
                       "시작일":pd.to_datetime(we),"목표일":pd.to_datetime(we),"실제완료일":now,
                       "장소":"-","관련자(참석자/송수신자)":"-","제목":title,"내용":edited,
                       "태그":"주간보고","상태":"완료","드라이브_링크":"","연관업무ID":"",
                       "생성일시":now,"수정일시":now}
                df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_tasks(USER, df); st.success(f"{title} 저장"); st.rerun()
        rc2.download_button("⬇️ TXT 다운로드", data=edited.encode("utf-8"), file_name=f"{title}.txt")

    # 집중 업무표
    st.markdown("### 📋 집중 업무표")
    f1,f2,f3 = st.columns(3)
    tf = f1.multiselect("태그 필터", tags)
    yf = f2.multiselect("업무유형", act_types)
    pf = f3.multiselect("우선순위", PRIORITY_LIST)
    disp = project_df[project_df["상태"].isin(["진행중","미정","지연","보류"])].copy()
    if tf: disp = disp[disp["태그"].fillna("").str.contains("|".join(map(re.escape,tf)))]
    if yf: disp = disp[disp["업무유형"].isin(yf)]
    if pf: disp = disp[disp["우선순위"].isin(pf)]
    cols = ["상태","업무유형","우선순위","시작일","목표일","제목","내용","태그","관련자(참석자/송수신자)"]
    if disp.empty:
        st.info("표시할 업무가 없습니다.")
    else:
        ev = st.dataframe(
            disp[cols].sort_values(by=["우선순위","목표일"], ascending=[False,True], na_position="last"),
            use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row",
            column_config={"시작일":st.column_config.DateColumn(format="YYYY-MM-DD"),
                           "목표일":st.column_config.DateColumn(format="YYYY-MM-DD")},
            key="dash_tbl"
        )
        if ev.selection.rows:
            st.session_state.selected_task_id = disp.iloc[ev.selection.rows[0]]["ID"]
    if st.session_state.selected_task_id:
        df = render_task_editor(df, st.session_state.selected_task_id)


# ---------- 캘린더 ----------
elif NAV == "cal":
    st.markdown("### 🗓️ 캘린더")
    nc1,nc2,nc3,nc4 = st.columns([1,1,1.2,4])
    if nc1.button("◀ 이전"): st.session_state.cal_base_date -= timedelta(weeks=4); st.rerun()
    if nc2.button("다음 ▶"): st.session_state.cal_base_date += timedelta(weeks=4); st.rerun()
    if nc3.button("🎯 오늘로", use_container_width=True): st.session_state.cal_base_date=date.today(); st.rerun()
    st.session_state.cal_base_date = nc4.date_input("기준일", value=st.session_state.cal_base_date, label_visibility="collapsed", key="cal_dt")
    st.markdown(render_month(project_df, st.session_state.cal_base_date, act_types, week_start_monday), unsafe_allow_html=True)
    if st.session_state.selected_task_id:
        df = render_task_editor(df, st.session_state.selected_task_id)


# ---------- 메일함 ----------
elif NAV == "mail":
    if not settings.get("gmail_email") or not settings.get("gmail_app_password"):
        st.warning("먼저 [⚙️ 설정 → Gmail]에서 계정과 앱 비밀번호를 저장하세요.")
        if st.button("설정으로 이동", type="primary"): st.session_state.nav="admin"; st.rerun()
        st.stop()

    # 좌우 2단: 폴더 사이드바 + 본문
    left, right = st.columns([1.3, 6])

    with left:
        st.markdown("### 📁 메일함")
        if st.button("🔄 새 메일 불러오기", type="primary", use_container_width=True):
            with st.spinner("Gmail 조회 중..."):
                new_mails = fetch_gmail(settings["gmail_email"], settings["gmail_app_password"],
                                        settings["gmail_target_sender"], scan=250, limit=30)
            if new_mails:
                existing_uids = set(mdf["msg_uid"].astype(str).tolist())
                added = 0
                for m in new_mails:
                    if str(m["msg_uid"]) in existing_uids: continue
                    row = {
                        "ID": new_id(), "user": USER, "msg_uid": m["msg_uid"],
                        "received_at": m["received_at"], "sender": m["sender"],
                        "sender_name": m["sender_name"], "subject": m["subject"],
                        "body": m["body"], "ai_summary": "", "ai_actions": "",
                        "ai_translated": "", "folder": "받은편지함", "tags": "",
                        "read": False, "registered_task_id": "", "fetched_at": pd.Timestamp.now(),
                    }
                    mdf = pd.concat([mdf, pd.DataFrame([row])], ignore_index=True)
                    added += 1
                # AI 자동 분석
                if ai_available(settings) and settings.get("ai_auto_classify_mail") and added > 0:
                    prog = st.progress(0.0, text=f"AI 분석 중 (0/{added})")
                    to_analyze = mdf[(mdf["ai_summary"]=="")|mdf["ai_summary"].isna()]
                    for i, (mid, row) in enumerate(to_analyze.iterrows()):
                        try:
                            res = ai_action_plan(settings, row["subject"], row["sender"], row["body"])
                            if isinstance(res, dict):
                                mdf.at[mid,"ai_summary"] = res.get("요약","")
                                mdf.at[mid,"ai_actions"] = json.dumps(res, ensure_ascii=False)
                        except Exception:
                            pass
                        prog.progress((i+1)/len(to_analyze), text=f"AI 분석 중 ({i+1}/{len(to_analyze)})")
                    prog.empty()
                save_mails(USER, mdf)
                st.success(f"신규 {added}통 저장됨")
                st.rerun()
            else:
                st.info("새 메일 없음")

        st.markdown("---")
        folders = settings.get("mail_folders", ["받은편지함"])
        for f in folders:
            cnt = int((mdf["folder"]==f).sum())
            unread = int(((mdf["folder"]==f)&(~mdf["read"])).sum())
            active = " • 선택됨" if f == st.session_state.mail_folder else ""
            label = f"{'📥' if f=='받은편지함' else '📁'} {f} ({cnt}){' 🔵'+str(unread) if unread else ''}"
            if st.button(label, use_container_width=True, key=f"fld_{f}"):
                st.session_state.mail_folder = f
                st.session_state.selected_mail_id = None
                st.rerun()

        st.markdown("---")
        with st.expander("➕ 폴더 추가"):
            nf = st.text_input("폴더 이름", key="new_folder_name")
            if st.button("추가", use_container_width=True):
                if nf and nf not in folders:
                    folders.append(nf); settings["mail_folders"] = folders
                    save_user_settings(USER, settings); st.rerun()

    with right:
        if st.session_state.selected_mail_id is None:
            # ---- 메일 리스트 ----
            folder = st.session_state.mail_folder
            st.markdown(f"### 📬 {folder}")
            fmdf = mdf[mdf["folder"]==folder].sort_values("received_at", ascending=False)
            if fmdf.empty:
                st.info("메일이 없습니다. 좌측에서 [새 메일 불러오기]를 클릭하세요.")
            else:
                # 검색
                q = st.text_input("🔍 메일 검색 (제목·본문·발신자)", key="mail_search")
                if q:
                    ql = q.lower()
                    fmdf = fmdf[fmdf.apply(lambda r: ql in str(r["subject"]).lower() or ql in str(r["body"]).lower() or ql in str(r["sender"]).lower(), axis=1)]

                # 렌더링
                for _, r in fmdf.iterrows():
                    dt = pd.to_datetime(r["received_at"], errors="coerce")
                    dt_s = dt.strftime("%m/%d %H:%M") if pd.notna(dt) else "-"
                    snippet = re.sub(r"\s+"," ", str(r["ai_summary"] or r["body"] or ""))[:100]
                    unread_cls = "unread" if not r["read"] else "read"
                    subj = str(r["subject"]).replace("<","&lt;")
                    sname = str(r["sender_name"]).replace("<","&lt;")
                    ai_mark = "🤖 " if r["ai_summary"] else ""
                    st.markdown(
                        f'<a class="mailrow {unread_cls}" href="?nav=mail&mail_id={r["ID"]}" target="_self">'
                        f'<span>{"●" if not r["read"] else "○"}</span>'
                        f'<span class="sender">{sname}</span>'
                        f'<span class="date">{dt_s}</span>'
                        f'<span class="subject">{subj}<span class="snippet"> — {ai_mark}{snippet}</span></span>'
                        f'<span class="date">{"✓" if r["registered_task_id"] else ""}</span>'
                        f'</a>', unsafe_allow_html=True
                    )
        else:
            # ---- 메일 상세 ----
            mail_id = st.session_state.selected_mail_id
            midx = mdf.index[mdf["ID"]==mail_id]
            if len(midx)==0:
                st.warning("메일을 찾을 수 없습니다.")
                st.session_state.selected_mail_id = None
            else:
                mi = midx[0]; m = mdf.loc[mi]
                # 읽음 표시
                if not m["read"]:
                    mdf.at[mi,"read"] = True; save_mails(USER, mdf); m = mdf.loc[mi]

                tb1,tb2,tb3,tb4 = st.columns([6,1.3,1.3,1.4])
                tb1.subheader(f"✉️ {m['subject']}")
                if tb2.button("◀ 목록", use_container_width=True):
                    st.session_state.selected_mail_id=None; st.rerun()
                # 폴더 이동
                folders = settings.get("mail_folders", ["받은편지함"])
                current_f = m["folder"] if m["folder"] in folders else "받은편지함"
                new_folder = tb3.selectbox("📁 폴더", folders, index=folders.index(current_f),
                                            key=f"movefld_{mail_id}", label_visibility="collapsed")
                if new_folder != current_f:
                    mdf.at[mi,"folder"] = new_folder; save_mails(USER, mdf); st.rerun()
                if tb4.button("🗑️ 삭제", use_container_width=True):
                    mdf = mdf.drop(mi).reset_index(drop=True); save_mails(USER, mdf)
                    st.session_state.selected_mail_id=None; st.rerun()

                st.caption(f"**보낸이**: {m['sender']}  ·  **받은시각**: {pd.to_datetime(m['received_at']).strftime('%Y-%m-%d %H:%M') if pd.notna(m['received_at']) else '-'}")

                # ---- AI 액션플랜 ----
                ai_on2 = ai_available(settings)
                ac1, ac2 = st.columns([1,1])
                do_ai = ac1.button("🤖 AI 액션플랜 (재)분석", disabled=not ai_on2, use_container_width=True)
                do_tr = ac2.button("🌐 한국어 번역 (재)생성", disabled=not ai_on2, use_container_width=True)
                if do_ai:
                    try:
                        with st.spinner("AI 분석 중..."):
                            res = ai_action_plan(settings, m["subject"], m["sender"], m["body"])
                        mdf.at[mi,"ai_summary"] = res.get("요약","") if isinstance(res,dict) else ""
                        mdf.at[mi,"ai_actions"] = json.dumps(res, ensure_ascii=False)
                        save_mails(USER, mdf); st.rerun()
                    except Exception as e:
                        st.error(f"AI 실패: {e}")
                if do_tr:
                    try:
                        with st.spinner("번역 중..."):
                            tr = ai_translate(settings, m["body"])
                        mdf.at[mi,"ai_translated"] = tr; save_mails(USER, mdf); st.rerun()
                    except Exception as e:
                        st.error(f"번역 실패: {e}")

                # AI 결과 카드
                if m["ai_actions"]:
                    try: ap = json.loads(m["ai_actions"])
                    except: ap = {}
                    if isinstance(ap, dict) and not ap.get("_error"):
                        with st.container(border=True):
                            st.markdown("#### 🤖 AI 액션플랜")
                            ck1, ck2 = st.columns(2)
                            ck1.markdown(f"**긴급도**: {ap.get('긴급도','-')}")
                            ck2.markdown(f"**마감**: {ap.get('마감일자','-') or '미정'}")
                            st.markdown(f"**요약**: {ap.get('요약','-')}")
                            plan = ap.get("액션플랜", [])
                            if plan:
                                st.markdown("**📋 액션 아이템 (무엇을 언제까지 어떻게)**")
                                for i,p in enumerate(plan, 1):
                                    st.markdown(f"{i}. **{p.get('무엇','?')}** — 언제까지: `{p.get('언제까지','미정')}` / 어떻게: {p.get('어떻게','-')} / 담당: {p.get('담당','-')}")
                            if ap.get("핵심결정사항"):
                                st.markdown("**⚖️ 핵심 결정사항**")
                                for x in ap["핵심결정사항"]: st.markdown(f"- {x}")
                            if ap.get("확인필요"):
                                st.markdown("**🔎 확인 필요**")
                                for x in ap["확인필요"]: st.markdown(f"- {x}")
                elif ai_on2:
                    st.info("💡 [🤖 AI 액션플랜] 버튼을 눌러 자동 분석하세요.")

                # ---- 본문 / 번역 탭 ----
                tab_orig, tab_tr = st.tabs(["📄 본문", "🌐 한국어 번역"])
                with tab_orig:
                    st.text_area("원문", value=m["body"] or "", height=380, key=f"orig_{mail_id}", disabled=False)
                with tab_tr:
                    if m["ai_translated"]:
                        st.text_area("번역문", value=m["ai_translated"], height=380, key=f"tr_{mail_id}")
                    else:
                        st.info("아직 번역이 없습니다. 위의 [🌐 한국어 번역] 버튼을 눌러 생성하세요.")

                # ---- 캘린더 등록 (컴팩트 1행) ----
                st.markdown("---")
                st.markdown("#### 📌 캘린더에 업무로 등록")
                if m["registered_task_id"]:
                    st.success(f"✅ 이미 등록됨 · Task ID: `{m['registered_task_id']}`")
                # AI 추천값
                ap = {}
                if m["ai_actions"]:
                    try: ap = json.loads(m["ai_actions"])
                    except: ap = {}
                ai_due = ap.get("마감일자","") if isinstance(ap, dict) else ""
                default_due = date.today() + timedelta(days=7)
                if ai_due:
                    try: default_due = pd.to_datetime(ai_due).date()
                    except: pass
                ai_prio = ap.get("긴급도","🔵 보통") if isinstance(ap, dict) else "🔵 보통"
                if ai_prio not in PRIORITY_LIST: ai_prio = "🔵 보통"

                rc1,rc2,rc3,rc4,rc5,rc6 = st.columns([1.3,1,1.3,1.2,1.5,1.3])
                r_type = rc1.selectbox("업무유형", act_types,
                    index=act_types.index("메일/자료 송수신") if "메일/자료 송수신" in act_types else 0,
                    key=f"mrt_{mail_id}")
                r_stat = rc2.selectbox("상태", ["진행중","미정","완료"], key=f"mrs_{mail_id}")
                r_date = rc3.date_input("마감", default_due, key=f"mrd_{mail_id}")
                r_prio = rc4.selectbox("우선순위", PRIORITY_LIST, index=PRIORITY_LIST.index(ai_prio), key=f"mrp_{mail_id}")
                r_cat  = rc5.selectbox("대분류", list(cats.keys()), key=f"mrc_{mail_id}")
                r_sub_opts = cats.get(r_cat, ["없음"]) or ["없음"]
                r_sub  = rc6.selectbox("중분류", r_sub_opts, key=f"mrsu_{mail_id}")

                r_tags_default = []
                if isinstance(ap, dict):
                    # 태그 자동 매칭 (텍스트에서 태그 이름 포함 여부)
                    body_up = (m["subject"] + " " + (m["body"] or ""))
                    r_tags_default = [t for t in tags if t.lower() in body_up.lower()]
                r_tags = st.multiselect("태그", tags, default=r_tags_default, key=f"mrtg_{mail_id}")

                if st.button("📌 이 메일을 캘린더에 등록", type="primary", use_container_width=True):
                    now = pd.Timestamp.now()
                    body_prefix = ""
                    if m["ai_summary"]:
                        body_prefix = f"📌 AI 요약\n{m['ai_summary']}\n\n"
                    if isinstance(ap, dict) and ap.get("액션플랜"):
                        body_prefix += "✅ 액션 아이템\n"
                        for i,p in enumerate(ap["액션플랜"],1):
                            body_prefix += f"{i}. {p.get('무엇','')} (~{p.get('언제까지','미정')}, {p.get('어떻게','')})\n"
                        body_prefix += "\n"
                    body_prefix += "─── 원문 ───\n"
                    tid = new_id()
                    row = {"ID":tid,"프로젝트":selected_project,"업무유형":r_type,
                           "대분류":r_cat,"중분류":r_sub,"우선순위":r_prio,
                           "시작일":pd.to_datetime(date.today()),
                           "목표일":pd.NaT if r_stat=="미정" else pd.to_datetime(r_date),
                           "실제완료일":now if r_stat=="완료" else pd.NaT,
                           "장소":"-","관련자(참석자/송수신자)":m["sender_name"],
                           "제목":str(m["subject"])[:150],
                           "내용":(body_prefix + (m["body"] or ""))[:5000],
                           "태그":", ".join(r_tags),"상태":r_stat,
                           "드라이브_링크":"","연관업무ID":"",
                           "생성일시":now,"수정일시":now}
                    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
                    save_tasks(USER, df)
                    mdf.at[mi,"registered_task_id"] = tid
                    save_mails(USER, mdf)
                    st.success(f"등록 완료 (Task ID: {tid})"); st.rerun()


# ---------- 전체 검색 ----------
elif NAV == "search":
    st.markdown("### 🗂️ 전체 업무 · 검색")
    f1,f2,f3,f4 = st.columns(4)
    q = f1.text_input("🔍 검색어")
    sf = f2.multiselect("상태", STATUS_LIST)
    tf2 = f3.multiselect("업무유형", act_types)
    gf = f4.multiselect("태그", tags)
    d1,d2 = st.columns([1,5])
    dfrom = d1.date_input("시작일 이후", value=None)
    dto = d2.date_input("시작일 이전", value=None)

    fl = project_df.copy()
    if q:
        ql = q.lower()
        m = pd.Series(False, index=fl.index)
        for c in ("제목","내용","태그","관련자(참석자/송수신자)","장소","업무유형","대분류","중분류"):
            m = m | fl[c].fillna("").astype(str).str.lower().str.contains(re.escape(ql))
        fl = fl[m]
    if sf: fl = fl[fl["상태"].isin(sf)]
    if tf2: fl = fl[fl["업무유형"].isin(tf2)]
    if gf: fl = fl[fl["태그"].fillna("").str.contains("|".join(map(re.escape,gf)))]
    if dfrom: fl = fl[fl["시작일"]>=pd.to_datetime(dfrom)]
    if dto: fl = fl[fl["시작일"]<=pd.to_datetime(dto)]

    st.caption(f"총 **{len(fl)}건**")
    cols = ["상태","업무유형","우선순위","시작일","목표일","실제완료일","관련자(참석자/송수신자)","제목","태그"]
    ev = st.dataframe(
        fl[cols].sort_values("시작일", ascending=False),
        use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row",
        column_config={"시작일":st.column_config.DateColumn(format="YYYY-MM-DD"),
                       "목표일":st.column_config.DateColumn(format="YYYY-MM-DD"),
                       "실제완료일":st.column_config.DateColumn(format="YYYY-MM-DD")},
        key="all_tbl"
    )
    if ev.selection.rows:
        st.session_state.selected_task_id = fl.iloc[ev.selection.rows[0]]["ID"]
    st.download_button("⬇️ CSV 다운로드", data=fl.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"업무_{selected_project}_{date.today()}.csv")
    if st.session_state.selected_task_id:
        df = render_task_editor(df, st.session_state.selected_task_id)


# ---------- 통계 ----------
elif NAV == "stat":
    st.markdown("### 📈 통계")
    if project_df.empty:
        st.info("데이터가 없습니다.")
    else:
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("**상태별**")
            sc = project_df["상태"].value_counts().reset_index()
            sc.columns = ["상태","건수"]
            cm = {"진행중":"#3b82f6","완료":"#10b981","지연":"#ef4444","미정":"#6b7280","보류":"#f59e0b"}
            fig = px.pie(sc, names="상태", values="건수", hole=.45, color="상태", color_discrete_map=cm)
            fig.update_layout(height=320, margin=dict(t=10,b=10,l=10,r=10))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("**업무유형별**")
            tc = project_df["업무유형"].value_counts().reset_index(); tc.columns=["업무유형","건수"]
            fig2 = px.bar(tc, x="업무유형", y="건수", color="업무유형", text="건수")
            fig2.update_layout(showlegend=False, height=320, margin=dict(t=10,b=10,l=10,r=10))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**주별 완료 (최근 12주)**")
        dv = project_df[project_df["상태"]=="완료"].copy()
        dv["dt"] = pd.to_datetime(dv["실제완료일"], errors="coerce")
        dv = dv.dropna(subset=["dt"])
        if not dv.empty:
            dv["주"] = dv["dt"].dt.to_period("W-MON").dt.start_time
            wk = dv.groupby("주").size().reset_index(name="완료").sort_values("주").tail(12)
            fig3 = px.bar(wk, x="주", y="완료", text="완료", color_discrete_sequence=["#10b981"])
            fig3.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10))
            st.plotly_chart(fig3, use_container_width=True)


# ---------- 관리자 설정 ----------
elif NAV == "admin":
    st.markdown("### ⚙️ 설정")

    ta, tb, tc, td, te, tf, tg = st.tabs(["📁 프로젝트","🏷️ 분류·태그","📧 Gmail","🤖 AI","☁️ 서버 저장","🎨 화면","💾 백업"])

    with ta:
        st.markdown("#### 프로젝트")
        for i,p in enumerate(settings.get("projects", [])):
            c1,c2 = st.columns([5,1])
            c1.write(f"📁 {p}")
            if c2.button("삭제", key=f"delp_{i}") and len(settings["projects"])>1:
                settings["projects"].remove(p)
                if settings.get("current_project")==p: settings["current_project"]=settings["projects"][0]
                save_user_settings(USER, settings); st.rerun()
        np = st.text_input("새 프로젝트")
        if st.button("추가", type="primary") and np and np not in settings.get("projects",[]):
            settings["projects"] = settings.get("projects", []) + [np]
            save_user_settings(USER, settings); st.rerun()

    with tb:
        st.markdown(f"#### [{selected_project}] 업무유형 · 태그 · 분류")
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("**업무유형**")
            av = st.data_editor(pd.DataFrame({"업무유형":act_types}), num_rows="dynamic", key="ed_act")
            if st.button("💾 유형 저장"):
                settings["activity_types"] = av["업무유형"].dropna().astype(str).str.strip().tolist()
                if "주간보고" not in settings["activity_types"]: settings["activity_types"].append("주간보고")
                save_user_settings(USER, settings); st.rerun()
        with c2:
            st.markdown("**태그**")
            tv = st.data_editor(pd.DataFrame({"태그":tags}), num_rows="dynamic", key="ed_tag")
            if st.button("💾 태그 저장"):
                settings["tags"] = tv["태그"].dropna().astype(str).str.strip().tolist()
                save_user_settings(USER, settings); st.rerun()

        st.markdown("**분류 체계 (대분류→중분류)**")
        cl=[]
        for m,ss in cats.items():
            if not ss: cl.append({"대분류":m,"중분류":""})
            for s in ss: cl.append({"대분류":m,"중분류":s})
        cv = st.data_editor(pd.DataFrame(cl) if cl else pd.DataFrame(columns=["대분류","중분류"]),
                            num_rows="dynamic", key="ed_cat", use_container_width=True)
        if st.button("💾 분류 저장", type="primary"):
            nc={}
            for _,r in cv.iterrows():
                m = str(r["대분류"]).strip() if pd.notna(r["대분류"]) else ""
                s = str(r["중분류"]).strip() if pd.notna(r["중분류"]) else ""
                if not m: continue
                nc.setdefault(m,[])
                if s and s not in nc[m]: nc[m].append(s)
            settings["categories"] = nc
            save_user_settings(USER, settings); st.rerun()

    with tc:
        st.markdown("#### Gmail (한 번만 저장, 로그인 시 자동 로드)")
        ge = st.text_input("Gmail 주소", value=settings.get("gmail_email",""))
        gp = st.text_input("앱 비밀번호 (16자리)", value=settings.get("gmail_app_password",""), type="password")
        gt = st.text_input("고정 발신자 필터 (쉼표)", value=settings.get("gmail_target_sender",""))
        if st.button("💾 Gmail 저장", type="primary"):
            settings.update({"gmail_email":ge.strip(),
                              "gmail_app_password":gp.strip().replace(" ",""),
                              "gmail_target_sender":gt.strip()})
            save_user_settings(USER, settings)
            st.success("저장. 이제 매번 재입력할 필요 없습니다."); st.rerun()
        st.caption("💡 앱 비밀번호: https://myaccount.google.com/apppasswords (2단계 인증 켜져 있어야 함)")

    with td:
        st.markdown("#### AI 자동화 (한 번만 저장, 로그인 시 자동 로드)")
        ae = st.toggle("AI 활성화", value=settings.get("ai_enabled", False))
        ap_ = st.radio("공급자", ["gemini","openai","anthropic"],
                       index=["gemini","openai","anthropic"].index(settings.get("ai_provider","gemini")),
                       horizontal=True, format_func=lambda x:{"gemini":"Google Gemini","openai":"OpenAI","anthropic":"Anthropic"}[x])
        model_map = {
            "gemini":["gemini-3.5-flash","gemini-3.5-flash-lite","gemini-flash-latest","gemini-pro-latest","gemini-3.6-flash"],
            "openai":["gpt-4o-mini","gpt-4o","gpt-4.1-mini","gpt-4.1"],
            "anthropic":["claude-3-5-haiku-20241022","claude-3-5-sonnet-20241022","claude-sonnet-4-20250514"],
        }
        cm = settings.get("ai_model", model_map[ap_][0])
        mo = model_map[ap_]
        if cm not in mo: mo = [cm] + mo
        am = st.selectbox("모델", mo, index=mo.index(cm) if cm in mo else 0)
        am = st.text_input("모델명 (직접 입력 가능)", value=am)
        ak = st.text_input("API 키", value=settings.get("ai_api_key",""), type="password")

        au1 = st.checkbox("메일 불러올 때 자동 AI 분석", value=settings.get("ai_auto_classify_mail", True))
        au2 = st.checkbox("자동 번역 (영문 감지 시)", value=settings.get("ai_auto_translate", True))

        b1,b2 = st.columns(2)
        if b1.button("💾 AI 저장", type="primary", use_container_width=True):
            clean_m = am.strip()
            if ap_=="gemini" and clean_m.startswith("models/"): clean_m = clean_m[len("models/"):]
            settings.update({"ai_enabled":ae, "ai_provider":ap_, "ai_api_key":ak.strip(),
                             "ai_model":clean_m, "ai_auto_classify_mail":au1, "ai_auto_translate":au2})
            save_user_settings(USER, settings); st.success("저장"); st.rerun()
        if b2.button("🧪 연결 테스트", use_container_width=True, disabled=not ak.strip()):
            tmp = {"ai_enabled":True,"ai_provider":ap_,"ai_api_key":ak.strip(),"ai_model":am.strip()}
            try:
                with st.spinner("호출 중..."):
                    r = ai_call(tmp, "You are a test bot.", "한 줄로 안녕하세요 라고만 답하세요.", mx=50)
                st.success(f"✅ 응답: {r[:120]}")
            except Exception as e:
                st.error(f"❌ {e}")

        with st.expander("🔑 Gemini 키 발급 (무료 티어)"):
            st.markdown("""
1. https://aistudio.google.com/app/apikey → **Create API key**
2. `AQ.` 또는 `AIza` 로 시작하는 키 복사 → 위 API 키 필드에 붙여넣기
3. **2026-09 현재 유효한 모델**: `gemini-3.5-flash` (기본값 · 무료 티어)
4. `gemini-1.5-flash`, `gemini-2.5-flash` 는 신규 계정에서 서비스 종료 → 404 발생
""")
        with st.expander("🔑 OpenAI"):
            st.markdown("https://platform.openai.com/api-keys · 추천 모델 `gpt-4o-mini`")
        with st.expander("🔑 Anthropic Claude"):
            st.markdown("https://console.anthropic.com/settings/keys · 추천 모델 `claude-3-5-haiku-20241022`")

    with te:
        st.markdown("#### ☁️ 서버 영속 저장 (GitHub)")
        if gh_available():
            owner, repo, branch = gh_conf()
            st.success(f"✅ 서버 저장 활성화됨: `{owner}/{repo}` (branch: {branch})")
            st.caption("모든 데이터는 저장할 때마다 GitHub에 자동 커밋됩니다. Streamlit이 초기화되어도 다시 로그인하면 그대로 복원됩니다.")
            u_files = [_paths(USER)["tasks"], _paths(USER)["mails"], _paths(USER)["settings"]]
            st.markdown("**저장 경로**")
            for f in u_files: st.code(f)
        else:
            st.warning("⚠️ 서버 저장이 아직 설정되지 않았습니다.")
            st.markdown("""
### 설정 방법 (5분)

1. **GitHub 개인 저장소 만들기** (public/private 상관 없음)
   - 예: `musv-data`
2. **Personal Access Token 발급**
   - https://github.com/settings/personal-access-tokens/new
   - Repository access: 위에서 만든 저장소만
   - Permissions → Contents: **Read and write**
   - 생성된 토큰 (`github_pat_...`) 복사
3. **Streamlit Cloud 시크릿 설정**
   - Streamlit Cloud 대시보드 → 앱 → ⋮ → Settings → **Secrets**
   - 아래 내용 붙여넣고 저장:
   ```toml
   GITHUB_TOKEN = "github_pat_여기에붙여넣기"
   GITHUB_OWNER = "여러분_GitHub_아이디"
   GITHUB_REPO  = "musv-data"
   GITHUB_BRANCH = "main"
   ```
4. **자동 재배포** → 이 페이지 새로고침하면 위에 '서버 저장 활성화됨' 뜹니다.

로컬 실행 시에는 환경변수로 같은 값을 세팅하면 됩니다.
""")

    with tf:
        st.markdown("#### 화면")
        ws_choice = st.radio("주 시작 요일", ["월요일","일요일"],
                             index=["월요일","일요일"].index(settings.get("week_start","월요일")), horizontal=True)
        if st.button("💾 저장"):
            settings["week_start"] = ws_choice; save_user_settings(USER, settings); st.rerun()

    with tg:
        st.markdown("#### 데이터 백업/복원")
        c1,c2 = st.columns(2)
        with c1:
            st.download_button("⬇️ 업무 CSV",
                data=df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"tasks_{USER}_{date.today()}.csv", use_container_width=True)
            st.download_button("⬇️ 메일 CSV",
                data=mdf.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"mails_{USER}_{date.today()}.csv", use_container_width=True)
            st.download_button("⬇️ 설정 JSON",
                data=json.dumps(settings, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name=f"settings_{USER}_{date.today()}.json", use_container_width=True)
        with c2:
            up = st.file_uploader("업무 CSV 복원", type=["csv"])
            if up and st.button("업무 복원", type="primary"):
                try:
                    _df = pd.read_csv(up); save_tasks(USER, _df); st.success("복원 완료"); st.rerun()
                except Exception as e: st.error(f"실패: {e}")
            up2 = st.file_uploader("설정 JSON 복원", type=["json"])
            if up2 and st.button("설정 복원"):
                try:
                    obj = json.load(up2); save_user_settings(USER, obj); st.success("복원"); st.rerun()
                except Exception as e: st.error(f"실패: {e}")

st.markdown('<div style="text-align:center;color:#9ca3af;font-size:12px;margin-top:32px">🚢 MUSV Task Dashboard v3 · Built by Genspark AI</div>', unsafe_allow_html=True)
