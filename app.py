import chainlit as cl
import asyncio
import os
from typing import List, Dict, Any
from document_processor import DocumentProcessor
from mcp_actions import MCPActions
from utils import format_response

# Initialize processors
doc_processor = DocumentProcessor()
mcp_actions = MCPActions()

@cl.on_chat_start
async def start():
    """Initialize the chat session"""
    await cl.Message(
        content="Welcome to the MCP Document Processing Agent! 📄\n\nPlease upload a document (PDF, DOCX, or TXT) and select the actions you'd like to perform on it.",
        author="Assistant"
    ).send()
    
    # Set up session state
    cl.user_session.set("document_content", None)
    cl.user_session.set("document_name", None)
    cl.user_session.set("selected_actions", [])

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages and file uploads"""
    
    # Check if there are any files attached
    if message.elements:
        await handle_file_upload(message.elements)
        return
    
    # Handle text messages
    user_input = message.content.strip()
    
    if user_input.lower() in ["help", "/help"]:
        await show_help()
    elif user_input.lower() in ["actions", "/actions"]:
        await show_actions()
    elif user_input.lower() == "process":
        await process_document_with_actions()
    elif cl.user_session.get("document_content"):
        # Handle action selection if document is uploaded
        await handle_action_selection(user_input)
    else:
        await cl.Message(
            content="Please upload a document first, or type 'help' for assistance.",
            author="Assistant"
        ).send()

async def handle_action_selection(user_input: str):
    """Handle action selection from user input"""
    # Parse action selection
    if user_input.lower() == "all":
        selected_actions = list(mcp_actions.get_available_actions().keys())
        cl.user_session.set("selected_actions", selected_actions)
        await cl.Message(
            "✅ All actions selected! Type 'process' to execute."
        ).send()
        return
    
    # Parse comma-separated numbers
    if any(char.isdigit() for char in user_input):
        try:
            action_numbers = [int(x.strip()) for x in user_input.split(',')]
            actions = list(mcp_actions.get_available_actions().keys())
            selected_actions = [actions[i-1] for i in action_numbers if 1 <= i <= len(actions)]
            
            if selected_actions:
                cl.user_session.set("selected_actions", selected_actions)
                action_names = [mcp_actions.get_available_actions()[key]['name'] for key in selected_actions]
                await cl.Message(
                    f"✅ Selected actions: {', '.join(action_names)}\n\nType 'process' to execute these actions."
                ).send()
            else:
                await cl.Message(
                    "❌ Invalid action numbers. Please select valid action numbers."
                ).send()
        except ValueError:
            await cl.Message(
                "❌ Invalid input format. Please use comma-separated numbers (e.g., '1,2,3') or 'all'."
            ).send()
    else:
        await cl.Message(
            "I didn't understand that. Please select actions by typing numbers (e.g., '1,2,3'), 'all', or 'process' to execute."
        ).send()

async def handle_file_upload(elements: List[Any]):
    """Handle file upload and processing"""
    file_element = elements[0]
    
    # Validate file type
    if not doc_processor.is_supported_file(file_element.name):
        await cl.Message(
            f"❌ Unsupported file type. Please upload PDF, DOCX, or TXT files only.\n\nReceived: {file_element.name}"
        ).send()
        return
    
    # Show processing message
    processing_msg = await cl.Message(
        f"📄 Processing document: {file_element.name}..."
    ).send()
    
    try:
        # Read and process the document
        document_content = await doc_processor.process_document(file_element)
        
        if not document_content:
            processing_msg.content = f"❌ Failed to extract content from {file_element.name}. Please check if the file is valid and not corrupted."
            await processing_msg.update()
            return
        
        # Store in session
        cl.user_session.set("document_content", document_content)
        cl.user_session.set("document_name", file_element.name)
        
        # Update processing message
        processing_msg.content = f"✅ Document processed successfully: {file_element.name}\n\n📊 **Document Stats:**\n- Characters: {len(document_content):,}\n- Words: {len(document_content.split()):,}\n\nNow please select the actions you'd like to perform:"
        await processing_msg.update()
        
        # Show available actions
        await show_action_selection()
        
    except Exception as e:
        processing_msg.content = f"❌ Error processing document: {str(e)}\n\nPlease try uploading the file again or contact support if the issue persists."
        await processing_msg.update()

async def show_action_selection():
    """Display available actions as an interactive selection"""
    actions = mcp_actions.get_available_actions()
    
    actions_text = "**Available Actions:**\n\n"
    for i, (key, action) in enumerate(actions.items(), 1):
        actions_text += f"{i}. **{action['name']}** - {action['description']}\n"
    
    actions_text += "\n📝 **How to proceed:**\n"
    actions_text += "Type the numbers of actions you want (e.g., '1,3,5') or 'all' for all actions, then type 'process' to execute.\n\n"
    actions_text += "Example: `1,2,4` then `process`"
    
    await cl.Message(
        content=actions_text,
        author="Assistant"
    ).send()



async def process_document_with_actions():
    """Process the document with selected actions"""
    document_content = cl.user_session.get("document_content")
    document_name = cl.user_session.get("document_name")
    selected_actions = cl.user_session.get("selected_actions")
    
    if not document_content:
        await cl.Message(
            content="❌ No document uploaded. Please upload a document first.",
            author="Assistant"
        ).send()
        return
    
    if not selected_actions:
        await cl.Message(
            content="❌ No actions selected. Please select actions first.",
            author="Assistant"
        ).send()
        return
    
    # Show processing message
    processing_msg = await cl.Message(
        content=f"🔄 Processing document '{document_name}' with selected actions...",
        author="Assistant"
    ).send()
    
    try:
        # Generate dynamic prompt
        prompt = mcp_actions.generate_prompt(document_content, selected_actions)
        
        # Process with AI (using OpenAI API)
        response = await mcp_actions.process_with_ai(prompt)
        
        if response:
            # Format and display response
            formatted_response = format_response(response, selected_actions, document_name or "Unknown Document")
            processing_msg.content = formatted_response
            await processing_msg.update()
            
            # Reset session for new processing
            await cl.Message(
                "✨ Processing complete! You can upload another document or select different actions for the current document."
            ).send()
        else:
            processing_msg.content = "❌ Failed to process document with AI. Please check your API configuration and try again."
            await processing_msg.update()
    
    except Exception as e:
        processing_msg.content = f"❌ Error during processing: {str(e)}\n\nPlease try again or contact support if the issue persists."
        await processing_msg.update()

async def show_help():
    """Display help information"""
    help_text = """
**📋 MCP Document Processing Agent - Help**

**Supported File Types:**
- PDF (.pdf)
- Word Documents (.docx)
- Text Files (.txt)

**How to Use:**
1. Upload a document using the file upload button
2. Select actions by typing numbers (e.g., '1,2,3' or 'all')
3. Type 'process' to execute the selected actions

**Available Commands:**
- `help` - Show this help message
- `actions` - Show available actions
- `process` - Process document with selected actions
- `all` - Select all available actions

**Tips:**
- You can select multiple actions at once
- Large documents may take longer to process
- Make sure your API keys are properly configured
    """
    
    await cl.Message(content=help_text, author="Assistant").send()

async def show_actions():
    """Display available actions"""
    await show_action_selection()

if __name__ == "__main__":
    cl.run()
