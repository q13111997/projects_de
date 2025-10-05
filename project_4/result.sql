USE beemovies;

/* Now that you have imported the data sets, let’s explore some of the tables. 
 To begin with, it is beneficial to know the shape of the tables and whether any column has null values.
 Further in this segment, you will take a look at 'movies' and 'genre' tables.*/


-- Segment 1:

-- Q1. Find the total number of rows in each table of the schema?
-- Type your code below:
SELECT 'director_mapping' AS table_name, COUNT(*) AS row_count FROM director_mapping;
SELECT 'genre' AS table_name, COUNT(*) AS row_count FROM genre;
SELECT 'movie' AS table_name, COUNT(*) AS row_count FROM movie;
SELECT 'names' AS table_name, COUNT(*) AS row_count FROM names;
SELECT 'ratings' AS table_name, COUNT(*) AS row_count FROM ratings;
SELECT 'role_mapping' AS table_name, COUNT(*) AS row_count FROM role_mapping;

-- Q2. Which columns in the movie table have null values?
-- Type your code below:
SELECT
	COUNT(CASE WHEN id IS NULL THEN 1 END) id
	,COUNT(CASE WHEN title IS NULL THEN 1 END) title
	,COUNT(CASE WHEN year IS NULL THEN 1 END) year
	,COUNT(CASE WHEN date_published IS NULL THEN 1 END) date_published
	,COUNT(CASE WHEN duration IS NULL THEN 1 END) duration
	,COUNT(CASE WHEN country IS NULL THEN 1 END) country
	,COUNT(CASE WHEN worlwide_gross_income IS NULL THEN 1 END) worlwide_gross_income
	,COUNT(CASE WHEN languages IS NULL THEN 1 END) languages
	,COUNT(CASE WHEN production_company IS NULL THEN 1 END) production_company
FROM movie;

-- Now as you can see four columns of the movie table has null values. Let's look at the at the movies released each year. 
-- Q3. Find the total number of movies released each year? How does the trend look month wise? (Output expected)

/* Output format for the first part:

+---------------+-------------------+
| Year			|	number_of_movies|
+-------------------+----------------
|	2017		|	2134			|
|	2018		|		.			|
|	2019		|		.			|
+---------------+-------------------+


Output format for the second part of the question:
+---------------+-------------------+
|	month_num	|	number_of_movies|
+---------------+----------------
|	1			|	 134			|
|	2			|	 231			|
|	.			|		.			|
+---------------+-------------------+ */
-- Type your code below:
SELECT
    year
    ,count(*) number_of_movies
FROM movie
GROUP BY year
ORDER BY 1;


SELECT	
    DATE_FORMAT(date_published,'%m') month
    ,COUNT(*) number_of_movies
FROM movie
GROUP BY DATE_FORMAT(date_published,'%m')
ORDER BY 1;


/*The highest number of movies is produced in the month of March.
So, now that you have understood the month-wise trend of movies, let’s take a look at the other details in the movies table. 
We know USA and India produces huge number of movies each year. Lets find the number of movies produced by USA or India for the last year.*/
  
-- Q4. How many movies were produced in the USA or India in the year 2019??
-- Type your code below:
SELECT
    COUNT(CASE WHEN UPPER(country) LIKE '%USA%' THEN 1 END) usa_movies_count
    ,COUNT(CASE WHEN UPPER(country) LIKE '%INDIA%' THEN 1 END) india_movies_count
FROM movie
WHERE year = 2019;

/* USA and India produced more than a thousand movies(you know the exact number!) in the year 2019.
Exploring table Genre would be fun!! 
Let’s find out the different genres in the dataset.*/

-- Q5. Find the unique list of the genres present in the data set?
-- Type your code below:
SELECT DISTINCT genre
FROM genre;

/* So, Bee Movies plans to make a movie of one of these genres.
Now, wouldn’t you want to know which genre had the highest number of movies produced in the last year?
Combining both the movie and genres table can give more interesting insights. */

-- Q6.Which genre had the highest number of movies produced overall?
-- Type your code below:
SELECT 
    g.genre
	,COUNT(DISTINCT g.movie_id) number_of_movie
