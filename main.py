import uuid
import logging
import requests
import telebot
import json
from flask import Flask, request, abort
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, ReplyKeyboardMarkup, KeyboardButton
import asyncio
import threading
import time
import os

from msspeech import MSSpeech, MSSpeechError
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

TOKEN = "7790991731:AAF4NHGm0BJCf08JTdBaUWKzwfs82_Y9Ecw"
ADMIN_ID = 5978150981
WEBHOOK_URL = "https://probable-sybilla-wwmahe-52df4f73.koyeb.app/"
REQUIRED_CHANNEL = "@guruubka_wasmada"

bot = telebot.TeleBot(TOKEN, threaded=True)
app = Flask(__name__)

MONGO_URI = "mongodb+srv://hoskasii:GHyCdwpI0PvNuLTg@cluster0.dy7oe7t.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "telegram_bot_db"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]
tts_settings_collection = db["tts_settings"]
stt_settings_collection = db["stt_settings"]
tokens_collection = db["tokens"]

ASSEMBLYAI_API_KEY = "894ad2705ab54e33bb011a87b658ede2"

in_memory_data = {
    "users": {},
    "tts_settings": {},
    "stt_settings": {},
}

user_tts_mode = {}
user_pitch_input_mode = {}
user_rate_input_mode = {}

admin_state = {}

STT_LANGUAGES = {
    "English 🇬🇧": "en", "العربية 🇸🇦": "ar", "Spanish 🇪🇸": "es", "French 🇫🇷": "fr", "German 🇩🇪": "de",
    "Russian 🇷🇺": "ru", "Portuguese 🇵🇹": "pt", "Japanese 🇯🇵": "ja", "Korean 🇰🇷": "ko", "Chinese 🇨🇳": "zh",
    "Hindi 🇮🇳": "hi", "Indonesian 🇮🇩": "id", "Italian 🇮🇹": "it", "Turkish 🇹🇷": "tr", "Vietnamese 🇻🇳": "vi",
    "Thai 🇹🇱": "th", "Polish 🇵🇱": "pl", "Dutch 🇳🇱": "nl", "Swedish 🇸🇪": "sv", "Norwegian 🇳🇴": "no",
    "Danish 🇩🇰": "da", "Finnish 🇫🇮": "fi", "Czech 🇨🇿": "cs", "Hungarian 🇭🇺": "hu", "Romanian 🇷🇴": "ro",
    "Malay 🇲🇾": "ms", "Uzbek 🇺🇿": "uz", "Tagalog 🇵🇱": "tl", "اردو 🇵🇰": "ur", "Swahili 🇰🇪": "sw",
    "Kazakh 🇰🇿": "kk", "Azerbaijani 🇦🇿": "az", "Bulgarian 🇧🇬": "bg", "Serbian 🇷🇸": "sr", "فارسى 🇮🇷": "fa",
}

