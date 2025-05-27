import os
from django.apps import AppConfig
from django.core.management import call_command

class ServiceAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'service_app'

    def ready(self):
        if os.getenv("IMPORT_INITIAL_DATA", "False") == "True":
            try:
                json_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'service_categories.json'
                )
                call_command('loaddata', json_path)
                print("[INFO] ✅ 已自动导入 service_categories.json")
            except Exception as e:
                print(f"[WARNING] ❌ 自动导入失败: {e}")
