import os
import re
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pymysql
from flask import Flask, g, jsonify, render_template, request
from flask.json.provider import DefaultJSONProvider


class BankJSON(DefaultJSONProvider):
    @staticmethod
    def default(value):
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        return DefaultJSONProvider.default(value)


app = Flask(__name__)
app.json = BankJSON(app)
app.config["MAX_CONTENT_LENGTH"] = 32_768


def db():
    if "db" not in g:
        g.db = pymysql.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"), port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "ptit_app"), password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME","ptit_chi_nhanh"), charset="utf8mb4", autocommit=True,
            cursorclass=pymysql.cursors.DictCursor, connect_timeout=5,
            init_command="SET time_zone='+07:00'",
        )
    return g.db


@app.teardown_appcontext
def close(_error):
    connection = g.pop("db", None)
    if connection:
        connection.close()


def sql(query, args=()):
    with db().cursor() as cursor:
        cursor.execute(query, args)
        return list(cursor.fetchall()) if cursor.description else []


def field(data, key, length, pattern=None):
    value = data.get(key)
    if not isinstance(value, str) or not 0 < len(value.strip()) <= length:
        raise ValueError("Vui lòng nhập đầy đủ và đúng độ dài các trường.")
    value = value.strip()
    if pattern and not re.fullmatch(pattern, value):
        raise ValueError("Mã hoặc số giấy tờ không đúng định dạng.")
    return value