VOICE_MAPPING = {
    "ar-DZ-AminaNeural": "Amina - Arabic (Algeria)", "ar-DZ-IsmaelNeural": "Ismael - Arabic (Algeria)",
    "ar-BH-AliNeural": "Ali - Arabic (Bahrain)", "ar-BH-LailaNeural": "Laila - Arabic (Bahrain)",
    "ar-EG-SalmaNeural": "Salma - Arabic (Egypt)", "ar-EG-ShakirNeural": "Shakir - Arabic (Egypt)",
    "ar-IQ-BasselNeural": "Bassel - Arabic (Iraq)", "ar-IQ-RanaNeural": "Rana - Arabic (Iraq)",
    "ar-JO-SanaNeural": "Sana - Arabic (Jordan)", "ar-JO-TaimNeural": "Taim - Arabic (Jordan)",
    "ar-KW-FahedNeural": "Fahed - Arabic (Kuwait)", "ar-KW-NouraNeural": "Noura - Arabic (Kuwait)",
    "ar-LB-LaylaNeural": "Layla - Arabic (Lebanon)", "ar-LB-RamiNeural": "Rami - Arabic (Lebanon)",
    "ar-LY-ImanNeural": "Iman - Arabic (Libya)", "ar-LY-OmarNeural": "Omar - Arabic (Libya)",
    "ar-MA-JamalNeural": "Jamal - Arabic (Morocco)", "ar-MA-MounaNeural": "Mouna - Arabic (Morocco)",
    "ar-OM-AbdullahNeural": "Abdullah - Arabic (Oman)", "ar-OM-AyshaNeural": "Aysha - Arabic (Oman)",
    "ar-QA-AmalNeural": "Amal - Arabic (Qatar)", "ar-QA-MoazNeural": "Moaz - Arabic (Qatar)",
    "ar-SA-HamedNeural": "Hamed - Arabic (Saudi Arabia)", "ar-SA-ZariyahNeural": "Zariyah - Arabic (Saudi Arabia)",
    "ar-SY-AmanyNeural": "Amany - Arabic (Syria)", "ar-SY-LaithNeural": "Laith - Arabic (Syria)",
    "ar-TN-HediNeural": "Hedi - Arabic (Tunisia)", "ar-TN-ReemNeural": "Reem - Arabic (Tunisia)",
    "ar-AE-FatimaNeural": "Fatima - Arabic (UAE)", "ar-AE-HamdanNeural": "Hamdan - Arabic (UAE)",
    "ar-YE-MaryamNeural": "Maryam - Arabic (Yemen)", "ar-YE-SalehNeural": "Saleh - Arabic (Yemen)",
    "en-AU-NatashaNeural": "Natasha - English (Australia)", "en-AU-WilliamNeural": "William - English (Australia)",
    "en-CA-ClaraNeural": "Clara - English (Canada)", "en-CA-LiamNeural": "Liam - English (Canada)",
    "en-HK-SamNeural": "Sam - English (Hongkong)", "en-HK-YanNeural": "Yan - English (Hongkong)",
    "en-IN-NeerjaNeural": "Neerja - English (India)", "en-IN-PrabhatNeural": "Prabhat - English (India)",
    "en-IE-ConnorNeural": "Connor - English (Ireland)", "en-IE-EmilyNeural": "Emily - English (Ireland)",
    "en-KE-AsiliaNeural": "Asilia - English (Kenya)", "en-KE-ChilembaNeural": "Chilemba - English (Kenya)",
    "en-NZ-MitchellNeural": "Mitchell - English (New Zealand)", "en-NZ-MollyNeural": "Molly - English (New Zealand)",
    "en-NG-AbeoNeural": "Abeo - English (Nigeria)", "en-NG-EzinneNeural": "Ezinne - English (Nigeria)",
    "en-PH-James": "James - English (Philippines)", "en-PH-RosaNeural": "Rosa - English (Philippines)",
    "en-SG-LunaNeural": "Luna - English (Singapore)", "en-SG-WayneNeural": "Wayne - English (Singapore)",
    "en-ZA-LeahNeural": "Leah - English (South Africa)", "en-ZA-LukeNeural": "Luke - English (South Africa)",
    "en-TZ-ElimuNeural": "Elimu - English (Tanzania)", "en-TZ-ImaniNeural": "Imani - English (Tanzania)",
    "en-GB-LibbyNeural": "Libby - English (United Kingdom)", "en-GB-MaisieNeural": "Maisie - English (United Kingdom)",
    "en-GB-RyanNeural": "Ryan - English (United Kingdom)", "en-GB-SoniaNeural": "Sonia - English (United Kingdom)",
    "en-GB-ThomasNeural": "Thomas - English (United Kingdom)",
    "en-US-AriaNeural": "Aria - English (United States)", "en-US-AnaNeural": "Ana - English (United States)",
    "en-US-ChristopherNeural": "Christopher - English (United States)", "en-US-EricNeural": "Eric - English (United States)",
    "en-US-GuyNeural": "Guy - English (United States)", "en-US-JennyNeural": "Jenny - English (United States)",
    "en-US-MichelleNeural": "Michelle - English (United States)", "en-US-RogerNeural": "Roger - English (United States)",
    "en-US-SteffanNeural": "Steffan - English (United States)",
    "es-AR-ElenaNeural": "Elena - Spanish (Argentina)", "es-AR-TomasNeural": "Tomas - Spanish (Argentina)",
    "es-BO-MarceloNeural": "Marcelo - Spanish (Bolivia)", "es-BO-SofiaNeural": "Sofia - Spanish (Bolivia)",
    "es-CL-CatalinaNeural": "Catalina - Spanish (Chile)", "es-CL-LorenzoNeural": "Lorenzo - Spanish (Chile)",
    "es-CO-GonzaloNeural": "Gonzalo - Spanish (Colombia)", "es-CO-SalomeNeural": "Salome - Spanish (Colombia)",
    "es-CR-JuanNeural": "Juan - Spanish (Costa Rica)", "es-CR-MariaNeural": "Maria - Spanish (Costa Rica)",
    "es-CU-BelkysNeural": "Belkys - Spanish (Cuba)", "es-CU-ManuelNeural": "Manuel - Spanish (Cuba)",
    "es-DO-EmilioNeural": "Emilio - Spanish (Dominican Republic)", "es-DO-RamonaNeural": "Ramona - Spanish (Dominican Republic)",
    "es-EC-AndreaNeural": "Andrea - Spanish (Ecuador)", "es-EC-LorenaNeural": "Lorena - Spanish (Ecuador)",
    "es-SV-RodrigoNeural": "Rodrigo - Spanish (El Salvador)", "es-SV-LorenaNeural": "Lorena - Spanish (El Salvador)",
    "es-GQ-JavierNeural": "Javier - Spanish (Equatorial Guinea)", "es-GQ-TeresaNeural": "Teresa - Spanish (Equatorial Guinea)",
    "es-GT-AndresNeural": "Andres - Spanish (Guatemala)", "es-GT-MartaNeural": "Marta - Spanish (Guatemala)",
    "es-HN-CarlosNeural": "Carlos - Spanish (Honduras)", "es-HN-KarlaNeural": "Karla - Spanish (Honduras)",
    "es-MX-DaliaNeural": "Dalia - Spanish (Mexico)", "es-MX-JorgeNeural": "Jorge - Spanish (Mexico)",
    "es-NI-FedericoNeural": "Federico - Spanish (Nicaragua)", "es-NI-YolandaNeural": "Yolanda - Spanish (Nicaragua)",
    "es-PA-MargaritaNeural": "Margarita - Spanish (Panama)", "es-PA-RobertoNeural": "Roberto - Spanish (Panama)",
    "es-PY-MarioNeural": "Mario - Spanish (Paraguay)", "es-PY-TaniaNeural": "Tania - Spanish (Paraguay)",
    "es-PE-AlexNeural": "Alex - Spanish (Peru)", "es-PE-CamilaNeural": "Camila - Spanish (Peru)",
    "es-PR-KarinaNeural": "Karina - Spanish (Puerto Rico)", "es-PR-VictorNeural": "Victor - Spanish (Puerto Rico)",
    "es-ES-AlvaroNeural": "Alvaro - Spanish (Spain)", "es-ES-ElviraNeural": "Elvira - Spanish (Spain)",
    "es-US-AlonsoNeural": "Alonso - Spanish (United States)", "es-US-PalomaNeural": "Paloma - Spanish (United States)",
    "es-UY-MateoNeural": "Mateo - Spanish (Uruguay)", "es-UY-ValentinaNeural": "Valentina - Spanish (Uruguay)",
    "es-VE-PaolaNeural": "Paola - Spanish (Venezuela)", "es-VE-SebastianNeural": "Sebastian - Spanish (Venezuela)",
    "hi-IN-SwaraNeural": "Swara - Hindi (India)", "hi-IN-MadhurNeural": "Madhur - Hindi (India)",
    "fr-FR-DeniseNeural": "Denise - French (France)", "fr-FR-HenriNeural": "Henri - French (France)",
    "fr-CA-SylvieNeural": "Sylvie - French (Canada)", "fr-CA-JeanNeural": "Jean - French (Canada)",
    "fr-CH-ArianeNeural": "Ariane - French (Switzerland)", "fr-CH-FabriceNeural": "Fabrice - French (Switzerland)",
    "fr-CH-GerardNeural": "Gerard - French (Switzerland)",
    "de-DE-KatjaNeural": "Katja - German (Germany)", "de-DE-ConradNeural": "Conrad - German (Germany)",
    "de-CH-LeniNeural": "Leni - German (Switzerland)", "de-CH-JanNeural": "Jan - German (Switzerland)",
    "de-AT-IngridNeural": "Ingrid - German (Austria)", "de-AT-JonasNeural": "Jonas - German (Austria)",
    "zh-CN-XiaoxiaoNeural": "Xiaoxiao - Chinese (Mandarin, Simplified)",
    "zh-CN-YunyangNeural": "Yunyang - Chinese (Mandarin, Simplified)",
    "zh-CN-YunjianNeural": "Yunjian - Chinese (Mandarin, Simplified)",
    "zh-TW-HsiaoChenNeural": "HsiaoChen - Chinese (Taiwan)", "zh-TW-YunJheNeural": "YunJhe - Chinese (Taiwan)",
    "zh-HK-HiuMaanNeural": "HiuMaan - Chinese (Hong Kong)", "zh-HK-WanLungNeural": "WanLung - Chinese (Hong Kong)",
    "ja-JP-NanamiNeural": "Nanami - Japanese (Japan)", "ja-JP-KeitaNeural": "Keita - Japanese (Japan)",
    "pt-BR-FranciscaNeural": "Francisca - Portuguese (Brazil)", "pt-BR-AntonioNeural": "Antonio - Portuguese (Brazil)",
    "pt-PT-RaquelNeural": "Raquel - Portuguese (Portugal)", "pt-PT-DuarteNeural": "Duarte - Portuguese (Portugal)",
    "ru-RU-SvetlanaNeural": "Svetlana - Russian (Russia)", "ru-RU-DmitryNeural": "Dmitry - Russian (Russia)",
    "ru-RU-LarisaNeural": "Larisa - Russian (Russia)", "ru-RU-MaximNeural": "Maxim - Russian (Russia)",
    "tr-TR-EmelNeural": "Emel - Turkish (Turkey)", "tr-TR-AhmetNeural": "Ahmet - Turkish (Turkey)",
    "ko-KR-SunHiNeural": "SunHi - Korean (Korea)", "ko-KR-InJoonNeural": "InJoon - Korean (Korea)",
    "it-IT-ElsaNeural": "Elsa - Italian (Italy)", "it-IT-DiegoNeural": "Diego - Italian (Italy)",
    "id-ID-GadisNeural": "Gadis - Indonesian (Indonesia)", "id-ID-ArdiNeural": "Ardi - Indonesian (Indonesia)",
    "vi-VN-HoaiMyNeural": "HoaiMy - Vietnamese (Vietnam)", "vi-VN-NamMinhNeural": "NamMinh - Vietnamese (Vietnam)",
    "th-TH-PremwadeeNeural": "Premwadee - Thai (Thailand)", "th-TH-NiwatNeural": "Niwat - Thai (Thailand)",
    "nl-NL-ColetteNeural": "Colette - Dutch (Netherlands)", "nl-NL-MaartenNeural": "Maarten - Dutch (Netherlands)",
    "pl-PL-ZofiaNeural": "Zofia - Polish (Poland)", "pl-PL-MarekNeural": "Marek - Polish (Poland)",
    "sv-SE-SofieNeural": "Sofie - Swedish (Sweden)", "sv-SE-MattiasNeural": "Mattias - Swedish (Sweden)",
    "fil-PH-BlessicaNeural": "Blessica - Filipino (Philippines)", "fil-PH-AngeloNeural": "Angelo - Filipino (Philippines)",
    "el-GR-AthinaNeural": "Athina - Greek (Greece)", "el-GR-NestorasNeural": "Nestoras - Greek (Greece)",
    "he-IL-AvriNeural": "Avri - Hebrew (Israel)", "he-IL-HilaNeural": "Hila - Hebrew (Israel)",
    "hu-HU-NoemiNeural": "Noemi - Hungarian (Hungary)", "hu-HU-AndrasNeural": "Andras - Hungarian (Hungary)",
    "cs-CZ-VlastaNeural": "Vlasta - Czech (Czech Republic)", "cs-CZ-AntoninNeural": "Antonin - Czech (Czech Republic)",
    "da-DK-ChristelNeural": "Christel - Danish (Denmark)", "da-DK-JeppeNeural": "Jeppe - Danish (Denmark)",
    "fi-FI-SelmaNeural": "Selma - Finnish (Finland)", "fi-FI-HarriNeural": "Harri - Finnish (Finland)",
    "nb-NO-PernilleNeural": "Pernille - Norwegian Bokmål (Norway)", "nb-NO-FinnNeural": "Finn - Norwegian Bokmål (Norway)",
    "ro-RO-AlinaNeural": "Alina - Romanian (Romania)", "ro-RO-EmilNeural": "Emil - Romanian (Romania)",
    "sk-SK-LukasNeural": "Lukas - Slovak (Slovakia)", "sk-SK-ViktoriaNeural": "Viktoria - Slovak (Slovakia)",
    "uk-UA-PolinaNeural": "Polina - Ukrainian (Ukraine)", "uk-UA-OstapNeural": "Ostap - Ukrainian (Ukraine)",
    "ms-MY-YasminNeural": "Yasmin - Malay (Malaysia)", "ms-MY-OsmanNeural": "Osman - Malay (Malaysia)",
    "bn-BD-NabanitaNeural": "Nabanita - Bengali (Bangladesh)", "bn-BD-BasharNeural": "Bashar - Bengali (Bangladesh)",
    "ur-PK-AsmaNeural": "Asma - Urdu (Pakistan)", "ur-PK-FaizanNeural": "Faizan - Urdu (Pakistan)",
    "ne-NP-SagarNeural": "Sagar - Nepali (Nepal)", "ne-NP-HemkalaNeural": "Hemkala - Nepali (Nepal)",
    "si-LK-SameeraNeural": "Sameera - Sinhala (Sri Lanka)", "si-LK-ThiliniNeural": "Thilini - Sinhala (Sri Lanka)",
    "lo-LA-ChanthavongNeural": "Chanthavong - Lao (Laos)", "lo-LA-KeomanyNeural": "Keomany - Lao (Laos)",
    "my-MM-NilarNeural": "Nilar - Burmese (Myanmar)", "my-MM-ThihaNeural": "Thiha - Burmese (Myanmar)",
    "ka-GE-EkaNeural": "Eka - Georgian (Georgia)", "ka-GE-GiorgiNeural": "Giorgi - Georgian (Georgia)",
    "hy-AM-AnahitNeural": "Anahit - Armenian (Armenia)", "hy-AM-AraratNeural": "Ararat - Armenian (Armenia)",
    "az-AZ-BabekNeural": "Babek - Azerbaijani (Azerbaijan)", "az-AZ-BanuNeural": "Banu - Azerbaijani (Azerbaijan)",
    "uz-UZ-MadinaNeural": "Madina - Uzbek (Uzbekistan)", "uz-UZ-SuhrobNeural": "Suhrob - Uzbek (Uzbekistan)",
    "sr-RS-NikolaNeural": "Nikola - Serbian (Serbia)", "sr-RS-SophieNeural": "Sophie - Serbian (Serbia)",
    "hr-HR-GabrijelaNeural": "Gabrijela - Croatian (Croatia)", "hr-HR-SreckoNeural": "Srecko - Croatian (Croatia)",
    "sl-SI-PetraNeural": "Petra - Slovenian (Slovenia)", "sl-SI-RokNeural": "Rok - Slovenian (Slovenia)",
    "lv-LV-EveritaNeural": "Everita - Latvian (Latvia)", "lv-LV-AnsisNeural": "Ansis - Latvian (Latvia)",
    "lt-LT-OnaNeural": "Ona - Lithuanian (Lithuania)", "lt-LT-LeonasNeural": "Leonas - Lithuanian (Lithuania)",
    "am-ET-MekdesNeural": "Mekdes - Amharic (Ethiopia)", "am-ET-AbebeNeural": "Abebe - Amharic (Ethiopia)",
    "sw-KE-ZuriNeural": "Zuri - Swahili (Kenya)", "sw-KE-RafikiNeural": "Rafiki - Swahili (Kenya)",
    "zu-ZA-ThandoNeural": "Thando - Zulu (South Africa)", "zu-ZA-ThembaNeural": "Themba - Zulu (South Africa)",
    "af-ZA-AdriNeural": "Adri - Afrikaans (South Africa)", "af-ZA-WillemNeural": "Willem - Afrikaans (South Africa)",
    "so-SO-UbaxNeural": "Ubax - Somali (Somalia)", "so-SO-MuuseNeural": "Muuse - Somali (Somalia)",
    "fa-IR-DilaraNeural": "Dilara - Persian (Iran)", "fa-IR-ImanNeural": "Iman - Persian (Iran)",
    "mn-MN-BataaNeural": "Bataa - Mongolian (Mongolia)", "mn-MN-YesuiNeural": "Yesui - Mongolian (Mongolia)",
    "mt-MT-GraceNeural": "Grace - Maltese (Malta)", "mt-MT-JosephNeural": "Joseph - Maltese (Malta)",
    "ga-IE-ColmNeural": "Colm - Irish (Ireland)", "ga-IE-OrlaNeural": "Orla - Irish (Ireland)",
    "sq-AL-AnilaNeural": "Anila - Albanian (Albania)", "sq-AL-IlirNeural": "Ilir - Albanian (Albania)"
}

