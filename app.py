from flask import Flask, request
import psycopg2
import os

app = Flask(__name__)

# חיבור למסד (תשים ב-Render ENV בשם DATABASE_URL)
conn = psycopg2.connect(os.environ['DATABASE_URL'])
conn.autocommit = True


# =====================
# פונקציות עזר
# =====================

def get_last(val):
    if not val:
        return None
    if isinstance(val, list):
        return val[-1]
    return val


def count(val):
    if not val:
        return 0
    if isinstance(val, list):
        return len(val)
    return 1


# =====================
# תרגום מספרים לשם
# =====================

mapping = {
    "3": "א", "33": "ב", "333": "ג",
    "2": "ד", "22": "ה", "222": "ו",
    "6": "ז", "66": "ח", "666": "ט",
    "5": "י", "55": "כ", "555": "ך", "5555": "ל",
    "4": "מ", "44": "ם", "444": "נ", "4444": "ן",
    "9": "ס", "99": "ע", "999": "פ", "9999": "ף",
    "8": "צ", "88": "ץ", "888": "ק",
    "7": "ר", "77": "ש", "777": "ת",
    "0": " ",
    "1": "'"
}


def decode_enp(code):
    result = []
    current = ""

    for ch in code:
        if ch == "/":
            if current in mapping:
                result.append(mapping[current])
            current = ""
            continue

        if not current or ch == current[0]:
            current += ch
        else:
            if current in mapping:
                result.append(mapping[current])
            current = ch

    if current in mapping:
        result.append(mapping[current])

    return "".join(result)


# =====================
# איות שם
# =====================

def spell_name(name):
    parts = ["f-in"]

    for ch in name:
        if ch == " ":
            parts.append("f-רווח")
        elif ch == "'":
            parts.append("f-גרש")
        else:
            parts.append(f"f-{ch}")

    return ".".join(parts)


# =====================
# DB
# =====================

def get_name(phone):
    cur = conn.cursor()
    cur.execute("SELECT name FROM contacts WHERE phone=%s", (phone,))
    row = cur.fetchone()
    return row[0] if row else None


def save_name(phone, name):
    cur = conn.cursor()
    cur.execute("INSERT INTO contacts(phone,name) VALUES(%s,%s)", (phone, name))


# =====================
# ה־API
# =====================

@app.route("/", methods=["GET", "POST"])
def api():
    q = request.args

    phone = get_last(q.getlist("phone"))
    nm = get_last(q.getlist("nm"))
    ym = get_last(q.getlist("ym"))
    enp_arr = q.getlist("enp")
    epi_arr = q.getlist("epi")

    enp_last = get_last(enp_arr)
    epi_last = get_last(epi_arr)

    enp_count = count(enp_arr)
    epi_count = count(epi_arr)

    # =====================
    # 1. אין טלפון
    # =====================
    if not phone:
        return "read=f-ep=phone,,,,,NO,yes,,,,,,,,no"

    # =====================
    # בדיקת DB
    # =====================
    name_in_db = get_name(phone)

    # =====================
    # מצב: אין שם במסד
    # =====================
    if not name_in_db:

        # אין nm ו ym
        if not nm and not ym:
            return "read=f-nm=nm,,1,1,,NO,yes,,,123,,,,,no"

        # בחירת nm
        if nm and not enp_arr:
            if nm == "2":
                return "go_to_folder=."
            if nm == "3":
                return "go_to_folder=.."
            if nm == "1":
                return "read=f-enp=enp,,,,,NO,yes,,*/,,,,,,no"

        # יש enp חדש
        if enp_count > epi_count:
            name = decode_enp(enp_last)
            return f"id_list_message=f-tni.t-{name}&read=f-epi=epi,,1,1,,NO,yes,,,12"

        # יש אישור
        if enp_count == epi_count and enp_count > 0:

            if epi_last == "1":
                name = decode_enp(enp_last)
                save_name(phone, name)
                return "id_list_message=f-eno"

            if epi_last == "2":
                return "read=f-enp=enp,,,,,NO,yes,,*/,,,,,,no"

    # =====================
    # מצב: יש שם במסד
    # =====================
    else:

        # תפריט ראשוני
        if not ym:
            return f"id_list_message=f-n.t-{name_in_db}&read=f-ym=ym,,1,1,,NO,yes,,,1234,,,,,no"

        # ym פעולות
        if ym == "3":
            return "go_to_folder=."

        if ym == "4":
            return "go_to_folder=.."

        if ym == "1":
            return f"id_list_message=f-n.t-{name_in_db}&read=f-ym=ym,,1,1,,NO,yes,,,1234,,,,,no"

        if ym == "2":
            spelled = spell_name(name_in_db)
            return f"id_list_message={spelled}&read=f-ym=ym,,1,1,,NO,yes,,,1234,,,,,no"

    return "id_list_message=שגיאה"


# =====================
# הרצה
# =====================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)