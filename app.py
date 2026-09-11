import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import json
import imaplib
import email
from email.header import decode_header
import re

# ==========================================
# 1. 파일 경로 및 기본 설정
# ==========================================
DATA_FILE = 'all_tasks_v2.csv'
SETTINGS_FILE = 'settings.json'

DEFAULT_SETTINGS = {
    "MUSV-2": {
        "activity_types": ["회의 진행", "메일/자료 송수신", "일반 업무 (설계/검토 등)"],
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
                if proj != "gmail_settings":
                    if "weekly_reports" not in data[proj]:
                        data[proj]["weekly_reports"] = {}
                    if "activity_types" not in data[proj]:
                        data[proj]["activity_types"] = ["회의 진행", "메일/자료 송수신", "일반 업무 (설계/검토 등)"]
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
        required_cols = ["프로젝트", "업무유형", "대분류", "중분류", "시작일", "목표일", "실제완료일", "장소", "관련자(참석자/송수신자)", "내용(주제)", "회의록_및_비고", "태그", "상태", "드라이브_링크", "연관업무ID"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
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

def fetch_musv_emails(email_user, app_password, target_sender):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, app_password)
        
        status, folders = mail.list()
        all_mail_folder = '"[Gmail]/All Mail"'
        for folder in folders:
            if b'\\All' in folder:
                parts = folder.decode('utf-8', errors='ignore').split(' "/" ')
                if len(parts) == 2:
                    all_mail_folder = parts[1]
                break
        
        mail.select(all_mail_folder, readonly=True)
        status, messages = mail.search(None, "ALL")
        
        email_list = []
        if status == "OK" and messages[0]:
            msg_ids = messages[0].split()
            targets = [t.strip().lower() for t in target_sender.replace('OR', ',').split(',') if t.strip()]
            
            for msg_id in reversed(msg_ids[-150:]):
                res, msg_data = mail.fetch(msg_id, '(RFC822)')
                if res == "OK":
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    sender = decode_mime_words(msg.get("From", ""))
                    sender_lower = sender.lower()
                    
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
                            "날짜": date_, "회사명": company, "보낸이": sender,
                            "제목": subject, "본문요약": short_body.strip()
                        })
                        
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

def generate_calendar_html(df, base_date, act_types):
    idx = (base_date.weekday() + 1) % 7
    current_sunday = base_date - timedelta(days=idx)
    start_date = current_sunday - timedelta(weeks=2)
    
    html = "<table style='width:100%; border-collapse: collapse; font-family: sans-serif; font-size:13px;'>"
    html += "<tr style='background-color:#f0f2f6; text-align:center; height:40px;'>"
    html += "<th style='width:5%; color:#555;'>주차</th>"
    html += "<th style='width:13.5%; color:#e52528;'>일</th><th style='width:13.5%;'>월</th><th style='width:13.5%;'>화</th><th style='width:13.5%;'>수</th><th style='width:13.5%;'>목</th><th style='width:13.5%;'>금</th><th style='width:13.5%; color:#1890ff;'>토</th></tr>"
    
    curr_date = start_date
    today = pd.Timestamp(date.today())
    
    color_palettes = [
        (('#b5e0f5', '#333'), ('#1890ff', '#fff')), 
        (('#d9f7be', '#333'), ('#52c41a', '#fff')), 
        (('#efdbff', '#333'), ('#722ed1', '#fff')), 
        (('#ffe58f', '#333'), ('#faad14', '#fff')), 
        (('#ffd8bf', '#333'), ('#fa541c', '#fff')), 
    ]
    
    for _ in range(6):
        thursday = curr_date + timedelta(days=4)
        week_num = str(thursday.isocalendar()[1])
        
        html += "<tr>"
        html += f"<td style='border:1px solid #ddd; text-align:center; background-color:#fafafa; font-weight:bold; color:#777;'>{week_num}주</td>"
        
        for i in range(7):
            curr_ts = pd.Timestamp(curr_date)
            is_today = (curr_ts.date() == today.date())
            bg = "#fffbe6" if is_today else "#ffffff"
            text_color = "#e52528" if i==0 else ("#1890ff" if i==6 else "#262730")
            
            html += f"<td style='border:1px solid #ddd; height:120px; vertical-align:top; background-color:{bg}; padding:6px;'>"
            html += f"<div style='font-weight:bold; color:{text_color}; margin-bottom:4px;'>{curr_date.month}/{curr_date.day}</div>"
            
            if not df.empty:
                for _, task in df.iterrows():
                    start = task['시작일']
                    if pd.isna(start): continue
                    
                    end = task['목표일']
                    status = task['상태']
                    ttype = task['업무유형']
                    is_active = False
                    
                    if pd.notna(end):
                        if start <= curr_ts <= end:
                            is_active = True
                    else:
                        if status in ['진행중', '미정']:
                            if start <= curr_ts <= today:
                                is_active = True
                        else:
                            if start == curr_ts:
                                is_active = True
                                
                    if is_active:
                        if status == '지연':
                            bg_color, font_color = '#f5222d', '#ffffff'
                        else:
                            try:
                                c_idx = act_types.index(ttype) % len(color_palettes)
                            except:
                                c_idx = 2
                            pal = color_palettes[c_idx]
                            bg_color, font_color = pal[0] if status == '완료' else pal[1]

                        html += f"<div style='background-color:{bg_color}; color:{font_color}; border-radius:3px; padding:2px 5px; margin-bottom:2px; font-size:11px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;' title='{task['내용(주제)']}'>{task['내용(주제)']}</div>"
            html += "</td>"
            curr_date += timedelta(days=1)
        html += "</tr>"
    html += "</table>"
    return html

