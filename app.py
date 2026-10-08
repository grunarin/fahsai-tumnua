import streamlit as st
import sqlite3
import os
import base64
import wave
import struct
import math
import io
from datetime import datetime, timedelta

# ตั้งค่าหน้าเว็บรองรับทุกขนาดหน้าจอ
st.set_page_config(
    page_title="ร้านฟ้าใสตำนัว",
    page_icon="🌶️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS อัจฉริยะ ปรับหน้าตาให้สวยงาม รองรับทั้ง มือถือ (iOS/Android), แท็บเล็ต, iPad และ คอมพิวเตอร์ ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

/* บังคับใช้ฟอนต์ Prompt โดยไม่ทับไอคอน Material Symbols ของ Streamlit */
html, body, p, input, select, textarea {
    font-family: 'Prompt', sans-serif !important;
}

.stMarkdown, .stButton > button {
    font-family: 'Prompt', sans-serif !important;
}

/* คืนค่าฟอนต์ไอคอน Material Symbols เพื่อไม่ให้กลายเป็นตัวหนังสือคำว่า expand_less ทับบนปุ่ม */
[data-testid="stIconMaterial"], 
[class*="material-symbols"], 
[class*="material-icons"] {
    font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    font-style: normal !important;
}

/* ซ่อนไอคอนลูกศร expand_less/expand_more ในปุ่ม popover ไม่ให้บังข้อความ */
div[data-testid="stPopover"] > button [data-testid="stIconMaterial"] {
    display: none !important;
}

div[data-testid="stPopover"] > button {
    font-family: 'Prompt', sans-serif !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    min-height: 44px !important;
    font-weight: 600 !important;
}

/* ปรับระยะขอบหน้าจอให้พอดีกับมือถือ */
@media (max-width: 640px) {
    .main .block-container {
        padding: 0.75rem 0.5rem 3rem 0.5rem !important;
    }
    h1 { font-size: 1.8rem !important; }
    h2 { font-size: 1.35rem !important; }
    h3 { font-size: 1.15rem !important; }
}

@media (min-width: 641px) and (max-width: 1024px) {
    .main .block-container {
        padding: 1.5rem 1.25rem 3rem 1.25rem !important;
    }
}

/* ปุ่มกดขนาดใหญ่ สัมผัสง่ายสำหรับนิ้วมือบนสมาร์ตโฟน (Touch-friendly 44px+) */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    min-height: 44px !important;
    font-size: 14px !important;
    transition: all 0.15s ease !important;
}

.stButton > button:active {
    transform: scale(0.96) !important;
}

/* ปุ่ม Primary โดดเด่นด้วยสีส้มไล่เฉด */
button[kind="primary"] {
    background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 12px rgba(234, 88, 12, 0.35) !important;
}

/* การ์ดรายการอาหารมนโค้ง สวยงาม มีมิติ */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
    border: 1px solid #fed7aa !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04) !important;
    background: #ffffff !important;
    padding: 10px !important;
}

/* รูปภาพอาหารตัดมุมโค้งสวยงาม */
img {
    border-radius: 14px !important;
    object-fit: cover !important;
}

/* 🔶 ปุ่มเลือกหมวดหมู่อาหาร ให้เป็นปุ่มทรงเหลี่ยมชัดเจน (Crisp Rectangular Category Buttons) */
div[data-testid="stPills"], div[data-testid="stRadio"] {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
    margin: 4px 0 14px 0 !important;
}
div[data-testid="stPills"] > div, div[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    justify-content: center !important;
    width: 100% !important;
}

/* สไตล์สำหรับ st.pills */
div[data-testid="stPills"] button {
    border-radius: 4px !important; /* ปรับเป็นทรงเหลี่ยมชัดเจน */
    border: 2px solid #ea580c !important;
    background-color: #ffffff !important;
    color: #431407 !important;
    padding: 8px 18px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.15s ease-in-out !important;
}
div[data-testid="stPills"] button:hover {
    background-color: #ffedd5 !important;
    border-color: #c2410c !important;
}
div[data-testid="stPills"] button[aria-selected="true"],
div[data-testid="stPills"] button[data-checked="true"] {
    background-color: #ea580c !important;
    color: #ffffff !important;
    border-color: #9a3412 !important;
    box-shadow: 0 4px 10px rgba(234, 88, 12, 0.35) !important;
}

