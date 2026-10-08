import streamlit as st
import sqlite3
import os
from datetime import datetime, timedelta

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(
    page_title="ร้านฟ้าใสตำนัว - POS & Food Prep",
    page_icon="🌶️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_NAME = "restaurant.db"

# --- ฟังก์ชันจัดการฐานข้อมูล SQLite ---
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

    # เมนูเริ่มต้นร้าน "ฟ้าใสตำนัว"
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

    # วัตถุดิบและสัดส่วนต่อจาน
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

    # ข้อมูลตัวอย่างยอดขาย
    c.execute('SELECT COUNT(*) FROM orders')
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO orders (table_id, status, total_price, created_at) VALUES (1, 'served', 255, datetime('now', '-2 hours'))")
        oid1 = c.lastrowid
        c.execute("INSERT INTO order_items (order_id, item_name, price, cost, quantity, note) VALUES (?, 'ตำปูปลาร้านัวแซ่บ', 70, 25, 1, 'เผ็ดน้อย')", (oid1,))
        c.execute("INSERT INTO order_items (order_id, item_name, price, cost, quantity, note) VALUES (?, 'คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว', 120, 48, 1, '')", (oid1,))
        c.execute("INSERT INTO order_items (order_id, item_name, price, cost, quantity, note) VALUES (?, 'ข้าวเหนียวเขี้ยวงูอบนุ่ม', 20, 6, 2, '')", (oid1,))
        c.execute("INSERT INTO order_items (order_id, item_name, price, cost, quantity, note) VALUES (?, 'ชาไทยเย็นสูตรโบราณ', 45, 14, 1, '')", (oid1,))

        c.execute("INSERT INTO orders (table_id, status, total_price, created_at) VALUES (2, 'accepted', 329, datetime('now', '-45 minutes'))")
        oid2 = c.lastrowid
        c.execute("INSERT INTO order_items (order_id, item_name, price, cost, quantity, note) VALUES (?, 'ตำถาดฟ้าใสรวมมิตร', 199, 75, 1, '')", (oid2,))
        c.execute("INSERT INTO order_items (order_id, item_name, price, cost, quantity, note) VALUES (?, 'ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา', 130, 45, 1, '')", (oid2,))

    conn.commit()
    conn.close()

init_db()

# Session State สำหรับตะกร้าสินค้า
if 'cart' not in st.session_state:
    st.session_state.cart = {}

# --- Header & Logo ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    logo_path = "static/img/logo.png"
    if not os.path.exists(logo_path):
        logo_path = "templates/img/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=110)
    else:
        st.title("🌶️")

with col_title:
    st.markdown("<h1 style='color: #c2410c; margin-bottom: 0px;'>ร้านฟ้าใสตำนัว 🌶️</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 15px;'>ส้มตำ ยำ ลาบ ย่าง ต้มแซ่บ • ระบบสั่งอาหารโต๊ะ & จัดการสต็อกวัตถุดิบ</p>", unsafe_allow_html=True)

st.write("---")

# --- แถบเมนูหลัก 4 โหมด ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📱 สั่งอาหารที่โต๊ะ (ลูกค้า)", 
    "👨‍🍳 เคาน์เตอร์ & ห้องครัว", 
    "📊 รายงานยอดขาย & วางแผนเตรียมของ",
    "📲 ดู QR Code แต่ละโต๊ะ"
])

