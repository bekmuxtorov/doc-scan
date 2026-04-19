# Doc-Scan API

Word hujjatlarini tahlil qilish va `s2` matni bilan solishtirish uchun FastAPI asosidagi API.

## O'rnatish (Local)

1. Repozitoriyani klon qiling:
   ```bash
   git clone https://github.com/bekmuxtorov/doc-scan.git
   cd doc-scan
   ```

2. Virtual muhit yarating va faollashtiring:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # yoki
   venv\Scripts\activate  # Windows
   ```

3. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

4. `.env` faylini yarating va API kalitni kiriting:
   ```bash
   cp .env.example .env
   # .env faylini tahrirlang
   ```

5. Loyihani ishga tushiring:
   ```bash
   uvicorn main:app --reload
   ```

## Ubuntu Serverga Deploy qilish (Manual)

### 1. Gunicorn va Uvicorn o'rnatish
`requirements.txt` ichida uvicorn bor. Gunicorn-ni tizimda ishlatish tavsiya etiladi:
```bash
pip install gunicorn
```

### 2. Systemd Servis fayli yarating
`/etc/systemd/system/doc-scan.service` faylini yarating:

```ini
[Unit]
Description=Gunicorn instance to serve doc-scan API
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/doc-scan
Environment="PATH=/home/ubuntu/doc-scan/venv/bin"
EnvironmentFile=/home/ubuntu/doc-scan/.env
ExecStart=/home/ubuntu/doc-scan/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

### 3. Servisni ishga tushiring
```bash
sudo systemctl start doc-scan
sudo systemctl enable doc-scan
```

## API Endpointlar

- **POST `/analyze`**: Word fayl va `s2` matnini solishtirish.
- **GET `/docs`**: Swagger dokumentatsiyasi.