FROM genre g
GROUP BY g.genre
ORDER BY 2 DESC
LIMIT 1;

/* So, based on the insight that you just drew, Bee Movies should focus on the ‘Drama’ genre. 
But wait, it is too early to decide. A movie can belong to two or more genres. 
So, let’s find out the count of movies that belong to only one genre.*/

-- Q7. How many movies belong to only one genre?
-- Type your code below:
SELECT *
FROM movie m
JOIN 
    (SELECT movie_id, COUNT(DISTINCT genre) number_of_genres
    FROM genre
    GROUP BY movie_id
    HAVING COUNT(DISTINCT genre) = 1) g on m.id = g.movie_id
;

/* There are more than three thousand movies which has only one genre associated with them.
So, this figure appears significant. 
Now, let's find out the possible duration of Bee Movies’ next project.*/

-- Q8.What is the average duration of movies in each genre? 
-- (Note: The same movie can belong to multiple genres.)

/* Output format:

+---------------+-------------------+
| genre			|	avg_duration	|
+-------------------+----------------
|	thriller	|		105			|
|	.			|		.			|
|	.			|		.			|
+---------------+-------------------+ */
-- Type your code below:
SELECT
    g.genre
    ,ROUND(AVG(m.duration),0) avg_duration
FROM movie m
JOIN genre g ON m.id = g.movie_id
GROUP BY g.genre;

/* Now you know, movies of genre 'Drama' (produced highest in number in 2019) has the average duration of 106.77 mins.
Lets find where the movies of genre 'thriller' on the basis of number of movies.*/

-- Q9.What is the rank of the ‘thriller’ genre of movies among all the genres in terms of number of movies produced? 
-- (Hint: Use the Rank function)


/* Output format:
+---------------+-------------------+---------------------+
| genre			|		movie_count	|		genre_rank    |	
+---------------+-------------------+---------------------+
|drama			|	2312			|			2		  |
+---------------+-------------------+---------------------+*/
-- Type your code below:
SELECT
    a.genre
    ,a.movie_count
    ,a.genre_rank
FROM
	(SELECT 
	    g.genre
		,COUNT(DISTINCT g.movie_id) movie_count
		,RANK() OVER (ORDER BY COUNT(DISTINCT g.movie_id) DESC) genre_rank
	FROM genre g
	GROUP BY g.genre) a
WHERE a.genre = 'Thriller';

/*Thriller movies is in top 3 among all genres in terms of number of movies
 In the previous segment, you analysed the movies and genres tables. 
 In this segment, you will analyse the ratings table as well.
To start with lets get the min and max values of different columns in the table*/

-- Segment 2:

-- Q10.  Find the minimum and maximum values in  each column of the ratings table except the movie_id column?
/* Output format:
+---------------+-------------------+---------------------+----------------------+-----------------+-----------------+
| min_avg_rating|	max_avg_rating	|	min_total_votes   |	max_total_votes 	 |min_median_rating|min_median_rating|
+---------------+-------------------+---------------------+----------------------+-----------------+-----------------+
|		0		|			5		|	       177		  |	   2000	    		 |		0	       |	8			 |
+---------------+-------------------+---------------------+----------------------+-----------------+-----------------+*/
-- Type your code below:
SELECT
    MIN(avg_rating) min_avg_rating
    ,MAX(avg_rating) max_avg_rating
    ,MIN(total_votes) min_total_votes
    ,MAX(total_votes) max_total_votes
    ,MIN(median_rating) min_median_rating
    ,MAX(median_rating) max_median_rating
FROM ratings;

/* So, the minimum and maximum values in each column of the ratings table are in the expected range. 
This implies there are no outliers in the table. 
Now, let’s find out the top 10 movies based on average rating.*/

