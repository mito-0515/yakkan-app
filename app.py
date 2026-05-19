import streamlit as st
import pdfplumber
import io
from google import genai

st.set_page_config(page_title="約款 有無責判定アプリ", page_icon="📋", layout="wide")

st.title("📋 約款 有無責判定アプリ")
st.caption("D&O保険などの約款PDFをアップロードして、有責・無責を自動判定します")

with st.sidebar:
    st.header("⚙️ 設定")
    api_key = st.text_input("Gemini APIキー", type="password", placeholder="AIza...")
    st.caption("Google AI Studioで取得したAPIキーを入力してください")
    st.divider()
    st.markdown("**使い方**")
    st.markdown("1. APIキーを入力")
    st.markdown("2. 約款PDFをアップロード（最大3社）")
    st.markdown("3. 質問を入力して「判定する」を押す")

if not api_key:
    st.info("👈 左のサイドバーにGemini APIキーを入力してください")
    st.stop()

def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

st.subheader("① 約款PDFのアップロード（最大3社）")

cols = st.columns(3)
companies = []
texts = []

labels = ["1社目", "2社目", "3社目"]
for i, col in enumerate(cols):
    with col:
        name = st.text_input(f"保険会社名（{labels[i]}）", key=f"name_{i}", placeholder="例：明治安田")
        pdf = st.file_uploader(f"約款PDF（{labels[i]}）", type="pdf", key=f"pdf_{i}")
        if name and pdf:
            companies.append(name)
            texts.append(pdf)

if not companies:
    st.warning("保険会社名とPDFをセットで入力してください（1社以上）")
    st.stop()

st.success(f"✅ {len(companies)}社の約款が読み込まれています：{' / '.join(companies)}")

st.subheader("② 質問を入力してください")
question = st.text_area(
    "有責・無責を判定したいケースを入力",
    placeholder="例：役員の配偶者から損害賠償請求された場合、保険金は支払われますか？",
    height=100
)

if st.button("🔍 判定する", type="primary", disabled=not question):
    client = genai.Client(api_key=api_key)

    st.subheader("③ 判定結果")
    result_cols = st.columns(len(companies))

    for i, (company, pdf_file) in enumerate(zip(companies, texts)):
        with result_cols[i]:
            st.markdown(f"### 🏢 {company}")
            with st.spinner("約款を分析中..."):
                try:
                    pdf_text = extract_text_from_pdf(pdf_file)

                    if not pdf_text.strip():
                        st.error("PDFからテキストを抽出できませんでした。スキャンPDFの場合は対応しておりません。")
                        continue

                    prompt = f"""あなたは保険約款の専門家です。
以下の保険約款の内容を精読し、質問に対して有責・無責を判定してください。

【約款内容】
{pdf_text[:30000]}

【質問】
{question}

【回答形式】
## 判定
**有責** または **無責** または **条件付き有責** と明記してください。

## 根拠条文
該当する条項番号と条文の内容を引用してください。

## 理由
なぜその判定になるか、わかりやすく説明してください。

## 補足
例外・特約・注意点があれば記載してください。

必ず日本語で回答してください。"""

                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"エラーが発生しました：{e}")

    if len(companies) > 1:
        st.divider()
        st.subheader("④ 各社比較まとめ")
        st.info("上記の各社判定結果を参照して、各社の有責・無責と根拠の違いを整理してください。")
