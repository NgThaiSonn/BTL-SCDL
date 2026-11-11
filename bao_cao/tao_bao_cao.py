"""Tạo báo cáo PDF và sơ đồ EER dạng vector. Dùng ReportLab và phông tiếng Việt."""
import argparse
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

parser = argparse.ArgumentParser()
parser.add_argument("--nhom", default="")
parser.add_argument("--thanh-vien", default="", help="Họ tên và mã SV, ngăn cách bằng dấu phẩy")
args = parser.parse_args()
directory = Path(__file__).resolve().parent
for regular, bold in [("C:/Windows/Fonts/arial.ttf","C:/Windows/Fonts/arialbd.ttf"),
                     ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")]:
    if Path(regular).exists():
        break
pdfmetrics.registerFont(TTFont("Body",regular))
pdfmetrics.registerFont(TTFont("Bold",bold))
pdfmetrics.registerFontFamily("Body",normal="Body",bold="Bold")
W,H=A4
c=canvas.Canvas(str(directory/"Bao-cao-chi-nhanh-ngan-hang.pdf"),pagesize=A4)
c.setTitle("Quản lý chi nhánh ngân hàng | Bài tập lớn Cơ sở dữ liệu")
ink="#172e2e"; sub="#41595a"; green="#126651"; tint="#eaf3ee"; line="#ceded5"; blue="#eaf1fa"
def color(s): return colors.HexColor(s)
def rect(x,y,w,h,fill,stroke=None,r=0):
    c.setFillColor(color(fill));c.setStrokeColor(color(stroke or fill))
    c.roundRect(x,H-y-h,w,h,r,fill=1,stroke=int(bool(stroke)))
def text(x,y,s,size=11,font="Body",fg=ink):
    c.setFont(font,size);c.setFillColor(color(fg));c.drawString(x,H-y,s)
def center(x,y,s,size=10,font="Body",fg=ink):
    c.setFont(font,size);c.setFillColor(color(fg));c.drawCentredString(x,H-y,s)
def para(x,y,w,s,size=11,leading=16,fg=ink,font="Body"):
    style=ParagraphStyle("p",fontName=font,fontSize=size,leading=leading,textColor=color(fg),alignment=TA_LEFT)
    obj=Paragraph(s,style);_,h=obj.wrap(w,750);obj.drawOn(c,x,H-y-h);return y+h
def wire(points,fg=green,weight=1.3):
    c.setStrokeColor(color(fg));c.setLineWidth(weight);p=c.beginPath();p.moveTo(points[0][0],H-points[0][1])
    for x,y in points[1:]:p.lineTo(x,H-y)
    c.drawPath(p)
def frame(n,title):
    text(42,40,"PTIT  /  CƠ SỞ DỮ LIỆU",9,"Bold",green)
    c.setFont("Body",9);c.setFillColor(color(sub));c.drawRightString(W-42,H-40,"Chủ đề 3   /   Chi nhánh ngân hàng")
    wire([(42,779),(W-42,779)],line,.8);text(42,802,title,9,"Body",sub)
    c.setFont("Bold",9);c.drawRightString(W-42,H-802,f"{n:02d} / 06")
def title(s,h=94):text(42,h,s,25,"Bold")
def sect(y,s):text(42,y,s,14,"Bold",green);return y+11
def grid(y,headers,rows,widths,size=10):
    x0=42
    def get_pars(vals,bold=False):
        return [Paragraph(v,ParagraphStyle("cell",fontName="Bold" if bold else "Body",fontSize=size,
                    leading=size+4,textColor=color("#ffffff" if bold else ink))) for v in vals]
    for i,vals in enumerate([headers]+rows):
        ps=get_pars(vals,i==0);hs=[p.wrap(w-16,750)[1] for p,w in zip(ps,widths)]
        height=max(hs)+14;rect(x0,y,sum(widths),height,green if i==0 else (tint if i%2 else "#ffffff"))
        x=x0
        for p,w,h in zip(ps,widths,hs):
            p.drawOn(c,x+8,H-y-7-h);x+=w
        wire([(x0,y+height),(x0+sum(widths),y+height)],line,.45);y+=height
    return y
def note(y,heading,body):
    temp=Paragraph(body,ParagraphStyle("note",fontName="Body",fontSize=10.5,leading=15))
    h=temp.wrap(W-112,600)[1]+43;rect(42,y,W-84,h,tint,r=8)
    text(55,y+19,heading,11,"Bold",green);para(55,y+27,W-111,body,10.5,15);return y+h
def end():c.showPage()

frame(1,"Phạm vi và quy ước")
text(42,100,"BÀI TẬP LỚN MÔN CƠ SỞ DỮ LIỆU",11,"Bold",green)
text(42,149,"Quản lý chi nhánh",36,"Bold")
text(42,194,"ngân hàng",36,"Bold")
y=para(43,216,495,"Học viện Công nghệ Bưu chính Viễn thông",13,19,sub)
if args.nhom or args.thanh_vien:
    y=para(43,y+7,495,escape(" · ".join(v for v in (args.nhom,args.thanh_vien) if v)),10.5,14)
y=sect(y+50,"Phạm vi nghiệp vụ")
y=para(42,y,510,"Một chi nhánh quản lý hồ sơ khách hàng, nhân viên và hai loại tài khoản. Khi thanh toán dư nợ, hệ thống xác định tài khoản gửi tiền của người trả và tài khoản tín dụng của người nhận. Hai tài khoản có thể thuộc hai khách hàng khác nhau.")
y=sect(y+39,"Quy ước tính toán")
y=grid(y,["Đại lượng","Cách hiểu trong hệ thống"],[
    ["Số dư tài khoản gửi","Số tiền đang có. Sau khi trả nợ, số dư phải lớn hơn hoặc bằng mức tối thiểu của chính tài khoản đó."],
    ["Số dư tài khoản tín dụng","Phần hạn mức còn khả dụng. Dư nợ hiện tại bằng hạn mức trừ số dư khả dụng."],
    ["Lương tháng","Khoản lương theo nghiệp vụ mở tài khoản. Đề bài cho hai mức hưởng và không cung cấp lương cơ bản."],
    ["Thời gian và tiền tệ","Ghi thời gian theo UTC+7. Giao dịch dùng đồng Việt Nam nguyên. Lương tính theo tỷ lệ 2% có thể có phần lẻ."]],[153,358])
if y>745:raise RuntimeError("Phần tên nhóm quá dài cho trang bìa.")
end()

frame(2,"Mô hình thực thể liên kết mở rộng")
title("Mô hình EER")
para(42,111,510,"Lớp tài khoản chuyên biệt hóa toàn phần và rời nhau. Mỗi tài khoản thuộc đúng một lớp con. Các cặp (min, max) trên đường nối thể hiện số lần tham gia quan hệ.",10.5,15,sub)
def node(x,y,w,name,lines):
    h=32+len(lines)*14;rect(x,y,w,h,"#ffffff",line,8);rect(x+1,y+1,w-2,23,tint,r=6)
    center(x+w/2,y+16,name,10,"Bold",green)
    for i,s in enumerate(lines):text(x+9,y+37+i*14,s,8.8)
    return h
def label(x,y,s):center(x,y,s,8.1,"Bold",sub)
node(42,164,200,"KHÁCH HÀNG",["PK  ma_kh","cmt, ho_ten, ngay_sinh, dia_chi"])
node(337,164,200,"NHÂN VIÊN",["PK  ma_nv","cmt, ho_ten, ngay_sinh, dia_chi","bac_nghe, ngay_vao_lam, vi_tri"])
node(184,304,216,"TÀI KHOẢN",["PK  so_tk","ngay_mo, loai, so_du"])
wire([(138,224),(138,276),(226,276),(226,304)])
wire([(436,238),(436,276),(355,276),(355,304)])
label(86,253,"(0,N)");label(179,269,"sở hữu");label(206,298,"(1,1)")
label(476,253,"(0,N)");label(394,269,"mở tài khoản");label(375,298,"(1,1)")
wire([(290,364),(290,392)]);wire([(295,364),(295,392)])
c.setFillColor(color("#ffffff"));c.setStrokeColor(color(green));c.circle(292.5,H-405,13,fill=1,stroke=1);center(292.5,409,"d",12,"Bold",green)
wire([(280,409),(145,409),(145,447)]);wire([(305,409),(432,409),(432,447)])
node(42,447,207,"TÀI KHOẢN GỬI",["PK kế thừa  so_tk","tien_gui_dau, du_toi_thieu, lai_thang"])
node(329,447,208,"TÀI KHOẢN TÍN DỤNG",["PK kế thừa  so_tk","han_muc"])
wire([(145,507),(145,553),(223,553),(223,590)]);wire([(431,507),(431,553),(356,553),(356,590)])
label(111,533,"(0,N)");label(177,546,"nộp / trích");label(205,578,"(0,1)")
label(464,533,"(0,N)");label(393,546,"chi / trả nợ");label(379,578,"(0,1)")
node(184,590,216,"GIAO DỊCH",["PK  ma_gd","luc, loai, so_tien"])
wire([(537,201),(554,201),(554,622),(400,622)],sub,1)
label(495,613,"hỗ trợ");label(535,195,"");label(442,635,"(0,1)");label(541,250,"(0,N)")
note(675,"Cách đọc","Mỗi khách hàng sở hữu 0–2 tài khoản tín dụng và 0–3 tài khoản gửi. Chỉ nhân viên kinh doanh mở tài khoản. Bất kỳ nhân viên nào cũng có thể hỗ trợ giao dịch. Quy tắc chọn tài khoản theo từng loại giao dịch được nêu ở trang 4.")
end()

frame(3,"Chuyển từ EER sang mô hình quan hệ");title("Lược đồ và thuộc tính")
para(42,111,510,"Mô hình EER được chuyển thành bốn bảng MySQL. Hai lớp con của tài khoản dùng chung khóa chính của bảng tai_khoan. PK là khóa chính, FK là khóa ngoại.",10.5,15,sub)
y=sect(189,"Khách hàng và nhân viên")
y=grid(y,["Bảng","Khóa và thuộc tính"],[
 ["khach_hang","<b>ma_kh</b> (PK), <b>cmt</b> (duy nhất), ho_ten, ngay_sinh, dia_chi. Mỗi dòng đại diện một khách hàng."],
 ["nhan_vien","<b>ma_nv</b> (PK), <b>cmt</b> (duy nhất), ho_ten, ngay_sinh, dia_chi, bac_nghe, ngay_vao_lam, vi_tri. Thâm niên tính bằng số năm tròn từ ngày vào làm đến ngày tra cứu."]],[128,383])
y=sect(y+35,"Tài khoản và hai lớp con")
y=grid(y,["Nhóm cột","Biểu diễn trong bảng tai_khoan"],[
 ["Dùng chung","<b>so_tk</b> (PK), ma_kh (FK), nv_mo (FK), ngay_mo, loai, suat, so_du. Mỗi tài khoản có một chủ và một nhân viên mở."],
 ["Gửi tiền · GUI","tien_gui_dau lưu riêng khoản gửi đầu để tính lương. du_toi_thieu là mức sàn. lai_thang là tỷ lệ %/tháng. han_muc nhận NULL."],
 ["Tín dụng · TD","han_muc là trần tín dụng. Khi mở, so_du = han_muc và dư nợ bằng 0. Các cột dành riêng cho tiền gửi nhận NULL."],
 ["Ràng buộc số lượng","Khóa duy nhất (ma_kh, loai, suat) kết hợp CHECK. Với TD chỉ có suất 1–2, với GUI chỉ có suất 1–3. Hai yêu cầu mở cùng lúc cũng không thể nhận cùng suất."]],[128,383])
note(y+24,"Kiểu dữ liệu","Tiền giao dịch dùng DECIMAL(16,0), lãi tháng dùng DECIMAL(6,3). CMT và số tài khoản lưu dưới dạng chuỗi để giữ số 0 ở đầu. Ngày sinh kiểu DATE, thời điểm mở và giao dịch kiểu DATETIME.")
end()

frame(4,"Nhật ký giao dịch và tính nhất quán");title("Ghi nhận giao dịch")
y=para(42,111,509,"Bảng giao_dich dùng ma_gd làm PK, lưu luc, loai, so_tien và ba FK tùy nghiệp vụ: tk_gui, tk_td, nv_ho_tro. Nhân viên hỗ trợ có thể để trống với giao dịch tự thực hiện.",11,16)
y=sect(y+35,"Tác động của từng nghiệp vụ")
y=grid(y,["Loại","Tài khoản tham gia","Tác động lên số dư"],[
 ["NAP","Một TK gửi","Cộng số tiền nộp vào số dư tiền gửi."],
 ["CHI","Một TK tín dụng","Trừ số tiền chi vào phần tín dụng khả dụng. Số tiền phải nhỏ hơn hoặc bằng hạn mức còn lại."],
 ["TRA","Một TK gửi và một TK tín dụng","Trừ ở TK gửi và cộng lại phần khả dụng ở TK tín dụng. Chấp nhận trả hộ. Số tiền không vượt dư nợ và số dư gửi sau trích phải đạt mức sàn."]],[58,149,304])
y=sect(y+34,"Trình tự thanh toán")
for n,h,b in [
 ("1","Khóa các dòng liên quan","Thủ tục sp_giao_dich mở giao dịch InnoDB, khóa dòng tiền gửi trước rồi dòng tín dụng bằng SELECT … FOR UPDATE."),
 ("2","Đối chiếu yêu cầu và số dư","Một mã yêu cầu gửi lại với cùng nội dung trả về thành công cho lần đã ghi. Nếu dùng lại mã cho nội dung khác, hệ thống từ chối."),
 ("3","Ghi nhật ký và chốt số dư","Sau khi kiểm tra số tiền, thời điểm và hai tài khoản, thủ tục ghi một dòng nhật ký, cập nhật số dư rồi COMMIT. Bất kỳ lỗi SQL nào cũng dẫn đến ROLLBACK.")]:
    text(42,y+11,n,11,"Bold",green);text(64,y+11,h,11,"Bold")
    y=para(64,y+18,482,b,10.5,15)+15
note(y+3,"Quyền ghi của ứng dụng","Tài khoản MySQL dành cho giao diện có quyền đọc và gọi thủ tục, thêm khách hàng và sửa địa chỉ. Thay đổi số dư đi qua thủ tục giao dịch.")
end()

frame(5,"Truy vấn và kết quả đối chiếu");title("Năm yêu cầu của đề")
y=para(42,111,510,"Dữ liệu mẫu trải trên tháng cài đặt và tháng liền trước. Các kết quả dưới đây tính ngay sau khi nhập dữ liệu mẫu, trước khi người dùng ghi giao dịch mới.",10.5,15,sub)
y=sect(y+32,"Báo cáo và nghiệp vụ")
y=grid(y,["Yêu cầu","Thực hiện và cách đọc kết quả"],[
 ["1 · Lương kinh doanh","sp_luong(ngày trong tháng). Với mỗi nhân viên kinh doanh, cộng 500.000 ₫ cho mỗi TK tín dụng mở mới và 2% tiền gửi ban đầu của từng TK gửi mở trong tháng. LEFT JOIN giữ cả nhân viên có kết quả bằng 0."],
 ["2 · Giao dịch trong kỳ","sp_tin_dung_trong_ky(từ, đến). Gom theo người thực hiện và tài khoản tín dụng. Tách tổng chi và tổng trả. Tổng giá trị giao dịch bằng tổng hai cột. Bộ lọc lấy từ đầu ngày bắt đầu đến trước ngày kế tiếp ngày kết thúc."],
 ["3 · Dư nợ hiện tại","Đọc v_du_no, sắp theo du_no giảm dần rồi so_tk tăng dần. Bao gồm cả tài khoản có dư nợ bằng 0."],
 ["4 · Top 10 tiền gửi","Đọc v_tien_gui. Cộng số dư hiện tại trên toàn bộ tài khoản gửi của một khách hàng, sắp giảm dần, phá hòa theo ma_kh và lấy tối đa 10 người."],
 ["5 · Thanh toán tín dụng","Gọi sp_giao_dich với loại TRA và hai số tài khoản. Chủ TK gửi là người thực hiện. Chủ TK tín dụng có thể là người khác."]],[135,376])
y=sect(y+31,"Kết quả trên dữ liệu mẫu")
y=grid(y,["Tình huống","Giá trị đối chiếu"],[
 ["Lương tháng cài đặt","NV01 mở một TK tín dụng và một TK gửi 3.000.000 ₫. Lương nghiệp vụ 560.000 ₫. NV02 được 500.000 ₫ và NV05 được 0 ₫."],
 ["Dư nợ và tiền gửi","T203 có dư nợ cao nhất, 8.000.000 ₫. KH03 đứng đầu về tiền gửi với 32.000.000 ₫. KH01 có hai TK gửi, tổng số dư là 20.500.000 ₫."],
 ["Thanh toán hộ","Giao dịch DEMO-06 trích 1.500.000 ₫ từ G101 của Nguyễn An để giảm dư nợ T202 của Trần Bình từ 6.000.000 ₫ xuống 4.500.000 ₫."]],[135,376])
end()

frame(6,"Sử dụng ứng dụng và kiểm tra");title("Trình diễn và kiểm tra")
y=para(42,111,510,"Ứng dụng web dùng Flask và MySQL. Trên giao diện, người sử dụng chọn khách hàng, tài khoản và kỳ báo cáo bằng biểu mẫu. Hướng dẫn cài đặt và chạy lại nằm trong README.md.")
y=sect(y+33,"Kịch bản trình diễn")
y=grid(y,["Thao tác trên giao diện","Kết quả mong đợi với dữ liệu mới cài"],[
 ["Báo cáo → Lương kinh doanh","Chọn tháng hiện tại. Đối chiếu NV01, NV02, NV05 với bảng trang 5. Có thể xuất CSV."],
 ["Giao dịch → Thanh toán dư nợ","Chọn G101 và T202, nhập 500.000 ₫. G101 giảm từ 17.500.000 ₫ xuống 17.000.000 ₫. Dư nợ T202 giảm từ 4.500.000 ₫ xuống 4.000.000 ₫."],
 ["Tài khoản → Sao kê","Mở sao kê G101 hoặc T202 để thấy cùng mã giao dịch thanh toán. Vào Báo cáo → Giao dịch tín dụng để xem tên người thực hiện và chủ tài khoản."],
 ["Tài khoản → Mở tài khoản","Chọn KH01 và thử mở thêm TK tín dụng. KH01 đã sở hữu T201 và T205 nên hệ thống từ chối."]],[153,358])
y=sect(y+32,"Các chức năng bổ sung")
y=para(42,y,509,"Tạo khách hàng, tìm theo tên hoặc mã, sửa địa chỉ, mở tài khoản, nộp tiền gửi, ghi chi tiêu tín dụng, tra cứu tài khoản, xem sao kê, tra cứu nhân viên và xuất báo cáo CSV. Tổng quan hiển thị số dư tổng hợp và các giao dịch gần đây.",10.5,15)
y=sect(y+31,"Nguồn và tài liệu kỹ thuật")
y=para(42,y,510,"Đề bài tập lớn môn Cơ sở dữ liệu, Project 3, bản do người học cung cấp. Các hồ sơ minh họa được tạo cho bài tập.",10,14)
y=para(42,y+7,510,'Vũ Thị Thúy Hà và Trần Hà Nguyên (2022), <link href="https://dlib.ptit.edu.vn/handle/HVCNBCVT/3387" color="#126651">Bài giảng Cơ sở dữ liệu</link>, Học viện Công nghệ Bưu chính Viễn thông. Chương 2 và 4 về mô hình và thiết kế quan hệ.',10,14)
para(42,y+7,510,'Oracle, <link href="https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html" color="#126651">MySQL 8.4 Reference Manual, Locking Reads</link> và <link href="https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html" color="#126651">CHECK Constraints</link>.',10,14)
end()
c.save()