-- Q11. Which are the top 10 movies based on average rating?
/* Output format:
+---------------+-------------------+---------------------+
| title			|		avg_rating	|		movie_rank    |
+---------------+-------------------+---------------------+
| Fan			|		9.6			|			5	  	  |
|	.			|		.			|			.		  |
|	.			|		.			|			.		  |
|	.			|		.			|			.		  |
+---------------+-------------------+---------------------+*/
-- Type your code below:
-- It's ok if RANK() or DENSE_RANK() is used too
SELECT
    a.title
    ,a.avg_rating
    ,a.movie_rank
FROM
	(SELECT
	    m.title
	    ,r.avg_rating
	    ,RANK() OVER (ORDER BY r.avg_rating DESC) movie_rank
	FROM ratings r
	JOIN movie m ON r.movie_id = m.id) a
WHERE a.movie_rank <= 10;

/* Do you find you favourite movie FAN in the top 10 movies with an average rating of 9.6? If not, please check your code again!!
So, now that you know the top 10 movies, do you think character actors and filler actors can be from these movies?
Summarising the ratings table based on the movie counts by median rating can give an excellent insight.*/

-- Q12. Summarise the ratings table based on the movie counts by median ratings.
/* Output format:

+---------------+-------------------+
| median_rating	|	movie_count		|
+-------------------+----------------
|	1			|		105			|
|	.			|		.			|
|	.			|		.			|
+---------------+-------------------+ */
-- Type your code below:
-- Order by is good to have
SELECT
    median_rating
    ,COUNT(DISTINCT movie_id) movie_count
FROM ratings
GROUP BY median_rating;

/* Movies with a median rating of 7 is highest in number. 
Now, let's find out the production house with which Bee Movies can partner for its next project.*/

-- Q13. Which production house has produced the most number of hit movies (average rating > 8)??
/* Output format:
+------------------+-------------------+---------------------+
|production_company|movie_count	       |	prod_company_rank|
+------------------+-------------------+---------------------+
| The Archers	   |		1		   |			1	  	 |
+------------------+-------------------+---------------------+*/
-- Type your code below:
SELECT
    a.production_company
    ,a.movie_count
    ,a.prod_company_rank
FROM
	(SELECT
	    m.production_company
	    ,COUNT(DISTINCT m.id) movie_count
	    ,RANK() OVER (ORDER BY COUNT(DISTINCT m.id) DESC) prod_company_rank
	FROM movie m
	JOIN ratings r ON m.id = r.movie_id 
					  AND r.avg_rating > 8
	WHERE m.production_company IS NOT NULL				  
	GROUP BY m.production_company) a
WHERE prod_company_rank = 1;

-- It's ok if RANK() or DENSE_RANK() is used too
-- Answer can be Dream Warrior Pictures or National Theatre Live or both

-- Q14. How many movies released in each genre during March 2017 in the USA had more than 1,000 votes?
/* Output format:

+---------------+-------------------+
| genre			|	movie_count		|
+-------------------+----------------
|	thriller	|		105			|
|	.			|		.			|
|	.			|		.			|
+---------------+-------------------+ */
-- Type your code below:
SELECT 
    g.genre
    ,COUNT(DISTINCT m.id) movie_count
FROM movie m 
JOIN genre g ON m.id = g.movie_id
JOIN ratings r ON m.id = r.movie_id
				  AND r.total_votes > 1000
WHERE DATE_FORMAT(m.date_published,'%m/%Y') = '03/2017'
GROUP BY g.genre;

-- Lets try to analyse with a unique problem statement.
-- Q15. Find movies of each genre that start with the word ‘The’ and which have an average rating > 8?
/* Output format:
+---------------+-------------------+---------------------+
| title			|		avg_rating	|		genre	      |
+---------------+-------------------+---------------------+
| Theeran		|		8.3			|		Thriller	  |
|	.			|		.			|			.		  |
|	.			|		.			|			.		  |
|	.			|		.			|			.		  |
+---------------+-------------------+---------------------+*/
-- Type your code below:
SELECT
    m.title
    ,r.avg_rating 
    ,g.genre
FROM movie m 
JOIN genre g ON m.id = g.movie_id
JOIN ratings r ON m.id = r.movie_id
				  AND r.avg_rating > 8
