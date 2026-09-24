SECRET_KEY = "test-only"
ROOT_URLCONF = "tests.django.test_integration"
ALLOWED_HOSTS = ["testserver"]
INSTALLED_APPS: list[str] = []
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"