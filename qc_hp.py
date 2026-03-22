import streamlit as st
import pandas as pd
import requests 
import json
import os
import re 
from youtube_transcript_api import YouTubeTranscriptApi

# --- KONFIGURASI HALAMAN UNTUK HP ---
st.set_page_config(
    page_title="QC Edu Mobile",
    layout="centered", # Menggunakan centered lebih optimal untuk HP dibanding wide
    initial_sidebar_state="collapsed"
)

# --- FILE MEMORI AI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "memory_ai.json")

if not os.path.exists(MEMORY_FILE):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    except Exception as e:
        st.error(f"Gagal membuat file memori: {e}")

DEFAULT_API_KEY = "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" 

SUBJECT_LIST = [
    "Coding Knight (Early Kids / Pre-Visual)", "Visual Programming (Scratch/Tynker)",
    "Design Junior", "Design Senior", "Digital Literacy", "Python Start",
    "Python Pro", "AI (Artificial Intelligence)", "Math Junior", "Math Master",
    "Roblox Studio / Game Dev", "Web Development", "Graduation / Trial Class"
]

QC_MODES = ["General QC", "Next Level QC", "Bad Retention", "Good Retention", "Private Class"]

PARAMS_GENERAL = [
    "Warming Up / Ice Breaking", "Theory & Material Explanation", "Platform Task Explanation",
    "Time Management", "Compliance with Methodological Guidelines", "Reflection / Lesson Recap",
    "Kids Platform Engagement & Monitoring Progress", "Interaction & Two-Way Communication",
    "Audience Coverage / Equal Attention", "Discipline in the Classroom", "Feedback & Praise",
    "Tutor’s Emotional Control", "Technical Readiness & Internet Stability", "Use of Platform Features"
]

RUBRIC_GENERAL = """
STANDAR PENILAIAN UMUM (PEDAGOGI):
1. Warming Up: 1=Langsung materi, 5=Game/Kuis interaktif (3-5 menit).
2. Theory: 1=Baca slide, 5=Analogi kreatif/visual/storytelling.
3. Task Explanation: 1=Kerjakan sendiri, 5=Scaffolded questions (bertahap).
4. Time Mgmt: 1=Berantakan, 5=Presisi sesuai rundown.
5. Methodology: 1=Improvisasi, 5=Ikut alur (Warmup-Teori-Praktek-Refleksi).
6. Reflection: 1=Tidak ada, 5=Siswa menyimpulkan materi sendiri.
7. Engagement: 1=<20% tugas, 5=>90% tugas platform selesai.
8. Interaction: 1=Satu arah, 5=Diskusi dua arah/pertanyaan terbuka (Why/How).
9. Attention: 1=Pilih kasih, 5=Merata ke semua siswa (panggil nama).
10. Discipline: 1=Ribut, 5=Tertib & aturan jelas (Cam On/Mute).
11. Feedback: 1=Nihil, 5=Spesifik & personal ("Logika loop kamu rapi").
12. Emotion: 1=Marah, 5=Sabar & ceria.
13. Tech: 1=Error, 5=Lancar jaya.
14. Features: 1=Manual, 5=Integrasi fitur platform maksimal.
"""

PARAMS_NEXT_LEVEL = [
    "Greeting (Salam)", "Project Showcase (Penampilan Proyek)", "Interaction (Interaksi)",
    "Closing the Presentation", "All Attendees Open Cam", "Communication with Parents", 
    "Professional Appearance", "Audio Quality", "Good Internet"
]

RUBRIC_NEXT_LEVEL = """
STANDAR PENILAIAN GRADUATION & NEXT LEVEL:
1. Greeting: 1=Tidak ada, 5=Sangat hangat dan ramah.
2. Project Showcase: 1=Tidak ada, 5=Tutor memandu showcase dengan profesional.
3. Interaction: 1=Monolog, 5=Membangun dialog dua arah yang nyaman.
4. Closing: 1=Tidak ada ajakan, 5=Menjelaskan langkah berikutnya (Next Level).
5. Open Cam: 1=Tidak diminta, 5=Mengajak semua peserta open cam.
6. Comm with Parents: 1=Diam, 5=Menjelaskan manfaat program lanjutan kepada Ortu.
7. Appearance: 1=Kusut, 5=Sangat rapi & profesional.
8. Audio: 1=Buruk, 5=Sangat jernih.
9. Internet: 1=Putus-putus, 5=Stabil.
"""

