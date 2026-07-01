"""
Seeds the database with starter skills, interview questions, and learning
resources. Run once after creating the schema:

    python seed_data.py
"""
import uuid
from database import SessionLocal, Skill, InterviewQuestionDB, LearningResource, Base, engine

Base.metadata.create_all(bind=engine)

SKILLS = [
    ("C++", "Programming", "medium"),
    ("Python", "Programming", "easy"),
    ("JavaScript", "Programming", "easy"),
    ("TypeScript", "Programming", "medium"),
    ("React", "Frontend", "medium"),
    ("Next.js", "Frontend", "medium"),
    ("HTML5", "Frontend", "easy"),
    ("CSS3", "Frontend", "easy"),
    ("Tailwind CSS", "Frontend", "easy"),
    ("Node.js", "Backend", "medium"),
    ("Express.js", "Backend", "medium"),
    ("Flask", "Backend", "medium"),
    ("SQL", "Database", "medium"),
    ("MySQL", "Database", "medium"),
    ("PostgreSQL", "Database", "medium"),
    ("SQLite", "Database", "easy"),
    ("MongoDB", "Database", "medium"),
    ("Firebase", "Database", "medium"),
    ("AWS", "Cloud", "hard"),
    ("AWS EC2", "Cloud", "hard"),
    ("AWS S3", "Cloud", "hard"),
    ("Vercel", "Cloud", "easy"),
    ("Netlify", "Cloud", "easy"),
    ("Docker", "DevOps", "medium"),
    ("DevOps", "DevOps", "medium"),
    ("CI/CD", "DevOps", "medium"),
    ("Git", "Tools", "easy"),
    ("System Design", "System Design", "hard"),
    ("Data Structures", "Algorithms", "medium"),
    ("Algorithms", "Algorithms", "medium"),
    ("Machine Learning", "ML", "hard"),
    ("REST APIs", "Backend", "medium"),
    ("GraphQL", "Backend", "medium"),
    ("JWT", "Security", "medium"),
    ("OAuth", "Security", "medium"),
    ("Authentication", "Security", "medium"),
    ("Microservices", "Architecture", "hard"),
    ("Load Balancing", "System Design", "hard"),
    ("Caching", "System Design", "hard"),
]

QUESTIONS = [
    ("Design a URL Shortener", "System Design", "medium", "System Design"),
    ("Design TinyURL", "System Design", "medium", "System Design"),
    ("Design a Chat Application", "System Design", "hard", "System Design"),
    ("Design an E-commerce Platform", "System Design", "hard", "System Design"),
    ("Design a Video Streaming Service", "System Design", "hard", "System Design"),
    ("Explain EC2 vs Lambda", "AWS", "medium", "AWS"),
    ("What is S3 and its use cases?", "AWS", "easy", "AWS"),
    ("Design a highly available application on AWS", "AWS", "hard", "AWS"),
    ("Explain VPC and security groups", "AWS", "medium", "AWS"),
    ("Explain overfitting and underfitting", "Machine Learning", "medium", "ML"),
    ("What is cross-validation?", "Machine Learning", "medium", "ML"),
    ("Design an ML pipeline", "Machine Learning", "hard", "ML"),
    ("Explain gradient descent", "Machine Learning", "medium", "ML"),
    ("What is a microservice architecture?", "Microservices", "medium", "Architecture"),
    ("How do you handle service communication?", "Microservices", "hard", "Architecture"),
    ("Explain API Gateway pattern", "Microservices", "medium", "Architecture"),
    ("Docker vs Virtual Machine", "Docker", "medium", "DevOps"),
]

RESOURCES = [
    ("AWS", "AWS Official Documentation", "https://docs.aws.amazon.com", "article", "high"),
    ("AWS", "A Cloud Guru - AWS Fundamentals", "https://acloudguru.com", "course", "high"),
    ("AWS", "Udemy - AWS Solutions Architect", "https://udemy.com", "course", "high"),
    ("System Design", "Designing Data-Intensive Applications", "https://dataintensive.net", "article", "high"),
    ("System Design", "ByteByteGo - System Design Course", "https://bytebytego.com", "course", "high"),
    ("System Design", "Grokking the System Design Interview", "https://educative.io", "course", "high"),
    ("Machine Learning", "Andrew Ng - Machine Learning Specialization", "https://coursera.org", "course", "medium"),
    ("Machine Learning", "Fast.ai - Practical Deep Learning", "https://fast.ai", "course", "medium"),
    ("Microservices", "Building Microservices - Sam Newman", "https://samnewman.io", "article", "medium"),
    ("Microservices", "Docker & Kubernetes Course", "https://udemy.com", "course", "medium"),
    ("Docker", "Docker Official Documentation", "https://docs.docker.com", "article", "medium"),
    ("Docker", "Docker Mastery Course", "https://udemy.com", "course", "medium"),
]


def seed():
    db = SessionLocal()
    try:
        for name, category, difficulty in SKILLS:
            if not db.query(Skill).filter(Skill.name == name).first():
                db.add(Skill(id=str(uuid.uuid4()), name=name, category=category, difficulty=difficulty))

        for question, skill, difficulty, topic in QUESTIONS:
            exists = db.query(InterviewQuestionDB).filter(
                InterviewQuestionDB.question == question
            ).first()
            if not exists:
                db.add(InterviewQuestionDB(
                    id=str(uuid.uuid4()), question=question, skill=skill,
                    difficulty=difficulty, topic=topic
                ))

        for topic, title, url, rtype, priority in RESOURCES:
            exists = db.query(LearningResource).filter(
                LearningResource.title == title, LearningResource.topic == topic
            ).first()
            if not exists:
                db.add(LearningResource(
                    id=str(uuid.uuid4()), topic=topic, title=title,
                    url=url, resource_type=rtype, priority=priority
                ))

        db.commit()
        print("Seed data inserted successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
