import os 
import sqlite3 as sql
import pandas as pd
import matplotlib.pyplot as plt
import funciones as fn
from PIL import Image
import preprocesamientos as pre
import numpy as np

### para ver y cambiar directorio de trabajo
os.getcwd()
#os.chdir('C:/Users/Asus/Documents/Analitica 3 Caso Marketing')

# Diseño de la solución
i=Image.open('diseño_solución.png','r') # imagen en color 
i.show()

###### para ejecutar sql y conectarse a bd ###
conn=sql.connect('db_movies')
cur=conn.cursor()

### para verificar las tablas que hay disponibles
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cur.fetchall()) # movies, ratings

############ cargar tablas ####
movies = pd.read_sql("SELECT * FROM movies; ",conn)
ratings = pd.read_sql("SELECT * FROM ratings; ",conn)

### Identificar campos de cruce y verificar que estén en mismo formato ####
### verificar duplicados

movies.info() # Se observa que tiene 3 campos, el id de la película, el título y el género
movies.head() # Se identifica que los años de lanzamiento de la película estaban indexados al título
movies.duplicated().sum() #No se tienen duplicados 

ratings.info() # Se observa que tiene 4 campos, userid, movieId, rating y timestamp
ratings.head() # Se debe cambiar el formato del timestamp a fecha
ratings.duplicated().sum() #No se tienen duplicados

movies["genres"].unique() #Separar los géneros que estan indicados con |
ratings["rating"].unique() #Los valores están comprendidos entre 0 y 5. La calificación más baja es de 0.5
ratings["rating"].value_counts()

##### Descripción base de ratings

###calcular la distribución de ratings
dr=pd.read_sql(""" select 
                          rating, 
                          count(*) as conteo 
                          from ratings
                          group by rating
                          order by conteo asc""", conn)                          

# Graficar las ventas por categoría de productos
dr.plot(kind='bar', x='rating', y='conteo', legend=None)
plt.title('Cantidad de usuarios por rating')
plt.xlabel('Rating')
plt.ylabel('Usuarios')
plt.show()            
# La mayoría de usuarios considera que las películas son regulares o buenas

### calcular cada usuario cuátos películas calificó
rating_users=pd.read_sql(''' select userId,
                         count(*) as cnt_rat
                         from ratings
                         group by userId
                         order by cnt_rat asc
                         ''',conn )

# Graficar histograma de frecuencia de numero de calificaciones por usuario
plt.hist(rating_users, bins=15)
plt.title('Hist frecuencia de número de calificaciones por usuario')
plt.xlabel('Calificaciones')
plt.ylabel('Usuarios')
plt.show() #La mayoría de usuarios decidieron no calificar las películas. 

rating_users.describe()
#El valor máximo de películas calificadas por un usuario es demasiado grande, ya que dista en gran proporción de la media

#### filtrar usuarios con más de 20 películas calificadas (para tener calificaion confiable) y los que tienen mas de 1200 porque pueden ser no razonables
rating_users2=pd.read_sql(''' select userId,
                         count(*) as cnt_rat
                         from ratings
                         group by userId
                         having cnt_rat >=20 and cnt_rat <=1200
                         order by cnt_rat asc
                         ''',conn )

### ver distribucion despues de filtros,ahora se ve mas razonables
rating_users2.describe()

### graficar distribucion despues de filtrar datos
plt.hist(rating_users2, bins=15)
plt.title('Hist frecuencia de número de calificaciones por usuario')
plt.xlabel('Calificaciones')
plt.ylabel('Usuarios')
plt.show() #La minoría de usuarios ha calificado 

#### verificar cuantas calificaciones tiene cada película
rating_movies=pd.read_sql(''' select movieId,
                         count(*) as cnt_rat
                         from ratings
                         group by movieId
                         order by cnt_rat desc
                         ''',conn )

### analizar distribucion de calificaciones por película
rating_movies.describe()

### graficar distribucion
plt.hist(rating_movies, bins=15)
plt.title('Hist frecuencia de número de calificaciones por película')
plt.xlabel('Calificaciones')
plt.ylabel('Películas')
plt.show()
 
#### Filtrar películas que tengan más de 5 calificaciones
rating_movies2=pd.read_sql(''' select movieId,
                         count(*) as cnt_rat
                         from ratings
                         group by movieId
                         having cnt_rat>=5
                         order by cnt_rat desc
                         ''',conn )

rating_movies2.describe()

### graficar distribucion despues de filtrar datos
plt.hist(rating_movies2, bins=15)
plt.title('Hist frecuencia de número de calificaciones por película')
plt.xlabel('Calificaciones')
plt.ylabel('Películas')
plt.show() # Quedan 450 películas luego del filtro