st.set_page_config(page_title="통합 업무 대시보드", layout="wide")
settings = load_settings()
df = load_data()

col_proj1, col_proj2 = st.columns([7, 3])
with col_proj1:
    st.title("🚢 통합 업무 대시보드")
with col_proj2:
    project_list = [p for p in settings.keys() if p != "gmail_settings"]
    selected_project = st.selectbox("📁 현재 프로젝트", project_list)
    menu = st.selectbox("메뉴 이동", ["📊 대시보드 (업무 관리)", "📩 이메일 연동함", "🗂️ 전체 항목 보기 (검색)", "⚙️ 관리자 설정 (분류/백업)"])

proj_act_types = settings[selected_project].get("activity_types", ["일반 업무"])
if not proj_act_types: proj_act_types = ["일반 업무"]
proj_categories = settings[selected_project]["categories"]
proj_tags = settings[selected_project]["tags"]

if menu == "📊 대시보드 (업무 관리)":
    
    st.sidebar.markdown("### 📝 새로운 업무 등록")
    # [오류 해결] st.sidebar.form 구조를 제거하여 실시간 연동(반응형)되도록 수정
    activity_type = st.sidebar.selectbox("업무 유형 선택", proj_act_types, key="new_act_type")
    main_cat = st.sidebar.selectbox("대분류", list(proj_categories.keys()) if proj_categories else ["없음"], key="new_main_cat")
    
    # 대분류 선택 시 실시간으로 옵션이 바뀝니다.
    sub_cat_options = proj_categories.get(main_cat, ["없음"]) if proj_categories else ["없음"]
    sub_cat = st.sidebar.selectbox("중분류", sub_cat_options, key="new_sub_cat")
    
    start_date = st.sidebar.date_input("시작일", date.today(), key="new_start_date")
    target_date = st.sidebar.date_input("목표일", date.today(), key="new_target_date")
    
    if activity_type == "회의 진행":
        location = st.sidebar.text_input("장소", key="new_loc")
        people = st.sidebar.text_input("참석자 / 관련자", key="new_ppl")
        content = st.sidebar.text_input("주제", key="new_content1")
        note = st.sidebar.text_area("회의록 요약", key="new_note1")
    else:
        location = "-"
        people = st.sidebar.text_input("관련자/송수신자", key="new_ppl2")
        content = st.sidebar.text_area("내용", key="new_content2")
        note = st.sidebar.text_input("비고", key="new_note2")
        
    tags = st.sidebar.multiselect("태그", proj_tags, key="new_tags")
    drive_link = st.sidebar.text_input("자료 링크 🔗", key="new_link")
    
    existing_tasks = df[df['프로젝트'] == selected_project]['내용(주제)'].dropna().unique().tolist()
    related_task = st.sidebar.selectbox("관련 이전 메일/업무 (선택)", ["없음"] + existing_tasks, key="new_related")
    
    if st.sidebar.button("등록하기 (기본: 진행중)", use_container_width=True, type="primary"):
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
        st.sidebar.success("성공적으로 등록되었습니다.")
        st.rerun()

    project_df = df[df['프로젝트'] == selected_project].copy()
    
    tab1, tab2 = st.tabs(["🗓️ 월간 캘린더 (실전 6주)", "📋 집중 업무 표 (진행중/지연)"])

    with tab1:
        st.subheader("업무 일정 캘린더")
        col_cal1, col_cal2 = st.columns([3, 7])
        with col_cal1:
            st.date_input("조회 기준일", key='cal_base_date')
            st.button("🎯 오늘로 복귀", on_click=set_today)
        
        calendar_html = generate_calendar_html(project_df, st.session_state.cal_base_date, proj_act_types)
        st.markdown(calendar_html, unsafe_allow_html=True)

    with tab2:
        st.subheader("업무 표 (완료 항목 제외, ◻️ 체크박스를 클릭하여 수정)")
        selected_filter_tags = st.multiselect("조회할 태그 필터", proj_tags)
        
        display_df = project_df[project_df['상태'] != '완료'].copy()
        
        if selected_filter_tags:
            pattern = '|'.join(selected_filter_tags)
            display_df = display_df[display_df['태그'].str.contains(pattern, na=False)]
            
        col_order = ['상태', '업무유형', '시작일', '목표일', '관련자(참석자/송수신자)', '내용(주제)', '연관업무ID', '드라이브_링크', '회의록_및_비고']
        display_df = display_df[col_order]
        
        event = st.dataframe(
            display_df,
            column_config={"드라이브_링크": st.column_config.LinkColumn("자료 링크")},
            on_select="rerun", selection_mode="single-row", use_container_width=True, hide_index=True
        )
        
        if len(event.selection.rows) > 0:
            selected_row_idx = event.selection.rows[0]
            actual_idx = display_df.index[selected_row_idx]
            task_data = project_df.loc[actual_idx]
            
            st.markdown("---")
            st.subheader("📝 선택한 업무 상세 보기 및 전체 수정")
            
            # [오류 해결] 편집 창에서도 폼 구조를 제거하여 분류가 실시간 연동되도록 수정
            with st.container(border=True):
                col_e1, col_e2, col_e3 = st.columns(3)
                edit_status = col_e1.selectbox("상태", ["진행중", "미정", "완료", "지연"], index=["진행중", "미정", "완료", "지연"].index(task_data['상태']), key="edit_status")
                
                type_idx = proj_act_types.index(task_data['업무유형']) if task_data['업무유형'] in proj_act_types else 0
                edit_type = col_e2.selectbox("업무유형", proj_act_types, index=type_idx, key="edit_type")
                
                s_date = task_data['시작일'] if pd.notna(task_data['시작일']) else date.today()
                t_date = task_data['목표일'] if pd.notna(task_data['목표일']) else date.today()
                r_date = task_data['실제완료일'] if pd.notna(task_data['실제완료일']) else None
                
                edit_s_date = col_e1.date_input("시작일", s_date, key="edit_s_date")
                edit_t_date = col_e2.date_input("목표일", t_date, key="edit_t_date")
                edit_r_date = col_e3.date_input("실제완료일", value=r_date, key="edit_r_date")

                col_e4, col_e5 = st.columns(2)
                main_cat_idx = list(proj_categories.keys()).index(task_data['대분류']) if task_data['대분류'] in proj_categories else 0
                edit_main_cat = col_e4.selectbox("대분류", list(proj_categories.keys()), index=main_cat_idx, key="edit_main_cat")
                
                # 수정 창에서도 대분류 변경 시 중분류 리스트가 즉각 연동됩니다.
                sub_cats = proj_categories.get(edit_main_cat, ["없음"])
                sub_cat_idx = sub_cats.index(task_data['중분류']) if task_data['중분류'] in sub_cats else 0
                edit_sub_cat = col_e5.selectbox("중분류", sub_cats, index=sub_cat_idx, key="edit_sub_cat")
                
                edit_loc = st.text_input("장소", str(task_data['장소']) if pd.notna(task_data['장소']) else "", key="edit_loc")
                edit_people = st.text_input("관련자(참석자/송수신자)", str(task_data['관련자(참석자/송수신자)']) if pd.notna(task_data['관련자(참석자/송수신자)']) else "", key="edit_people")
                edit_content = st.text_area("내용(주제)", str(task_data['내용(주제)']) if pd.notna(task_data['내용(주제)']) else "", key="edit_content")
                edit_note = st.text_area("회의록 및 비고", str(task_data['회의록_및_비고']) if pd.notna(task_data['회의록_및_비고']) else "", height=150, key="edit_note")
                edit_link = st.text_input("구글 드라이브 링크", str(task_data['드라이브_링크']) if pd.notna(task_data['드라이브_링크']) else "", key="edit_link")
                
                current_tags = [t.strip() for t in str(task_data['태그']).split(",")] if pd.notna(task_data['태그']) and task_data['태그'] else []
                valid_tags = [t for t in current_tags if t in proj_tags]
                edit_tags = st.multiselect("태그", proj_tags, default=valid_tags, key="edit_tags")
                
                if st.button("변경 사항 저장", type="primary"):
                    df.at[actual_idx, '상태'] = edit_status
                    df.at[actual_idx, '업무유형'] = edit_type
                    df.at[actual_idx, '대분류'] = edit_main_cat
                    df.at[actual_idx, '중분류'] = edit_sub_cat
                    df.at[actual_idx, '시작일'] = pd.to_datetime(edit_s_date)
                    df.at[actual_idx, '목표일'] = pd.to_datetime(edit_t_date) if edit_status != '미정' else pd.NaT
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

