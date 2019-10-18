import networkx as nx
import pymysql


#######################AUTHS & CONNECT###############################
connection = pymysql.connect(
    host='172.17.0.2',
    user='root',
    password='123',
    database='projetoredes',
    autocommit=True)
# db_connection = partial(run_db_query, connection)
#####################################################################

   
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

print("\n".join(nx.generate_gml(graph)))
b = nx.betweenness_centrality(graph)
print(b)
