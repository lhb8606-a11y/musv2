import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import os
import json

# 1. 파일 경로 설정
DATA_FILE = 'all_tasks.csv'
SETTINGS_FILE = 'settings.json'

# 초기 기본 세팅 (파일이 없을 경우 생성)
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
                 "히스토리안서버", "극동선박설계", "유일조선소", "PANEL", "I/O", "통신", "한화시스템", "MS", "MRC", "NOG"]
    }
}

# 2. 데이터 및 설정 로드/저장 함수
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
        cols = ["프로젝트", "대분류", "중분류", "시작일", "종료일", "수신/발신", "내용", "태그", "완료여부", "비고"]
        return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# 3. 앱 기본 설정
st.set_page_config(page_title="PM 통합 업무 대시보드", layout="wide")
settings = load_settings()
df = load_data()

# 4. 사이드바 - 프로젝트 및 메뉴 선택
st.sidebar.title("🛠️ PM 컨트롤 패널")
menu = st.sidebar.radio("메뉴 이동", ["📊 대시보드 (업무 관리)", "⚙️ 관리자 설정 (분류/태그)"])

project_list = list(settings.keys())
selected_project = st.sidebar.selectbox("📁 현재 프로젝트 선택", project_list)

proj_categories = settings[selected_project]["categories"]
proj_tags = settings[selected_project]["tags"]

# 5. 메인 로직 분기
if menu == "📊 대시보드 (업무 관리)":
    st.title(f"🚢 {selected_project} 통합 업무 대시보드")
    
    # 신규 업무 입력 폼 (선택된 프로젝트의 분류/태그 연동)
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"[{selected_project}] 업무 추가")
    
    if proj_categories:
        main_cat = st.sidebar.selectbox("대분류", list(proj_categories.keys()))
        sub_cat = st.sidebar.selectbox("중분류", proj_categories[main_cat] if proj_categories[main_cat] else ["없음"])
    else:
        main_cat, sub_cat = "설정 필요", "설정 필요"
        st.sidebar.warning("관리자 설정에서 분류를 추가해주세요.")

    col1, col2 = st.sidebar.columns(2)
    start_date = col1.date_input("시작일", date.today())
    end_date = col2.date_input("종료일", date.today())
    
    send_recv = st.sidebar.selectbox("수신/발신", ["수신", "발신", "회의", "내부", "일정"])
    content = st.sidebar.text_area("업무 내용")
    tags = st.sidebar.multiselect("태그 선택", proj_tags)
    note = st.sidebar.text_input("비고/결과물 요약")
    
    if st.sidebar.button("일정 등록하기"):
        new_row = {
            "프로젝트": selected_project, "대분류": main_cat, "중분류": sub_cat, 
            "시작일": str(start_date), "종료일": str(end_date),
            "수신/발신": send_recv, "내용": content, 
            "태그": ", ".join(tags), "완료여부": "미완료", "비고": note
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.sidebar.success("성공적으로 등록되었습니다.")
        st.rerun()

    # 현재 프로젝트 데이터만 필터링
    project_df = df[df['프로젝트'] == selected_project].copy()

    tab1, tab2 = st.tabs(["🗓️ 일정 캘린더 (타임라인)", "📋 전체 업무 상세 표"])

    with tab1:
        if not project_df.empty:
            timeline_df = project_df.copy()
            timeline_df['시작일'] = pd.to_datetime(timeline_df['시작일'])
            timeline_df['시각화_종료일'] = pd.to_datetime(timeline_df['종료일']) + pd.Timedelta(days=1)
            
            fig = px.timeline(
                timeline_df, x_start="시작일", x_end="시각화_종료일", y="내용", color="대분류",
                hover_data=["중분류", "태그", "완료여부", "종료일"], title=f"{selected_project} 업무 진행 기간"
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(xaxis_title="날짜", yaxis_title="업무 내용", height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("등록된 일정이 없습니다.")

    with tab2:
        selected_filter_tags = st.multiselect("조회할 태그 필터", proj_tags)
        if selected_filter_tags:
            pattern = '|'.join(selected_filter_tags)
            project_df = project_df[project_df['태그'].str.contains(pattern, na=False)]
        
        edited_df = st.data_editor(
            project_df,
            column_config={"완료여부": st.column_config.SelectboxColumn("완료여부", options=["미완료", "완료"])},
            disabled=["프로젝트", "대분류", "중분류", "시작일", "종료일", "수신/발신", "내용", "태그", "비고"],
            use_container_width=True, hide_index=True
        )
        
        # 수정 발생 시 전체 df에 업데이트
        if not edited_df.equals(project_df):
            df.update(edited_df)
            save_data(df)
            st.rerun()

elif menu == "⚙️ 관리자 설정 (분류/태그)":
    st.title("⚙️ 시스템 관리자 페이지")
    
    st.subheader("1. 신규 프로젝트 생성")
    new_project = st.text_input("새로운 프로젝트 이름 (예: MUSV-3, 다목적해상드론)")
    if st.button("프로젝트 생성"):
        if new_project and new_project not in settings:
            settings[new_project] = {"categories": {}, "tags": []}
            save_settings(settings)
            st.success(f"'{new_project}' 프로젝트가 생성되었습니다.")
            st.rerun()
        elif new_project in settings:
            st.warning("이미 존재하는 프로젝트입니다.")

    st.markdown("---")
    st.subheader(f"2. [{selected_project}] 분류 체계 관리")
    
    col_main, col_sub = st.columns(2)
    with col_main:
        st.markdown("**새로운 대분류 추가**")
        new_main_cat = st.text_input("대분류명 입력 (예: 6. 테스트)")
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
    new_tag = st.text_input("새로운 태그 입력 (예: 공장수락시험, 납기지연)")
    if st.button("태그 추가"):
        if new_tag and new_tag not in settings[selected_project]["tags"]:
            settings[selected_project]["tags"].append(new_tag)
            save_settings(settings)
            st.success("태그가 추가되었습니다.")
            st.rerun()
    
    st.markdown("**현재 프로젝트의 등록된 태그 목록:**")
    st.write(", ".join(proj_tags) if proj_tags else "등록된 태그가 없습니다.")
