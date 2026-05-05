import os
import streamlit as st
import pandas as pd
from utils.file_loader import load_file
from utils.preprocess import split_sentences
from utils.similarity import calculate_overall_similarity, calculate_local_similarity, classify_similarity, calculate_target_coverage
from utils.autocorrect import AutoCorrectConfig, CorrectionEngine
from utils.autocorrect.ai_engine import configure_ai, process_text_with_ai

API_KEY_FILE = "utils/autocorrect/data/api_key.txt"

def get_saved_apikey():
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            return f.read().strip()
    return ""

def save_apikey(key):
    with open(API_KEY_FILE, "w") as f:
        f.write(key)

# --- Page Configuration ---
st.set_page_config(
    page_title="Anti-Plagiarism Demo",
    page_icon="🔍",
    layout="wide"
)

# --- CSS Styling for Highlights ---
st.markdown("""
<style>
.highlight-high { background-color: #ffcccc; padding: 2px; border-radius: 3px; font-weight: bold; }
.highlight-medium { background-color: #ffe5b4; padding: 2px; border-radius: 3px; }
.highlight-low { background-color: #f0f2f6; padding: 2px; border-radius: 3px; }
.box { padding: 10px; border-radius: 5px; border: 1px solid #ddd; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

def render_highlighted_text(text: str, segments: list) -> str:
    if not segments:
        return text
        
    segments.sort(key=lambda x: x[0])
    merged = [segments[0]]
    for current in segments[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
            
    last_idx = 0
    html = ""
    for start, end in merged:
        html += text[last_idx:start]
        html += f"<span class='highlight-high'>{text[start:end]}</span>"
        last_idx = end
    html += text[last_idx:]
    
    return html.replace("\n", "<br>")

def render_side_by_side(local_results, low_thresh, high_thresh):
    """Render side-by-side local matches in the UI for 1 vs 1 mode."""
    st.write("**Matched Pair View** (Showing Reference segments and their best match from the Target)")
    for res in local_results:
        score = res['similarity_score']
        sim_class = classify_similarity(score, low_thresh, high_thresh)
        
        css_class = f"highlight-{sim_class.lower()}"
        
        # Limit to Medium and High matches to keep UI clean, unless there are none.
        if sim_class in ['High', 'Medium']:
            c1, c2, c3 = st.columns([4, 4, 1])
            with c1:
                st.markdown(f"**Reference:** <span class='{css_class}'>{res['doc2_text']}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"**Target:** {res['doc1_text']}")
            with c3:
                st.markdown(f"**{score:.1%}** ({sim_class})")
            st.markdown("<hr style='margin: 0.5em 0; opacity: 0.2;'>", unsafe_allow_html=True)

def render_coverage_side_by_side(coverage_results, low_thresh, high_thresh):
    """Render side-by-side matches from the Target's perspective for Batch Mode."""
    st.write("**Detailed Target View** (Showing suspicious sentences in your Target Document and where they likely came from)")
    for res in coverage_results:
        score = res['similarity_score']
        sim_class = classify_similarity(score, low_thresh, high_thresh)
        
        css_class = f"highlight-{sim_class.lower()}"
        
        # Only highlight if it breaches the suspicious threshold
        if sim_class in ['High', 'Medium']:
            c1, c2, c3 = st.columns([4, 4, 1])
            with c1:
                st.markdown(f"**Target Document:** <span class='{css_class}'>{res['target_text']}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"**Top Match ({res['best_match_file']}):** {res['best_ref_text']}")
            with c3:
                st.markdown(f"**{score:.1%}** ({sim_class})")
            st.markdown("<hr style='margin: 0.5em 0; opacity: 0.2;'>", unsafe_allow_html=True)

# --- App Header ---
col_title, col_api = st.columns([3, 1])

with col_title:
    st.title("🔍 Vietnamese Academic Plagiarism Detection Demo")
    st.markdown("A simple tool to detect potential plagiarism using TF-IDF and Cosine Similarity.")

with col_api:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔑 Cấu hình Hệ thống AI", expanded=False):
        current_key = get_saved_apikey()
        api_key_input = st.text_input("Gemini API Key", value=current_key, type="password", key="api_key_global")
        if st.button("Lưu cấu hình"):
            save_apikey(api_key_input)
            st.success("Đã ghi nhớ API Key!")
            
st.markdown("---")

# --- Sidebar Controls ---
st.sidebar.header("Cài đặt (Settings)")
mode = st.sidebar.radio("Chế độ (Mode)", [
    "So sánh 2 tài liệu (1 vs 1)", 
    "So sánh nhiều tài liệu (Batch)",
    "So sánh thuật toán (Algorithm Comparison)",
    "Kiểm tra & Sửa lỗi chính tả (Auto-correct)"
])

low_thresh_pct = st.sidebar.slider("Ngưỡng Cảnh báo Trung bình", min_value=10, max_value=50, value=30, step=5, format="%d%%")
high_thresh_pct = st.sidebar.slider("Ngưỡng Cảnh báo Cao", min_value=50, max_value=90, value=70, step=5, format="%d%%")

low_thresh = low_thresh_pct / 100.0
high_thresh = high_thresh_pct / 100.0

if low_thresh >= high_thresh:
    st.sidebar.error("Ngưỡng Trung bình phải nhỏ hơn Ngưỡng Cao.")

if mode == "Kiểm tra & Sửa lỗi chính tả (Auto-correct)":
    st.sidebar.markdown("---")
    st.sidebar.header("Cấu hình Auto-correct")
    ac_enabled = st.sidebar.checkbox("Bật Engine", value=True)
    engine_type = st.sidebar.radio("Bộ Mã Máy Xử lý", ["Từ điển Truyền thống", "AI Siêu Trí Tuệ (Gemini)"])
    
    saved_key = get_saved_apikey()
    if engine_type == "AI Siêu Trí Tuệ (Gemini)":
        if saved_key:
            configure_ai(saved_key)
        else:
            st.sidebar.warning("Vui lòng thiết lập API Key ở góc trên bên phải màn hình để dùng AI.")
        
    ac_mode = st.sidebar.selectbox("Chế độ xử lý", ["autocorrect", "suggest_only", "spellcheck_only"])
    ac_threshold_pct = st.sidebar.slider("Độ tự tin (Confidence)", 50, 100, 85, 5, format="%d%%")
    ac_threshold = ac_threshold_pct / 100.0
else:
    ac_enabled = False
    engine_type = "Từ điển Truyền thống"
    ac_mode = "autocorrect"
    ac_threshold = 0.85

@st.cache_resource
def get_correction_engine(enabled, acmode, threshold):
    config = AutoCorrectConfig(enabled=enabled, mode=acmode, confidence_threshold=threshold)
    return CorrectionEngine(config)

engine = get_correction_engine(ac_enabled, ac_mode, ac_threshold)

def apply_autocorrect(text, tag=""):
    if not ac_enabled:
        return text, []
        
    if engine_type == "AI Siêu Trí Tuệ (Gemini)" and not get_saved_apikey():
        st.error("Chưa cấu hình API Key ở góc phải. Sẽ giữ nguyên văn bản gốc.")
        return text, []
    
    with st.spinner(f"Đang kiểm tra chính tả {tag}..."):
        if engine_type == "AI Siêu Trí Tuệ (Gemini)":
            result = process_text_with_ai(text)
        else:
            result = engine.process_text(text)
            
        logs = result['logs']
        applied_count = sum(1 for log in logs if log.get('applied'))
        if applied_count > 0 or any(l.get('suggestions') for l in logs):
            st.success(f"Spellcheck: Tự động sửa {applied_count} lỗi trong {tag}.")
            with st.expander(f"Xem chi tiết lỗi - {tag}", expanded=True):
                for log in logs:
                    if log.get('applied'):
                        st.write(f"🔧 Đã sửa: **{log['word']}** ➡️ **{log['suggested']}** ({log.get('score',0):.2f})")
                    elif log.get('suggestions'):
                        st.write(f"💡 Gợi ý cho **{log['word']}**: {', '.join([s['word'] for s in log['suggestions']])}")
        else:
            st.info("Tuyệt vời! Không tìm thấy lỗi chính tả nào đáng chú ý.")
        return result['corrected'], logs

# --- MODE 1: 1 vs 1 ---
if mode == "So sánh 2 tài liệu (1 vs 1)":
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 Tài liệu gốc (Target)")
        file1 = st.file_uploader("Upload target document (.txt, .docx)", type=['txt', 'docx'], key='file1')

    with col2:
        st.subheader("📄 Tài liệu kiểm tra (Reference)")
        file2 = st.file_uploader("Upload reference document (.txt, .docx)", type=['txt', 'docx'], key='file2')

    if file1 and file2:
        text1 = load_file(file1)
        text2 = load_file(file2)
        
        if not text1 or not text2:
            st.error("Error reading one or both files. Please ensure they contain text.")
            st.stop()
            
        with st.spinner("Calculating similarity..."):
            overall_score = calculate_overall_similarity(text1, text2)
            overall_classification = classify_similarity(overall_score, low_thresh, high_thresh)
            
            segments1 = split_sentences(text1)
            segments2 = split_sentences(text2)
            local_results = calculate_local_similarity(segments1, segments2)
            
        st.markdown("---")
        st.subheader("📊 Kết quả tổng quan (Overall Result)")
        
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        metrics_col1.metric("Overall Similarity", f"{overall_score:.1%}")
        metrics_col2.metric("Classification", overall_classification)
        
        high_count = sum(1 for r in local_results if classify_similarity(r['similarity_score'], low_thresh, high_thresh) == 'High')
        medium_count = sum(1 for r in local_results if classify_similarity(r['similarity_score'], low_thresh, high_thresh) == 'Medium')
        metrics_col3.metric("Suspicious Segments (High/Med)", f"{high_count} / {medium_count}")
        
        st.markdown("---")
        st.subheader("🔎 Phân tích chi tiết (Detailed Analysis)")
        render_side_by_side(local_results, low_thresh, high_thresh)

    elif file1 or file2:
        st.info("Vui lòng tải lên cả hai tài liệu để bắt đầu.")

# --- MODE 2: Batch (1 vs Many) ---
elif mode == "So sánh nhiều tài liệu (Batch)":
    st.markdown("### Chế độ làm việc lô (Batch Mode with Coverage & Top Match)")
    st.write("Kiểm tra 1 tài liệu mục tiêu đối chiếu với nhiều tài liệu tham khảo khác nhau.")

    col_target, col_refs = st.columns(2)
    with col_target:
        target_file = st.file_uploader("1. Tải lên tài liệu gốc (Target)", type=['txt', 'docx'], key='batch_target')
    
    with col_refs:
        ref_files = st.file_uploader("2. Tải lên danh sách tài liệu kiểm tra (References)", type=['txt', 'docx'], accept_multiple_files=True, key='batch_refs')

    if target_file and ref_files:
        target_text = load_file(target_file)
        if not target_text:
            st.error("Tài liệu gốc bị trống hoặc không đọc được.")
            st.stop()
            
        target_segments = split_sentences(target_text)
        
        if len(target_segments) == 0:
            st.error("Không tìm thấy câu nào hợp lệ trong tài liệu gốc.")
            st.stop()

        results_data = [] # For ranking table
        all_refs_segments_dict = {}
        
        top_match_score = 0.0
        top_match_file = "None"

        with st.spinner(f"Đang kiểm tra {len(ref_files)} tài liệu..."):
            for ref_file in ref_files:
                ref_text = load_file(ref_file)
                if not ref_text:
                    continue
                    
                over_sim = calculate_overall_similarity(target_text, ref_text)
                classification = classify_similarity(over_sim, low_thresh, high_thresh)
                
                # Keep track of the top overall match
                if over_sim > top_match_score:
                    top_match_score = over_sim
                    top_match_file = ref_file.name

                ref_segments = split_sentences(ref_text)
                all_refs_segments_dict[ref_file.name] = ref_segments
                
                # Optional: calculate traditional local counts (Reference side) for the table
                loc_res = calculate_local_similarity(target_segments, ref_segments)
                high_c = sum(1 for r in loc_res if classify_similarity(r['similarity_score'], low_thresh, high_thresh) == 'High')
                med_c = sum(1 for r in loc_res if classify_similarity(r['similarity_score'], low_thresh, high_thresh) == 'Medium')
                
                results_data.append({
                    "File Name": ref_file.name,
                    "Overall Similarity": over_sim,
                    "Risk Level": classification,
                    "High Matches": high_c,
                    "Medium Matches": med_c
                })

            # Calculate unified Coverage across ALL references
            coverage_results = calculate_target_coverage(target_segments, all_refs_segments_dict)
            
            # Coverage = percentage of sentences in Target scoring >= low_thresh
            suspicious_count = sum(1 for r in coverage_results if r['similarity_score'] >= low_thresh)
            coverage_percentage = suspicious_count / len(target_segments) if len(target_segments) > 0 else 0.0
            
            # Final Risk Calculation Setup
            final_risk = "Minimal"
            if coverage_percentage >= 0.5 or top_match_score >= 0.35:
                final_risk = "High"
            elif coverage_percentage >= 0.25 or top_match_score >= 0.20:
                final_risk = "Medium"
            elif coverage_percentage >= 0.10:
                final_risk = "Low"

        # Display Final Conclusion Dashboard
        st.markdown("---")
        st.subheader("🏁 Kết luận chung (Final Risk Assessment)")
        
        # Color code risk label 
        risk_color = "red" if final_risk == "High" else "orange" if final_risk == "Medium" else "gray" if final_risk == "Low" else "green"
        st.markdown(f"### Mức độ rủi ro: <span style='color:{risk_color}'>{final_risk}</span>", unsafe_allow_html=True)
        
        met1, met2, met3, met4 = st.columns(4)
        met1.metric("Tổng File Đã Kiểm Tra", len(results_data))
        met2.metric("Độ Bao Phủ (Coverage)", f"{coverage_percentage:.1%}", help="Phần trăm file gốc trùng khớp với bất kỳ file tham khảo nào.")
        met3.metric("Tài Liệu Top Match", top_match_file)
        met4.metric("Điểm Top Match", f"{top_match_score:.1%}")

        # Expanded Table View
        if results_data:
            df = pd.DataFrame(results_data)
            df = df.sort_values(by="Overall Similarity", ascending=False).reset_index(drop=True)
            
            st.markdown("### 🏆 Bảng Xếp Hạng Tham Khảo (Ranked References)")
            df_display = df.copy()
            df_display["Overall Similarity"] = df_display["Overall Similarity"].apply(lambda x: f"{x:.1%}")
            st.dataframe(df_display, use_container_width=True)
            
            # Export CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Xuất dữ liệu (Export CSV)",
                data=csv,
                file_name='plagiarism_batch_results.csv',
                mime='text/csv',
            )

            st.markdown("---")
            st.subheader("🔎 Chi tiết Độ Bao Phủ (Coverage Deep Dive)")
            st.write("Dưới đây là các đoạn mã đáng ngờ trong file gốc (Target) và hệ thống cho thấy nguồn có khả năng nhất.")
            
            with st.expander("Hiển thị Câu Trùng Lặp (Show Copied Sentences)", expanded=True):
                render_coverage_side_by_side(coverage_results, low_thresh, high_thresh)

    elif target_file or ref_files:
        st.info("Vui lòng tải lên tài liệu đích và danh sách tài liệu tham khảo.")

# --- MODE 3: Algorithm Comparison ---
elif mode == "So sánh thuật toán (Algorithm Comparison)":
    st.markdown("### 🧮 Tỉ lệ trùng hợp theo Các thuật toán")
    st.write("Kiểm thử định lượng tỷ lệ trùng hợp (Overlap Ratio) của 5 thuật toán so khớp chuỗi kinh điển ứng dụng trong NLP.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        file_a = st.file_uploader("1. Tải lên Văn bản tham chiếu (Text A)", type=['txt', 'docx'], key='algo_a')
        text_a_input = st.text_area("Hoặc dán thủ công (Text A - Nguồn)", height=150, help="Đóng vai trò là Pattern / Source")
    with col_b:
        file_b = st.file_uploader("2. Tải lên Văn bản kiểm tra (Text B)", type=['txt', 'docx'], key='algo_b')
        text_b_input = st.text_area("Hoặc dán thủ công (Text B - Đích)", height=150, help="Đóng vai trò là Text cần quét")
        
    if st.button("🚀 Chạy So sánh", type="primary"):
        text_a = load_file(file_a) if file_a else text_a_input
        text_b = load_file(file_b) if file_b else text_b_input
        
        if not text_a.strip() or not text_b.strip():
            st.error("Vui lòng nhập/tải lên cả hai văn bản (chứa ít nhất 1 câu).")
        else:
            from utils.algorithms import SimilarityAlgorithmService
            service = SimilarityAlgorithmService()
            
            with st.spinner("Đang chạy và tập hợp song song 5 thuật toán..."):
                results = service.compare_all(text_a, text_b)
                
            data = []
            chart_data = []
            for r in results:
                data.append({
                    "🚀 Thuật toán": r.algorithm_name,
                    "🎯 Số Match": r.match_count,
                    "📏 Size Khớp (char)": r.matched_length,
                    "🔥 Tỉ lệ Trùng (%)": f"{r.similarity_percent:.1f}%",
                    "📝 Nguyên lý & Đánh giá": r.notes
                })
                chart_data.append({
                    "Thuật toán": r.algorithm_name,
                    "Tỉ lệ Trùng hợp (%)": r.similarity_percent
                })
                
            st.markdown("### 📊 Biểu đồ Tương quan Thuật toán")
            st.write("Mỗi thuật toán đại diện cho một cách đánh giá (Keyword, Sentence, Substring...). Nhìn vào biểu đồ bạn sẽ biết văn bản này chủ yếu giống nhau ở Cấu trúc nào.")
            
            import altair as alt
            df_chart = pd.DataFrame(chart_data)
            bar_chart = alt.Chart(df_chart).mark_bar().encode(
                x=alt.X('Thuật toán:N', title='', sort=None),
                y=alt.Y('Tỉ lệ Trùng hợp (%):Q', title='Tỉ lệ trùng khớp (%)'),
                color=alt.Color('Thuật toán:N', legend=None),
                tooltip=['Thuật toán:N', 'Tỉ lệ Trùng hợp (%):Q']
            ).properties(height=350)
            st.altair_chart(bar_chart, use_container_width=True)
            
            st.dataframe(pd.DataFrame(data), use_container_width=True)
            
            st.markdown("---")
            st.subheader("🖍 Hiển thị Visual Match (Best Coverage)")
            
            # Chọn thuật toán cho ra kết quả trùng lắp (match len) cao nhất để highlight UI
            valid_results = [r for r in results if r.matched_length > 0]
            if valid_results:
                best_r = sorted(valid_results, key=lambda x: x.matched_length, reverse=True)[0]
                st.write(f"Đang minh hoạ highlight từ kết quả phân tích của vòng quét: **{best_r.algorithm_name}**")
                
                html = render_highlighted_text(text_b, best_r.matched_segments)
                st.markdown(f"<div class='box'>{html}</div>", unsafe_allow_html=True)
            else:
                st.success("Tuyệt vời! Không phát hiện trùng lặp giữa 2 văn bản này bởi bất kỳ thuật toán nào.")

# --- MODE 4: Auto-correct ---
elif mode == "Kiểm tra & Sửa lỗi chính tả (Auto-correct)":
    st.markdown("### 📝 Công cụ Kiểm tra và Tự động sửa lỗi chính tả")
    st.write("Sử dụng AI và từ điển mở rộng để tự động chuẩn hóa văn bản, đặc biệt hỗ trợ domain y tế.")
    
    file_ac = st.file_uploader("Tải lên tài liệu cần kiểm tra (.txt, .docx)", type=['txt', 'docx'], key='file_ac')
    
    if file_ac:
        text_ac = load_file(file_ac)
        if not text_ac:
            st.error("Tài liệu bị trống hoặc không đọc được.")
            st.stop()
            
        col_orig, col_corr = st.columns(2)
        with col_orig:
            st.subheader("Bản gốc")
            st.text_area("Original Text", text_ac, height=300, disabled=True)
            
        with col_corr:
            st.subheader("Bản sửa lỗi")
            corrected_text, logs = apply_autocorrect(text_ac, "Tài liệu upload")
            st.text_area("Corrected Text", corrected_text, height=300)
            
            # Allow user to download corrected version
            if corrected_text != text_ac:
                st.download_button(
                    label="📥 Tải xuống Bản sửa lỗi",
                    data=corrected_text.encode('utf-8'),
                    file_name=f"corrected_{file_ac.name}",
                    mime='text/plain',
                )
