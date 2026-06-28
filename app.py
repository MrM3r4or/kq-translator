"""
kq-translator
Copyright KhandaQh

"""

import os
import uuid
import time
import threading
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# ─── App Setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "khandaqh-secret"
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*",
                    max_http_buffer_size=500 * 1024 * 1024)

UPLOAD_FOLDER = Path("static/uploads")
SRT_FOLDER    = Path("static/srt")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
SRT_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}

MODEL_SPEED = {
    "fast":     {"whisper": "base",   "secs_per_min": 8},
    "balanced": {"whisper": "small",  "secs_per_min": 20},
    "accurate": {"whisper": "large",  "secs_per_min": 60},
}

JOBS = {}

# ─── زبان‌های پشتیبانی‌شده توسط DeepL ──────────────────────────────────────────
DEEPL_SUPPORTED = {
    'bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr',
    'hu', 'id', 'it', 'ja', 'lt', 'lv', 'nl', 'pl', 'pt', 'ro',
    'ru', 'sk', 'sl', 'sv', 'tr', 'uk', 'zh'
}

# ─── Helper Functions ──────────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def seconds_to_srt_time(s):
    ms = int((s % 1) * 1000)
    total = int(s)
    secs = total % 60
    mins = (total // 60) % 60
    hrs  = total // 3600
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

def get_video_duration(path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except:
        return 0.0

def extract_audio(video_path, audio_path):
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-vn",
             "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path],
            capture_output=True, check=True, timeout=300
        )
        return True
    except:
        return False

def replace_audio_with_tts(video_path, text, target_lang):
    from gtts import gTTS
    tts = gTTS(text=text, lang=target_lang, slow=False)
    temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tts.save(temp_audio.name)
    temp_audio.close()

    video_dir = os.path.dirname(video_path)
    video_base = os.path.splitext(os.path.basename(video_path))[0]
    dubbed_path = os.path.join(video_dir, f"{video_base}_dubbed.mp4")

    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-i", temp_audio.name,
         "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0", "-shortest", dubbed_path],
        capture_output=True, check=True
    )
    os.unlink(temp_audio.name)
    return dubbed_path

# ─── SocketIO Safe Emit ──────────────────────────────────────────────────────────
def safe_emit(event, data, room=None):
    try:
        if room:
            socketio.emit(event, data, room=room)
        else:
            socketio.emit(event, data)
    except Exception:
        pass

def emit_log(sid, line, level="info"):
    safe_emit("log", {"line": line, "level": level}, room=sid)

def emit_progress(sid, step, total, label, pct=0, eta=""):
    safe_emit("progress", {"step": step, "total": total, "label": label,
                           "pct": pct, "eta": eta}, room=sid)

def emit_done(sid, srt_url, srt_filename, dubbed_video_url=None):
    safe_emit("done", {"srt_url": srt_url, "srt_filename": srt_filename,
                       "dubbed_video_url": dubbed_video_url}, room=sid)

def emit_error(sid, msg):
    safe_emit("error", {"message": msg}, room=sid)

def format_eta(seconds):
    if seconds <= 0: return "almost done"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}m {s}s remaining" if m > 0 else f"{s}s remaining"

# ─── Translator Factory with Smart Fallback ──────────────────────────────────
def _get_translator(engine, source, target, api_key=None):
    from deep_translator import GoogleTranslator, DeeplTranslator, MicrosoftTranslator
    src = source if source and source != "auto" else "auto"

    if engine == "deepl":
        # اگر زبان مقصد پشتیبانی نشود، به Google Translate برگرد
        if target not in DEEPL_SUPPORTED:
            print(f"[FALLBACK] DeepL does not support '{target}', using Google Translate.")
            return GoogleTranslator(source=src, target=target)
        key = api_key or os.getenv("DEEPL_API_KEY", "")
        if not key:
            print("[FALLBACK] No DeepL API key, using Google Translate.")
            return GoogleTranslator(source=src, target=target)
        try:
            return DeeplTranslator(api_key=key, source=src, target=target)
        except Exception as e:
            print(f"[FALLBACK] DeepL init failed ({e}), using Google Translate.")
            return GoogleTranslator(source=src, target=target)
    elif engine == "microsoft":
        key = api_key or os.getenv("MICROSOFT_API_KEY", "")
        if not key:
            print("[FALLBACK] No Microsoft API key, using Google Translate.")
            return GoogleTranslator(source=src, target=target)
        try:
            return MicrosoftTranslator(api_key=key, source=src, target=target)
        except Exception as e:
            print(f"[FALLBACK] Microsoft init failed ({e}), using Google Translate.")
            return GoogleTranslator(source=src, target=target)
    else:
        return GoogleTranslator(source=src, target=target)

