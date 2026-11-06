from pathlib import Path
import dj_database_url
from decouple import config, Csv
from django.core.exceptions import ImproperlyConfigured
BASE_DIR = Path(__file__).resolve().parent.parent

IS_RENDER = config('RENDER', default=False, cast=bool)
DEBUG = config('DEBUG', default=not IS_RENDER, cast=bool)
SECRET_KEY = config('SECRET_KEY', default=None)
if not SECRET_KEY:
 if DEBUG:
  SECRET_KEY = 'dev-only-insecure-key-for-local-development'
 else:
  raise ImproperlyConfigured('SECRET_KEY must be configured when DEBUG is False.')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())
RENDER_EXTERNAL_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default='')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
 ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
 'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
 'rest_framework','rest_framework_simplejwt.token_blacklist','django_filters','corsheaders','portfolio',
]
MIDDLEWARE = [
 'django.middleware.security.SecurityMiddleware',
 'whitenoise.middleware.WhiteNoiseMiddleware',
 'corsheaders.middleware.CorsMiddleware',
 'django.contrib.sessions.middleware.SessionMiddleware',
 'django.middleware.common.CommonMiddleware',
 'django.middleware.csrf.CsrfViewMiddleware',
 'django.contrib.auth.middleware.AuthenticationMiddleware',
 'django.contrib.messages.middleware.MessageMiddleware',
 'django.middleware.clickjacking.XFrameOptionsMiddleware',
 'portfolio.middleware.RequestTimingMiddleware',
]
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='config.wsgi.application'
DATABASE_URL = config('DATABASE_URL', default='')
if DATABASE_URL:
 DATABASES = {'default': dj_database_url.parse(
  DATABASE_URL,
  conn_max_age=600,
  ssl_require=not DEBUG,
 )}
else:
 DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS=[{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE='en-us'; TIME_ZONE='Asia/Dhaka'; USE_I18N=True; USE_TZ=True
STATIC_URL='/static/'
STATIC_ROOT=BASE_DIR/'staticfiles'
MEDIA_URL='/media/'
MEDIA_ROOT=BASE_DIR/'media'
STORAGES = {
 'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
 'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
CORS_ALLOWED_ORIGINS=config(
 'CORS_ALLOWED_ORIGINS',
 default='http://localhost:5173,http://127.0.0.1:5173,https://emon-m-raju-portfolio-frontend.vercel.app',
 cast=Csv(),
)
CSRF_TRUSTED_ORIGINS=config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())
SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')
SECURE_SSL_REDIRECT=not DEBUG
SESSION_COOKIE_SECURE=not DEBUG
CSRF_COOKIE_SECURE=not DEBUG
REST_FRAMEWORK={
 'DEFAULT_AUTHENTICATION_CLASSES':['rest_framework_simplejwt.authentication.JWTAuthentication'],
 'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.AllowAny'],
 'DEFAULT_FILTER_BACKENDS':['django_filters.rest_framework.DjangoFilterBackend','rest_framework.filters.SearchFilter','rest_framework.filters.OrderingFilter'],
 'DEFAULT_PAGINATION_CLASS':'rest_framework.pagination.PageNumberPagination','PAGE_SIZE':10,
 'DEFAULT_THROTTLE_CLASSES':['rest_framework.throttling.AnonRateThrottle'],'DEFAULT_THROTTLE_RATES':{'anon':'20/min','comment':'5/hour','contact':'3/hour','like':'30/min'},
}
SIMPLE_JWT={'BLACKLIST_AFTER_ROTATION':True,'ROTATE_REFRESH_TOKENS':True}
EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
