import os, json, re
from datetime import datetime, timedelta, date
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "eventops-demo-secret")
DB_PATH = "/tmp/eventops.db" if os.getenv("VERCEL") else os.path.join(app.instance_path, "eventops.db")
os.makedirs(app.instance_path, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    phone = db.Column(db.String(40))
    password_hash = db.Column(db.String(255), nullable=False)
    organization = db.Column(db.String(160))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(180), nullable=False)
    event_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    event_date = db.Column(db.Date)
    registration_open = db.Column(db.Date)
    registration_close = db.Column(db.Date)
    target_registrations = db.Column(db.Integer, default=0)
    venue = db.Column(db.String(200))
    goals = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160))
    role = db.Column(db.String(120))
    responsibilities = db.Column(db.Text)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(220), nullable=False)
    description = db.Column(db.Text)
    owner = db.Column(db.String(120))
    due_date = db.Column(db.Date)
    priority = db.Column(db.String(30), default="Medium")
    status = db.Column(db.String(30), default="Not Started")
    depends_on = db.Column(db.String(220))
    phase = db.Column(db.String(120))
    source = db.Column(db.String(50), default="AI")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    organization = db.Column(db.String(160))
    email = db.Column(db.String(160))
    phone = db.Column(db.String(60))
    status = db.Column(db.String(40), default="Not Contacted")
    last_contacted = db.Column(db.Date)
    next_followup = db.Column(db.Date)
    notes = db.Column(db.Text)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(220), nullable=False)
    platform = db.Column(db.String(80))
    post_date = db.Column(db.Date)
    owner = db.Column(db.String(120))
    status = db.Column(db.String(40), default="Pending")
    caption = db.Column(db.Text)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    participant_name = db.Column(db.String(160))
    email = db.Column(db.String(160))
    source = db.Column(db.String(100))
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    kind = db.Column(db.String(40), default="info")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    customer = db.Column(db.String(160), nullable=False)
    channel = db.Column(db.String(60), default="Email")
    subject = db.Column(db.String(220), nullable=False)
    message = db.Column(db.Text)
    category = db.Column(db.String(80), default="General")
    priority = db.Column(db.String(30), default="Medium")
    status = db.Column(db.String(40), default="Open")
    owner = db.Column(db.String(120))
    sla_due = db.Column(db.DateTime)
    ai_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DocumentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(220), nullable=False)
    doc_type = db.Column(db.String(100), default="Other")
    status = db.Column(db.String(40), default="Uploaded")
    extracted_text = db.Column(db.Text)
    ai_summary = db.Column(db.Text)
    key_fields = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    company = db.Column(db.String(180), nullable=False)
    contact = db.Column(db.String(160))
    stage = db.Column(db.String(60), default="Lead")
    value = db.Column(db.Float, default=0)
    probability = db.Column(db.Integer, default=20)
    next_action = db.Column(db.String(220))
    next_date = db.Column(db.Date)
    owner = db.Column(db.String(120))
    notes = db.Column(db.Text)

class KPI(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(160), nullable=False)
    value = db.Column(db.Float, default=0)
    target = db.Column(db.Float, default=0)
    unit = db.Column(db.String(40), default="")
    period = db.Column(db.String(60), default="Current")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class InternalRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, nullable=False)
    requester = db.Column(db.String(160), nullable=False)
    request_type = db.Column(db.String(100), default="General")
    title = db.Column(db.String(220), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(30), default="Medium")
    status = db.Column(db.String(40), default="Open")
    assignee = db.Column(db.String(120))
    due_date = db.Column(db.Date)
    ai_recommendation = db.Column(db.Text)

def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None

@app.context_processor
def inject():
    return {"current_user": current_user(), "today": date.today()}

def login_required():
    return "user_id" in session

def parse_date(v):
    if not v: return None
    try: return datetime.strptime(v, "%Y-%m-%d").date()
    except: return None

