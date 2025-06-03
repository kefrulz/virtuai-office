# VirtuAI Office - Data Formatting Utilities
import re
import json
import html
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import unicodedata
import markdown
from urllib.parse import quote, unquote


class OutputFormat(Enum):
    """Supported output formats"""
    PLAIN_TEXT = "plain"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    CODE = "code"


class CodeLanguage(Enum):
    """Supported programming languages for syntax highlighting"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    BASH = "bash"
    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"


def sanitize_text(text: str, preserve_newlines: bool = True) -> str:
    """Sanitize text input by removing harmful content"""
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    
    # HTML escape
    text = html.escape(text)
    
    # Remove potentially harmful patterns
    # Remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove javascript: links
    text = re.sub(r'javascript\s*:', '', text, flags=re.IGNORECASE)
    
    # Preserve or normalize newlines
    if preserve_newlines:
        text = text.replace('\r\n', '\n').replace('\r', '\n')
    else:
        text = ' '.join(text.split())
    
    return text.strip()


def format_task_output(output: str, format_type: OutputFormat = OutputFormat.MARKDOWN) -> str:
    """Format AI-generated task output for display"""
    if not output:
        return ""
    
    # Basic sanitization
    output = sanitize_text(output, preserve_newlines=True)
    
    if format_type == OutputFormat.PLAIN_TEXT:
        return strip_markdown(output)
    
    elif format_type == OutputFormat.MARKDOWN:
        return format_markdown(output)
    
    elif format_type == OutputFormat.HTML:
        return markdown_to_html(output)
    
    elif format_type == OutputFormat.JSON:
        try:
            # Try to parse and pretty-print JSON
            parsed = json.loads(output)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return output
    
    elif format_type == OutputFormat.CODE:
        return format_code_block(output)
    
    return output


def format_markdown(text: str) -> str:
    """Enhance markdown formatting"""
    if not text:
        return ""
    
    # Fix common markdown issues
    # Ensure proper spacing around headers
    text = re.sub(r'\n(#{1,6})\s*([^\n]+)', r'\n\n\1 \2\n', text)
    
    # Fix list formatting
    text = re.sub(r'\n(\d+\.|\*|\-)\s*([^\n]+)', r'\n\1 \2', text)
    
    # Ensure code blocks have proper spacing
    text = re.sub(r'\n```(\w+)?\n', r'\n\n```\1\n', text)
    text = re.sub(r'\n```\n', r'\n```\n\n', text)
    
    # Fix emphasis formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', text)
    text = re.sub(r'\*([^*]+)\*', r'*\1*', text)
    
    # Clean up excessive whitespace while preserving structure
    text = re.sub(r'\n\n\n+', '\n\n', text)
    
    return text.strip()


def strip_markdown(text: str) -> str:
    """Remove markdown formatting to get plain text"""
    if not text:
        return ""
    
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove emphasis
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove blockquotes
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    
    # Remove list markers
    text = re.sub(r'^\s*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()


def markdown_to_html(text: str) -> str:
    """Convert markdown to HTML"""
    if not text:
        return ""
    
    try:
        # Use python-markdown with extensions
        html_content = markdown.markdown(
            text,
            extensions=[
                'codehilite',
                'fenced_code',
                'tables',
                'toc',
                'nl2br'
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True
                }
            }
        )
        return html_content
    except Exception:
        # Fallback to basic conversion
        return basic_markdown_to_html(text)


def basic_markdown_to_html(text: str) -> str:
    """Basic markdown to HTML conversion without dependencies"""
    if not text:
        return ""
    
    # Headers
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Bold and italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Code blocks
    text = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code class="language-\1">\2</code></pre>', text, flags=re.DOTALL)
    
    # Line breaks
    text = text.replace('\n', '<br>\n')
    
    return text


def format_code_block(code: str, language: Optional[CodeLanguage] = None) -> str:
    """Format code with proper indentation and syntax highlighting markers"""
    if not code:
        return ""
    
    # Detect language if not provided
    if not language:
        language = detect_code_language(code)
    
    # Clean up code formatting
    lines = code.split('\n')
    
    # Remove empty lines at start and end
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    if not lines:
        return ""
    
    # Find minimum indentation (excluding empty lines)
    min_indent = float('inf')
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            min_indent = min(min_indent, indent)
    
    # Remove common indentation
    if min_indent > 0 and min_indent != float('inf'):
        lines = [line[min_indent:] if line.strip() else line for line in lines]
    
    # Join lines and format as code block
    formatted_code = '\n'.join(lines)
    
    if language:
        return f"```{language.value}\n{formatted_code}\n```"
    else:
        return f"```\n{formatted_code}\n```"


def detect_code_language(code: str) -> Optional[CodeLanguage]:
    """Detect programming language from code content"""
    if not code:
        return None
    
    code_lower = code.lower()
    
    # Python indicators
    if any(keyword in code for keyword in ['def ', 'import ', 'from ', 'class ', 'if __name__']):
        return CodeLanguage.PYTHON
    
    # JavaScript/TypeScript indicators
    if any(keyword in code for keyword in ['function ', 'const ', 'let ', 'var ', '=>', 'console.log']):
        if 'interface ' in code or ': string' in code or ': number' in code:
            return CodeLanguage.TYPESCRIPT
        return CodeLanguage.JAVASCRIPT
    
    # HTML indicators
    if re.search(r'<[^>]+>', code):
        return CodeLanguage.HTML
    
    # CSS indicators
    if re.search(r'[^{}]+\s*\{[^{}]*\}', code) and '{' in code:
        return CodeLanguage.CSS
    
    # SQL indicators
    if any(keyword in code_lower for keyword in ['select ', 'insert ', 'update ', 'delete ', 'create table']):
        return CodeLanguage.SQL
    
    # Bash indicators
    if code.startswith('#!') or any(keyword in code for keyword in ['#!/bin/bash', 'echo ', 'cd ', 'ls ']):
        return CodeLanguage.BASH
    
    # JSON indicators
    try:
        json.loads(code)
        return CodeLanguage.JSON
    except:
        pass
    
    # YAML indicators
    if re.search(r'^[a-zA-Z_][a-zA-Z0-9_]*:\s*', code, re.MULTILINE):
        return CodeLanguage.YAML
    
    return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 0:
        return "0s"
    
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        if remaining_seconds > 0:
            return f"{minutes}m {remaining_seconds:.1f}s"
        return f"{minutes}m"
    
    hours = int(minutes // 60)
    remaining_minutes = minutes % 60
    
    if hours < 24:
        if remaining_minutes > 0:
            return f"{hours}h {remaining_minutes}m"
        return f"{hours}h"
    
    days = int(hours // 24)
    remaining_hours = hours % 24
    
    if remaining_hours > 0:
        return f"{days}d {remaining_hours}h"
    return f"{days}d"


def format_datetime(dt: datetime, format_type: str = "relative") -> str:
    """Format datetime in various formats"""
    if not isinstance(dt, datetime):
        return str(dt)
    
    if format_type == "relative":
        return format_relative_time(dt)
    elif format_type == "short":
        return dt.strftime("%Y-%m-%d %H:%M")
    elif format_type == "long":
        return dt.strftime("%B %d, %Y at %I:%M %p")
    elif format_type == "iso":
        return dt.isoformat()
    elif format_type == "date_only":
        return dt.strftime("%Y-%m-%d")
    elif format_type == "time_only":
        return dt.strftime("%H:%M:%S")
    else:
        return dt.strftime(format_type)


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time (e.g., '5 minutes ago')"""
    now = datetime.utcnow()
    
    if dt > now:
        # Future time
        diff = dt - now
        return f"in {format_time_delta(diff)}"
    else:
        # Past time
        diff = now - dt
        return f"{format_time_delta(diff)} ago"