def check_db_connection():
    try:
        client.admin.command('ismaster')
        logging.info("MongoDB connection successful.")
        return True
    except ConnectionFailure:
        logging.error("MongoDB connection failed.")
        return False

def init_in_memory_data():
    logging.info("Initializing in-memory data structures from MongoDB.")
    try:
        all_users = users_collection.find()
        for user in all_users:
            in_memory_data["users"][user["_id"]] = user
        all_tts_settings = tts_settings_collection.find()
        for setting in all_tts_settings:
            in_memory_data["tts_settings"][setting["_id"]] = setting
        all_stt_settings = stt_settings_collection.find()
        for setting in all_stt_settings:
            in_memory_data["stt_settings"][setting["_id"]] = setting
    except OperationFailure as e:
        logging.error(f"Failed to load data from MongoDB: {e}")

def update_user_activity_in_memory(user_id: int):
    user_id_str = str(user_id)
    now = datetime.now()
    user_data = in_memory_data["users"].get(user_id_str, {
        "_id": user_id_str, "first_seen": now, "tts_conversion_count": 0, "stt_conversion_count": 0,
    })
    user_data["last_active"] = now
    in_memory_data["users"][user_id_str] = user_data
    users_collection.update_one({"_id": user_id_str}, {"$set": {"last_active": now}}, upsert=True)

def get_user_data_in_memory(user_id: str) -> dict | None:
    user_data = in_memory_data["users"].get(user_id)
    if user_data:
        return user_data
    db_user = users_collection.find_one({"_id": user_id})
    if db_user:
        in_memory_data["users"][user_id] = db_user
    return db_user

def increment_processing_count_in_memory(user_id: str, service_type: str):
    user_id_str = str(user_id)
    now = datetime.now()
    user_data = in_memory_data["users"].get(user_id_str, {
        "_id": user_id_str, "first_seen": now, "tts_conversion_count": 0, "stt_conversion_count": 0,
    })
    field_to_inc = f"{service_type}_conversion_count"
    user_data[field_to_inc] = user_data.get(field_to_inc, 0) + 1
    user_data["last_active"] = now
    in_memory_data["users"][user_id_str] = user_data
    users_collection.update_one(
        {"_id": user_id_str}, {"$inc": {field_to_inc: 1}, "$set": {"last_active": now}}, upsert=True
    )

def get_tts_user_voice_in_memory(user_id: str) -> str:
    setting = in_memory_data["tts_settings"].get(user_id)
    if setting:
        return setting.get("voice", "en-US-EricNeural")
    db_setting = tts_settings_collection.find_one({"_id": user_id})
    if db_setting:
        in_memory_data["tts_settings"][user_id] = db_setting
        return db_setting.get("voice", "en-US-EricNeural")
    return "en-US-EricNeural"

def set_tts_user_voice_in_memory(user_id: str, voice: str):
    if user_id not in in_memory_data["tts_settings"]:
        in_memory_data["tts_settings"][user_id] = {}
    in_memory_data["tts_settings"][user_id]["voice"] = voice
    tts_settings_collection.update_one({"_id": user_id}, {"$set": {"voice": voice}}, upsert=True)

def get_tts_user_pitch_in_memory(user_id: str) -> int:
    setting = in_memory_data["tts_settings"].get(user_id)
    if setting:
        return setting.get("pitch", 0)
    db_setting = tts_settings_collection.find_one({"_id": user_id})
    if db_setting:
        in_memory_data["tts_settings"][user_id] = db_setting
        return db_setting.get("pitch", 0)
    return 0

def set_tts_user_pitch_in_memory(user_id: str, pitch: int):
    if user_id not in in_memory_data["tts_settings"]:
        in_memory_data["tts_settings"][user_id] = {}
    in_memory_data["tts_settings"][user_id]["pitch"] = pitch
    tts_settings_collection.update_one({"_id": user_id}, {"$set": {"pitch": pitch}}, upsert=True)

def get_tts_user_rate_in_memory(user_id: str) -> int:
    setting = in_memory_data["tts_settings"].get(user_id)
    if setting:
        return setting.get("rate", 0)
    db_setting = tts_settings_collection.find_one({"_id": user_id})
    if db_setting:
        in_memory_data["tts_settings"][user_id] = db_setting
        return db_setting.get("rate", 0)
    return 0

def set_tts_user_rate_in_memory(user_id: str, rate: int):
    if user_id not in in_memory_data["tts_settings"]:
        in_memory_data["tts_settings"][user_id] = {}
    in_memory_data["tts_settings"][user_id]["rate"] = rate
    tts_settings_collection.update_one({"_id": user_id}, {"$set": {"rate": rate}}, upsert=True)

def get_stt_user_lang_in_memory(user_id: str) -> str:
    setting = in_memory_data["stt_settings"].get(user_id)
    if setting:
        return setting.get("language_code", "en")
    db_setting = stt_settings_collection.find_one({"_id": user_id})
    if db_setting:
        in_memory_data["stt_settings"][user_id] = db_setting
        return db_setting.get("language_code", "en")
    return "en"

