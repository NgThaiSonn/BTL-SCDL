-- Khởi tạo MySQL cho ứng dụng quản lý chi nhánh ngân hàng.
CREATE DATABASE IF NOT EXISTS ptit_chi_nhanh CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE ptit_chi_nhanh;
SET NAMES utf8mb4;
SET time_zone = '+07:00';

CREATE TABLE nhan_vien (
    ma_nv VARCHAR(12) PRIMARY KEY, cmt VARCHAR(12) NOT NULL UNIQUE,
    ho_ten VARCHAR(100) NOT NULL, ngay_sinh DATE NOT NULL, dia_chi VARCHAR(200) NOT NULL,
    bac_nghe TINYINT UNSIGNED NOT NULL, ngay_vao_lam DATE NOT NULL,
    vi_tri ENUM('KINH_DOANH','GIAO_DICH','QUAN_LY') NOT NULL,
    CHECK (bac_nghe > 0), CHECK (ngay_vao_lam > ngay_sinh)
) ENGINE=InnoDB;

CREATE TABLE khach_hang (
    ma_kh VARCHAR(12) PRIMARY KEY, cmt VARCHAR(12) NOT NULL UNIQUE,
    ho_ten VARCHAR(100) NOT NULL, ngay_sinh DATE NOT NULL, dia_chi VARCHAR(200) NOT NULL
) ENGINE=InnoDB;

-- Ánh xạ hai lớp con EER vào một bảng. Mỗi vị trí (suat) chỉ cấp một lần
-- cho mỗi chủ sở hữu và loại TK. Khóa UNIQUE duy trì trần 2/3 ngay cả khi ghi đồng thời.
CREATE TABLE tai_khoan (
    so_tk VARCHAR(20) PRIMARY KEY,
    ma_kh VARCHAR(12) NOT NULL, nv_mo VARCHAR(12) NOT NULL, ngay_mo DATETIME NOT NULL,
    loai ENUM('GUI','TD') NOT NULL, suat TINYINT NOT NULL,
    so_du DECIMAL(16,0) NOT NULL, tien_gui_dau DECIMAL(16,0),
    du_toi_thieu DECIMAL(16,0), lai_thang DECIMAL(6,3), han_muc DECIMAL(16,0),
    UNIQUE (ma_kh,loai,suat), INDEX (nv_mo,ngay_mo),
    FOREIGN KEY (ma_kh) REFERENCES khach_hang(ma_kh),
    FOREIGN KEY (nv_mo) REFERENCES nhan_vien(ma_nv),
    CHECK (
      (loai='GUI' AND suat BETWEEN 1 AND 3 AND han_muc IS NULL
       AND du_toi_thieu IS NOT NULL AND du_toi_thieu >= 0 AND so_du >= du_toi_thieu
       AND tien_gui_dau IS NOT NULL AND tien_gui_dau >= du_toi_thieu
       AND lai_thang IS NOT NULL AND lai_thang BETWEEN 0 AND 100)
      OR (loai='TD' AND suat BETWEEN 1 AND 2 AND han_muc IS NOT NULL AND han_muc > 0
       AND so_du BETWEEN 0 AND han_muc AND tien_gui_dau IS NULL
       AND du_toi_thieu IS NULL AND lai_thang IS NULL))
) ENGINE=InnoDB;

CREATE TABLE giao_dich (
    ma_gd CHAR(36) PRIMARY KEY, luc DATETIME NOT NULL,
    loai ENUM('NAP','CHI','TRA') NOT NULL, so_tien DECIMAL(16,0) NOT NULL,
    tk_gui VARCHAR(20), tk_td VARCHAR(20), nv_ho_tro VARCHAR(12),
    FOREIGN KEY (tk_gui) REFERENCES tai_khoan(so_tk),
    FOREIGN KEY (tk_td) REFERENCES tai_khoan(so_tk),
    FOREIGN KEY (nv_ho_tro) REFERENCES nhan_vien(ma_nv),
    INDEX (tk_td,luc), INDEX (tk_gui,luc), INDEX(luc),
    CHECK (so_tien > 0),
    CHECK ((loai='NAP' AND tk_gui IS NOT NULL AND tk_td IS NULL)
        OR (loai='CHI' AND tk_td IS NOT NULL AND tk_gui IS NULL)
        OR (loai='TRA' AND tk_gui IS NOT NULL AND tk_td IS NOT NULL AND tk_gui <> tk_td))
) ENGINE=InnoDB;