def generate_workflow(event):
    start = event.registration_open or (date.today() + timedelta(days=1))
    end = event.event_date or (start + timedelta(days=21))
    span = max((end-start).days, 7)
    members = Member.query.filter_by(event_id=event.id).all()
    names = [m.name for m in members] or ["Team Lead"]
    rolemap = {m.role.lower(): m.name for m in members if m.role}
    def owner(words, fallback_index=0):
        for w in words:
            for r,n in rolemap.items():
                if w in r: return n
        return names[fallback_index % len(names)]

    templates = [
        ("Planning","Finalize event requirements and success metrics",0.03,"High",None),
        ("Web & Registration","Create registration form / landing page",0.14,"High","Finalize event requirements and success metrics"),
        ("Creative","Design launch poster and event identity",0.17,"High",None),
        ("Promotion","Publish launch announcement",0.24,"High","Design launch poster and event identity"),
        ("Outreach","Contact colleges, communities and partners",0.31,"High","Create registration form / landing page"),
        ("Promotion","Publish promotion post #2",0.43,"Medium","Publish launch announcement"),
        ("Outreach","Run first follow-up cycle",0.50,"High","Contact colleges, communities and partners"),
        ("Promotion","Publish promotion post #3",0.62,"Medium","Run first follow-up cycle"),
        ("Operations","Finalize volunteers, venue and logistics",0.72,"High",None),
        ("Promotion","Final registration push",0.84,"High","Publish promotion post #3"),
        ("Operations","Participant confirmation and final briefing",0.92,"High","Finalize volunteers, venue and logistics"),
        ("Event","Event-day readiness check",0.98,"High","Participant confirmation and final briefing"),
    ]
    created=[]
    for phase,title,pct,priority,dep in templates:
        d = start + timedelta(days=max(0, int(span*pct)))
        if d >= end: d = end - timedelta(days=1) if end > start else end
        if phase in ("Promotion","Creative"): own=owner(["pr","media","creative","marketing"],1)
        elif phase=="Web & Registration": own=owner(["web","tech","development"],0)
        elif phase=="Outreach": own=owner(["pr","outreach"],0)
        elif phase=="Operations": own=owner(["operations","ops"],0)
        else: own=names[0]
        t=Task(event_id=event.id,title=title,description=f"AI-generated action for {event.name}.",owner=own,due_date=d,priority=priority,status="Not Started",depends_on=dep,phase=phase,source="AI")
        db.session.add(t); created.append(t)
    # Content schedule
    content_items=[
        ("Launch announcement",0.24),("Promotion post #2",0.43),("Promotion post #3",0.62),("Final registration push",0.84)
    ]
    for title,pct in content_items:
        d=start+timedelta(days=max(0,int(span*pct)))
        if d>=end: d=end-timedelta(days=1)
        db.session.add(Content(event_id=event.id,title=title,platform="Instagram",post_date=d,owner=owner(["pr","media"],1),status="Pending",caption=f"AI suggested campaign content for {event.name}."))
    db.session.add(Activity(event_id=event.id,message="AI generated the initial workflow, dependencies and content calendar.",kind="success"))
    db.session.commit()
    return created