def set_stt_user_lang_in_memory(user_id: str, lang_code: str):
    if user_id not in in_memory_data["stt_settings"]:
        in_memory_data["stt_settings"][user_id] = {}
    in_memory_data["stt_settings"][user_id]["language_code"] = lang_code
    stt_settings_collection.update_one({"_id": user_id}, {"$set": {"language_code": lang_code}}, upsert=True)

def keep_recording(chat_id, stop_event, target_bot):
    while not stop_event.is_set():
        try:
            target_bot.send_chat_action(chat_id, 'record_audio')
            time.sleep(4)
        except Exception as e:
            logging.error(f"Error sending record_audio action: {e}")
            break

def check_subscription(user_id: int) -> bool:
    if not REQUIRED_CHANNEL:
        return True
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except telebot.apihelper.ApiTelegramException as e:
        logging.error(f"Error checking subscription: {e}")
        return False

def send_subscription_message(chat_id: int):
    if bot.get_chat(chat_id).type == 'private' and REQUIRED_CHANNEL:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Click here to join the group ", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}"))
        bot.send_message(chat_id, "🔒 Access Restricted\n\nPlease join our group to use this bot.\n\nJoin and send /start again.", reply_markup=markup)

def create_main_reply_keyboard():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(KeyboardButton("⚙️ Settings"), KeyboardButton("❓ Help"))
    return markup

def create_settings_reply_keyboard():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(KeyboardButton("Choose Voice"), KeyboardButton("Pitch"), KeyboardButton("Rate"), KeyboardButton("STT Lang"), KeyboardButton("Main Menu"))
    return markup

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id_str = str(message.from_user.id)
    user_first_name = message.from_user.first_name or "User"
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.from_user.id):
        send_subscription_message(message.chat.id)
        return
    user_tts_mode[user_id_str] = None
    user_pitch_input_mode[user_id_str] = None
    user_rate_input_mode[user_id_str] = None
    if message.from_user.id == ADMIN_ID:
        admin_markup = InlineKeyboardMarkup()
        admin_markup.add(InlineKeyboardButton("Send Broadcast", callback_data="admin_broadcast"), InlineKeyboardButton("Total Users", callback_data="admin_total_users"))
        bot.send_message(message.chat.id, "Welcome to the Admin Panel! Choose an action:", reply_markup=admin_markup)
    else:
        welcome_message = (
            f"👋 Hello {user_first_name}! I am - your AI voice assistant that helps you convert text to audio or audio to text - for free! 🔊✍️\n\n"
            "✨ **Here's how to use it:**\n"
            "1. **Convert Text to Audio (TTS):**\n"
            "   - Choose the voice (by pressing `Choose Voice` from Settings)\n"
            "   - Adjust your voice (by pressing `Pitch` or `Rate` from Settings)\n"
            "   - Send me text, I will convert it to audio!\n\n"
            "2. **Convert Audio to Text (STT):**\n"
            "   - Choose the language (by pressing `STT Lang` from Settings)\n"
            "   - Send me audio, video or file (up to 20MB)\n\n"
            "👉 You can also add me to your chats - click https://t.me/mediatotextbot?startgroup=!"
        )
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton(" Add to your Groups", url="https://t.me/mediatotextbot?startgroup="))
        bot.send_message(message.chat.id, welcome_message, reply_markup=create_main_reply_keyboard(), parse_mode="Markdown")
    
@bot.message_handler(func=lambda message: message.text == "❓ Help")
@bot.message_handler(commands=['help'])
def help_handler(message):
    user_id = str(message.from_user.id)
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.from_user.id):
        send_subscription_message(message.chat.id)
        return
    user_tts_mode[user_id] = None
    user_pitch_input_mode[user_id] = None
    user_rate_input_mode[user_id] = None
    help_text = (
        "📖 **How to use This Bot?**\n\n"
        "This bot makes it easy to convert text to audio or audio/video to text. Here's how it works:\n\n"
        "⸻\n"
        "**1. Convert Text to Audio (TTS):**\n"
        "• **Choose Voice:** Use the `Choose Voice` button to select the language and voice you want,\n"
        "• **Send your Text:** Once you choose the voice, any text you send me will be returned as audio,\n"
        "• **Adjust Voice:**\n"
        "  • Use `Pitch` to increase or decrease the pitch,\n"
        "  • Use `Rate` to speed up or slow down the speech,\n\n"
        "⸻\n"
        "**2. Convert Audio to Text (STT):**\n"
        "• **Choose Language:** Use `STT Lang` to specify the language of the audio or video you are sending – this helps with accuracy,\n"
        "• **Send Audio/Video:** Send me an audio message, audio file or video (up to 20MB),\n\n"
        "⸻\n"
        "**3. Your Data & Privacy:**\n"
        "• **Your Data is Private:** The text and audio you send are not saved – they are used temporarily,\n"
        "• **Your preferences are saved:** The voice, pitch, and rate you choose are saved until the bot restarts.\n\n"
        "👉 Questions or problems? Contact @kookabeela\n\n"
        "Enjoy creating and writing! ✨"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['privacy'])
def privacy_notice_handler(message):
    user_id = str(message.from_user.id)
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.chat.id):
        send_subscription_message(message.chat.id)
        return
    user_tts_mode[user_id] = None
    user_pitch_input_mode[user_id] = None
    user_rate_input_mode[user_id] = None
    privacy_text = (
        "🔐 **Privacy Notice**\n\n"
        "If you have any questions or concerns about your privacy, please feel free to contact the bot administrator @user33230."
    )
    bot.send_message(message.chat.id, privacy_text, parse_mode="Markdown")

@bot.message_handler(commands=['commands'])
def handle_commands_command(message):
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.from_user.id):
        send_subscription_message(message.chat.id)
        return
    bot.send_message(message.chat.id, "The request you sent is currently unavailable.")

@bot.callback_query_handler(lambda c: c.data in ["admin_total_users", "admin_broadcast"] and c.from_user.id == ADMIN_ID)
def admin_menu_callback(call):
    chat_id = call.message.chat.id
    if call.data == "admin_total_users":
        total_registered = users_collection.count_documents({})
        bot.send_message(chat_id, f"Total registered users (from database): {total_registered}")
    elif call.data == "admin_broadcast":
        admin_state[call.from_user.id] = 'awaiting_broadcast_message'
        bot.send_message(chat_id, "Send the broadcast message now:")
    bot.answer_callback_query(call.id)

@bot.message_handler(
    func=lambda m: m.from_user.id == ADMIN_ID and admin_state.get(m.from_user.id) == 'awaiting_broadcast_message',
    content_types=['text', 'photo', 'video', 'audio', 'document']
)
def broadcast_message(message):
    admin_state[message.from_user.id] = None
    success = fail = 0
    all_users_from_db = users_collection.find()
    for user_doc in all_users_from_db:
        uid = user_doc["_id"]
        if uid == str(ADMIN_ID):
            continue
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
        except telebot.apihelper.ApiTelegramException as e:
            logging.error(f"Failed to send broadcast to {uid}: {e}")
            fail += 1
        time.sleep(0.05)
    bot.send_message(message.chat.id, f"Broadcast complete.\nSuccessful: {success}\nFailed: {fail}")

