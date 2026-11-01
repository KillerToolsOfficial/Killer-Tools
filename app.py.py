
from flask import Flask, request, render_template_string, send_file
from PIL import Image
from pypdf import PdfWriter, PdfReader
import qrcode
import io
from datetime import date

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

STYLE = """
<style>
:root{--blue:#2563eb;--navy:#102a56;--pale:#eff6ff;--ink:#172554;--muted:#64748b}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#f5f8ff;color:var(--ink)}
a{color:var(--blue);text-decoration:none}.topbar{background:#fff;border-bottom:1px solid #e5eaf3;position:sticky;top:0;z-index:5}.nav{max-width:1160px;margin:auto;padding:13px 20px;display:flex;align-items:center;justify-content:space-between;gap:18px}.brand{display:flex;align-items:center;gap:10px;color:var(--navy);font-weight:800;font-size:19px}.logo{width:39px;height:39px;border-radius:12px;background:linear-gradient(135deg,#12327a,#3b82f6);color:white;display:grid;place-items:center;font-weight:800}.navlinks{display:flex;gap:20px;flex-wrap:wrap;font-weight:600;font-size:14px}.navlinks a{color:#334155}.navlinks a:hover{color:var(--blue)}
.hero{background:linear-gradient(125deg,#102a56,#2563eb);color:white;text-align:center;padding:65px 18px 58px}.hero h1{font-size:clamp(30px,5vw,46px);margin:0 0 13px}.hero p{font-size:17px;color:#dbeafe;margin:0 auto 24px;max-width:650px;line-height:1.6}.hero .search{max-width:570px;margin:auto;background:white}
.container{max-width:1160px;margin:38px auto;padding:0 20px}.section-title{text-align:center;margin:0 0 8px;font-size:29px;color:var(--navy)}.section-sub{text-align:center;color:var(--muted);margin:0 0 25px}.search,input,textarea,select{width:100%;padding:14px 15px;margin:9px 0 16px;border:1px solid #cbd5e1;border-radius:10px;font-size:16px;background:#fff;color:var(--ink)}input:focus,textarea:focus,select:focus,.search:focus{outline:3px solid #bfdbfe;border-color:var(--blue)}textarea{min-height:145px;resize:vertical}.tools{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:19px;margin-top:24px}.card,.toolbox,.info-card{background:white;padding:24px;border-radius:17px;border:1px solid #e2e8f0;box-shadow:0 8px 24px #1e40af0d}.card{transition:transform .18s,box-shadow .18s}.card:hover{transform:translateY(-4px);box-shadow:0 13px 28px #1e40af1c}.card h2{font-size:18px;margin:0 0 9px;color:#1e3a8a}.card p{color:var(--muted);line-height:1.55;min-height:42px}.card a button{width:auto}.toolbox{max-width:800px;margin:auto}.toolbox h2{color:#1e3a8a;margin-top:0}button,.button{display:inline-block;background:var(--blue);color:white;border:0;padding:12px 19px;border-radius:9px;cursor:pointer;font-size:15px;font-weight:700}button:hover,.button:hover{background:#1d4ed8;color:white}.back{display:inline-block;margin-bottom:18px;font-weight:600}.result{background:#eff6ff;border:1px solid #bfdbfe;color:#1e3a8a;padding:18px;border-radius:11px;margin-top:20px;overflow-wrap:anywhere;line-height:1.6}.info-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px}.info-card h3{margin-top:0;color:#1e3a8a}.footer{background:#102a56;color:#dbeafe;margin-top:55px;padding:28px 18px;text-align:center}.footer a{color:white;margin:0 9px}.footer p{margin:8px 0;color:#bfdbfe}.empty{display:none;text-align:center;color:var(--muted);padding:25px}@media(max-width:650px){.nav{align-items:flex-start;flex-direction:column}.navlinks{gap:14px}.hero{padding:48px 15px}.container{margin:26px auto;padding:0 14px}.card,.toolbox{padding:19px}.card a button,button{width:100%;margin:6px 0}}
</style>
"""

PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Free online tools for calculations, text, images and PDF files."><title>{{ title }} | All-in-One Tools</title>
""" + STYLE + """
</head><body>
<div class="topbar"><nav class="nav"><a class="brand" href="/"><span class="logo">AO</span><span>All-in-One Tools</span></a><div class="navlinks"><a href="/">Home</a><a href="/#tools">Tools</a><a href="/about">About</a><a href="/contact">Contact</a></div></nav></div>
{% if title == "Home" %}<section class="hero"><h1>Simple Tools. Smarter Work.</h1><p>Free and easy online tools to help with everyday calculations, text, images and PDF tasks.</p>{{ hero_search|safe }}</section>{% endif %}
<main class="container">{% if title != "Home" %}<a class="back" href="/">← Back to Home</a>{% endif %}{{ content|safe }}{% if result %}<div class="result">{{ result|safe }}</div>{% endif %}</main>
<footer class="footer"><strong>All-in-One Tools</strong><p>Useful everyday tools in one simple place.</p><a href="/">Home</a><a href="/about">About</a><a href="/contact">Contact</a><p>© 2026 All-in-One Tools</p></footer>
</body></html>
"""

TOOLS = [
("🔢","Percentage Calculator","/percentage","Calculate marks percentage"),
("🔠","Word Counter","/word-counter","Count words and characters"),
("🔤","Text Case Converter","/text-case","Change text style"),
("🖼️","Image Resizer","/image-resizer","Resize your pictures"),
("📦","Image Compressor","/image-compressor","Reduce image file size"),
("🔳","QR Code Generator","/qr-code","Create QR codes"),
("🎂","Age Calculator","/age-calculator","Calculate your age"),
("📏","Unit Converter","/unit-converter","Convert measurement units"),
("📄","PDF Merger","/pdf-merger","Join multiple PDF files"),
("📖","PDF Text Extractor","/pdf-text","Extract text from PDF")
]

@app.route("/")
def home():
    cards = ""
    for icon,name,url,description in TOOLS:
        cards += f"""
        <article class="card">
          <h2>{icon} {name}</h2><p>{description}</p>
          <a href="{url}"><button type="button">Open Tool</button></a>
        </article>"""
    content = f"""
    <section id="tools"><h2 class="section-title">Explore Our Tools</h2>
    <p class="section-sub">Choose a tool and get your task done in a few clicks.</p>
    <div class="tools" id="toolCards">{cards}</div><p class="empty" id="noTools">No tools found. Try another search.</p></section>
    <script>function searchTools(){{let q=document.getElementById('toolSearch').value.toLowerCase();let shown=0;document.querySelectorAll('.card').forEach(c=>{{let ok=c.innerText.toLowerCase().includes(q);c.style.display=ok?'':'none';if(ok)shown++;}});document.getElementById('noTools').style.display=shown?'none':'block';}}</script>
    """
    hero_search = '<input class="search" id="toolSearch" placeholder="Search tools, e.g. percentage, PDF, image..." oninput="searchTools()" aria-label="Search tools">'
    return render_template_string(PAGE,title="Home",content=content,hero_search=hero_search)

@app.route("/about")
def about():
    content = """
    <h1 class="section-title">About All-in-One Tools</h1>
    <p class="section-sub">A simple place for useful everyday online tools.</p>
    <div class="info-grid">
      <div class="info-card"><h3>Our Purpose</h3><p>We bring common tasks together in one easy-to-use website, so visitors can quickly find the tool they need.</p></div>
      <div class="info-card"><h3>Easy to Use</h3><p>Our tools are designed with clear labels and simple steps for students, families and everyday users.</p></div>
      <div class="info-card"><h3>Available Tools</h3><p>Use calculators, text tools, image tools, QR code generation and PDF utilities from the home page.</p></div>
    </div>
    """
    return render_template_string(PAGE,title="About",content=content)

@app.route("/contact",methods=["GET","POST"])
def contact():
    result=""
    content = """
    <h1 class="section-title">Contact Us</h1>
    <p class="section-sub">Have a suggestion or found a problem? Send a message using the form below.</p>
    <div class="toolbox"><form method="POST">
      <label>Your Name</label><input name="name" maxlength="80" required>
      <label>Your Email</label><input type="email" name="email" maxlength="120" required>
      <label>Message</label><textarea name="message" maxlength="2000" required></textarea>
      <button type="submit">Submit Message</button>
    </form></div>
    """
    if request.method == "POST":
        result = "Thank you! This demo form is working, but messages are not emailed or saved yet. An email service must be connected to receive messages."
    return render_template_string(PAGE,title="Contact",content=content,result=result)

@app.route("/percentage",methods=["GET","POST"])
def percentage():
    result=""
    if request.method=="POST":
        try:
            total=float(request.form["total"])
            obtained=float(request.form["obtained"])
            if total<=0 or obtained<0 or obtained>total:
                result="Please enter valid marks."
            else:
                result=f"Your Percentage: {(obtained/total)*100:.2f}%"
        except ValueError:
            result="Enter valid numbers."

    content="""
    <form method="POST">
    <label>Total Marks</label>
    <input type="number" step="any" name="total" required>
    <label>Obtained Marks</label>
    <input type="number" step="any" name="obtained" required>
    <button>Calculate Percentage</button>
    </form>
    """
    return render_template_string(PAGE,title="Percentage Calculator",
                                  content=content,result=result)

@app.route("/word-counter",methods=["GET","POST"])
def word_counter():
    result=""
    if request.method=="POST":
        text=request.form.get("text","")
        words=len(text.split())
        characters=len(text)
        sentences=sum(text.count(x) for x in ".!?")
        result=f"Words: {words}<br>Characters: {characters}<br>Sentences: {sentences}"

    content="""
    <form method="POST">
    <textarea name="text" placeholder="Write or paste your text here..."></textarea>
    <button>Count Words</button>
    </form>
    """
    return render_template_string(PAGE,title="Word Counter",
                                  content=content,result=result)

@app.route("/text-case",methods=["GET","POST"])
def text_case():
    result=""
    if request.method=="POST":
        text=request.form.get("text","")
        action=request.form.get("action")
        if action=="upper":
            result=text.upper()
        elif action=="lower":
            result=text.lower()
        elif action=="title":
            result=text.title()

    content="""
    <form method="POST">
    <textarea name="text" placeholder="Enter your text..."></textarea>
    <button name="action" value="upper">UPPERCASE</button>
    <button name="action" value="lower">lowercase</button>
    <button name="action" value="title">Title Case</button>
    </form>
    """
    return render_template_string(PAGE,title="Text Case Converter",
                                  content=content,result=result)

@app.route("/image-resizer",methods=["GET","POST"])
def image_resizer():
    content="""
    <form method="POST" enctype="multipart/form-data">
    <label>Select Image</label>
    <input type="file" name="image" accept="image/*" required>
    <label>New Width (pixels)</label>
    <input type="number" name="width" min="1" max="5000" required>
    <label>New Height (pixels)</label>
    <input type="number" name="height" min="1" max="5000" required>
    <button>Resize Image</button>
    </form>
    """
    if request.method=="POST":
        try:
            image=Image.open(request.files["image"])
            width=int(request.form["width"])
            height=int(request.form["height"])
            if not (1<=width<=5000 and 1<=height<=5000):
                raise ValueError()
            image=image.convert("RGB")
            image=image.resize((width,height))
            output=io.BytesIO()
            image.save(output,format="JPEG",quality=90)
            output.seek(0)
            return send_file(output,as_attachment=True,
                             download_name="resized.jpg",
                             mimetype="image/jpeg")
        except Exception:
            return render_template_string(PAGE,title="Image Resizer",
                content=content,result="Invalid image or dimensions.")
    return render_template_string(PAGE,title="Image Resizer",content=content)

@app.route("/image-compressor",methods=["GET","POST"])
def image_compressor():
    content="""
    <form method="POST" enctype="multipart/form-data">
    <label>Select Image</label>
    <input type="file" name="image" accept="image/*" required>
    <label>Image Quality (20 to 95)</label>
    <input type="number" name="quality" min="20" max="95" value="65" required>
    <button>Compress Image</button>
    </form>
    """
    if request.method=="POST":
        try:
            image=Image.open(request.files["image"]).convert("RGB")
            quality=int(request.form["quality"])
            if not 20<=quality<=95:
                raise ValueError()
            output=io.BytesIO()
            image.save(output,format="JPEG",quality=quality,optimize=True)
            output.seek(0)
            return send_file(output,as_attachment=True,
                download_name="compressed.jpg",mimetype="image/jpeg")
        except Exception:
            return render_template_string(PAGE,title="Image Compressor",
                content=content,result="Invalid image or quality.")
    return render_template_string(PAGE,title="Image Compressor",content=content)

@app.route("/qr-code",methods=["GET","POST"])
def qr_code():
    content="""
    <form method="POST">
    <label>Enter Text or Website Link</label>
    <input type="text" name="data" required>
    <button>Generate QR Code</button>
    </form>
    """
    if request.method=="POST":
        data=request.form.get("data","").strip()
        if data:
            qr=qrcode.make(data)
            output=io.BytesIO()
            qr.save(output,format="PNG")
            output.seek(0)
            return send_file(output,as_attachment=True,
                download_name="my_qr_code.png",mimetype="image/png")
    return render_template_string(PAGE,title="QR Code Generator",content=content)

@app.route("/age-calculator",methods=["GET","POST"])
def age_calculator():
    result=""
    if request.method=="POST":
        try:
            dob=date.fromisoformat(request.form["dob"])
            today=date.today()
            if dob>today:
                result="Date of birth cannot be in the future."
            else:
                years=today.year-dob.year
                months=today.month-dob.month
                days=today.day-dob.day
                if days<0:
                    months-=1
                    from calendar import monthrange
                    previous_month=today.month-1 or 12
                    previous_year=today.year if today.month>1 else today.year-1
                    days+=monthrange(previous_year,previous_month)[1]
                if months<0:
                    years-=1
                    months+=12
                result=f"Your Age: {years} Years, {months} Months, {days} Days"
        except ValueError:
            result="Please enter a valid date."

    content="""
    <form method="POST">
    <label>Date of Birth</label>
    <input type="date" name="dob" required>
    <button>Calculate Age</button>
    </form>
    """
    return render_template_string(PAGE,title="Age Calculator",
                                  content=content,result=result)

@app.route("/unit-converter",methods=["GET","POST"])
def unit_converter():
    result=""
    if request.method=="POST":
        try:
            value=float(request.form["value"])
            unit=request.form["unit"]
            conversions={
                "km-mile":value*0.621371,
                "mile-km":value*1.60934,
                "kg-pound":value*2.20462,
                "pound-kg":value/2.20462,
                "cm-inch":value/2.54,
                "inch-cm":value*2.54,
                "c-f":(value*9/5)+32,
                "f-c":(value-32)*5/9
            }
            if unit not in conversions:
                raise ValueError()
            result=f"Converted Result: {conversions[unit]:.4f}"
        except ValueError:
            result="Please enter a valid value."

    content="""
    <form method="POST">
    <label>Enter Value</label>
    <input type="number" step="any" name="value" required>
    <label>Choose Conversion</label>
    <select name="unit">
    <option value="km-mile">Kilometers to Miles</option>
    <option value="mile-km">Miles to Kilometers</option>
    <option value="kg-pound">Kilograms to Pounds</option>
    <option value="pound-kg">Pounds to Kilograms</option>
    <option value="cm-inch">Centimeters to Inches</option>
    <option value="inch-cm">Inches to Centimeters</option>
    <option value="c-f">Celsius to Fahrenheit</option>
    <option value="f-c">Fahrenheit to Celsius</option>
    </select>
    <button>Convert</button>
    </form>
    """
    return render_template_string(PAGE,title="Unit Converter",
                                  content=content,result=result)

@app.route("/pdf-merger",methods=["GET","POST"])
def pdf_merger():
    content="""
    <form method="POST" enctype="multipart/form-data">
    <label>Select at least two PDF files</label>
    <input type="file" name="pdfs" accept=".pdf,application/pdf"
           multiple required>
    <button>Merge PDF Files</button>
    </form>
    """
    if request.method=="POST":
        try:
            files=request.files.getlist("pdfs")
            if len(files)<2:
                raise ValueError()
            writer=PdfWriter()
            for file in files:
                if not file.filename.lower().endswith(".pdf"):
                    raise ValueError()
                writer.append(file.stream)
            output=io.BytesIO()
            writer.write(output)
            output.seek(0)
            writer.close()
            return send_file(output,as_attachment=True,
                download_name="merged.pdf",mimetype="application/pdf")
        except Exception:
            return render_template_string(PAGE,title="PDF Merger",
                content=content,result="Could not merge these PDF files.")
    return render_template_string(PAGE,title="PDF Merger",content=content)

@app.route("/pdf-text",methods=["GET","POST"])
def pdf_text():
    content="""
    <form method="POST" enctype="multipart/form-data">
    <label>Select PDF File</label>
    <input type="file" name="pdf" accept=".pdf,application/pdf" required>
    <button>Extract Text</button>
    </form>
    """
    if request.method=="POST":
        try:
            file=request.files["pdf"]
            if not file.filename.lower().endswith(".pdf"):
                raise ValueError()
            reader=PdfReader(file.stream)
            text="\n\n".join(page.extract_text() or "" for page in reader.pages)
            if not text.strip():
                text="No extractable text found. This PDF may contain scanned images."
            return render_template_string(PAGE,title="PDF Text Extractor",
                content=content,result="<pre style=\'white-space:pre-wrap\'>" + __import__('html').escape(text) + "</pre>")
        except Exception:
            return render_template_string(PAGE,title="PDF Text Extractor",
                content=content,result="Could not read this PDF.")

@app.errorhandler(413)
def too_large(error):
    return "File too large. Maximum upload size is 20 MB.",413

if __name__=="__main__":
    app.run(debug=True)