WHERE UPPER(m.title) LIKE 'THE%';

-- You should also try your hand at median rating and check whether the ‘median rating’ column gives any significant insights.
-- Q16. Of the movies released between 1 April 2018 and 1 April 2019, how many were given a median rating of 8?
-- Type your code below:
SELECT COUNT(m.id) movie_count
FROM movie m 
JOIN ratings r ON m.id  = r.movie_id 
				  AND r.median_rating = 8
WHERE m.date_published BETWEEN STR_TO_DATE('20180401','%Y%m%d') AND STR_TO_DATE('20190401','%Y%m%d');

-- Once again, try to solve the problem given below.
-- Q17. Do German movies get more votes than Italian movies? 
-- Hint: Here you have to find the total number of votes for both German and Italian movies.
-- Type your code below:
SELECT
    SUM(CASE WHEN UPPER(m.country) LIKE '%GERMAN%' THEN r.total_votes END) german_total_votes 
    ,SUM(CASE WHEN UPPER(m.country) LIKE '%ITALY%' THEN r.total_votes END) italian_total_votes 
FROM movie m 
JOIN ratings r ON m.id = r.movie_id;

-- Answer is Yes

/* Now that you have analysed the movies, genres and ratings tables, let us now analyse another table, the names table. 
Let’s begin by searching for null values in the tables.*/

-- Segment 3:

-- Q18. Which columns in the names table have null values??
/*Hint: You can find null values for individual columns or follow below output format
+---------------+-------------------+---------------------+----------------------+
| name_nulls	|	height_nulls	|date_of_birth_nulls  |known_for_movies_nulls|
+---------------+-------------------+---------------------+----------------------+
|		0		|			123		|	       1234		  |	   12345	    	 |
+---------------+-------------------+---------------------+----------------------+*/
-- Type your code below:
SELECT
    COUNT(CASE WHEN name IS NULL THEN 1 END) name_nulls
    ,COUNT(CASE WHEN height IS NULL THEN 1 END) height_nulls
    ,COUNT(CASE WHEN date_of_birth IS NULL THEN 1 END) date_of_birth_nulls
    ,COUNT(CASE WHEN known_for_movies IS NULL THEN 1 END) known_for_movies_nulls
FROM names;
select * FROM names;
/* There are no Null value in the column 'name'.
The director is the most important person in a movie crew. 
Let’s find out the top three directors in the top three genres who can be hired by Bee Movies.*/

-- Q19. Who are the top three directors in the top three genres whose movies have an average rating > 8?
-- (Hint: The top three genres would have the most number of movies with an average rating > 8.)
/* Output format:

+---------------+-------------------+
| director_name	|	movie_count		|
+---------------+-------------------|
|James Mangold	|		4			|
|	.			|		.			|
|	.			|		.			|
+---------------+-------------------+ */
-- Type your code below:
SELECT
    a.director_name
    ,a.movie_count
FROM 
	(SELECT
	    n.id
	    ,MAX(n.name) director_name
	    ,COUNT(DISTINCT g.movie_id) movie_count
	    ,RANK() OVER (ORDER BY COUNT(DISTINCT g.movie_id) DESC) movie_count_rank
	FROM genre g
	JOIN
		(SELECT
		    g.genre
		    ,COUNT(r.movie_id) movie_count
		    ,RANK() OVER (ORDER BY COUNT(r.movie_id) DESC) genre_rank
		FROM genre g
		JOIN ratings r ON g.movie_id = r.movie_id
						  AND r.avg_rating > 8
		GROUP BY g.genre) g1 ON g.genre = g1.genre
								AND g1.genre_rank <= 3
	JOIN director_mapping d ON g.movie_id = d.movie_id
	JOIN names n ON d.name_id = n.id
	GROUP BY n.id) a
WHERE movie_count_rank <= 3;

/* James Mangold can be hired as the director for Bee's next project. Do you remeber his movies, 'Logan' and 'The Wolverine'. 
Now, let’s find out the top two actors.*/