TTS_VOICES_BY_LANGUAGE = {
    "Arabic": ["ar-DZ-AminaNeural", "ar-DZ-IsmaelNeural", "ar-BH-AliNeural", "ar-BH-LailaNeural", "ar-EG-SalmaNeural", "ar-EG-ShakirNeural", "ar-IQ-BasselNeural", "ar-IQ-RanaNeural", "ar-JO-SanaNeural", "ar-JO-TaimNeural", "ar-KW-FahedNeural", "ar-KW-NouraNeural", "ar-LB-LaylaNeural", "ar-LB-RamiNeural", "ar-LY-ImanNeural", "ar-LY-OmarNeural", "ar-MA-JamalNeural", "ar-MA-MounaNeural", "ar-OM-AbdullahNeural", "ar-OM-AyshaNeural", "ar-QA-AmalNeural", "ar-QA-MoazNeural", "ar-SA-HamedNeural", "ar-SA-ZariyahNeural", "ar-SY-AmanyNeural", "ar-SY-LaithNeural", "ar-TN-HediNeural", "ar-TN-ReemNeural", "ar-AE-FatimaNeural", "ar-AE-HamdanNeural", "ar-YE-MaryamNeural", "ar-YE-SalehNeural"],
    "English": ["en-AU-NatashaNeural", "en-AU-WilliamNeural", "en-CA-ClaraNeural", "en-CA-LiamNeural", "en-HK-SamNeural", "en-HK-YanNeural", "en-IN-NeerjaNeural", "en-IN-PrabhatNeural", "en-IE-ConnorNeural", "en-IE-EmilyNeural", "en-KE-AsiliaNeural", "en-KE-ChilembaNeural", "en-NZ-MitchellNeural", "en-NZ-MollyNeural", "en-NG-AbeoNeural", "en-NG-EzinneNeural", "en-PH-James", "en-PH-RosaNeural", "en-SG-LunaNeural", "en-SG-WayneNeural", "en-ZA-LeahNeural", "en-ZA-LukeNeural", "en-TZ-ElimuNeural", "en-TZ-ImaniNeural", "en-GB-LibbyNeural", "en-GB-MaisieNeural", "en-GB-RyanNeural", "en-GB-SoniaNeural", "en-GB-ThomasNeural", "en-US-AriaNeural", "en-US-AnaNeural", "en-US-ChristopherNeural", "en-US-EricNeural", "en-US-GuyNeural", "en-US-JennyNeural", "en-US-MichelleNeural", "en-US-RogerNeural", "en-US-SteffanNeural"],
    "Spanish": ["es-AR-ElenaNeural", "es-AR-TomasNeural", "es-BO-MarceloNeural", "es-BO-SofiaNeural", "es-CL-CatalinaNeural", "es-CL-LorenzoNeural", "es-CO-GonzaloNeural", "es-CO-SalomeNeural", "es-CR-JuanNeural", "es-CR-MariaNeural", "es-CU-BelkysNeural", "es-CU-ManuelNeural", "es-DO-EmilioNeural", "es-DO-RamonaNeural", "es-EC-AndreaNeural", "es-EC-LorenaNeural", "es-SV-RodrigoNeural", "es-SV-LorenaNeural", "es-GQ-JavierNeural", "es-GQ-TeresaNeural", "es-GT-AndresNeural", "es-GT-MartaNeural", "es-HN-CarlosNeural", "es-HN-KarlaNeural", "es-MX-DaliaNeural", "es-MX-JorgeNeural", "es-NI-FedericoNeural", "es-NI-YolandaNeural", "es-PA-MargaritaNeural", "es-PA-RobertoNeural", "es-PY-MarioNeural", "es-PY-TaniaNeural", "es-PE-AlexNeural", "es-PE-CamilaNeural", "es-PR-KarinaNeural", "es-PR-VictorNeural", "es-ES-AlvaroNeural", "es-ES-ElviraNeural", "es-US-AlonsoNeural", "es-US-PalomaNeural", "es-UY-MateoNeural", "es-UY-ValentinaNeural", "es-VE-PaolaNeural", "es-VE-SebastianNeural"],
    "Hindi": ["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"],
    "French": ["fr-FR-DeniseNeural", "fr-FR-HenriNeural", "fr-CA-SylvieNeural", "fr-CA-JeanNeural", "fr-CH-ArianeNeural", "fr-CH-FabriceNeural", "fr-CH-GerardNeural"],
    "German": ["de-DE-KatjaNeural", "de-DE-ConradNeural", "de-CH-LeniNeural", "de-CH-JanNeural", "de-AT-IngridNeural", "de-AT-JonasNeural"],
    "Chinese": ["zh-CN-XiaoxiaoNeural", "zh-CN-YunyangNeural", "zh-CN-YunjianNeural", "zh-TW-HsiaoChenNeural", "zh-TW-YunJheNeural", "zh-HK-HiuMaanNeural", "zh-HK-WanLungNeural"],
    "Japanese": ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"],
    "Portuguese": ["pt-BR-FranciscaNeural", "pt-BR-AntonioNeural", "pt-PT-RaquelNeural", "pt-PT-DuarteNeural"],
    "Russian": ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural", "ru-RU-LarisaNeural", "ru-RU-MaximNeural"],
    "Turkish": ["tr-TR-EmelNeural", "tr-TR-AhmetNeural"],
    "Korean": ["ko-KR-SunHiNeural", "ko-KR-InJoonNeural"],
    "Italian": ["it-IT-ElsaNeural", "it-IT-DiegoNeural"],
    "Indonesian": ["id-ID-GadisNeural", "id-ID-ArdiNeural"],
    "Vietnamese": ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"],
    "Thai": ["th-TH-PremwadeeNeural", "th-TH-NiwatNeural"],
    "Dutch": ["nl-NL-ColetteNeural", "nl-NL-MaartenNeural"],
    "Polish": ["pl-PL-ZofiaNeural", "pl-PL-MarekNeural"],
    "Swedish": ["sv-SE-SofieNeural", "sv-SE-MattiasNeural"],
    "Filipino": ["fil-PH-BlessicaNeural", "fil-PH-AngeloNeural"],
    "Greek": ["el-GR-AthinaNeural", "el-GR-NestorasNeural"],
    "Hebrew": ["he-IL-AvriNeural", "he-IL-HilaNeural"],
    "Hungarian": ["hu-HU-NoemiNeural", "hu-HU-AndrasNeural"],
    "Czech": ["cs-CZ-VlastaNeural", "cs-CZ-AntoninNeural"],
    "Danish": ["da-DK-ChristelNeural", "da-DK-JeppeNeural"],
    "Finnish": ["fi-FI-SelmaNeural", "fi-FI-HarriNeural"],
    "Norwegian": ["nb-NO-PernilleNeural", "nb-NO-FinnNeural"],
    "Romanian": ["ro-RO-AlinaNeural", "ro-RO-EmilNeural"],
    "Slovak": ["sk-SK-LukasNeural", "sk-SK-ViktoriaNeural"],
    "Ukrainian": ["uk-UA-PolinaNeural", "uk-UA-OstapNeural"],
    "Malay": ["ms-MY-YasminNeural", "ms-MY-OsmanNeural"],
    "Bengali": ["bn-BD-NabanitaNeural", "bn-BD-BasharNeural"],
    "Urdu": ["ur-PK-AsmaNeural", "ur-PK-FaizanNeural"],
    "Nepali": ["ne-NP-SagarNeural", "ne-NP-HemkalaNeural"],
    "Sinhala": ["si-LK-SameeraNeural", "si-LK-ThiliniNeural"],
    "Lao": ["lo-LA-ChanthavongNeural", "lo-LA-KeomanyNeural"],
    "Myanmar": ["my-MM-NilarNeural", "my-MM-ThihaNeural"],
    "Georgian": ["ka-GE-EkaNeural", "ka-GE-GiorgiNeural"],
    "Armenian": ["hy-AM-AnahitNeural", "hy-AM-AraratNeural"],
    "Azerbaijani": ["az-AZ-BabekNeural", "az-AZ-BanuNeural"],
    "Uzbek": ["uz-UZ-MadinaNeural", "uz-UZ-SuhrobNeural"],
    "Serbian": ["sr-RS-NikolaNeural", "sr-RS-SophieNeural"],
    "Croatian": ["hr-HR-GabrijelaNeural", "hr-HR-SreckoNeural"],
    "Slovenian": ["sl-SI-PetraNeural", "sl-SI-RokNeural"],
    "Latvian": ["lv-LV-EveritaNeural", "lv-LV-AnsisNeural"],
    "Lithuanian": ["lt-LT-OnaNeural", "lt-LT-LeonasNeural"],
    "Amharic": ["am-ET-MekdesNeural", "am-ET-AbebeNeural"],
    "Swahili": ["sw-KE-ZuriNeural", "sw-KE-RafikiNeural"],
    "Zulu": ["zu-ZA-ThandoNeural", "zu-ZA-ThembaNeural"],
    "Afrikaans": ["af-ZA-AdriNeural", "af-ZA-WillemNeural"],
    "Somali": ["so-SO-UbaxNeural", "so-SO-MuuseNeural"],
    "Persian": ["fa-IR-DilaraNeural", "fa-IR-ImanNeural"],
    "Mongolian": ["mn-MN-BataaNeural", "mn-MN-YesuiNeural"],
    "Maltese": ["mt-MT-GraceNeural", "mt-MT-JosephNeural"],
    "Irish": ["ga-IE-ColmNeural", "ga-IE-OrlaNeural"],
    "Albanian": ["sq-AL-AnilaNeural", "sq-AL-IlirNeural"]
}

ORDERED_TTS_LANGUAGES = [
    "English", "Arabic", "Spanish", "French", "German", "Chinese", "Japanese", "Portuguese", "Russian", "Turkish",
    "Hindi", "Somali", "Italian", "Indonesian", "Vietnamese", "Thai", "Korean", "Dutch", "Polish", "Swedish",
    "Filipino", "Greek", "Hebrew", "Hungarian", "Czech", "Danish", "Finnish", "Norwegian", "Romanian", "Slovak",
    "Ukrainian", "Malay", "Bengali", "Urdu", "Nepali", "Sinhala", "Lao", "Myanmar", "Georgian", "Armenian",
    "Azerbaijani", "Uzbek", "Serbian", "Croatian", "Slovenian", "Latvian", "Lithuanian", "Amharic", "Swahili", "Zulu",
    "Afrikaans", "Persian", "Mongolian", "Maltese", "Irish", "Albanian"
]

def make_tts_language_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(lang_name, callback_data=f"tts_lang|{lang_name}") for lang_name in ORDERED_TTS_LANGUAGES if lang_name in TTS_VOICES_BY_LANGUAGE]
    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i+3])
    return markup

