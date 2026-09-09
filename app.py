import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# 1. 기초 데이터 설정
DATA_FILE = 'musv_tasks.csv'
CATEGORIES = {
    "1. 개요": ["1-1. 일정", "1-2. 회의"],
    "2. BCC": ["2-1. BCC", "2-2. 사급자재", "2-3. ECS PC", "2-4. 모니터"],
    "3. DAU": ["3-1. DAU PANEL", "3-2. DAU & HISTORIAN", "3-3. UPS", "3-4. ECS PLC 프로그램"],
    "4. KR": ["4-1. 제출자료"],
    "5. 프로그램": ["5-1. 컨셉 다이어그램", "5-2. ECS PLC", "5-3. ECS PC", "5-4. ECS HMI", "5-5. 임무콘솔", "5-6. DAU & HISTORIAN", "5-7. ETC."]
}
TAGS = ["한화시스템", "한화엔진", "한화오션", "유일조선소", "극동선박설계", "도면", "회의", "자재", "선급", "요청", "수신", "발신"]

# 2. 데이터 로드 및 저장 함수
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        cols = ["대분류", "중분류", "날짜", "수신/발신", "내용", "마감날짜", "태그", "완료여부", "비고"]
        return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

st.set_page_config(page_title="MUSV PM Dashboard", layout="wide")
st.title("🚢 MUSV 통합 업무 관리 대시보드")

df = load_data()

# 3. 신규 업무 입력 폼 (달력 연동)
with st.sidebar.form("task_form"):
    st.subheader("새로운 업무 추가 (달력 연동)")
    date_input = st.date_input("날짜", date.today())
    main_cat = st.selectbox("대분류", list(CATEGORIES.keys()))
    sub_cat = st.selectbox("중분류", CATEGORIES[main_cat])
    send_recv = st.selectbox("수신/발신", ["수신", "발신", "회의", "내부"])
    content = st.text_area("내용 (누구에게, 어떤 자료 등)")
    deadline = st.date_input("마감날짜", date.today())
    tags = st.multiselect("태그 (다중 선택)", TAGS)
    note = st.text_input("비고/결과물")
    
    submitted = st.form_submit_button("추가하기")
    if submitted:
        new_row = {
            "대분류": main_cat, "중분류": sub_cat, "날짜": str(date_input),
            "수신/발신": send_recv, "내용": content, "마감날짜": str(deadline),
            "태그": ", ".join(tags), "완료여부": "미완료", "비고": note
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("성공적으로 추가되었습니다.")

# 4. 화면 탭 구성
tab1, tab2 = st.tabs(["📋 상세 업무 일지", "🚨 미완료 및 지연 업무 (자동 이월)"])

with tab1:
    st.subheader("전체 업무 조회 및 필터링")
    # 태그 필터링 기능
    selected_tags = st.multiselect("조회할 태그를 선택하세요", TAGS, key="filter")
    filtered_df = df.copy()
    if selected_tags:
        # 선택된 태그가 하나라도 포함된 행 필터링
        pattern = '|'.join(selected_tags)
        filtered_df = filtered_df[filtered_df['태그'].str.contains(pattern, na=False)]
    
    # 완료여부에 따른 취소선 스타일 적용 함수
    def apply_strikethrough(val):
        return 'text-decoration: line-through; color: gray;' if val == '완료' else ''

    # 데이터 에디터를 통해 표에서 직접 완료여부 수정 가능
    edited_df = st.data_editor(
        filtered_df,
        column_config={
            "완료여부": st.column_config.SelectboxColumn("완료여부", options=["미완료", "완료"])
        },
        disabled=["대분류", "중분류", "날짜", "수신/발신", "내용", "마감날짜", "태그", "비고"],
        use_container_width=True,
        hide_index=True
    )
    
    # 수정된 상태 저장
    if not edited_df.equals(filtered_df):
        df.update(edited_df)
        save_data(df)
        st.rerun()

with tab2:
    st.subheader("진행 중인 업무 목록")
    # 마감일이 지났거나 당일인 미완료 업무 자동 추출 (이월 기능)
    pending_df = df[df['완료여부'] == '미완료']
    st.dataframe(pending_df, use_container_width=True, hide_index=True)
