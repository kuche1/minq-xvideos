#!/usr/bin/env python3

import requests
import os
import shlex
import tempfile
import subprocess

import bs4







def alert(msg):
    print(msg)
    input("PRESS ENTER")

def get_temp_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        return f.name

def download_raw(url):
    name = get_temp_file()
    with open(name, 'wb') as f:
        page = requests.get(url)
        assert page.ok
        f.write(page.content)
    return name






class XVideo:
    def __init__(s, id, link, title, thumb, resolution, views, uploader, duration):
        s.id = id
        s.link = link
        s.title = title
        s.thumb_url = thumb
        s.resolution = resolution
        s.views = views
        s.uploader = uploader
        s.duration = duration

        s.downloaded_thumb = False
        s.downloaded_video = False

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
            
        subprocess.run(shlex.join(['viu', s.thumb]), shell=True, check=True)
        #viu -h 12 -w 24 1.jpg -f

    def download(s):
        cmd_download = shlex.join(['youtube-dl', s.link])
        cmd_get_name = shlex.join(['youtube-dl', '--get-filename', s.link])

        subprocess.run(cmd_download, shell=True, check=True)
        res = subprocess.run(cmd_get_name, shell=True, check=True, capture_output=True)
        res = res.stdout.decode().split('\n')[-2]
        s.video_dir = res
        s.downloaded_video = True

    def play(s):
        if not s.downloaded_video:
            s.download()
        
        #subprocess.run(shlex.join(['mplayer', '-vo', 'caca', s.video_dir]), shell=True, check=True)
        #subprocess.run('export CACA_DRIVER=ncurses', shell=True, check=True)
        os.environ['CACA_DRIVER'] = 'ncurses'
        subprocess.run(shlex.join(['mplayer', '-really-quiet', '-vo', 'caca', s.video_dir]), shell=True, check=True)
        #subprocess.run(shlex.join(['viu', s.video_dir]), shell=True, check=True)



class XVideos:
    url = 'https://www.xvideos.com/'
    first_page_url = url
    nth_page_url = first_page_url + 'new/{}/'

    blacklisted_videos_file = 'video_niggerlist.blacklist'

    last_scrapped_page = 0

    video_ind = 0
    last_command = 'next'

    def __init__(s):
        s.videos = []
        
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
            
            videos.append(XVideo(id, link, title, image, resolution, views, uploader, duration))

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

            elif cmd in ['backlist', 'black'] + ['niggerlist', 'nigger', 'nigg', 'nig']:
                s.blacklist_a_video(video)
                continue
                
            else:
                alert(f'Unknown command: {cmd}')
                continue

            s.last_command = cmd


if __name__ == '__main__':
    xvideos = XVideos()
    xvideos.interactive()