# ================= TAB 1: ลูกค้าสั่งอาหาร =================
with tab1:
    c_table, c_status = st.columns([2, 4])
    with c_table:
        # อ่านค่า table จาก URL Query Params หากมี เช่น ?table=2
        query_params = st.query_params
        default_table_idx = 0
        if "table" in query_params:
            try:
                t_val = int(query_params["table"])
                if 1 <= t_val <= 6:
                    default_table_idx = t_val - 1
            except:
                pass
        
        selected_table = st.selectbox(
            "📍 เลือกโต๊ะอาหารของคุณ:", 
            [f"โต๊ะที่ {i}" for i in range(1, 7)],
            index=default_table_idx
        )
        table_num = int(selected_table.split(" ")[1])

    with c_status:
        st.info(f"✨ กำลังสั่งอาหารสำหรับ **{selected_table}** (อาหารจะส่งตรงไปยังจอครัว)")

    # ดึงเมนูจากฐานข้อมูล
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, category, price, image, description FROM menu_items')
    all_menus = c.fetchall()
    categories = sorted(list(set(m[2] for m in all_menus)))
    
    # หมวดหมู่
    sel_cat = st.radio("หมวดหมู่อาหาร:", ["ทั้งหมด"] + categories, horizontal=True)
    
    col_menu, col_cart = st.columns([3, 2])
    
    with col_menu:
        filtered_menus = all_menus if sel_cat == "ทั้งหมด" else [m for m in all_menus if m[2] == sel_cat]
        for m_id, name, cat, price, img, desc in filtered_menus:
            with st.container(border=True):
                m_c1, m_c2 = st.columns([1, 2])
                with m_c1:
                    st.image(img, use_container_width=True)
                with m_c2:
                    st.markdown(f"**{name}**")
                    st.caption(desc)
                    st.markdown(f"<span style='color: #ea580c; font-weight: bold; font-size: 18px;'>฿{int(price)}</span>", unsafe_allow_html=True)
                    
                    btn_add = st.button(f"➕ เพิ่มลงตะกร้า", key=f"add_{m_id}")
                    if btn_add:
                        if name in st.session_state.cart:
                            st.session_state.cart[name]['qty'] += 1
                        else:
                            st.session_state.cart[name] = {'price': price, 'qty': 1, 'note': ''}
                        st.toast(f"เพิ่ม '{name}' ลงตะกร้าแล้ว!", icon="🍲")
                        st.rerun()

    # ฝั่งตะกร้าอาหาร
    with col_cart:
        with st.container(border=True):
            st.subheader(f"🛒 ตะกร้าอาหาร ({selected_table})")
            if not st.session_state.cart:
                st.write("ยังไม่มีรายการอาหารในตะกร้า")
            else:
                total_sum = 0
                for item_name, data in list(st.session_state.cart.items()):
                    subtotal = data['price'] * data['qty']
                    total_sum += subtotal
                    
                    st.markdown(f"**{item_name}**")
                    r1, r2, r3 = st.columns([2, 2, 1])
                    with r1:
                        st.caption(f"฿{int(data['price'])} x {data['qty']} = **฿{int(subtotal)}**")
                    with r2:
                        note = st.text_input("โน้ตพิเศษ (เช่น เผ็ดน้อย):", value=data['note'], key=f"note_{item_name}", placeholder="เผ็ดน้อย/ไม่ผัก")
                        st.session_state.cart[item_name]['note'] = note
                    with r3:
                        if st.button("🗑️", key=f"del_{item_name}"):
                            del st.session_state.cart[item_name]
                            st.rerun()
                    st.write("---")

                st.markdown(f"### ยอดรวมทั้งสิ้น: <span style='color: #ea580c;'>฿{int(total_sum)}</span>", unsafe_allow_html=True)
                
                if st.button("🚀 ยืนยันส่งออเดอร์เข้าครัว", type="primary", use_container_width=True):
                    # บันทึกลงฐานข้อมูล SQLite
                    c.execute("INSERT INTO orders (table_id, status, total_price, created_at) VALUES (?, 'pending', ?, datetime('now', 'localtime'))", (table_num, total_sum))
                    new_order_id = c.lastrowid
                    for iname, idata in st.session_state.cart.items():
                        c.execute("INSERT INTO order_items (order_id, item_name, price, quantity, note) VALUES (?, ?, ?, ?, ?)", (new_order_id, iname, idata['price'], idata['qty'], idata['note']))
                    conn.commit()
                    st.session_state.cart = {}
                    st.success(f"🎉 ส่งออเดอร์ #{new_order_id} เข้าครัวเรียบร้อยแล้วค่ะ!")
                    st.rerun()

    # แสดงประวัติออเดอร์ของโต๊ะนี้
    st.write("---")
    st.subheader(f"📋 ประวัติและสถานะอาหารของ {selected_table}")
    c.execute("SELECT id, status, total_price, created_at FROM orders WHERE table_id = ? AND status != 'paid' ORDER BY id DESC", (table_num,))
    cur_orders = c.fetchall()
    if not cur_orders:
        st.caption("ไม่มีออเดอร์ที่กำลังปรุงในขณะนี้")
    else:
        st_map = {
            'pending': ('⏳ รอร้านรับออเดอร์', 'orange'),
            'accepted': ('🍳 ครัวกำลังปรุง', 'blue'),
            'cooked': ('🍲 ปรุงเสร็จ รอเสิร์ฟ', 'purple'),
            'served': ('🍽️ เสิร์ฟแล้ว (ทานให้อร่อยนะคะ)', 'green')
        }
        for oid, status, total, otime in cur_orders:
            label, color = st_map.get(status, (status, 'gray'))
            with st.expander(f"ออเดอร์ #{oid} — สถานะ: :{color}[{label}] (฿{int(total)})"):
                c.execute("SELECT item_name, quantity, note FROM order_items WHERE order_id = ?", (oid,))
                for iname, iqty, inote in c.fetchall():
                    st.write(f"- **{iname}** x{iqty} {' *(โน้ต: ' + inote + ')*' if inote else ''}")

    conn.close()

