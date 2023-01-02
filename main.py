""" Youtube maximum quality downloader application.
Supports individual links to videos and playlists.

Downloads videos with highest quality possible and
 saves a seperate audio file with it.

Dependencies:
 - pytube used to download YouTube streams. (pip install pytube)
 - FFmpeg used to convert and merge streams.

Made by Mαtq#0035 on Discord
User ID 243713302750953482 on https://discord.id/ & https://lookup.guru/
"""

import pytube
import ffmpy
import os
records = {}
RECORDS_FILE = 'records'
RECORD_SEPERATOR = '-= End of record =-\n'
VIDEO_DIR = 'Videos\\'
TRACK_DIR = 'Tracks\\'
TEMP_DIR = 'Temp\\'
TEMP_VIDEO_DIR = TEMP_DIR + 'Video\\'
TEMP_TRACK_DIR = TEMP_DIR + 'Track\\'
os.system('')
GREEN = '\033[32m'
YELLOW = '\033[33m'
RED = '\033[31m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
RESETCOLOR = '\033[39m'
RESETBGCOLOR = '\033[49m'
RESET = '\033[0m'
UNDERLINE = '\033[4m'
UNUNDERLINE = '\033[24m'
BOLD = '\033[1m'
UNBOLD = '\033[2m'


def cleanup_temp():
    path = f'{os.getcwd()}\\{TEMP_DIR}'
    if os.path.exists(path):
        for subdir in os.listdir(path):
            subdir = f'{path}{subdir}\\'
            for file in os.listdir(subdir):
                os.remove(subdir+file)
            os.rmdir(subdir)
        os.rmdir(path)


def background_color(r: int, g: int, b: int):
    print(f'\033[48;2;{r};{g};{b}m', end='')


def list_records(output_records: dict):
    for video_id in output_records:
        current_record = output_records[video_id]

        msg = []
        if 'title' in current_record and current_record['title'] is not None:
            msg.append(f'{BOLD}{current_record["title"]}{UNBOLD}')

        id_text = f'{UNDERLINE}{video_id}{UNUNDERLINE}'
        msg.append(id_text)

        if 'progressive' in current_record and current_record['progressive'] is not None:
            msg.append(f'{(f"{MAGENTA}Interlaced{RESETCOLOR}", f"{CYAN}Progressive{RESETCOLOR}")[current_record["progressive"]]}')

        msg.append(f'{GREEN}#{list(records.keys()).index(video_id)}{RESETCOLOR}')
        print(' | '.join(msg))


def update_records():
    global records
    new_content = ''
    for record in records.values():
        new_content += parse_record(record)

    with open(RECORDS_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)


def parse_record(record: dict):
    parsed = ''
    for key, value in record.items():
        parsed += f'{key}={value}\n'
    parsed += RECORD_SEPERATOR
    return parsed


def stream_is_progressive(stream: pytube.Stream):
    return stream.video_codec is not None and stream.audio_codec is not None


def process_playlist(playlist_url: str):
    playlist = pytube.Playlist(playlist_url)
    print(f'Playlist {playlist.title} with video count of {playlist.length}')

    for i, session in enumerate(playlist.videos):
        if i % 2:
            background_color(50, 50, 50)
        else:
            background_color(30, 30, 30)

        try:
            process_video(session)
        except Exception as e:
            print(f"{RED}Couldn't process video {session.title}\n{e}{RESETCOLOR}")


def process_video(session: pytube.YouTube):
    video_id = session.video_id
    id_text = f'{UNDERLINE}{video_id}{UNUNDERLINE}'

    if video_id in records:
        msg = []
        if 'title' in records[video_id] and records[video_id]['title'] is not None:
            msg.append(f'{BOLD}{records[video_id]["title"]}{UNBOLD}')

        msg.append(id_text)
        if 'progressive' in records[video_id] and records[video_id]['progressive'] is not None:
            msg.append(f'{(f"{MAGENTA}Interlaced{RESETCOLOR}", f"{CYAN}Progressive{RESETCOLOR}")[records[video_id]["progressive"]]}')

        msg.append(f'{GREEN}Video already downloaded at #{list(records.keys()).index(video_id)}{RESETCOLOR}')
        print(' | '.join(msg))

        if 'title' not in records[video_id] or records[video_id]['title'] is None:
            title = session.title
            records[video_id]['title'] = title
            print(f'{YELLOW}Updated title to {title}{RESETCOLOR}')
        if 'progressive' not in records[video_id] or records[video_id]['progressive'] is None:
            video_streams = session.streams.filter(type='video')
            sorted_streams = sorted(video_streams, key=lambda s: int(s.resolution[:len(s.resolution) - 1]), reverse=True)
            video_stream = sorted_streams[0]
            progressive = stream_is_progressive(video_stream)
            records[video_id]['progressive'] = progressive
            print(f'{YELLOW}Updated progressive to {progressive}{RESETCOLOR}')
        update_records()
        return

    next_index = len(records)
    title = session.title
    msg = [f'{BOLD}{title}{UNBOLD}', id_text, f'{YELLOW}Processing video at #{next_index}{RESETCOLOR}']
    print(' | '.join(msg))

    if session.age_restricted:
        print(f'{RED}Video is age restricted and cannot be downloaded with this application (no authentification option){RESETCOLOR}')
        return

    all_streams = session.streams

    video_streams = all_streams.filter(type='video')
    sorted_streams = sorted(video_streams, key=lambda s: int(s.resolution[:len(s.resolution)-1]), reverse=True)
    video_stream = sorted_streams[0]
    print(f'Video stream {video_stream}')

    if not os.path.exists(VIDEO_DIR):
        os.mkdir(VIDEO_DIR)
    if not os.path.exists(TRACK_DIR):
        os.mkdir(TRACK_DIR)

    progressive = stream_is_progressive(video_stream)
    if progressive:
        base_video_path = process_video_stream(video_stream, progressive)
        audio_path = process_audio_from_video(base_video_path)
        video_path = base_video_path
    else:
        audio_streams = all_streams.filter(type='audio').order_by('abr').desc()
        audio_stream = audio_streams[0]
        print(f'Audio stream {audio_stream}')
        base_video_path = process_video_stream(video_stream, progressive)
        audio_path = process_audio_stream(audio_stream)
        video_path = merge_video_audio(base_video_path, audio_path)

    records[video_id] = {}
    record = records[video_id]
    record['video_id'] = video_id
    record['title'] = title
    record['progressive'] = progressive
    record['last_changed'] = None
    record['video'] = video_path
    record['audio'] = audio_path

    new_content = parse_record(record)

    with open(RECORDS_FILE, 'a', encoding='utf-8') as f:
        f.write(new_content)
    print(f'{GREEN}Video successfully added at #{next_index}{RESETCOLOR}')


