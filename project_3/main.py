import pandas as pd
import numpy as np

data_file = "tmdb-movies.csv"
df = pd.read_csv(data_file)


df.drop_duplicates(inplace=True)
df['release_date'] = pd.to_datetime(df['release_date'], format="%m/%d/%y", errors="coerce")
df['revenue'] = df['revenue'].replace(0, np.nan)

# print(df.info())

# Sắp xếp các bộ phim theo ngày phát hành giảm dần rồi lưu ra một file mới
df_1 = df.sort_values('release_date',ascending=False)
df_1.to_csv('sort_by_release_date.csv')

# Lọc ra các bộ phim có đánh giá trung bình trên 7.5 rồi lưu ra một file mới
# df_2 = df[df['vote_average'] > 7.5].sort_values('vote_average',ascending=False)
# df_2.to_csv('vote_greater_than_7.5.csv')
a = df[df['revenue'] == df['revenue'].min()][['original_title','revenue']]
for idx, row in a.iterrows():
    print(row['original_title'])
# print(a['original_title'])
# Tìm ra phim nào có doanh thu cao nhất và doanh thu thấp nhất
# with open('min_max_revenue.txt','w') as file:
#     file.write("- Những bộ phim có doanh thu cao nhất:\n")
#     for row in df[df['revenue'] == df['revenue'].max()][['original_title','revenue']]:
#         file.write(f"{movie} (Doanh thu: {revenue})")
#         file.write("\n")
#     file.write("- Những bộ phim có doanh thu thấp nhất:\n")
#     for movie, revenue in df[df['revenue'] == df['revenue'].min()][['original_title','revenue']]:
#         file.write(f"{movie} (Doanh thu: {revenue})")
#         file.write("\n")

# Tính tổng doanh thu tất cả các bộ phim


# Top 10 bộ phim đem về lợi nhuận cao nhất


# Đạo diễn nào có nhiều bộ phim nhất và diễn viên nào đóng nhiều phim nhất


# Thống kê số lượng phim theo các thể loại. Ví dụ có bao nhiêu phim thuộc thể loại Action, bao nhiêu thuộc thể loại Family...