########### Cargue de funciones de preprocesamiento ###########
pre.timestamp(ratings)
pre.split_year(movies)
movies=pre.split__gender(movies)

# Guardar tablas en base de datos
movies.to_sql('movies2', conn, if_exists='replace')
ratings.to_sql('ratings2', conn, if_exists='replace')

### Preprocesamiento en sql
fn.ejecutar_sql('preprocesamientos.sql', cur)

full = pd.read_sql("SELECT * FROM full_ratings; ",conn)
pre.escalar(full)

# Guardar tabla escalada en base de datos
full.to_sql('full', conn, if_exists='replace')

### para verificar la tabla
full.info() 
full.duplicated().sum() #No existen duplicados

####  10 películas peor calificadas
consulta=pd.read_sql("""select Title, 
            avg(rating) as avg_rat,
            count(*) as view
            from full
            group by title
            order by avg_rat asc
            limit 10
            
            """, conn)
        
print('Las películas con peor calificación son:', np.array(consulta['title']))


#### Cantidad de vistas por género

sumgen = pd.read_sql("""select 
                        sum(Action) as Action,
                        sum(Adventure) as Adventure,
                        sum(Animation) as Animation, 
                        sum(Children) as Children, 
                        sum(Comedy) as Comedy, 
                        sum(Crime) as Crime, 
                        sum(Documentary) as Documentary, 
                        sum(Drama) as Drama,
                        sum(Fantasy) as Fantasy, 
                        sum(Film_Noir) as Film_Noir, 
                        sum(Horror) as Horror, 
                        sum(IMAX) as IMAX, 
                        sum(Musical) as Musical, 
                        sum(Mystery) as Mystery,
                        sum(Romance) as Romance, 
                        sum(Sci_Fi) as Sci_Fi, 
                        sum(Thriller) as Thriller, 
                        sum(War) as War, 
                        sum(Western) as Western,
                        sum(no_genres_listed) as no_genres_listed
                    from full; """, conn)
                    
sumgen = sumgen.T.reset_index().rename(columns={'index': 'genero', 0: 'num_peliculas'}).sort_values(by='num_peliculas', ascending=False)
 
# Crear la gráfica de barras
plt.bar(sumgen['genero'], sumgen['num_peliculas'])
plt.title('Número de visualizaciones por género')
plt.xlabel('Género')
plt.ylabel('Visualizaciones')
plt.xticks(rotation=60)
plt.show()

# Rating promedio a lo largo del tiempo
serie = pd.read_sql("""select strftime('%Y', timestamp) as year, avg(rating) as avg_rating 
                    from ratings2 
                    group by year 
                    order by year asc
                """, conn)

# Crear la gráfica de serie de tiempo
plt.plot(serie['year'], serie['avg_rating'])
plt.title('Rating promedio a lo largo del tiempo')
plt.xlabel('Fecha')
plt.ylabel('Rating promedio')
plt.xticks(rotation=60)
plt.show() 


# Visualizaciones a lo largo del tiempo
serie = pd.read_sql("""select strftime('%Y', timestamp) as year, count(*) as views 
                    from full 
                    group by year 
                    order by year asc
                """, conn)

# Crear la gráfica de serie de tiempo
plt.plot(serie['year'], serie['views'])
plt.title('Visualizaciones a lo largo del tiempo')
plt.xlabel('Fecha')
plt.ylabel('Visualizaciones')
plt.xticks(rotation=60)
plt.show()              
     
              
##### Recomendaciones Basadas en Popularidad ######

#### 10 peliculas mejores calificadas ###
consulta1=pd.read_sql("""select Title, 
            avg(rating) as avg_rat,
            count(*) as view
            from full
            group by title
            order by avg_rat desc
            limit 10
            
            """, conn)
        
print('Las películas con mejor calificación son:', np.array(consulta1['title']))

#### 10 peliculas más vistas ###
consulta2=pd.read_sql("""select title, 
            avg(rating) as avg_rat,
            count(*) as view
            from full
            group by title
            order by view desc
            limit 10
            """, conn)

print('Las películas con mejor calificación son:', np.array(consulta2['title']))

#### Las peliculas mejor calificadas en cada año de publicación ###
consulta3=pd.read_sql(""" with t1 as  (select year, title, 
                              avg(rating) as avg_rat, 
                              count(*) as view,
                              row_number() 
                              over (partition by year order by avg(rating) desc) as rn
                              from full_ratings
                              group by year, title)
                          select *  from t1
                          where rn = 1
                          order by year desc, avg_rat desc
                          """, conn)

consulta3=pd.DataFrame(data=consulta3)
print(consulta3.iloc[:,:2])