def seed():
    db.create_all()
    if not User.query.filter_by(email="demo@eventops.ai").first():
        u=User(name="Demo Admin",email="demo@eventops.ai",phone="9999999999",password_hash=generate_password_hash("demo123"),organization="Demo Team")
        db.session.add(u); db.session.commit()
        e=Event(owner_id=u.id,name="AndroForge Demo Hackathon",event_type="Hackathon",description="A 24-hour student hackathon demo event.",event_date=date.today()+timedelta(days=18),registration_open=date.today(),registration_close=date.today()+timedelta(days=14),target_registrations=200,venue="Campus Innovation Hall",goals="Drive registrations, coordinate PR/media/web and deliver a smooth event.")
        db.session.add(e); db.session.commit()
        ms=[
            ("Priya","pr@demo.ai","PR Lead","Outreach, registrations and follow-ups"),
            ("Arun","web@demo.ai","Web Lead","Registration page and website"),
            ("Kavi","media@demo.ai","Media Lead","Posters, creatives and social media"),
            ("Riya","ops@demo.ai","Operations Lead","Venue, volunteers and logistics"),
            ("Sam","tech@demo.ai","Tech Lead","Forms, integrations and technical support")
        ]
        for n,em,r,resp in ms: db.session.add(Member(event_id=e.id,name=n,email=em,role=r,responsibilities=resp))
        db.session.commit()
        generate_workflow(e)
        contacts=[
            ("ABC College","ABC College","abc@example.com","9876500001","Interested",date.today()-timedelta(days=1),date.today()+timedelta(days=1)),
            ("XYZ Institute","XYZ Institute","xyz@example.com","9876500002","Call Back",date.today()-timedelta(days=2),date.today()),
            ("Campus Coding Club","Campus Coding Club","club@example.com","9876500003","Contacted",date.today()-timedelta(days=1),date.today()+timedelta(days=3)),
        ]
        for x in contacts:
            db.session.add(Contact(event_id=e.id,name=x[0],organization=x[1],email=x[2],phone=x[3],status=x[4],last_contacted=x[5],next_followup=x[6]))
        for i in range(147):
            db.session.add(Registration(event_id=e.id,participant_name=f"Participant {i+1}",email=f"p{i+1}@example.com",source=["Instagram","College Outreach","Website"][i%3]))
        db.session.add(Activity(event_id=e.id,message="Demo data loaded: 147 registrations and 3 outreach contacts.",kind="info"))
        tickets=[
            ("Asha","Email","Registration link not opening","The registration page shows an error when I try to submit.","Arun"),
            ("Rahul","WhatsApp","Payment receipt question","Please help with the invoice/receipt for our team.","Priya"),
            ("Meena","Website","Venue timing","Can you confirm the event start time?","Riya")
        ]
        for customer,channel,subject,msg,owner in tickets:
            t=SupportTicket(event_id=e.id,customer=customer,channel=channel,subject=subject,message=msg,owner=owner); support_ai(t); db.session.add(t)
        docs=[
            ("Venue Agreement","Agreement","Event venue: Campus Innovation Hall. Deadline: 2026-09-25. Owner: Riya. Amount: 25000."),
            ("Partner Brief","Brief","Contact: partner@example.com. Date: 2026-10-05. Status: Pending. Owner: Priya.")
        ]
        for n,typ,txt in docs:
            d=DocumentRecord(event_id=e.id,name=n,doc_type=typ,extracted_text=txt); document_ai(d); db.session.add(d)
        deals=[
            ("TechCorp","Anil","Lead",50000,20,"Send sponsorship deck",date.today()+timedelta(days=2),"Priya"),
            ("CodeHub","Divya","Proposal",80000,60,"Schedule partner call",date.today()+timedelta(days=1),"Priya"),
            ("CloudNine","Karthik","Negotiation",120000,75,"Confirm package",date.today()+timedelta(days=4),"Demo Admin")
        ]
        for company,contact,stage,val,prob,next_action,next_date,owner in deals: db.session.add(Deal(event_id=e.id,company=company,contact=contact,stage=stage,value=val,probability=prob,next_action=next_action,next_date=next_date,owner=owner))
        kpis=[("Registration conversion",73,80,"%"),("Tasks completed",42,70,"%"),("Support SLA met",91,95,"%"),("Partner response rate",68,75,"%")]
        for n,v,t,u in kpis: db.session.add(KPI(event_id=e.id,name=n,value=v,target=t,unit=u,period="Current event"))
        requests=[("Priya","IT Access","Create shared drive for event team","Need a central place for event documents.","High","Sam",date.today()+timedelta(days=1)),("Kavi","Creative","Approve final sponsor logo","Need approval before next promotion post.","Medium","Priya",date.today()+timedelta(days=2))]
        for requester,typ,title,desc,pri,assignee,due in requests: db.session.add(InternalRequest(event_id=e.id,requester=requester,request_type=typ,title=title,description=desc,priority=pri,assignee=assignee,due_date=due,ai_recommendation=f"AI recommendation: route this {pri.lower()} priority request to {assignee} and track it against the workflow."))
        db.session.commit()