def make_tts_voice_keyboard_for_language(lang_name: str):
    markup = InlineKeyboardMarkup(row_width=2)
    voices = TTS_VOICES_BY_LANGUAGE.get(lang_name, [])
    for voice in voices:
        display_name = VOICE_MAPPING.get(voice, voice)
        markup.add(InlineKeyboardButton(display_name, callback_data=f"tts_voice|{voice}"))
    markup.add(InlineKeyboardButton("⬅️ Back", callback_data="tts_back_to_languages"))
    return markup

def make_pitch_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("⬆️ High", callback_data="pitch_set|+50"), InlineKeyboardButton("⬇️ Lower", callback_data="pitch_set|-50"), InlineKeyboardButton("🔄 Reset", callback_data="pitch_set|0"))
    return markup

def make_rate_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("⚡️ speed", callback_data="rate_set|+50"), InlineKeyboardButton("🐢 Slow down", callback_data="rate_set|-50"), InlineKeyboardButton("🔄 Reset", callback_data="rate_set|0"))
    return markup

def handle_rate_command(message, target_bot: telebot.TeleBot, user_id_for_settings: str):
    chat_id = message.chat.id
    user_tts_mode[user_id_for_settings] = None
    user_pitch_input_mode[user_id_for_settings] = None
    user_rate_input_mode[user_id_for_settings] = "awaiting_rate_input"
    target_bot.send_message(chat_id, "How fast or slow should I speak? Choose one or send a number from -100 (slow) to +100 (fast), 0 is normal:", reply_markup=make_rate_keyboard())

def handle_rate_callback(call, target_bot: telebot.TeleBot, user_id_for_settings: str):
    chat_id = call.message.chat.id
    user_rate_input_mode[user_id_for_settings] = None
    try:
        _, rate_value_str = call.data.split("|", 1)
        rate_value = int(rate_value_str)
        set_tts_user_rate_in_memory(user_id_for_settings, rate_value)
        target_bot.answer_callback_query(call.id, f"The rate is {rate_value}!")
        target_bot.edit_message_text(
            chat_id=chat_id, message_id=call.message.message_id,
            text=f"🔊 Speech rate is *{rate_value}*.\n\nReady for text? Or use `Choose Voice` to change the voice.",
            parse_mode="Markdown", reply_markup=None
        )
    except ValueError:
        target_bot.answer_callback_query(call.id, "Invalid rate.")
    except Exception as e:
        logging.error(f"Error setting rate: {e}")
        target_bot.answer_callback_query(call.id, "An error occurred.")

@bot.message_handler(func=lambda message: message.text == "Rate")
@bot.message_handler(commands=['rate'])
def cmd_voice_rate(message):
    uid = str(message.from_user.id)
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.chat.id):
        send_subscription_message(message.chat.id)
        return
    handle_rate_command(message, bot, uid)

@bot.callback_query_handler(lambda c: c.data.startswith("rate_set|"))
def on_rate_set_callback(call):
    uid = str(call.from_user.id)
    update_user_activity_in_memory(call.from_user.id)
    if call.message.chat.type == 'private' and str(call.from_user.id) != str(ADMIN_ID) and not check_subscription(call.message.chat.id):
        send_subscription_message(call.message.chat.id)
        bot.answer_callback_query(call.id)
        return
    handle_rate_callback(call, bot, uid)

def handle_pitch_command(message, target_bot: telebot.TeleBot, user_id_for_settings: str):
    chat_id = message.chat.id
    user_tts_mode[user_id_for_settings] = None
    user_pitch_input_mode[user_id_for_settings] = "awaiting_pitch_input"
    user_rate_input_mode[user_id_for_settings] = None
    target_bot.send_message(chat_id, "Let's adjust the pitch! Choose one or send a number from -100 (low) to +100 (high), 0 is normal:", reply_markup=make_pitch_keyboard())

def handle_pitch_callback(call, target_bot: telebot.TeleBot, user_id_for_settings: str):
    chat_id = call.message.chat.id
    user_pitch_input_mode[user_id_for_settings] = None
    try:
        _, pitch_value_str = call.data.split("|", 1)
        pitch_value = int(pitch_value_str)
        set_tts_user_pitch_in_memory(user_id_for_settings, pitch_value)
        target_bot.answer_callback_query(call.id, f"The pitch is {pitch_value}!")
        target_bot.edit_message_text(
            chat_id=chat_id, message_id=call.message.message_id,
            text=f"🔊 The pitch is *{pitch_value}*.\n\nReady for text? Or use `Choose Voice` to change the voice.",
            parse_mode="Markdown", reply_markup=None
        )
    except ValueError:
        target_bot.answer_callback_query(call.id, "Invalid pitch.")
    except Exception as e:
        logging.error(f"Error setting pitch: {e}")
        target_bot.answer_callback_query(call.id, "An error occurred.")

@bot.message_handler(func=lambda message: message.text == "Pitch")
@bot.message_handler(commands=['pitch'])
def cmd_voice_pitch(message):
    uid = str(message.from_user.id)
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.chat.id):
        send_subscription_message(message.chat.id)
        return
    handle_pitch_command(message, bot, uid)

@bot.callback_query_handler(lambda c: c.data.startswith("pitch_set|"))
def on_pitch_set_callback(call):
    uid = str(call.from_user.id)
    update_user_activity_in_memory(call.from_user.id)
    if call.message.chat.type == 'private' and str(call.from_user.id) != str(ADMIN_ID) and not check_subscription(call.message.chat.id):
        send_subscription_message(call.message.chat.id)
        bot.answer_callback_query(call.id)
        return
    handle_pitch_callback(call, bot, uid)

def handle_voice_command(message, target_bot: telebot.TeleBot, user_id_for_settings: str):
    chat_id = message.chat.id
    user_tts_mode[user_id_for_settings] = None
    user_pitch_input_mode[user_id_for_settings] = None
    user_rate_input_mode[user_id_for_settings] = None
    target_bot.send_message(chat_id, "First, choose the *language* of your voice. 👇", reply_markup=make_tts_language_keyboard(), parse_mode="Markdown")

def handle_tts_language_select_callback(call, target_bot: telebot.TeleBot, user_id_for_settings: str):
    chat_id = call.message.chat.id
    user_pitch_input_mode[user_id_for_settings] = None
    user_rate_input_mode[user_id_for_settings] = None
    _, lang_name = call.data.split("|", 1)
    target_bot.edit_message_text(
        chat_id=chat_id, message_id=call.message.message_id,
        text=f"Okay! Now choose a specific *voice* from {lang_name}. 👇",
        reply_markup=make_tts_voice_keyboard_for_language(lang_name), parse_mode="Markdown"
    )
    target_bot.answer_callback_query(call.id)

def handle_tts_voice_change_callback(call, target_bot: telebot.TeleBot, user_id_for_settings: str):
    chat_id = call.message.chat.id
    user_pitch_input_mode[user_id_for_settings] = None
    user_rate_input_mode[user_id_for_settings] = None
    _, voice = call.data.split("|", 1)
    set_tts_user_voice_in_memory(user_id_for_settings, voice)
    user_tts_mode[user_id_for_settings] = voice
    current_pitch = get_tts_user_pitch_in_memory(user_id_for_settings)
    current_rate = get_tts_user_rate_in_memory(user_id_for_settings)
    voice_display_name = VOICE_MAPPING.get(voice, voice)
    target_bot.answer_callback_query(call.id, f"✔️ The voice is {voice_display_name}")
    target_bot.edit_message_text(
        chat_id=chat_id, message_id=call.message.message_id,
        text=f"🔊 Great! You are using: *{voice_display_name}*.\n\n"
             f"Current settings:\n• Pitch: *{current_pitch}*\n• Rate: *{current_rate}*\n\n"
             f"Ready to speak? Send me text!",
        parse_mode="Markdown", reply_markup=None
    )

def handle_tts_back_to_languages_callback(call, target_bot: telebot.TeleBot, user_id_for_settings: str):
    chat_id = call.message.chat.id
    user_tts_mode[user_id_for_settings] = None
    user_pitch_input_mode[user_id_for_settings] = None
    user_rate_input_mode[user_id_for_settings] = None
    target_bot.edit_message_text(
        chat_id=chat_id, message_id=call.message.message_id,
        text="Choose the *language* of your voice. 👇",
        reply_markup=make_tts_language_keyboard(), parse_mode="Markdown"
    )
    target_bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.text == "Choose Voice")
@bot.message_handler(commands=['voice'])
def cmd_text_to_speech(message):
    user_id = str(message.from_user.id)
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.chat.id):
        send_subscription_message(message.chat.id)
        return
    handle_voice_command(message, bot, user_id)

