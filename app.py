import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import json
import imaplib
import email
from email.header import decode_header
import re

# 1. 파일 경로 설정
DATA_FILE = 'all_tasks_v2.csv'
SETTINGS_FILE = 'settings.json'

DEFAULT_SETTINGS = {
    "MUSV-2": {
        "categories": {
            "1. 개요": ["1-1. 일정", "1-2. 회의"],
            "2. BCC": ["2-1. BCC", "2-2. 사급자재", "2-3. ECS PC", "2-4. 모니터"],
            "3. DAU": ["3-1. DAU PANEL", "3-2. DAU & HISTORIAN", "3-3. UPS", "3-4. ECS PLC 프로그램"],
            "4. KR": ["4-1. 제출자료"],
            "5. 프로그램": ["5-1. 컨셉 다이어그램", "5-2. ECS PLC", "5-3. ECS PC", "5-4. ECS HMI", "5-5. 임무콘솔", "5-6. DAU & HISTORIAN", "5-7. ETC."]
        },
        "tags": ["DAU", "BCC", "사급자재", "UPS", "ECS PC", "ECS PLC", "ECS 모니터", "DAU PANEL", 
                 "히스토리안서버", "극동선박설계", "유일조선소", "한화시스템", "한화엔진", "한화오션", "KR선급"],
        "weekly_reports": {}
    },
    "gmail_settings": {
        "email": "lhb8606@gmail.com",
        "app_password": "",
        "target_sender": "hblee@dh.co.kr OR 이헌범"
    }
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "gmail_settings" not in data:
                data["gmail_settings"] = {"email": "lhb8606@gmail.com", "app_password": "", "target_sender": "hblee@dh.co.kr OR 이헌범"}
            elif "target_sender" not in data["gmail_settings"]:
                data["gmail_settings"]["target_sender"] = "hblee@dh.co.kr OR 이헌범"
                
            for proj in data:
                if proj != "gmail_settings" and "weekly_reports" not in data[proj]:
                    data[proj]["weekly_reports"] = {}
            return data
    else:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if '드라이브_링크' not in df.columns:
            df['드라이브_링크'] = ""
        if '연관업무ID' not in df.columns:
            df['연관업무ID'] = ""
    else:
        cols = ["프로젝트", "업무유형", "대분류", "중분류", "시작일", "목표일", "실제완료일", "장소", "관련자(참석자/송수신자)", "내용(주제)", "회의록_및_비고", "태그", "상태", "드라이브_링크", "연관업무ID"]
        df = pd.DataFrame(columns=cols)
    
    date_columns = ['시작일', '목표일', '실제완료일']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def extract_company_from_email(email_addr):
    match = re.search(r'@([a-zA-Z0-9-]+)\.', str(email_addr))
    if match:
        return match.group(1)
    return str(email_addr)

def decode_mime_words(s):
    if not s: return ""
    decoded_words = decode_header(s)
    result = ""
    for word, encoding in decoded_words:
        if isinstance(word, bytes):
            result += word.decode(encoding or 'utf-8', errors='ignore')
        else:
            result += str(word)
    return result

def get_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                except:
                    pass
    else:
        try:
            return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='ignore')
        except:
            pass
    return ""

