import networkx as nx
import pymysql
import sys
import matplotlib.pyplot as plt


#######################AUTHS & CONNECT###############################
connection = pymysql.connect(
    host='172.17.0.2',
    user='root',
    password='123',
    database='projetoredes',
    autocommit=True)
# db_connection = partial(run_db_query, connection)
#####################################################################


args = sys.argv
write = False
if '-w' in args:
    write = True

# cursor = connection.cursor()
# q = ('SELECT nome, popularidade FROM artistas')
# cursor.execute(q)
# result = cursor.fetchall()
# cursor.close()

# cursor = connection.cursor()
# q = ('SELECT origem, destino FROM edges')
# cursor.execute(q)
# result_edge = cursor.fetchall()
# cursor.close()

cursor = connection.cursor()
q = ('SELECT * FROM musicas')
cursor.execute(q)
all_musics = cursor.fetchall()
cursor.close()


def get_music_id(nome_musica):
    cursor = connection.cursor()
    q = ('SELECT id_musicas FROM musicas WHERE nome=%s')
    cursor.execute(q, (nome_musica))
    music_id = cursor.fetchone()
    cursor.close()
    return music_id


def get_music_playlists(id_musica):
    cursor = connection.cursor()
    q = ('SELECT playlist.nome FROM playlist_musicas, INNER JOIN playlist using(id_playlist) WHERE playlist_musicas.id_musica=%s')
    cursor.execute(q, (id_musica))
    playlists_nomes = cursor.fetchall()
    cursor.close()
    return playlists_nomes


def get_playlists():
    cursor = connection.cursor()
    q = ('SELECT nome FROM playlist')
    cursor.execute(q)
    playlists_nomes = cursor.fetchall()
    playlists_nomes = [pls[0] for pls in playlists_nomes]
    cursor.close()
    return playlists_nomes


def get_musics_of_playlist(playlist_name):
    cursor = connection.cursor()
    q = ('SELECT musicas.nome FROM playlist , INNER JOIN playlist_musicas using(id_playlist), INNER JOIN musicas using(id_musica) WHERE playlist.nome=%s')
    cursor.execute(q, (playlist_name))
    musicas_da_playlist = cursor.fetchall()
    cursor.close()
    return musicas_da_playlist


def get_all_songs():
    cursor = connection.cursor()
    q = ('SELECT nome FROM musicas')
    cursor.execute(q)
    musicas = cursor.fetchall()
    musicas = [musica[0] for musica in musicas]
    cursor.close()
    return musicas

def get_all_relations():
    cursor = connection.cursor()
    q = ('''SELECT 
                musicas.nome, playlist.nome 
            FROM 
                musicas, playlist, playlist_musicas
            WHERE
                playlist_musicas.id_musicas = musicas.id_musicas
                AND playlist_musicas.id_playlist = playlist.id_playlist
                
                
    ''')
    cursor.execute(q)
    musicas = cursor.fetchall()
    musicas = [(musica[0], musica[1]) for musica in musicas]
    cursor.close()
    return musicas


musicas = get_all_songs()[:100]
# print(musicas)

pls = get_playlists()[:100]
# print(pls)

relations = get_all_relations()[:100]
# print(relations)

# https://stackoverflow.com/questions/35472402/how-do-display-bipartite-graphs-with-python-networkx-package
B = nx.Graph()
B.add_nodes_from(musicas, bipartite=0)  # Add the node attribute "bipartite"
B.add_nodes_from(pls, bipartite=1)
B.add_edges_from(relations)



print(nx.hits(B, max_iter=50000))

if write:
    f = open('rock.gml', 'w')

    f.write("\n".join(nx.generate_gml(B)))

    f.close()
