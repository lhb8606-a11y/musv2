import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os
import json

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
                 "히스토리안서버", "극동선박설계", "유일조선소", "한화시스템", "한화엔진", "한화오션", "KR선급"]
    }
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        cols = ["프로젝트", "업무유형", "대분류", "중분류", "시작일", "목표일", "실제완료일", "장소", "관련자(참석자/송수신자)", "내용(주제)", "회의록_및_비고", "태그", "상태"]
        df = pd.DataFrame(columns=cols)
    
    date_columns = ['시작일', '목표일', '실제완료일']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# [핵심] 달력 오늘 날짜 복귀를 위한 세션 상태 관리
if 'cal_base_date' not in st.session_state:
    st.session_state.cal_base_date = date.today()

def set_today():
    st.session_state.cal_base_date = date.today()

# [핵심] 과거 2주 ~ 미래 3주 (총 6주) 달력 렌더링 함수
def generate_calendar_html(df, base_date):
    # 기준일이 속한 주의 일요일 계산
    idx = (base_date.weekday() + 1) % 7
    current_sunday = base_date - timedelta(days=idx)
    
    # 시작일을 현재 주차 일요일에서 2주 전으로 설정
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
        week_num = thursday.isocalendar()[1]
        
        html += "<tr>"
        html += f"<td style='border:1px solid #ddd; text-align:center; background-color:#fafafa; font-weight:bold; color:#777;'>{week_num}주</td>"
        
        for i in range(7):
            is_today = (curr_date == today)
            # 오늘 날짜는 배경색 하이라이트
            bg = "#e6f7ff" if is_today else "#ffffff"
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

st.sidebar.title("🛠️ PM 컨트롤 패널")
menu = st.sidebar.radio("메뉴 이동", ["📊 대시보드 (업무 관리)", "⚙️ 관리자 설정 (분류/태그)"])

project_list = list(settings.keys())
selected_project = st.sidebar.selectbox("📁 현재 프로젝트 선택", project_list)
proj_categories = settings[selected_project]["categories"]
proj_tags = settings[selected_project]["tags"]

