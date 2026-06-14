import json

def append_disclosure():
    with open('Project_2.ipynb', 'r', encoding='utf-8') as f:
        nb = json.load(f)

    disclosure_text = """<div dir="rtl">

## 🪖 הצהרה על שימוש בכלי AI 🤖

עקב שירות מילואים פעיל (ועומס החיים הסטודנטיאליים הכללי), נעזרתי בכלי בינה מלאכותית כעזר למידה, ייעול תהליכי תכנות וניסוח. הבסיס המהותי לדו"ח ולחישובים (סינון, ספקטרום, גזירת ה-IAF) נשען לחלוטין על חומר הקורס, ההרצאות והדרישות. ה-AI סייע בעיקר בכתיבת קוד הויזואליזציה (Matplotlib), ניהול התיקייה ב-Git, ועיצוב דפי ה-HTML וה-PDF כך שיהיו קריאים ויפים.

<sub>וכן, כמו פעם קודמת - גם את ההצהרה הזאת ניסחתי (קצת) בעזרת AI. כנות זה שם המשחק.</sub>

</div>"""

    # Check if disclosure is already there to avoid duplicates
    if nb['cells'] and 'הצהרה על שימוש בכלי AI' in "".join(nb['cells'][-1].get('source', [])):
        print("Disclosure already exists.")
        return

    new_cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + '\n' for line in disclosure_text.split('\n')]
    }
    # remove trailing newline from last line
    new_cell["source"][-1] = new_cell["source"][-1].rstrip('\n')

    nb['cells'].append(new_cell)

    with open('Project_2.ipynb', 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)

if __name__ == '__main__':
    append_disclosure()