-- Q20. Who are the top two actors whose movies have a median rating >= 8?
/* Output format:

+---------------+-------------------+
| actor_name	|	movie_count		|
+-------------------+----------------
|Christain Bale	|		10			|
|	.			|		.			|
+---------------+-------------------+ */
-- Type your code below:
SELECT
    a.name
    ,a.movie_count
FROM
	(SELECT
	    n.id
	    ,MAX(n.name) name
	    ,COUNT(m.id) movie_count
	    ,RANK() OVER (ORDER BY COUNT(m.id) DESC) movie_count_rank
	FROM movie m 
	JOIN ratings r ON m.id = r.movie_id
					  AND r.median_rating >= 8
	JOIN role_mapping rm ON m.id = rm.movie_id
	JOIN names n ON rm.name_id = n.id
	GROUP BY n.id) a
WHERE a.movie_count_rank <= 2;

/* Have you find your favourite actor 'Mohanlal' in the list. If no, please check your code again. 
Bee Movies plans to partner with other global production houses. 
Let’s find out the top three production houses in the world.*/

-- Q21. Which are the top three production houses based on the number of votes received by their movies?
/* Output format:
+------------------+--------------------+---------------------+
|production_company|vote_count			|		prod_comp_rank|
+------------------+--------------------+---------------------+
| The Archers		|		830			|		1	  		  |
|	.				|		.			|			.		  |
|	.				|		.			|			.		  |
+-------------------+-------------------+---------------------+*/
-- Type your code below:
SELECT
    a.production_company
    ,a.vote_count
    ,a.prod_comp_rank
FROM
	(SELECT
	    m.production_company 
	    ,SUM(r.total_votes) vote_count
	    ,RANK() OVER (ORDER BY SUM(r.total_votes) DESC) prod_comp_rank
	FROM movie m 
	JOIN ratings r ON m.id = r.movie_id 
	GROUP BY m.production_company) a
WHERE a.prod_comp_rank <= 3;

/*Yes Marvel Studios rules the movie world.
So, these are the top three production houses based on the number of votes received by the movies they have produced.

Since Bee Movies is based out of Mumbai, India also wants to woo its local audience. 
Bee Movies also wants to hire a few Indian actors for its upcoming project to give a regional feel. 
Let’s find who these actors could be.*/

-- Q22. Rank actors with movies released in India based on their average ratings. Which actor is at the top of the list?
-- Note: The actor should have acted in at least five Indian movies. 
-- (Hint: You should use the weighted average based on votes. If the ratings clash, then the total number of votes should act as the tie breaker.)

/* Output format:
+---------------+-------------------+---------------------+----------------------+-----------------+
| actor_name	|	total_votes		|	movie_count		  |	actor_avg_rating 	 |actor_rank	   |
+---------------+-------------------+---------------------+----------------------+-----------------+
|	Yogi Babu	|			3455	|	       11		  |	   8.42	    		 |		1	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
+---------------+-------------------+---------------------+----------------------+-----------------+*/
-- Type your code below:
SELECT
    a.name
    ,a.total_votes
    ,a.movie_count
    ,a.actor_avg_rating
    ,a.actor_rank
FROM
	(SELECT
	    n.id
	    ,MAX(n.name) name
	    ,SUM(r.total_votes) total_votes
	    ,COUNT(DISTINCT m.id) movie_count
	    ,ROUND(SUM(r.avg_rating * r.total_votes) / SUM(r.total_votes), 2) AS actor_avg_rating
	    ,RANK() OVER (
	        ORDER BY 
	            ROUND(SUM(r.avg_rating * r.total_votes) * 1.0 / SUM(r.total_votes), 2) DESC,
	            SUM(r.total_votes) DESC
	    ) AS actor_rank
	FROM movie m
	JOIN ratings r ON m.id = r.movie_id
	JOIN role_mapping rm ON m.id = rm.movie_id 
							AND rm.category = 'actor'
	JOIN names n ON rm.name_id = n.id
	WHERE UPPER(m.country) LIKE '%INDIA%'
	GROUP BY n.id
	HAVING COUNT(DISTINCT m.id) >= 5) a
