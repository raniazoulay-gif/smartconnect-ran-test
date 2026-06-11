# 📋 לוג פיתוח — אפליקציית GILI מכירות שטח
**עודכן לאחרונה:** 15/04/2026

---

## 🗂️ מבנה תיקיות

```
GOOD/GILI/sales-app/
├── main.py              ← שרת FastAPI ראשי
├── database.py          ← הגדרת DB + init
├── import_data.py       ← ייבוא Excel → SQLite (openpyxl)
├── build_schedule.py    ← יצירת לוח עבודה מהרמזור (בתיקיית GILI)
├── sales.db             ← מסד הנתונים SQLite
├── סידור_עבודה_חדש.xlsx ← קובץ לוח עבודה (עם רמזור + שבועות)
├── requirements.txt
├── Procfile             ← הגדרת Railway
├── static/
│   └── placeholder.txt
└── templates/
    ├── login.html
    ├── agent.html
    ├── store.html
    └── manager.html
```

---

## 👥 משתמשים במערכת

| יוזרנים | סיסמה | תפקיד | אזורים |
|---------|--------|--------|--------|
| gili_agent | gili2026 | agent | השרון, מרכז, דרום |
| eli | eli2026 | agent | בני ברק, ירושלים והסביבה |
| shirael | shirael2026 | agent | אילת (ריק — יתווסף בהמשך) |
| manager | GILI2026 | manager | הכל |

---

## 🗃️ טבלאות במסד הנתונים

### users
- id, username, password_hash, name, role, regions

### customers (201 רשומות מ-Excel)
- id, name, city, address, region, card_code, delivery_day, x_days, visit_day
- **traffic_light** ← ירוק / כתום / אדום (מעמודת הרמזור)
- **assigned_visit_day** ← יום הביקור המחושב (א/ב/ג/ד/ה)
- **week_1, week_2, week_3, week_4** ← 1/0 האם מבקרים באותו שבוע

### visits
- id, user_id, customer_id, visit_date, check_in_time, check_out_time, duration_minutes, notes

### notifications
- id, message, user_name, store_name, action, is_read, created_at
- **action='eod_report'** ← דוחות סוף יום אוטומטיים

### visit_comments
- id, visit_id, customer_id, visit_date, user_id, user_name, user_role, message, created_at

---

## 🌐 נתיבי API

| Method | נתיב | תיאור |
|--------|------|--------|
| GET | / | עמוד כניסה |
| POST | /login | התחברות |
| GET | /logout | התנתקות |
| GET | /dashboard | לוח הסוכן |
| GET | /store/{id}?date= | פרטי חנות |
| GET | /manager | לוח המנהל |
| GET | /manager/agent/{id} | צפייה בסוכן ספציפי |
| POST | /api/checkin | כניסה לחנות |
| POST | /api/checkout | יציאה מחנות |
| POST | /api/notes | שמירת הערות |
| POST | /api/comment | שליחת הודעה בצ'ט |
| GET | /api/comments | טעינת הודעות |
| GET | /api/notifications | התראות למנהל |
| GET | /api/trigger-eod | הפעלה ידנית של דוח סוף יום |

---

## ✅ מה בוצע עד כה

- [x] מסד נתונים + ייבוא 201 לקוחות מ-Excel
- [x] מערכת התחברות עם cookies
- [x] לוח סוכן — חנויות לפי יום ביקור ואזור
- [x] ניווט תאריכים (אתמול / היום / מחר)
- [x] כניסה / יציאה מחנות עם שעון
- [x] חישוב משך שהייה אוטומטי
- [x] הערות לביקור
- [x] כפתורי שמור / בטל / חזרה
- [x] לוח מנהל — סקירה / התראות / ביקורים
- [x] קלפים לכל סוכן עם מצב נוכחי
- [x] התראות בזמן אמת (כניסה / יציאה)
- [x] צ'ט בין סוכן למנהל — בדף החנות
- [x] צ'ט בלוח המנהל — פאנל slide-up לכל ביקור
- [x] **שיטת רמזור** — קריאת צבעי Excel + חישוב לוח ביקורים
- [x] **לוח חודש מלא** — גריד 7×N לכל ימי החודש, ניווט בין חודשים
- [x] **שבוע בחודש** — פילטר לפי שבוע 1/2/3/4 בחודש
- [x] **עמודת רמזור** — נקודה צבעונית (ירוק/כתום/אדום) בכל כרטיס חנות
- [x] **סטטוס צבעוני** — ירוק=הושלם, כתום=בפנים, אדום=לא בוקר (אחרי 18:00)
- [x] **דוח סוף יום ב-18:00** — Scheduler אוטומטי לכל סוכן
- [x] **דוחות אדומים במנהל** — תצוגת חנויות שלא בוקרו
- [x] **תצוגת מנהל בעמוד חנות** — ממשק סיכום בלבד (ללא כפתורי כניסה/יציאה), רקע ורוד
- [x] **צ'אט תקין** — תיקון באג DOM (chatList נפרד מ-chatEmpty), שמירת כל היסטוריית השיחה
- [x] **ייבוא Excel עם data_only=True** — קריאת ערכי נוסחאות מחושבים במקום טקסט הנוסחה
- [x] **כיתוב קלפי חנות בולט יותר** — store-footer: גודל 13px, צבע #4a5568, font-weight:600
- [x] **רענון אוטומטי כל 15 שניות** — כל שלושת הדפים (store/agent/manager) עם location.reload(). מושהה אם המשתמש מקליד. המנהל שומר טאב פעיל ב-sessionStorage

