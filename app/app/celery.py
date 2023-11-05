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

app.conf.beat_schedule = {
    'update-recipe-views': {
        'task': 'recipe.tasks.update_recipe_views_in_redis',
        'schedule': crontab(minute='*/30'),  # every 30 minutes
    },
    'consist-recipe-to-sql':{
        'task': 'recipe.tasks.consist_redis_and_sql_data',
        'schedule': crontab(minute='*/15'),  # every 15 minutes
    }
}



@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

