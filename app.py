import streamlit as st
import pandas as pd
from utils.file_loader import load_file
from utils.preprocess import split_sentences
from utils.similarity import calculate_overall_similarity, calculate_local_similarity, classify_similarity, calculate_target_coverage

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
st.title("🔍 Vietnamese Academic Plagiarism Detection Demo")
st.markdown("A simple tool to detect potential plagiarism using TF-IDF and Cosine Similarity.")
st.markdown("---")

# --- Sidebar Controls ---
st.sidebar.header("Cài đặt (Settings)")
mode = st.sidebar.radio("Chế độ so sánh (Mode)", [
    "So sánh 2 tài liệu (1 vs 1)", 
    "So sánh nhiều tài liệu (Batch)"
])

low_thresh = st.sidebar.slider("Medium Similarity Threshold", min_value=0.1, max_value=0.5, value=0.3, step=0.05)
high_thresh = st.sidebar.slider("High Similarity Threshold", min_value=0.5, max_value=0.9, value=0.7, step=0.05)

if low_thresh >= high_thresh:
    st.sidebar.error("Medium threshold must be lower than High threshold.")

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
else:
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