# ================= TAB 2: เคาน์เตอร์ & ครัว =================
with tab2:
    st.subheader("👨‍🍳 จอเคาน์เตอร์คิดเงินและห้องครัว")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # สถิติด้านบน
    c.execute("SELECT COALESCE(SUM(total_price), 0), COUNT(*) FROM orders WHERE status = 'paid'")
    revenue, paid_cnt = c.fetchone()
    c.execute("SELECT COUNT(*), COUNT(DISTINCT table_id) FROM orders WHERE status != 'paid'")
    active_cnt, active_tables = c.fetchone()
    
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("💰 ยอดขายรวม (เช็คบิลแล้ว)", f"฿{int(revenue):,}")
    s2.metric("🍳 ออเดอร์กำลังปรุง", f"{active_cnt} บิล")
    s3.metric("🪑 โต๊ะที่กำลังนั่งทาน", f"{active_tables} โต๊ะ")
    s4.metric("✅ บิลที่ปิดแล้ว", f"{paid_cnt} โต๊ะ")
    
    st.write("---")
    
    # ดึงออเดอร์ที่ยังไม่ปิดบิล
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
        grid_cols = st.columns(3)
        for idx, (oid, t_id, st_code, total, otime) in enumerate(orders_to_manage):
            col_target = grid_cols[idx % 3]
            with col_target:
                with st.container(border=True):
                    h1, h2 = st.columns([2, 1])
                    h1.markdown(f"### โต๊ะที่ {t_id}")
                    h2.caption(f"#{oid}")
                    
                    st.caption(f"เวลาสั่ง: {otime}")
                    
                    # รายการอาหาร
                    c.execute("SELECT item_name, quantity, note FROM order_items WHERE order_id = ?", (oid,))
                    for iname, iqty, inote in c.fetchall():
                        st.markdown(f"• **{iname}** <span style='color: #ea580c;'>x{iqty}</span>", unsafe_allow_html=True)
                        if inote:
                            st.caption(f"⚠️ โน้ต: {inote}")
                    
                    st.write(f"**ยอดรวม: ฿{int(total)}**")
                    
                    # ปุ่มเปลี่ยนสถานะ
                    if st_code == 'pending':
                        if st.button("1. ✅ กดรับออเดอร์", key=f"btn_accept_{oid}", use_container_width=True, type="primary"):
                            c.execute("UPDATE orders SET status = 'accepted' WHERE id = ?", (oid,))
                            conn.commit()
                            st.rerun()
                    elif st_code == 'accepted':
                        if st.button("2. 🍳 ทำอาหารเสร็จ", key=f"btn_cook_{oid}", use_container_width=True):
                            c.execute("UPDATE orders SET status = 'cooked' WHERE id = ?", (oid,))
                            conn.commit()
                            st.rerun()
                    elif st_code == 'cooked':
                        if st.button("3. 🍽️ นำเสิร์ฟแล้ว", key=f"btn_serve_{oid}", use_container_width=True):
                            c.execute("UPDATE orders SET status = 'served' WHERE id = ?", (oid,))
                            conn.commit()
                            st.rerun()
                    elif st_code == 'served':
                        if st.button("4. 💵 รับเงิน (ปิดบิล)", key=f"btn_pay_{oid}", use_container_width=True, type="primary"):
                            c.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (oid,))
                            conn.commit()
                            st.rerun()
                    
                    if st.button(f"🧾 เช็คบิลโต๊ะ {t_id}", key=f"btn_pay_all_{oid}"):
                        c.execute("UPDATE orders SET status = 'paid' WHERE table_id = ?", (t_id,))
                        conn.commit()
                        st.rerun()

    conn.close()