def format_time_delta(delta: timedelta) -> str:
    """Format timedelta in human-readable format"""
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} second{'s' if total_seconds != 1 else ''}"
    
    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    
    days = hours // 24
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''}"
    
    months = days // 30
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''}"
    
    years = months // 12
    return f"{years} year{'s' if years != 1 else ''}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage with proper rounding"""
    if value is None:
        return "N/A"
    
    percentage = value * 100
    return f"{percentage:.{decimals}f}%"


def format_number(value: Union[int, float], decimals: int = 2) -> str:
    """Format number with thousands separators"""
    if value is None:
        return "N/A"
    
    if isinstance(value, float):
        return f"{value:,.{decimals}f}"
    else:
        return f"{value:,}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if not text or len(text) <= max_length:
        return text
    
    # Try to break at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If word boundary is reasonably close
        truncated = truncated[:last_space]
    
    return truncated + suffix


def extract_summary(text: str, max_sentences: int = 3) -> str:
    """Extract a summary from text (first few sentences)"""
    if not text:
        return ""
    
    # Split into sentences (basic implementation)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= max_sentences:
        return text
    
    summary_sentences = sentences[:max_sentences]
    return '. '.join(summary_sentences) + '.' if summary_sentences else ""


def format_task_status(status: str) -> Dict[str, str]:
    """Format task status with appropriate styling"""
    status_map = {
        'pending': {'label': 'Pending', 'color': 'yellow', 'icon': '⏳'},
        'in_progress': {'label': 'In Progress', 'color': 'blue', 'icon': '🔄'},
        'completed': {'label': 'Completed', 'color': 'green', 'icon': '✅'},
        'failed': {'label': 'Failed', 'color': 'red', 'icon': '❌'},
    }
    
    return status_map.get(status.lower(), {
        'label': status.title(),
        'color': 'gray',
        'icon': '❓'
    })


