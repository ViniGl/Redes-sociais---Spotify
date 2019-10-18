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
