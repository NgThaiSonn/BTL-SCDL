# BTL SCDL

Ứng dụng quản lý chi nhánh ngân hàng cho bài tập lớn môn Cơ sở dữ liệu PTIT (chủ đề 3). Ứng dụng dùng Flask và MySQL 8.4.

## Chạy bằng Docker

Mở Docker Desktop, chạy lệnh sau trong thư mục chứa `compose.yaml`, rồi mở [ứng dụng](http://localhost:8080).

```sh
docker compose up --build -d
```

Lần đầu, ứng dụng tạo 12 khách hàng, 5 nhân viên, 18 tài khoản và 7 giao dịch mẫu. Dùng `docker compose down` để dừng và `docker compose up -d` để mở lại với dữ liệu đã lưu.

## Thử trên giao diện

- Trong **Báo cáo**, chọn lương theo tháng, giao dịch tín dụng theo khoảng ngày, dư nợ hiện tại hoặc top 10 khách hàng có tổng tiền gửi cao nhất.
- Trong **Giao dịch**, chọn **Thanh toán dư nợ**, trích 500.000 đồng từ G101 cho T202. Trên dữ liệu mới khởi tạo, G101 còn 17.000.000 đồng và dư nợ T202 còn 4.000.000 đồng.
- Trong **Tài khoản**, tìm một số tài khoản rồi chọn **Sao kê** để xem giao dịch.

## Chạy với MySQL đã cài trên máy

1. Mở MySQL Workbench, kết nối bằng tài khoản có quyền tạo bảng, trigger, view và thủ tục. Mở `docker/init.sql`, chạy **toàn bộ tệp** một lần trên môi trường mới. Tên CSDL được tạo là `ptit_chi_nhanh`.
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

## Kiểm tra tự động

`tests/kiem_tra.py` gọi các API thực tế trên MySQL. Để chạy lại, tạo một **bản thử nghiệm mới** bằng cách sao chép `docker/init.sql`, thay toàn bộ tên CSDL `ptit_chi_nhanh` bằng `ptit_btl_test` rồi chạy bản sao trong Workbench. Cấp cho tài khoản chạy thử cùng các quyền ở bước cài đặt thủ công trên CSDL thử. Trong terminal đã cấu hình kết nối, chạy

```powershell
$env:DB_NAME = 'ptit_btl_test'
.\.venv\Scripts\python.exe tests/kiem_tra.py
Remove-Item Env:DB_NAME
```

Bộ kiểm tra đối chiếu kết quả bốn báo cáo, trả nợ cùng chủ và khác chủ trong dữ liệu mẫu, trường hợp bằng/vượt hạn mức hoặc mức sàn, mở tài khoản và chi tiêu đồng thời, gửi lại mã thanh toán và chống trả thừa. Bộ kiểm tra ghi thêm hồ sơ vào CSDL thử.
