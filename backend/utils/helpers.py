# Helper functions - TBD
# VirtuAI Office - Utility Helper Functions
import asyncio
import hashlib
import json
import os
import re
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from pathlib import Path
import subprocess
import platform
import psutil
from functools import wraps, lru_cache
from contextlib import contextmanager, asynccontextmanager
import mimetypes
import base64
from urllib.parse import urlparse, parse_qs
import secrets
import string

T = TypeVar('T')


# String Utilities
def sanitize_string(text: str, max_length: int = None, allow_unicode: bool = True) -> str:
    """Sanitize string for safe usage"""
    if not text:
        return ""
    
    # Remove control characters
    if allow_unicode:
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    else:
        text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
    
    # Trim whitespace
    text = text.strip()
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text


def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove punctuation and special characters
    text = re.sub(r'[^\w\s]', '', text)
    
    return text


def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text"""
    if not text:
        return []
    
    # Common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'this', 'that', 'these', 'those', 'is', 'are',
        'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can',
        'must', 'shall', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Filter words
    keywords = []
    for word in words:
        if (len(word) >= min_length and
            word not in stop_words and
            word not in keywords):
            keywords.append(word)
    
    return keywords[:max_keywords]


def generate_slug(text: str, max_length: int = 50) -> str:
    """Generate URL-friendly slug from text"""
    if not text:
        return ""
    
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().replace(' ', '-')
    
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Truncate if needed
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


# Data Validation
def is_valid_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def is_valid_uuid(uuid_string: str) -> bool:
    """Validate UUID format"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def validate_json(json_string: str) -> bool:
    """Validate JSON string"""
    try:
        json.loads(json_string)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


