import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px
import os

# 1. 카테고리 및 태그 설정
DATA_FILE = 'musv_tasks.csv'
TAGS_FILE = 'musv_tags.txt'

# 요청하신 5대 분류 완벽 반영
CATEGORIES = {
    "1. 개요": ["1-1. 일정", "1-2. 회의"],
    "2. BCC": ["2-1. BCC", "2-2. 사급자재", "2-3. ECS PC", "2-4. 모니터"],
    "3. DAU": ["3-1. DAU PANEL", "3-2. DAU & HISTORIAN", "3-3. UPS", "3-4. ECS PLC 프로그램"],
    "4. KR": ["4-1. 제출자료"],
    "5. 프로그램": ["5-1. 컨셉 다이어그램", "5-2. ECS PLC", "5-3. ECS PC", "5-4. ECS HMI", "5-5. 임무콘솔", "5-6. DAU & HISTORIAN", "5-7. ETC."]
}

INITIAL_TAGS = [
    "DAU", "BCC", "사급자재", "UPS", "ECS PC", "ECS PLC", "ECS 모니터", "DAU PANEL", 
    "히스토리안서버", "극동선박설계", "유일조선소", "PANEL", "I/O", "통신", "한화시스템", "MS", "MRC", "NOG"
]

# 2. 파일 로드 및 저장 함수
def load_tags():
    if os.path.exists(TAGS_FILE):
        with open(TAGS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    else:
        with open(TAGS_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(INITIAL_TAGS))
        return INITIAL_TAGS

def save_tag(new_tag):
    with open(TAGS_FILE, 'a', encoding='utf-8') as f:
        f.write(f'\n{new_tag}')

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        cols = ["대분류", "중분류", "시작일", "종료일", "수신/발신", "내용", "태그", "완료여부", "비고"]
        return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# 3. 앱 화면 구성
st.set_page_config(page_title="MUSV PM Dashboard", layout="wide")
st.title("🚢 MUSV 통합 업무 관리 캘린더 & 표")

current_tags = load_tags()
df = load_data()

# 사이드바 1: 웹에서 즉시 새로운 태그 추가
with st.sidebar.expander("🏷️ 새로운 태그 추가하기"):
    new_tag_input = st.text_input("새로운 업체명 또는 키워드 입력")
    if st.button("태그 저장"):
        if new_tag_input and new_tag_input not in current_tags:
            save_tag(new_tag_input)
            st.success(f"'{new_tag_input}' 태그가 추가되었습니다!")
            st.rerun()
        elif new_tag_input in current_tags:
            st.warning("이미 존재하는 태그입니다.")

# 사이드바 2: 신규 업무 입력 폼 (form 제거하여 실시간 연동 활성화)
st.sidebar.subheader("새로운 업무 추가")

# 대분류 선택 시 즉시 화면이 갱신되며 중분류가 업데이트 됩니다.
main_cat = st.sidebar.selectbox("대분류", list(CATEGORIES.keys()))
sub_cat = st.sidebar.selectbox("중분류", CATEGORIES[main_cat])

col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("시작일 (작성일)", date.today())
end_date = col2.date_input("종료일 (마감일)", date.today())

send_recv = st.sidebar.selectbox("수신/발신", ["수신", "발신", "회의", "내부", "일정"])
content = st.sidebar.text_area("업무 내용 (누구와 어디서 무엇을, 요청 자료 등)")
tags = st.sidebar.multiselect("태그 선택", current_tags)
note = st.sidebar.text_input("비고/결과물 요약")

# 버튼 클릭 시 데이터 저장
if st.sidebar.button("일정 등록하기"):
    new_row = {
        "대분류": main_cat, "중분류": sub_cat, 
        "시작일": str(start_date), "종료일": str(end_date),
        "수신/발신": send_recv, "내용": content, 
        "태그": ", ".join(tags), "완료여부": "미완료", "비고": note
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    st.sidebar.success("업무가 성공적으로 등록되었습니다.")
    st.rerun()

# 4. 메인 화면 탭 구성
tab1, tab2 = st.tabs(["🗓️ 일정 캘린더 (타임라인)", "📋 전체 업무 상세 표"])

# 탭 1: 삼성 캘린더 형태의 타임라인 차트
with tab1:
    st.subheader("진행 일정 한눈에 보기")
    if not df.empty:
        timeline_df = df.copy()
        timeline_df['시작일'] = pd.to_datetime(timeline_df['시작일'])
        timeline_df['시각화_종료일'] = pd.to_datetime(timeline_df['종료일']) + pd.Timedelta(days=1)
        
        fig = px.timeline(
            timeline_df, 
            x_start="시작일", 
            x_end="시각화_종료일", 
            y="내용", 
            color="대분류",
            hover_data=["중분류", "태그", "완료여부", "종료일"],
            title="대분류별 MUSV 업무 진행 기간"
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis_title="날짜", yaxis_title="업무 내용", height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("등록된 일정이 없습니다. 좌측 메뉴에서 일정을 추가해 주세요.")

# 탭 2: 기존 업무표 및 완료 처리
with tab2:
    st.subheader("업무 상세 표 및 상태 수정")
    selected_tags = st.multiselect("조회할 태그를 선택하세요", current_tags, key="filter")
    filtered_df = df.copy()
    if selected_tags:
        pattern = '|'.join(selected_tags)
        filtered_df = filtered_df[filtered_df['태그'].str.contains(pattern, na=False)]
    
    edited_df = st.data_editor(
        filtered_df,
        column_config={
            "완료여부": st.column_config.SelectboxColumn("완료여부", options=["미완료", "완료"])
        },
        disabled=["대분류", "중분류", "시작일", "종료일", "수신/발신", "내용", "태그", "비고"],
        use_container_width=True,
        hide_index=True
    )
    
    if not edited_df.equals(filtered_df):
        df.update(edited_df)
        save_data(df)
        st.rerun()