@app.route("/")
def index():
    if login_required(): return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=User.query.filter_by(email=request.form.get("email","").strip().lower()).first()
        if u and check_password_hash(u.password_hash,request.form.get("password","")):
            session["user_id"]=u.id; return redirect(url_for("dashboard"))
        flash("Invalid email or password.","error")
    return render_template("login.html")

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.","error")
        else:
            u=User(name=request.form.get("name"),email=email,phone=request.form.get("phone"),organization=request.form.get("organization"),password_hash=generate_password_hash(request.form.get("password")))
            db.session.add(u); db.session.commit(); session["user_id"]=u.id
            return redirect(url_for("dashboard"))
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    if not login_required(): return redirect(url_for("login"))
    events=Event.query.filter_by(owner_id=session["user_id"]).order_by(Event.event_date.asc()).all()
    if not events:
        return render_template("dashboard.html",events=[],stats={},alerts=[])
    active=events[0]
    tasks=Task.query.filter_by(event_id=active.id).all()
    contacts=Contact.query.filter_by(event_id=active.id).all()
    regs=Registration.query.filter_by(event_id=active.id).count()
    stats={"events":len(events),"pending":sum(t.status not in ("Completed",) for t in tasks),"overdue":sum(t.due_date and t.due_date<date.today() and t.status!="Completed" for t in tasks),"followups":sum(c.next_followup and c.next_followup<=date.today() and c.status not in ("Confirmed","Not Interested") for c in contacts),"registrations":regs,"target":active.target_registrations}
    alerts=analyze(active.id)
    return render_template("dashboard.html",events=events,active=active,stats=stats,alerts=alerts,tasks=tasks[:6])

@app.route("/event/new", methods=["GET","POST"])
def new_event():
    if not login_required(): return redirect(url_for("login"))
    if request.method=="POST":
        e=Event(owner_id=session["user_id"],name=request.form.get("name"),event_type=request.form.get("event_type"),description=request.form.get("description"),event_date=parse_date(request.form.get("event_date")),registration_open=parse_date(request.form.get("registration_open")),registration_close=parse_date(request.form.get("registration_close")),target_registrations=int(request.form.get("target_registrations") or 0),venue=request.form.get("venue"),goals=request.form.get("goals"))
        db.session.add(e); db.session.commit()
        names=request.form.getlist("member_name"); emails=request.form.getlist("member_email"); roles=request.form.getlist("member_role"); resps=request.form.getlist("member_resp")
        for i,n in enumerate(names):
            if n.strip(): db.session.add(Member(event_id=e.id,name=n,email=emails[i] if i<len(emails) else "",role=roles[i] if i<len(roles) else "",responsibilities=resps[i] if i<len(resps) else ""))
        db.session.commit()
        generate_workflow(e)
        flash("AI workflow generated successfully.","success")
        return redirect(url_for("event_overview",event_id=e.id))
    return render_template("new_event.html")

def get_event(eid):
    e=Event.query.get_or_404(eid)
    if e.owner_id!=session.get("user_id"): return None
    return e

def support_ai(ticket):
    text=((ticket.subject or "")+" "+(ticket.message or "")).lower()
    if any(w in text for w in ["refund","payment","charged","invoice"]): category="Billing"
    elif any(w in text for w in ["error","bug","login","website","not working"]): category="Technical"
    elif any(w in text for w in ["register","registration","ticket","event"]): category="Registration"
    else: category="General"
    if any(w in text for w in ["urgent","blocked","cannot","failed","today"]): priority="High"
    elif any(w in text for w in ["when","question","help"]): priority="Medium"
    else: priority="Low"
    ticket.category, ticket.priority = category, priority
    ticket.ai_summary=f"AI triage: {category} issue, {priority.lower()} priority. Suggested next step: acknowledge the customer, resolve or route to the appropriate owner, and record the outcome."

    return ticket

def document_ai(doc):
    text=(doc.extracted_text or "").strip()
    words=text.split()
    doc.ai_summary=("AI summary: "+" ".join(words[:45])+("…" if len(words)>45 else "")) if text else "AI summary: No extracted text supplied yet. Add document text for automatic summarization and key-field extraction."
    keys=[]
    for label in ["date","deadline","amount","email","phone","venue","owner","status"]:
        if label in text.lower(): keys.append(label)
    doc.key_fields=", ".join(keys) if keys else "No obvious key fields detected"
    doc.status="Processed"
    return doc

