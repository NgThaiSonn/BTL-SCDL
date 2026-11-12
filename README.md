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

## Đối chiếu yêu cầu 3

### Năm yêu cầu bắt buộc

Đọc các kết quả mẫu trước khi ghi thêm giao dịch. Chọn tháng khởi tạo dữ liệu cho hai báo cáo có lọc thời gian.

| Yêu cầu | Thao tác | Kết quả mẫu |
|---|---|---|
| 1. Tính lương | Báo cáo → Lương kinh doanh | NV01 nhận 560.000 đồng, NV02 nhận 500.000 đồng và NV05 nhận 0 đồng. |
| 2. Giao dịch tín dụng trong kỳ | Báo cáo → Giao dịch tín dụng, chọn ngày đầu tháng khởi tạo cho cả hai ô ngày | Nguyễn An trả 1.500.000 đồng trên T202 của Trần Bình. |
| 3. Dư nợ giảm dần | Báo cáo → Dư nợ | T203 đứng đầu với 8.000.000 đồng. |
| 4. Top 10 theo tổng tiền gửi | Báo cáo → Top 10 tiền gửi | Lê Chi đứng đầu với 32.000.000 đồng. |
| 5. Thanh toán từ tiền gửi | Giao dịch → Thanh toán dư nợ | Trả 500.000 đồng từ G101 cho T202. G101 còn 17.000.000 đồng, dư nợ T202 còn 4.000.000 đồng. Thử trả thêm 4.000.001 đồng sẽ bị từ chối. |

### Chức năng phụ và cách trình diễn

| STT | Chức năng | Vị trí | Thao tác và kết quả |
|---|---|---|---|
| 1 | Quản lý hồ sơ khách hàng | Khách hàng | Thêm một khách hàng với mã và CCCD mới, sửa địa chỉ rồi tìm lại theo CCCD để đối chiếu. |
| 2 | Mở tài khoản | Tài khoản → Mở tài khoản | Chọn khách hàng và nhân viên kinh doanh. Kiểm tra tài khoản mới xuất hiện đúng loại và chủ sở hữu. |
| 3 | Nộp tiền gửi | Giao dịch → Nộp tiền gửi | Nộp 100.000 đồng vào G101. Sao kê ghi khoản nộp và số dư tiền gửi tăng 100.000 đồng. |
| 4 | Chi tiêu tín dụng | Giao dịch → Chi tiêu tín dụng | Chi 50.000 đồng trên T202. Phần tín dụng khả dụng giảm và sao kê ghi một giao dịch chi. |
| 5 | Sao kê từng tài khoản | Tài khoản → Sao kê | Tìm G101. Mở sao kê để xem mã giao dịch, thời điểm, số tiền và tài khoản đối ứng. |
| 6 | Tra cứu hồ sơ nhân viên | Nhân viên | Tìm NV03 để xem vị trí giao dịch viên, ngày vào làm, bậc nghề và thâm niên. |
| 7 | Tổng quan chi nhánh | Tổng quan | Đối chiếu số khách, số tài khoản, tổng tiền gửi và nhật ký giao dịch gần đây. |
| 8 | Xuất báo cáo CSV | Báo cáo → Xuất CSV | Chọn kỳ báo cáo, tải CSV và đối chiếu các hàng, cột với kết quả đang hiển thị. |
| 9 | Tra biên lai theo mã | Giao dịch → Tra biên lai | Tra DEMO-06 để thấy Nguyễn An trả hộ Trần Bình 1.500.000 đồng, có Đỗ Thu Hà hỗ trợ. |
| 10 | Thống kê giao dịch có nhân viên hỗ trợ | Báo cáo → Giao dịch nhân viên hỗ trợ | Chọn tháng khởi tạo. NV03 hỗ trợ 2 lượt với tổng 2.200.000 đồng. NV04 hỗ trợ 1 lượt với 1.500.000 đồng. |
| 11 | Đối soát số dư với nhật ký | Báo cáo → Đối soát số dư | Xem số dư được tính lại từ số dư ban đầu và các giao dịch. Lúc khởi tạo, cả 18 tài khoản đều khớp. |

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