def save_to_memory(subject, mode, score_state, feedback_text):
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memory = json.load(f)
        new_data = {
            "subject": subject, "mode": mode,
            "need_improvement": score_state.get("need_improvement", []), 
            "perfect_scores": score_state.get("perfect_scores", []),
            "feedback": feedback_text
        }
        memory.append(new_data)
        if len(memory) > 500: memory = memory[-500:]
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=4)
        return True
    except: return False

def retrieve_from_memory(subject, mode, current_need_improvement, current_perfect_scores):
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memory = json.load(f)
        if not memory: return ""
        best_match = None; highest_score = -1
        for item in memory:
            score = 0
            if item["mode"] == mode: score += 5
            if item["subject"] == subject: score += 3
            overlap_bad = set(item.get("need_improvement", [])).intersection(set(current_need_improvement))
            score += len(overlap_bad) * 4 
            overlap_good = set(item.get("perfect_scores", [])).intersection(set(current_perfect_scores))
            score += len(overlap_good) * 2 
            if score > highest_score and score > 6: 
                highest_score = score
                best_match = item["feedback"]
        return best_match if best_match else ""
    except: return ""

def get_youtube_transcript(video_url):
    try:
        video_id = ""
        if "v=" in video_url: video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url: video_id = video_url.split("youtu.be/")[1].split("?")[0]
        else: return None, "Link tidak valid."
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'id'])
        return " ".join([t['text'] for t in transcript_list]), None
    except: return None, "Tidak bisa mengambil transkrip."

def auto_detect_scores(text, mode):
    if not text: return {}
    text = text.lower(); suggestions = {}
    def check(pos): return 1 if any(k in text for k in pos) else 0
    if mode == "Next Level QC": 
        if check(["bapak", "ibu", "ayah", "bunda", "ortu"]): suggestions["Communication with Parents"] = 4
        if check(["admin", "bayar", "lanjut", "daftar"]): suggestions["Closing the Presentation"] = 4
        if check(["foto", "dokumentasi", "kamera", "cam"]): suggestions["All Attendees Open Cam"] = 4
    else:
        if check(["kuis", "game", "tebak"]): suggestions["Warming Up / Ice Breaking"] = 4
        if check(["refleksi", "kesimpulan"]): suggestions["Reflection / Lesson Recap"] = 4
    return suggestions

