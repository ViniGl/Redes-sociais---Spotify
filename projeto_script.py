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
save = False


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
                q = (
                    'INSERT INTO artistas (id_artistas, nome, popularidade) VALUES (%s, %s, %s)')
                cursor.execute(
                    q, (artist_id, artist_nome, artist_popularidade))
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
        print(
            "Artista: {} // Popularidade: {} ".format(infos['name'], infos['popularity']))

    for top_filtered in filtered:
        # pass
        print('''\
    Id: {} // Titulo: {} // Popularidade: {}
    Dancabilidade: {} // Energia: {}
        '''.format(top_filtered['song_id'], top_filtered['song_name'], top_filtered['song_popularity'], top_filtered['danceability'], top_filtered['energy']))


def track_analysis(api, song_id):
    data = api.audio_features(song_id)[0]

    analysis = {}

    analysis['danceability'] = data['danceability']
    analysis['energy'] = data['energy']
    return analysis


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

        a = requests.get(playlists[pl]['href'], headers={
                         "Accept": "application/json", "Content-Type": "application/json", "Authorization": "Bearer {}".format(ACCESS_TOKEN)})

        
        playlist_tracks = []
        for song in a.json()['items']:
            track_infos = {}
            # print(song['track']['name'])
            track_infos['song_id'] = song['track']['id']
            track_infos['song_name'] = song['track']['name']
            track_infos['song_artist'] = song['track']['album']['artists'][0]['name']
            track_infos['song_popularity'] = song['track']['popularity']
            track_infos['song_lenght'] = song['track']['duration_ms']

            playlist_tracks.append(track_infos)
        
        # print(playlist_tracks)
        songs_playlist[pl] = playlist_tracks

    return songs_playlist


def get_id_playlist(api, connection, nome):
    cursor = connection.cursor()
    q = ('SELECT id_playlist FROM playlist WHERE nome=%s')
    cursor.execute(q, (nome))
    id = cursor.fetchone()
    cursor.close()
    return id

def get_id_song(api, connection, id_spotify):
    cursor = connection.cursor()
    q = ('SELECT id_musicas FROM musicas WHERE id_spotify=%s')
    cursor.execute(q, (id_spotify))
    id = cursor.fetchone()
    cursor.close()
    return id



def insert_playlist(api, connection, raw_playlist, genero):

    cursor = connection.cursor()
    for playlist in raw_playlist:
        q = ('INSERT INTO playlist (nome, genero) VALUES (%s, %s)')
        cursor.execute(q, (playlist, genero))
    cursor.close()


def insert_musica_playlist(api, connection, raw_playlist):

    cursor = connection.cursor()
    for playlist in raw_playlist:

        playlist_id = get_id_playlist(api, connection, playlist)

        for song in raw_playlist[playlist]:

            #Insere musica
            try:
                q = ('INSERT INTO musicas (nome, id_spotify, popularidade, duracao, energia, dancabilidade, nome_artistas) VALUES (%s, %s, %s, %s, %s,%s, %s)')
                cursor.execute(q, (song['song_name'], song['song_id'], song['song_popularity'], song['song_lenght'],
                                song['energy'], song['danceability'], song['song_artist']))
            except:
                pass
            
            #Insere na tabela intermediaria
            try:
                song_id = get_id_song(api, connection, song['song_id'])
                q = ('INSERT INTO playlist_musicas (id_playlist, id_musicas) VALUES (%s, %s)')
                cursor.execute(q, (playlist_id, song_id))
            except Exception as e:
                print(e) 
           
    cursor.close()


def update_playlist_songs_info(api, raw_two_way):
    total = len(raw_two_way)
    actual = 0
    for playlist in raw_two_way:
        total_song = len(raw_two_way[playlist])
        actual_song = 0
        for song in raw_two_way[playlist]:
            # print(song['song_name'])
            song_id = song['song_id']
            analyse = track_analysis(api, song_id)

            danceability = analyse['danceability']
            energy = analyse['energy']
            song['danceability'] = danceability
            song['energy'] = energy
        
            actual_song += 1
            print("Musica em playlist : {} -- Total :{} %".format(playlist,   (actual_song/total_song) * 100))
    
        actual += 1
        print("#"*100)
        print("Playlist total : {} %".format( (actual/total) * 100))
        print("#"*100)

def main():
    args = sys.argv
    if "-v" in args:
        VERBOSE = True

    if '--save' in args:
        save = True

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
    
    print('GETTING ALL CATEGORIES')
    all_categories = get_categories(api)

    category_1 = "Rock"
    # category_2 = "Sertanejo"

    print('GET ALL PLAYLISTS FROM A CATEGORY')
    playlists_rock = get_playlists(api, all_categories[category_1])
    # playlists_sertanejo = get_playlists(api, all_categories[category_2])
    # print(playlists_rock)

    print('MAKING RAW_TWO_WAY')
    raw_two_way = playlist_song_relation(api, playlists_rock)

    print('ENERGY + DANCEABILITY')
    update_playlist_songs_info(api, raw_two_way)


    if save:
        print('SAVING')
        insert_playlist(api, connection, raw_two_way, category_1)
        insert_musica_playlist(api, connection, raw_two_way)


if __name__ == '__main__':
    main()