def process_video_stream(video_stream: pytube.Stream, progressive: bool):
    video_at = video_stream.download(TEMP_VIDEO_DIR)
    video_file = os.path.basename(video_at)
    video_filename, video_ext = os.path.splitext(video_file)
    if not progressive:
        return video_at

    video_path = f'{VIDEO_DIR}{video_filename}.mp4'
    ffmpeg = ffmpy.FFmpeg(inputs={video_at: None},
                          outputs={video_path: None},
                          global_options='-y -loglevel warning')
    ffmpeg.run()
    os.remove(video_at)
    return video_path


def process_audio_from_video(video_path: str):
    video_file = os.path.basename(video_path)
    video_filename, _ = os.path.splitext(video_file)
    audio_path = f'{TRACK_DIR}{video_filename}.mp3'

    ffmpeg = ffmpy.FFmpeg(inputs={video_path: None},
                          outputs={audio_path: None},
                          global_options='-y -loglevel warning')
    ffmpeg.run()
    return audio_path


def process_audio_stream(audio_stream: pytube.Stream):
    audio_at = audio_stream.download(TEMP_TRACK_DIR)
    audio_file = os.path.basename(audio_at)
    audio_filename, _ = os.path.splitext(audio_file)
    audio_path = f'{TRACK_DIR}{audio_filename}.mp3'

    ffmpeg = ffmpy.FFmpeg(inputs={audio_at: None},
                          outputs={audio_path: None},
                          global_options='-y -loglevel warning')
    ffmpeg.run()
    os.remove(audio_at)
    return audio_path


def merge_video_audio(video_path: str, audio_path: str):
    video_file = os.path.basename(video_path)
    video_filename, _ = os.path.splitext(video_file)
    new_video_path = f'{VIDEO_DIR}{video_filename}.mp4'

    ffmpeg = ffmpy.FFmpeg(inputs={video_path: None, audio_path: None},
                          outputs={new_video_path: '-c copy -map 0:v:0 -map 1:a:0'},
                          global_options='-y -loglevel warning')
    ffmpeg.run()
    os.remove(video_path)
    return new_video_path


forms = {'v': 'video', 'p': 'playlist'}


def main():
    cleanup_temp()

    if not os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, 'w', encoding='utf-8') as f:
            f.write('')

    with open(RECORDS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    containers = [[attr for attr in container.splitlines() if attr] for container in content.split(RECORD_SEPERATOR)]
    for container in containers:
        result = {}
        for attribute in container:
            seperate_at = attribute.find('=')
            key = attribute[:seperate_at]
            value = attribute[seperate_at + 1:]
            if value == 'None':
                value = None
            elif value == 'False':
                value = False
            elif value == 'True':
                value = True
            result[key] = value
        if 'video_id' in result:
            video_id = result['video_id']
            records[video_id] = result
    print(f'Found {len(records)} records.')

    while True:
        try:
            print('\n'
                  'Process [P]laylist or [V]ideo\n'
                  'List [R]ecords')
            user_choice = input('> ').lower()

            if not user_choice:
                continue

            first_char = user_choice[0]
            if first_char in 'pv':
                form_name = forms[first_char]
                print(f'Enter {form_name} url')
                url = input('> ')

                if first_char == 'p':
                    process_playlist(url)
                elif first_char == 'v':
                    session = pytube.YouTube(url=url)
                    process_video(session)
            elif first_char in 'r':
                list_records(records)
            else:
                print('Selection not found')

        except Exception as e:
            print(f'{RED}{e}{RESETCOLOR}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
