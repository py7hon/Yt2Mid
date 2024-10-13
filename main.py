import requests
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage
import re

# Fungsi untuk mengekstrak ID video dari URL YouTube
def extract_video_id(youtube_url):
    match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', youtube_url)
    return match.group(1) if match else None

# Fungsi untuk mengambil informasi video (judul dan artis) dari API
def get_video_info(video_id):
    api_url = f'https://pipedapi.nosebs.ru/streams/{video_id}'
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        title = data.get("title", "Judul Tidak Dikenal")
        artist = data.get("uploader", "Artis Tidak Dikenal")
        if "- Topic" in artist:
            artist = artist.split(" - Topic")[0]
        return title, artist
    else:
        print(f"Kesalahan saat mengambil informasi video: {response.status_code} - {response.text}")
        return None, None

# Fungsi untuk mengambil data akor dari API Chordify
def get_chord_info(video_id):
    load_url = f'https://chordify.net/api/v2/songs/youtube:{video_id}/chords?vocabulary=extended_inversions'
    r = requests.get(load_url)

    if r.status_code == 200:
        json = r.json()
        
        derived_key = json.get('derivedKey', 'N/A')
        bar_length = json.get('barLength', 'N/A')
        
        try:
            derived_bpm = json['derivedBpm']  # Mencoba mendapatkan derivedBpm
        except KeyError:
            print("Musik belum dibuatkan chordnya.")
            return None, None  # Kembali None jika tidak ada chord

        print(f'Kunci Lagu: {derived_key}')
        print(f'Panjang Bar: {bar_length}')
        print(f'Tempo (BPM): {derived_bpm}')

        return json, derived_key  # Mengembalikan JSON dan kunci yang diterima
    else:
        print(f"Kesalahan saat mengambil data: {r.status_code} - {r.text}")
        return None, None  # Mengembalikan None jika terjadi kesalahan

# Fungsi untuk mengonversi kunci musik menjadi nomor not MIDI
def key_to_midi(key):
    # Pemetaan kunci musik ke nomor not MIDI
    key_mapping = {
        'C': 60,  # C4
        'C#': 61, 'Db': 61,  # C#4/Db4
        'D': 62,  # D4
        'D#': 63, 'Eb': 63,  # D#4/Eb4
        'E': 64,  # E4
        'F': 65,  # F4
        'F#': 66, 'Gb': 66,  # F#4/Gb4
        'G': 67,  # G4
        'G#': 68, 'Ab': 68,  # G#4/Ab4
        'A': 69,  # A4
        'A#': 70, 'Bb': 70,  # A#4/Bb4
        'B': 71,  # B4
        'N': 60   # Default ke C4 untuk kunci yang tidak dikenal
    }
    return key_mapping.get(key, 60)  # Default ke C4 jika kunci tidak ditemukan

