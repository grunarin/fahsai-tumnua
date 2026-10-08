import streamlit as st
import sqlite3
import os
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

/* บังคับใช้ฟอนต์ Prompt ทั้งระบบ */
html, body, [class*="css"], .stMarkdown, p, span, button, input {
    font-family: 'Prompt', sans-serif !important;
}

/* ปรับระยะขอบหน้าจอให้พอดีกับมือถือ */
@media (max-width: 640px) {
    .main .block-container {
        padding: 0.75rem 0.5rem 3rem 0.5rem !important;
    }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.25rem !important; }
    h3 { font-size: 1.1rem !important; }
}

@media (min-width: 641px) and (max-width: 1024px) {
    .main .block-container {
        padding: 1.5rem 1.25rem 3rem 1.25rem !important;
    }
}

/* ปุ่มกดขนาดใหญ่ สัมผัสง่ายสำหรับนิ้วมือบนสมาร์ตโฟน (Touch-friendly 44px+) */
.stButton > button {
    border-radius: 14px !important;
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
    border-radius: 18px !important;
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

# ==============================================================================
# 🔴 ฝั่งร้านค้า (เคาน์เตอร์ & ครัว & รายงาน) -> https://.../?mode=admin
# ==============================================================================
if is_admin_mode:
    # Header ปรับขนาดอัตโนมัติตามหน้าจอ
    head_c1, head_c2, head_c3 = st.columns([1, 4, 2])
    with head_c1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=75)
        else:
            st.title("🌶️")
    with head_c2:
        st.markdown("<h2 style='color: #c2410c; margin: 0;'>ร้านฟ้าใสตำนัว (ระบบจัดการหลังร้าน)</h2>", unsafe_allow_html=True)
        st.caption("👨‍🍳 หน้าจอเคาน์เตอร์คิดเงิน • ครัวปรุงอาหาร • รายงานสต็อกวัตถุดิบ")
    with head_c3:
        if st.button("📱 สลับไปดูลูกค้าสั่ง", use_container_width=True):
            st.query_params.clear()
            st.rerun()

    st.write("---")

    tab_pos, tab_rep, tab_qr = st.tabs([
        "🍳 จอครัว & เคาน์เตอร์คิดเงิน", 
        "📊 รายงาน & วางแผนเตรียมของ", 
        "📲 เครื่องพิมพ์ QR Code โต๊ะ"
    ])

    with tab_pos:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        c.execute("SELECT COALESCE(SUM(total_price), 0), COUNT(*) FROM orders WHERE status = 'paid'")
        revenue, paid_cnt = c.fetchone()
        c.execute("SELECT COUNT(*), COUNT(DISTINCT table_id) FROM orders WHERE status != 'paid'")
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
            WHERE status != 'paid'
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
            # ใช้ Responsive 3 คอลัมน์ (บนมือถือจะ wrap ลงมาอัตโนมัติ)
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
                        
                        st.markdown(f"**ยอดรวม: ฿{int(total)}**")
                        
                        # ปุ่มกดสเต็ปการทำงาน
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
                        
                        if st.button(f"🧾 เช็คบิลโต๊ะ {t_id}", key=f"adm_all_{oid}", use_container_width=True):
                            c.execute("UPDATE orders SET status = 'paid' WHERE table_id = ?", (t_id,))
                            conn.commit()
                            st.rerun()
        conn.close()

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

    with tab_qr:
        st.subheader("📲 ลิงก์และ QR Code ประจำโต๊ะ (ให้ลูกค้าสแกน)")
        st.caption("ลูกค้าสแกน QR Code แล้วจะเข้าสู่หน้าสั่งอาหารเฉพาะโต๊ะนั้นทันที")
        
        base_app_url = "https://fahsai-tumnua-xwwixnezbpyxzpwvkvhad3.streamlit.app"
        
        qr_cols = st.columns(3)
        for i in range(1, 7):
            with qr_cols[(i-1) % 3]:
                with st.container(border=True):
                    st.markdown(f"### โต๊ะที่ {i}")
                    table_direct_url = f"{base_app_url}/?table={i}"
                    qr_img_api = f"https://quickchart.io/qr?text={table_direct_url}&size=200"
                    st.image(qr_img_api, width=170)
                    st.code(table_direct_url, language="text")

