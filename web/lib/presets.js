/** Default job descriptions for users who don't have one — mapped near the
    role-classifier's training categories. */

export const PRESET_ROLES = [
  {
    id: "sde",
    title: "Software Engineer",
    emoji: "⌨️",
    jd: `We are hiring a Software Engineer to build and ship user-facing products.

Requirements:
- 2+ years of experience in software development
- Strong Python or Java skills; solid data structures and algorithms
- Experience with SQL and REST APIs
- Familiar with Git, Docker and CI/CD pipelines
- Unit testing and code review culture

Nice to have: AWS or GCP, Kubernetes, microservices, React.`,
  },
  {
    id: "ds",
    title: "Data Scientist",
    emoji: "📊",
    jd: `Join our analytics team as a Data Scientist.

Requirements:
- 2+ years of experience in data science or analytics
- Strong Python: pandas, scikit-learn, statistics
- SQL fluency and data-wrangling skills
- Experience with machine learning models and A/B testing
- Clear communication of insights to stakeholders

Nice to have: PyTorch or TensorFlow, Tableau or Power BI, NLP experience.`,
  },
  {
    id: "frontend",
    title: "Frontend Developer",
    emoji: "🎨",
    jd: `We're looking for a Frontend Developer obsessed with craft.

Requirements:
- 2+ years building production web interfaces
- Strong JavaScript/TypeScript and React or Vue
- CSS excellence: responsive layouts, animation, accessibility
- Experience consuming REST APIs and managing state
- Eye for design detail and pixel accuracy

Nice to have: Next.js, Tailwind, testing (Jest/Playwright), Figma.`,
  },
  {
    id: "da",
    title: "Data Analyst",
    emoji: "📈",
    jd: `Help the business make smarter decisions as our Data Analyst.

Requirements:
- 1+ years of experience in analytics or reporting
- Advanced SQL; comfortable with large datasets
- Python or R for analysis (pandas, tidyverse)
- Dashboards: Tableau, Power BI or Looker
- Storytelling with data; stakeholder communication

Nice to have: statistics, experimentation, Excel modelling, ETL basics.`,
  },
  {
    id: "ml",
    title: "ML Engineer",
    emoji: "🤖",
    jd: `Deploy models to production as our Machine Learning Engineer.

Requirements:
- 2+ years shipping ML systems end to end
- Python, PyTorch or TensorFlow; model training and evaluation
- Docker, AWS or GCP; CI/CD for ML
- Data pipelines: SQL, Spark or Airflow
- MLOps: monitoring, drift detection, retraining loops

Nice to have: Kubernetes, feature stores, LLM fine-tuning, NLP.`,
  },
  {
    id: "designer",
    title: "Product Designer",
    emoji: "✏️",
    jd: `Shape our product as a Product Designer.

Requirements:
- 2+ years designing digital products end to end
- Strong UI craft: layout, type, color, interaction
- Figma fluency: systems, components, prototyping
- User research and usability testing experience
- Portfolio showing shipped work and process

Nice to have: HTML/CSS knowledge, design systems at scale, motion design.`,
  },
];