def calendar_day(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise ValueError("Ngày không hợp lệ.")


def number(data, key, *, rate=False):
    try:
        val = Decimal(str(data.get(key)))
        places = 3 if rate else 0
        if not val.is_finite() or val < 0 or val > (100 if rate else 10**16-1):
            raise ValueError
        if val != val.quantize(Decimal(1).scaleb(-places)):
            raise ValueError
        return val
    except (ValueError, InvalidOperation):
        raise ValueError("Lãi suất phải từ 0 đến 100, tối đa 3 số lẻ." if rate else "Số tiền phải là số nguyên không âm, tối đa 16 chữ số.")


@app.errorhandler(ValueError)
def validation(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(pymysql.MySQLError)
def database_error(error):
    code = error.args[0]
    messages = {1062: "Mã hoặc số giấy tờ đã tồn tại.", 1452: "Không tìm thấy hồ sơ được tham chiếu.",
                3819: "Dữ liệu vi phạm ràng buộc của cơ sở dữ liệu.", 1264: "Giá trị vượt miền lưu trữ.",
                1213: "Giao dịch đang được xử lý đồng thời. Vui lòng gửi lại.",
                1205: "Tài khoản đang bận. Vui lòng gửi lại."}
    if code == 1644:
        return jsonify(error=error.args[1]), 422
    if code in messages:
        return jsonify(error=messages[code]), 409
    app.logger.error("MySQL error %s", code)
    return jsonify(error="Không thể xử lý yêu cầu. Kiểm tra dịch vụ MySQL và cấu hình kết nối."), 503


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/overview")
def overview():
    totals = sql("""SELECT (SELECT COUNT(*) FROM khach_hang) khach,
        (SELECT COUNT(*) FROM tai_khoan) tai_khoan,
        (SELECT COALESCE(SUM(tong_gui),0) FROM v_tien_gui) tong_gui,
        (SELECT COALESCE(SUM(du_no),0) FROM v_du_no) du_no,
        CURRENT_DATE hom_nay""")[0]
    recent = sql("""SELECT g.ma_gd,g.luc,g.loai,k.ho_ten,g.tk_gui,g.tk_td,g.so_tien
        FROM giao_dich g JOIN tai_khoan t ON t.so_tk=COALESCE(g.tk_gui,g.tk_td)
        JOIN khach_hang k ON k.ma_kh=t.ma_kh ORDER BY g.luc DESC,g.ma_gd DESC LIMIT 6""")
    return jsonify(totals=totals, recent=recent)


@app.get("/api/customers")
def customers():
    return jsonify(sql("SELECT * FROM khach_hang ORDER BY ma_kh"))


@app.post("/api/customers")
def add_customer():
    d = request.get_json()
    born = calendar_day(d.get("ngay_sinh"))
    if born >= date.today():
        raise ValueError("Ngày sinh phải trước ngày hiện tại.")
    args = (field(d,"ma_kh",12,r"[A-Za-z0-9_-]+"), field(d,"cmt",12,r"[0-9]{9}|[0-9]{12}"),
            field(d,"ho_ten",100), born, field(d,"dia_chi",200))
    sql("INSERT INTO khach_hang(ma_kh,cmt,ho_ten,ngay_sinh,dia_chi) VALUES(%s,%s,%s,%s,%s)", args)
    return jsonify(message="Đã thêm khách hàng."), 201


@app.patch("/api/customers/<code>/address")
def update_address(code):
    address = field(request.get_json(),"dia_chi",200)
    if not sql("SELECT ma_kh FROM khach_hang WHERE ma_kh=%s",(code,)):
        raise ValueError("Không tìm thấy khách hàng.")
    sql("UPDATE khach_hang SET dia_chi=%s WHERE ma_kh=%s",(address,code))
    return jsonify(message="Đã cập nhật địa chỉ.")


@app.get("/api/employees")
def employees():
    return jsonify(sql("""SELECT *,TIMESTAMPDIFF(YEAR,ngay_vao_lam,CURRENT_DATE) tham_nien
                          FROM nhan_vien ORDER BY ma_nv"""))


@app.get("/api/accounts")
def accounts():
    return jsonify(sql("""SELECT t.*,k.ho_ten, n.ho_ten nguoi_mo FROM tai_khoan t
        JOIN khach_hang k USING(ma_kh) JOIN nhan_vien n ON n.ma_nv=t.nv_mo ORDER BY t.so_tk"""))


@app.post("/api/accounts")
def open_account():
    d = request.get_json()
    kind = d.get("loai")
    if kind not in ("GUI","TD"):
        raise ValueError("Loại tài khoản không hợp lệ.")
    attrs = ((number(d,"tien_gui_dau"),number(d,"du_toi_thieu"),number(d,"lai_thang",rate=True),None)
             if kind=="GUI" else (None,None,None,number(d,"han_muc")))
    args = (field(d,"so_tk",20,r"[A-Za-z0-9_-]+"),field(d,"ma_kh",12),field(d,"nv_mo",12),kind,*attrs)
    sql("CALL sp_mo_tai_khoan(%s,%s,%s,%s,NOW(),%s,%s,%s,%s)",args)
    return jsonify(message="Đã mở tài khoản."), 201


@app.get("/api/accounts/<code>/statement")
def statement(code):
    account = sql("SELECT so_tk,ngay_mo,tien_gui_dau,loai FROM tai_khoan WHERE so_tk=%s",(code,))
    if not account:
        raise ValueError("Không tìm thấy tài khoản.")
    rows = sql("""SELECT ma_gd,luc,loai,tk_gui,tk_td,so_tien,nv_ho_tro FROM giao_dich
                  WHERE tk_gui=%s OR tk_td=%s ORDER BY luc DESC,ma_gd DESC""",(code,code))
    return jsonify(account=account[0],rows=rows)


@app.post("/api/transactions")
def transact():
    d = request.get_json()
    try:
        key = str(uuid.UUID(str(d.get("ma_gd"))))
    except ValueError:
        raise ValueError("Mã giao dịch không hợp lệ. Vui lòng mở lại biểu mẫu.")
    args = (key,field(d,"loai",3),d.get("tk_gui") or None,d.get("tk_td") or None,
            number(d,"so_tien"),d.get("nv_ho_tro") or None)
    sql("CALL sp_giao_dich(%s,%s,%s,%s,%s,%s,NOW())",args)
    return jsonify(message="Đã ghi nhận giao dịch.",ma_gd=key)


@app.get("/api/transactions/<code>")
def receipt(code):
    rows = sql("""SELECT g.ma_gd, g.luc, g.loai, g.so_tien, g.tk_gui, g.tk_td,
                         COALESCE(k_gui.ho_ten,k_td.ho_ten) nguoi_thuc_hien,
                         k_td.ho_ten chu_tin_dung, n.ho_ten nhan_vien
                  FROM giao_dich g
                  LEFT JOIN tai_khoan gui ON gui.so_tk=g.tk_gui
                  LEFT JOIN khach_hang k_gui ON k_gui.ma_kh=gui.ma_kh
                  LEFT JOIN tai_khoan td ON td.so_tk=g.tk_td
                  LEFT JOIN khach_hang k_td ON k_td.ma_kh=td.ma_kh
                  LEFT JOIN nhan_vien n ON n.ma_nv=g.nv_ho_tro
                  WHERE g.ma_gd=%s""", (code,))
    if not rows:
        return jsonify(error="Không tìm thấy biên lai có mã này."), 404
    return jsonify(rows[0])


@app.get("/api/reports/support")
def staff_support():
    first_day = calendar_day(request.args.get("month", "") + "-01")
    return jsonify(sql("""SELECT n.ma_nv, n.ho_ten, COUNT(g.ma_gd) so_luot,
                                 COALESCE(SUM(g.so_tien),0) tong_gia_tri
                          FROM nhan_vien n LEFT JOIN giao_dich g
                            ON g.nv_ho_tro=n.ma_nv AND g.luc >= %s
                            AND g.luc < DATE_ADD(%s, INTERVAL 1 MONTH)
                          GROUP BY n.ma_nv,n.ho_ten ORDER BY so_luot DESC,n.ma_nv""",
                       (first_day, first_day)))


@app.get("/api/reports/reconciliation")
def reconcile_balances():
    return jsonify(sql("""WITH but_toan AS (
                            SELECT tk_gui so_tk, IF(loai='NAP',so_tien,-so_tien) bien_dong
                            FROM giao_dich WHERE tk_gui IS NOT NULL
                            UNION ALL
                            SELECT tk_td so_tk, IF(loai='CHI',-so_tien,so_tien) bien_dong
                            FROM giao_dich WHERE tk_td IS NOT NULL
                          ), doi_chieu AS (
                            SELECT t.so_tk, t.loai, t.so_du,
                                   COALESCE(t.tien_gui_dau,t.han_muc) + COALESCE(SUM(b.bien_dong),0) theo_nhat_ky
                            FROM tai_khoan t LEFT JOIN but_toan b ON b.so_tk=t.so_tk
                            GROUP BY t.so_tk
                          )
                          SELECT *, so_du-theo_nhat_ky chenh_lech,
                                 IF(so_du=theo_nhat_ky,'Khớp','Cần kiểm tra') ket_qua
                          FROM doi_chieu ORDER BY ABS(so_du-theo_nhat_ky) DESC,so_tk"""))


@app.get("/api/reports/<name>")
def reports(name):
    if name == "salary":
        month = request.args.get("month","")
        return jsonify(sql("CALL sp_luong(%s)",(calendar_day(month+"-01"),)))
    if name == "activity":
        return jsonify(sql("CALL sp_tin_dung_trong_ky(%s,%s)",(
            calendar_day(request.args.get("from")),calendar_day(request.args.get("to")))))
    if name == "debt":
        return jsonify(sql("SELECT * FROM v_du_no ORDER BY du_no DESC,so_tk"))
    if name == "top":
        return jsonify(sql("SELECT * FROM v_tien_gui ORDER BY tong_gui DESC,ma_kh LIMIT 10"))
    return jsonify(error="Không tìm thấy báo cáo."),404


if __name__ == "__main__":
    app.run(host=os.getenv("APP_HOST","127.0.0.1"),port=int(os.getenv("APP_PORT","8080")))
