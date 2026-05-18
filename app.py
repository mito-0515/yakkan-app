import streamlit as st
import google.generativeai as genai
import tempfile
import os

st.set_page_config(page_title="約款 有無責判定アプリ", page_icon="📋", layout="wide")

st.title("📋 約款 有無責判定アプリ")
st.caption("D&O保険などの約款PDFをアップロードして、有責・無責を自動判定します")

# サイドバー：APIキー入力
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

genai.configure(api_key=api_key)

# 約款アップロード
st.subheader("① 約款PDFのアップロード（最大3社）")

cols = st.columns(3)
companies = []
pdfs = []

labels = ["1社目", "2社目", "3社目"]
for i, col in enumerate(cols):
    with col:
        name = st.text_input(f"保険会社名（{labels[i]}）", key=f"name_{i}", placeholder="例：明治安田")
        pdf = st.file_uploader(f"約款PDF（{labels[i]}）", type="pdf", key=f"pdf_{i}")
        if name and pdf:
            companies.append(name)
            pdfs.append(pdf)

if not companies:
    st.warning("保険会社名とPDFをセットで入力してください（1社以上）")
    st.stop()

st.success(f"✅ {len(companies)}社の約款が読み込まれています：{' / '.join(companies)}")

# 質問入力
st.subheader("② 質問を入力してください")
question = st.text_area(
    "有責・無責を判定したいケースを入力",
    placeholder="例：役員の配偶者から損害賠償請求された場合、保険金は支払われますか？",
    height=100
)

# 判定実行
if st.button("🔍 判定する", type="primary", disabled=not question):
    model = genai.GenerativeModel("gemini-1.5-flash")

    st.subheader("③ 判定結果")
    result_cols = st.columns(len(companies))

    for i, (company, pdf_file) in enumerate(zip(companies, pdfs)):
        with result_cols[i]:
            st.markdown(f"### 🏢 {company}")
            with st.spinner("約款を分析中..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(pdf_file.read())
                    tmp_path = tmp.name

                try:
                    uploaded = genai.upload_file(tmp_path, mime_type="application/pdf")

                    prompt = f"""あなたは保険約款の専門家です。
添付の保険約款PDFを精読し、以下の質問に対して有責・無責を判定してください。

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

                    response = model.generate_content([uploaded, prompt])
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"エラーが発生しました：{e}")
                finally:
                    os.unlink(tmp_path)

    # 複数社の場合は比較まとめを表示
    if len(companies) > 1:
        st.divider()
        st.subheader("④ 各社比較まとめ")
        st.info("上記の各社判定結果を参照して、各社の有責・無責と根拠の違いを整理してください。")
