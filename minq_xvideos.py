#!/usr/bin/env python3

import requests
import os
import shlex
import tempfile
import subprocess
import shutil

import bs4







def alert(msg):
    print(msg)
    input("PRESS ENTER")

def get_temp_file(prefix=None):
    with tempfile.NamedTemporaryFile(delete=False, prefix=prefix) as f:
        return f.name

def download_raw(url):
    name = get_temp_file()
    with open(name, 'wb') as f:
        page = requests.get(url)
        assert page.ok
        f.write(page.content)
    return name

def run_in_terminal(cmd:list, capture_output=False):
    cmd_fixed = shlex.join(cmd)
    print('running: %s'%cmd_fixed)
    res = subprocess.run(cmd_fixed, shell=True, check=True, capture_output=capture_output)
    return res

def display_image(path):
    #subprocess.run(shlex.join(['viu', s.thumb]), shell=True, check=True)
    run_in_terminal(['viu', path])
    #viu -h 12 -w 24 1.jpg -f

def play_video(path):
    os.environ['CACA_DRIVER'] = 'ncurses'
    #subprocess.run(shlex.join(['mplayer', '-really-quiet', '-vo', 'caca', s.video]), shell=True, check=True)
    run_in_terminal(['mplayer', '-really-quiet', '-vo', 'caca', path])
    os.environ['CACA_DRIVER'] = ''

    


DONE_POSTFIX = '.done'

class XVideo:
    
    def __init__(s, id, link, title, thumb, resolution, views, uploader, duration, cache_dir):
        s.id = id
        s.link = link
        s.title = title
        s.thumb_url = thumb
        s.resolution = resolution
        s.views = views
        s.uploader = uploader
        s.duration = duration

        s.downloaded_thumb = False
        s.thumb = None

        assert cache_dir.endswith('/')
        cache_dir = cache_dir.format(id)

        '''
        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir)

        stock_file_name_cache_dir = cache_dir + 'stock_file_name'
        stock_file_name_cache_dir_done = stock_file_name_cache_dir + DONE_POSTFIX
        if os.path.isfile(stock_file_name_cache_dir_done):
            with open(stock_file_name_cache_dir, 'r') as f:
                s.stock_file_name = f.read()
        else:
            #cmd_get_name = shlex.join(['youtube-dl', '--get-filename', s.link])
            #name = subprocess.run(cmd_get_name, shell=True, check=True, capture_output=True)
            name = run_in_terminal(['youtube-dl', '--get-filename', s.link], capture_output=True)
            name = name.stdout.decode().split('\n')[-2]
            s.stock_file_name = name

            with open(stock_file_name_cache_dir, 'w') as f:
                f.write(s.stock_file_name)
            with open(stock_file_name_cache_dir_done, 'w') as f:
                pass
        '''

        s.video = cache_dir + 'video' 
        s.video_cached = os.path.isfile(s.video + DONE_POSTFIX)

    def download(s):
        s.video_cached = False
        
        dir_ = s.video + DONE_POSTFIX
        if os.path.isfile(dir_):
            os.remove(dir_)

        #run_in_terminal(['youtube-dl', s.link])
        video_temp = '/tmp/' + s.id #get_temp_file(prefix=s.id)
        #run_in_terminal(['youtube-dl', '--output', video_temp, s.link])
        run_in_terminal(['yt-dlp', '--output', video_temp, s.link])

        dir_ = os.path.dirname(s.video)
        if not os.path.isdir(dir_):
            os.makedirs(dir_)
        
        #shutil.move(s.stock_file_name, s.video)
        shutil.move(video_temp, s.video)
        with open(s.video + DONE_POSTFIX, 'w') as f:
            pass
        
        s.video_cached = True

    def show_preview(s):
        print(s.title)
        print(s.duration)
        print(s.resolution)
        print(s.views)
        print(s.uploader)
        print(s.link)
    
        if not s.downloaded_thumb:
            s.thumb = download_raw(s.thumb_url)
            s.downloaded_thumb = True

        display_image(s.thumb)

    def play(s):
        if not s.video_cached:
            s.download()

        play_video(s.video)