elif menu == "🗂️ 전체 항목 보기 (검색)":
    st.title("🗂️ 전체 업무 내역 및 검색")
    project_df = df[df['프로젝트'] == selected_project].copy()
    
    st.markdown("과거 완료된 업무를 포함한 모든 내역을 확인할 수 있습니다.")
    search_query = st.text_input("🔍 검색어 입력 (주제, 참석자, 장소, 태그 등)")
    
    if search_query:
        search_mask = (
            project_df['내용(주제)'].fillna('').str.contains(search_query, case=False) |
            project_df['관련자(참석자/송수신자)'].fillna('').str.contains(search_query, case=False) |
            project_df['장소'].fillna('').str.contains(search_query, case=False) |
            project_df['회의록_및_비고'].fillna('').str.contains(search_query, case=False) |
            project_df['태그'].fillna('').str.contains(search_query, case=False) |
            project_df['업무유형'].fillna('').str.contains(search_query, case=False)
        )
        filtered_all_df = project_df[search_mask]
    else:
        filtered_all_df = project_df
        
    col_order = ['상태', '업무유형', '시작일', '목표일', '실제완료일', '관련자(참석자/송수신자)', '내용(주제)', '태그', '드라이브_링크', '회의록_및_비고']
    
    st.dataframe(
        filtered_all_df[col_order],
        column_config={"드라이브_링크": st.column_config.LinkColumn("자료 링크")},
        use_container_width=True,
        hide_index=True
    )
    st.info(f"총 {len(filtered_all_df)}건의 업무가 조회되었습니다.")