DELIMITER $$
CREATE TRIGGER kiem_tra_nguoi_mo BEFORE INSERT ON tai_khoan FOR EACH ROW
BEGIN
    IF NOT EXISTS (SELECT 1 FROM nhan_vien WHERE ma_nv=NEW.nv_mo AND vi_tri='KINH_DOANH') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Chỉ nhân viên kinh doanh được mở tài khoản.';
    END IF;
END$$

CREATE PROCEDURE sp_mo_tai_khoan(IN p_tk VARCHAR(20), IN p_kh VARCHAR(12),
    IN p_nv VARCHAR(12), IN p_loai VARCHAR(3), IN p_luc DATETIME,
    IN p_gui DECIMAL(16,0), IN p_min DECIMAL(16,0), IN p_lai DECIMAL(6,3), IN p_hm DECIMAL(16,0))
BEGIN
    DECLARE v_kh VARCHAR(12) DEFAULT NULL;
    DECLARE v_suat INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
    START TRANSACTION;
    SELECT ma_kh INTO v_kh FROM khach_hang WHERE ma_kh=p_kh FOR UPDATE;
    IF v_kh IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Không tìm thấy khách hàng.'; END IF;
    IF p_luc IS NULL OR p_luc>NOW() OR p_tk IS NULL OR TRIM(p_tk)='' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Số tài khoản hoặc thời điểm mở không hợp lệ.';
    END IF;
    IF p_loai IS NULL OR p_loai NOT IN ('GUI','TD') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Loại tài khoản không hợp lệ.';
    END IF;
    SELECT MIN(s.n) INTO v_suat FROM (SELECT 1 n UNION ALL SELECT 2 UNION ALL SELECT 3) s
    LEFT JOIN tai_khoan t ON t.ma_kh=p_kh AND t.loai=p_loai AND t.suat=s.n
    WHERE t.so_tk IS NULL AND s.n<=IF(p_loai='TD',2,3);
    IF v_suat IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Đã đạt giới hạn 2 TK tín dụng hoặc 3 TK gửi tiền.'; END IF;
    IF p_loai='GUI' AND (p_gui IS NULL OR p_min IS NULL OR p_lai IS NULL OR p_gui<p_min
        OR p_min<0 OR p_lai NOT BETWEEN 0 AND 100 OR p_hm IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Kiểm tra tiền gửi đầu, số dư tối thiểu và lãi suất.';
    END IF;
    IF p_loai='TD' AND (p_hm IS NULL OR p_hm<=0 OR p_gui IS NOT NULL OR p_min IS NOT NULL OR p_lai IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Tài khoản tín dụng cần một hạn mức dương.';
    END IF;
    INSERT INTO tai_khoan VALUES (p_tk,p_kh,p_nv,p_luc,p_loai,v_suat,IF(p_loai='TD',p_hm,p_gui),p_gui,p_min,p_lai,p_hm);
    COMMIT;
END$$

-- NAP: nộp vào TK gửi. CHI: sử dụng tín dụng. TRA: thanh toán dư nợ bằng TK gửi.
-- Khóa nguồn gửi rồi khóa đích tín dụng theo cùng thứ tự ở mọi giao dịch.
CREATE PROCEDURE sp_giao_dich(IN p_ma CHAR(36), IN p_loai VARCHAR(3),
    IN p_gui VARCHAR(20), IN p_td VARCHAR(20), IN p_tien DECIMAL(16,0),
    IN p_nv VARCHAR(12), IN p_luc DATETIME)
body: BEGIN
    DECLARE v_gui, v_min, v_td, v_hm DECIMAL(16,0);
    DECLARE v_mo_gui, v_mo_td DATETIME;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
    START TRANSACTION;
    IF p_ma IS NULL OR CHAR_LENGTH(TRIM(p_ma))=0 OR p_tien IS NULL OR p_tien<=0
       OR p_luc IS NULL OR p_luc>NOW() OR p_loai IS NULL OR p_loai NOT IN ('NAP','CHI','TRA') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Mã, loại, số tiền hoặc thời điểm giao dịch không hợp lệ.';
    END IF;
    IF (p_loai IN ('NAP','TRA')) <> (p_gui IS NOT NULL)
       OR (p_loai IN ('CHI','TRA')) <> (p_td IS NOT NULL) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Chọn đúng tài khoản nguồn và đích cho nghiệp vụ.';
    END IF;
    IF p_gui IS NOT NULL THEN
        SELECT so_du,du_toi_thieu,ngay_mo INTO v_gui,v_min,v_mo_gui FROM tai_khoan
        WHERE so_tk=p_gui AND loai='GUI' FOR UPDATE;
        IF v_gui IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Tài khoản gửi tiền không tồn tại.'; END IF;
    END IF;
    IF p_td IS NOT NULL THEN
        SELECT so_du,han_muc,ngay_mo INTO v_td,v_hm,v_mo_td FROM tai_khoan
        WHERE so_tk=p_td AND loai='TD' FOR UPDATE;
        IF v_td IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Tài khoản tín dụng không tồn tại.'; END IF;
    END IF;
    IF EXISTS (SELECT 1 FROM giao_dich WHERE ma_gd=p_ma) THEN
        IF NOT EXISTS (SELECT 1 FROM giao_dich WHERE ma_gd=p_ma AND loai=p_loai
           AND tk_gui <=> p_gui AND tk_td <=> p_td AND so_tien=p_tien AND nv_ho_tro <=> p_nv) THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Mã yêu cầu đã được dùng cho một giao dịch khác.';
        END IF;
        COMMIT;
        LEAVE body;
    END IF;
    IF p_luc<v_mo_gui OR p_luc<v_mo_td THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Giao dịch xảy ra trước thời điểm mở tài khoản.';
    END IF;
    IF p_loai='CHI' AND p_tien>v_td THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Giao dịch vượt hạn mức tín dụng còn lại.'; END IF;
    IF p_loai='TRA' AND v_gui-p_tien<v_min THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Số dư sau thanh toán thấp hơn mức tối thiểu.'; END IF;
    IF p_loai='TRA' AND p_tien>v_hm-v_td THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Số tiền thanh toán vượt dư nợ hiện tại.'; END IF;
    INSERT INTO giao_dich VALUES (p_ma,p_luc,p_loai,p_tien,p_gui,p_td,p_nv);
    IF p_gui IS NOT NULL THEN
        UPDATE tai_khoan SET so_du=so_du+IF(p_loai='NAP',p_tien,-p_tien) WHERE so_tk=p_gui;
    END IF;
    IF p_td IS NOT NULL THEN
        UPDATE tai_khoan SET so_du=so_du+IF(p_loai='TRA',p_tien,-p_tien) WHERE so_tk=p_td;
    END IF;
    COMMIT;
END$$

-- Yêu cầu 1. Bao gồm nhân viên kinh doanh không mở tài khoản trong tháng.
CREATE PROCEDURE sp_luong(IN p_thang DATE)
BEGIN
    DECLARE v_dau DATE;
    SET v_dau=DATE_SUB(p_thang, INTERVAL (DAYOFMONTH(p_thang)-1) DAY);
    SELECT n.ma_nv,n.ho_ten,COUNT(IF(t.loai='TD',1,NULL)) so_td,COUNT(IF(t.loai='GUI',1,NULL)) so_gui,
        COALESCE(SUM(t.tien_gui_dau),0) tong_gui_dau,
        COALESCE(SUM(CASE WHEN t.loai='TD' THEN 500000 WHEN t.loai='GUI' THEN t.tien_gui_dau*0.02 ELSE 0 END),0) luong
    FROM nhan_vien n LEFT JOIN tai_khoan t ON t.nv_mo=n.ma_nv AND t.ngay_mo>=v_dau
        AND t.ngay_mo<DATE_ADD(v_dau,INTERVAL 1 MONTH)
    WHERE n.vi_tri='KINH_DOANH' GROUP BY n.ma_nv,n.ho_ten ORDER BY luong DESC,n.ma_nv;
END$$

-- Yêu cầu 2. Phân biệt người thực hiện và chủ TK tín dụng khi trả nợ hộ.
CREATE PROCEDURE sp_tin_dung_trong_ky(IN p_tu DATE, IN p_den DATE)
BEGIN
    IF p_tu IS NULL OR p_den IS NULL OR p_tu>p_den THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Khoảng ngày không hợp lệ.'; END IF;
    SELECT k.ma_kh,k.ho_ten,td.so_tk,chu.ho_ten chu_tk,COUNT(*) so_luot,
       SUM(IF(g.loai='CHI',g.so_tien,0)) chi_tieu,SUM(IF(g.loai='TRA',g.so_tien,0)) thanh_toan,
       SUM(g.so_tien) tong_giao_dich
    FROM giao_dich g JOIN tai_khoan td ON td.so_tk=g.tk_td LEFT JOIN tai_khoan gui ON gui.so_tk=g.tk_gui
    JOIN khach_hang k ON k.ma_kh=COALESCE(gui.ma_kh,td.ma_kh) JOIN khach_hang chu ON chu.ma_kh=td.ma_kh
    WHERE g.luc>=p_tu AND g.luc<DATE_ADD(p_den,INTERVAL 1 DAY)
    GROUP BY k.ma_kh,k.ho_ten,td.so_tk,chu.ho_ten ORDER BY k.ma_kh,td.so_tk;
END$$
DELIMITER ;

-- Yêu cầu 3 và 4. Truy vấn ở cuối tệp quy định thứ tự và số dòng trả về.
CREATE VIEW v_du_no AS
SELECT t.so_tk,k.ma_kh,k.ho_ten,t.han_muc,t.so_du kha_dung,t.han_muc-t.so_du du_no
FROM tai_khoan t JOIN khach_hang k ON t.ma_kh=k.ma_kh WHERE t.loai='TD';
CREATE VIEW v_tien_gui AS
SELECT k.ma_kh,k.ho_ten,COUNT(*) so_tk_gui,SUM(t.so_du) tong_gui
FROM tai_khoan t JOIN khach_hang k ON t.ma_kh=k.ma_kh WHERE t.loai='GUI' GROUP BY k.ma_kh,k.ho_ten;

INSERT INTO nhan_vien VALUES
('NV01','910000000001','Nguyễn Minh Anh','1993-06-14','Hà Nội',3,'2018-07-01','KINH_DOANH'),
('NV02','910000000002','Trần Hải Yến','1995-03-19','Bắc Ninh',2,'2020-02-10','KINH_DOANH'),
('NV03','910000000003','Lê Đức Nam','1991-09-03','Hà Nội',4,'2016-08-15','GIAO_DICH'),
('NV04','910000000004','Đỗ Thu Hà','1988-01-27','Hà Nội',5,'2013-10-01','QUAN_LY'),
('NV05','910000000005','Phan Hoàng Vũ','1997-11-06','Hà Nội',1,'2022-04-12','KINH_DOANH');
INSERT INTO khach_hang VALUES
('KH01','920000000001','Nguyễn An','1996-02-15','Hà Đông, Hà Nội'),
('KH02','920000000002','Trần Bình','1990-03-20','Thanh Xuân, Hà Nội'),
('KH03','920000000003','Lê Chi','1994-06-08','Cầu Giấy, Hà Nội'),
('KH04','920000000004','Đỗ Dũng','1987-11-18','Hà Đông, Hà Nội'),
('KH05','920000000005','Hoàng Giang','2000-12-09','Bắc Ninh'),
('KH06','920000000006','Vũ Hạnh','1998-09-22','Hải Phòng'),
('KH07','920000000007','Phạm Khôi','1995-04-10','Hà Nội'),
('KH08','920000000008','Đào Linh','1988-07-25','Hải Dương'),
('KH09','920000000009','Bùi Minh','1991-01-09','Hà Nội'),
('KH10','920000000010','Ngô Ngọc','1993-10-13','Hà Nội'),
('KH11','920000000011','Phan Phúc','1996-05-06','Hưng Yên'),
('KH12','920000000012','Đặng Trang','1999-08-29','Hà Nội');

-- Hai tháng để thử lọc kỳ. Toàn bộ dữ liệu dùng thủ tục giống ứng dụng.
SET @nay=CAST(DATE_FORMAT(CURRENT_DATE,'%Y-%m-01') AS DATE);
SET @truoc=DATE_SUB(@nay,INTERVAL 1 MONTH);
CALL sp_mo_tai_khoan('G101','KH01','NV01','GUI',@truoc,20000000,100000,0.45,NULL);
CALL sp_mo_tai_khoan('G102','KH02','NV02','GUI',@truoc,8500000,100000,0.35,NULL);
CALL sp_mo_tai_khoan('G103','KH03','NV01','GUI',@truoc,32000000,100000,0.45,NULL);
CALL sp_mo_tai_khoan('G104','KH04','NV02','GUI',@truoc,7200000,100000,0.35,NULL);
CALL sp_mo_tai_khoan('G105','KH05','NV01','GUI',@truoc,4200000,100000,0.35,NULL);
CALL sp_mo_tai_khoan('G106','KH06','NV02','GUI',@truoc,15800000,100000,0.45,NULL);
CALL sp_mo_tai_khoan('G107','KH07','NV01','GUI',@truoc,9200000,100000,0.35,NULL);
CALL sp_mo_tai_khoan('G108','KH08','NV02','GUI',@truoc,6500000,100000,0.35,NULL);
CALL sp_mo_tai_khoan('G109','KH09','NV01','GUI',@truoc,12000000,100000,0.45,NULL);
CALL sp_mo_tai_khoan('G110','KH10','NV02','GUI',@truoc,3500000,100000,0.35,NULL);
CALL sp_mo_tai_khoan('G111','KH11','NV01','GUI',@truoc,27500000,100000,0.45,NULL);
CALL sp_mo_tai_khoan('G112','KH12','NV02','GUI',@truoc,5600000,100000,0.35,NULL);
CALL sp_mo_tai_khoan('T201','KH01','NV01','TD',@truoc,NULL,NULL,NULL,10000000);
CALL sp_mo_tai_khoan('T202','KH02','NV02','TD',@truoc,NULL,NULL,NULL,15000000);
CALL sp_mo_tai_khoan('T203','KH03','NV01','TD',@truoc,NULL,NULL,NULL,20000000);
CALL sp_mo_tai_khoan('T204','KH04','NV02','TD',@nay,NULL,NULL,NULL,5000000);
CALL sp_mo_tai_khoan('G113','KH01','NV01','GUI',@nay,3000000,50000,0.3,NULL);
CALL sp_mo_tai_khoan('T205','KH01','NV01','TD',@nay,NULL,NULL,NULL,4000000);
CALL sp_giao_dich('DEMO-01','CHI',NULL,'T201',4500000,'NV03',DATE_ADD(@truoc,INTERVAL 5 DAY));
CALL sp_giao_dich('DEMO-02','CHI',NULL,'T202',6000000,NULL,DATE_ADD(@truoc,INTERVAL 7 DAY));
CALL sp_giao_dich('DEMO-03','CHI',NULL,'T203',8000000,'NV04',DATE_ADD(@truoc,INTERVAL 9 DAY));
CALL sp_giao_dich('DEMO-04','NAP','G104',NULL,500000,'NV03',DATE_ADD(@truoc,INTERVAL 12 DAY));
CALL sp_giao_dich('DEMO-05','TRA','G101','T201',1000000,'NV03',@nay);
-- Yêu cầu 5: Nguyễn An (G101) thanh toán hộ Trần Bình (T202).
CALL sp_giao_dich('DEMO-06','TRA','G101','T202',1500000,'NV04',@nay);
CALL sp_giao_dich('DEMO-07','CHI',NULL,'T204',1200000,'NV03',@nay);