class XVideos:
    url = 'https://www.xvideos.com/'
    first_page_url = url
    nth_page_url = first_page_url + 'new/{}/'

    blacklisted_videos_file = os.path.expanduser('~/.minq_xvideos/video_blacklist.blacklist')
    videos_cache_dir = 'videos/{}/'

    video_ind = 0
    last_command = 'next'
    last_scrapped_page = 0


    def __init__(s):
        s.videos = []

        blacklisted_videos_dir = os.path.dirname(s.blacklisted_videos_file)
        if not os.path.isdir(blacklisted_videos_dir):
            os.makedirs(blacklisted_videos_dir)

        if not os.path.isfile(s.blacklisted_videos_file):
            alert('Blacklisted video file doesn\'t exist; creating')
            with open(s.blacklisted_videos_file, 'w') as f:
                pass
    
        with open(s.blacklisted_videos_file) as f:
            videos = f.read().splitlines()
            while '' in videos:
                videos.remove('')
            s.blacklisted_videos = videos

    def extend_videos(s, videos):
        if len(videos) == 0:
            return
        
        # TODO: check for repeating videos

        videos = [video for video in videos if video.id not in s.blacklisted_videos]
        
        s.videos.extend(videos)

    def blacklist_a_video(s, video):
        s.blacklisted_videos.append(video.id)
        with open(s.blacklisted_videos_file, 'a') as f:
            f.write(video.id)
            f.write('\n')
        s.videos.remove(video)

    def scrape_another_page(s):
        assert s.url.endswith('/')

        page_num = s.last_scrapped_page + 1
        page_url = s.first_page_url if page_num == 1 else s.nth_page_url.format(page_num)

        page = requests.get(page_url)
        assert page.ok

        soup = bs4.BeautifulSoup(page.content, "lxml")

        videos = []
        metadatas1 = soup.find_all(class_='title')
        images = soup.find_all(class_='thumb')
        metadatas2 = soup.find_all(class_='metadata')
        durations = soup.find_all(class_='thumb-under')
        
        assert len(metadatas1) == len(images) == len(metadatas2) == len(durations)
        
        for data, image, data2, duration in zip(metadatas1, images, metadatas2, durations):           
            data = data.next

            id = data['href'].split('/')[1]
            if id in s.blacklisted_videos:
                continue
            
            link = s.url + data['href'][1:]
            title = data['title']
            
            image = image.next.next['data-src']
            if 'THUMBNUM' in image:
                assert image.count('THUMBNUM') == 1
                image = image.replace('THUMBNUM', '20')

            resolution = data2.next.next.text
            views = data2.next.text.split(' -  ')[-1].split(' - ')[0].split(' ')[0]
            uploader = data2.next.find(class_='name').text

            duration = duration.next.find(class_='duration').text
            
            videos.append(XVideo(id, link, title, image, resolution, views, uploader, duration, s.videos_cache_dir))
            print('scraped a video')

        s.extend_videos(videos)
        s.last_scrapped_page = page_num  

    def interactive(s):
        while True:
            print()
            print()
            
            if s.video_ind < 0:
                s.video_ind = 0
                alert('This is the first video')
            elif s.video_ind >= len(s.videos):
                s.scrape_another_page()

            video = s.videos[s.video_ind]

            video.show_preview()

            cmd = input('>')


            if cmd == '':
                cmd = s.last_command

            if cmd in ['quit', 'q']:
                break
            
            elif cmd in ['next', 'n', '']:
                s.video_ind += 1
            elif cmd in ['previous', 'prev', 'p']:
                s.video_ind -= 1

            elif cmd in ['download']:
                video.download()
                continue
            elif cmd in ['play']:
                video.play()

            elif cmd in ['backlist', 'black']:
                s.blacklist_a_video(video)
                continue
                
            else:
                alert(f'Unknown command: {cmd}')
                continue

            s.last_command = cmd


if __name__ == '__main__':
    xvideos = XVideos()
    xvideos.interactive()