if menu == "📊 대시보드 (업무 관리)":
    st.title("🚢 통합 업무 대시보드")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("새로운 업무 등록")
    activity_type = st.sidebar.selectbox("업무 유형 선택", ["회의 진행", "메일/자료 송수신", "일반 업무 (설계/검토 등)"])
    main_cat = st.sidebar.selectbox("대분류", list(proj_categories.keys()))
    sub_cat = st.sidebar.selectbox("중분류", proj_categories[main_cat] if proj_categories[main_cat] else ["없음"])
    
    start_date = st.sidebar.date_input("시작일 (작성일)", date.today())
    target_date = st.sidebar.date_input("목표일 (예상 종료일)", date.today())
    
    if activity_type == "회의 진행":
        location = st.sidebar.text_input("회의 장소")
        people = st.sidebar.text_input("참석자")
        content = st.sidebar.text_input("회의 주제")
        note = st.sidebar.text_area("회의록 요약")
    elif activity_type == "메일/자료 송수신":
        location = "-"
        people = st.sidebar.text_input("송수신자")
        content = st.sidebar.text_area("메일/자료 내용")
        note = st.sidebar.text_input("비고")
    else:
        location = "-"
        people = st.sidebar.text_input("담당자 / 관련자")
        content = st.sidebar.text_area("업무 내용")
        note = st.sidebar.text_input("비고")
        
    tags = st.sidebar.multiselect("태그 선택", proj_tags)
    
    if st.sidebar.button("등록하기 (기본: 진행중)"):
        new_row = {
            "프로젝트": selected_project, "업무유형": activity_type,
            "대분류": main_cat, "중분류": sub_cat, 
            "시작일": pd.to_datetime(start_date), "목표일": pd.to_datetime(target_date), "실제완료일": pd.NaT,
            "장소": location, "관련자(참석자/송수신자)": people, "내용(주제)": content, 
            "회의록_및_비고": note, "태그": ", ".join(tags), "상태": "진행중"
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.sidebar.success("성공적으로 등록되었습니다.")
        st.rerun()

    project_df = df[df['프로젝트'] == selected_project].copy()

    tab1, tab2 = st.tabs(["🗓️ 월간 캘린더 (실전 6주)", "📋 상세 업무 표 (진행 상태 & 회의록 수정)"])

    with tab1:
        st.subheader("업무 일정 캘린더")
        col_cal1, col_cal2, col_cal3 = st.columns([2, 1, 7])
        
        with col_cal1:
            # 세션 상태에 저장된 날짜를 기본값으로 사용
            st.date_input("조회 기준일 선택", key='cal_base_date')
        with col_cal2:
            st.write("") # 간격 맞춤
            st.write("")
            st.button("🎯 오늘로 바로 가기", on_click=set_today)
        
        # 선택된 날짜(과거2주 ~ 미래3주)를 기준으로 HTML 캘린더 렌더링
        calendar_html = generate_calendar_html(project_df, st.session_state.cal_base_date)
        st.markdown(calendar_html, unsafe_allow_html=True)

    with tab2:
        st.subheader("업무 표 (더블 클릭하여 완료일 및 회의록 입력)")
        selected_filter_tags = st.multiselect("조회할 태그 필터", proj_tags)
        
        display_df = project_df.copy()
        if selected_filter_tags:
            pattern = '|'.join(selected_filter_tags)
            display_df = display_df[display_df['태그'].str.contains(pattern, na=False)]
        
        edited_df = st.data_editor(
            display_df,
            column_config={
                "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "지연"]),
                "실제완료일": st.column_config.DateColumn("실제완료일 (달력선택)"),
                "회의록_및_비고": st.column_config.TextColumn("회의록_및_비고")
            },
            disabled=["프로젝트", "업무유형", "대분류", "중분류", "시작일", "목표일", "장소", "관련자(참석자/송수신자)", "내용(주제)", "태그"],
            use_container_width=True, hide_index=True
        )
        
        if not edited_df.equals(display_df):
            df.update(edited_df)
            save_data(df)
            st.rerun()

elif menu == "⚙️ 관리자 설정 (분류/태그)":
    st.title("⚙️ 시스템 관리자 페이지")
    new_project = st.text_input("새로운 프로젝트 이름")
    if st.button("프로젝트 생성"):
        if new_project and new_project not in settings:
            settings[new_project] = {"categories": {}, "tags": []}
            save_settings(settings)
            st.success("생성 완료")
            st.rerun()
            
    st.markdown("---")
    st.subheader(f"2. [{selected_project}] 분류 체계 관리")
    col_main, col_sub = st.columns(2)
    with col_main:
        st.markdown("**새로운 대분류 추가**")
        new_main_cat = st.text_input("대분류명 입력")
        if st.button("대분류 추가"):
            if new_main_cat and new_main_cat not in settings[selected_project]["categories"]:
                settings[selected_project]["categories"][new_main_cat] = []
                save_settings(settings)
                st.success("추가되었습니다.")
                st.rerun()
    with col_sub:
        st.markdown("**기존 대분류에 중분류 추가**")
        if proj_categories:
            target_main = st.selectbox("어느 대분류에 추가하시겠습니까?", list(proj_categories.keys()))
            new_sub_cat = st.text_input("중분류명 입력")
            if st.button("중분류 추가"):
                if new_sub_cat and new_sub_cat not in settings[selected_project]["categories"][target_main]:
                    settings[selected_project]["categories"][target_main].append(new_sub_cat)
                    save_settings(settings)
                    st.success("추가되었습니다.")
                    st.rerun()

    st.markdown("---")
    st.subheader(f"3. [{selected_project}] 태그 관리")
    new_tag = st.text_input("새로운 태그 입력")
    if st.button("태그 추가"):
        if new_tag and new_tag not in settings[selected_project]["tags"]:
            settings[selected_project]["tags"].append(new_tag)
            save_settings(settings)
            st.success("태그가 추가되었습니다.")
            st.rerun()