def business_insights(eid):
    e=get_event(eid)
    if not e: return []
    tasks=Task.query.filter_by(event_id=eid).all(); tickets=SupportTicket.query.filter_by(event_id=eid).all(); deals=Deal.query.filter_by(event_id=eid).all(); regs=Registration.query.filter_by(event_id=eid).count()
    insights=[]
    if tickets:
        open_t=sum(t.status not in ("Resolved","Closed") for t in tickets)
        if open_t: insights.append({"kind":"warning","title":"Customer support queue","message":f"{open_t} support ticket(s) still need action. AI triage can route high-priority issues first."})
    if deals:
        pipeline=sum(d.value for d in deals if d.stage not in ("Won","Lost")); weighted=sum(d.value*(d.probability/100) for d in deals if d.stage not in ("Won","Lost"))
        insights.append({"kind":"info","title":"Sales pipeline","message":f"Pipeline value is ₹{pipeline:,.0f}; weighted pipeline is about ₹{weighted:,.0f}. Focus on deals with an upcoming next action."})
    if e.target_registrations:
        pct=regs/e.target_registrations*100
        insights.append({"kind":"success" if pct>=75 else "info","title":"Demand signal","message":f"Registrations are at {pct:.0f}% of target. Use outreach and promotion tasks to close the gap."})
    owners={}
    for t in tasks:
        if t.status!="Completed": owners[t.owner]=owners.get(t.owner,0)+1
    if owners:
        who,maxn=max(owners.items(),key=lambda x:x[1]); insights.append({"kind":"warning" if maxn>=5 else "info","title":"Employee productivity","message":f"{who} currently owns {maxn} open task(s). AI recommends reviewing workload and dependencies."})
    return insights

def analyze(eid):
    e=get_event(eid)
    if not e: return []
    tasks=Task.query.filter_by(event_id=eid).all()
    contacts=Contact.query.filter_by(event_id=eid).all()
    regs=Registration.query.filter_by(event_id=eid).count()
    alerts=[]
    overdue=[t for t in tasks if t.due_date and t.due_date<date.today() and t.status!="Completed"]
    if overdue: alerts.append({"kind":"danger","title":"Overdue work","message":f"{len(overdue)} task(s) are overdue. Owners should act now."})
    blocked=[t for t in tasks if t.depends_on and t.status!="Completed" and any(x.title==t.depends_on and x.status not in ("Completed",) for x in tasks)]
    if blocked: alerts.append({"kind":"warning","title":"Dependency risk","message":f"{len(blocked)} task(s) are waiting on unfinished dependencies."})
    overloaded={}
    for t in tasks:
        if t.status!="Completed": overloaded[t.owner]=overloaded.get(t.owner,0)+1
    if overloaded:
        who,count=max(overloaded.items(),key=lambda x:x[1])
        if count>=5: alerts.append({"kind":"warning","title":"Workload imbalance","message":f"{who} has {count} pending tasks. Consider rebalancing."})
    due_contacts=[c for c in contacts if c.next_followup and c.next_followup<=date.today() and c.status not in ("Confirmed","Not Interested")]
    if due_contacts: alerts.append({"kind":"warning","title":"Follow-ups due","message":f"{len(due_contacts)} contact(s) need follow-up today."})
    if e.target_registrations and regs < e.target_registrations:
        remaining=max(e.target_registrations-regs,0)
        if e.registration_close:
            days=max((e.registration_close-date.today()).days,1)
            expected=(e.target_registrations/max((e.registration_close-(e.registration_open or date.today())).days,1))
            # lightweight pace signal
            if remaining > max(5, days*5): alerts.append({"kind":"info","title":"Registration pace","message":f"{remaining} registrations remain to hit the target. {days} day(s) left."})
    if not alerts: alerts.append({"kind":"success","title":"Workflow looks healthy","message":"No major risks detected right now."})
    return alerts

