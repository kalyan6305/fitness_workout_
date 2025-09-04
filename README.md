🌍 Travel Booking Portal

A simple Flask-based Travel Booking Website with Login, Signup, Contact Form, and Travel Options.
Users can register, log in, and explore travel booking links for Cars, Trains, Flights, and Buses.
Data (users & contact messages) is stored in JSON files.

✨ Features

🔐 User Authentication – Signup & Login system with session handling

📬 Contact Form – Stores user messages

🏠 Pages – Home, About, Contact, Login, Signup

🚗 Travel Options – Car, Train, Bus, Flight booking (external links)

💾 JSON storage – No database required

🌐 Deployable on Render/Heroku

📂 Project Structure
travel-app/
│── app.py
│── requirements.txt
│── render.yaml
│── users.json
│── contacts.json
│
├── templates/
│   ├── index.html
│   ├── about.html
│   ├── contact.html
│   ├── login.html
│   └── signup.html
│
└── static/
    └── style.css

⚡ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/your-username/travel-app.git
cd travel-app

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Run the app locally
python app.py


App will run at 👉 http://127.0.0.1:5000/

🚀 Deploy on Render

Push your code to GitHub

Create a new Web Service on Render

Use:

Build Command: pip install -r requirements.txt

Start Command: gunicorn app:app

Add PORT environment variable if needed (Render sets this automatically).

🛠 Requirements

Python 3.9+

Flask 2.3.3

Gunicorn (for deployment)

Install via:

pip install -r requirements.txt

📸 Screenshots

(Add your screenshots here if available – home, login, signup, contact page)

👨‍💻 Author

Developed by Kalyan Nagu 🚀