# Fungsi untuk menghasilkan file MIDI berdasarkan informasi root
def generate_midi(json, title, artist, derived_key):
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)

    # Mengatur tempo berdasarkan derivedBpm dari respon API
    derived_bpm = json['derivedBpm']
    tempo = mido.bpm2tempo(derived_bpm)  # Mengonversi BPM menjadi mikrodetik per ketukan
    track.append(MetaMessage('set_tempo', tempo=tempo))

    # Dapatkan not MIDI untuk kunci yang diterima
    root_key_midi = key_to_midi(derived_key)

    # Definisikan nomor not MIDI untuk root dasar
    chord_mapping = {
        'C:maj': [60, 64, 67],      # C mayor (C4, E4, G4)
        'D:maj': [62, 66, 69],      # D mayor (D4, F#4, A4)
        'E:maj': [64, 68, 71],      # E mayor (E4, G#4, B4)
        'F:maj': [65, 69, 72],      # F mayor (F4, A4, C5)
        'G:maj': [67, 71, 74],      # G mayor (G4, B4, D5)
        'A:maj': [69, 73, 76],      # A mayor (A4, C#5, E5)
        'B:maj': [71, 75, 78],      # B mayor (B4, D#5, F#5)
        'C:min': [60, 63, 67],      # C minor (C4, Eb4, G4)
        'D:min': [62, 65, 69],      # D minor (D4, F4, A4)
        'E:min': [64, 67, 71],      # E minor (E4, G4, B4)
        'F:min': [65, 68, 72],      # F minor (F4, Ab4, C5)
        'G:min': [67, 70, 74],      # G minor (G4, Bb4, D5)
        'A:min': [69, 72, 76],      # A minor (A4, C4, E5)
        'B:min': [71, 74, 78],      # B minor (B4, D4, F#5, A5)
        'C7': [60, 64, 67, 70],     # C7 (C4, E4, G4, Bb4)
        'D7': [62, 66, 69, 72],     # D7 (D4, F#4, A4, C4)
        'E7': [64, 68, 71, 74],     # E7 (E4, G#4, B4, D5)
        'F7': [65, 69, 72, 75],     # F7 (F4, A4, C5, Eb5)
        'G7': [67, 71, 74, 77],     # G7 (G4, B4, D5, F5)
        'A7': [69, 73, 76, 79],     # A7 (A4, C#5, E5, G5)
        'B7': [71, 75, 78, 81],     # B7 (B4, D#5, F#5, A#5)
        'Cmaj7': [60, 64, 67, 71],  # Cmaj7 (C4, E4, G4, B4)
        'Dmaj7': [62, 66, 69, 73],  # Dmaj7 (D4, F#4, A4, C#5)
        'Emaj7': [64, 68, 71, 75],  # Emaj7 (E4, G#4, B4, D#5)
        'Fmaj7': [65, 69, 72, 76],  # Fmaj7 (F4, A4, C5, E5)
        'Gmaj7': [67, 71, 74, 78],  # Gmaj7 (G4, B4, D5, F#5)
        'Amaj7': [69, 73, 76, 80],  # Amaj7 (A4, C#5, E5, G#5)
        'Bmaj7': [71, 75, 78, 82],  # Bmaj7 (B4, D#5, F#5, A#5)
        'Cdim': [60, 63, 66],       # C diminished (C4, Eb4, Gb4)
        'Ddim': [62, 65, 68],       # D diminished (D4, F4, Ab4)
        'Edim': [64, 67, 70],       # E diminished (E4, G4, Bb4)
        'Fdim': [65, 68, 71],       # F diminished (F4, Ab4, C5)
        'Gdim': [67, 70, 73],       # G diminished (G4, Bb4, Db5)
        'Adim': [69, 72, 75],       # A diminished (A4, C5, Eb5)
        'Bdim': [71, 74, 77],       # B diminished (B4, D5, F5)
        'C:min7': [60, 63, 67, 70], # C minor 7 (C4, Eb4, G4, Bb4)
        'D:min7': [62, 65, 69, 72], # D minor 7 (D4, F4, A4, C4)
        'E:min7': [64, 67, 71, 74], # E minor 7 (E4, G4, B4, D5)
        'F:min7': [65, 68, 72, 75], # F minor 7 (F4, Ab4, C5, Eb5)
        'G:min7': [67, 70, 74, 77], # G minor 7 (G4, Bb4, D5, F5)
        'A:min7': [69, 72, 76, 79], # A minor 7 (A4, C4, E5, G5)
        'B:min7': [71, 74, 78, 81], # B minor 7 (B4, D4, F#5, A5)
        'C:min7b5': [60, 63, 66, 70], # C minor 7 flat 5 (C4, Eb4, Gb4, Bb4)
        'D:min7b5': [62, 65, 68, 72], # D minor 7 flat 5 (D4, F4, Ab4, C4)
        'E:min7b5': [64, 67, 70, 74], # E minor 7 flat 5 (E4, G4, Bb4, D5)
        'F:min7b5': [65, 68, 71, 75], # F minor 7 flat 5 (F4, Ab4, C5, Eb5)
        'G:min7b5': [67, 70, 73, 77], # G minor 7 flat 5 (G4, Bb4, D5, F5)
        'A:min7b5': [69, 72, 76, 79], # A minor 7 flat 5 (A4, C4, E5, G5)
        'B:min7b5': [71, 74, 78, 81], # B minor 7 flat 5 (B4, D4, F#5, A5)
    }

    chords = [chord.split(';') for chord in json['chords'].split('\n')]
    i = 0

    # Menambahkan durasi not berdasarkan panjang bar
    note_duration = (480 * json['barLength']) // 4  # 480 ticks per ketukan
    
    while i < len(chords):
        for j in range(json['barLength']):
            if len(chords[i]) != 4:
                i += 1
                break
            
            if int(chords[i][0]) == j + 1:
                chord_name = chords[i][1]
                if chord_name in chord_mapping:
                    # Transpose not berdasarkan root_key_midi
                    notes = [note + (root_key_midi - 60) for note in chord_mapping[chord_name]]
                    for note in notes:
                        track.append(Message('note_on', note=note, velocity=64, time=0))
                    for note in notes:
                        track.append(Message('note_off', note=note, velocity=64, time=note_duration))
                i += 1
            else:
                # Jika tidak ada root, tambahkan jeda
                for note in range(60, 72):  # Dari C4 ke B4
                    track.append(Message('note_off', note=note, velocity=0, time=note_duration))
        
        # Akhir bar
        track.append(Message('note_off', note=60, velocity=0, time=note_duration))

    output_file_name = f"{artist} - {title}.mid"
    midi.save(output_file_name)
    print(f"File MIDI telah dibuat: {output_file_name}")

if __name__ == "__main__":
    print(f'Youtube Chord to Midi ')
    print(f'2024 © Yukifag (Iqbal Rifai)') 
    youtube_url = input("Masukkan link YouTube: ")
    
    video_id = extract_video_id(youtube_url)
    if video_id:
        title, artist = get_video_info(video_id)
        if title and artist:
            json_data, derived_key = get_chord_info(video_id)
            if json_data:
                generate_midi(json_data, title, artist, derived_key)
        else:
            print("Tidak dapat mengambil judul dan artis.")
    else:
        print("URL YouTube tidak valid.")