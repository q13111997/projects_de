import pandas as pd
import numpy as np

data_file = 'tmdb-movies.csv'
df = pd.read_csv(data_file)


df.drop_duplicates(inplace=True)
df['release_date'] = pd.to_datetime(df['release_date'], format='%m/%d/%y', errors='coerce')
df['revenue'] = df['revenue'].replace(0, np.nan)
df['budget'] = df['budget'].replace(0, np.nan)

print(df.info())

# Sắp xếp các bộ phim theo ngày phát hành giảm dần rồi lưu ra một file mới
df_1 = df.sort_values('release_date',ascending=False)
df_1.to_csv('sort_by_release_date.csv')

# Lọc ra các bộ phim có đánh giá trung bình trên 7.5 rồi lưu ra một file mới
df_2 = df[df['vote_average'] > 7.5].sort_values('vote_average',ascending=False)
df_2.to_csv('vote_greater_than_7.5.csv')

# Tìm ra phim nào có doanh thu cao nhất và doanh thu thấp nhất
print('Những bộ phim có doanh thu cao nhất:')
for idx, row in df[df['revenue'] == df['revenue'].max()][['original_title','revenue']].iterrows():
    movie = row['original_title']
    revenue = row['revenue']
    print(f'+ {movie} - {revenue}')
print('\nNhững bộ phim có doanh thu thấp nhất:')
for idx, row in df[df['revenue'] == df['revenue'].min()][['original_title','revenue']].iterrows():
    movie = row['original_title']
    revenue = row['revenue']
    print(f'+ {movie} - {revenue}')

# Tính tổng doanh thu tất cả các bộ phim
total = df['revenue'].sum()
print('\nTổng doanh thu của tất cả các bộ phim:')
print(total)

# Top 10 bộ phim đem về lợi nhuận cao nhất
df['profit'] = df['revenue'] - df['budget']
top_10 = df.dropna(subset=['profit']).sort_values('profit',ascending=False).head(10)[['original_title','profit']]
print('\nTop 10 bộ phim đem về lợi nhuận cao nhất:')
for idx, row in top_10.iterrows():
    title = row['original_title']
    profit = row['profit']
    print(f'+ {title} - {profit}')

# Đạo diễn nào có nhiều bộ phim nhất và diễn viên nào đóng nhiều phim nhất
top_director = df['director'].value_counts()
print('\nĐạo diễn có nhiều bộ phim nhất')
director = top_director.index[0]
cnt = top_director.iloc[0]
print(f'{director} - {cnt} bộ phim')

print('\nDiễn viên đóng nhiều phim nhất:')
cast = df['cast'].dropna().str.split('|')
cast = cast.explode()
cast_count = cast.value_counts()
actor = cast_count.index[0]
cnt = cast_count.iloc[0]
print(f'{actor} - {cnt} bộ phim')

# Thống kê số lượng phim theo các thể loại. Ví dụ có bao nhiêu phim thuộc thể loại Action, bao nhiêu thuộc thể loại Family...
print('\nThống kê số lượng phim theo các thể loại:')
genres = df['genres'].dropna().str.split('|').explode()
genres_count = genres.value_counts().reset_index()
genres_count.columns = ['genre','count']
for idx, row in genres_count.iterrows():
    genre = row['genre']
    cnt = row['count']
    print(f'+ {genre} - {cnt} bộ phim')
#     print(f'{genre} - {cnt} bộ phim')