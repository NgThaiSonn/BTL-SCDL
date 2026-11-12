# Quản lý chi nhánh ngân hàng

Bài tập lớn môn Cơ sở dữ liệu, chủ đề 3, Học viện Công nghệ Bưu chính Viễn thông. Ứng dụng web tiếng Việt dùng Flask, PyMySQL và MySQL 8.4. Bộ dữ liệu mẫu gồm 12 khách hàng, 5 nhân viên, 18 tài khoản và 7 giao dịch thuộc hai tháng liên tiếp.

## Chạy bằng Docker Desktop

Khởi động Docker Desktop. Mở terminal trong thư mục chứa `compose.yaml` rồi chạy lệnh dưới đây. Lần chạy đầu cần kết nối mạng để tải MySQL và thư viện Python.

```sh
docker compose up --build -d
```

Mở [ứng dụng tại localhost:8080](http://localhost:8080). MySQL tự nhập bộ mẫu khi tạo volume lần đầu. Giao diện kết nối bằng tài khoản ứng dụng có quyền thực thi các thủ tục. Có thể đặt `DB_PASSWORD` trước lần khởi tạo để chọn mật khẩu demo. Cổng web chỉ lắng nghe trên máy đang chạy.

```sh
docker compose ps
docker compose logs db
docker compose down
```

Lệnh cuối dừng ứng dụng và giữ dữ liệu trong volume `bank_data`. Lần sau chạy `docker compose up -d`.

## Chạy với MySQL đã cài trên máy

1. Mở MySQL Workbench, kết nối bằng tài khoản có quyền tạo bảng, trigger, view và thủ tục. Mở `docker/init.sql`, chạy **toàn bộ tệp** một lần trên môi trường mới. Tên CSDL được tạo là `ptit_chi_nhanh`. Nếu chỉ muốn xem lại báo cáo, chạy các lệnh ở mục «Chạy truy vấn» bên dưới.
2. Tạo tài khoản cho app bằng các lệnh dưới đây, thay mật khẩu mẫu bằng mật khẩu của bạn. Ví dụ sau áp dụng khi cả app và MySQL chạy trên cùng máy.

```sql
CREATE USER 'ptit_app'@'localhost' IDENTIFIED BY 'MAT_KHAU_BAN_CHON';
GRANT SELECT, EXECUTE ON ptit_chi_nhanh.* TO 'ptit_app'@'localhost';
GRANT INSERT, UPDATE (dia_chi) ON ptit_chi_nhanh.khach_hang TO 'ptit_app'@'localhost';
```

3. Với Python 3.10 trở lên, chạy trong PowerShell. Dùng đúng mật khẩu đã đặt ở bước 2.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DB_PASSWORD = 'MAT_KHAU_BAN_CHON'
.\.venv\Scripts\python.exe app.py
```

Mở [localhost:8080](http://localhost:8080). Nếu MySQL dùng địa chỉ hoặc cổng khác, đặt thêm `DB_HOST`, `DB_PORT` trước khi chạy. Trên macOS hoặc Linux có thể dùng `.venv/bin/python` và `export DB_PASSWORD=...`.

## Chạy truy vấn

Tháng cài đặt được chọn làm tháng mẫu hiện hành. Trường lương của đề chỉ tính thu nhập theo mở tài khoản. Có thể thay mốc ngày trong hai câu `CALL` đầu.

```sql
USE ptit_chi_nhanh;
SET time_zone = '+07:00';
SET @dau_thang = CAST(DATE_FORMAT(CURRENT_DATE, '%Y-%m-01') AS DATE);
CALL sp_luong(@dau_thang);
CALL sp_tin_dung_trong_ky(@dau_thang, CURRENT_DATE);
SELECT * FROM v_du_no ORDER BY du_no DESC, so_tk;
SELECT * FROM v_tien_gui ORDER BY tong_gui DESC, ma_kh LIMIT 10;
```

**Thanh toán dư nợ.** Ví dụ sau thực hiện một giao dịch mới 500.000 đồng. G101 là tài khoản gửi của Nguyễn An, T202 là tài khoản tín dụng của Trần Bình. Giữ nguyên `@ma` khi cần gửi lại cùng yêu cầu để hệ thống không trích tiền hai lần.

```sql
SET @ma = UUID();
CALL sp_giao_dich(@ma, 'TRA', 'G101', 'T202', 500000, 'NV03', NOW());
```

## Đối chiếu khi trình diễn

| Chức năng | Thao tác | Kết quả trên dữ liệu mới cài |
|---|---|---|
| Lương kinh doanh | Báo cáo → Lương kinh doanh → tháng cài đặt | NV01 nhận 560.000 đồng, NV02 nhận 500.000 đồng, NV05 nhận 0 đồng. |
| Giao dịch tín dụng | Báo cáo → Giao dịch tín dụng → ngày đầu tháng cài đặt | Có dòng Nguyễn An thanh toán hộ chủ T202 là Trần Bình, số tiền 1.500.000 đồng. |
| Xếp dư nợ | Báo cáo → Dư nợ | T203 đứng đầu với 8.000.000 đồng. T205 có dư nợ bằng 0. |
| Top 10 tiền gửi | Báo cáo → Top 10 tiền gửi | KH03 đứng đầu với 32.000.000 đồng. KH01 có tổng 20.500.000 đồng trên hai tài khoản. |
| Trả nợ hộ | Giao dịch → Thanh toán dư nợ → G101, T202, 500.000 đồng | G101 còn 17.000.000 đồng, T202 còn nợ 4.000.000 đồng. Hai tài khoản có cùng một mã giao dịch trên sao kê. |

**Mười chức năng bổ sung** gồm thêm khách hàng, tìm khách hàng, sửa địa chỉ, mở tài khoản, nộp tiền gửi, ghi chi tiêu tín dụng, tra cứu tài khoản, xem sao kê, tra cứu nhân viên và xuất báo cáo CSV.

## Thiết kế và ràng buộc

- Một chi nhánh, mỗi tài khoản thuộc một khách hàng. Hai loại tài khoản là hai lớp con toàn phần, rời nhau trên EER. MySQL ánh xạ cả hai vào `tai_khoan` và kiểm tra thuộc tính riêng bằng `CHECK`.
- Mỗi khách hàng có tối đa 2 TK tín dụng và 3 TK gửi. Khóa duy nhất theo khách hàng, loại và suất mở tài khoản bảo vệ giới hạn kể cả khi có yêu cầu đồng thời. Trigger kiểm tra người mở có vị trí kinh doanh.
- Với TK tín dụng, `so_du` là phần tín dụng còn khả dụng. `han_muc - so_du` là dư nợ. Các giao dịch tiền tệ đi qua `sp_giao_dich`, dùng khóa dòng, kiểm tra mức sàn và ghi nhật ký cùng hai biến động số dư trong một giao dịch InnoDB.
- Khoản nộp đầu là một thuộc tính khi mở tài khoản gửi. Các lần nộp thêm không làm tăng hoa hồng. Ứng dụng lưu lãi suất theo tháng trên hồ sơ tài khoản. Đề không quy định nghiệp vụ kết chuyển lãi.
- Trong báo cáo tín dụng, chi tiêu được gán cho chủ TK tín dụng, còn trả nợ được gán cho chủ TK gửi đã trích tiền. Cột chủ TK tín dụng cho biết ai nhận khoản thanh toán. Khoảng lọc bao gồm trọn ngày đầu và ngày cuối.
- Tiền giao dịch là số nguyên dương. Quy ước của nhóm là từ chối trả quá dư nợ. Có thể thanh toán đến đúng số dư tối thiểu và chi tiêu đến đúng hạn mức.

## Kiểm tra tự động

`tests/kiem_tra.py` gọi các API thực tế trên MySQL. Để chạy lại, tạo một **bản thử nghiệm mới** bằng cách sao chép `docker/init.sql`, thay toàn bộ tên CSDL `ptit_chi_nhanh` bằng `ptit_btl_test` rồi chạy bản sao trong Workbench. Cấp cho tài khoản chạy thử cùng các quyền ở bước cài đặt thủ công trên CSDL thử. Trong terminal đã cấu hình kết nối, chạy

```powershell
$env:DB_NAME = 'ptit_btl_test'
.\.venv\Scripts\python.exe tests/kiem_tra.py
Remove-Item Env:DB_NAME
```

Bộ kiểm tra đối chiếu kết quả bốn báo cáo, trả nợ cùng chủ và khác chủ trong dữ liệu mẫu, trường hợp bằng/vượt hạn mức hoặc mức sàn, mở tài khoản và chi tiêu đồng thời, gửi lại mã thanh toán và chống trả thừa. Bộ kiểm tra ghi thêm hồ sơ vào CSDL thử.
