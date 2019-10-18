import sys
import os
import networkx as nx
from functools import partial
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import pymysql

# Go to the Dashboard at developer.spotify.com and
# create an app. You will receive an id and secret.
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

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
            artist_id = artist['id']
            artist_nome = artist['name']
            artist_popularidade = artist['popularity']
            if VERBOSE:
                print("Artista/Banda: {} , id: {}".format(artist_nome, artist_id))
            q = ('INSERT INTO artistas (id_artistas, nome, popularidade) VALUES (%s, %s, %s)')
            cursor.execute(q, (artist_id, artist_nome, artist_popularidade))
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

    artist_info = get_name(api, EGO_USERNAME)

    infos = artist_filter(artist_info)  # Get some filtered artist infos

    if save:
        cursor = connection.cursor()
        q = ('INSERT INTO artistas (id_artistas, nome, popularidade) VALUES (%s, %s, %s)')
        cursor.execute(q, (infos['artist_id'], infos['artist_name'], infos['artist_popularity']))
        cursor.close()

    tops = get_top_tracks(api, artist_info)

    filtered = top_tracks_filter(api, tops)  # Get top tracks infos
    # print(VERBOSE)
    # if VERBOSE:
    #     debug_print(infos, filtered, 0)

    related = get_related_artists(api, EGO_USERNAME, connection, save)

    # print(related)
    ##################Artistas relacionados##############################
    
    for related_artist in related:
        edge = (infos['artist_name'], related_artist['name'])
        cursor = connection.cursor()
        q = ('INSERT INTO edges (origem, destino) VALUES (%s, %s)')
        cursor.execute(q, (infos['artist_name'], related_artist['name']))
        cursor.close()

        # related = get_related_artists(api, related_artist, connection, save)
        tops = get_top_tracks(api, related_artist)

        filtered = top_tracks_filter(api, tops)  # Get top tracks infos
        # if VERBOSE:
        #     debug_print(related_artist, filtered, 1)

    #####################################################################
    
if __name__ == '__main__':
    main()
