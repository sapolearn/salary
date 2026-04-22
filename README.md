# Salary Calendar

Calendar-first salary app with:
- registration/login
- forgot-password OTP via email
- multilingual UI (EN/HE/RU/NE)
- manual day entries (start/end/festival settings)
- monthly payroll with overtime/deductions/additions

## Local Run

```bash
python3 app.py
```

Open: `http://127.0.0.1:8080`

## SMTP (for OTP emails)

Set these env vars before running:

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your_email@example.com"
export SMTP_PASS="your_app_password"
export SMTP_FROM="your_email@example.com"
```

## Production Deploy (Docker)

Build image:

```bash
docker build -t salary-calendar .
```

Run container:

```bash
docker run -d --name salary-calendar -p 8080:8080 \
  -e PORT=8080 \
  -e HOST=0.0.0.0 \
  -e SMTP_HOST="smtp.gmail.com" \
  -e SMTP_PORT="587" \
  -e SMTP_USER="your_email@example.com" \
  -e SMTP_PASS="your_app_password" \
  -e SMTP_FROM="your_email@example.com" \
  salary-calendar
```

Health check endpoint: `/health`