# ==============================================================================
# 🟢 ฝั่งลูกค้าสั่งอาหารที่โต๊ะ -> https://.../?table=1
# ==============================================================================
else:
    table_from_param = params.get("table", "1")
    try:
        current_table_num = int(table_from_param)
        if current_table_num < 1 or current_table_num > 6:
            current_table_num = 1
    except:
        current_table_num = 1

    # Header ลูกค้า: แสดงเฉพาะชื่อร้าน โต๊ะ และสโลแกน (ไม่มีปุ่มไปหลังร้านเด็ดขาด)
    col_l, col_t = st.columns([1, 5])
    with col_l:
        if os.path.exists(logo_path):
            st.image(logo_path, width=70)
        else:
            st.title("🌶️")
    with col_t:
        st.markdown(f"<h3 style='color: #c2410c; margin: 0;'>ร้านฟ้าใสตำนัว • โต๊ะที่ {current_table_num}</h3>", unsafe_allow_html=True)
        st.caption("ส้มตำ ยำ ลาบ ย่าง แซ่บนัว สดใหม่ทุกครก")

    st.write("---")

    if 'cart' not in st.session_state:
        st.session_state.cart = {}

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, category, price, image, description FROM menu_items')
    all_menus = c.fetchall()
    categories = sorted(list(set(m[2] for m in all_menus)))
    
    sel_cat = st.radio("เลือกหมวดหมู่อาหาร:", ["ทั้งหมด"] + categories, horizontal=True)
    
    # คำนวณยอดตะกร้า
    total_cart_qty = sum(item['qty'] for item in st.session_state.cart.values())
    total_cart_sum = sum(item['price'] * item['qty'] for item in st.session_state.cart.values())

    # แถบตะกร้าลอยด้านบน/ข้าง เพื่อให้ลูกค้าบนมือถือไม่ต้องเลื่อนหา
    if total_cart_qty > 0:
        with st.container(border=True):
            b_c1, b_c2 = st.columns([3, 2])
            b_c1.markdown(f"🛒 **ในตะกร้า:** {total_cart_qty} รายการ | รวม **฿{int(total_cart_sum)}**")
            with b_c2:
                with st.popover("👀 ดูตะกร้า & ยืนยันสั่ง", use_container_width=True):
                    st.markdown(f"### 🛒 ตะกร้าอาหาร (โต๊ะ {current_table_num})")
                    for item_name, data in list(st.session_state.cart.items()):
                        subtotal = data['price'] * data['qty']
                        st.markdown(f"**{item_name}** (฿{int(data['price'])} x {data['qty']} = ฿{int(subtotal)})")
                        p1, p2 = st.columns([3, 1])
                        with p1:
                            note = st.text_input("โน้ตพิเศษ:", value=data['note'], key=f"pop_note_{item_name}", placeholder="เผ็ดน้อย/ไม่พริก")
                            st.session_state.cart[item_name]['note'] = note
                        with p2:
                            if st.button("ลบ", key=f"pop_del_{item_name}"):
                                del st.session_state.cart[item_name]
                                st.rerun()
                        st.write("---")
                    
                    st.markdown(f"#### ยอดรวมทั้งสิ้น: <span style='color: #ea580c;'>฿{int(total_cart_sum)}</span>", unsafe_allow_html=True)
                    if st.button("🚀 ยืนยันส่งออเดอร์เข้าครัว", type="primary", use_container_width=True):
                        c.execute("INSERT INTO orders (table_id, status, total_price, created_at) VALUES (?, 'pending', ?, datetime('now', 'localtime'))", (current_table_num, total_cart_sum))
                        new_order_id = c.lastrowid
                        for iname, idata in st.session_state.cart.items():
                            c.execute("INSERT INTO order_items (order_id, item_name, price, quantity, note) VALUES (?, ?, ?, ?, ?)", (new_order_id, iname, idata['price'], idata['qty'], idata['note']))
                        conn.commit()
                        st.session_state.cart = {}
                        st.success(f"🎉 ส่งออเดอร์ #{new_order_id} เรียบร้อยแล้วค่ะ!")
                        st.rerun()

    # แสดงเมนูแบบการ์ด 2 คอลัมน์บนจอใหญ่ / 1 คอลัมน์บนมือถือ
    filtered_menus = all_menus if sel_cat == "ทั้งหมด" else [m for m in all_menus if m[2] == sel_cat]
    
    # จัดตารางการ์ดอาหารให้อ่านง่าย สบายตา
    menu_cols = st.columns(2)
    for idx, (m_id, name, cat, price, img, desc) in enumerate(filtered_menus):
        with menu_cols[idx % 2]:
            with st.container(border=True):
                mc_img, mc_info = st.columns([1, 2])
                with mc_img:
                    st.image(img, use_container_width=True)
                with mc_info:
                    st.markdown(f"**{name}**")
                    st.caption(desc)
                    st.markdown(f"<span style='color: #ea580c; font-weight: bold; font-size: 17px;'>฿{int(price)}</span>", unsafe_allow_html=True)
                    if st.button("➕ เพิ่ม", key=f"m_add_{m_id}", use_container_width=True):
                        if name in st.session_state.cart:
                            st.session_state.cart[name]['qty'] += 1
                        else:
                            st.session_state.cart[name] = {'price': price, 'qty': 1, 'note': ''}
                        st.toast(f"เพิ่ม '{name}' แล้ว!", icon="🍲")
                        st.rerun()

    # ตรวจสอบสถานะอาหารที่สั่งไปแล้วของโต๊ะนี้
    st.write("---")
    st.markdown(f"#### 📋 ติดตามสถานะอาหารของ โต๊ะที่ {current_table_num}")
    c.execute("SELECT id, status, total_price, created_at FROM orders WHERE table_id = ? AND status != 'paid' ORDER BY id DESC", (current_table_num,))
    cur_orders = c.fetchall()
    if not cur_orders:
        st.caption("ยังไม่มีรายการอาหารที่สั่งในขณะนี้ค่ะ")
    else:
        st_map = {
            'pending': ('⏳ รอร้านรับออเดอร์', 'orange'),
            'accepted': ('🍳 ครัวกำลังปรุง', 'blue'),
            'cooked': ('🍲 ปรุงเสร็จ รอเสิร์ฟ', 'purple'),
            'served': ('🍽️ เสิร์ฟแล้ว ทานให้อร่อยนะคะ', 'green')
        }
        for oid, status, total, otime in cur_orders:
            label, color = st_map.get(status, (status, 'gray'))
            with st.expander(f"ออเดอร์ #{oid} — สถานะ: :{color}[{label}] (฿{int(total)})", expanded=True):
                c.execute("SELECT item_name, quantity, note FROM order_items WHERE order_id = ?", (oid,))
                for iname, iqty, inote in c.fetchall():
                    st.write(f"- **{iname}** x{iqty} {' *(โน้ต: ' + inote + ')*' if inote else ''}")

    conn.close()