# [에러 원천 차단] 파이썬 자체 필터링 엔진이 탑재된 이메일 연동 함수
def fetch_musv_emails(email_user, app_password, target_sender):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, app_password)
        
        # 1. 언어에 상관없이 '전체보관함(All Mail)' 폴더를 자동으로 찾아 접속
        status, folders = mail.list()
        all_mail_folder = '"[Gmail]/All Mail"'
        for folder in folders:
            if b'\\All' in folder:
                parts = folder.decode('utf-8', errors='ignore').split(' "/" ')
                if len(parts) == 2:
                    all_mail_folder = parts[1]
                break
        
        mail.select(all_mail_folder, readonly=True)
        
        # 2. 구글 서버에는 '가장 최근 메일 전부 가져와' 라고만 명령 (에러 발생 확률 0%)
        status, messages = mail.search(None, "ALL")
        
        email_list = []
        if status == "OK" and messages[0]:
            msg_ids = messages[0].split()
            
            # 검색어 분리 (예: 'hblee@dh.co.kr' 와 '이헌범')
            targets = [t.strip().lower() for t in target_sender.replace('OR', ',').split(',') if t.strip()]
            
            # 3. 가장 최근 메일 150개를 역순으로 스캔하며 파이썬이 직접 발신자 검사
            for msg_id in reversed(msg_ids[-150:]):
                res, msg_data = mail.fetch(msg_id, '(RFC822)')
                if res == "OK":
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    sender = decode_mime_words(msg.get("From", ""))
                    sender_lower = sender.lower()
                    
                    # 파이썬 자체 필터링 (완벽한 한글 매칭 지원)
                    matched = False
                    for t in targets:
                        if t in sender_lower:
                            matched = True
                            break
                            
                    if matched:
                        subject = decode_mime_words(msg.get("Subject", ""))
                        date_ = msg.get("Date", "")
                        company = extract_company_from_email(sender)
                        body = get_email_body(msg)
                        
                        short_body = (body[:100] + '...') if len(body) > 100 else body
                        
                        email_list.append({
                            "날짜": date_,
                            "회사명": company,
                            "보낸이": sender,
                            "제목": subject,
                            "본문요약": short_body.strip()
                        })
                        
                        # 원하는 메일을 10개 찾으면 탐색 종료
                        if len(email_list) >= 10:
                            break
        mail.logout()
        return email_list
    except Exception as e:
        st.error(f"메일 연동 실패: {e}")
        return []

if 'cal_base_date' not in st.session_state:
    st.session_state.cal_base_date = date.today()

def set_today():
    st.session_state.cal_base_date = date.today()

def generate_calendar_html(df, base_date):
    idx = (base_date.weekday() + 1) % 7
    current_sunday = base_date - timedelta(days=idx)
    start_date = current_sunday - timedelta(weeks=2)
    
    html = "<table style='width:100%; border-collapse: collapse; font-family: sans-serif; font-size:13px;'>"
    html += "<tr style='background-color:#f0f2f6; text-align:center; height:40px;'>"
    html += "<th style='width:5%; color:#555;'>주차</th>"
    html += "<th style='width:13.5%; color:#e52528;'>일</th><th style='width:13.5%;'>월</th><th style='width:13.5%;'>화</th><th style='width:13.5%;'>수</th><th style='width:13.5%;'>목</th><th style='width:13.5%;'>금</th><th style='width:13.5%; color:#1890ff;'>토</th></tr>"
    
    curr_date = start_date
    today = date.today()
    valid_df = df.dropna(subset=['시작일', '목표일'])
    
    for _ in range(6):
        thursday = curr_date + timedelta(days=4)
        week_num = str(thursday.isocalendar()[1])
        
        html += "<tr>"
        html += f"<td style='border:1px solid #ddd; text-align:center; background-color:#fafafa; font-weight:bold; color:#777;'>{week_num}주</td>"
        
        for i in range(7):
            is_today = (curr_date == today)
            bg = "#fffbe6" if is_today else "#ffffff"
            text_color = "#e52528" if i==0 else ("#1890ff" if i==6 else "#262730")
            
            html += f"<td style='border:1px solid #ddd; height:120px; vertical-align:top; background-color:{bg}; padding:6px;'>"
            html += f"<div style='font-weight:bold; color:{text_color}; margin-bottom:4px;'>{curr_date.month}/{curr_date.day}</div>"
            
            if not valid_df.empty:
                day_tasks = valid_df[(valid_df['시작일'] <= pd.Timestamp(curr_date)) & (valid_df['목표일'] >= pd.Timestamp(curr_date))]
                for _, task in day_tasks.iterrows():
                    bg_color = "#52c41a" if task['상태'] == "완료" else ("#f5222d" if task['상태'] == "지연" else "#1890ff")
                    html += f"<div style='background-color:{bg_color}; color:white; border-radius:3px; padding:2px 5px; margin-bottom:2px; font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;' title='{task['내용(주제)']}'>{task['내용(주제)']}</div>"
                    
            html += "</td>"
            curr_date += timedelta(days=1)
        html += "</tr>"
    html += "</table>"
    return html

