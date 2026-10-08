import sqlite3
import json
import socket
import csv
import io
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, send_from_directory

app = Flask(__name__, static_folder='static')
DB_NAME = "restaurant.db"
RESTAURANT_NAME = "ฟ้าใสตำนัว"

@app.route('/img/<path:filename>')
def serve_img(filename):
    return send_from_directory('static/img', filename)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def init_db(force_reset=False):
    if force_reset and os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. ตารางเมนูอาหาร
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
    
    # 2. ตารางสูตรอาหารและวัตถุดิบ (Recipe & Ingredients)
    c.execute('''
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            menu_name TEXT NOT NULL,
            ingredient_name TEXT NOT NULL,
            quantity_per_portion REAL NOT NULL,
            unit TEXT NOT NULL
        )
    ''')

    # 3. ตารางออเดอร์
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            total_price REAL NOT NULL,
            payment_method TEXT DEFAULT 'cash',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. ตารางรายการย่อยในออเดอร์
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            price REAL NOT NULL,
            cost REAL DEFAULT 0,
            quantity INTEGER NOT NULL,
            note TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    ''')

    # เมนูอาหารประจำร้าน "ฟ้าใสตำนัว" (ส้มตำ ยำ ลาบ ย่าง ต้มแซ่บ)
    fahsai_menu = [
        # หมวด: ส้มตำ & ตำนัว
        ("ตำปูปลาร้านัวแซ่บ", "ส้มตำ & ตำนัว", 70, 25, "https://images.unsplash.com/photo-1569058242253-92a9c755a0ec?auto=format&fit=crop&w=600&q=80", "เส้นมะละกอกรอบ ตำกับพริกแห้งและน้ำปลาร้าต้มสุกสูตรฟ้าใส นัวเข้มข้นถึงใจ"),
        ("ตำไทยไข่เค็ม", "ส้มตำ & ตำนัว", 80, 28, "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80", "รสเปรี้ยวหวานกลมกล่อม กุ้งแห้งคัดพิเศษ ถั่วลิสงคั่วใหม่ ท็อปไข่เค็มเต็มใบ"),
        ("ตำข้าวโพดกุ้งสด", "ส้มตำ & ตำนัว", 130, 50, "https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=600&q=80", "ข้าวโพดหวานคลุกเคล้าน้ำยำสุดแซ่บ พร้อมกุ้งสดตัวโตเนื้อเด้งหวานฉ่ำ"),
        ("ตำถาดฟ้าใสรวมมิตร", "ส้มตำ & ตำนัว", 199, 75, "https://images.unsplash.com/photo-1603133872878-684f208fb84b?auto=format&fit=crop&w=600&q=80", "ตำถาดเครื่องแน่น! เสิร์ฟพร้อมแคบหมู หมูยออุบล ไข่ต้ม ขนมจีน และผักเคียงครบครัน"),
        
        # หมวด: ลาบ ยำ & ต้มแซ่บ
        ("คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว", "ย่าง & ทอด & ลาบ", 120, 48, "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80", "คอหมูแท้แทรกมันย่างเตาถ่านหอมกรุ่น นุ่มฉ่ำ เสิร์ฟคู่น้ำจิ้มแจ่วมะขามเปียกข้าวคั่ว"),
        ("ไก่ย่างสมุนไพรเขาสวนกวาง", "ย่าง & ทอด & ลาบ", 140, 55, "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?auto=format&fit=crop&w=600&q=80", "ไก่บ้านหมักสมุนไพรไทย ย่างหนังกรอบเนื้อนุ่มฉ่ำ หอมกระเทียมพริกไทย"),
        ("ลาบหมูสับตับหวานข้าวคั่ว", "ย่าง & ทอด & ลาบ", 95, 36, "https://images.unsplash.com/photo-1548943487-a2e4e43b4853?auto=format&fit=crop&w=600&q=80", "หมูสับเนื้อเน้นคลุกตับลวกพอสุก หอมกลิ่นข้าวคั่วใหม่และสะระแหน่"),
        ("ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา", "ต้ม & ซดร้อน", 130, 45, "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80", "กระดูกหมูอ่อนเคี่ยวจนเปื่อยนุ่ม ซุปสมุนไพรเปรี้ยวเผ็ดร้อน ซดคล่องคอ"),
        ("ปีกไก่ทอดน้ำปลาหอมกรอบ", "ย่าง & ทอด & ลาบ", 90, 35, "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?auto=format&fit=crop&w=600&q=80", "ปีกไก่ทอดกรอบสีทอง หอมน้ำปลาแท้ ไม่อมน้ำมัน เมนูขวัญใจเด็กและผู้ใหญ่"),

        # หมวด: ข้าว & เครื่องเคียง
        ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", "ข้าว & เครื่องเคียง", 20, 6, "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?auto=format&fit=crop&w=600&q=80", "ข้าวเหนียวคัดเกรด เมล็ดเรียวยาว นึ่งร้อนๆ เหนียวนุ่มตลอดมื้อ"),
        ("ขนมจีนแป้งหมัก", "ข้าว & เครื่องเคียง", 20, 6, "https://images.unsplash.com/photo-1612927601601-6638404737ce?auto=format&fit=crop&w=600&q=80", "เส้นขนมจีนนุ่มลื่น ทานคู่ส้มตำแซ่บๆ เข้ากันเป็นที่สุด"),
        ("แคบหมูไร้มันกรอบโบราณ", "ข้าว & เครื่องเคียง", 30, 10, "https://images.unsplash.com/photo-1541529086526-db283c563270?auto=format&fit=crop&w=600&q=80", "แคบหมูทอดกรอบไม่อมน้ำมัน เคี้ยวเพลิน"),

        # หมวด: เครื่องดื่ม & ของหวาน
        ("ชาไทยเย็นสูตรโบราณ", "เครื่องดื่ม & หวาน", 45, 14, "https://images.unsplash.com/photo-1558857563-b371033873b8?auto=format&fit=crop&w=600&q=80", "ชาใบเข้มข้น หอมมันนมสดแท้ ดับเผ็ดได้เป็นอย่างดี"),
        ("น้ำเก๊กฮวยต้มสมุนไพรสดชื่น", "เครื่องดื่ม & หวาน", 35, 10, "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=600&q=80", "เก๊กฮวยดอกแท้ต้มใบเตย หอมละมุน หวานน้อย ชื่นใจ"),
        ("ลอดช่องสิงคโปร์กะทิสดน้ำตาลโตนด", "เครื่องดื่ม & หวาน", 50, 18, "https://images.unsplash.com/photo-1563805042-7684c019e1cb?auto=format&fit=crop&w=600&q=80", "เส้นลอดช่องเหนียวนุ่ม กะทิอบควันเทียนหอมหวานชื่นใจ")
    ]
    
    for item in fahsai_menu:
        c.execute('''
            INSERT OR REPLACE INTO menu_items (name, category, price, cost, image, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', item)

    # วัตถุดิบและสัดส่วนต่อจาน สำหรับ "ฟ้าใสตำนัว" เพื่อวางแผนเตรียมของ
    recipes = [
        # ตำปูปลาร้า
        ("ตำปูปลาร้านัวแซ่บ", "เส้นมะละกอดิบขูด", 180, "กรัม"),
        ("ตำปูปลาร้านัวแซ่บ", "น้ำปลาร้าต้มสุกปรุงรส", 45, "มล."),
        ("ตำปูปลาร้านัวแซ่บ", "พริกสด & พริกแห้ง", 20, "กรัม"),
        ("ตำปูปลาร้านัวแซ่บ", "มะนาวแป้นสด", 1, "ลูก"),
        ("ตำปูปลาร้านัวแซ่บ", "มะเขือเทศสีดา", 35, "กรัม"),

        # ตำไทยไข่เค็ม
        ("ตำไทยไข่เค็ม", "เส้นมะละกอดิบขูด", 180, "กรัม"),
        ("ตำไทยไข่เค็ม", "ไข่เค็ม", 1, "ฟอง"),
        ("ตำไทยไข่เค็ม", "กุ้งแห้ง", 15, "กรัม"),
        ("ตำไทยไข่เค็ม", "ถั่วลิสงคั่ว", 20, "กรัม"),
        ("ตำไทยไข่เค็ม", "มะนาวแป้นสด", 1, "ลูก"),

        # ตำข้าวโพดกุ้งสด
        ("ตำข้าวโพดกุ้งสด", "ข้าวโพดหวานต้มฝาน", 150, "กรัม"),
        ("ตำข้าวโพดกุ้งสด", "กุ้งสดแกะเปลือก", 4, "ตัว"),
        ("ตำข้าวโพดกุ้งสด", "มะนาวแป้นสด", 1.5, "ลูก"),

        # ตำถาด
        ("ตำถาดฟ้าใสรวมมิตร", "เส้นมะละกอดิบขูด", 200, "กรัม"),
        ("ตำถาดฟ้าใสรวมมิตร", "น้ำปลาร้าต้มสุกปรุงรส", 50, "มล."),
        ("ตำถาดฟ้าใสรวมมิตร", "หมูยออุบลนึ่ง", 80, "กรัม"),
        ("ตำถาดฟ้าใสรวมมิตร", "ไข่ต้มยางมะตูม", 1, "ฟอง"),
        ("ตำถาดฟ้าใสรวมมิตร", "แคบหมู", 30, "กรัม"),
        ("ตำถาดฟ้าใสรวมมิตร", "ขนมจีน", 100, "กรัม"),

        # คอหมูย่าง
        ("คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว", "คอหมูสดหมักเครื่องเทศ", 220, "กรัม"),
        ("คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว", "ข้าวคั่ว & พริกป่นแจ่ว", 20, "กรัม"),

        # ไก่ย่างเขาสวนกวาง
        ("ไก่ย่างสมุนไพรเขาสวนกวาง", "ไก่สดหมักสมุนไพร", 350, "กรัม"),

        # ลาบหมู
        ("ลาบหมูสับตับหวานข้าวคั่ว", "หมูบดสด", 150, "กรัม"),
        ("ลาบหมูสับตับหวานข้าวคั่ว", "ตับหมูสด", 50, "กรัม"),
        ("ลาบหมูสับตับหวานข้าวคั่ว", "ข้าวคั่วหอม & ผักชีใบเลื่อย", 25, "กรัม"),

        # ต้มแซ่บ
        ("ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา", "กระดูกหมูอ่อน", 200, "กรัม"),
        ("ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา", "สมุนไพรต้มแซ่บ (ข่า ตะไคร้ กะเพรา)", 40, "กรัม"),

        # ปีกไก่ทอด
        ("ปีกไก่ทอดน้ำปลาหอมกรอบ", "ปีกไก่สด", 250, "กรัม"),

        # ข้าวเหนียว
        ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", "ข้าวเหนียวดิบเขี้ยวงู", 120, "กรัม"),

        # ชาไทย
        ("ชาไทยเย็นสูตรโบราณ", "ใบชาไทย", 25, "กรัม"),
        ("ชาไทยเย็นสูตรโบราณ", "นมสด & นมข้น", 120, "มล.")
    ]

    c.execute('DELETE FROM recipe_ingredients')
    c.executemany('''
        INSERT INTO recipe_ingredients (menu_name, ingredient_name, quantity_per_portion, unit)
        VALUES (?, ?, ?, ?)
    ''', recipes)

    # ข้อมูลตัวอย่างยอดขายร้าน "ฟ้าใสตำนัว"
    c.execute('SELECT COUNT(*) FROM orders')
    if c.fetchone()[0] == 0:
        seed_fahsai_sales(c)

    conn.commit()
    conn.close()

# เรียกใช้งาน init_db ทันทีเมื่อแอปเริ่มทำงาน (สำคัญมากสำหรับ Render / Gunicorn)
init_db(force_reset=False)

def seed_fahsai_sales(cursor):
    """ยอดขายจำลองของร้าน ฟ้าใสตำนัว เพื่อดูรายงาน"""
    sample_data = [
        # (days_ago, hour, table_id, [(item_name, qty)])
        (2, "11:45", 1, [("ตำปูปลาร้านัวแซ่บ", 2), ("ไก่ย่างสมุนไพรเขาสวนกวาง", 1), ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", 3)]),
        (2, "12:15", 3, [("ตำถาดฟ้าใสรวมมิตร", 1), ("คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว", 2), ("ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา", 1), ("ชาไทยเย็นสูตรโบราณ", 3)]),
        (2, "13:00", 2, [("ตำไทยไข่เค็ม", 1), ("ปีกไก่ทอดน้ำปลาหอมกรอบ", 1), ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", 2)]),
        (2, "18:30", 4, [("ตำปูปลาร้านัวแซ่บ", 3), ("คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว", 2), ("ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา", 2), ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", 4), ("น้ำเก๊กฮวยต้มสมุนไพรสดชื่น", 3)]),
        (2, "19:15", 5, [("ตำข้าวโพดกุ้งสด", 2), ("ลาบหมูสับตับหวานข้าวคั่ว", 1), ("แคบหมูไร้มันกรอบโบราณ", 2)]),

        (1, "11:30", 2, [("ตำปูปลาร้านัวแซ่บ", 3), ("คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว", 2), ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", 4)]),
        (1, "12:05", 4, [("ตำถาดฟ้าใสรวมมิตร", 1), ("ไก่ย่างสมุนไพรเขาสวนกวาง", 1), ("ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา", 1), ("ชาไทยเย็นสูตรโบราณ", 2)]),
        (1, "12:50", 1, [("ตำไทยไข่เค็ม", 2), ("ปีกไก่ทอดน้ำปลาหอมกรอบ", 1), ("ขนมจีนแป้งหมัก", 2)]),
        (1, "18:00", 6, [("ตำปูปลาร้านัวแซ่บ", 4), ("คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว", 3), ("ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา", 2), ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", 5)]),
        (1, "19:20", 3, [("ตำข้าวโพดกุ้งสด", 2), ("ลาบหมูสับตับหวานข้าวคั่ว", 2), ("น้ำเก๊กฮวยต้มสมุนไพรสดชื่น", 2), ("ลอดช่องสิงคโปร์กะทิสดน้ำตาลโตนด", 2)]),

        (0, "11:20", 1, [("ตำปูปลาร้านัวแซ่บ", 2), ("คอหมูย่างฉ่ำซอสน้ำจิ้มแจ่ว", 1), ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", 2)]),
        (0, "12:00", 2, [("ตำถาดฟ้าใสรวมมิตร", 1), ("ไก่ย่างสมุนไพรเขาสวนกวาง", 1), ("ต้มแซ่บกระดูกอ่อนหมูใบกะเพรา", 1), ("ชาไทยเย็นสูตรโบราณ", 2)]),
        (0, "12:45", 5, [("ตำไทยไข่เค็ม", 1), ("ปีกไก่ทอดน้ำปลาหอมกรอบ", 1), ("ข้าวเหนียวเขี้ยวงูอบนุ่ม", 1)]),
        (0, "13:10", 3, [("ตำปูปลาร้านัวแซ่บ", 1), ("ลาบหมูสับตับหวานข้าวคั่ว", 1), ("น้ำเก๊กฮวยต้มสมุนไพรสดชื่น", 1)])
    ]

    now = datetime.now()
    cursor.execute('SELECT name, price, cost FROM menu_items')
    price_map = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

    for days_ago, time_str, table_id, items in sample_data:
        h, m = map(int, time_str.split(':'))
        order_date = (now - timedelta(days=days_ago)).replace(hour=h, minute=m, second=0).strftime('%Y-%m-%d %H:%M:%S')
        
        total_price = 0
        order_items_data = []
        for name, qty in items:
            p, c = price_map.get(name, (70, 25))
            total_price += p * qty
            order_items_data.append((name, p, c, qty))
        
        cursor.execute('''
            INSERT INTO orders (table_id, status, total_price, payment_method, created_at, updated_at)
            VALUES (?, 'paid', ?, 'promptpay', ?, ?)
        ''', (table_id, total_price, order_date, order_date))
        order_id = cursor.lastrowid

        for name, p, c, qty in order_items_data:
            cursor.execute('''
                INSERT INTO order_items (order_id, item_name, price, cost, quantity, note)
                VALUES (?, ?, ?, ?, ?, '')
            ''', (order_id, name, p, c, qty))

# ----------------- ROUTES ----------------- #

@app.route('/')
def home():
    local_ip = get_local_ip()
    port = 5000
    return render_template('home.html', local_ip=local_ip, port=port, restaurant_name=RESTAURANT_NAME)

@app.route('/table/<int:table_id>')
def table_view(table_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, name, category, price, image, description FROM menu_items')
    items = [
        {"id": row[0], "name": row[1], "category": row[2], "price": row[3], "image": row[4], "description": row[5]}
        for row in c.fetchall()
    ]
    conn.close()
    
    categories = sorted(list(set(item["category"] for item in items)))
    return render_template('table.html', table_id=table_id, menu_items=items, categories=categories, restaurant_name=RESTAURANT_NAME)

@app.route('/counter')
def counter_view():
    local_ip = get_local_ip()
    return render_template('counter.html', local_ip=local_ip, restaurant_name=RESTAURANT_NAME)

@app.route('/reports')
def reports_view():
    today = datetime.now().strftime('%Y-%m-%d')
    local_ip = get_local_ip()
    return render_template('reports.html', today=today, local_ip=local_ip, restaurant_name=RESTAURANT_NAME)

# ----------------- ORDER APIS ----------------- #

@app.route('/api/order', methods=['POST'])
def place_order():
    data = request.json
    table_id = data.get('table_id')
    items = data.get('items', [])
    
    if not table_id or not items:
        return jsonify({"success": False, "error": "ข้อมูลไม่ถูกต้อง"}), 400
    
    total_price = sum(item['price'] * item['quantity'] for item in items)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('SELECT name, cost FROM menu_items')
    cost_map = dict(c.fetchall())

    c.execute('''
        INSERT INTO orders (table_id, status, total_price, created_at, updated_at)
        VALUES (?, 'pending', ?, ?, ?)
    ''', (table_id, total_price, now_str, now_str))
    order_id = c.lastrowid
    
    for item in items:
        cost = cost_map.get(item['name'], 0)
        c.execute('''
            INSERT INTO order_items (order_id, item_name, price, cost, quantity, note)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (order_id, item['name'], item['price'], cost, item['quantity'], item.get('note', '')))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "order_id": order_id})

@app.route('/api/table/<int:table_id>/orders', methods=['GET'])
def get_table_orders(table_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''
        SELECT id, status, total_price, created_at
        FROM orders
        WHERE table_id = ? AND status != 'paid'
        ORDER BY id DESC
    ''', (table_id,))
    
    orders = []
    for row in c.fetchall():
        order_id = row[0]
        c2 = conn.cursor()
        c2.execute('''
            SELECT item_name, price, quantity, note
            FROM order_items
            WHERE order_id = ?
        ''', (order_id,))
        items = [{"name": r[0], "price": r[1], "quantity": r[2], "note": r[3]} for r in c2.fetchall()]
        orders.append({
            "order_id": order_id,
            "status": row[1],
            "total_price": row[2],
            "created_at": row[3],
            "items": items
        })
        
    conn.close()
    return jsonify({"orders": orders})

@app.route('/api/counter/orders', methods=['GET'])
def get_counter_orders():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    c.execute('''
        SELECT id, table_id, status, total_price, created_at, updated_at
        FROM orders
        WHERE status != 'paid'
        ORDER BY 
            CASE status
                WHEN 'pending' THEN 1
                WHEN 'accepted' THEN 2
                WHEN 'cooked' THEN 3
                WHEN 'served' THEN 4
                ELSE 5
            END, id ASC
    ''')
    
    active_orders = []
    for row in c.fetchall():
        order_id = row[0]
        c2 = conn.cursor()
        c2.execute('''
            SELECT item_name, price, quantity, note
            FROM order_items
            WHERE order_id = ?
        ''', (order_id,))
        items = [{"name": r[0], "price": r[1], "quantity": r[2], "note": r[3]} for r in c2.fetchall()]
        active_orders.append({
            "order_id": order_id,
            "table_id": row[1],
            "status": row[2],
            "total_price": row[3],
            "created_at": row[4],
            "updated_at": row[5],
            "items": items
        })

    c.execute('''
        SELECT COUNT(*), COALESCE(SUM(total_price), 0)
        FROM orders
        WHERE status = 'paid' AND created_at LIKE ?
    ''', (f"{today_str}%",))
    stat_paid_orders, stat_revenue = c.fetchone()
    
    c.execute('SELECT COUNT(DISTINCT table_id) FROM orders WHERE status != "paid"')
    active_tables = c.fetchone()[0]

    conn.close()
    return jsonify({
        "orders": active_orders,
        "stats": {
            "paid_orders": stat_paid_orders,
            "revenue": stat_revenue,
            "active_tables": active_tables,
            "active_orders": len(active_orders)
        }
    })

@app.route('/api/order/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    data = request.json
    new_status = data.get('status')
    
    valid_statuses = ['pending', 'accepted', 'cooked', 'served', 'paid']
    if new_status not in valid_statuses:
        return jsonify({"success": False, "error": "สถานะไม่ถูกต้อง"}), 400
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        UPDATE orders
        SET status = ?, updated_at = ?
        WHERE id = ?
    ''', (new_status, now_str, order_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "order_id": order_id, "new_status": new_status})

@app.route('/api/table/<int:table_id>/pay_all', methods=['POST'])
def pay_all_for_table(table_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        UPDATE orders
        SET status = 'paid', updated_at = ?
        WHERE table_id = ? AND status != 'paid'
    ''', (now_str, table_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# ----------------- REPORT & FOOD PREP APIS ----------------- #

@app.route('/api/reports/daily', methods=['GET'])
def get_daily_report():
    target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''
        SELECT 
            COUNT(DISTINCT o.id) as order_count,
            COALESCE(SUM(oi.price * oi.quantity), 0) as total_revenue,
            COALESCE(SUM(oi.cost * oi.quantity), 0) as total_cost,
            COALESCE(SUM(oi.quantity), 0) as total_items_sold
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        WHERE o.status = 'paid' AND o.created_at LIKE ?
    ''', (f"{target_date}%",))
    summary_row = c.fetchone()
    
    order_count = summary_row['order_count'] or 0
    total_revenue = summary_row['total_revenue'] or 0
    total_cost = summary_row['total_cost'] or 0
    gross_profit = total_revenue - total_cost
    margin_percent = round((gross_profit / total_revenue * 100), 1) if total_revenue > 0 else 0
    avg_ticket = round(total_revenue / order_count, 1) if order_count > 0 else 0

    c.execute('''
        SELECT 
            oi.item_name,
            m.category,
            SUM(oi.quantity) as total_qty,
            SUM(oi.price * oi.quantity) as item_revenue,
            SUM((oi.price - oi.cost) * oi.quantity) as item_profit
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN menu_items m ON oi.item_name = m.name
        WHERE o.status = 'paid' AND o.created_at LIKE ?
        GROUP BY oi.item_name
        ORDER BY total_qty DESC
    ''', (f"{target_date}%",))
    top_items = [dict(row) for row in c.fetchall()]

    c.execute('''
        SELECT 
            strftime('%H', created_at) as hour,
            COUNT(DISTINCT id) as orders_count,
            SUM(total_price) as hourly_revenue
        FROM orders
        WHERE status = 'paid' AND created_at LIKE ?
        GROUP BY hour
        ORDER BY hour ASC
    ''', (f"{target_date}%",))
    hourly_data = {f"{int(row['hour']):02d}:00": {"orders": row['orders_count'], "revenue": row['hourly_revenue']} for row in c.fetchall()}

    hours_labels = [f"{h:02d}:00" for h in range(10, 23)]
    hourly_revenues = [hourly_data.get(h, {}).get("revenue", 0) for h in hours_labels]
    hourly_orders = [hourly_data.get(h, {}).get("orders", 0) for h in hours_labels]

    c.execute('''
        SELECT 
            r.ingredient_name,
            r.unit,
            SUM(r.quantity_per_portion * oi.quantity) as total_used
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN recipe_ingredients r ON oi.item_name = r.menu_name
        WHERE o.status = 'paid' AND o.created_at LIKE ?
        GROUP BY r.ingredient_name, r.unit
        ORDER BY total_used DESC
    ''', (f"{target_date}%",))
    prep_ingredients = []
    for row in c.fetchall():
        used = row['total_used']
        recommended_prep = round(used * 1.15, 1)
        prep_ingredients.append({
            "ingredient_name": row['ingredient_name'],
            "unit": row['unit'],
            "consumed_today": used,
            "recommended_prep_next_day": recommended_prep
        })

    past_7_days = []
    for i in range(6, -1, -1):
        day = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=i)).strftime('%Y-%m-%d')
        c.execute('''
            SELECT COALESCE(SUM(total_price), 0), COUNT(DISTINCT id)
            FROM orders
            WHERE status = 'paid' AND created_at LIKE ?
        ''', (f"{day}%",))
        day_rev, day_cnt = c.fetchone()
        past_7_days.append({
            "date": day,
            "revenue": day_rev,
            "order_count": day_cnt
        })

    conn.close()

    return jsonify({
        "restaurant_name": RESTAURANT_NAME,
        "date": target_date,
        "summary": {
            "order_count": order_count,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "gross_profit": gross_profit,
            "margin_percent": margin_percent,
            "avg_ticket": avg_ticket
        },
        "top_items": top_items,
        "hourly": {
            "labels": hours_labels,
            "revenues": hourly_revenues,
            "orders": hourly_orders
        },
        "prep_plan": prep_ingredients,
        "trend_7_days": past_7_days
    })

@app.route('/api/reports/export/csv', methods=['GET'])
def export_csv():
    target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT 
            o.id, o.table_id, o.created_at, oi.item_name, oi.price, oi.cost, oi.quantity, (oi.price * oi.quantity) as subtotal
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        WHERE o.status = 'paid' AND o.created_at LIKE ?
        ORDER BY o.id ASC
    ''', (f"{target_date}%",))
    rows = c.fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    si.write('\ufeff')
    cw.writerow(['Order ID', 'Table', 'Time', 'Item Name', 'Price', 'Cost', 'Qty', 'Subtotal'])
    for r in rows:
        cw.writerow(list(r))
        
    output = Response(si.getvalue(), mimetype="text/csv")
    output.headers["Content-Disposition"] = f"attachment; filename=fahsai_tumnua_sales_{target_date}.csv"
    return output

if __name__ == '__main__':
    init_db(force_reset=False)
    ip = get_local_ip()
    print("=" * 60)
    print(">> Restaurant: Fahsai Tum Nua (Fahsai POS) is Ready!")
    print(f">> Home Hub            : http://127.0.0.1:5000/ or http://{ip}:5000/")
    print(f">> Daily Sales Report  : http://127.0.0.1:5000/reports")
    print(f">> Counter / Kitchen   : http://127.0.0.1:5000/counter")
    print(f">> Table 1 Menu        : http://127.0.0.1:5000/table/1")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)