def format_priority(priority: str) -> Dict[str, str]:
    """Format task priority with appropriate styling"""
    priority_map = {
        'low': {'label': 'Low', 'color': 'gray', 'weight': 1},
        'medium': {'label': 'Medium', 'color': 'blue', 'weight': 2},
        'high': {'label': 'High', 'color': 'orange', 'weight': 3},
        'urgent': {'label': 'Urgent', 'color': 'red', 'weight': 4},
    }
    
    return priority_map.get(priority.lower(), {
        'label': priority.title(),
        'color': 'gray',
        'weight': 0
    })


def format_agent_type(agent_type: str) -> Dict[str, str]:
    """Format agent type with appropriate styling"""
    agent_map = {
        'product_manager': {'label': 'Product Manager', 'icon': '👩‍💼', 'color': 'purple'},
        'frontend_developer': {'label': 'Frontend Developer', 'icon': '👨‍💻', 'color': 'blue'},
        'backend_developer': {'label': 'Backend Developer', 'icon': '👩‍💻', 'color': 'green'},
        'ui_ux_designer': {'label': 'UI/UX Designer', 'icon': '🎨', 'color': 'pink'},
        'qa_tester': {'label': 'QA Tester', 'icon': '🔍', 'color': 'orange'},
    }
    
    return agent_map.get(agent_type.lower(), {
        'label': agent_type.replace('_', ' ').title(),
        'icon': '🤖',
        'color': 'gray'
    })


def format_api_response(data: Any, format_type: str = "json") -> str:
    """Format API response data"""
    if format_type == "json":
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    elif format_type == "yaml":
        try:
            import yaml
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    else:
        return str(data)


def clean_filename(filename: str) -> str:
    """Clean filename for safe filesystem usage"""
    if not filename:
        return "untitled"
    
    # Remove or replace unsafe characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remove leading/trailing periods and spaces
    cleaned = cleaned.strip('. ')
    
    # Limit length
    if len(cleaned) > 255:
        name, ext = cleaned.rsplit('.', 1) if '.' in cleaned else (cleaned, '')
        max_name_len = 255 - len(ext) - 1 if ext else 255
        cleaned = name[:max_name_len] + ('.' + ext if ext else '')
    
    return cleaned or "untitled"


def format_search_query(query: str) -> str:
    """Format and clean search query"""
    if not query:
        return ""
    
    # Basic cleaning
    query = query.strip()
    
    # Remove excessive whitespace
    query = re.sub(r'\s+', ' ', query)
    
    # Remove special characters that might break search
    query = re.sub(r'[^\w\s\-\.]', '', query)
    
    return query


def highlight_search_terms(text: str, search_terms: List[str],
                         highlight_tag: str = "mark") -> str:
    """Highlight search terms in text"""
    if not text or not search_terms:
        return text
    
    highlighted_text = text
    
    for term in search_terms:
        if not term.strip():
            continue
        
        # Case-insensitive highlighting
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        highlighted_text = pattern.sub(
            f'<{highlight_tag}>\\g<0></{highlight_tag}>',
            highlighted_text
        )
    
    return highlighted_text
