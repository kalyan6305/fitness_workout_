from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"  # required for session handling

# -------------------------
# Fake database (in-memory for demo)
# -------------------------
users = {}

# -------------------------
# Helpers for time handling
# -------------------------
def parse_hhmm(hhmm: str) -> int:
    """'07:30' -> minutes since midnight (450)"""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)

def fmt(mins: int) -> str:
    """450 -> '07:30 AM' (wraps around 24h safely)"""
    mins = mins % (24 * 60)
    t = (datetime(2000, 1, 1) + timedelta(minutes=mins)).strftime("%I:%M %p")
    return t.lstrip("0")

def block(start: int, minutes: int, title: str, note: str = ""):
    return {"start": fmt(start), "end": fmt(start + minutes), "title": title, "note": note}

# -------------------------
# Workout plan generator
# -------------------------
def generate_workout_plan(goal: str, duration_min: int, level: str, equipment: str):
    lvl_sets = {"beginner": 2, "intermediate": 3, "advanced": 4}
    lvl_reps = {"beginner": 10, "intermediate": 12, "advanced": 15}
    sets = lvl_sets.get(level, 3)
    reps = lvl_reps.get(level, 12)

    warmup = [
        {"name": "Joint rotations + light cardio", "plan": "5 min total"},
        {"name": "Dynamic leg swings & arm circles", "plan": "3 min"},
    ]
    cooldown = [
        {"name": "Slow walk + deep breathing", "plan": "3 min"},
        {"name": "Static stretching (hamstrings, chest, hips)", "plan": "5 min"},
    ]

    body = [
        ("Push-Ups", f"{sets} × {reps}"),
        ("Air Squats", f"{sets} × {reps}"),
        ("Glute Bridges", f"{sets} × {reps}"),
        ("Plank", f"{sets} × 40 sec"),
    ]
    dumbbell = [
        ("DB Goblet Squat", f"{sets} × {reps}"),
        ("DB Bench Press", f"{sets} × {reps}"),
        ("DB Rows", f"{sets} × {reps}"),
    ]
    gym = [
        ("Barbell Back Squat", f"{sets} × 5–8"),
        ("Deadlift", f"{sets} × 5–8"),
        ("Bench Press", f"{sets} × 6–10"),
    ]
    hiit = [
        ("Jumping Jacks", "40/20"),
        ("High Knees", "40/20"),
        ("Burpees", "40/20"),
    ]

    if equipment == "gym":
        strength_list = gym
    elif equipment == "dumbbells":
        strength_list = dumbbell
    else:
        strength_list = body

    if goal == "lose":
        main = hiit[:2] + strength_list[:2]
        main_note = "Circuit style. Keep rest short."
    elif goal == "gain":
        main = strength_list
        main_note = "Controlled tempo. 60–90s rest."
    else:
        main = strength_list[:2] + hiit[:1]
        main_note = "Balanced strength + cardio."

    warm = 8
    cool = 8
    main_time = max(10, duration_min - warm - cool)
    per_ex = max(6, main_time // max(1, len(main)))

    main_structured = [{"name": n, "plan": p, "est": f"~{per_ex} min"} for (n, p) in main]
    return warmup, main_structured, cooldown, main_note

# -------------------------
# In-memory store for schedules
# -------------------------
SAVED_SCHEDULES = []

# -------------------------
# Workouts Data (80+ now, expandable to 150+)
# -------------------------
workouts_data = [
        {"name": "Push-Ups", "image": "images/push-up.png", "uses": "Strengthens chest, shoulders, and triceps.", "plan": "3 sets × 15 reps"},
    {"name": "Incline Push-Ups", "image": "images/incline-push-up.png", "uses": "Easier variation for beginners, builds upper chest.", "plan": "3 sets × 12 reps"},
    {"name": "Decline Push-Ups", "image": "images/exercises.png", "uses": "Targets upper chest and shoulders.", "plan": "3 sets × 10 reps"},
    {"name": "Diamond Push-Ups", "image": "images/images.jpeg", "uses": "Builds triceps and inner chest.", "plan": "3 sets × 8 reps"},
    {"name": "Wide Push-Ups", "image": "images/workout.jpg", "uses": "Focuses on chest muscles.", "plan": "3 sets × 12 reps"},
    {"name": "Pull-Ups", "image": "images/workout.jpg", "uses": "Strengthens lats, biceps, and grip.", "plan": "4 sets × 8 reps"},
    {"name": "Chin-Ups", "image": "images/workout.jpg", "uses": "Focuses on biceps and back.", "plan": "4 sets × 8 reps"},
    {"name": "Squats", "image": "images/workout.jpg", "uses": "Builds legs and glutes, improves core strength.", "plan": "4 sets × 12 reps"},
    {"name": "Jump Squats", "image": "images/workout.jpg", "uses": "Boosts explosive power and endurance.", "plan": "3 sets × 15 reps"},
    {"name": "Lunges", "image": "images/workout.jpg", "uses": "Strengthens legs and improves balance.", "plan": "3 sets × 12 reps per leg"},
    {"name": "Side Lunges", "image": "images/workout.jpg", "uses": "Works inner thighs and balance.", "plan": "3 sets × 10 reps per side"},
    {"name": "Bulgarian Split Squats", "image": "images/workout.jpg", "uses": "Targets quads and glutes.", "plan": "3 sets × 10 reps per leg"},
    {"name": "Step-Ups", "image": "images/workout.jpg", "uses": "Improves leg strength and coordination.", "plan": "3 sets × 12 reps per leg"},
    {"name": "Glute Bridges", "image": "images/workout.jpg", "uses": "Strengthens glutes and lower back.", "plan": "3 sets × 15 reps"},
    {"name": "Hip Thrusts", "image": "images/workout.jpg", "uses": "Advanced glute and hamstring workout.", "plan": "4 sets × 12 reps"},
    {"name": "Deadlifts", "image": "images/workout.jpg", "uses": "Full-body strength, focuses on hamstrings and back.", "plan": "4 sets × 8 reps"},
    {"name": "Romanian Deadlifts", "image": "images/workout.jpg", "uses": "Targets hamstrings and glutes.", "plan": "3 sets × 10 reps"},
    {"name": "Bench Press", "image": "images/workout.jpg", "uses": "Builds chest, shoulders, and triceps.", "plan": "4 sets × 8 reps"},
    {"name": "Incline Bench Press", "image": "images/workout.jpg", "uses": "Emphasizes upper chest.", "plan": "4 sets × 8 reps"},
    {"name": "Dumbbell Press", "image": "images/workout.jpg", "uses": "Improves stability and chest strength.", "plan": "4 sets × 10 reps"},
    {"name": "Shoulder Press", "image": "images/workout.jpg", "uses": "Strengthens shoulders and triceps.", "plan": "3 sets × 12 reps"},
    {"name": "Arnold Press", "image": "images/workout.jpg", "uses": "Enhances shoulder muscle activation.", "plan": "3 sets × 10 reps"},
    {"name": "Lateral Raises", "image": "images/workout.jpg", "uses": "Builds side deltoids for wider shoulders.", "plan": "3 sets × 12 reps"},
    {"name": "Front Raises", "image": "images/workout.jpg", "uses": "Strengthens front shoulders.", "plan": "3 sets × 12 reps"},
    {"name": "Bicep Curls", "image": "images/workout.jpg", "uses": "Builds bicep strength and size.", "plan": "4 sets × 12 reps"},
    {"name": "Hammer Curls", "image": "images/workout.jpg", "uses": "Targets biceps and forearms.", "plan": "3 sets × 10 reps"},
    {"name": "Tricep Dips", "image": "images/workout.jpg", "uses": "Strengthens triceps and chest.", "plan": "3 sets × 12 reps"},
    {"name": "Skull Crushers", "image": "images/workout.jpg", "uses": "Isolates and strengthens triceps.", "plan": "3 sets × 10 reps"},
    {"name": "Overhead Tricep Extensions", "image": "images/workout.jpg", "uses": "Improves tricep strength.", "plan": "3 sets × 12 reps"},
    {"name": "Cable Rows", "image": "images/workout.jpg", "uses": "Strengthens back and biceps.", "plan": "4 sets × 10 reps"},
    {"name": "Lat Pulldowns", "image": "images/workout.jpg", "uses": "Builds back muscles, alternative to pull-ups.", "plan": "4 sets × 12 reps"},
    {"name": "Face Pulls", "image": "images/workout.jpg", "uses": "Improves posture and rear delts.", "plan": "3 sets × 15 reps"},
    {"name": "Farmer’s Carry", "image": "images/workout.jpg", "uses": "Strengthens grip, shoulders, and core.", "plan": "3 sets × 30 sec walk"},
    {"name": "Chest Fly", "image": "images/workout.jpg", "uses": "Isolates chest muscles.", "plan": "3 sets × 12 reps"},
    {"name": "Dumbbell Rows", "image": "images/workout.jpg", "uses": "Builds lats and biceps.", "plan": "4 sets × 10 reps"},
    {"name": "Good Mornings", "image": "images/workout.jpg", "uses": "Strengthens hamstrings and lower back.", "plan": "3 sets × 12 reps"},

    # Core
    {"name": "Plank", "image": "images/workout.jpg", "uses": "Improves core stability and posture.", "plan": "3 sets × 1 min"},
    {"name": "Side Plank", "image": "images/workout.jpg", "uses": "Targets obliques and core balance.", "plan": "3 sets × 30 sec each side"},
    {"name": "Crunches", "image": "images/workout.jpg", "uses": "Strengthens abdominal muscles.", "plan": "3 sets × 20 reps"},
    {"name": "Bicycle Crunches", "image": "images/workout.jpg", "uses": "Targets obliques and abs.", "plan": "3 sets × 15 reps per side"},
    {"name": "Leg Raises", "image": "images/workout.jpg", "uses": "Strengthens lower abs.", "plan": "3 sets × 15 reps"},
    {"name": "Russian Twists", "image": "images/workout.jpg", "uses": "Improves core rotation and obliques.", "plan": "3 sets × 20 reps"},
    {"name": "Mountain Climbers", "image": "images/workout.jpg", "uses": "Full-body cardio + core activation.", "plan": "3 sets × 30 sec"},
    {"name": "Hollow Hold", "image": "images/workout.jpg", "uses": "Engages full core for stability.", "plan": "3 sets × 45 sec"},
    {"name": "Flutter Kicks", "image": "images/workout.jpg", "uses": "Works lower abs and hip flexors.", "plan": "3 sets × 30 sec"},
    {"name": "Ab Rollouts", "image": "images/workout.jpg", "uses": "Strengthens abs and lower back.", "plan": "3 sets × 10 reps"},

    # Cardio
    {"name": "Jumping Jacks", "image": "images/workout.jpg", "uses": "Improves cardiovascular health.", "plan": "3 sets × 50 reps"},
    {"name": "High Knees", "image": "images/workout.jpg", "uses": "Increases heart rate and leg endurance.", "plan": "3 sets × 30 sec"},
    {"name": "Butt Kicks", "image": "images/workout.jpg", "uses": "Warms up hamstrings and glutes.", "plan": "3 sets × 30 sec"},
    {"name": "Burpees", "image": "images/workout.jpg", "uses": "Full-body cardio and strength.", "plan": "3 sets × 12 reps"},
    {"name": "Sprints", "image": "images/workout.jpg", "uses": "Improves speed and explosiveness.", "plan": "6 × 50m runs"},
    {"name": "Jump Rope", "image": "images/workout.jpg", "uses": "Cardio, coordination, and endurance.", "plan": "3 × 2 min"},
    {"name": "Box Jumps", "image": "images/workout.jpg", "uses": "Builds explosive leg strength.", "plan": "3 sets × 12 reps"},
    {"name": "Lateral Bounds", "image": "images/workout.jpg", "uses": "Improves agility and power.", "plan": "3 sets × 20 reps"},
    {"name": "Shadow Boxing", "image": "images/workout.jpg", "uses": "Cardio and upper body endurance.", "plan": "3 × 2 min"},
    {"name": "Stair Running", "image": "images/workout.jpg", "uses": "Leg endurance and cardio.", "plan": "5 min continuous"},

    # Yoga
    {"name": "Sun Salutation", "image": "images/workout.jpg", "uses": "Full-body flexibility and relaxation.", "plan": "5 rounds"},
    {"name": "Downward Dog", "image": "images/workout.jpg", "uses": "Stretches hamstrings and shoulders.", "plan": "3 × 30 sec"},
    {"name": "Cobra Pose", "image": "images/workout.jpg", "uses": "Strengthens spine and stretches chest.", "plan": "3 × 20 sec"},
    {"name": "Child’s Pose", "image": "images/workout.jpg", "uses": "Relieves back tension.", "plan": "3 × 1 min"},
    {"name": "Warrior Pose", "image": "images/workout.jpg", "uses": "Improves balance and leg strength.", "plan": "3 × 30 sec"},
    {"name": "Tree Pose", "image": "images/workout.jpg", "uses": "Enhances balance and focus.", "plan": "3 × 30 sec"},
    {"name": "Seated Forward Bend", "image": "images/workout.jpg", "uses": "Stretches hamstrings and spine.", "plan": "3 × 30 sec"},
    {"name": "Cat-Cow Stretch", "image": "images/workout.jpg", "uses": "Improves spinal mobility.", "plan": "3 × 10 reps"},
    {"name": "Bridge Pose", "image": "images/workout.jpg", "uses": "Strengthens glutes and back.", "plan": "3 × 20 sec"},
    {"name": "Neck Stretch", "image": "images/workout.jpg", "uses": "Releases neck stiffness.", "plan": "3 × 30 sec"}
]


# -------------------------
# LOGIN / SIGNUP / LOGOUT
# -------------------------



@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["user"] = username
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials!", "error")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            flash("User already exists!", "error")
        else:
            users[username] = password
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

# -------------------------
# HOME (Protected)
# -------------------------
@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", user=session["user"])

# -------------------------
# Workouts
# -------------------------
@app.route("/workouts")
def workouts():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("workouts.html", workouts=workouts_data)

# -------------------------
# Diet
# -------------------------
@app.route("/diet", methods=["GET", "POST"])
def diet():
    if "user" not in session:
        return redirect(url_for("login"))

    diet_plan = None
    if request.method == "POST":
        weight = float(request.form["weight"])
        height = float(request.form["height"]) / 100
        age = int(request.form["age"])
        goal = request.form["goal"]

        bmi = weight / (height ** 2)
        if goal == "lose":
            diet_plan = {"title": "Weight Loss Diet", "bmi": round(bmi, 2), "recommendation": ["Eat ~500 kcal deficit.", "High protein, low refined carbs.", "Lots of veggies & hydration."]}
        elif goal == "gain":
            diet_plan = {"title": "Muscle Gain Diet", "bmi": round(bmi, 2), "recommendation": ["Eat ~300 kcal surplus.", "Protein-rich + complex carbs.", "Strength training is required."]}
        else:
            diet_plan = {"title": "Maintenance Diet", "bmi": round(bmi, 2), "recommendation": ["Balanced macros.", "Whole foods, avoid processed.", "Stay hydrated."]}

    return render_template("diet.html", diet_plan=diet_plan)

# -------------------------
# Worklife
# -------------------------
@app.route("/worklife", methods=["GET", "POST"])
def worklife():
    if "user" not in session:
        return redirect(url_for("login"))

    generated = None
    if request.method == "POST":
        name = request.form.get("name", "Person")
        wake_time = parse_hhmm(request.form["wake_time"])
        work_start = parse_hhmm(request.form["work_start"])
        work_end = parse_hhmm(request.form["work_end"])
        sleep_time = parse_hhmm(request.form["sleep_time"])
        workout_slot = request.form["workout_slot"]
        workout_duration = int(request.form.get("workout_duration", 30))
        goal = request.form["goal"]
        level = request.form["level"]
        equipment = request.form["equipment"]

        schedule = []
        schedule.append(block(wake_time, 20, "Morning Routine", "Hydrate & get ready"))

        workout_detail = None
        if workout_slot == "morning":
            warm, main, cool, note = generate_workout_plan(goal, workout_duration, level, equipment)
            schedule.append(block(wake_time + 20, workout_duration, "Workout", f"{goal}/{level}/{equipment}"))
            workout_detail = {"warmup": warm, "main": main, "cooldown": cool, "note": note}

        schedule.append(block(work_start, (work_end - work_start), "Work", "Focus time"))
        schedule.append(block(work_end, 60, "Evening Routine", "Relax & family time"))
        schedule.append(block(sleep_time, 480, "Sleep", "Recovery"))

        generated = {"name": name, "schedule": schedule, "workout": workout_detail}
        SAVED_SCHEDULES.append(generated)

    return render_template("worklife.html", generated=generated, saved=SAVED_SCHEDULES)

# -------------------------
# About / Contact
# -------------------------
@app.route("/about")
def about():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        # ✅ Here you can save to DB or send email later
        print(f"New message from {name} ({email}): {subject} - {message}")

        flash("✅ Your message has been sent successfully!")
        return redirect(url_for("contact"))

    return render_template("contact.html")


@app.context_processor
def inject_user():
    return dict(user=session.get("user"))


# -------------------------
# Run app
# -------------------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