elif menu == "📩 이메일 연동함":
    st.title("📩 수신된 이메일 일정 등록")
    g_settings = settings.get("gmail_settings", {})
    
    with st.expander("⚙️ Gmail 연동 설정 (한 번만 입력)"):
        g_email = st.text_input("Gmail 주소", value=g_settings.get("email", ""))
        g_app_pw = st.text_input("앱 비밀번호 (16자리)", value=g_settings.get("app_password", ""), type="password")
        g_target = st.text_input("고정 발신자 필터 (쉼표 구분)", value=g_settings.get("target_sender", "hblee@dh.co.kr, 이헌범"))
        
        if st.button("설정 저장"):
            settings["gmail_settings"] = {"email": g_email, "app_password": g_app_pw, "target_sender": g_target}
            save_settings(settings)
            st.success("메일 설정이 저장되었습니다.")
            
    if st.button("🔄 새 메일 불러오기", type="primary"):
        if g_email and g_app_pw and g_target:
            with st.spinner(f"최근 메일 중 발신자가 '{g_target}'인 메일을 검색 중입니다..."):
                emails = fetch_musv_emails(g_email, g_app_pw, g_target)
                if emails:
                    st.session_state.fetched_emails = emails
                    st.success(f"{len(emails)}개의 메일을 성공적으로 불러왔습니다.")
                else:
                    st.warning("최근 메일 중 해당 조건에 맞는 메일이 없습니다.")
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
                    m_tags = st.multiselect("태그 달기", proj_tags, default=[])
                    
                    existing_tasks = df[df['프로젝트'] == selected_project]['내용(주제)'].dropna().unique().tolist()
                    m_related = st.selectbox("관련 이전 업무", ["없음"] + existing_tasks)
                    
                    if st.form_submit_button("일정으로 등록"):
                        m_type = "메일/자료 송수신" if "메일/자료 송수신" in proj_act_types else proj_act_types[0]
                        m_cat = list(proj_categories.keys())[0] if proj_categories else "없음"
                        m_sub = proj_categories[m_cat][0] if m_cat != "없음" and proj_categories[m_cat] else "없음"
                        
                        new_row = {
                            "프로젝트": selected_project, "업무유형": m_type,
                            "대분류": m_cat, "중분류": m_sub,
                            "시작일": pd.to_datetime(date.today()), 
                            "목표일": pd.to_datetime(m_date) if m_status != "미정" else pd.NaT, 
                            "실제완료일": pd.NaT,
                            "장소": "-", "관련자(참석자/송수신자)": email_data['회사명'], "내용(주제)": email_data['제목'], 
                            "회의록_및_비고": email_data['본문요약'], "태그": ", ".join(m_tags), "상태": m_status, 
                            "드라이브_링크": "", "연관업무ID": m_related if m_related != "없음" else ""
                        }
                        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(df)
                        st.success("달력과 표에 등록되었습니다!")