def generate_feedback_groq(api_key, name, subject, scores, violations, mistakes_df, transcript_text, qc_notes, parents_present, ppt_present, vbg_status, use_ai, mode, language):
    rubric_text = RUBRIC_NEXT_LEVEL if mode == "Next Level QC" else RUBRIC_GENERAL
    need_improvement = {k: v for k, v in scores.items() if v <= 3} 
    perfect_scores   = {k: v for k, v in scores.items() if v >= 4} 
    
    violation_texts = []
    if violations and mistakes_df is not None:
        for v in violations:
            try:
                row = mistakes_df[mistakes_df['Code'] == v].iloc[0]
                violation_texts.append(f"{row['Bentuk Pelanggaran']}")
            except: violation_texts.append(v)

    is_technical_issue = False
    if not ppt_present: is_technical_issue = True
    if mode == "Next Level QC":
        if not parents_present: is_technical_issue = True
        if "Tidak Memakai" in vbg_status or "Algo Biasa" in vbg_status: is_technical_issue = True
        
    is_perfect = (len(need_improvement) == 0) and (len(violation_texts) == 0) and (not is_technical_issue) and (not qc_notes)

    mode_specific_instructions = ""
    if mode == "Bad Retention":
        mode_specific_instructions = "KONTEKS KRITIS: RETENSI BURUK. Fokus alasan perbaikan pada peningkatan antusiasme agar murid betah."
    elif mode == "Good Retention":
        mode_specific_instructions = "KONTEKS KRITIS: RETENSI SANGAT BAIK. Sampaikan saran perbaikan dengan nada sangat suportif."
    elif mode == "Private Class":
        mode_specific_instructions = "KONTEKS KRITIS: KELAS PRIVAT. Fokus saran pada personalisasi dan ikatan emosional."

    if language == "English":
        opening_perfect = f"Hello {name}, outstanding! We want to express our gratitude for your excellent teaching performance today."
        opening_normal = f"Hello {name}, thank you for your hard work and dedication."
        transition_saran = "To make your class even more perfect, here are a few things that can be optimized:"
        lang_instruction = "Write in Professional English. Use 'We'."
        
        tech_instructions = []
        if not ppt_present:
            if mode == "Next Level QC": tech_instructions.append("MUST add: 'We require the use of the provided PPT.'")
            else: tech_instructions.append("MUST add: 'We recommend using PPT/Visual slides.'")
        if mode == "Next Level QC":
            if not parents_present: tech_instructions.append("MUST add: 'Please try to invite the parents.'")
            if "Tidak Memakai" in vbg_status: tech_instructions.append("MUST add: 'Please use the special Next Level Virtual Background.'")
            elif "Algo Biasa" in vbg_status: tech_instructions.append("MUST add: 'Change your background to the Next Level edition.'")
    else: 
        opening_perfect = f"Halo {name}, luar biasa! Kami ingin mengucapkan terima kasih atas performa mengajar yang sangat baik hari ini."
        opening_normal = f"Halo {name}, terima kasih atas kerja keras dan dedikasinya."
        transition_saran = "Untuk membuat kelasmu semakin sempurna, ada beberapa hal yang bisa dioptimalkan:"
        lang_instruction = "Tulis dalam Bahasa Indonesia. Gunakan kata ganti 'KAMI'."
        
        tech_instructions = []
        if not ppt_present:
            if mode == "Next Level QC": tech_instructions.append("WAJIB tambahkan: 'Kami mewajibkan penggunaan PPT.'")
            else: tech_instructions.append("WAJIB tambahkan: 'Kami menyarankan penggunaan PPT.'")
        if mode == "Next Level QC":
            if not parents_present: tech_instructions.append("WAJIB tambahkan: 'Usahakan mengundang orang tua di akhir sesi.'")
            if "Tidak Memakai" in vbg_status: tech_instructions.append("WAJIB tambahkan: 'Mohon gunakan Virtual Background khusus Next Level.'")
            elif "Algo Biasa" in vbg_status: tech_instructions.append("WAJIB tambahkan: 'Disarankan mengganti background dengan edisi khusus Next Level.'")

    tech_rules_str = "\n".join([f"- {rule}" for rule in tech_instructions])
    status_msg = ""
    
    if use_ai and api_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            context = transcript_text[:3000] if transcript_text else "Tidak ada transkrip."
            past_memory = retrieve_from_memory(subject, mode, list(need_improvement.keys()), list(perfect_scores.keys()))
            memory_prompt = f"REFERENSI GAYA BAHASA: {past_memory}" if past_memory else ""

            if is_perfect:
                prompt_text = f"Tugas: Buat Feedback FULL APRESIASI (TANPA SARAN) untuk Tutor {name}. Mapel: {subject}. Pembuka: '{opening_perfect}'. {lang_instruction}. Plain text. Dilarang menyebut kata QC atau transkrip."
            else:
                prompt_text = f"""
                Buat Feedback Personal untuk Tutor {name}. Mapel: {subject}.
                {mode_specific_instructions}
                {memory_prompt}
                Konteks video: "{context}..."
                SANGAT BAIK: {', '.join(perfect_scores.keys()) if perfect_scores else 'TIDAK ADA'}
                PERLU PERBAIKAN: {', '.join(need_improvement.keys()) if need_improvement else 'TIDAK ADA'}
                Pelanggaran: {', '.join(violation_texts) if violation_texts else 'TIDAK ADA'}
                Catatan Manual: {qc_notes}
                Instruksi:
                1. Buka dengan: "{opening_normal}"
                2. Puji aspek SANGAT BAIK.
                3. Transisi: "{transition_saran}"
                4. Beri saran bernomor untuk aspek PERLU PERBAIKAN beserta alasan pedagogisnya. Masukkan poin teknis ini jika ada: {tech_rules_str}
                5. {lang_instruction}. Dilarang sebut kata rekaman, transkrip, atau nama mode QC.
                """
            
            payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.3}
            response = requests.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload)
            if response.status_code == 200:
                clean_text = response.json()['choices'][0]['message']['content'].replace("**", "").replace("##", "")
                for word in ["General QC", "Next Level QC", "Bad Retention", "Good Retention", "Private Class"]:
                    clean_text = re.sub(r'(?i)' + re.escape(word), '', clean_text)
                return clean_text.strip(), "Sukses"
            else: status_msg = f"Groq Error: {response.text}"
        except Exception as e: status_msg = f"Error: {str(e)}"

    text = f"Halo {name}, evaluasi manual selesai.\n\nPerlu perbaikan pada: {', '.join(need_improvement.keys())}."
    return text, f"Mode Manual ({status_msg})"

