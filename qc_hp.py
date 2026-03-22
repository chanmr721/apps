import streamlit as st

# --- KONFIGURASI HALAMAN ---
# Menggunakan layout centered agar proporsional di layar vertikal HP
st.set_page_config(page_title="Lembar QC Algo", layout="centered")

# --- DATA PARAMETER ---
QC_MODES = ["General QC", "Next Level QC", "Bad Retention", "Good Retention", "Private Class"]

PARAMS_GENERAL = [
    "Warming Up / Ice Breaking", "Theory & Material Explanation", "Platform Task Explanation",
    "Time Management", "Compliance with Methodological Guidelines", "Reflection / Lesson Recap",
    "Kids Platform Engagement & Monitoring Progress", "Interaction & Two-Way Communication",
    "Audience Coverage / Equal Attention", "Discipline in the Classroom", "Feedback & Praise",
    "Tutor’s Emotional Control", "Technical Readiness & Internet Stability", "Use of Platform Features"
]

PARAMS_NEXT_LEVEL = [
    "Greeting (Salam)", "Project Showcase (Penampilan Proyek)", "Interaction (Interaksi)",
    "Closing the Presentation", "All Attendees Open Cam", "Communication with Parents", 
    "Professional Appearance", "Audio Quality", "Good Internet"
]

def main():
    st.markdown("<h3 style='text-align: center;'>📝 Lembar Penilaian QC</h3>", unsafe_allow_html=True)

    # 1. Mode & Info Dasar
    qc_mode = st.selectbox("Tipe Evaluasi", QC_MODES)
    tutor_name = st.text_input("Nama Tutor")

    st.divider()

    # 2. Ceklis Teknis
    st.markdown("**🛠️ Ceklis Teknis**")
    st.checkbox("Tutor Pakai PPT?", value=True)
    
    if qc_mode == "Next Level QC":
        st.selectbox("Virtual Background", ["Pakai BG Next Level + Avatar", "Pakai BG Algo Biasa", "Tidak Memakai"])

    st.divider()

    # 3. Parameter Penilaian (Slider Vertikal)
    st.markdown("**📊 Parameter (Geser 1-5)**")
    current_params = PARAMS_NEXT_LEVEL if qc_mode == "Next Level QC" else PARAMS_GENERAL
    scores = {}

    for p in current_params:
        scores[p] = st.slider(p, 1, 5, 3, key=f"sl_{p}")
        
        # Opsi tambahan khusus untuk Next Level
        if qc_mode == "Next Level QC" and p == "Communication with Parents":
            st.checkbox("Orang Tua Hadir?", value=False)

    st.divider()

    # 4. Catatan Manual
    st.text_area("Catatan Tambahan Pelanggaran/QC (Opsional)")

    st.divider()

    # 5. Format Copy-Paste (Memudahkan rekap akhir)
    st.markdown("**📋 Rekap Nilai**")
    st.caption("Klik kotak di bawah lalu salin (copy) untuk memindahkan deretan nilai.")
    ordered_scores = [str(scores[p]) for p in current_params]
    st.text_input("Format Tab:", value="\t".join(ordered_scores))

if __name__ == "__main__":
    main()