@app.route("/event/<int:event_id>")
def event_overview(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    tasks=Task.query.filter_by(event_id=e.id).order_by(Task.due_date.asc()).all()
    contacts=Contact.query.filter_by(event_id=e.id).order_by(Contact.next_followup.asc()).all()
    contents=Content.query.filter_by(event_id=e.id).order_by(Content.post_date.asc()).all()
    members=Member.query.filter_by(event_id=e.id).all()
    regs=Registration.query.filter_by(event_id=e.id).count()
    completed=sum(t.status=="Completed" for t in tasks)
    readiness=round((completed/len(tasks))*100) if tasks else 0
    return render_template("event.html",event=e,tasks=tasks,contacts=contacts,contents=contents,members=members,registrations=regs,readiness=readiness,alerts=analyze(e.id),activities=Activity.query.filter_by(event_id=e.id).order_by(Activity.created_at.desc()).limit(10).all())

@app.route("/event/<int:event_id>/tasks")
def tasks_page(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    return render_template("tasks.html",event=e,tasks=Task.query.filter_by(event_id=e.id).order_by(Task.due_date.asc()).all())

@app.route("/task/<int:task_id>/status", methods=["POST"])
def task_status(task_id):
    if not login_required(): return jsonify(ok=False),401
    t=Task.query.get_or_404(task_id); e=get_event(t.event_id)
    if not e: return jsonify(ok=False),403
    t.status=request.json.get("status","Completed")
    db.session.add(Activity(event_id=e.id,message=f"{t.owner} marked “{t.title}” as {t.status}.",kind="success"))
    db.session.commit()
    return jsonify(ok=True)

@app.route("/event/<int:event_id>/outreach", methods=["GET","POST"])
def outreach(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    if request.method=="POST":
        c=Contact(event_id=e.id,name=request.form.get("name"),organization=request.form.get("organization"),email=request.form.get("email"),phone=request.form.get("phone"),status=request.form.get("status","Not Contacted"),next_followup=parse_date(request.form.get("next_followup")),notes=request.form.get("notes"))
        db.session.add(c); db.session.add(Activity(event_id=e.id,message=f"Added outreach contact: {c.name}.",kind="info")); db.session.commit()
        return redirect(url_for("outreach",event_id=e.id))
    return render_template("outreach.html",event=e,contacts=Contact.query.filter_by(event_id=e.id).order_by(Contact.next_followup.asc()).all())

@app.route("/contact/<int:contact_id>/status", methods=["POST"])
def contact_status(contact_id):
    if not login_required(): return jsonify(ok=False),401
    c=Contact.query.get_or_404(contact_id); e=get_event(c.event_id)
    if not e: return jsonify(ok=False),403
    data=request.json or {}; c.status=data.get("status",c.status)
    if data.get("followup"): c.next_followup=parse_date(data["followup"])
    c.last_contacted=date.today()
    db.session.add(Activity(event_id=e.id,message=f"Updated outreach status for {c.name} to {c.status}.",kind="info")); db.session.commit()
    return jsonify(ok=True)

@app.route("/event/<int:event_id>/content")
def content_page(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    return render_template("content.html",event=e,contents=Content.query.filter_by(event_id=e.id).order_by(Content.post_date.asc()).all())

@app.route("/event/<int:event_id>/team")
def team_page(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    members=Member.query.filter_by(event_id=e.id).all()
    taskmap={m.name:Task.query.filter_by(event_id=e.id,owner=m.name).all() for m in members}
    return render_template("team.html",event=e,members=members,taskmap=taskmap)

@app.route("/event/<int:event_id>/registrations", methods=["GET","POST"])
def registrations(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    if request.method=="POST":
        db.session.add(Registration(event_id=e.id,participant_name=request.form.get("name"),email=request.form.get("email"),source=request.form.get("source","Manual")))
        db.session.commit()
        return redirect(url_for("registrations",event_id=e.id))
    regs=Registration.query.filter_by(event_id=e.id).order_by(Registration.registered_at.desc()).all()
    return render_template("registrations.html",event=e,regs=regs)

@app.route("/event/<int:event_id>/ai")
def ai_page(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    return render_template("ai.html",event=e,alerts=analyze(e.id))

@app.route("/event/<int:event_id>/assistant", methods=["POST"])
def assistant(event_id):
    if not login_required(): return jsonify({"answer":"Please log in."}),401
    e=get_event(event_id)
    if not e: return jsonify({"answer":"Event not found."}),404
    q=request.json.get("question","").lower()
    tasks=Task.query.filter_by(event_id=e.id).all()
    contacts=Contact.query.filter_by(event_id=e.id).all()
    regs=Registration.query.filter_by(event_id=e.id).count()
    if "today" in q or "work" in q:
        due=[t.title for t in tasks if t.status!="Completed" and t.due_date and t.due_date<=date.today()]
        ans="Your priority work today: " + (", ".join(due[:6]) if due else "No urgent tasks. Review upcoming deadlines.")
    elif "block" in q or "risk" in q:
        ans=" | ".join(a["title"]+": "+a["message"] for a in analyze(e.id))
    elif "follow" in q:
        due=[c.name for c in contacts if c.next_followup and c.next_followup<=date.today()]
        ans="Follow up today with: "+(", ".join(due) if due else "No follow-ups are due today.")
    elif "registration" in q:
        ans=f"{regs} registrations received against a target of {e.target_registrations}."
    elif "overdue" in q:
        due=[t.title for t in tasks if t.due_date and t.due_date<date.today() and t.status!="Completed"]
        ans="Overdue: "+(", ".join(due) if due else "Nothing is overdue.")
    else:
        ans=f"{e.name} currently has {len(tasks)} tasks, {sum(t.status=='Completed' for t in tasks)} completed, {len(contacts)} outreach contacts and {regs} registrations."
    return jsonify({"answer":ans})

@app.route("/event/<int:event_id>/automations")
def automations(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    return render_template("automations.html",event=e,alerts=analyze(e.id),activities=Activity.query.filter_by(event_id=e.id).order_by(Activity.created_at.desc()).all())

@app.route("/event/<int:event_id>/support", methods=["GET","POST"])
def support_page(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    if request.method=="POST":
        t=SupportTicket(event_id=e.id,customer=request.form.get("customer"),channel=request.form.get("channel","Email"),subject=request.form.get("subject"),message=request.form.get("message"),owner=request.form.get("owner"))
        support_ai(t); db.session.add(t); db.session.add(Activity(event_id=e.id,message=f"AI triaged support ticket: {t.subject} ({t.priority}).",kind="info")); db.session.commit(); return redirect(url_for("support_page",event_id=e.id))
    return render_template("support.html",event=e,tickets=SupportTicket.query.filter_by(event_id=e.id).order_by(SupportTicket.created_at.desc()).all())

@app.route("/ticket/<int:ticket_id>/status", methods=["POST"])
def ticket_status(ticket_id):
    if not login_required(): return jsonify(ok=False),401
    t=SupportTicket.query.get_or_404(ticket_id); e=get_event(t.event_id)
    if not e: return jsonify(ok=False),403
    t.status=(request.json or {}).get("status",t.status); db.session.add(Activity(event_id=e.id,message=f"Support ticket {t.subject} marked {t.status}.",kind="success")); db.session.commit(); return jsonify(ok=True)

@app.route("/event/<int:event_id>/documents", methods=["GET","POST"])
def documents_page(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    if request.method=="POST":
        d=DocumentRecord(event_id=e.id,name=request.form.get("name"),doc_type=request.form.get("doc_type","Other"),extracted_text=request.form.get("text")); document_ai(d); db.session.add(d); db.session.add(Activity(event_id=e.id,message=f"Processed document: {d.name}.",kind="success")); db.session.commit(); return redirect(url_for("documents_page",event_id=e.id))
    return render_template("documents.html",event=e,documents=DocumentRecord.query.filter_by(event_id=e.id).order_by(DocumentRecord.created_at.desc()).all())

@app.route("/event/<int:event_id>/sales", methods=["GET","POST"])
def sales_page(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    if request.method=="POST":
        d=Deal(event_id=e.id,company=request.form.get("company"),contact=request.form.get("contact"),stage=request.form.get("stage","Lead"),value=float(request.form.get("value") or 0),probability=int(request.form.get("probability") or 20),next_action=request.form.get("next_action"),next_date=parse_date(request.form.get("next_date")),owner=request.form.get("owner"),notes=request.form.get("notes")); db.session.add(d); db.session.add(Activity(event_id=e.id,message=f"Added business opportunity: {d.company}.",kind="info")); db.session.commit(); return redirect(url_for("sales_page",event_id=e.id))
    deals=Deal.query.filter_by(event_id=e.id).order_by(Deal.next_date.asc()).all(); pipeline=sum(d.value for d in deals if d.stage not in ("Won","Lost")); weighted=sum(d.value*d.probability/100 for d in deals if d.stage not in ("Won","Lost"))
    return render_template("sales.html",event=e,deals=deals,pipeline=pipeline,weighted=weighted)

@app.route("/event/<int:event_id>/analytics")
def analytics_page(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    tasks=Task.query.filter_by(event_id=e.id).all(); tickets=SupportTicket.query.filter_by(event_id=e.id).all(); deals=Deal.query.filter_by(event_id=e.id).all(); regs=Registration.query.filter_by(event_id=e.id).count()
    kpis=KPI.query.filter_by(event_id=e.id).all()
    metrics={"registrations":regs,"target":e.target_registrations,"completion":round(sum(t.status=="Completed" for t in tasks)/len(tasks)*100) if tasks else 0,"open_tickets":sum(t.status not in ("Resolved","Closed") for t in tickets),"pipeline":sum(d.value for d in deals if d.stage not in ("Won","Lost")),"weighted_pipeline":sum(d.value*d.probability/100 for d in deals if d.stage not in ("Won","Lost"))}
    return render_template("analytics.html",event=e,metrics=metrics,kpis=kpis,insights=business_insights(e.id))

@app.route("/event/<int:event_id>/internal", methods=["GET","POST"])
def internal_page(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    if request.method=="POST":
        r=InternalRequest(event_id=e.id,requester=request.form.get("requester"),request_type=request.form.get("request_type","General"),title=request.form.get("title"),description=request.form.get("description"),priority=request.form.get("priority","Medium"),assignee=request.form.get("assignee"),due_date=parse_date(request.form.get("due_date"))); r.ai_recommendation=f"AI recommendation: route this {r.priority.lower()} priority request to {r.assignee or 'the appropriate owner'} and track it against the event workflow."; db.session.add(r); db.session.add(Activity(event_id=e.id,message=f"Internal request created: {r.title}.",kind="info")); db.session.commit(); return redirect(url_for("internal_page",event_id=e.id))
    return render_template("internal.html",event=e,requests=InternalRequest.query.filter_by(event_id=e.id).order_by(InternalRequest.due_date.asc()).all())

@app.route("/event/<int:event_id>/business-hub")
def business_hub(event_id):
    if not login_required(): return redirect(url_for("login"))
    e=get_event(event_id)
    if not e: return redirect(url_for("dashboard"))
    return render_template("business_hub.html",event=e,insights=business_insights(e.id),tickets=SupportTicket.query.filter_by(event_id=e.id).count(),docs=DocumentRecord.query.filter_by(event_id=e.id).count(),deals=Deal.query.filter_by(event_id=e.id).count(),requests=InternalRequest.query.filter_by(event_id=e.id).count())

@app.route("/api/event/<int:event_id>/snapshot")
def snapshot(event_id):
    if not login_required(): return jsonify(error="unauthorized"),401
    e=get_event(event_id)
    if not e: return jsonify(error="not found"),404
    tasks=Task.query.filter_by(event_id=e.id).all()
    regs=Registration.query.filter_by(event_id=e.id).count()
    return jsonify(event=e.name,readiness=round(sum(t.status=="Completed" for t in tasks)/len(tasks)*100) if tasks else 0,registrations=regs,target=e.target_registrations,alerts=analyze(e.id))

with app.app_context():
    seed()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)),debug=False)
