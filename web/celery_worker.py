from celery import Celery
from googletrans import Translator

celery_app = Celery('tasks', broker='redis://localhost:6379/0')

@celery_app.task
def translate_text(text, language):
    try:
        translator = Translator()
        translated_text = translator.translate(text, dest=language).text
        return translated_text
    except Exception as e:
        return str(e)
