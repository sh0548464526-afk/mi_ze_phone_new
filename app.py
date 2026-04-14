from flask import Flask, request
import psycopg2
import os

app = Flask(__name__)

def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def last(val):
    if not val:
        return None
    return val[-1]

def count(val):
    if not val:
        return 0
    return len(val)

def get_name(phone):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM contacts WHERE phone=%s", (phone,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def save_name(phone, name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO contacts(phone,name) VALUES(%s,%s)", (phone, name))
    conn.commit()
    conn.close()

mapping = {
    "3": "א","33":"ב","333":"ג",
    "2": "ד","22":"ה","222":"ו",
    "6":"ז","66":"ח","666":"ט",
    "5":"י","55":"כ","555":"ך","5555":"ל",
    "4":"מ","44":"ם","444":"נ","4444":"ן",
    "9":"ס","99":"ע","999":"פ","9999":"ף",
    "8":"צ","88":"ץ","888":"ק",
    "7":"ר","77":"ש","777":"ת",
    "0":" ","1":"'"
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

@app.route("/", methods=["GET","POST"])
def api():

    q = request.args

    phone = last(q.getlist("phone"))
    nm = last(q.getlist("nm"))
    ym = last(q.getlist("ym"))

    enp_arr = q.getlist("enp")
    epi_arr = q.getlist("epi")

    enp_last = last(enp_arr)
    epi_last = last(epi_arr)

    enp_count = count(enp_arr)
    epi_count = count(epi_arr)

    if not phone:
        return "read=f-ep=phone,,,,,NO,yes,,,,,,,,no"

    name_in_db = get_name(phone)

    if not name_in_db:

        if not nm and not ym:
            return "read=f-nm=nm,,1,1,,NO,yes,,,123,,,,,no"

        if nm and not enp_arr:
            if nm == "1":
                return "read=f-enp=enp,,,,,NO,,,*/,,,,,,no"
            if nm == "2":
                return "go_to_folder=."
            if nm == "3":
                return "go_to_folder=.."

        if enp_count > epi_count:
            name = decode_enp(enp_last)
            return f"id_list_message=f-tni.t-{name}&read=f-epi=epi,,1,1,,NO,yes,,,12,,,,,no"

        if enp_count == epi_count and enp_count > 0:

            if epi_last == "1":
                name = decode_enp(enp_last)
                save_name(phone, name)

                # 🔥 שינוי שביקשת
                return "id_list_message=f-eno&read=f-epi=epi,,1,1,,NO,yes,,,12,,,,,no"

            if epi_last == "2":
                return "read=f-enp=enp,,,,,NO,,,*/,,,,,,no"

    else:

        if not ym:
            return f"id_list_message=f-n.t-{name_in_db}&read=f-ym=ym,,1,1,,NO,yes,,,1234,,,,,no"

        if ym == "1":
            return f"id_list_message=f-n.t-{name_in_db}&read=f-ym=ym,,1,1,,NO,yes,,,1234,,,,,no"

        if ym == "2":
            return f"id_list_message={spell_name(name_in_db)}&read=f-ym=ym,,1,1,,NO,yes,,,1234,,,,,no"

        if ym == "3":
            return "go_to_folder=."

        if ym == "4":
            return "go_to_folder=.."

    return "id_list_message=שגיאה"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)