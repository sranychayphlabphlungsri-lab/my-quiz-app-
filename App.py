import streamlit as st
import requests
import pypdf 
import re
import random
import io
import urllib3

# ตั้งค่าหน้าจอให้ดูเหมือนแอปมือถือ
st.set_page_config(page_title="Quiz App", page_icon="📝")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ใช้ cache เพื่อให้โหลด PDF ครั้งเดียว ไม่ต้องโหลดใหม่ทุกครั้งที่กดปุ่ม
@st.cache_data
def get_questions():
    url = "https://learning.mirdc.org.tw/banner/10A001/%E5%85%B1%E5%90%8C%E7%A7%91%E7%9B%AE-%E8%81%B7%E6%A5%AD%E5%AE%89%E5%85%A8%E8%A1%9B%E7%94%9F_900060A14.pdf"
    try:
        r = requests.get(url, timeout=30, verify=False)
        pdf_reader = pypdf.PdfReader(io.BytesIO(r.content))
        all_text = ""
        for page in pdf_reader.pages:
            t = page.extract_text()
            if t: all_text += t + "\n"
        
        pattern = re.compile(r'(\d+)\s*[.．]\s*[\(（]\s*([1234])\s*[\)）]')
        matches = list(pattern.finditer(all_text))
        
        questions = []
        for i in range(len(matches)):
            m = matches[i]
            q_id = m.group(1)
            q_ans = m.group(2)
            if q_id == "75": q_ans = "1" # แก้ไขเฉลยตามสั่ง
            
            start = m.end()
            end = matches[i+1].start() if i+1 < len(matches) else len(all_text)
            content = " ".join(re.sub(r'Page \d+ of \d+', '', all_text[start:end]).split())
            
            questions.append({'id': q_id, 'ans': q_ans, 'content': content})
        return questions
    except:
        return []

# --- ส่วนของการจัดการสถานะ (Session State) ---
if 'pool' not in st.session_state:
    st.session_state.pool = get_questions()
if 'current_q' not in st.session_state:
    st.session_state.current_q = None
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'total_done' not in st.session_state:
    st.session_state.total_done = 0

# --- หน้าตาเว็บ ---
st.title("📝 ทบทวนข้อสอบ")
st.write(f"📊 ทำไปแล้ว {st.session_state.total_done} ข้อ | เหลือ {len(st.session_state.pool)} ข้อ")

# ปุ่มเริ่มสุ่มข้อสอบ
if st.button("สุ่มข้อสอบข้อถัดไป 🎲") or st.session_state.current_q is None:
    if st.session_state.pool:
        st.session_state.current_q = random.choice(st.session_state.pool)
        st.session_state.answered = False
    else:
        st.success("เก่งมาก! ทำครบทุกข้อแล้ว 🎉")

# แสดงโจทย์
if st.session_state.current_q:
    q = st.session_state.current_q
    st.info(f"**ข้อที่ {q['id']}**")
    st.write(q['content'])
    
    # ส่วนการตอบ
    user_ans = st.radio("เลือกคำตอบ:", ["1", "2", "3", "4"], key=q['id'], horizontal=True)
    
    if st.button("ส่งคำตอบ"):
        if user_ans == q['ans']:
            st.success("✨ ถูกต้อง!")
            st.session_state.score += 1
        else:
            st.error(f"❌ ผิด... เฉลยคือข้อ ({q['ans']})")
        
        # ลบข้อที่ทำแล้วออกจาก pool
        st.session_state.pool = [item for item in st.session_state.pool if item['id'] != q['id']]
        st.session_state.total_done += 1