elif menu == "⚙️ 관리자 설정 (분류/백업)":
    st.title("⚙️ 시스템 관리자 페이지")
    
    st.markdown("### 💾 시스템 데이터 백업 및 복구")
    st.info("시스템 업데이트 전, 반드시 '현재 데이터 저장'을 눌러 백업 파일을 보관해 주세요.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("**1. 현재 데이터 저장 (백업)**")
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "rb") as file:
                st.download_button(label="⬇️ CSV 다운로드", data=file, file_name=f"MUSV_업무데이터_백업_{date.today()}.csv", mime="text/csv", use_container_width=True)
    with col_b2:
        st.markdown("**2. 백업 파일 불러오기 (복구)**")
        uploaded_file = st.file_uploader("저장해둔 CSV 파일을 선택하세요.", type=["csv"], label_visibility="collapsed")
        if uploaded_file is not None:
            if st.button("데이터 복구 실행", use_container_width=True, type="primary"):
                try:
                    df_uploaded = pd.read_csv(uploaded_file)
                    df_uploaded.to_csv(DATA_FILE, index=False)
                    st.success("성공적으로 데이터를 불러왔습니다! 대시보드 탭으로 이동하세요.")
                except Exception as e:
                    st.error(f"데이터 복구 실패: {e}")
                    
    st.markdown("---")
    
    st.subheader(f"🛠️ [{selected_project}] 업무유형, 분류, 태그 관리")
    st.info("💡 아래 표의 빈 칸을 클릭해 새로운 항목을 자유롭게 추가하거나 기존 텍스트를 바로 수정하세요. 행 가장 왼쪽의 영역을 선택하고 키보드 Delete 키를 누르면 삭제됩니다.")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    
    with col_s1:
        st.markdown("**1. 업무 유형 관리**")
        act_df = pd.DataFrame(proj_act_types, columns=["업무유형"])
        new_act_df = st.data_editor(act_df, num_rows="dynamic", key="edit_act", use_container_width=True)
        if st.button("업무 유형 저장"):
            settings[selected_project]["activity_types"] = new_act_df["업무유형"].dropna().astype(str).str.strip().tolist()
            save_settings(settings)
            st.success("저장 완료")
            st.rerun()
            
    with col_s2:
        st.markdown("**2. 태그 관리**")
        tag_df = pd.DataFrame(proj_tags, columns=["태그"])
        new_tag_df = st.data_editor(tag_df, num_rows="dynamic", key="edit_tag", use_container_width=True)
        if st.button("태그 저장"):
            settings[selected_project]["tags"] = new_tag_df["태그"].dropna().astype(str).str.strip().tolist()
            save_settings(settings)
            st.success("저장 완료")
            st.rerun()
            
    with col_s3:
        st.markdown("**3. 분류 체계 관리**")
        cat_list = []
        for m_cat, sub_cats in proj_categories.items():
            if not sub_cats:
                cat_list.append({"대분류": m_cat, "중분류": ""})
            for s_cat in sub_cats:
                cat_list.append({"대분류": m_cat, "중분류": s_cat})
        cat_df = pd.DataFrame(cat_list) if cat_list else pd.DataFrame(columns=["대분류", "중분류"])
        
        new_cat_df = st.data_editor(cat_df, num_rows="dynamic", key="edit_cat", use_container_width=True)
        if st.button("분류 체계 저장"):
            new_cats = {}
            for _, row in new_cat_df.iterrows():
                m = str(row["대분류"]).strip() if pd.notna(row["대분류"]) else ""
                s = str(row["중분류"]).strip() if pd.notna(row["중분류"]) else ""
                if not m: continue
                if m not in new_cats:
                    new_cats[m] = []
                if s and s not in new_cats[m]:
                    new_cats[m].append(s)
            settings[selected_project]["categories"] = new_cats
            save_settings(settings)
            st.success("저장 완료")
            st.rerun()

    st.markdown("---")
    st.subheader("📁 신규 프로젝트 생성")
    new_project = st.text_input("새로운 프로젝트 이름")
    if st.button("프로젝트 생성"):
        if new_project and new_project not in settings:
            settings[new_project] = {"categories": {}, "tags": [], "weekly_reports": {}, "activity_types": ["일반 업무"]}
            save_settings(settings)
            st.success("생성 완료")
            st.rerun()
