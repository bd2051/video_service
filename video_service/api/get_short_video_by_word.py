import tempfile
from urllib.parse import parse_qs, urlparse
from pytube import YouTube
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from transliterate import translit
from youtube_transcript_api import YouTubeTranscriptApi
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

from video_service.settings import MEDIA_ROOT


@csrf_exempt
def get_short_video_by_word(request):
    video_link = request.POST['video_link']
    word = request.POST['word']
    if not video_link or not word:
        return HttpResponse('Не хватает параметров')
    video_url = urlparse(video_link)
    video_qs = parse_qs(video_url.query)
    video_id = video_qs['v'][0]
    subtitles = YouTubeTranscriptApi.get_transcript(video_id, languages=['ru'])
    time_periods = []
    for subtitle in subtitles:
        if subtitle['text'].find(word) != -1:
            time_periods.append(subtitle)
    if not len(time_periods):
        return HttpResponse('слово не найдено')
    with tempfile.TemporaryDirectory() as tempdir:
        url = YouTube(video_link).streams.first().download(tempdir)
        result = ''
        for time_period in time_periods:
            name = '{}_{}.mp4'.format(translit(word, reversed=True), time_period['start'])
            path = '{}/{}'.format(MEDIA_ROOT, name)
            ffmpeg_extract_subclip(
                url,
                time_period['start'],
                float(time_period['start']) + float(time_period['duration']),
                targetname=path
            )
            result += '<a href="/media/{}" download>{}</a><br>'.format(name, name)

        return HttpResponse(result)