st.set_page_config(page_title="통합 업무 대시보드", layout="wide")
settings = load_settings()
df = load_data()

st.sidebar.title("🛠️ 시스템 관리")
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "rb") as file:
        st.sidebar.download_button(label="⬇️ CSV 백업", data=file, file_name="MUSV_백업.csv", mime="text/csv", use_container_width=True)

col_proj1, col_proj2 = st.columns([8, 2])
with col_proj1:
    st.title("🚢 통합 업무 대시보드")
with col_proj2:
    project_list = [p for p in settings.keys() if p != "gmail_settings"]
    selected_project = st.selectbox("📁 현재 프로젝트", project_list)
    menu = st.selectbox("메뉴", ["📊 대시보드 (업무 관리)", "📩 이메일 연동함", "⚙️ 관리자 설정"])

proj_categories = settings[selected_project]["categories"]
proj_tags = settings[selected_project]["tags"]

if menu == "📊 대시보드 (업무 관리)":
    col_main, col_input = st.columns([3, 1])
    
    with col_input:
        st.markdown("### 📝 새로운 업무 등록")
        with st.container(border=True):
            activity_type = st.selectbox("업무 유형 선택", ["회의 진행", "메일/자료 송수신", "일반 업무 (설계/검토 등)"])
            main_cat = st.selectbox("대분류", list(proj_categories.keys()))
            sub_cat = st.selectbox("중분류", proj_categories[main_cat] if proj_categories[main_cat] else ["없음"])
            start_date = st.date_input("시작일", date.today())
            target_date = st.date_input("목표일", date.today())
            
            if activity_type == "회의 진행":
                location = st.text_input("장소")
                people = st.text_input("참석자")
                content = st.text_input("주제")
                note = st.text_area("회의록 요약")
            else:
                location = "-"
                people = st.text_input("관련자/송수신자")
                content = st.text_area("내용")
                note = st.text_input("비고")
                
            tags = st.multiselect("태그", proj_tags)
            drive_link = st.text_input("자료 링크 🔗")
            
            existing_tasks = df[df['프로젝트'] == selected_project]['내용(주제)'].dropna().unique().tolist()
            related_task = st.selectbox("관련 이전 메일/업무 (선택)", ["없음"] + existing_tasks)
            
            if st.button("등록하기", type="primary", use_container_width=True):
                rel_val = related_task if related_task != "없음" else ""
                new_row = {
                    "프로젝트": selected_project, "업무유형": activity_type,
                    "대분류": main_cat, "중분류": sub_cat, 
                    "시작일": pd.to_datetime(start_date), "목표일": pd.to_datetime(target_date), "실제완료일": pd.NaT,
                    "장소": location, "관련자(참석자/송수신자)": people, "내용(주제)": content, 
                    "회의록_및_비고": note, "태그": ", ".join(tags), "상태": "진행중", "드라이브_링크": drive_link, "연관업무ID": rel_val
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("등록 성공!")
                st.rerun()

    with col_main:
        project_df = df[df['프로젝트'] == selected_project].copy()
        st.subheader("업무 일정 캘린더")
        col_cal1, col_cal2 = st.columns([3, 7])
        with col_cal1:
            st.date_input("조회 기준일", key='cal_base_date')
            st.button("🎯 오늘로 복귀", on_click=set_today)
        
        calendar_html = generate_calendar_html(project_df, st.session_state.cal_base_date)
        st.markdown(calendar_html, unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("📋 전체 업무 상세 표 (선택하여 수정)")
        
        display_df = project_df[['상태', '업무유형', '시작일', '목표일', '관련자(참석자/송수신자)', '내용(주제)', '연관업무ID', '드라이브_링크']]
        
        event = st.dataframe(
            display_df,
            column_config={"드라이브_링크": st.column_config.LinkColumn("자료 링크")},
            on_select="rerun", selection_mode="single-row", use_container_width=True, hide_index=True
        )
        
        if len(event.selection.rows) > 0:
            selected_row_idx = event.selection.rows[0]
            actual_idx = display_df.index[selected_row_idx]
            task_data = display_df.loc[actual_idx]
            
            st.markdown("---")
            st.subheader("📝 선택한 업무 상세 보기 및 전체 수정")
            
            with st.form("edit_form"):
                col_e1, col_e2, col_e3 = st.columns(3)
                edit_status = col_e1.selectbox("상태", ["진행중", "완료", "지연"], index=["진행중", "완료", "지연"].index(task_data['상태']))
                edit_type = col_e2.selectbox("업무유형", ["회의 진행", "메일/자료 송수신", "일반 업무 (설계/검토 등)"], index=["회의 진행", "메일/자료 송수신", "일반 업무 (설계/검토 등)"].index(task_data['업무유형']))
                
                s_date = task_data['시작일'] if pd.notna(task_data['시작일']) else date.today()
                t_date = task_data['목표일'] if pd.notna(task_data['목표일']) else date.today()
                r_date = task_data['실제완료일'] if pd.notna(task_data['실제완료일']) else None
                
                edit_s_date = col_e1.date_input("시작일", s_date)
                edit_t_date = col_e2.date_input("목표일", t_date)
                edit_r_date = col_e3.date_input("실제완료일", value=r_date)

                col_e4, col_e5 = st.columns(2)
                main_cat_idx = list(proj_categories.keys()).index(task_data['대분류']) if task_data['대분류'] in proj_categories else 0
                edit_main_cat = col_e4.selectbox("대분류", list(proj_categories.keys()), index=main_cat_idx)
                
                sub_cats = proj_categories.get(edit_main_cat, ["없음"])
                sub_cat_idx = sub_cats.index(task_data['중분류']) if task_data['중분류'] in sub_cats else 0
                edit_sub_cat = col_e5.selectbox("중분류", sub_cats, index=sub_cat_idx)
                
                edit_loc = st.text_input("장소", str(task_data['장소']) if pd.notna(task_data['장소']) else "")
                edit_people = st.text_input("관련자(참석자/송수신자)", str(task_data['관련자(참석자/송수신자)']) if pd.notna(task_data['관련자(참석자/송수신자)']) else "")
                edit_content = st.text_area("내용(주제)", str(task_data['내용(주제)']) if pd.notna(task_data['내용(주제)']) else "")
                edit_note = st.text_area("회의록 및 비고", str(task_data['회의록_및_비고']) if pd.notna(task_data['회의록_및_비고']) else "", height=150)
                edit_link = st.text_input("구글 드라이브 링크", str(task_data['드라이브_링크']) if pd.notna(task_data['드라이브_링크']) else "")
                
                current_tags = [t.strip() for t in str(task_data['태그']).split(",")] if pd.notna(task_data['태그']) and task_data['태그'] else []
                valid_tags = [t for t in current_tags if t in proj_tags]
                edit_tags = st.multiselect("태그", proj_tags, default=valid_tags)
                
                if st.form_submit_button("변경 사항 저장"):
                    df.at[actual_idx, '상태'] = edit_status
                    df.at[actual_idx, '업무유형'] = edit_type
                    df.at[actual_idx, '대분류'] = edit_main_cat
                    df.at[actual_idx, '중분류'] = edit_sub_cat
                    df.at[actual_idx, '시작일'] = pd.to_datetime(edit_s_date)
                    df.at[actual_idx, '목표일'] = pd.to_datetime(edit_t_date)
                    df.at[actual_idx, '실제완료일'] = pd.to_datetime(edit_r_date) if edit_r_date else pd.NaT
                    df.at[actual_idx, '장소'] = edit_loc
                    df.at[actual_idx, '관련자(참석자/송수신자)'] = edit_people
                    df.at[actual_idx, '내용(주제)'] = edit_content
                    df.at[actual_idx, '회의록_및_비고'] = edit_note
                    df.at[actual_idx, '드라이브_링크'] = edit_link
                    df.at[actual_idx, '태그'] = ", ".join(edit_tags)
                    
                    save_data(df)
                    st.success("업무 내용이 성공적으로 수정되었습니다.")
                    st.rerun()

elif menu == "📩 이메일 연동함":
    st.title("📩 수신된 이메일 일정 등록")
    g_settings = settings.get("gmail_settings", {})
    
    with st.expander("⚙️ Gmail 연동 설정 (한 번만 입력)"):
        g_email = st.text_input("Gmail 주소", value=g_settings.get("email", ""))
        g_app_pw = st.text_input("앱 비밀번호 (16자리)", value=g_settings.get("app_password", ""), type="password")
        
        # 라벨 입력칸은 제거했습니다 (파이썬이 직접 발신자만 필터링하므로 훨씬 안정적입니다)
        st.info("💡 에러 방지를 위해 '고정 발신자' 기준으로 수신 메일을 탐색합니다.")
        g_target = st.text_input("고정 발신자 필터 (여러 명일 경우 'OR' 대신 쉼표(,)로 구분)", value=g_settings.get("target_sender", "hblee@dh.co.kr, 이헌범"))
        
        if st.button("설정 저장"):
            settings["gmail_settings"] = {"email": g_email, "app_password": g_app_pw, "target_sender": g_target}
            save_settings(settings)
            st.success("메일 설정이 저장되었습니다.")
            
    if st.button("🔄 새 메일 불러오기", type="primary"):
        if g_email and g_app_pw and g_target:
            with st.spinner(f"가장 최근 수신된 메일 중 발신자가 '{g_target}'인 메일을 걸러내고 있습니다..."):
                emails = fetch_musv_emails(g_email, g_app_pw, g_target)
                if emails:
                    st.session_state.fetched_emails = emails
                    st.success(f"{len(emails)}개의 지정된 메일을 성공적으로 불러왔습니다.")
                else:
                    st.warning("최근 150개의 메일 중 해당 발신자의 메일이 없습니다.")
        else:
            st.error("위의 연동 설정에서 이메일, 앱 비밀번호, 고정 발신자를 모두 확인해 주세요.")
            
    if 'fetched_emails' in st.session_state and st.session_state.fetched_emails:
        for idx, email_data in enumerate(st.session_state.fetched_emails):
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**[{email_data['회사명'].upper()}]** {email_data['제목']}")
                st.caption(f"보낸이: {email_data['보낸이']} | 날짜: {email_data['날짜']}")
                st.write(f"📝 요약: {email_data['본문요약']}")
            with col2:
                with st.form(f"mail_reg_{idx}"):
                    m_date = st.date_input("마감 일정", date.today())
                    m_status = st.selectbox("마감 상태", ["진행중", "미정", "완료"])
                    
                    existing_tasks = df[df['프로젝트'] == selected_project]['내용(주제)'].dropna().unique().tolist()
                    m_related = st.selectbox("관련 이전 업무", ["없음"] + existing_tasks)
                    
                    if st.form_submit_button("일정으로 등록"):
                        new_row = {
                            "프로젝트": selected_project, "업무유형": "메일/자료 송수신",
                            "대분류": list(proj_categories.keys())[0], "중분류": proj_categories[list(proj_categories.keys())[0]][0],
                            "시작일": pd.to_datetime(date.today()), "목표일": pd.to_datetime(m_date) if m_status != "미정" else pd.NaT, "실제완료일": pd.NaT,
                            "장소": "-", "관련자(참석자/송수신자)": email_data['회사명'], "내용(주제)": email_data['제목'], 
                            "회의록_및_비고": email_data['본문요약'], "태그": "메일수신", "상태": m_status if m_status != "미정" else "진행중", 
                            "드라이브_링크": "", "연관업무ID": m_related if m_related != "없음" else ""
                        }
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(df)
                        st.success("달력과 표에 등록되었습니다!")

elif menu == "⚙️ 관리자 설정":
    st.title("⚙️ 시스템 관리자 페이지")
    st.info("분류/태그 관리는 동일하게 동작합니다.")