/* สไตล์ fallback สำหรับ stRadio โดยไม่ปิดกั้นการคลิก */
div[data-testid="stRadio"] label[data-baseweb="radio"] {
    border-radius: 4px !important;
    border: 2px solid #ea580c !important;
    background-color: #ffffff !important;
    padding: 8px 18px !important;
    cursor: pointer !important;
    margin: 0 !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.15s ease-in-out !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
    background-color: #ffedd5 !important;
    border-color: #c2410c !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] svg {
    display: none !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] input {
    opacity: 0 !important;
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    pointer-events: none !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] p,
div[data-testid="stRadio"] label[data-baseweb="radio"] span,
div[data-testid="stRadio"] label[data-baseweb="radio"] div {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #431407 !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked),
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] {
    background-color: #ea580c !important;
    border: 2px solid #9a3412 !important;
    box-shadow: 0 4px 10px rgba(234, 88, 12, 0.35) !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p,
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) span,
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) div,
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] p,
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] span {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* ซ่อนแถบเมนูที่ไม่จำเป็นของ Streamlit เพื่อประสบการณ์แบบ App แท้ */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

DB_NAME = "restaurant.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            cost REAL DEFAULT 0,
            image TEXT,
            description TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_name TEXT NOT NULL,
            ingredient_name TEXT NOT NULL,
            quantity_per_portion REAL NOT NULL,
            unit TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            total_price REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            price REAL NOT NULL,
            cost REAL DEFAULT 0,
            quantity INTEGER NOT NULL,
            note TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY,
            table_number INTEGER NOT NULL UNIQUE,
            name TEXT,
            status TEXT DEFAULT 'available'
        )
    ''')
    c.execute('SELECT COUNT(*) FROM tables')
    if c.fetchone()[0] == 0:
        for t in range(1, 7):
            c.execute('INSERT OR IGNORE INTO tables (table_number, name) VALUES (?, ?)', (t, f'โต๊ะที่ {t}'))

    fahsai_menu = [
        ("ตำปูปลาร้านัวแซ่บ", "ส้มตำ & ตำนัว", 70, 25, "https://images.unsplash.com/photo-1569058242253-92a9c755a0ec?auto=format&fit=crop&w=600&q=80", "เส้นมะละกอกรอบ พริกแห้ง น้ำปลาร้าต้มสุกสูตรฟ้าใส นัวเข้มข้นถึงใจ"),
        ("ตำไทยไข่เค็ม", "ส้มตำ & ตำนัว", 80, 28, "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80", "รสเปรี้ยวหวานกลมกล่อม กุ้งแห้งคัดพิเศษ ถั่วลิสงคั่วใหม่ ไข่เค็มเต็มใบ"),
        ("ตำข้าวโพดกุ้งสด", "ส้มตำ & ตำนัว", 130, 50, "https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=600&q=80", "ข้าวโพดหวานคลุกน้ำยำรสแซ่บ กุ้งสดตัวโตเนื้อเด้งหวานฉ่ำ"),
        ("ตำถาดฟ้าใสรวมมิตร", "ส้มตำ & ตำนัว", 199, 75, "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=600&q=80", "ตำถาดเครื่องแน่น แคบหมู หมูยออุบล ไข่ต้ม ขนมจีน ผักเคียงครบครัน"),
        ("คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว", "ย่าง & ทอด & ลาบ", 120, 48, "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80", "คอหมูแท้แทรกมันย่างเตาถ่านหอมกรุ่น นุ่มฉ่ำ น้ำจิ้มแจ่วมะขามเปียก"),
        ("ไก่ย่างสมุนไพรเขาสวนกวาง", "ย่าง & ทอด & ลาบ", 140, 55, "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=600&q=80", "ไก่บ้านหมักสมุนไพรไทย ย่างหนังกรอบเนื้อนุ่มฉ่ำ หอมกระเทียมพริกไทย"),
        ("ลาบหมูสับตับหวานข้าวคั่ว", "ย่าง & ทอด & ลาบ", 95, 36, "https://images.unsplash.com/photo-1548943487-a2e4e43b4853?auto=format&fit=crop&w=600&q=80", "หมูสับคลุกตับลวก ข้าวคั่วใหม่หอมกรุ่นและสะระแหน่"),
        ("ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา", "ต้ม & ซดร้อน", 130, 45, "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80", "กระดูกหมูอ่อนเคี่ยวจนเปื่อยนุ่ม ซุปสมุนไพรเปรี้ยวเผ็ดร้อน ซดคล่องคอ"),
        ("ปีกไก่ทอดน้ำปลาหอมกรอบ", "ย่าง & ทอด & ลาบ", 90, 35, "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?auto=format&fit=crop&w=600&q=80", "ปีกไก่ทอดกรอบสีทอง หอมน้ำปลาแท้ ไม่อมน้ำมัน"),
        ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", "ข้าว & เครื่องเคียง", 20, 6, "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?auto=format&fit=crop&w=600&q=80", "ข้าวเหนียวคัดเกรด เมล็ดเรียวยาว นึ่งร้อนๆ เหนียวนุ่ม"),
        ("ขนมจีนแป้งหมัก", "ข้าว & เครื่องเคียง", 20, 6, "https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=600&q=80", "เส้นขนมจีนนุ่มลื่น ทานคู่ส้มตำแซ่บๆ"),
        ("แคบหมูไร้มันกรอบโบราณ", "ข้าว & เครื่องเคียง", 30, 10, "https://images.unsplash.com/photo-1541529086526-db283c563270?auto=format&fit=crop&w=600&q=80", "แคบหมูทอดกรอบไม่อมน้ำมัน เคี้ยวเพลิน"),
        ("ชาไทยเย็นสูตรโบราณ", "เครื่องดื่ม & หวาน", 45, 14, "https://images.unsplash.com/photo-1558857563-b371033873b8?auto=format&fit=crop&w=600&q=80", "ชาใบเข้มข้น หอมมันนมสดแท้ ดับเผ็ดได้ดี"),
        ("น้ำเก๊กฮวยต้มสมุนไพรสดชื่น", "เครื่องดื่ม & หวาน", 35, 10, "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=600&q=80", "เก๊กฮวยดอกแท้ต้มใบเตย หอมละมุน หวานน้อย")
    ]
    for item in fahsai_menu:
        c.execute('INSERT OR REPLACE INTO menu_items (name, category, price, cost, image, description) VALUES (?, ?, ?, ?, ?, ?)', item)

    recipes = [
        ("ตำปูปลาร้านัวแซ่บ", "เส้นมะละกอดิบขูด", 180, "กรัม"),
        ("ตำปูปลาร้านัวแซ่บ", "น้ำปลาร้าต้มสุก", 45, "มล."),
        ("ตำปูปลาร้านัวแซ่บ", "มะนาวแป้นสด", 1, "ลูก"),
        ("ตำไทยไข่เค็ม", "เส้นมะละกอดิบขูด", 180, "กรัม"),
        ("ตำไทยไข่เค็ม", "ไข่เค็ม", 1, "ฟอง"),
        ("ตำข้าวโพดกุ้งสด", "ข้าวโพดหวานต้ม", 150, "กรัม"),
        ("ตำข้าวโพดกุ้งสด", "กุ้งสดแกะเปลือก", 4, "ตัว"),
        ("ตำถาดฟ้าใสรวมมิตร", "เส้นมะละกอดิบขูด", 200, "กรัม"),
        ("ตำถาดฟ้าใสรวมมิตร", "หมูยออุบล", 80, "กรัม"),
        ("ตำถาดฟ้าใสรวมมิตร", "ไข่ต้ม", 1, "ฟอง"),
        ("คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว", "คอหมูสดหมัก", 220, "กรัม"),
        ("ไก่ย่างสมุนไพรเขาสวนกวาง", "ไก่สดหมักสมุนไพร", 350, "กรัม"),
        ("ลาบหมูสับตับหวานข้าวคั่ว", "หมูบดสด", 150, "กรัม"),
        ("ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา", "กระดูกหมูอ่อน", 200, "กรัม"),
        ("ปีกไก่ทอดน้ำปลาหอมกรอบ", "ปีกไก่สด", 250, "กรัม"),
        ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", "ข้าวเหนียวดิบ", 120, "กรัม"),
        ("ชาไทยเย็นสูตรโบราณ", "ใบชาไทย", 25, "กรัม")
    ]
    c.execute('DELETE FROM recipe_ingredients')
    c.executemany('INSERT INTO recipe_ingredients (menu_name, ingredient_name, quantity_per_portion, unit) VALUES (?, ?, ?, ?)', recipes)
    conn.commit()
    conn.close()

init_db()

# ตรวจสอบการแยกโหมดผ่าน Query Parameter
params = st.query_params
is_admin_mode = (params.get("mode", "") == "admin")

logo_path = "static/img/logo.png"
if not os.path.exists(logo_path):
    logo_path = "templates/img/logo.png"

def get_base64_image(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

@st.cache_data
def get_bell_sound_b64():
    sample_rate = 22050
    duration = 0.85
    n_samples = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            decay = math.exp(-4.2 * t)
            v1 = math.sin(2 * math.pi * 784.0 * t)
            v2 = math.sin(2 * math.pi * 1046.5 * t) if t > 0.08 else 0
            sample = int(32767 * 0.45 * (v1 * 0.55 + v2 * 0.45) * decay)
            wav_file.writeframes(struct.pack('<h', sample))
    return base64.b64encode(buf.getvalue()).decode()

def play_order_sound():
    sound_b64 = get_bell_sound_b64()
    audio_html = f'''
    <audio autoplay style="display:none;">
        <source src="data:audio/wav;base64,{sound_b64}" type="audio/wav">
    </audio>
    <script>
    try {{
        const snd = new Audio("data:audio/wav;base64,{sound_b64}");
        snd.play().catch(e => {{ console.log("Audio waiting for gesture:", e); }});
    }} catch(e) {{}}
    </script>
    '''
    st.markdown(audio_html, unsafe_allow_html=True)

# ==============================================================================
# 🔴 ฝั่งร้านค้า (เคาน์เตอร์ & ครัว & รายงาน) -> https://.../?mode=admin
# ==============================================================================
if is_admin_mode:
    # Header ปรับขนาดอัตโนมัติตามหน้าจอ
    head_c1, head_c2 = st.columns([1, 6])
    with head_c1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=75)
        else:
            st.title("🌶️")
    with head_c2:
        st.markdown("<h2 style='color: #c2410c; margin: 0;'>ร้านฟ้าใสตำนัว (ระบบจัดการหลังร้าน)</h2>", unsafe_allow_html=True)
        st.caption("👨‍🍳 หน้าจอเคาน์เตอร์คิดเงิน • ครัวปรุงอาหาร • รายงานสต็อกวัตถุดิบ")

    st.write("---")

    tab_pos, tab_rep, tab_tbl = st.tabs([
        "🍳 จอครัว & เคาน์เตอร์คิดเงิน", 
        "📊 รายงาน & วางแผนเตรียมของ", 
        "🪑 จัดการโต๊ะอาหาร & เคลียร์โต๊ะ"
    ])

    with tab_pos:
        @st.fragment(run_every=3)
        def render_pos_dashboard():
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            # ตรวจจับออเดอร์ใหม่สถานะ pending ที่เพิ่งเข้ามา
            c.execute("SELECT MAX(id) FROM orders WHERE status = 'pending'")
            row_max = c.fetchone()
            cur_max = row_max[0] if (row_max and row_max[0]) else 0
            
            if 'last_seen_pending_id' not in st.session_state:
                st.session_state['last_seen_pending_id'] = cur_max
            elif cur_max > st.session_state['last_seen_pending_id']:
                st.session_state['last_seen_pending_id'] = cur_max
                play_order_sound()
                st.toast("🔔 มีออเดอร์ใหม่เข้ามาในครัวแล้วค่ะ!", icon="🛎️")
                st.warning("🔔 **มีออเดอร์ใหม่เพิ่งส่งเข้ามาในครัว!** กำลังรอให้กดรับออเดอร์")
            
            top_c1, top_c2 = st.columns([3, 1])
            with top_c1:
                st.caption("⚡ ระบบอัปเดตออเดอร์อัตโนมัติแบบเรียลไทม์ทุก 3 วินาที (ไม่ต้องกดรีเฟรชหน้าเว็บ)")
            with top_c2:
                if st.button("🔔 ทดสอบเสียงกระดิ่ง", key="btn_test_sound", use_container_width=True):
                    play_order_sound()
                    st.toast("ทดสอบเสียงกระดิ่งเตือนออเดอร์แล้ว 🔔", icon="🛎️")

            c.execute("SELECT COALESCE(SUM(total_price), 0), COUNT(*) FROM orders WHERE status IN ('paid', 'archived')")
            revenue, paid_cnt = c.fetchone()
            c.execute("SELECT COUNT(*), COUNT(DISTINCT table_id) FROM orders WHERE status NOT IN ('paid', 'archived')")
            active_cnt, active_tables = c.fetchone()
            
            # Responsive Metrics: บนมือถือจะเรียง 2x2 สวยงาม
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("💰 ยอดขายรวม", f"฿{int(revenue):,}")
            s2.metric("🍳 กำลังปรุง", f"{active_cnt} บิล")
            s3.metric("🪑 นั่งทาน", f"{active_tables} โต๊ะ")
            s4.metric("✅ เช็คบิลแล้ว", f"{paid_cnt} บิล")
            
            st.write("---")
            
            c.execute('''
                SELECT id, table_id, status, total_price, created_at 
                FROM orders 
                WHERE status NOT IN ('paid', 'archived')
                ORDER BY 
                    CASE status 
                        WHEN 'pending' THEN 1 
                        WHEN 'accepted' THEN 2 
                        WHEN 'cooked' THEN 3 
                        WHEN 'served' THEN 4 
                    END, id ASC
            ''')
            orders_to_manage = c.fetchall()
            
            if not orders_to_manage:
                st.success("🎉 ไม่มีออเดอร์ค้างในครัว น้องฟ้าใสพร้อมรับออเดอร์ใหม่เสมอค่ะ 🌶️")
            else:
                grid_cols = st.columns(3)
                for idx, (oid, t_id, st_code, total, otime) in enumerate(orders_to_manage):
                    with grid_cols[idx % 3]:
                        with st.container(border=True):
                            h1, h2 = st.columns([2, 1])
                            h1.markdown(f"### โต๊ะที่ {t_id}")
                            h2.caption(f"#{oid}")
                            st.caption(f"เวลาสั่ง: {otime}")
                            
                            c.execute("SELECT item_name, quantity, note FROM order_items WHERE order_id = ?", (oid,))
                            for iname, iqty, inote in c.fetchall():
                                st.markdown(f"• **{iname}** <span style='color: #ea580c; font-weight: bold;'>x{iqty}</span>", unsafe_allow_html=True)
                                if inote:
                                    st.caption(f"⚠️ โน้ต: {inote}")
                            
                            st.markdown(f"**ยอดรวม: ฿{int(total):,}**")
                            
                            if st_code == 'pending':
                                if st.button("1. ✅ กดรับออเดอร์", key=f"adm_acc_{oid}", use_container_width=True, type="primary"):
                                    c.execute("UPDATE orders SET status = 'accepted' WHERE id = ?", (oid,))
                                    conn.commit()
                                    st.rerun()
                            elif st_code == 'accepted':
                                if st.button("2. 🍳 ทำอาหารเสร็จ", key=f"adm_cook_{oid}", use_container_width=True):
                                    c.execute("UPDATE orders SET status = 'cooked' WHERE id = ?", (oid,))
                                    conn.commit()
                                    st.rerun()
                            elif st_code == 'cooked':
                                if st.button("3. 🍽️ นำเสิร์ฟแล้ว", key=f"adm_srv_{oid}", use_container_width=True):
                                    c.execute("UPDATE orders SET status = 'served' WHERE id = ?", (oid,))
                                    conn.commit()
                                    st.rerun()
                            elif st_code == 'served':
                                if st.button("4. 💵 รับเงิน (ปิดบิล)", key=f"adm_pay_{oid}", use_container_width=True, type="primary"):
                                    c.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (oid,))
                                    conn.commit()
                                    st.rerun()
                            
                            b_c1, b_c2 = st.columns(2)
                            with b_c1:
                                if st.button(f"🧾 เช็คบิลโต๊ะ {t_id}", key=f"adm_all_{oid}", use_container_width=True):
                                    c.execute("UPDATE orders SET status = 'paid' WHERE table_id = ?", (t_id,))
                                    conn.commit()
                                    st.rerun()
                            with b_c2:
                                if st.button(f"🧹 เคลียร์โต๊ะ {t_id}", key=f"adm_clr_{oid}", use_container_width=True, help="ล้างสถานะเพื่อรับลูกค้าใหม่"):
                                    c.execute("UPDATE orders SET status = 'archived' WHERE table_id = ?", (t_id,))
                                    conn.commit()
                                    st.toast(f"เคลียร์โต๊ะ {t_id} เรียบร้อยแล้ว โต๊ะพร้อมรับลูกค้าใหม่!", icon="✨")
                                    st.rerun()
            conn.close()

        render_pos_dashboard()

    with tab_rep:
        st.subheader("📊 ตารางวางแผนเตรียมวัตถุดิบอาหารล่วงหน้า (+15% Buffer)")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            SELECT r.ingredient_name, r.unit, SUM(r.quantity_per_portion * oi.quantity) as total_used
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN recipe_ingredients r ON oi.item_name = r.menu_name
            GROUP BY r.ingredient_name, r.unit
            ORDER BY total_used DESC
        ''')
        prep_data = c.fetchall()
        
        if prep_data:
            table_rows = []
            for ing, unit, used in prep_data:
                rec = round(used * 1.15, 1)
                step = "ชั่งแบ่ง Portion แช่เย็น"
                if "มะละกอ" in ing: step = "ขูดเส้น แช่น้ำเย็นให้กรอบ"
                elif "ไก่" in ing or "หมู" in ing: step = "หั่นและหมักเครื่องเทศข้ามคืน"
                elif "ข้าวเหนียว" in ing: step = "แช่น้ำเตรียมหุงร้อน"
                elif "ปลาร้า" in ing: step = "ต้มปรุงรส พักให้เย็น"
                table_rows.append({
                    "รายการวัตถุดิบ": ing,
                    "หน่วย": unit,
                    "ใช้ไปแล้ว (วันนี้)": f"{used:,}",
                    "แนะนำเตรียมพรุ่งนี้ (+15%)": f"{rec:,} {unit}",
                    "คำแนะนำ": step
                })
            st.dataframe(table_rows, use_container_width=True)
        else:
            st.info("ยังไม่มีข้อมูลการใช้วัตถุดิบในระบบ")
        conn.close()

    with tab_tbl:
        st.subheader("🪑 จัดการโต๊ะอาหาร & ล้างสถานะเพื่อรับลูกค้ารายใหม่")
        st.caption("เพิ่มหรือลบจำนวนโต๊ะในร้าน และกดล้างสถานะโต๊ะเมื่อลูกค้าทานเสร็จ เพื่อให้โต๊ะว่างพร้อมรับลูกค้ารายใหม่")
        
        conn_tb = sqlite3.connect(DB_NAME)
        c_tb = conn_tb.cursor()
        
        # ส่วนที่ 1: ล้างสถานะโต๊ะ (เคลียร์โต๊ะรับลูกค้าใหม่)
        st.markdown("### 🧹 1. ล้างสถานะโต๊ะอาหาร (พร้อมรับลูกค้ารายใหม่)")
        st.info("💡 การกด **'ล้างสถานะโต๊ะ'** จะทำให้หน้าจอมือถือของลูกค้ารายใหม่ที่สแกนโต๊ะนั้นเป็นหน้าว่างพร้อมสั่งอาหาร โดยยอดขายและรายงานสต็อกยังคงถูกบันทึกไว้อย่างปลอดภัย")
        
        c_tb.execute("""
            SELECT t.table_number, t.name,
                   COUNT(CASE WHEN o.status NOT IN ('paid', 'archived') THEN 1 END) as active_orders,
                   COUNT(CASE WHEN o.status = 'paid' THEN 1 END) as paid_orders
            FROM tables t
            LEFT JOIN orders o ON t.table_number = o.table_id
            GROUP BY t.table_number
            ORDER BY t.table_number ASC
        """)
        table_statuses = c_tb.fetchall()
        
        # ปุ่มล้างทุกโต๊ะที่เช็คบิลแล้วพร้อมกัน
        total_paid_orders = sum(r[3] for r in table_statuses)
        if total_paid_orders > 0:
            if st.button("🧹 ล้างสถานะทุกโต๊ะที่เช็คบิลแล้วพร้อมกันทั้งหมด", type="primary", use_container_width=True):
                c_tb.execute("UPDATE orders SET status = 'archived' WHERE status = 'paid'")
                conn_tb.commit()
                st.toast("ล้างสถานะทุกโต๊ะที่เช็คบิลแล้วเรียบร้อย!", icon="✨")
                st.rerun()
            st.write("")
        
        clr_cols = st.columns(3)
        for idx, (t_no, t_name, act_cnt, paid_cnt) in enumerate(table_statuses):
            with clr_cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"**🪑 {t_name}**")
                    if act_cnt > 0:
                        st.markdown(f"สถานะ: :orange[**มีออเดอร์ค้าง {act_cnt} บิล**]")
                    elif paid_cnt > 0:
                        st.markdown(f"สถานะ: :blue[**เช็คบิลแล้ว {paid_cnt} บิล (รอเคลียร์)**]")
                    else:
                        st.markdown(f"สถานะ: :green[**โต๊ะว่าง (พร้อมรับลูกค้า)**]")
                        
                    btn_type = "primary" if (paid_cnt > 0 or act_cnt > 0) else "secondary"
                    if st.button(f"🧹 ล้างสถานะโต๊ะ {t_no}", key=f"btn_clr_tbl_{t_no}", use_container_width=True, type=btn_type):
                        c_tb.execute("UPDATE orders SET status = 'archived' WHERE table_id = ?", (t_no,))
                        conn_tb.commit()
                        st.toast(f"ล้างสถานะ '{t_name}' เรียบร้อยแล้ว โต๊ะพร้อมรับลูกค้าใหม่!", icon="✨")
                        st.rerun()
                        
        st.write("---")
        
        # ส่วนที่ 2: เพิ่ม / ลบ โต๊ะอาหาร
        st.markdown("### ⚙️ 2. เพิ่ม / ลบ โต๊ะอาหารในร้าน")
        t_c1, t_c2 = st.columns(2)
        
        existing_nums = [r[0] for r in table_statuses]
        with t_c1:
            with st.container(border=True):
                st.markdown("#### ➕ เพิ่มโต๊ะใหม่")
                next_t_num = (max(existing_nums) + 1) if existing_nums else 1
                new_t_num = st.number_input("หมายเลขโต๊ะที่จะเพิ่ม:", min_value=1, max_value=999, value=next_t_num, step=1)
                new_t_name = st.text_input("ชื่อเรียกโต๊ะ:", value=f"โต๊ะที่ {new_t_num}")
                
                if st.button("➕ ยืนยันเพิ่มโต๊ะ", key="btn_add_new_table", type="primary", use_container_width=True):
                    if new_t_num in existing_nums:
                        st.error(f"หมายเลขโต๊ะ {new_t_num} มีอยู่ในระบบแล้วค่ะ")
                    else:
                        c_tb.execute("INSERT INTO tables (table_number, name) VALUES (?, ?)", (new_t_num, new_t_name))
                        conn_tb.commit()
                        st.success(f"เพิ่ม '{new_t_name}' สำเร็จเรียบร้อยแล้ว!")
                        st.rerun()

        with t_c2:
            with st.container(border=True):
                st.markdown("#### 🗑️ ลบโต๊ะอาหาร")
                if existing_nums:
                    table_options = [f"โต๊ะที่ {r[0]} ({r[1]})" for r in table_statuses]
                    table_to_del_str = st.selectbox("เลือกโต๊ะที่ต้องการลบ:", table_options)
                    del_t_num = int(table_to_del_str.split(" ")[1])
                    
                    if st.button(f"🗑️ ยืนยันลบโต๊ะที่ {del_t_num}", key="btn_del_table", use_container_width=True):
                        c_tb.execute("DELETE FROM tables WHERE table_number = ?", (del_t_num,))
                        conn_tb.commit()
                        st.warning(f"ลบโต๊ะที่ {del_t_num} ออกจากระบบเรียบร้อยแล้ว")
                        st.rerun()
                else:
                    st.info("ไม่มีโต๊ะในระบบ")

        conn_tb.close()

