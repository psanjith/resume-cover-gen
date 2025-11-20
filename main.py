import os
import textwrap
from openai import OpenAI
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()



# CONFIGURATION

MODEL = "llama-3.3-70b-versatile"
API_BASE = "https://api.groq.com/openai/v1"

client = OpenAI(
    base_url=API_BASE,
    api_key=os.getenv("GROQ_API_KEY"), 
)


# USER DATA CLASS

class User:
    def __init__(self, name, email, phone, linkedin, portfolio, job_title, summary, skills, experiences, education, certifications):
        self.name = name.strip()
        self.email = email.strip()
        self.phone = phone.strip()
        self.linkedin = linkedin.strip()
        self.portfolio = portfolio.strip()
        self.job_title = job_title.strip()
        self.summary = summary.strip()
        self.skills = [s.strip() for s in skills if s.strip()]
        self.experiences = [e.strip() for e in experiences if e.strip()]
        self.education = education.strip()
        self.certifications = [c.strip() for c in certifications if c.strip()]



# PROMPT BUILDER 

class PromptBuilder:
    @staticmethod
    def _list_to_str(items):
        return ", ".join(items) if items else "None provided"

    @staticmethod
    @staticmethod
    def resume_prompt(user: User, target_job_title: str):
        skills_str = PromptBuilder._list_to_str(user.skills)
        experiences_str = PromptBuilder._list_to_str(user.experiences)
        certs_str = PromptBuilder._list_to_str(user.certifications)

        return f"""
You are an expert recruiter and resume writer. 
Create a **complete, polished, ATS-friendly resume** for the following candidate, tailored for the role: "{target_job_title}". 
Output strictly in this structure (do NOT skip sections):

NAME: [Full Name]
CONTACT: [Phone] • [Email] • [LinkedIn or Portfolio]
PROFESSIONAL SUMMARY:
[3–4 sentences summarizing experience, strengths, and measurable results.]

SKILLS:
- [Technical Skills]
- [Tools & Software]
- [Interpersonal Skills]

EXPERIENCE:
[For each experience, use this format:]
Job Title | Company | Dates
• [Achievement/result]
• [Achievement/result]
• [Achievement/result]

EDUCATION:
[Degree, University, Graduation Year]

CERTIFICATIONS & PROJECTS:
[List certifications or relevant projects.]

Candidate data:
Name: {user.name}
Phone: {user.phone}
Email: {user.email}
LinkedIn: {user.linkedin}
Portfolio: {user.portfolio}
Summary: {user.summary}
Target Role: {target_job_title}
Skills: {skills_str}
Experience Highlights: {experiences_str}
Education: {user.education}
Certifications: {certs_str}

Ensure all sections are filled logically based only on provided info.
If something is missing, infer a brief, natural placeholder (e.g., “N/A” or “Not specified”), but avoid “No experience provided”.
Return only the resume text in clean, consistent formatting.
"""


    @staticmethod
    def coverletter_prompt(user: User, company: str, job_description: str):
        skills_str = PromptBuilder._list_to_str(user.skills)
        experiences_str = PromptBuilder._list_to_str(user.experiences)

        return f"""
Write a professional, personalized one-page cover letter for {user.name} applying to {company}.  
Use the following information only — do not fabricate details.

---
Job Description: {job_description}
Candidate Skills: {skills_str}
Experience Summary: {experiences_str}
Education: {user.education}
Portfolio: {user.portfolio}
LinkedIn: {user.linkedin}
---

**Guidelines**
- Address the hiring manager naturally (e.g., “Dear Hiring Manager,” if no name provided).  
- Opening paragraph: express enthusiasm for the specific role and company; briefly connect to the company’s values or goals.  
- Middle paragraphs: highlight 2–3 relevant experiences or skills that directly match the job description.  
- Final paragraph: thank them for their time and express eagerness for an interview.  
- Tone: confident, concise, professional, and authentic — avoid clichés.  
- Output clean text with standard formatting (no markdown).
"""



#  TEXT GENERATION (Groq)

def generate_text(prompt: str, max_tokens: int = 700) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f" Text generation failed: {e}")
    
def clean_resume_text(text: str) -> str:
    """Clean up bullet points and normalize spacing."""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Normalize bullets
        if line.startswith("- "):
            line = "• " + line[2:]
        lines.append(line)
    return "\n".join(lines)




# PDF GENERATOR (professional design)

from fpdf import FPDF
import textwrap

from fpdf import FPDF
import textwrap


# PDF GENERATOR (professional design with Unicode support)

from fpdf import FPDF
import textwrap

