# Interview Prep System - Setup Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+

---

## Backend Setup (Python + FastAPI)

### 1. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Database
```bash
# Copy the .env.example to .env
cp .env.example .env

# Edit .env with your PostgreSQL credentials
DATABASE_URL=postgresql://user:password@localhost:5432/interview_prep
```

### 3. Initialize Database
```bash
# Create PostgreSQL database
createdb interview_prep

# Load schema
psql interview_prep < ../database/schema.sql
```

### 4. Run the Backend Server
```bash
python app.py
```

Server runs on: `http://localhost:8000`

---

## Frontend Setup (React)

### 1. Install Node Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm start
```

Server runs on: `http://localhost:3000`

---

## 📊 Project Structure

```
InterviewPrepSystem/
├── backend/
│   ├── app.py               # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models.py            # Pydantic models
│   ├── database.py          # SQLAlchemy setup
│   ├── ml_engine.py         # ML/skill matching logic
│   ├── requirements.txt      # Python dependencies
│   └── .env.example         # Environment template
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── App.css          # Styling
│   │   └── components/
│   │       ├── Upload.jsx   # File upload form
│   │       └── Results.jsx  # Results display
│   └── package.json         # NPM dependencies
└── database/
    └── schema.sql           # Database schema
```

---

## 🔑 Key Features

### Backend
- **FastAPI**: High-performance REST API
- **Sentence Transformers**: ML embeddings for semantic similarity
- **FAISS**: Fast similarity search
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation

### Frontend
- **React 18**: Modern UI framework
- **Tailwind CSS**: Responsive styling
- **Axios**: HTTP requests
- **Smooth Animations**: UI/UX enhancements

---

## 📡 API Endpoints

### Analyze Resume vs Job Description
```
POST /api/analyze
Content-Type: multipart/form-data

Body:
- resume (file): Resume PDF/DOCX/TXT
- job_description (file): Job Description PDF/DOCX/TXT

Response: {
  "id": "uuid",
  "match_score": 75.5,
  "matched_skills": ["Python", "SQL"],
  "missing_skills": ["AWS", "System Design"],
  "recommended_topics": ["AWS", "System Design"],
  "interview_questions": ["Design a URL Shortener", ...],
  "created_at": "2024-06-03T..."
}
```

### Get Recommendations
```
GET /api/recommendations/{analysis_id}

Response: {
  "analysis_id": "uuid",
  "topics": [...],
  "estimated_hours": 50,
  "priority_order": ["AWS", "System Design"],
  "resources": {...}
}
```

### Health Check
```
GET /api/health

Response: {
  "status": "ok",
  "service": "Interview Prep System"
}
```

---

## 🎓 How It Works

### Step 1: Extract Skills
- Parse resume and job description text
- Match against known skill database
- Extract technical competencies

### Step 2: Generate Embeddings
- Convert text snippets into numerical vectors
- Use Sentence Transformers for semantic understanding
- Understand skill relationships (e.g., "REST APIs" ≈ "Backend Development")

### Step 3: Calculate Similarity
- Compare resume embedding with JD embedding
- Use FAISS for fast similarity search
- Generate match score (0-100%)

### Step 4: Identify Gaps
- Find skills in JD that are missing from resume
- Categorize by difficulty level
- Prioritize learning order

### Step 5: Recommend Preparation
- Suggest learning topics with resources
- Provide interview questions tailored to missing skills
- Create personalized study plan

---

## 🔧 Troubleshooting

### Database Connection Error
```
Error: psycopg2.OperationalError: could not connect to server
```
✅ Solution: Check PostgreSQL is running and credentials in `.env` are correct

### Missing Dependencies
```
ModuleNotFoundError: No module named 'sentence_transformers'
```
✅ Solution: Run `pip install -r requirements.txt` in backend directory

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
✅ Solution: Change port in `.env` or kill existing process

### CORS Error in Frontend
```
Access to XMLHttpRequest blocked by CORS policy
```
✅ Solution: Backend CORS is configured for all origins by default

---

## 📚 Skill Database

Pre-loaded skills include:
- **Programming**: C++, Python, JavaScript, Java, Go, Rust
- **Frontend**: React, Vue, Angular, HTML, CSS
- **Backend**: Node.js, Django, Flask, Spring, FastAPI
- **Database**: SQL, MongoDB, PostgreSQL, MySQL
- **Cloud**: AWS, Azure, GCP, Docker, Kubernetes
- **System Design**: Microservices, Load Balancing, Caching, Database Design
- **ML**: Machine Learning, Deep Learning, NLP, Computer Vision

---

## 📖 Example Workflow

1. **User uploads resume** (Python, React, Node.js skills)
2. **User uploads JD** (AWS, System Design, SQL required)
3. **System analyzes**:
   - Match score: 40% (only SQL is matched)
   - Missing: AWS, System Design
4. **Recommendations provided**:
   - Learn AWS (high priority)
   - Learn System Design (high priority)
   - Practice questions for AWS, System Design
   - Estimated time: 20 hours

---

## 🚀 Next Steps

1. **Customize skills database** - Add more skills specific to your domain
2. **Add user accounts** - Track analysis history
3. **Enhance ML model** - Use more sophisticated embeddings
4. **Mobile support** - Build mobile app
5. **Interview prep content** - Add video tutorials, articles

---

## 📄 License

MIT License - Feel free to use for educational and commercial purposes.

---

## 💡 Tips

- **First time?** Start with sample resume and job description
- **Large files?** Keep PDFs under 10MB for best performance
- **Want to help?** Contribute to the project on GitHub
- **Have ideas?** Open an issue or feature request

---

Enjoy your interview preparation! 🎉
