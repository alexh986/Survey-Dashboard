from http.server import BaseHTTPRequestHandler
import urllib.request
import json
import os

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)

            question = data.get('question', '')
            survey_data = data.get('surveyData', {})
            survey_type = data.get('surveyType', 'family')

            # Build the system prompt based on survey type
            if survey_type == 'all':
                # Combined survey data
                family_data = survey_data.get('family', {})
                faculty_data = survey_data.get('faculty', {})
                data_section = f"""
FAMILY SURVEY DATA ({family_data.get('count', 0)} responses):
{json.dumps(family_data.get('distribution', []), indent=2)}

Family Feedback:
{json.dumps(family_data.get('feedback', []), indent=2)}

FACULTY SURVEY DATA ({faculty_data.get('count', 0)} responses):
{json.dumps(faculty_data.get('distribution', []), indent=2)}

Faculty Feedback:
{json.dumps(faculty_data.get('feedback', []), indent=2)}
"""
            else:
                # Single survey data
                data_section = f"""
RESPONSE DISTRIBUTIONS:
{json.dumps(survey_data.get('distribution', []), indent=2)}

QUESTIONS ASKED:
{json.dumps(survey_data.get('questions', []), indent=2)}

OPEN-ENDED FEEDBACK:
{json.dumps(survey_data.get('feedback', []), indent=2)}

TOTAL RESPONSES: {survey_data.get('count', 0)}
"""

            system_prompt = f"""You are an expert data analyst helping school administrators understand survey results from Breaking Ground Schools.

Your role is to:
- Provide clear, actionable insights
- Reference specific numbers and percentages from the data
- Identify patterns and concerns
- Be concise but thorough (2-3 paragraphs max)
- Use a professional, helpful tone

When discussing satisfaction levels:
- "Strongly Agree" and "Agree" are positive responses
- "Disagree" and "Strongly Disagree" indicate concerns

Here is the survey data:
{data_section}
"""

            # Call Claude API
            url = 'https://api.anthropic.com/v1/messages'
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            }

            payload = {
                'model': 'claude-3-5-sonnet-20241022',
                'max_tokens': 1024,
                'system': system_prompt,
                'messages': [
                    {'role': 'user', 'content': question}
                ]
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read())
                assistant_message = result['content'][0]['text']

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'response': assistant_message}).encode())

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'API Error: {error_body}'}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
