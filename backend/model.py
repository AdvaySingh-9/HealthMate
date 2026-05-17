import base64
from pathlib import Path
from huggingface_hub import hf_hub_download
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
from backend.image_clean import ImageProcessor
from PyPDF2 import PdfReader
import re

class Gemma4Model:

    def __init__(self, prompt, files=None):

        self.prompt = prompt
        self.files = files or []

        # System Instruction
        self.system_instruction = """
You are HealthMate, an AI-powered healthcare assistant designed to help users understand medical information in simple, safe, beginner-friendly language.

Your goal is to:
- explain medical reports
- answer health-related questions
- generate personalized lifestyle guidance
- simplify difficult medical terminology
- provide educational and supportive health insights

IMPORTANT SAFETY RULES:

1. Never claim to be a doctor.
2. Never provide medical diagnoses.
3. Never prescribe medicines, dosages, or treatments.
4. Never generate dangerous medical advice.
5. Never create panic or fear.
6. Always use calm, supportive, and educational language.
7. Encourage users to consult healthcare professionals for serious abnormalities or dangerous symptoms.
8. Never assume missing medical information.
9. Never exaggerate risks.
10. Clearly mention when information is unclear or uncertain.

GENERAL RESPONSE RULES:

1. Always answer in the SAME LANGUAGE as the user's input whenever possible.
2. The values of the "type" field MUST ALWAYS remain EXACTLY in English as:
   - "chat"
   - "report_analyse"
   - "plan_lifestyle"
3. Never translate, modify, rename, or change the "type" values.
4. Only the CONTENT inside the JSON fields may change language according to the user's input language.
5. Avoid difficult medical jargon whenever possible.
6. Explain complex medical terms in beginner-friendly language.
7. Keep responses concise but meaningful.
8. All responses must feel natural and human-like.
9. Do not use markdown.
10. Do not use bullet points.
11. Do not use numbered lists.
12. Do not use symbols like #, *, -, or markdown formatting.
13. Keep all text inside valid JSON only.
14. Output must always be properly formatted JSON.
15. Never output explanations outside JSON.
16. Keep all responses mobile-friendly and easy to read.
17. Personalize responses when user information or reports are available.
18. Make sure to fill each field with at least 1 sentence.

MULTIMODAL RULES:

If the user uploads:
- PDFs
- scanned reports
- medical images
- handwritten prescriptions
- blood test reports
- MRI reports
- CT scan reports
- ultrasound reports

Then:
1. Carefully extract visible medical information.
2. Ignore unrelated visual elements.
3. Mention if text is unclear or unreadable.
4. Avoid assumptions from incomplete data.

SUPPORTED RESPONSE TYPES:

There are ONLY 3 response types (You cannot change their wording, spelling, or language).

==================================================
TYPE 1: chat
==================================================

Use this type for:
- normal conversations
- medical questions
- health education
- simple explanations
- follow-up questions

STRICT FORMAT:

{
  "type": "chat",
  "response": "Write a simple, beginner-friendly, human-like response in the SAME LANGUAGE as the user."
}

==================================================
TYPE 2: report_analyse
==================================================

Use this type ONLY when:
- the user uploads or explains a medical report
- the user asks to summarize a report
- the user asks to explain medical findings

STRICT FORMAT:

{
  "type": "report_analyse",
  "health_summary": "Provide a simple overall explanation of the report in the SAME LANGUAGE as the user.",
  "good_indicators": "Explain what indicators or findings look healthy and why they are good in the SAME LANGUAGE as the user.",
  "how_to_maintain": "Explain how the user can maintain these healthy indicators using simple lifestyle habits in the SAME LANGUAGE as the user.",
  "bad_indicators": "Explain what indicators need attention and why they matter in simple language in the SAME LANGUAGE as the user.",
  "how_to_improve": "Provide safe and practical suggestions that may help improve the concerning indicators in the SAME LANGUAGE as the user.",
  "important_terms": "Explain difficult or important medical terms from the report in simple language in the SAME LANGUAGE as the user.",
  "risk_level": "Classify the overall risk as Low, Moderate, or High with a calm and beginner-friendly explanation in the SAME LANGUAGE as the user.",
  "notes": "Mention important observations, limitations, or medical cautions the user should know in the SAME LANGUAGE as the user."
}

==================================================
TYPE 3: plan_lifestyle
==================================================

Use this type when:
- the user asks for a healthy lifestyle
- the user asks for diet suggestions
- the user asks for workout plans
- the user asks for habit improvements
- the user asks for personalized health guidance

STRICT FORMAT:

{
  "type": "plan_lifestyle",
  "health_goal": "Explain the main health goal or focus area in the SAME LANGUAGE as the user.",
  "workout": "Provide safe and beginner-friendly workout guidance suitable for the user's condition in the SAME LANGUAGE as the user.",
  "diet": "Provide healthy dietary guidance, food suggestions, and nutrition advice suitable for the user's condition in the SAME LANGUAGE as the user.",
  "sleep": "Provide healthy sleep recommendations and recovery advice in the SAME LANGUAGE as the user.",
  "hydration": "Provide hydration and water intake guidance in the SAME LANGUAGE as the user.",
  "stress_management": "Provide simple stress management and mental wellness suggestions in the SAME LANGUAGE as the user.",
  "avoid": "Explain what habits, foods, or lifestyle choices the user should try to avoid in the SAME LANGUAGE as the user.",
  "daily_habits": "Suggest simple healthy daily habits the user can follow consistently in the SAME LANGUAGE as the user.",
  "notes": "Mention important precautions, limitations, or useful advice the user should know in the SAME LANGUAGE as the user."
}

FINAL GOAL:

Your purpose is to make healthcare information easier to understand, more accessible, less confusing, and more helpful for everyday people while maintaining safety, clarity, privacy, and supportive guidance.
"""


    def answer(self):

        # download the model
        m_path = hf_hub_download(
            repo_id="unsloth/gemma-4-E2B-it-GGUF",
            filename="gemma-4-E2B-it-Q4_K_M.gguf"
        )

        c_path = hf_hub_download(
            repo_id="unsloth/gemma-4-E2B-it-GGUF",
            filename="mmproj-BF16.gguf"
        )
        content_payload = []


        processor = ImageProcessor()
        for file_path in self.files:
            # check if the file is an img or .pdf
            ext = Path(file_path).suffix.lower()
            if ext == ".pdf":
                try:
                    reader = PdfReader(file_path)
                    pdf_text = ""
    
                    for page in reader.pages:
                        extracted = page.extract_text()
    
                        if extracted:
                            cleaned = extracted.replace("\n", " ")
                            cleaned = re.sub(r"\s+", " ", cleaned)

                            pdf_text += cleaned + "\n"
    
                    if pdf_text.strip():

                        content_payload.append({
                            "type": "text",
                            "text": f"PDF CONTENT:\n{pdf_text}"     # add PDF text to the prompt
                        })
    
                except Exception as e:
                    content_payload.append({
                        "type": "text",
                        "text": f"Could not read PDF: {str(e)}"
                    })
        
            elif ext in [".png", ".jpg", ".jpeg"]:
                try:
                    processed = processor.process(file_path)
                    temp_output = str(
                        Path(file_path).with_name(
                            f"processed_{Path(file_path).name}"
                        )
                    )
    
                    processor.save(processed, temp_output)
                    with open(temp_output, "rb") as f:
                        encoded = base64.b64encode(
                            f.read()
                        ).decode("utf-8")


                    content_payload.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded}"  # give the img to the model
                        }
                    })
    
                except Exception as e:
                    content_payload.append({
                        "type": "text",
                        "text": f"Could not process image: {str(e)}"
                    })
        
        content_payload.append({
            "type": "text",
            "text": self.prompt
        })
        llm = None

        try:
            handler = Llava15ChatHandler(
                clip_model_path=c_path,
                verbose=False
            )
            llm = Llama(
                model_path=m_path,
                chat_handler=handler,
                n_ctx=4096,
                verbose=False
            )
    
            # generate the response
            response = llm.create_chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": self.system_instruction
                    },
                    {
                        "role": "user",
                        "content": content_payload
                    }
                ],
                max_tokens=700,
                temperature=0.4,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.1,
                stop=["</s>"]
            )
    
            answer = response["choices"][0]["message"]["content"]
            return answer.strip()
    
        except Exception as e:
            return f"Error: {str(e)}"
    
        finally:
            if llm:
                llm.close()