@bot.callback_query_handler(lambda c: c.data.startswith("tts_lang|"))
def on_tts_language_select(call):
    uid = str(call.from_user.id)
    update_user_activity_in_memory(call.from_user.id)
    if call.message.chat.type == 'private' and str(call.from_user.id) != str(ADMIN_ID) and not check_subscription(call.message.chat.id):
        send_subscription_message(call.message.chat.id)
        bot.answer_callback_query(call.id)
        return
    handle_tts_language_select_callback(call, bot, uid)

@bot.callback_query_handler(lambda c: c.data.startswith("tts_voice|"))
def on_tts_voice_change(call):
    uid = str(call.from_user.id)
    update_user_activity_in_memory(call.from_user.id)
    if call.message.chat.type == 'private' and str(call.from_user.id) != str(ADMIN_ID) and not check_subscription(call.message.chat.id):
        send_subscription_message(call.message.chat.id)
        bot.answer_callback_query(call.id)
        return
    handle_tts_voice_change_callback(call, bot, uid)

@bot.callback_query_handler(lambda c: c.data == "tts_back_to_languages")
def on_tts_back_to_languages(call):
    uid = str(call.from_user.id)
    update_user_activity_in_memory(call.from_user.id)
    if call.message.chat.type == 'private' and str(call.from_user.id) != str(ADMIN_ID) and not check_subscription(call.message.chat.id):
        send_subscription_message(call.message.chat.id)
        bot.answer_callback_query(call.id)
        return
    handle_tts_back_to_languages_callback(call, bot, uid)

async def synth_and_send_tts(chat_id: int, user_id_for_settings: str, text: str, target_bot: telebot.TeleBot):
    text = text.replace('.', ',')
    voice = get_tts_user_voice_in_memory(user_id_for_settings)
    pitch = get_tts_user_pitch_in_memory(user_id_for_settings)
    rate = get_tts_user_rate_in_memory(user_id_for_settings)
    filename = f"tts_{user_id_for_settings}_{uuid.uuid4()}.mp3"
    stop_recording = threading.Event()
    recording_thread = threading.Thread(target=keep_recording, args=(chat_id, stop_recording, target_bot))
    recording_thread.daemon = True
    recording_thread.start()
    try:
        mss = MSSpeech()
        await mss.set_voice(voice)
        await mss.set_rate(rate)
        await mss.set_pitch(pitch)
        await mss.set_volume(1.0)
        await mss.synthesize(text, filename)
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            target_bot.send_message(chat_id, "❌ I failed to create the audio. Try another text.")
            return
        with open(filename, "rb") as f:
            voice_display_name = VOICE_MAPPING.get(voice, voice)
            caption_text = (
                f"🎧 *Here is your voice!* \n\n"
                f"Voice: **{voice_display_name}**\n"
                f"Pitch: *{pitch}*\n"
                f"Rate: *{rate}*\n\n"
                f"Enjoy listening! ✨"
            )
            target_bot.send_audio(chat_id, f, caption=caption_text, parse_mode="Markdown")
        increment_processing_count_in_memory(user_id_for_settings, "tts")
    except MSSpeechError as e:
        logging.error(f"TTS error: {e}")
        target_bot.send_message(chat_id, "❌ An error occurred while generating the audio. Try again or choose another voice.")
    except Exception:
        logging.exception("TTS error")
        target_bot.send_message(chat_id, "This voice is not available, please choose another one.")
    finally:
        stop_recording.set()
        if os.path.exists(filename):
            try:
                os.remove(filename)
                logging.info(f"Deleted temporary TTS file: {filename}")
            except Exception as e:
                logging.error(f"Error deleting TTS file {filename}: {e}")

def build_stt_language_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    ordered_keys = sorted(STT_LANGUAGES.keys(), key=lambda k: (k != "English 🇬🇧", k != "العربية 🇸🇦", k != "Spanish 🇪🇸", k != "French 🇫🇷", k != "German 🇩🇪", k != "Russian 🇷🇺", k))
    buttons = [InlineKeyboardButton(lang_name, callback_data=f"stt_lang|{STT_LANGUAGES[lang_name]}") for lang_name in ordered_keys]
    for i in range(0, len(buttons), 3):
        markup.add(*buttons[i:i+3])
    return markup

def handle_language_stt_command(message, target_bot: telebot.TeleBot, user_id_for_settings: str):
    chat_id = message.chat.id
    user_tts_mode[user_id_for_settings] = None
    user_pitch_input_mode[user_id_for_settings] = None
    user_rate_input_mode[user_id_for_settings] = None
    target_bot.send_message(chat_id, "Choose the language of your voice, audio, or video file for transcription using the buttons below:", reply_markup=build_stt_language_keyboard(), parse_mode="Markdown")

def handle_stt_language_select_callback(call, target_bot: telebot.TeleBot, user_id_for_settings: str):
    chat_id = call.message.chat.id
    _, lang_code = call.data.split("|", 1)
    lang_name = next((name for name, code in STT_LANGUAGES.items() if code == lang_code), "Unknown")
    set_stt_user_lang_in_memory(user_id_for_settings, lang_code)
    target_bot.answer_callback_query(call.id, f"✅ The language is {lang_name}!")
    target_bot.edit_message_text(
        chat_id=chat_id, message_id=call.message.message_id,
        text=f"✅ The transcription language is: *{lang_name}*\n\n🎙️ Send audio, file or video (up to 20MB) for me to transcribe.",
        parse_mode="Markdown", reply_markup=None
    )

@bot.message_handler(func=lambda message: message.text == "STT Lang")
@bot.message_handler(commands=['lang'])
def send_stt_language_prompt(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.from_user.id):
        send_subscription_message(message.chat.id)
        return
    handle_language_stt_command(message, bot, user_id)

@bot.callback_query_handler(lambda c: c.data.startswith("stt_lang|"))
def on_stt_language_select(call):
    uid = str(call.from_user.id)
    update_user_activity_in_memory(call.from_user.id)
    if call.message.chat.type == 'private' and str(call.from_user.id) != str(ADMIN_ID) and not check_subscription(call.message.chat.id):
        send_subscription_message(call.message.chat.id)
        bot.answer_callback_query(call.id)
        return
    handle_stt_language_select_callback(call, bot, uid)

async def process_stt_media(chat_id: int, user_id_for_settings: str, message_type: str, file_id: str, target_bot: telebot.TeleBot, original_message_id: int):
    processing_msg = None
    downloaded_file_path = None
    try:
        processing_msg = target_bot.send_message(chat_id, " 🔄 Processing This might take a while...", reply_to_message_id=original_message_id)
        file_info = target_bot.get_file(file_id)
        if file_info.file_size > 20 * 1024 * 1024:
            target_bot.send_message(chat_id, "⚠️ The file is too large. Maximum size is 20MB. Send a smaller file.", reply_to_message_id=original_message_id)
            return
        downloaded_file_path = f"stt_temp_{uuid.uuid4()}_{file_info.file_path.split('/')[-1]}"
        downloaded_file = bot.download_file(file_info.file_path)
        with open(downloaded_file_path, 'wb') as f:
            f.write(downloaded_file)
        with open(downloaded_file_path, "rb") as f:
            upload_res = requests.post("https://api.assemblyai.com/v2/upload",
                headers={"authorization": ASSEMBLYAI_API_KEY, "Content-Type": "application/octet-stream"},
                data=f)
        upload_res.raise_for_status()
        audio_url = upload_res.json().get('upload_url')
        if not audio_url:
            raise Exception("AssemblyAI upload failed: No upload_url received.")
        lang_code = get_stt_user_lang_in_memory(user_id_for_settings)
        transcript_res = requests.post("https://api.assemblyai.com/v2/transcript",
            headers={"authorization": ASSEMBLYAI_API_KEY, "content-type": "application/json"},
            json={"audio_url": audio_url, "language_code": lang_code, "speech_model": "best"})
        transcript_res.raise_for_status()
        transcript_id = transcript_res.json().get("id")
        if not transcript_id:
            raise Exception("AssemblyAI transcription request failed: No transcript ID received.")
        polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        while True:
            res = requests.get(polling_url, headers={"authorization": ASSEMBLYAI_API_KEY}).json()
            if res['status'] in ['completed', 'error']:
                break
            time.sleep(2)
        if res['status'] == 'completed':
            text = res.get("text", "")
            if not text:
                target_bot.send_message(chat_id, "ℹ️ No text extracted from this file.", reply_to_message_id=original_message_id)
            elif len(text) <= 4000:
                target_bot.send_message(chat_id, text, reply_to_message_id=original_message_id)
            else:
                import io
                f = io.BytesIO(text.encode("utf-8"))
                f.name = "transcript.txt"
                target_bot.send_document(chat_id, f, caption="Your transcript is too long. Here is the file:", reply_to_message_id=original_message_id)
            increment_processing_count_in_memory(user_id_for_settings, "stt")
        else:
            error_msg = res.get("error", "Unknown transcription error.")
            target_bot.send_message(chat_id, f"❌ Transcription error: {error_msg}", parse_mode="Markdown", reply_to_message_id=original_message_id)
            logging.error(f"AssemblyAI transcription failed: {error_msg}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Network or API error during STT processing: {e}")
        target_bot.send_message(chat_id, "❌ A network error occurred. Try again.", reply_to_message_id=original_message_id)
    except Exception as e:
        logging.exception(f"Unhandled error during STT processing: {e}")
        target_bot.send_message(chat_id, "The file is too large, send one smaller than 20MB.", reply_to_message_id=original_message_id)
    finally:
        if processing_msg:
            try:
                target_bot.delete_message(chat_id, processing_msg.message_id)
            except Exception as e:
                logging.error(f"Could not delete processing message: {e}")
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            try:
                os.remove(downloaded_file_path)
                logging.info(f"Deleted temporary STT file: {downloaded_file_path}")
            except Exception as e:
                logging.error(f"Error deleting STT file {downloaded_file_path}: {e}")

