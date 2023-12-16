import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# 設置環境變量 DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE','app.settings')
# 創建實例
app = Celery('app')
app.config_from_object('django.conf:settings', namespace='CELERY')
# 查找在 INSTALLED_APPS 設置的異步任務
app.autodiscover_tasks()

app.conf.beat_schedule = settings.CELERY_BEAT_SCHEDULE



@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

