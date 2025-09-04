#!/bin/bash
# CÀI CSVQUOTE
sudo apt install golang-go
git clone https://github.com/adamgordonbell/csvquote
cd csvquote
go build -o csvquote cmd/cvsquote/main.go
cp ./csvquote /usr/local/bin

# Tìm ra những dòng hoàn toàn giống nhau
csvquote tmdb-movies.csv | sort | uniq -d | csvquote -u > duplicate_rows.csv
# Xuất ra file mới dedup những dòng bị duplicate
(head -n1 tmdb-movies.csv && tail -n +2 tmdb-movies.csv | csvquote | sort -u | csvquote -u) > tmdb_movies_cleaned.csv

# Sắp xếp các bộ phim theo ngày phát hành giảm dần rồi lưu ra một file mới
acsvquote tmdb_movies_cleaned.csv |\
awk -F',' 'BEGIN {OFS=","}
NR==1 {
    print "full_date," $0
    next
}
NR>1 {
    year = $19
    split($16, d, "/")
    month = (sprintf("%02d", d[1]))
    day   = (sprintf("%02d", d[2]))
    full_date = year "-" month "-" day
    print full_date, $0
}' |\
sort -t',' -k1,1r |\
cut -d',' -f2- |\
csvquote -u > sort.csv

# Lọc ra các bộ phim có đánh giá trung bình trên 7.5 rồi lưu ra một file mới
{
		head -n 1 tmdb_movies_cleaned.csv

		tail -n +2 tmdb_movies_cleaned.csv |\
		csvquote |\
		awk -F',' '$22 > 7.5' |\
		csvquote -u
} > high_rate.csv

# Tìm ra phim nào có doanh thu cao nhất và doanh thu thấp nhất
csvquote tmdb_movies_cleaned.csv |\
awk -F',' '
NR==1 {
    header = $0
    next
}
NR==2 {
    min=$5
    max=$5
    minlines[NR]=$0
    maxlines[NR]=$0
    next
}
{
    if ($5 < min) {
        min = $5
        delete minlines
        minlines[NR] = $0
    }
    else if ($5 == min) {
        minlines[NR] = $0
    }
    if ($5 > max) {
        max = $5
        delete maxlines
        maxlines[NR] = $0
    }
    else if ($5 == max) {
        maxlines[NR] = $0
    }
}
END {
    print header;
    print "-----Max Revenue-----"
    for (i in maxlines) print maxlines[i]
    print "-----Min Revenue-----"
    for (i in minlines) print minlines[i]
}' | csvquote -u > revenue.csv

# Tính tổng doanh thu tất cả các bộ phim
csvquote tmdb-movies_cleaned.csv | awk -F',' 'NR > 1 {sum += $5} END {print "Total Revenue: " sum}' > sum_revenue.csv

# Top 10 bộ phim đem về lợi nhuận cao nhất
csvquote tmdb_movies_cleaned.csv |\
awk -F',' 'BEGIN {OFS=","}
NR>1 {
    budget=$4
    revenue=$5
    profit=revenue-budget
    print profit, $6
}
' | sort -t',' -k1,1nr |\
head -10 |\
awk 'BEGIN{print "profit,title"} {print}' |\
csvquote -u > top_10_revenue.csv

# Đạo diễn nào có nhiều bộ phim nhất và diễn viên nào đóng nhiều phim nhất
csvquote tmdb_movies_cleaned.csv |\
awk -F',' '
NR>1 && $9 != "" {
    cnt[$9]++
}
END {
    max = 0
    name = ""
    for (i in cnt) {
        if (cnt[i] > max) {
            max = cnt[i]
            name = i
        }
    }
    print "Director: " name
    print "Movies count: " max
}' | csvquote -u > top_director.csv

csvquote tmdb_movies_cleaned.csv |\
awk -F',' '
NR>1 && $7 != "" {
    n = split($7, arr, "|")
    delete seen
    for (i=1; i<=n; i++) {
        gsub(/^ +| +$/, "", arr[i])
        if (!(arr[i] in seen)) {
		        cnt[arr[i]]++
				    seen[arr[i]] = 1
        }
    }
}
END {
    max=0
    name=""
    for (a in cnt) {
        if (cnt[a] > max) {
            max=cnt[a]
            name=a
        }
    }
    print "Actor: " name
    print "Movies count: " max
}' | csvquote -u > top_actor.csv

# Thống kê số lượng phim theo các thể loại. Ví dụ có bao nhiêu phim thuộc thể loại Action bao nhiêu thuộc thể loại Family, ….
csvquote tmdb_movies_cleaned.csv |\
awk -F',' 'BEGIN {OFS=","}
NR>1 && $14 != "" {
    n = split($14, arr, "|")
    for (i=1; i<=n; i++) {
        gsub(/^ +| +$/, "", arr[i])
        cnt[arr[i]]++
    }
}
END {
    print "Actor,Movies count"
    for (a in cnt) {
        max=cnt[a]
        name=a
        print name, max
    }
}' | csvquote -u > genre.csv

# Idea của bạn để có thêm những phân tích cho dữ liệu?
# 1. Top 10 công ty tham gia phát hành nhiều phim nhất
# 2. Top 10 phim có lượt đánh giá, điểm đánh giá trung bình cao nhất
# 3. Top 10 keywords phổ biến nhất qua các thời kỳ (chia mỗi khoáng 5 hoặc 10 năm)
# 4. Tổng doanh thu từ các bộ phim của từng đạo diễn
# 5. Số lượng phim phát hành trong từng năm
# 6. Top 10 bộ phim có kinh phí đầu tư cao nhất
# 7. Thời lượng phim trung bình qua các thời kỳ (chia mỗi khoảng 5 hoặc 10 năm)
# 8. Top 10 đạo diễn có điểm đánh giá trung bình các bộ phim cao nhất
# 9. Điểm đánh giá trung bình của từng thể loại phim
# 10.