# ==========================================
# UI KHUSUS MOBILE
# ==========================================
def main():
    # 1. Pengaturan disembunyikan di expander atas agar tidak menuhin layar HP
    with st.expander("⚙️ Konfigurasi Sistem"):
        qc_mode = st.selectbox("Tipe Evaluasi", QC_MODES)
        language = st.selectbox("Bahasa Output", ["Bahasa Indonesia", "English"])
        api_key = st.text_input("API Key Groq", value=DEFAULT_API_KEY, type="password")
        use_ai = st.checkbox("Gunakan AI", value=True)

    st.markdown(f"### 📝 Form QC")

    # 2. Input teks disusun lurus ke bawah
    tutor_name = st.text_input("Nama Tutor", "Hafizh")
    subject = st.selectbox("Mata Pelajaran", SUBJECT_LIST)
    
    # URL hanya untuk tarik teks, tidak ada display st.video()
    video_url = st.text_input("Link YouTube (Opsional - Tarik Teks)")
    if st.button("Tarik Data Video", use_container_width=True):
        if video_url:
            with st.spinner("Mengambil data..."):
                text, err = get_youtube_transcript(video_url)
                if text: st.session_state['transcript'] = text
                else: st.error(err)
    
    if 'transcript' not in st.session_state: st.session_state['transcript'] = ""
    suggested_scores = {}
    if st.session_state['transcript']: 
        suggested_scores = auto_detect_scores(st.session_state['transcript'], qc_mode)
        with st.expander("📄 Data Teks Terambil"):
            st.caption(st.session_state['transcript'][:500] + "...")

    st.divider()

    # 3. Kebutuhan Teknis
    st.markdown("**Ceklis Teknis**")
    ppt_present = st.checkbox("Tutor Pakai PPT?", value=True)
    vbg_status = "N/A"
    if qc_mode == "Next Level QC":
        vbg_status = st.selectbox("Virtual Background", ["Pakai BG Next Level + Avatar", "Pakai BG Algo Biasa", "Tidak Memakai"])

    st.divider()

    # 4. Rubrik Penilaian Vertikal (Sangat mobile-friendly)
    st.markdown("**Nilai Parameter (1-5)**")
    scores = {}
    current_params = PARAMS_NEXT_LEVEL if qc_mode == "Next Level QC" else PARAMS_GENERAL
    parents_present = False 

    for p in current_params:
        auto = suggested_scores.get(p, 3)
        # Menghapus label panjang agar pas di layar HP, menampilkan auto skor di sebelah nama
        label = p + (f" 🤖[{auto}]" if p in suggested_scores else "")
        scores[p] = st.slider(label, 1, 5, auto, key=f"sl_{p}")
        
        if qc_mode == "Next Level QC" and p == "Communication with Parents":
            parents_present = st.checkbox("Orang Tua Hadir?", value=False)

    st.divider()

    # 5. Pelanggaran & Catatan
    violation_codes = []
    df_mistake = None
    try:
        xls = pd.ExcelFile("StandardPenilaianNewQC (1).xlsx")
        df_mistake = pd.read_excel(xls, sheet_name='Mistake', header=1).dropna(subset=['Code'])
        opts = df_mistake['Code'] + " | " + df_mistake['Bentuk Pelanggaran']
        sel = st.multiselect("Pelanggaran (Jika ada)", opts)
        violation_codes = [s.split(" | ")[0] for s in sel]
    except: 
        st.caption("File Excel Mistake tidak termuat.")

    qc_notes = st.text_area("Catatan Tambahan (Bebas)")

    # 6. Tombol Generate Full Width
    if st.button("🚀 Buat Feedback", type="primary", use_container_width=True):
        with st.spinner("Memproses AI..."):
            score_state_temp = {
                "need_improvement": [k for k, v in scores.items() if v <= 3],
                "perfect_scores": [k for k, v in scores.items() if v >= 4]
            }
            feedback, status = generate_feedback_groq(
                api_key, tutor_name, subject, scores, violation_codes, 
                df_mistake, st.session_state['transcript'], qc_notes, 
                parents_present, ppt_present, vbg_status, use_ai, qc_mode, language
            )
            
            if "Error" in status: st.error(status)
            else: 
                st.session_state['generated_feedback'] = feedback
                st.session_state['score_state'] = score_state_temp
                st.rerun() # Refresh agar langsung tampil ke bawah
                
    # 7. Hasil Output
    if st.session_state.get('generated_feedback'):
        st.success("Selesai!")
        edited_feedback = st.text_area("Hasil Feedback (Bisa diedit):", value=st.session_state['generated_feedback'], height=300)
        
        if st.button("💾 Simpan ke Memori AI", use_container_width=True):
            if save_to_memory(subject, qc_mode, st.session_state['score_state'], edited_feedback):
                st.toast("Berhasil disimpan!")
        
        st.text_input("Salin Data Tabular:", value="\t".join([str(scores[p]) for p in current_params]))

if __name__ == "__main__":
    main()