-- WHERE a.actor_rank = 1
;

-- Top actor is Vijay Sethupathi

-- Q23.Find out the top five actresses in Hindi movies released in India based on their average ratings? 
-- Note: The actresses should have acted in at least three Indian movies. 
-- (Hint: You should use the weighted average based on votes. If the ratings clash, then the total number of votes should act as the tie breaker.)
/* Output format:
+---------------+-------------------+---------------------+----------------------+-----------------+
| actress_name	|	total_votes		|	movie_count		  |	actress_avg_rating 	 |actress_rank	   |
+---------------+-------------------+---------------------+----------------------+-----------------+
|	Tabu		|			3455	|	       11		  |	   8.42	    		 |		1	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
+---------------+-------------------+---------------------+----------------------+-----------------+*/
-- Type your code below:
SELECT
    a.name
    ,a.total_votes
    ,a.movie_count
    ,a.actress_avg_rating
    ,a.actress_rank
FROM
	(SELECT
		n.id
	    ,MAX(n.name) name
		,SUM(r.total_votes) total_votes
		,COUNT(DISTINCT m.id) movie_count
		,ROUND(SUM(r.avg_rating * r.total_votes) / SUM(r.total_votes), 2) AS actress_avg_rating
		,RANK() OVER (
		    ORDER BY 
		        ROUND(SUM(r.avg_rating * r.total_votes) * 1.0 / SUM(r.total_votes), 2) DESC,
		        SUM(r.total_votes) DESC
		) AS actress_rank
	FROM movie m 
	JOIN ratings r ON m.id = r.movie_id
	JOIN role_mapping rm ON m.id = rm.movie_id 
								AND rm.category = 'actress'
	JOIN names n ON rm.name_id = n.id
	WHERE UPPER(m.country) LIKE '%INDIA%'
	AND UPPER(m.languages) LIKE '%HINDI%'
	GROUP BY n.id
	HAVING COUNT(DISTINCT m.id) >= 3) a
-- WHERE a.actor_rank = 1
;

/* Taapsee Pannu tops with average rating 7.74. 
Now let us divide all the thriller movies in the following categories and find out their numbers.*/


/* Q24. Select thriller movies as per avg rating and classify them in the following category: 

			Rating > 8: Superhit movies
			Rating between 7 and 8: Hit movies
			Rating between 5 and 7: One-time-watch movies
			Rating < 5: Flop movies
--------------------------------------------------------------------------------------------*/
-- Type your code below:
SELECT
    m.title
    ,CASE WHEN r.avg_rating > 8 THEN 'Superhit movies'
    	  WHEN r.avg_rating BETWEEN 7 AND 8 THEN 'Hit movies'
    	  WHEN r.avg_rating BETWEEN 5 AND 7 THEN 'One-time-watch movies'
    	  WHEN r.avg_rating < 5 THEN 'Flop movies' END category
FROM movie m 
JOIN ratings r ON m.id = r.movie_id
JOIN genre g ON m.id = g.movie_id
				AND g.genre = 'Thriller';

/* Until now, you have analysed various tables of the data set. 
Now, you will perform some tasks that will give you a broader understanding of the data in this segment.*/

-- Segment 4:

-- Q25. What is the genre-wise running total and moving average of the average movie duration? 
-- (Note: You need to show the output table in the question.) 
/* Output format:
+---------------+-------------------+---------------------+----------------------+
| genre			|	avg_duration	|running_total_duration|moving_avg_duration  |
+---------------+-------------------+---------------------+----------------------+
|	comdy		|			145		|	       106.2	  |	   128.42	    	 |
|		.		|			.		|	       .		  |	   .	    		 |
|		.		|			.		|	       .		  |	   .	    		 |
|		.		|			.		|	       .		  |	   .	    		 |
+---------------+-------------------+---------------------+----------------------+*/
-- Type your code below:
SELECT
    a.genre
    ,a.avg_duration
    ,SUM(a.avg_duration) OVER (ORDER BY a.avg_duration) running_total_duration
    ,ROUND(AVG(a.avg_duration) OVER (ORDER BY a.avg_duration ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),2) moving_avg_duration
