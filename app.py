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
        week_num = thursday.isocalendar()[1]
        
        html += "<tr>"
        html += f"<td style='border:1px solid #ddd; text-align:center; background-color:#fafafa; font-weight:bold; color:#777;'>{week_num}주</td>"
        
        for i in range(7):
            is_today = (curr_date == today)
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

    tab1, tab2 = st.tabs(["🗓️ 월간 캘린더 (실전 6주)", "📋 상세 업무 표 (조회 및 전체 수정)"])

    with tab1:
        st.subheader("업무 일정 캘린더")
        col_cal1, col_cal2, col_cal3 = st.columns([2, 1, 7])
        with col_cal1:
            st.date_input("조회 기준일 선택", key='cal_base_date')
        with col_cal2:
            st.write("")
            st.write("")
            st.button("🎯 오늘로 바로 가기", on_click=set_today)
        
        calendar_html = generate_calendar_html(project_df, st.session_state.cal_base_date)
        st.markdown(calendar_html, unsafe_allow_html=True)

    with tab2:
        st.subheader("업무 표 (원하는 항목을 클릭하면 아래에서 전체 내용을 수정할 수 있습니다)")
        selected_filter_tags = st.multiselect("조회할 태그 필터", proj_tags)
        
        display_df = project_df.copy()
        if selected_filter_tags:
            pattern = '|'.join(selected_filter_tags)
            display_df = display_df[display_df['태그'].str.contains(pattern, na=False)]
            
        # [핵심 1] 열 순서 재배치 (상태를 제일 앞으로, 프로젝트를 제일 뒤로)
        col_order = ['상태', '업무유형', '대분류', '중분류', '시작일', '목표일', '실제완료일', 
                     '장소', '관련자(참석자/송수신자)', '내용(주제)', '회의록_및_비고', '태그', '프로젝트']
        
        # 프로젝트 열은 가장 뒤로 가고, 실제로 표출될 때는 생략해도 되지만 요청대로 맨 뒤로 배치합니다.
        display_df = display_df[col_order]
        
        # [핵심 2] 행을 클릭(선택)할 수 있는 대화형 데이터프레임
        event = st.dataframe(
            display_df,
            on_select="rerun",
            selection_mode="single-row",
            use_container_width=True,
            hide_index=True
        )
        
        # 행이 선택되었을 때 상세 수정 창 표시
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
                
                # 날짜 데이터 안전 처리
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
                
                # 기존 태그 복원
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
                    df.at[actual_idx, '태그'] = ", ".join(edit_tags)
                    
                    save_data(df)
                    st.success("업무 내용이 성공적으로 수정되었습니다.")
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