# ─── Core Processing ─────────────────────────────────────────────────────────────
def process_video(job_id, sid, video_path, source_lang, target_lang,
                  quality, translator_engine, api_key=None, dub=False):
    cancel_event = JOBS[job_id]["cancel"]
    def cancelled(): return cancel_event.is_set()
    def log(msg, level="info"):
        emit_log(sid, msg, level)
        print(f"[{job_id[:8]}] {msg}")

    try:
        if not os.path.exists(video_path):
            emit_error(sid, "Video file not found.")
            return

        log("🎬 Job started...")
        duration = get_video_duration(video_path)
        model_cfg = MODEL_SPEED.get(quality, MODEL_SPEED["balanced"])
        whisper_model_name = model_cfg["whisper"]
        total_eta = (duration / 60) * model_cfg["secs_per_min"] + 15

        log(f"📹 Duration: {duration:.1f}s | Model: {whisper_model_name} | ETA: {format_eta(total_eta)}")
        emit_progress(sid, 1, 5 if dub else 4, "Extracting audio", 5, format_eta(total_eta))
        if cancelled(): return

        # ── Step 1: Audio extraction ──
        log("🔊 Extracting audio...")
        audio_path = str(UPLOAD_FOLDER / f"{job_id}.wav")
        start = time.time()
        if not extract_audio(video_path, audio_path):
            emit_error(sid, "FFmpeg failed. Is it installed?")
            return
        log(f"✅ Audio extracted in {time.time()-start:.1f}s")
        emit_progress(sid, 2, 5 if dub else 4, "Transcribing", 25, format_eta(total_eta - (time.time()-start)))
        if cancelled(): return

        # ── Step 2: Whisper ──
        log(f"🤖 Loading Whisper '{whisper_model_name}'...")
        import whisper
        model = whisper.load_model(whisper_model_name)
        log("✅ Model loaded.")
        opts = {"verbose": False, "word_timestamps": False}
        if source_lang and source_lang != "auto":
            opts["language"] = source_lang
        log(f"⏳ Transcribing (source: {source_lang or 'auto'})...")
        result = model.transcribe(audio_path, **opts)
        segments = result.get("segments", [])
        detected = result.get("language", "?")
        log(f"✅ {len(segments)} segments, detected: {detected}")
        if not segments:
            emit_error(sid, "No speech detected.")
            return
        emit_progress(sid, 3, 5 if dub else 4, "Translating", 65, "estimating...")
        if cancelled(): return

        # ── Step 3: Translation with Smart Fallback ──
        translated = []
        full_text = ""
        skip = (target_lang == "none" or target_lang == detected or
                (source_lang != "auto" and source_lang == target_lang))
        if skip:
            log("ℹ️ Skipping translation (same language).")
            for s in segments:
                text = s["text"].strip()
                translated.append({"start": s["start"], "end": s["end"], "text": text})
                full_text += text + ". "
        else:
            log(f"🌐 Translating → {target_lang} using {translator_engine}...")

            # تلاش برای ایجاد مترجم اصلی
            primary_translator = None
            fallback_translator = None
            try:
                primary_translator = _get_translator(translator_engine, detected, target_lang, api_key)
            except Exception as e:
                log(f"⚠️ Primary translator init failed ({e}), will use fallback.", "warn")

            # همیشه یک مترجم گوگل به عنوان Fallback داشته باش
            try:
                from deep_translator import GoogleTranslator
                fallback_translator = GoogleTranslator(source=detected if detected != "auto" else "auto", target=target_lang)
            except:
                fallback_translator = None

            for i, seg in enumerate(segments):
                if cancelled(): return
                orig = seg["text"].strip()
                if not orig:
                    translated.append({"start": seg["start"], "end": seg["end"], "text": ""})
                    continue

                trans_text = orig
                # ابتدا با مترجم اصلی تلاش کن
                if primary_translator:
                    try:
                        trans_text = primary_translator.translate(orig)
                    except Exception as e:
                        log(f"   ⚠️ Seg {i+1} primary translation failed: {e}", "warn")
                        # اگر مترجم اصلی خطا داد، با Fallback (Google) امتحان کن
                        if fallback_translator:
                            try:
                                trans_text = fallback_translator.translate(orig)
                                log(f"   ✅ Seg {i+1} translated with fallback (Google).", "success")
                            except Exception as e2:
                                log(f"   ❌ Seg {i+1} fallback also failed: {e2}", "error")
                                trans_text = orig  # برگرد به متن اصلی
                        else:
                            trans_text = orig
                elif fallback_translator:
                    # اگر مترجم اصلی وجود نداشت، مستقیم از Fallback استفاده کن
                    try:
                        trans_text = fallback_translator.translate(orig)
                    except Exception as e:
                        log(f"   ❌ Seg {i+1} fallback translation failed: {e}", "error")
                        trans_text = orig

                translated.append({"start": seg["start"], "end": seg["end"], "text": trans_text})
                full_text += trans_text + ". "

                if (i+1) % 5 == 0 or (i+1) == len(segments):
                    pct = 65 + int(25 * (i+1)/len(segments))
                    emit_progress(sid, 3, 5 if dub else 4, f"Translating ({i+1}/{len(segments)})", pct, "translating...")
            log("✅ Translation complete.")

        if cancelled(): return

        # ── Step 4: SRT ──
        emit_progress(sid, 4, 5 if dub else 4, "Generating SRT", 95, "almost done")
        srt_filename = f"{job_id}.srt"
        srt_path = SRT_FOLDER / srt_filename
        with open(srt_path, "w", encoding="utf-8") as f:
            for idx, seg in enumerate(translated, 1):
                if seg["text"]:
                    f.write(f"{idx}\n{seconds_to_srt_time(seg['start'])} --> {seconds_to_srt_time(seg['end'])}\n{seg['text']}\n\n")
        srt_url = f"/static/srt/{srt_filename}"
        log(f"✅ SRT saved: {srt_filename}")

        # ── Step 5: Dubbing (only if translation was successful and text exists) ──
        dubbed_url = None
        if dub and not skip and full_text.strip():
            # بررسی کنیم که آیا متن ترجمه شده با زبان اصلی تفاوت دارد یا نه
            # اگر متن ترجمه نشده باشد (همان انگلیسی باشد)، دوبله انجام نشود
            if full_text.strip() == " ".join([s["text"] for s in translated]).strip():
                log("ℹ️ Dubbing skipped: text is not translated (same as original).", "warn")
            else:
                emit_progress(sid, 5, 5, "Dubbing", 98, "generating audio...")
                log("🔊 Dubbing with Google TTS...")
                try:
                    dubbed_path = replace_audio_with_tts(video_path, full_text, target_lang)
                    final_path = UPLOAD_FOLDER / f"{job_id}_dubbed.mp4"
                    os.rename(dubbed_path, final_path)
                    dubbed_url = f"/static/uploads/{job_id}_dubbed.mp4"
                    log("✅ Dubbing successful.", "success")
                except Exception as e:
                    log(f"⚠️ Dubbing failed: {e}", "warn")
                    emit_log(sid, f"⚠️ Dubbing not available for '{target_lang}'. Only subtitles generated.", "warn")
        elif dub:
            log("ℹ️ Dubbing skipped (no translation or empty text).")

        log("🎉 All done!")
        emit_progress(sid, 5 if dub else 4, 5 if dub else 4, "Complete!", 100, "done")
        emit_done(sid, srt_url, srt_filename, dubbed_url)

    except Exception as ex:
        import traceback
        log(f"❌ Error: {ex}", "error")
        log(traceback.format_exc(), "error")
        emit_error(sid, f"Processing failed: {ex}")
    finally:
        try:
            (UPLOAD_FOLDER / f"{job_id}.wav").unlink()
        except:
            pass
        JOBS.pop(job_id, None)

