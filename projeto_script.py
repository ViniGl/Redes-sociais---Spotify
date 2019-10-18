import sys
import os
import networkx as nx
from functools import partial
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import pymysql
import requests

# Go to the Dashboard at developer.spotify.com and
# create an app. You will receive an id and secret.
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

# Go to the Spotify webplayer and go the artist
# page. The id should be at the address bar.
EGO_USERNAME = r'6mdiAmATAx73kdxrNrnlao'  # Iron maiden ID

OUTPUT_PATH = r'spotify'

VERBOSE = False

def run_db_query(connection, query, args=None):
    with connection.cursor() as cursor:
        print('Executando query:')
        cursor.execute(query, args)
        for result in cursor:
            print(result)


def get_name(api, ego_username):
    '''Get artist infos. \n
       Input : api, artist ego \n
       Output : artist infos. \n
       REF : Spotify Docs.
    '''
    artist = api.artist(ego_username)
    return artist


def get_related_artists(api, ego_username, connection, save):
    '''Get related artists. \n
       Input : api, artist ego \n
       Output : artist infos. \n
       REF : Spotify Docs.
    '''
    cursor = connection.cursor()

    related = api.artist_related_artists(ego_username)
    artists = related['artists']
    
    # print(related)
    if save:
        for artist in artists:
            try:
                artist_id = artist['id']
                artist_nome = artist['name']
                artist_popularidade = artist['popularity']
                if VERBOSE:
                    print("Artista/Banda: {} , id: {}".format(artist_nome, artist_id))
                q = ('INSERT INTO artistas (id_artistas, nome, popularidade) VALUES (%s, %s, %s)')
                cursor.execute(q, (artist_id, artist_nome, artist_popularidade))
            except:
                pass
        cursor.close()
    return [artist for artist in artists]


def get_top_tracks(api, ego_username):
    '''Get artist Top Tracks. \n
       Input : api, artist ego \n
       Output : artist infos. \n
       REF : Spotify Docs.
    '''
    top_tracks = api.artist_top_tracks(ego_username['id'])
    return top_tracks


def artist_filter(artist_info):
    artist_name = artist_info['name']
    artist_popularity = artist_info['popularity']
    artist_id = artist_info['id']
    return {'artist_name': artist_name, 'artist_popularity': artist_popularity, 'artist_id': artist_id}


def debug_print(infos, filtered, select):
    if select == 0:
        print('''
Artista/Banda: {}
Popularidade : {}
Id : {}
'''.format(infos['artist_name'], infos['artist_popularity'], infos['artist_id']))

    else:
        print("Artista: {} // Popularidade: {} ".format(infos['name'], infos['popularity']))
    
    for top_filtered in filtered:
        # pass
        print('''\
    Id: {} // Titulo: {} // Popularidade: {}
    Dancabilidade: {} // Energia: {}
        '''.format(top_filtered['song_id'], top_filtered['song_name'], top_filtered['song_popularity'], top_filtered['danceability'], top_filtered['energy']))


def track_analysis(api, song_id):
    data = api.audio_features(song_id)[0]
    danceability = data['danceability']
    energy = data['energy']
    return (danceability, energy)


def top_tracks_filter(api, top_tracks):

    songs = []

    for song in top_tracks['tracks']:
        collected = {}
        collected['song_name'] = song['name']
        collected['song_id'] = song['id']
        collected['song_duration'] = song['duration_ms']
        collected['song_popularity'] = song['popularity']

        data = track_analysis(api, song['id'])

        collected['danceability'] = data[0]
        collected['energy'] = data[1]
        songs.append(collected)

    return songs

def get_categories(api):
    categories = api.categories()
    cats = {}
    for i in categories['categories']['items']:
        cats[i['name']] = i['id']
    return cats

def get_playlists(api, category_id):
    playlist = api.category_playlists(category_id)

    all_playlists = {}
    for i in playlist['playlists']['items']:
        pl_name = i['name']
        all_playlists[pl_name] = i['tracks']

    return all_playlists


def playlist_song_relation(api, playlists):
    
    songs_playlist = {}

    for pl in playlists:

        a = requests.get(playlists[pl]['href'], headers={"Accept": "application/json","Content-Type": "application/json", "Authorization": "Bearer {}".format(ACCESS_TOKEN)})

        tracks_infos = []
        for song in a.json()['items']:
            song_name = song['track']['name']
            song_artist = song['track']['album']['artists'][0]['name']
            song_popularity = song['track']['popularity']

            tracks_infos.append((song_name, song_popularity))

        songs_playlist[pl] = tracks_infos
    return songs_playlist

def main():
    args = sys.argv
    if "-v" in args:
        VERBOSE = True

    if '--save' in args:
        save = True
    else:
        save = False

    #######################AUTHS & CONNECT###############################
    connection = pymysql.connect(
        host='172.17.0.2',
        user='root',
        password='123',
        database='projetoredes',
        autocommit=True)
    # db_connection = partial(run_db_query, connection)

    client_credentials_manager = SpotifyClientCredentials(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    api = Spotify(client_credentials_manager=client_credentials_manager)
    #####################################################################
    all_categories = get_categories(api)

    category_1 = "Rock"
    # category_2 = "Sertanejo"


    playlists_rock = get_playlists(api, all_categories[category_1])
    # playlists_sertanejo = get_playlists(api, all_categories[category_2])
    # print(playlists_rock)

    two_way = playlist_song_relation(api, playlists_rock)



    for i in two_way:
        for u in two_way[i]:
            print(u)



    ######################################################################
    # artist_info = get_name(api, EGO_USERNAME)

    # infos = artist_filter(artist_info)  # Get some filtered artist infos

    # if save:
    #     cursor = connection.cursor()
    #     q = ('INSERT INTO artistas (id_artistas, nome, popularidade) VALUES (%s, %s, %s)')
    #     cursor.execute(q, (infos['artist_id'], infos['artist_name'], infos['artist_popularity']))
    #     cursor.close()

    # tops = get_top_tracks(api, artist_info)

    # filtered = top_tracks_filter(api, tops)  # Get top tracks infos
    # print(VERBOSE)
    # if VERBOSE:
    #     debug_print(infos, filtered, 0)

    # related = get_related_artists(api, EGO_USERNAME, connection, save)

    # print(related)
    ##################Artistas relacionados##############################
    
    # count = 0
    # limit = 100

    # ids = []

    # ids.append(artist_info)
        
    # while count <= limit :
        
    #     if save:
    #         cursor = connection.cursor()
    #         q = ('SELECT nome FROM artistas')
    #         cursor.execute(q)
    #         result = cursor.fetchall()
    #         cursor.close()

        
    #     current = ids[0]
    #     print(current['name'])
    #     related = get_related_artists(api, current['id'], connection, save)
    #     for related_artist in related:
    #         if save:
    #             cursor = connection.cursor()
    #             q = ('INSERT INTO edges (origem, destino) VALUES (%s, %s)')
    #             cursor.execute(q, (current['name'], related_artist['name']))
    #             cursor.close()
    #         # print(related_artist)
    #         if (related_artist['name'] not in result):
    #             ids.append(related_artist)

    
    #     ids.pop(0)
    #     count += 1
    #####################################################################
    
if __name__ == '__main__':
    main()