FROM
	(SELECT
	    g.genre 
	    ,ROUND(AVG(m.duration),2) avg_duration
	FROM movie m 
	JOIN genre g ON m.id = g.movie_id
	GROUP BY g.genre) a;

-- Round is good to have and not a must have; Same thing applies to sorting

-- Let us find top 5 movies of each year with top 3 genres.

-- Q26. Which are the five highest-grossing movies of each year that belong to the top three genres? 
-- (Note: The top 3 genres would have the most number of movies.)

/* Output format:
+---------------+-------------------+---------------------+----------------------+-----------------+
| genre			|	year			|	movie_name		  |worldwide_gross_income|movie_rank	   |
+---------------+-------------------+---------------------+----------------------+-----------------+
|	comedy		|			2017	|	       indian	  |	   $103244842	     |		1	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
+---------------+-------------------+---------------------+----------------------+-----------------+*/
-- Type your code below:

-- Top 3 Genres based on most number of movies
WITH top_genre AS (
    SELECT
        g.genre 
        ,g.movie_id
    FROM genre g
	JOIN 
	    (SELECT
	        genre
	        ,COUNT(movie_id) movie_count
	        ,RANK() OVER (ORDER BY COUNT(movie_id) DESC) movie_count_rank
	    FROM genre
	    GROUP BY genre) g1 ON g.genre = g1.genre
	    					  AND g1.movie_count_rank <= 3
)
SELECT
    a.genre 
    ,a.year
    ,a.title movie_name
    ,a.worlwide_gross_income
    ,a.movie_rank
FROM 
	(SELECT
	    g.genre 
	    ,m.year
	    ,m.title
	    ,SUM(CAST(TRIM(REPLACE(REPLACE(worlwide_gross_income,'$',''),'INR','')) AS UNSIGNED)) worlwide_gross_income
	    ,RANK()
	    OVER (
	        PARTITION BY m.year, g.genre
	        ORDER BY SUM(CAST(TRIM(REPLACE(REPLACE(worlwide_gross_income,'$',''),'INR','')) AS UNSIGNED)) DESC
	    ) movie_rank
	FROM movie m 
	JOIN top_genre g ON m.id = g.movie_id
	GROUP BY
	    g.genre 
	    ,m.year
	    ,m.title) a
WHERE a.movie_rank <= 5;

-- Finally, let’s find out the names of the top two production houses that have produced the highest number of hits among multilingual movies.
-- Q27.  Which are the top two production houses that have produced the highest number of hits (median rating >= 8) among multilingual movies?
/* Output format:
+-------------------+-------------------+---------------------+
|production_company |movie_count		|		prod_comp_rank|
+-------------------+-------------------+---------------------+
| The Archers		|		830			|		1	  		  |
|	.				|		.			|			.		  |
|	.				|		.			|			.		  |
+-------------------+-------------------+---------------------+*/
-- Type your code below:
SELECT
    a.production_company
    ,a.movie_count
    ,a.prod_comp_rank
FROM
	(SELECT
	    m.production_company
	    ,COUNT(m.id) movie_count
	    ,RANK() OVER (ORDER BY COUNT(m.id) DESC) prod_comp_rank
	FROM movie m
	JOIN ratings r ON m.id = r.movie_id
				      AND r.median_rating >= 8
	WHERE POSITION(',' IN m.languages) > 0
	AND m.production_company IS NOT NULL
	GROUP BY m.production_company) a
WHERE a.prod_comp_rank <= 2;

-- Multilingual is the important piece in the above question. It was created using POSITION(',' IN languages)>0 logic
-- If there is a comma, that means the movie is of more than one language


