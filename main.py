
import os
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cohere

# Set your Cohere API key here or use an environment variable
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "V182oGhCcdRCPAXzOrsOR6g5HDN5dmUbiuMvzDvq")
co = cohere.Client(COHERE_API_KEY)

app = FastAPI()

# Allow CORS for local frontend development
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

class ChatRequest(BaseModel):
	messages: list

def format_reply(text):
	"""
	Formats the reply into sections with headings, bullet points, code blocks, math, tables, and callouts as described.
	"""
	# Headings: lines starting with 'Definition:', 'Explanation:', etc.
	text = re.sub(r'^(Definition|Explanation|Examples?|Applications?|Summary|Step-by-step|Quick Facts|Table|Quote|Note):', r'\n**\1:**', text, flags=re.MULTILINE)

	# Bullet points: lines starting with '-', '*', or '•'
	text = re.sub(r'^[\-\*•]\s+', '\n- ', text, flags=re.MULTILINE)

	# Numbered steps: lines starting with numbers or arrows
	text = re.sub(r'^(\d+\.|→)', r'\n\1', text, flags=re.MULTILINE)

	# Bold highlights: **word**
	text = re.sub(r'\*\*(.*?)\*\*', r'**\1**', text)

	# Code blocks: ```python ... ```
	text = re.sub(r'```(.*?)```', r'\n```python\n\1\n```', text, flags=re.DOTALL)

	# Math blocks: $...$ or $$...$$
	text = re.sub(r'\$\$(.*?)\$\$', r'\n$$\1$$\n', text, flags=re.DOTALL)
	text = re.sub(r'\$(.*?)\$', r'$\1$', text, flags=re.DOTALL)

	# Tables: lines with | col | col |
	if '|' in text:
		lines = text.split('\n')
		for i, line in enumerate(lines):
			if line.count('|') >= 2 and not line.strip().startswith('|-'):
				# Add markdown table header separator if not present
				if i+1 < len(lines) and not lines[i+1].strip().startswith('|-'):
					cols = [c.strip() for c in line.split('|') if c.strip()]
					lines.insert(i+1, '|' + '|'.join(['---']*len(cols)) + '|')
		text = '\n'.join(lines)

	# Callouts: Quote/Note
	text = re.sub(r'\*\*Quote:\*\*', '> **Quote:**', text)
	text = re.sub(r'\*\*Note:\*\*', '> **Note:**', text)

	return text.strip()

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
	messages = request.messages
	# System prompt to enforce reply style
	style_instructions = (
		"Always reply in this style:\n"
		"\n"
		"Reply Style & Structure\n"
		"\n"
		"Tone & Voice\n"
		"Conversational but professional.\n"
		"Adaptive: can be casual and friendly (like 'hey Aarush!') or formal/exam-focused (like in your JEE notes).\n"
		"Balanced between concise explanations and deep breakdowns depending on context.\n"
		"\n"
		"Formatting\n"
		"- Use headings, bullet points, and bold highlights for clarity.\n"
		"- Structure answers into sections: definition → explanation → examples → applications → final summary (if needed).\n"
		"- For step-by-step guidance: numbers or arrows (→) are used.\n"
		"- For quick facts: inline bolding helps pick out keywords.\n"
		"\n"
		"Special Blocks\n"
		"- Code: always in monospaced fenced blocks (python … ).\n"
		"- Math/Physics: LaTeX-like inline or block formatting for formulas.\n"
		"- Tables: used for comparisons, schedules, or formula sheets.\n"
		"- Quotes/Notes: styled as emphasized callouts.\n"
		"\n"
		"Interaction Style\n"
		"- Often ask a clarifying or follow-up question at the end (to keep the conversation moving).\n"
		"- Match the user's context: e.g., for JEE, suggest questions/exam tricks; for fitness, give routines/diets.\n"
		"- Avoid long unbroken walls of text; break into digestible sections.\n"
	)
	# Insert style instructions as the first message if not present
	if not (messages and messages[0]["role"] == "System" and style_instructions in messages[0]["content"]):
		messages = [{"role": "System", "content": style_instructions}] + [m for m in messages if m["role"] != "System"]
	try:
		response = co.chat(
			message=messages[-1]["content"],
			chat_history=[{"role": m["role"], "message": m["content"]} for m in messages[:-1]],
			connectors=None,
			temperature=0.7,
			max_tokens=700,
		)
		formatted = format_reply(response.text)
		# Add a follow-up question at the end
		followup = "\n\n---\n**Anything else you'd like to ask or need more details on?**"
		return {"response": formatted + followup}
	except Exception as e:
		return {"error": str(e)}