# File and Path Utilities
def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if not"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes"""
    try:
        return Path(file_path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0


def get_file_extension(file_path: Union[str, Path]) -> str:
    """Get file extension"""
    return Path(file_path).suffix.lower()


def get_mime_type(file_path: Union[str, Path]) -> str:
    """Get MIME type of file"""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or 'application/octet-stream'


def is_text_file(file_path: Union[str, Path]) -> bool:
    """Check if file is a text file"""
    mime_type = get_mime_type(file_path)
    return mime_type.startswith('text/') or mime_type in [
        'application/json',
        'application/xml',
        'application/javascript',
        'application/yaml'
    ]


def safe_filename(filename: str) -> str:
    """Generate safe filename by removing/replacing invalid characters"""
    # Replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """Calculate file hash"""
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except (OSError, FileNotFoundError):
        return ""


# Date and Time Utilities
def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    if not dt:
        return ""
    return dt.strftime(format_str)


def parse_datetime(date_string: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Parse datetime from string"""
    try:
        return datetime.strptime(date_string, format_str)
    except ValueError:
        return None


def get_relative_time(dt: datetime) -> str:
    """Get human-readable relative time"""
    if not dt:
        return "unknown"
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        if diff.days == 1:
            return "1 day ago"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
    
    seconds = diff.seconds
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"


def get_timestamp() -> int:
    """Get current timestamp"""
    return int(time.time())


def get_iso_timestamp() -> str:
    """Get current ISO timestamp"""
    return datetime.utcnow().isoformat() + 'Z'


# System Utilities
def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    try:
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': {
                'total': psutil.disk_usage('/').total,
                'free': psutil.disk_usage('/').free,
                'used': psutil.disk_usage('/').used
            },
            'python_version': platform.python_version(),
            'hostname': platform.node()
        }
    except Exception as e:
        return {'error': str(e)}


def get_process_info() -> Dict[str, Any]:
    """Get current process information"""
    try:
        process = psutil.Process()
        return {
            'pid': process.pid,
            'name': process.name(),
            'status': process.status(),
            'cpu_percent': process.cpu_percent(),
            'memory_info': process.memory_info()._asdict(),
            'create_time': process.create_time(),
            'num_threads': process.num_threads()
        }
    except Exception as e:
        return {'error': str(e)}


def run_command(command: List[str], timeout: int = 30, capture_output: bool = True) -> Dict[str, Any]:
    """Run system command safely"""
    try:
        result = subprocess.run(
            command,
            timeout=timeout,
            capture_output=capture_output,
            text=True,
            check=False
        )
        
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout if capture_output else None,
            'stderr': result.stderr if capture_output else None
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Command timed out',
            'timeout': timeout
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# Data Conversion
def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """Safely convert value to boolean"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.capitalize() for x in components[1:])


def to_snake_case(camel_str: str) -> str:
    """Convert camelCase to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# Collection Utilities
def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List[T], key: Callable[[T], Any] = None) -> List[T]:
    """Remove duplicates from list while preserving order"""
    if key is None:
        seen = set()
        return [x for x in lst if not (x in seen or seen.add(x))]
    else:
        seen = set()
        return [x for x in lst if not (key(x) in seen or seen.add(key(x)))]


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


# Caching and Memoization
def async_lru_cache(maxsize: int = 128):
    """LRU cache decorator for async functions"""
    def decorator(func):
        cache = {}
        cache_order = []
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            
            if key in cache:
                # Move to end (most recently used)
                cache_order.remove(key)
                cache_order.append(key)
                return cache[key]
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache[key] = result
            cache_order.append(key)
            
            # Remove oldest if over limit
            if len(cache) > maxsize:
                oldest = cache_order.pop(0)
                del cache[oldest]
            
            return result
        
        return wrapper
    return decorator


def timed_cache(seconds: int = 300):
    """Cache with time-based expiration"""
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            now = time.time()
            
            if key in cache:
                value, timestamp = cache[key]
                if now - timestamp < seconds:
                    return value
                else:
                    del cache[key]
            
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
        
        return wrapper
    return decorator


# Security Utilities
def generate_random_string(length: int = 32,
                         use_digits: bool = True,
                         use_uppercase: bool = True,
                         use_lowercase: bool = True,
                         use_symbols: bool = False) -> str:
    """Generate random string"""
    chars = ""
    if use_lowercase:
        chars += string.ascii_lowercase
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_digits:
        chars += string.digits
    if use_symbols:
        chars += "!@#$%^&*"
    
    if not chars:
        chars = string.ascii_letters + string.digits
    
    return ''.join(secrets.choice(chars) for _ in range(length))


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(32)
    
    password_hash = hashlib.pbkdf2_hmac('sha256',
                                      password.encode('utf-8'),
                                      salt.encode('utf-8'),
                                      100000)
    
    return base64.b64encode(password_hash).decode('utf-8'), salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Verify password against hash"""
    test_hash, _ = hash_password(password, salt)
    return test_hash == hashed_password


def generate_api_key() -> str:
    """Generate API key"""
    return f"vai_{secrets.token_urlsafe(32)}"


# Performance Utilities
def measure_time(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper


def measure_async_time(func):
    """Decorator to measure async function execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper


@contextmanager
def timer(name: str = "Operation"):
    """Context manager to time operations"""
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        print(f"{name} took {end_time - start_time:.4f} seconds")


# Retry Utilities
def retry(max_attempts: int = 3,
          delay: float = 1.0,
          backoff: float = 2.0,
          exceptions: tuple = (Exception,)):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise e
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator


async def async_retry(func,
                     max_attempts: int = 3,
                     delay: float = 1.0,
                     backoff: float = 2.0,
                     exceptions: tuple = (Exception,)):
    """Async retry with exponential backoff"""
    attempt = 0
    current_delay = delay
    
    while attempt < max_attempts:
        try:
            return await func()
        except exceptions as e:
            attempt += 1
            if attempt >= max_attempts:
                raise e
            
            await asyncio.sleep(current_delay)
            current_delay *= backoff
    
    return None


# Environment Utilities
def get_env_var(key: str, default: Any = None, cast_type: type = str) -> Any:
    """Get environment variable with type casting"""
    value = os.getenv(key, default)
    
    if value is None:
        return default
    
    try:
        if cast_type == bool:
            return safe_bool(value)
        elif cast_type == int:
            return safe_int(value)
        elif cast_type == float:
            return safe_float(value)
        else:
            return cast_type(value)
    except (ValueError, TypeError):
        return default


def load_env_file(file_path: str = '.env') -> Dict[str, str]:
    """Load environment variables from file"""
    env_vars = {}
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    env_vars[key] = value
                    os.environ[key] = value
    except FileNotFoundError:
        pass
    
    return env_vars


# Logging Utilities
def get_caller_info(skip_frames: int = 1) -> Dict[str, str]:
    """Get information about the calling function"""
    import inspect
    
    frame = inspect.currentframe()
    try:
        for _ in range(skip_frames + 1):
            frame = frame.f_back
        
        return {
            'function': frame.f_code.co_name,
            'filename': frame.f_code.co_filename,
            'lineno': frame.f_lineno
        }
    finally:
        del frame


# JSON Utilities
def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "null") -> str:
    """Safely dump object to JSON string"""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return default


def json_encoder(obj: Any) -> Any:
    """Custom JSON encoder for complex objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)


# URL Utilities
def build_url(base_url: str, path: str = "", params: Dict[str, Any] = None) -> str:
    """Build URL with path and query parameters"""
    url = base_url.rstrip('/')
    
    if path:
        url += '/' + path.lstrip('/')
    
    if params:
        query_params = []
        for key, value in params.items():
            if value is not None:
                query_params.append(f"{key}={value}")
        
        if query_params:
            url += '?' + '&'.join(query_params)
    
    return url


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return ""


# Math Utilities
def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))


def round_to_nearest(value: float, nearest: float) -> float:
    """Round value to nearest multiple"""
    return round(value / nearest) * nearest


def percentage(part: Union[int, float], whole: Union[int, float]) -> float:
    """Calculate percentage"""
    if whole == 0:
        return 0.0
    return (part / whole) * 100


def average(values: List[Union[int, float]]) -> float:
    """Calculate average of values"""
    if not values:
        return 0.0
    return sum(values) / len(values)


# Color Utilities
def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB color to hex"""
    return f"#{r:02x}{g:02x}{b:02x}"


def generate_random_color() -> str:
    """Generate random hex color"""
    return f"#{secrets.randbelow(16777216):06x}"
