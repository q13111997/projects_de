import pandas as pd

data_file = "tmdb-movies.csv"
data = pd.read_csv(data_file)
print(data.info())
# Sắp xếp các bộ phim theo ngày phát hành giảm dần rồi lưu ra một file mới
# Lọc ra các bộ phim có đánh giá trung bình trên 7.5 rồi lưu ra một file mới
# Tìm ra phim nào có doanh thu cao nhất và doanh thu thấp nhất
# Tính tổng doanh thu tất cả các bộ phim
# Top 10 bộ phim đem về lợi nhuận cao nhất
# Đạo diễn nào có nhiều bộ phim nhất và diễn viên nào đóng nhiều phim nhất
# Thống kê số lượng phim theo các thể loại. Ví dụ có bao nhiêu phim thuộc thể loại Action, bao nhiêu thuộc thể loại Family...