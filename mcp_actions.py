import os
import openai
from typing import Dict, List, Any
import asyncio

class MCPActions:
    """MCP (Model Context Protocol) Actions for document processing"""
    
    def __init__(self):
        """Initialize MCP Actions with OpenAI client"""
        self.client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key")
        )
        
        self.actions = {
            "summarize": {
                "name": "Summarize Document",
                "description": "Create a comprehensive summary of the document",
                "prompt": "Please provide a detailed summary of this document, highlighting the main points and key information."
            },
            "analyze": {
                "name": "Analyze Content",
                "description": "Perform in-depth analysis of themes, tone, and structure",
                "prompt": "Please analyze this document in detail, including themes, tone, writing style, structure, and any notable patterns or insights."
            },
            "extract_key_points": {
                "name": "Extract Key Points",
                "description": "Identify and list the most important points",
                "prompt": "Please extract and list the key points from this document in a clear, organized format."
            },
            "generate_questions": {
                "name": "Generate Questions",
                "description": "Create relevant questions based on the content",
                "prompt": "Generate thoughtful questions that could be asked about this document, including comprehension questions and discussion points."
            },
            "identify_entities": {
                "name": "Identify Entities",
                "description": "Extract named entities (people, places, organizations, dates)",
                "prompt": "Identify and categorize all named entities in this document, including people, places, organizations, dates, and other significant entities."
            },
            "sentiment_analysis": {
                "name": "Sentiment Analysis",
                "description": "Analyze the emotional tone and sentiment",
                "prompt": "Analyze the sentiment and emotional tone of this document, identifying positive, negative, and neutral elements."
            },
            "action_items": {
                "name": "Extract Action Items",
                "description": "Identify tasks, recommendations, and action items",
                "prompt": "Extract any action items, tasks, recommendations, or next steps mentioned in this document."
            },
            "translate": {
                "name": "Language Detection",
                "description": "Detect language and provide translation insights",
                "prompt": "Detect the primary language of this document and identify any foreign terms or phrases that might need translation."
            }
        }
    
    def get_available_actions(self) -> Dict[str, Dict[str, str]]:
        """Get all available actions"""
        return self.actions
    
    def generate_prompt(self, document_content: str, selected_actions: List[str]) -> str:
        """Generate a comprehensive prompt based on selected actions"""
        if not selected_actions:
            return ""
        
        # Build the prompt
        prompt_parts = [
            "You are an expert document analysis assistant. Please analyze the following document and complete the requested tasks.",
            "",
            "DOCUMENT CONTENT:",
            "=" * 50,
            document_content,
            "=" * 50,
            "",
            "REQUESTED ANALYSIS TASKS:"
        ]
        
        for i, action_key in enumerate(selected_actions, 1):
            action = self.actions.get(action_key)
            if action:
                prompt_parts.append(f"{i}. {action['name']}: {action['prompt']}")
        
        prompt_parts.extend([
            "",
            "INSTRUCTIONS:",
            "- Please complete each requested task thoroughly and professionally",
            "- Structure your response clearly with headers for each task", 
            "- Provide detailed, actionable insights",
            "- If any task cannot be completed due to document content limitations, explain why",
            "- Use markdown formatting for better readability",
            "",
            "Please begin your analysis:"
        ])
        
        return "\n".join(prompt_parts)
    
    async def process_with_ai(self, prompt: str) -> str:
        """Process the prompt with AI and return the response"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",  # Using 16k model for longer documents
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert document analysis assistant. Provide thorough, professional analysis based on the user's requests. Always structure your responses clearly and use markdown formatting."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.3  # Lower temperature for more consistent, focused responses
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error processing with AI: {str(e)}\n\nPlease check your API configuration and try again."
    
    def get_action_description(self, action_key: str) -> str:
        """Get description for a specific action"""
        action = self.actions.get(action_key)
        return action['description'] if action else "Unknown action"
    
    def validate_actions(self, action_keys: List[str]) -> List[str]:
        """Validate and return only valid action keys"""
        return [key for key in action_keys if key in self.actions]
