import networkx as nx
import pymysql
import sys
import matplotlib.pyplot as plt 


#######################AUTHS & CONNECT###############################
connection = pymysql.connect(
    host='localhost',
    user='megadados',
    password='megadados2019',
    database='projetoredes',
    autocommit=True)
# db_connection = partial(run_db_query, connection)
#####################################################################


args = sys.argv
write = False
if '-w' in args:
    write = true
   
cursor = connection.cursor()
q = ('SELECT nome, popularidade FROM artistas')
cursor.execute(q)
result = cursor.fetchall()
cursor.close()

cursor = connection.cursor()
q = ('SELECT origem, destino FROM edges')
cursor.execute(q)
result_edge = cursor.fetchall()
cursor.close()

cursor = connection.cursor()
q = ('SELECT * FROM musicas')
cursor.execute(q)
all_musics = cursor.fetchall()
cursor.close()
def get_music_id(nome_musica):
    cursor = connection.cursor()
    q = ('SELECT id_musicas FROM musicas WHERE nome=%s')
    cursor.execute(q,(nome_musica))
    music_id = cursor.fetchone()
    cursor.close()
    return music_id
    
def get_music_playlists(id_musica):
    cursor = connection.cursor()
    q = ('SELECT playlist.nome FROM playlist_musicas, INNER JOIN playlist using(id_playlist) WHERE playlist_musicas.id_musica=%s')
    cursor.execute(q,(id_musica))
    playlists_nomes = cursor.fetchall()
    cursor.close()
    return playlists_nomes
def get_playlists():
    cursor = connection.cursor()
    q = ('SELECT nome FROM playlist')
    cursor.execute(q)
    playlists_nomes = cursor.fetchall()
    cursor.close()
    return playlists_nomes
def get_musics_of_playlist(playlist_name):
    cursor = connection.cursor()
    q = ('SELECT musicas.nome FROM playlist , INNER JOIN playlist_musicas using(id_playlist), INNER JOIN musicas using(id_musica) WHERE playlist.nome=%s')
    cursor.execute(q,(playlist_name))
    musicas_da_playlist = cursor.fetchall()
    cursor.close()
    return musicas_da_playlist





infos = {}
for i in result:
    infos[i[0]] = i[1]


edges = []
for i in result_edge:
    edges.append(i)


graph = nx.Graph()
for artist in infos:
    graph.add_node(artist)

graph.add_edges_from(edges)

if write:
    f = open('rock.gml', 'w')

    f.write("\n".join(nx.generate_gml(graph)))

    f.close()

b = nx.betweenness_centrality(graph)
# b = nx.closeness_centrality(graph)


y = []
x = []
for artist in infos:
    between = b[artist]
    pop = infos[artist]
    
    if (between != 0):
        x.append(between)
        y.append(pop)


print(x)
print(y)

plt.scatter(x ,y)

plt.show()
