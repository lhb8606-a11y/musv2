import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import os
import json

# 1. 파일 경로 설정 (구조 변경으로 인한 v2 적용)
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
        return pd.read_csv(DATA_FILE)
    else:
        # 데이터 구조 전면 개편 (관련자, 장소, 목표일, 실제완료일 추가)
        cols = ["프로젝트", "업무유형", "대분류", "중분류", "시작일", "목표일", "실제완료일", "장소", "관련자(참석자/송수신자)", "내용(주제)", "회의록_및_비고", "태그", "상태"]
        return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

st.set_page_config(page_title="PM 통합 업무 대시보드", layout="wide")
settings = load_settings()
df = load_data()

st.sidebar.title("🛠️ PM 컨트롤 패널")
menu = st.sidebar.radio("메뉴 이동", ["📊 대시보드 (업무 관리)", "⚙️ 관리자 설정 (분류/태그)"])

project_list = list(settings.keys())
selected_project = st.sidebar.selectbox("📁 현재 프로젝트 선택", project_list)
proj_categories = settings[selected_project]["categories"]
proj_tags = settings[selected_project]["tags"]

if menu == "📊 대시보드 (업무 관리)":
    st.title(f"🚢 {selected_project} 통합 업무 대시보드")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("새로운 업무 등록")
    
    # [핵심 1] 업무 유형에 따른 동적 폼 생성
    activity_type = st.sidebar.selectbox("업무 유형 선택", ["회의 진행", "메일/자료 송수신", "일반 업무 (설계/검토 등)"])
    
    main_cat = st.sidebar.selectbox("대분류", list(proj_categories.keys()))
    sub_cat = st.sidebar.selectbox("중분류", proj_categories[main_cat] if proj_categories[main_cat] else ["없음"])
    
    start_date = st.sidebar.date_input("시작일 (작성일)", date.today())
    target_date = st.sidebar.date_input("목표일 (예상 종료일)", date.today())
    
    # 업무 유형별 맞춤 입력 칸
    if activity_type == "회의 진행":
        location = st.sidebar.text_input("회의 장소 (예: 동화엔텍, 유일조선소)")
        people = st.sidebar.text_input("참석자 (예: 한화시스템 이태경 수석 등)")
        content = st.sidebar.text_input("회의 주제")
        note = st.sidebar.text_area("회의록 요약 (완료 후 표에서도 수정 가능)")
    elif activity_type == "메일/자료 송수신":
        location = "-"
        people = st.sidebar.text_input("송수신자 (예: 극동선박설계 배상권 전무)")
        content = st.sidebar.text_area("주고받은 메일/자료 내용")
        note = st.sidebar.text_input("비고 (첨부파일명 등)")
    else:
        location = "-"
        people = st.sidebar.text_input("담당자 / 관련자")
        content = st.sidebar.text_area("업무 내용 (H/W 설계, 도면 작성 등)")
        note = st.sidebar.text_input("비고")
        
    tags = st.sidebar.multiselect("태그 선택", proj_tags)
    
    if st.sidebar.button("등록하기 (기본: 진행중)"):
        new_row = {
            "프로젝트": selected_project, "업무유형": activity_type,
            "대분류": main_cat, "중분류": sub_cat, 
            "시작일": str(start_date), "목표일": str(target_date), "실제완료일": None,
            "장소": location, "관련자(참석자/송수신자)": people, "내용(주제)": content, 
            "회의록_및_비고": note, "태그": ", ".join(tags), "상태": "진행중"
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.sidebar.success("성공적으로 등록되었습니다.")
        st.rerun()

    project_df = df[df['프로젝트'] == selected_project].copy()

    tab1, tab2 = st.tabs(["📋 상세 업무 표 (진행 상태 & 회의록 수정)", "🗓️ 일정 캘린더 (타임라인)"])

    with tab1:
        st.subheader("업무 표 (더블 클릭하여 완료일 및 회의록 입력)")
        selected_filter_tags = st.multiselect("조회할 태그 필터", proj_tags)
        if selected_filter_tags:
            pattern = '|'.join(selected_filter_tags)
            project_df = project_df[project_df['태그'].str.contains(pattern, na=False)]
        
        # [핵심 2] Data Editor를 통한 달력(Date) 입력 및 진행상태 업데이트
        edited_df = st.data_editor(
            project_df,
            column_config={
                "상태": st.column_config.SelectboxColumn("상태", options=["진행중", "완료", "지연"]),
                "실제완료일": st.column_config.DateColumn("실제완료일 (달력선택)"),
                "회의록_및_비고": st.column_config.TextColumn("회의록_및_비고")
            },
            disabled=["프로젝트", "업무유형", "대분류", "중분류", "시작일", "목표일", "장소", "관련자(참석자/송수신자)", "내용(주제)", "태그"],
            use_container_width=True, hide_index=True
        )
        
        if not edited_df.equals(project_df):
            df.update(edited_df)
            save_data(df)
            st.rerun()

    with tab2:
        if not project_df.empty:
            timeline_df = project_df.copy()
            timeline_df['시작일'] = pd.to_datetime(timeline_df['시작일'])
            # 간트 차트는 '목표일'을 기준으로 막대를 생성합니다.
            timeline_df['시각화_종료일'] = pd.to_datetime(timeline_df['목표일']) + pd.Timedelta(days=1)
            
            fig = px.timeline(
                timeline_df, x_start="시작일", x_end="시각화_종료일", y="내용(주제)", color="상태",
                hover_data=["업무유형", "관련자(참석자/송수신자)", "목표일", "실제완료일"], 
                title=f"{selected_project} 전체 공정 타임라인"
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(xaxis_title="날짜", yaxis_title="업무", height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("등록된 일정이 없습니다.")

elif menu == "⚙️ 관리자 설정 (분류/태그)":
    st.title("⚙️ 시스템 관리자 페이지")
    # ... (기존과 동일한 프로젝트/분류/태그 관리 로직 유지)
    new_project = st.text_input("새로운 프로젝트 이름")
    if st.button("프로젝트 생성"):
        if new_project and new_project not in settings:
            settings[new_project] = {"categories": {}, "tags": []}
            save_settings(settings)
            st.success("생성 완료")
            st.rerun()