# ==============================================================================
# 🟢 ฝั่งลูกค้าสั่งอาหารที่โต๊ะ -> https://.../?table=1
# ==============================================================================
else:
    table_from_param = params.get("table", "1")
    conn_chk = sqlite3.connect(DB_NAME)
    c_chk = conn_chk.cursor()
    c_chk.execute("SELECT table_number FROM tables ORDER BY table_number ASC")
    valid_tables = [row[0] for row in c_chk.fetchall()]
    conn_chk.close()
    if not valid_tables:
        valid_tables = [1]
        
    try:
        current_table_num = int(table_from_param)
        if current_table_num not in valid_tables:
            current_table_num = valid_tables[0]
    except:
        current_table_num = valid_tables[0]

    # Header ลูกค้า: จัดกลางเสมอ สวยงาม ชัดเจน รองรับทุกขนาดหน้าจอ
    logo_b64 = get_base64_image(logo_path)
    if logo_b64:
        logo_html = f'''<div style="text-align: center; margin-bottom: 6px;">
            <img src="data:image/png;base64,{logo_b64}" 
                 style="width: 105px; height: 105px; object-fit: cover; border-radius: 50%; box-shadow: 0 4px 16px rgba(234, 88, 12, 0.28); display: inline-block; border: 3px solid #ffedd5;" 
                 alt="โลโก้ร้านฟ้าใสตำนัว" />
        </div>'''
    else:
        logo_html = '<div style="text-align: center; font-size: 55px; margin-bottom: 4px;">🌶️</div>'

    header_html = f'''
    {logo_html}
    <h1 style="text-align: center; color: #c2410c; font-weight: 800; font-size: 2.25rem; margin: 2px 0 0 0; letter-spacing: -0.5px; line-height: 1.2;">
        ร้านฟ้าใสตำนัว
    </h1>
    <p style="text-align: center; color: #78716c; font-size: 0.95rem; margin: 0 0 10px 0;">
        ส้มตำ ยำ ลาบ ย่าง แซ่บนัว สดใหม่ทุกครก 🌶️
    </p>
    <div style="text-align: center; margin: 6px 0 16px 0;">
        <div style="display: inline-block; background: linear-gradient(135deg, #ea580c, #c2410c); color: white; padding: 7px 30px; border-radius: 6px; font-size: 1.3rem; font-weight: 700; box-shadow: 0 4px 12px rgba(234, 88, 12, 0.35); letter-spacing: 0.5px;">
            🪑 โต๊ะที่ {current_table_num}
        </div>
    </div>
    '''
    st.markdown(header_html, unsafe_allow_html=True)
    st.write("---")

    # ฟังก์ชัน Callback สำหรับจัดการตะกร้าแบบเรียลไทม์ (Instant & Stable)
    def add_to_cart_item(item_name, item_price):
        if 'cart' not in st.session_state:
            st.session_state.cart = {}
        if item_name in st.session_state.cart:
            st.session_state.cart[item_name]['qty'] += 1
        else:
            st.session_state.cart[item_name] = {'price': item_price, 'qty': 1, 'note': ''}

    def dec_from_cart_item(item_name):
        if 'cart' in st.session_state and item_name in st.session_state.cart:
            if st.session_state.cart[item_name]['qty'] > 1:
                st.session_state.cart[item_name]['qty'] -= 1
            else:
                del st.session_state.cart[item_name]

    def del_from_cart_item(item_name):
        if 'cart' in st.session_state and item_name in st.session_state.cart:
            del st.session_state.cart[item_name]

    if 'cart' not in st.session_state:
        st.session_state.cart = {}

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT id, name, category, price, image, description 
        FROM menu_items 
        ORDER BY 
            CASE category 
                WHEN 'ส้มตำ & ตำนัว' THEN 1 
                WHEN 'ย่าง & ทอด & ลาบ' THEN 2 
                WHEN 'ต้ม & ซดร้อน' THEN 3 
                WHEN 'ข้าว & เครื่องเคียง' THEN 4 
                WHEN 'เครื่องดื่ม & หวาน' THEN 5 
                ELSE 6 
            END, id ASC
    ''')
    all_menus = c.fetchall()
    
    cat_order_list = ["ส้มตำ & ตำนัว", "ย่าง & ทอด & ลาบ", "ต้ม & ซดร้อน", "ข้าว & เครื่องเคียง", "เครื่องดื่ม & หวาน"]
    available_cats = list(set(m[2] for m in all_menus))
    categories = [cat for cat in cat_order_list if cat in available_cats]
    for cat in available_cats:
        if cat not in categories:
            categories.append(cat)
    
    st.markdown("<p style='text-align: center; font-weight: 600; color: #44403c; margin-bottom: 4px; font-size: 1.05rem;'>🍽️ เลือกหมวดหมู่อาหาร</p>", unsafe_allow_html=True)
    sel_cat = st.pills("เลือกหมวดหมู่อาหาร:", ["ทั้งหมด"] + categories, default="ทั้งหมด", key="pills_cat_sel", label_visibility="collapsed")
    if not sel_cat:
        sel_cat = "ทั้งหมด"
    
    # คำนวณยอดตะกร้า
    total_cart_qty = sum(item['qty'] for item in st.session_state.cart.values())
    total_cart_sum = sum(item['price'] * item['qty'] for item in st.session_state.cart.values())

    # แถบตะกร้าอาหาร เพื่อให้ลูกค้าสั่งและแก้ไขรายการได้สะดวก
    if total_cart_qty > 0:
        with st.container(border=True):
            st.markdown(f"<div style='text-align: center; font-size: 1.15rem; font-weight: 700; color: #1c1917; margin-bottom: 8px;'>🛒 ในตะกร้า: <span style='color: #ea580c;'>{total_cart_qty} รายการ</span> | รวม <span style='color: #ea580c;'>฿{int(total_cart_sum):,}</span></div>", unsafe_allow_html=True)
            with st.popover("👀 ดูตะกร้า & ยืนยันสั่งอาหาร", use_container_width=True):
                st.markdown(f"### 🛒 ตะกร้าอาหาร (โต๊ะ {current_table_num})")
                for item_name, data in list(st.session_state.cart.items()):
                    subtotal = data['price'] * data['qty']
                    with st.container():
                        st.markdown(f"**{item_name}** • <span style='color: #ea580c; font-weight: 600;'>฿{int(data['price'])} / จาน</span>", unsafe_allow_html=True)
                        
                        # แถวปุ่มปรับจำนวน: ➖ | ตัวเลขจำนวน | ➕ | 🗑️ ลบ
                        c_minus, c_num, c_plus, c_del = st.columns([1, 1.2, 1, 1.2])
                        with c_minus:
                            st.button("➖", key=f"cart_dec_{item_name}", on_click=dec_from_cart_item, args=(item_name,), use_container_width=True)
                        with c_num:
                            st.markdown(f"<div style='text-align: center; font-size: 1.25rem; font-weight: 700; line-height: 42px; background: #fff7ed; border-radius: 6px; border: 1.5px solid #fdba74; color: #c2410c;'>{data['qty']}</div>", unsafe_allow_html=True)
                        with c_plus:
                            st.button("➕", key=f"cart_inc_{item_name}", on_click=add_to_cart_item, args=(item_name, data['price']), use_container_width=True)
                        with c_del:
                            st.button("🗑️ ลบ", key=f"cart_rem_{item_name}", on_click=del_from_cart_item, args=(item_name,), use_container_width=True)
                                
                        st.caption(f"รวมย่อย: ฿{int(subtotal):,}")
                        note = st.text_input("โน้ตพิเศษ (เช่น เผ็ดน้อย/ไม่ใส่ชูรส):", value=data['note'], key=f"cart_note_{item_name}", placeholder="ระบุความต้องการ...")
                        st.session_state.cart[item_name]['note'] = note
                        st.write("---")
                
                st.markdown(f"#### ยอดรวมทั้งสิ้น: <span style='color: #ea580c;'>฿{int(total_cart_sum):,}</span>", unsafe_allow_html=True)
                if st.button("🚀 ยืนยันส่งออเดอร์เข้าครัว", type="primary", use_container_width=True):
                    c.execute("INSERT INTO orders (table_id, status, total_price, created_at) VALUES (?, 'pending', ?, datetime('now', 'localtime'))", (current_table_num, total_cart_sum))
                    new_order_id = c.lastrowid
                    for iname, idata in st.session_state.cart.items():
                        c.execute("INSERT INTO order_items (order_id, item_name, price, quantity, note) VALUES (?, ?, ?, ?, ?)", (new_order_id, iname, idata['price'], idata['qty'], idata['note']))
                    conn.commit()
                    st.session_state.cart = {}
                    st.success(f"🎉 ส่งออเดอร์ #{new_order_id} เรียบร้อยแล้วค่ะ!")
                    st.rerun()

    # แสดงรายการเมนูอาหาร แถวการ์ดแนวนอน (กดได้ทุกรายการ พร้อม Stepper ➖/➕ บนการ์ดโดยตรง)
    filtered_menus = all_menus if sel_cat == "ทั้งหมด" else [m for m in all_menus if m[2] == sel_cat]
    
    for m_id, name, cat, price, img, desc in filtered_menus:
        with st.container(border=True):
            mc_img, mc_info, mc_btn = st.columns([1.2, 3.2, 1.6])
            with mc_img:
                st.image(img, use_container_width=True)
            with mc_info:
                st.markdown(f"**{name}**")
                st.caption(desc)
                st.markdown(f"<span style='color: #ea580c; font-weight: bold; font-size: 1.15rem;'>฿{int(price)}</span>", unsafe_allow_html=True)
            with mc_btn:
                cur_qty = st.session_state.cart.get(name, {}).get('qty', 0)
                if cur_qty == 0:
                    st.button("➕ เพิ่ม", key=f"btn_add_menu_{m_id}", on_click=add_to_cart_item, args=(name, price), use_container_width=True)
                else:
                    c_m, c_q, c_p = st.columns([1, 1, 1])
                    with c_m:
                        st.button("➖", key=f"btn_dec_card_{m_id}", on_click=dec_from_cart_item, args=(name,), use_container_width=True)
                    with c_q:
                        st.markdown(f"<div style='text-align: center; font-weight: 700; line-height: 42px; color: #ea580c; font-size: 1.15rem;'>{cur_qty}</div>", unsafe_allow_html=True)
                    with c_p:
                        st.button("➕", key=f"btn_inc_card_{m_id}", on_click=add_to_cart_item, args=(name, price), use_container_width=True, type="primary")

    # ตรวจสอบสถานะอาหารที่สั่งไปแล้วของโต๊ะนี้ (ระบบเรียลไทม์ Auto-Refresh ทุก 3 วินาที)
    st.write("---")
    
    @st.fragment(run_every=3)
    def render_table_order_tracking(table_num):
        conn_trk = sqlite3.connect(DB_NAME)
        c_trk = conn_trk.cursor()
        
        # ดึงออเดอร์ล่าสุดของโต๊ะนี้
        c_trk.execute("""
            SELECT id, status, total_price, created_at 
            FROM orders 
            WHERE table_id = ? 
            ORDER BY id DESC LIMIT 5
        """, (table_num,))
        cur_orders = c_trk.fetchall()
        
        col_t_title, col_t_btn = st.columns([3, 1])
        with col_t_title:
            st.markdown(f"#### 📋 ติดตามสถานะอาหาร โต๊ะที่ {table_num} (เรียลไทม์ ⚡)")
            st.caption("ระบบจะอัปเดตสถานะอัตโนมัติทุก 3 วินาทีเมื่อครัวเปลี่ยนขั้นตอน")
        with col_t_btn:
            if st.button("🔄 รีเฟรช", key=f"btn_ref_table_{table_num}", use_container_width=True):
                st.rerun()

        if not cur_orders:
            st.info("ยังไม่มีรายการอาหารที่สั่งในขณะนี้ค่ะ สามารถเลือกเมนูแซ่บๆ ด้านบนแล้วส่งเข้าครัวได้เลยนะคะ 🌶️")
        else:
            st_map = {
                'pending': ('⏳ รอร้านรับออเดอร์', 'orange', 0.25, 'กำลังส่งออเดอร์เข้าจอครัว...'),
                'accepted': ('🍳 ครัวกำลังปรุงอาหาร', 'blue', 0.55, 'แม่ครัวกำลังตั้งกระทะ ปรุงสดใหม่ค่ะ'),
                'cooked': ('🍲 ปรุงเสร็จแล้ว รอเสิร์ฟ', 'purple', 0.85, 'อาหารปรุงเสร็จแล้ว พนักงานกำลังยกไปเสิร์ฟค่ะ'),
                'served': ('🍽️ เสิร์ฟถึงโต๊ะแล้ว', 'green', 1.0, 'เสิร์ฟครบแล้ว ทานให้อร่อยแซ่บนัวนะคะ!'),
                'paid': ('✅ เช็คบิลเรียบร้อยแล้ว', 'gray', 1.0, 'ขอบคุณที่มาอุดหนุนร้านฟ้าใสตำนัวนะคะ 🙏')
            }
            for oid, status, total, otime in cur_orders:
                label, color, prog_val, desc_status = st_map.get(status, (status, 'gray', 0.1, ''))
                with st.container(border=True):
                    c_oh1, c_oh2 = st.columns([3, 1])
                    with c_oh1:
                        st.markdown(f"**ออเดอร์ #{oid}** — <span style='font-size: 1.05rem; font-weight: bold;'>:{color}[{label}]</span>", unsafe_allow_html=True)
                        st.caption(f"⚡ {desc_status} • สั่งเมื่อ {otime}")
                    with c_oh2:
                        st.markdown(f"<div style='text-align: right; font-weight: bold; font-size: 1.1rem; color: #ea580c;'>฿{int(total):,}</div>", unsafe_allow_html=True)
                    
                    st.progress(prog_val)
                    
                    with st.expander("🔍 ดูรายการอาหารในบิลนี้", expanded=(status != 'paid')):
                        c_trk.execute("SELECT item_name, quantity, note FROM order_items WHERE order_id = ?", (oid,))
                        for iname, iqty, inote in c_trk.fetchall():
                            note_text = f" *(โน้ต: {inote})*" if inote else ""
                            st.write(f"- **{iname}** x{iqty}{note_text}")
        conn_trk.close()

    render_table_order_tracking(current_table_num)
    conn.close()
