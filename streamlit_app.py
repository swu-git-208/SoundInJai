import streamlit as st
import pandas as pd
from datetime import datetime
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="เสียงในใจ", layout="wide")

# ─── LOAD THAI SENTIMENT PIPELINE ──────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_thai_pipeline():
    model_name = "phoner45/wangchan-sentiment-thai-text-model"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model     = AutoModelForSequenceClassification.from_pretrained(model_name)
    return pipeline("text-classification", model=model, tokenizer=tokenizer)

sentiment_pipe = load_thai_pipeline()

# ─── HELPERS ────────────────────────────────────────────────────────────────────
DATA_FILE = "diary_records.csv"

def analyze_sentiment(text: str):
    result = sentiment_pipe(text)[0]
    return result["label"], result["score"]

def load_data():
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=["date","text","sentiment","score"]) \
          .to_csv(DATA_FILE, index=False)
    return pd.read_csv(DATA_FILE, parse_dates=["date"])

def save_entry(date, text, sentiment, score):
    df = load_data()
    # เพิ่มแถวใหม่
    df.loc[len(df)] = {
        "date": date, "text": text,
        "sentiment": sentiment, "score": score
    }
    df.to_csv(DATA_FILE, index=False)

# ─── STREAMLIT LAYOUT ──────────────────────────────────────────────────────────
st.title("🧠 เสียงในใจ — Diary Sentiment Tracker")
st.write("บันทึกไดอารี่ แล้วระบบจะวิเคราะห์อารมณ์ภาษาไทยให้ทันที")

col1, col2 = st.columns([1,2])

with col1:
    st.header("✍️ เขียนไดอารี่วันนี้")
    entry_date = st.date_input("วันที่", datetime.now().date())
    diary_text = st.text_area(
        "บันทึกความรู้สึก", height=200,
        placeholder="บอกสิ่งที่เกิดขึ้นและอารมณ์ของคุณ…"
    )

    if st.button("💾 บันทึกและวิเคราะห์"):
        if diary_text.strip():
            with st.spinner("กำลังวิเคราะห์…"):
                label, score = analyze_sentiment(diary_text)
            save_entry(entry_date, diary_text, label, score)
            st.success(f"ผลการวิเคราะห์: **{label}** ({score:.0%})")
        else:
            st.error("กรุณาใส่ข้อความก่อน")

with col2:
    st.header("📊 สรุปแนวโน้มอารมณ์")
    df = load_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูล ลองเพิ่มไดอารี่แล้วกลับมาดูกราฟ")
    else:
        # ตั้ง date เป็น index และ resample
        df = df.sort_values("date").set_index("date")
        weekly = df["score"].resample("W-MON").mean().rename("avg_score")
        st.subheader("แนวโน้มคะแนนอารมณ์เฉลี่ยรายสัปดาห์")
        st.line_chart(weekly)

        st.subheader("บันทึกล่าสุด")
        recent = df.reset_index().tail(5)[["date","text","sentiment","score"]]
        recent["score"] = recent["score"].apply(lambda x: f"{x:.0%}")
        st.table(recent)

        st.subheader("📌 คำแนะนำสำหรับคุณ")
        last = df.iloc[-1]
        if last["sentiment"] == "NEGATIVE" and last["score"] >= 0.6:
            st.info("ลองฟังเพลงสบาย ๆ เพื่อผ่อนคลาย")
        elif last["sentiment"] == "POSITIVE":
            st.success("จด gratitude list เพื่อเสริมความสุข")
        else:
            st.warning("ลองเดินเล่นสั้น ๆ ในธรรมชาติ")
