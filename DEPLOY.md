# pojia-breaker Web Console

Полноценный веб-интерфейс для pojia-breaker с тёплой paper-эстетикой. Запускай атаки, выбирай боеприпасы, смотри live-вывод — всё через браузер.

## 🚀 Деплой на Railway

### 1. Подготовь репозиторий

```bash
# Склонируй оригинальный pojia-breaker
git clone https://github.com/Justinuse1/pojia-breaker.git
cd pojia-breaker

# Скопируй файлы веб-интерфейса
# (Перенеси app.py, templates/, Procfile, railway.json, requirements.txt из этой папки)
```

### 2. Залей на GitHub (если ещё не там)

```bash
# Создай свой репозиторий на GitHub
git init
git add .
git commit -m "Add web UI for Railway"
git branch -M main
git remote add origin https://github.com/твой-username/pojia-breaker-web.git
git push -u origin main
```

### 3. Деплой на Railway

1. **Зайди на [railway.app](https://railway.app)** и залогинься через GitHub
2. **New Project** → **Deploy from GitHub repo**
3. **Выбери свой репозиторий** с pojia-breaker + веб-интерфейсом
4. Railway автоматом:
   - Прочитает `railway.json` и `Procfile`
   - Установит Python 3.11.9 (из `runtime.txt`)
   - Запустит gunicorn с Flask
5. **Подожди 2-3 минуты** — Railway соберёт и задеплоит
6. **Открой URL** который Railway выдаст (типа `your-app.up.railway.app`)

### 4. Что внутри

**Структура:**
```
pojia-breaker/
├── app.py              # Flask backend с API
├── templates/
│   └── index.html      # Веб-интерфейс (warm paper design)
├── Procfile            # Railway команда запуска
├── railway.json        # Railway конфиг
├── runtime.txt         # Python версия
├── requirements.txt    # Зависимости (Flask + gunicorn + оригинальные)
└── ammo/               # Оригинальные боеприпасы pojia-breaker
    ├── persona/
    ├── trigger/
    ├── cot-attack/
    └── ...
```

**Endpoints:**
- `GET /` — главная страница с UI
- `GET /api/config` — список боеприпасов и целей
- `POST /api/attack` — запуск атаки (Server-Sent Events streaming)
- `POST /api/probe` — probe matrix analysis
- `GET /healthz` — health check

**UI фичи:**
- **Target configuration** — API base, key, model name
- **Ammo library** — карточки по категориям (persona, trigger, cot-attack и т.д.)
- **Live terminal output** — стримящийся вывод атаки в реальном времени
- **Warm paper design** — янтарь (#C8853F), тёплая бумага (#F6F1E8), DM Serif Display для заголовков

## 🎯 Как юзать

1. Открой деплоенное приложение
2. **Target Configuration**:
   - API Base: `https://api.openai.com/v1` (или твой прокси)
   - API Key: твой ключ
   - Model: `gpt-4` / `deepseek-v4.1-flash` / что угодно
3. **Ammo Library**:
   - Кликни по категории (persona, trigger, etc)
   - Выбери шаблон атаки (карточка подсветится)
4. **Execute**:
   - **Launch Attack** — запустит выбранный template
   - **Run Probe Matrix** — прогонит матрицу explorers (off/high efforts)
5. Смотри live output в терминале внизу

## 🔧 Локальный запуск (для теста)

```bash
# Установи зависимости
pip install -r requirements.txt

# Запусти Flask
python app.py

# Открой http://localhost:5000
```

## ⚠️ Security Note

- **Не храни API ключи в коде** — вводи через UI или ставь env vars в Railway
- **Аутентификация не встроена** — если нужен паблик доступ, добавь basic auth или OAuth
- **Railway env vars** (если хочешь дефолтные значения):
  ```
  DEFAULT_TARGET_BASE=https://api.openai.com/v1
  DEFAULT_TARGET_KEY=sk-...
  DEFAULT_MODEL=gpt-4
  ```

## 📦 Зависимости

- **Flask 3.0+** — веб-фреймворк
- **gunicorn** — production WSGI сервер
- **requests, pyyaml** — оригинальные зависимости pojia-breaker

## 🎨 Design System

- **Background**: #F6F1E8 (warm paper)
- **Cards**: #FFFFFF с borders #E2D9C8
- **Accent**: #C8853F (amber, hover #A86B2C)
- **Typography**: DM Serif Display (headings), Inter (body)
- **Terminal**: #2A2723 background, #F6F1E8 text

---

**Built for Larpbase** | She/her | Kiro-powered
