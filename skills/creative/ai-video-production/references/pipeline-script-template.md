# Pipeline Script Template for Cron Jobs

This is the prompt template to use when creating a cron job for daily YouTube Shorts generation.

## Cron Job Prompt

```
Kamu adalah agent produksi video YouTube Shorts otomatis. Jalankan pipeline berikut:

1. CEK TOPIK
   - Baca file ~/youtube-shorts/logs/topic_history.md
   - Pilih tema emosional yang BELUM PERNAH dipakai (kehilangan, kerinduan, reuni, penyesalan, kasih sayang keluarga)

2. TULIS SCRIPT
   - Buat script 5-6 scene, tiap scene 3-8 detik (durasi Veo max 8 detik)
   - Format: Subject + Action + Setting + Mood/Lighting
   - Simpan ke ~/youtube-shorts/scripts/YYYY-MM-DD.md

3. GENERATE VIDEO CLIPS
   - Untuk tiap scene, panggil GEMINI_GENERATE_VIDEOS via COMPOSIO_MULTI_EXECUTE_TOOL
   - Parameter: aspect_ratio=9:16, duration_seconds=6 atau 8
   - JANGAN pakai negative_prompt (tidak support!)
   - Poll tiap clip dengan GEMINI_WAIT_FOR_VIDEO
   - Download clip ke ~/youtube-shorts/output/YYYYMMDD/clips/scene_XX.mp4

4. CONCAT DENGAN FFMPEG
   - Jalankan: bash ~/youtube-shorts/concat.sh
   - Atau manual: ffmpeg -f concat -safe 0 -i filelist.txt -c copy final.mp4

5. UPLOAD KE YOUTUBE
   - Upload final.mp4 via YOUTUBE_UPLOAD_VIDEO (Composio)
   - Title: 1 kalimat emosional + bikin penasaran
   - Description: + hashtag #shortfilm #animasi #ceritapendek #sadstory #viral #fyp
   - Category: 22 (People & Blogs)
   - Privacy: public

6. LOG TOPIC
   - Append ke ~/youtube-shorts/logs/topic_history.md:
     YYYY-MM-DD | TOPIC | TITLE | VIDEO_ID | published

7. LAPORAN
   - Kirim hasil ke user: judul, link video, topik, jam tayang
```

## Cron Job Setup

```python
cronjob(
    action='create',
    schedule='0 12 * * *',  # 19:00 WIB
    prompt='...',  # The full prompt above
    skills=['ai-video-production'],
    name='youtube-shorts-daily',
    workdir='/home/ubuntu/youtube-shorts'
)
```

## WIB Time Conversion

- 19:00 WIB = 12:00 UTC
- 20:00 WIB = 13:00 UTC
- 21:00 WIB = 14:00 UTC