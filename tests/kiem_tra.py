import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if os.getenv("DB_NAME") != "ptit_btl_test":
    raise SystemExit("Hãy dùng một bản sao riêng tên ptit_btl_test theo hướng dẫn README.")
from app import app

app.testing = True
def call(path, body=None):
    with app.test_client() as client:
        response = client.get("/api/"+path) if body is None else client.post("/api/"+path,json=body)
        return response.status_code, response.get_json()
def ok(path, body=None):
    status,data=call(path,body)
    assert status < 300,(path,status,data)
    return data
def fails(path,body,message):
    status,data=call(path,body)
    assert status in (400,409,422) and message in data["error"],(path,status,data)
def log(label):
    print("OK |",label)
def transaction(kind,amount,source=None,target=None,staff=None):
    return dict(ma_gd=str(uuid.uuid4()),loai=kind,so_tien=amount,tk_gui=source,tk_td=target,nv_ho_tro=staff)

def run():
    accounts=ok("accounts")
    sample_month=next(r["ngay_mo"][:7] for r in accounts if r["so_tk"]=="T204")
    salary=ok("reports/salary?month="+sample_month)
    assert {r["ma_nv"]:float(r["luong"]) for r in salary}=={"NV01":560000,"NV02":500000,"NV05":0}
    log("Lương 500.000 đồng/TK tín dụng, 2% tiền gửi đầu, có cả nhân viên lương 0")
    day=sample_month+"-01"
    activity=ok("reports/activity?from="+day+"&to="+day)
    assert any(r["ho_ten"]=="Nguyễn An" and r["chu_tk"]=="Trần Bình" and r["so_tk"]=="T202" and int(r["thanh_toan"])==1500000 for r in activity)
    log("Khoảng một ngày tính đủ hai đầu và ghi đúng người thanh toán hộ")
    debt=ok("reports/debt")
    assert [r["so_tk"] for r in debt]==["T203","T202","T201","T204","T205"]
    assert [int(r["du_no"]) for r in debt]==[8000000,4500000,3500000,1200000,0]
    top=ok("reports/top")
    assert len(top)==10 and top[0]["ma_kh"]=="KH03" and int(next(r["tong_gui"] for r in top if r["ma_kh"]=="KH01"))==20500000
    log("Xếp dư nợ giảm dần và top 10 cộng đủ nhiều tài khoản gửi")
    assert call("reports/activity?from=2026-02-02&to=2026-02-01")[0]==422
    receipt=ok("transactions/DEMO-06")
    assert (receipt["nguoi_thuc_hien"],receipt["chu_tin_dung"],receipt["nhan_vien"])==("Nguyễn An","Trần Bình","Đỗ Thu Hà")
    assert int(receipt["so_tien"])==1500000 and call("transactions/khong-ton-tai")[0]==404
    assert ok("transactions/DEMO-02")["nhan_vien"] is None
    support=ok("reports/support?month="+sample_month)
    assert {r["ma_nv"]:(r["so_luot"],int(r["tong_gia_tri"])) for r in support}=={
        "NV01":(0,0),"NV02":(0,0),"NV03":(2,2200000),"NV04":(1,1500000),"NV05":(0,0)},support
    assert call("reports/support?month=2026-13")[0]==400
    audit=ok("reports/reconciliation")
    assert len(audit)==len(accounts) and all(int(r["chenh_lech"])==0 for r in audit)
    log("Tra biên lai trả hộ, đếm giao dịch có hỗ trợ theo tháng và đối soát số dư ban đầu")
    prefix="Z"+uuid.uuid4().hex[:7]
    customer=prefix
    ok("customers",dict(ma_kh=customer,cmt=str(uuid.uuid4().int%10**12).zfill(12),ho_ten="Khách kiểm thử",ngay_sinh="1990-01-01",dia_chi="Hà Nội"))
    def new_account(suffix,kind,staff="NV01"):
        d=dict(so_tk=prefix+suffix,ma_kh=customer,nv_mo=staff,loai=kind)
        return {**d,**(dict(tien_gui_dau=2000,du_toi_thieu=500,lai_thang="0.5") if kind=="GUI" else dict(han_muc=2000))}
    fails("accounts",new_account("X","TD","NV03"),"kinh doanh")
    ok("accounts",new_account("D","TD"))
    ok("accounts",new_account("E","TD"))
    fails("accounts",new_account("F","TD"),"giới hạn")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda suffix:call("accounts",new_account(suffix,"GUI"))[0],"ABCG"))
    assert results.count(201)==3 and results.count(422)==1,results
    log("Chỉ kinh doanh được mở TK, giới hạn 2 tín dụng và 3 gửi tiền kể cả mở đồng thời")
    source=next(r["so_tk"] for r in ok("accounts") if r["ma_kh"]==customer and r["loai"]=="GUI")
    target=prefix+"D"
    def balances():
        return {r["so_tk"]:int(r["so_du"]) for r in ok("accounts") if r["so_tk"] in (source,target)}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:call("transactions",transaction("CHI",1500,target=target,staff="NV04"))[0],range(2)))
    assert sorted(results)==[200,422] and balances()[target]==500
    log("Hai chi tiêu đồng thời, chỉ một giao dịch đủ hạn mức được ghi")
    before=balances()
    fails("transactions",transaction("TRA",1501,source,target),"tối thiểu")
    assert balances()==before
    req=transaction("TRA",1500,source,target,"NV03")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:call("transactions",req)[0],range(2)))
    assert sorted(results)==[200,200] and balances()=={source:500,target:2000}
    stmt=ok("accounts/"+target+"/statement")
    assert len([r for r in stmt["rows"] if r["ma_gd"]==req["ma_gd"]])==1
    fails("transactions",{**req,"so_tien":1},"Mã yêu cầu")
    log("Thanh toán đúng mức sàn, ghi nợ một lần khi gửi lại và giữ nguyên số dư khi thất bại")
    ok("transactions",transaction("NAP",200,source=source))
    fails("transactions",transaction("TRA",100,source,target),"vượt dư nợ")
    fails("transactions",transaction("CHI","1.5",target=target),"số nguyên")
    fails("transactions",transaction("CHI",0,target=target),"không hợp lệ")
    ok("transactions",transaction("CHI",2000,target=target))
    assert balances()[target]==0
    audit={r["so_tk"]:r for r in ok("reports/reconciliation")}
    for account, balance in balances().items():
        assert int(audit[account]["theo_nhat_ky"])==balance and audit[account]["ket_qua"]=="Khớp"
    log("Từ chối trả thừa, tiền lẻ hoặc bằng 0; chấp nhận chi đúng hạn mức")
    print("Đã hoàn tất kiểm tra nghiệp vụ.")
if __name__=="__main__":
    run()
