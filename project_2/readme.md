# Project Kéo Dữ liệu từ TIKI qua API

## Giới thiệu
Đây là một project crawl dữ liệu từ tiki viết bằng Python, có thể chạy liên tục để thu thập dữ liệu, xuất dữ liệu ra file csv, mỗi file chứa dữ liệu của 1000 sản phẩm.  
Để quản lý quá trình crawl dữ liệu, project sử dụng **Supervisor** nhằm đảm bảo:
- Chương trình tự động restart nếu bị crash.
- Quản lý, start/stop dễ dàng qua `supervisorctl`.

---

## Cấu trúc thư mục
```bash
project_2/
├── configs/
│   └── supervisord.conf   # file cấu hình Supervisor
├── data/                  # db sqlite crawl.db lưu trạng thái crawl của từng product id
├── input/                 # file chứa 200,000 product id của TIKI
├── logs/                  # log hệ thống Supervisor, log crawl data và file tổng hợp kết quả crawl sau khi chạy xong chương trình
├── output/                # các file csv chứa thông tin sản phẩm crawl về qua API
├── src/
│   └── configs.py         # chứa cấu hình chung của project như API URL, header, file path...
│   └── crawler.py         # chứa các hàm chính để crawl dữ liệu từ API qua product id, trả về thông tin sản phẩm
│   └── db.py              # tạo db sqlite và import 200,000 product id từ file
│   └── main.py            # code chính quản lý toàn bộ luồng kéo dữ liệu
│   └── utlis.py           # chứa hàm clean trường description
└── README.md              # file mô tả dự án
```

## Hướng dẫn sử dụng Supervisor để chạy project
## 1. Khởi tạo Supervisor
```python
supervisord -c /home/<user>/projects_de/project_2/configs/supervisord.conf
```
## 2. Quản lý tiến trình crawl bằng supervisorctl
### Xem trạng thái job crawl
```python
supervisorctl -c /home/<user>/projects_de/project_2/configs/supervisord.conf status
```
### Start job crawl
```python
supervisorctl -c /home/<user>/projects_de/project_2/configs/supervisord.conf start crawl
```
### Stop job crawl
```python
supervisorctl -c /home/<user>/projects_de/project_2/configs/supervisord.conf stop crawl
```
### Restart job crawl
```python
supervisorctl -c /home/<user>/projects_de/project_2/configs/supervisord.conf restart crawl
```
### Reload Supervisor sau khi thay đổi config
```python
supervisorctl -c /home/<user>/projects_de/project_2/configs/supervisord.conf reread
supervisorctl -c /home/<user>/projects_de/project_2/configs/supervisord.conf update
```
## Test autorestart
### B1: Lấy PID tiến trình crawl
```bash
supervisorctl -c /home/<user>/projects_de/project_2/configs/supervisord.conf status
```
### B2: Kill tiến trình
```bash
kill -9 <pid>
```
### B3: Kiểm tra lại trạng thái (pid thay đổi là job đã được restart thành công)
```bash
supervisorctl -c /home/<user>/projects_de/project_2/configs/supervisord.conf status
```