-- Q28. Who are the top 3 actresses based on number of Super Hit movies (average rating >8) in drama genre?
/* Output format:
+---------------+-------------------+---------------------+----------------------+-----------------+
| actress_name	|	total_votes		|	movie_count		  |actress_avg_rating	 |actress_rank	   |
+---------------+-------------------+---------------------+----------------------+-----------------+
|	Laura Dern	|			1016	|	       1		  |	   9.60			     |		1	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
|		.		|			.		|	       .		  |	   .	    		 |		.	       |
+---------------+-------------------+---------------------+----------------------+-----------------+*/
-- Type your code below:
SELECT
    a.actress_name 
    ,a.total_votes 
    ,a.movie_count 
    ,a.actress_avg_rating 
    ,a.actress_rank 
FROM
	(SELECT
	    n.id
	    ,MAX(n.name) actress_name
		,SUM(r.total_votes) total_votes
	    ,COUNT(m.id) movie_count
	    ,AVG(r.avg_rating) actress_avg_rating
	    ,RANK() OVER (ORDER BY COUNT(m.id) DESC) actress_rank
	FROM movie m 
	JOIN ratings r ON m.id = r.movie_id
					  AND r.avg_rating > 8
	JOIN role_mapping rm ON m.id = rm.movie_id
							AND rm.category = 'actress'
	JOIN names n ON rm.name_id = n.id
	GROUP BY n.id) a
WHERE a.actress_rank <= 3;

/* Q29. Get the following details for top 9 directors (based on number of movies)
Director id
Name
Number of movies
Average inter movie duration in days
Average movie ratings
Total votes
Min rating
Max rating
total movie durations

Format:
+---------------+-------------------+---------------------+----------------------+--------------+--------------+------------+------------+----------------+
| director_id	|	director_name	|	number_of_movies  |	avg_inter_movie_days |	avg_rating	| total_votes  | min_rating	| max_rating | total_duration |
+---------------+-------------------+---------------------+----------------------+--------------+--------------+------------+------------+----------------+
|nm1777967		|	A.L. Vijay		|			5		  |	       177			 |	   5.65	    |	1754	   |	3.7		|	6.9		 |		613		  |
|	.			|		.			|			.		  |	       .			 |	   .	    |	.		   |	.		|	.		 |		.		  |
|	.			|		.			|			.		  |	       .			 |	   .	    |	.		   |	.		|	.		 |		.		  |
|	.			|		.			|			.		  |	       .			 |	   .	    |	.		   |	.		|	.		 |		.		  |
|	.			|		.			|			.		  |	       .			 |	   .	    |	.		   |	.		|	.		 |		.		  |
|	.			|		.			|			.		  |	       .			 |	   .	    |	.		   |	.		|	.		 |		.		  |
|	.			|		.			|			.		  |	       .			 |	   .	    |	.		   |	.		|	.		 |		.		  |
|	.			|		.			|			.		  |	       .			 |	   .	    |	.		   |	.		|	.		 |		.		  |
|	.			|		.			|			.		  |	       .			 |	   .	    |	.		   |	.		|	.		 |		.		  |
+---------------+-------------------+---------------------+----------------------+--------------+--------------+------------+------------+----------------+

--------------------------------------------------------------------------------------------*/
-- Type you code below:
WITH T1 AS(
	SELECT
	    n.id director_id
	    ,n.name 
	    ,m.id movie_id
	    ,m.title
	    ,m.date_published
	    ,COALESCE(LEAD(m.date_published) OVER (PARTITION BY n.id ORDER BY m.date_published), m.date_published) next_date_published
	    ,r.avg_rating
	    ,r.total_votes 
	    ,m.duration
	FROM movie m
	JOIN ratings r ON m.id = r.movie_id
	JOIN director_mapping dm ON m.id = dm.movie_id 
	JOIN names n ON dm.name_id = n.id
	ORDER BY n.id, m.date_published
)
SELECT
    a.director_id
    ,MAX(a.name) director_name
    ,COUNT(a.movie_id) number_of_movies
    ,AVG(DATEDIFF(a.next_date_published, a.date_published)) avg_inter_movie_days
    ,AVG(a.avg_rating) avg_rating
    ,SUM(a.total_votes) total_votes
    ,MIN(a.avg_rating) min_rating
    ,MAX(a.avg_rating) max_rating
    ,SUM(a.duration) total_duration
FROM T1 a
GROUP BY a.director_id;
