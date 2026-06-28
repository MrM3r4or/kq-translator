# Support Via Crypto
``` 
ETH : 0x2f999c341e2719ff6D04B1564CD8c34e5F24b3Db

BTC : bc1qmmqdaua4z5hqmer22ec2rvm7nmj2hqm0lafr27

TRX : TJ6upyswMxPNCeFgctiQjhLsyuGyxETug8
```

# ابزار kq-translator 🎬

یک ابزار کامل و قدرتمند برای **تبدیل خودکار گفتار ویدیو به زیرنویس و ترجمه‌ی آن به زبان‌های مختلف** با استفاده از هوش مصنوعی. این پروژه از **OpenAI Whisper** برای تشخیص گفتار، **deep-translator** برای ترجمه و **gTTS** برای دوبله‌ی صوتی استفاده می‌کند.

### Special TNX to
FFmpeg : https://github.com/ffmpeg/ffmpeg
Flask : https://flask.palletsprojects.com/
OpenAI Whisper : https://github.com/openai/whisper

---

## ✨ ویژگی‌ها (Features)

- 🎤 **تشخیص خودکار گفتار** – با استفاده از مدل‌های قدرتمند Whisper (tiny, base, small, medium, large)
- 🌐 **ترجمه‌ی چندزبانه** – پشتیبانی از ۱۰۰+ زبان با Google Translate، DeepL و Microsoft Translator
- 🔊 **دوبله‌ی صوتی (اختیاری)** – تبدیل متن ترجمه‌شده به صدای مصنوعی با Google Text‑to‑Speech
- 📄 **خروجی زیرنویس SRT** – قابل دانلود و استفاده در هر پخش‌کننده‌ای
- 🎬 **پخش زنده** – نمایش زیرنویس ترجمه‌شده روی ویدیو در حین پخش
- 🖥️ **رابط کاربری زیبا و واکنش‌گرا** – طراحی شیشه‌ای (Glassmorphism) با پشتیبانی از دسکتاپ و موبایل
- 📟 **کنسول لاگ لحظه‌ای** – نمایش پیشرفت پردازش به‌صورت Real‑Time با Socket.IO
- ⏱️ **برآورد زمان باقی‌مانده** – نمایش ETA در حین پردازش
- 🔄 **لغو پردازش** – امکان توقف عملیات در هر مرحله
- 🔑 **مدیریت API Key** – ورود کلید API برای DeepL و Microsoft در همان صفحه
- 🎯 **Fallback خودکار** – در صورت عدم پشتیبانی DeepL از زبانی، به‌صورت خودکار به Google Translate تغییر می‌کند

---

## 🖼️ پیش‌نمایش (Screenshot)
<img width="1280" height="673" alt="4" src="https://github.com/user-attachments/assets/b800ff9d-22f8-4e2a-8cec-61f4ade2977f" />
<img width="1280" height="673" alt="3" src="https://github.com/user-attachments/assets/d17ee588-319c-40e1-be2d-d3abf27dbeb9" />
<img width="1280" height="668" alt="2" src="https://github.com/user-attachments/assets/42443ccf-0ec7-4d53-b556-460ce078488d" />
<img width="1280" height="674" alt="1" src="https://github.com/user-attachments/assets/aac1cd9c-1208-43f3-b640-69e311188db4" />



---

## 🛠️ پیش‌نیازها (Prerequisites)

- **Python 3.10 یا بالاتر**
- **FFmpeg** – برای استخراج صدا از ویدیو
  
  **نصب FFmpeg:**
  - **ویندوز:** از [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) یا [BtbN](https://github.com/BtbN/FFmpeg-Builds/releases) دانلود کرده و به `PATH` اضافه کنید.
  - **macOS:** `brew install ffmpeg`
  - **لینوکس (Debian/Ubuntu):** `sudo apt update && sudo apt install ffmpeg`

---

## 📦 نصب و راه‌اندازی (Installation)

### 1. کلون کردن پروژه

```bash
git clone https://github.com/MrM3r4or/kq-translator.git
cd kq-translator

### 2. ایجاد محیط مجازی (Virtual Environment)
```bash 
ویندوز :

python -m venv venv
venv\Scripts\activate

```bash
لینوکس / macOS :

python3 -m venv venv
source venv/bin/activate

### 3. نصب کتابخانه‌های مورد نیاز
```bash
pip install -r requirements.txt

### 4.اجرا ی برنامه 
```bash
python app.py

سپس مرورگر خود را باز کرده و به آدرس زیر بروید :
```bash
http://127.0.0.1:5000

### 🚀 نحوه‌ی استفاده (Usage)
آپلود ویدیو – فایل ویدیویی خود را (MP4, AVI, MOV, MKV, WEBM) با کشیدن یا کلیک کردن آپلود کنید

انتخاب زبان‌ها – زبان مبدا (گفتار ویدیو) و زبان مقصد (ترجمه) را انتخاب کنید

انتخاب کیفیت – از بین گزینه‌های Fast (سریع)، Balanced (متوسط) و Accurate (دقیق) یکی را انتخاب کنید

انتخاب مترجم – Google Translate (رایگان)، DeepL یا Microsoft Translator را انتخاب کنید

اگر DeepL یا Microsoft را انتخاب کنید، یک کادر برای وارد کردن API Key نمایش داده می‌شود

دوبله (اختیاری) – اگر می‌خواهید ویدیو دوبله شود (صدای مصنوعی به زبان مقصد)، چک‌باکس Dubbing را فعال کنید

شروع ترجمه – روی دکمه Generate Subtitles کلیک کنید

مشاهده‌ی پیشرفت – در صفحه‌ی پردازش، لاگ‌های لحظه‌ای و میزان پیشرفت را مشاهده کنید

دریافت خروجی – پس از اتمام، زیرنویس روی ویدیو نمایش داده می‌شود و می‌توانید فایل SRT را دانلود کنید

### 🔧 عیب‌یابی (Troubleshooting)

خطای FFmpeg not found
مطمئن شوید FFmpeg نصب است و در PATH قرار دارد

با دستور ffmpeg -version در ترمینال تست کنید

خطای DeepL API key is required
هنگام انتخاب DeepL، کلید API معتبر خود را در کادر مربوطه وارد کنید
یا از Google Translate استفاده کنید

خطای Language not supported در دوبله
همه‌ی زبان‌ها توسط gTTS پشتیبانی نمی‌شوند. اگر خطا داد، فقط زیرنویس تولید می‌شود

خطای Connection aborted در ترجمه
این خطا معمولاً به‌خاطر قطع ارتباط با سرور مترجم است. برنامه به‌صورت خودکار به Google Translate Fallback می‌کند

### 👨‍💻 توسعه‌دهنده (Developer)
- KhandaQh – توسعه‌دهنده و طراح