def handle_stt_media_types_common(message, target_bot: telebot.TeleBot, user_id_for_settings: str):
    update_user_activity_in_memory(int(user_id_for_settings))
    user_tts_mode[user_id_for_settings] = None
    user_pitch_input_mode[user_id_for_settings] = None
    user_rate_input_mode[user_id_for_settings] = None
    file_id = None
    message_type = None
    if message.voice:
        file_id = message.voice.file_id
        message_type = "voice"
    elif message.audio:
        file_id = message.audio.file_id
        message_type = "audio"
    elif message.video:
        file_id = message.video.file_id
        message_type = "video"
    elif message.document:
        if message.document.mime_type and (message.document.mime_type.startswith('audio/') or message.document.mime_type.startswith('video/')):
            file_id = message.document.file_id
            message_type = "document_media"
        else:
            target_bot.send_message(message.chat.id, "I'm sorry, I can only transcribe audio or video. Send a valid file.")
            return
    if not file_id:
        target_bot.send_message(message.chat.id, "I don't support this file type. Send audio, file or video.")
        return
    if user_id_for_settings not in in_memory_data["stt_settings"]:
        target_bot.send_message(message.chat.id, "First choose the transcription language click or type /lang")
        return
    threading.Thread(target=lambda: asyncio.run(process_stt_media(message.chat.id, user_id_for_settings, message_type, file_id, target_bot, message.message_id))).start()

@bot.message_handler(func=lambda message: message.text == "✍️ Voice to text")
@bot.message_handler(content_types=['voice', 'audio', 'video', 'document'])
def handle_stt_media_types(message):
    uid = str(message.from_user.id)
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.chat.id):
        send_subscription_message(message.chat.id)
        return
    handle_stt_media_types_common(message, bot, uid)

def handle_text_for_tts_or_mode_input_common(message, target_bot: telebot.TeleBot, user_id_for_settings: str):
    update_user_activity_in_memory(int(user_id_for_settings))
    if message.text and message.text.startswith('/'):
        return
    if message.text == "🗣️ Text to voice":
        target_bot.send_message(message.chat.id, "Okay, send me the text you want to convert to voice!")
        return
    if user_rate_input_mode.get(user_id_for_settings) == "awaiting_rate_input":
        try:
            rate_val = int(message.text)
            if -100 <= rate_val <= 100:
                set_tts_user_rate_in_memory(user_id_for_settings, rate_val)
                target_bot.send_message(message.chat.id, f"🔊 The speech rate is *{rate_val}*.", parse_mode="Markdown")
                user_rate_input_mode[user_id_for_settings] = None
            else:
                target_bot.send_message(message.chat.id, "❌ Invalid rate. Send a number from -100 to +100 or 0. Try again:")
            return
        except ValueError:
            target_bot.send_message(message.chat.id, "That is not a valid number. Send a number from -100 to +100 or 0. Try again:")
            return
    if user_pitch_input_mode.get(user_id_for_settings) == "awaiting_pitch_input":
        try:
            pitch_val = int(message.text)
            if -100 <= pitch_val <= 100:
                set_tts_user_pitch_in_memory(user_id_for_settings, pitch_val)
                target_bot.send_message(message.chat.id, f"🔊 The pitch is *{pitch_val}*.", parse_mode="Markdown")
                user_pitch_input_mode[user_id_for_settings] = None
            else:
                target_bot.send_message(message.chat.id, "❌ Invalid pitch. Send a number from -100 to +100 or 0. Try again:")
            return
        except ValueError:
            target_bot.send_message(message.chat.id, "That is not a valid number. Send a number from -100 to +100 or 0. Try again:")
            return
    current_voice = get_tts_user_voice_in_memory(user_id_for_settings)
    if current_voice:
        threading.Thread(target=lambda: asyncio.run(synth_and_send_tts(message.chat.id, user_id_for_settings, message.text, target_bot))).start()
    else:
        target_bot.send_message(message.chat.id, "You haven't chosen a voice yet! Use the `Choose Voice` button from `Settings` first, then send me text. 🗣️")

@bot.message_handler(func=lambda message: message.text in ["⚙️ Settings", "Main Menu"])
def handle_settings_menu(message):
    uid = str(message.from_user.id)
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.chat.id):
        send_subscription_message(message.chat.id)
        return
    if message.text == "⚙️ Settings":
        bot.send_message(message.chat.id, "Choose a setting to change:", reply_markup=create_settings_reply_keyboard())
    elif message.text == "Main Menu":
        bot.send_message(message.chat.id, "Welcome back to the main menu!", reply_markup=create_main_reply_keyboard())

@bot.message_handler(content_types=['text'])
def handle_text_for_tts_or_mode_input(message):
    uid = str(message.from_user.id)
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.chat.id):
        send_subscription_message(message.chat.id)
        return
    handle_text_for_tts_or_mode_input_common(message, bot, uid)

@bot.message_handler(func=lambda m: True, content_types=['sticker', 'photo'])
def handle_unsupported_media_types(message):
    uid = str(message.from_user.id)
    update_user_activity_in_memory(message.from_user.id)
    if message.chat.type == 'private' and str(message.from_user.id) != str(ADMIN_ID) and not check_subscription(message.chat.id):
        send_subscription_message(message.chat.id)
        return
    user_tts_mode[uid] = None
    user_pitch_input_mode[uid] = None
    user_rate_input_mode[uid] = None
    bot.send_message(message.chat.id, "I'm sorry, I can only convert *text* to audio or *audio/files* to text. Send me one of those!")

bot_start_time = datetime.now()

@app.route("/", methods=["GET", "POST", "HEAD"])
def webhook():
    if request.method in ("GET", "HEAD"):
        return "OK", 200
    if request.method == "POST":
        content_type = request.headers.get("Content-Type", "")
        if content_type and content_type.startswith("application/json"):
            update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
            bot.process_new_updates([update])
            return "", 200
    return abort(403)

@app.route("/set_webhook", methods=["GET", "POST"])
def set_webhook_route():
    try:
        bot.set_webhook(url=WEBHOOK_URL)
        return f"Webhook set to {WEBHOOK_URL}", 200
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")
        return f"Failed to set webhook: {e}", 500

@app.route("/delete_webhook", methods=["GET", "POST"])
def delete_webhook_route():
    try:
        bot.delete_webhook()
        return "Webhook deleted.", 200
    except Exception as e:
        logging.error(f"Failed to delete webhook: {e}")
        return f"Failed to delete webhook: {e}", 500

def set_bot_commands():
    commands = [
        BotCommand("start", "👋 Get Started"), BotCommand("voice", "Choose a TTS different voice"),
        BotCommand("pitch", "Change TTS pitch "), BotCommand("rate", "Change TTS speed"),
        BotCommand("lang", "🌍 Set STT File language"), BotCommand("help", "❓How to use"),
    ]
    try:
        bot.set_my_commands(commands)
        logging.info("Main bot commands set successfully.")
        return True
    except Exception as e:
        logging.error(f"Failed to set main bot commands: {e}")
        return False

@app.route("/setup", methods=["GET"])
def setup_bot():
    webhook_status = set_webhook_on_startup()
    commands_status = set_bot_commands()
    response = "Bot setup complete:\n"
    response += f"Webhook status: {'Success' if webhook_status else 'Failed'}\n"
    response += f"Commands status: {'Success' if commands_status else 'Failed'}\n"
    return response, 200

def set_webhook_on_startup():
    try:
        bot.delete_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        logging.info(f"Main bot webhook set successfully to {WEBHOOK_URL}")
        return True
    except Exception as e:
        logging.error(f"Failed to set main bot webhook on startup: {e}")
        return False

def set_bot_info_and_startup():
    global bot_start_time
    bot_start_time = datetime.now()
    if check_db_connection():
        init_in_memory_data()
        set_webhook_on_startup()
        set_bot_commands()
    else:
        logging.error("Failed to connect to MongoDB. Bot will run with in-memory data only, which will be lost on restart.")
        set_webhook_on_startup()
        set_bot_commands()

if __name__ == "__main__":
    set_bot_info_and_startup()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