# ================= TAB 3: รายงาน & วางแผนเตรียมของ =================
with tab3:
    st.subheader("📊 รายงานการขาย & ตารางวางแผนเตรียมวัตถุดิบ (Food Prep Planner)")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # คำนวณปริมาณวัตถุดิบที่ใช้ไป
    c.execute('''
        SELECT r.ingredient_name, r.unit, SUM(r.quantity_per_portion * oi.quantity) as total_used
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN recipe_ingredients r ON oi.item_name = r.menu_name
        GROUP BY r.ingredient_name, r.unit
        ORDER BY total_used DESC
    ''')
    prep_data = c.fetchall()
    
    st.markdown("#### 🍲 ปริมาณวัตถุดิบที่ใช้ & แนะนำเตรียมสต็อกล่วงหน้า (+15% Buffer)")
    st.caption("ระบบคำนวณจากยอดอาหารที่ขายจริง เพื่อช่วยให้แม่ครัวชั่งและหมักวัตถุดิบล่วงหน้า")
    
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
        st.info("ยังไม่มีข้อมูลการใช้วัตถุดิบ")
        
    st.write("---")
    
    # อันดับเมนูขายดี
    st.markdown("#### 🏆 อันดับเมนูขายดีประจำร้าน")
    c.execute('''
        SELECT oi.item_name, m.category, SUM(oi.quantity) as qty, SUM(oi.price * oi.quantity) as rev
        FROM order_items oi
        JOIN menu_items m ON oi.item_name = m.name
        GROUP BY oi.item_name
        ORDER BY qty DESC
    ''')
    best_sellers = c.fetchall()
    if best_sellers:
        bs_rows = [{"อันดับ": idx+1, "ชื่อเมนู": r[0], "หมวดหมู่": r[1], "จำนวน (จาน)": r[2], "ยอดขาย (บาท)": f"฿{int(r[3]):,}"} for idx, r in enumerate(best_sellers)]
        st.dataframe(bs_rows, use_container_width=True)

    conn.close()

# ================= TAB 4: QR CODE แต่ละโต๊ะ =================
with tab4:
    st.subheader("📲 QR Code สั่งอาหารประจำโต๊ะ (โต๊ะ 1 - 6)")
    st.caption("ลูกค้าใช้มือถือสแกน QR Code เพื่อเปิดหน้าสั่งอาหารของโต๊ะนั้นได้ทันที")
    
    qr_cols = st.columns(3)
    for i in range(1, 7):
        target_col = qr_cols[(i-1) % 3]
        with target_col:
            with st.container(border=True):
                st.markdown(f"### โต๊ะที่ {i}")
                # สร้างลิงก์ QR code โดยใช้ quickchart API (รูปภาพโหลดได้ทันทีบน Streamlit)
                # เมื่อขึ้น Streamlit Cloud ลิงก์จะเป็น URL จริง
                current_url = "https://fahsai-tumnua.streamlit.app"
                table_link = f"{current_url}?table={i}"
                qr_api = f"https://quickchart.io/qr?text={table_link}&size=200"
                st.image(qr_api, width=180)
                st.caption(f"ลิงก์: {table_link}")