---

## 🔧 פתרונות טכניים שיושמו

| בעיה | פתרון |
|------|--------|
| Python 3.14 + Jinja2 cache | `Environment(cache_size=0, auto_reload=True)` |
| Starlette 1.0 API שינוי | `TemplateResponse(request=request, name=..., context=...)` |
| Static dir ריק → 500 | הוספת `placeholder.txt` |
| Cookies משותפים בין פורטים | שימוש ב-`127.0.0.1` מול `localhost` |
| ימי ביקור — Hebrew mapping | `{0:'ב', 1:'ג', 2:'ד', 3:'ה', 4:'ו', 5:'ש', 6:'א'}` |
| קריאת צבעי Excel | `openpyxl` + `fill.fgColor.rgb` |
| צבעי רמזור | FFFF0000=אדום, FFFFC000=כתום, FF92D050=ירוק |
| מקסימום 10 חנויות ביום | Greedy scheduler עם overflow |
| שבוע בחודש | `(date.day - 1) // 7 + 1` |
| דוח אוטומטי 18:00 | `APScheduler` + `cron(hour=18)` |
| נוסחאות Excel נקראות כטקסט | `openpyxl load_workbook(data_only=True)` |
| צ'אט DOM bug (chatEmpty=null) | `<div id="chatList">` נפרד בתוך chatMessages |
| sendComment מחליף את chatList | קריאה ל-`loadComments()` אחרי שליחה במקום innerHTML += |
| טאב מנהל מתאפס בכל רענון | `sessionStorage.setItem('managerTab', name)` + שחזור בטעינה |

---

## 📊 לוח עבודה — שיטת הרמזור

| צבע | תדירות ביקור | שבועות |
|-----|-------------|--------|
| 🟢 ירוק | כל שבוע | 1, 2, 3, 4 |
| 🟡 כתום | פעמיים בחודש | 1, 3 |
| 🔴 אדום | פעם בחודש | 2 או 4 (חלוקה שווה) |

**קובץ ה-build:** `GOOD/GILI/build_schedule.py`
**קובץ הפלט:** `sales-app/סידור_עבודה_חדש.xlsx`

---

## 🏃 הפעלת השרת (מקומי)

```bash
cd GOOD/GILI/sales-app
python -m uvicorn main:app --port 8007 --reload
```

**כתובת:** http://127.0.0.1:8007

> ⚠️ פורטים 8002, 8004 חסומים ב-Windows — השתמש ב-8006/8007

---

## 📌 משימות עתידיות (TODO)

- [ ] העלאה ל-Railway (production)
- [ ] ייבוא Excel בסביבת Railway
- [ ] הוספת שיראל + אזור אילת (ממתין לנתונים)
- [ ] עמוד היסטוריה מורחב למנהל
- [ ] אפשרות ייצוא דוח לאקסל
- [ ] Push notifications (אפשרי דרך PWA)
- [ ] בדיקת ייבוא Excel — לוודא שכל שדות יום ביקור ויום אספקה מגיעים כערך ולא נוסחה

---

## 📁 קבצים חשובים לשמור

1. `main.py` — כל הלוגיקה
2. `database.py` — הגדרת DB
3. `templates/*.html` — כל הממשקים
4. `import_data.py` — ייבוא Excel
5. `build_schedule.py` — יצירת לוח רמזור (בתיקיית GILI)
6. `סידור_עבודה_חדש.xlsx` — קובץ הלוח (לגיבוי!)
7. `sales.db` — מסד הנתונים (לגיבוי!)
