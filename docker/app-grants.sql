REVOKE ALL PRIVILEGES ON ptit_chi_nhanh.* FROM 'ptit_app'@'%';
GRANT SELECT, EXECUTE ON ptit_chi_nhanh.* TO 'ptit_app'@'%';
GRANT INSERT, UPDATE (dia_chi) ON ptit_chi_nhanh.khach_hang TO 'ptit_app'@'%';
