import re
from typing import List, Optional, Dict, Any

def clean_text(text: str) -> str:
    """Silently clean dirty data."""
    if not text:
        return ""
    # Replace zero-width characters and unusual whitespace
    text = re.sub(r'[\u200b\ufeff\u202a-\u202e]', '', text)
    # Normalize line breaks and spaces
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def split_novel_into_episodes(text: str, config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Split a novel into episodes targeting strong 3-second hooks and cliffhangers.

    Args:
        text: The input novel text.
        config: Optional configuration dictionary. Defaults are applied if missing.
            - target_length: ideal episode length in characters (default: 1000)
            - tolerance: acceptable variation in length (default: 200)
            - max_length: hard limit for episode length (default: 1500)

    Returns:
        A list of episode strings.
    """
    # 0. Handle empty/None
    if not text:
        return []

    # 1. Zero-configuration auto-fallback & default values
    if config is None:
        config = {}

    target_length = config.get("target_length", 1000)
    tolerance = config.get("tolerance", 200)
    max_length = config.get("max_length", 1500)

    # 2. Dirty data silent cleaning
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return []

    # 3. Split into paragraphs first to maintain paragraph integrity where possible
    paragraphs = cleaned_text.split('\n')

    episodes = []
    current_episode_paragraphs = []
    current_length = 0

    # Helper to check for cliffhanger/hook at the end of a paragraph
    def has_hook(p: str) -> bool:
        if not p:
            return False
        # Ends with suspenseful punctuation
        if p.endswith(('？', '！', '...', '…', '?', '!')):
            return True
        # Ends with a quote (often a dialogue cliffhanger)
        if p.endswith(('”', '"', '’', "'")):
            return True
        return False

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue

        p_len = len(p)

        # If adding this paragraph exceeds max length, we must split before adding it (if we have content)
        if current_length + p_len > max_length and current_length > 0:
            episodes.append('\n'.join(current_episode_paragraphs))
            current_episode_paragraphs = [p]
            current_length = p_len
            continue

        # If adding this paragraph pushes us past target_length + tolerance, split before adding
        if current_length + p_len > target_length + tolerance and current_length > 0:
            episodes.append('\n'.join(current_episode_paragraphs))
            current_episode_paragraphs = [p]
            current_length = p_len
            continue

        current_episode_paragraphs.append(p)
        current_length += p_len + 1 # +1 for newline

        # Check if we are in the target length zone AFTER adding this paragraph
        if target_length - tolerance <= current_length <= target_length + tolerance:
            # If it has a hook, we split here
            if has_hook(p):
                episodes.append('\n'.join(current_episode_paragraphs))
                current_episode_paragraphs = []
                current_length = 0

    # Add any remaining text as the last episode
    if current_episode_paragraphs:
        episodes.append('\n'.join(current_episode_paragraphs))

    return episodes