# ─── Routes ──────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/processing/<job_id>")
def processing(job_id):
    video = request.args.get("video", "")
    source = request.args.get("source_lang", "auto")
    target = request.args.get("target_lang", "en")
    quality = request.args.get("quality", "balanced")
    translator = request.args.get("translator", "google")
    return render_template("processing.html",
                           job_id=job_id,
                           video_filename=video,
                           source_lang=source,
                           target_lang=target,
                           quality=quality,
                           translator_engine=translator)

@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["video"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    job_id = str(uuid.uuid4())
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{job_id}.{ext}"
    file.save(str(UPLOAD_FOLDER / filename))
    return jsonify({"job_id": job_id, "filename": filename})

@app.route("/static/srt/<filename>")
def serve_srt(filename):
    return send_from_directory(SRT_FOLDER, filename, as_attachment=True)

@app.route("/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id):
    if job_id in JOBS:
        JOBS[job_id]["cancel"].set()
        return jsonify({"status": "cancelled"})
    return jsonify({"status": "not_found"}), 404

# ─── SocketIO Events ────────────────────────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    print(f"Client connected: {request.sid}")

@socketio.on("disconnect")
def on_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on("start_processing")
def on_start_processing(data):
    sid = request.sid
    job_id = data.get("job_id")
    video_filename = data.get("video_filename")
    source_lang = data.get("source_lang", "auto")
    target_lang = data.get("target_lang", "en")
    quality = data.get("quality", "balanced")
    translator_engine = data.get("translator_engine", "google")
    api_key = data.get("api_key")
    dub = data.get("dub", False)

    if not job_id or not video_filename:
        emit("error", {"message": "Missing data"})
        return

    video_path = None
    for ext in ALLOWED_EXTENSIONS:
        cand = UPLOAD_FOLDER / f"{job_id}.{ext}"
        if cand.exists():
            video_path = str(cand)
            break
    if not video_path:
        cand = UPLOAD_FOLDER / video_filename
        if cand.exists():
            video_path = str(cand)

    if not video_path:
        emit("error", {"message": "Video not found"})
        return

    cancel_event = threading.Event()
    t = threading.Thread(
        target=process_video,
        args=(job_id, sid, video_path, source_lang, target_lang,
              quality, translator_engine),
        kwargs={"api_key": api_key, "dub": dub},
        daemon=True
    )
    JOBS[job_id] = {"cancel": cancel_event, "thread": t}
    t.start()
    emit("started", {"job_id": job_id})

@socketio.on("cancel_processing")
def on_cancel(data):
    job_id = data.get("job_id")
    if job_id in JOBS:
        JOBS[job_id]["cancel"].set()
        emit("cancelled", {"job_id": job_id})

# ─── Entry Point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  AI Subtitle Generator — KhandaQh")
    print("  http://127.0.0.1:5000")
    print("=" * 60)
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)