class ResumePDF(FPDF):
    def __init__(self):
        super().__init__()
        # Add Unicode font support
        try:
            self.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
            self.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
            self.use_unicode = True
        except:
            # Fallback to standard fonts if DejaVu not available
            self.use_unicode = False
            print("⚠️  Unicode fonts not found. Using standard fonts with hyphens instead of bullets.")
    
    def header(self):
        """Top header with name and contact info."""
        if hasattr(self, "name") and self.name:
            font = 'DejaVu' if self.use_unicode else 'Helvetica'
            self.set_font(font, "B", 22)
            self.set_text_color(30, 50, 100)
            self.cell(0, 12, self.name, new_x="LMARGIN", new_y="NEXT", align="C")
            self.ln(2)

        if hasattr(self, "contact") and self.contact:
            font = 'DejaVu' if self.use_unicode else 'Helvetica'
            self.set_font(font, "", 11)
            self.set_text_color(90, 90, 90)
            self.multi_cell(0, 6, self.contact, align="C")
            self.ln(6)

        # Thin line under header
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def section(self, title: str, body: str = None):
        """Render a section title with optional body text."""
        font = 'DejaVu' if self.use_unicode else 'Helvetica'
        self.set_font(font, "B", 14)
        self.set_text_color(25, 45, 85)
        self.cell(0, 10, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(25, 45, 85)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

        if body:
            self.body_text(body)

    def body_text(self, text):
        """Render normal body text."""
        font = 'DejaVu' if self.use_unicode else 'Helvetica'
        self.set_font(font, "", 11)
        self.set_text_color(20, 20, 20)
        wrapped = textwrap.fill(text, width=95)
        self.multi_cell(0, 6, wrapped)
        self.ln(3)

    def bullet_point(self, text):
        """Render bullet points with indentation."""
        font = 'DejaVu' if self.use_unicode else 'Helvetica'
        self.set_font(font, "", 11)
        
        # Use bullet or hyphen depending on font support
        bullet = "• " if self.use_unicode else "- "
        
        wrapped = textwrap.fill(text, width=88, subsequent_indent="    ")
        self.multi_cell(0, 6, f"{bullet}{wrapped}")
        self.ln(2)

    # Compatibility alias
    def bullet(self, text):
        self

def save_text_as_pdf(text: str, filename: str):
    """Save resume text as a professional-looking PDF."""
    pdf = ResumePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.name = ""
    pdf.contact = ""

    section_titles = [
        "PROFESSIONAL SUMMARY", "SKILLS", "EXPERIENCE",
        "EDUCATION", "CERTIFICATIONS", "PROJECTS"
    ]
    current_section = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Detect name/contact
        if not pdf.name and line.upper().startswith("NAME:"):
            pdf.name = line.replace("NAME:", "").strip()
            continue
        if not pdf.contact and line.upper().startswith("CONTACT:"):
            pdf.contact = line.replace("CONTACT:", "").strip()
            continue

        # Section headers
        upper_line = line.strip(":").upper()
        if any(upper_line.startswith(s) for s in section_titles):
            current_section = upper_line
            pdf.section(current_section)
            continue

        # Bullets
        if line.startswith("•"):
            pdf.bullet_point(line[1:].strip())
            continue

        # Regular text
        pdf.body_text(line)

    pdf.output(filename)
    print(f" Professional PDF saved as: {filename}")





# INPUT COLLECTION

def collect_list(prompt_text):
    print(f"\n{prompt_text}\nEnter one item per line (press Enter twice to finish):")
    items = []
    while True:
        line = input("> ").strip()
        if line == "":
            break
        items.append(line)
    return items



# MAIN EXECUTION

def main():
    print("Enter your details (press Enter to skip optional fields):")
    name = input("Full name: ").strip()
    email = input("Email: ").strip()
    phone = input("Phone number: ").strip()
    linkedin = input("LinkedIn URL: ").strip()
    portfolio = input("Portfolio / Website: ").strip()
    job_title = input("Target job title: ").strip()
    summary = input("Professional summary (1–3 sentences): ").strip()
    skills = collect_list("Skills:")
    experiences = collect_list("Work experience / job highlights:")
    certifications = collect_list("Certifications / Projects:")
    education = input("Education summary: ").strip()

    user = User(name, email, phone, linkedin, portfolio, job_title, summary, skills, experiences, education, certifications)


    print("\n⏳ Generating resume...")
    resume_prompt = PromptBuilder.resume_prompt(user, job_title or "Unspecified role")
    resume_text = generate_text(resume_prompt)
    resume_text = clean_resume_text(resume_text)
    resume_filename = f"{user.name.replace(' ', '_')}_resume.pdf"
    save_text_as_pdf(resume_text, resume_filename)

    company = input("\nCompany applying to (optional): ").strip()
    job_desc = input("Short job description / summary (optional): ").strip()
    if company or job_desc:
        print("\n⏳ Generating cover letter...")
        cover_prompt = PromptBuilder.coverletter_prompt(user, company or "Company", job_desc or "No description provided")
        cover_text = generate_text(cover_prompt)
        cover_filename = f"{user.name.replace(' ', '_')}_cover_letter.pdf"
        save_text_as_pdf(cover_text, cover_filename)


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(" ERROR:", e)
        again = input("\nMake another resume? (Y/N): ").strip().lower()
        if again != "y":
            break
    print(" Done.")
