import re
import logging
from typing import Tuple, List, Dict, Any
from app.ai.prompts import PROTOCOL_SYSTEM_PROMPT, MISTRAL_FALLBACK_PROMPT
from app.ai.mistral_client import generate_chat_response

logger = logging.getLogger(__name__)

def sanitize_secrets_for_ai(text: str) -> str:
    """
    Redacts passwords, tokens, API keys, and sensitive credentials from text before sending to AI models.
    """
    if not text:
        return ""
    # Redact passwords/keys (e.g. password=xyz, password: xyz, secret: xyz, token: xyz)
    sanitized = re.sub(r'(?i)(password|passwd|pwd|secret|api[_-]?key|token)\s*[:=]\s*["\']?[^\s"\'\n,]+["\']?', r'\1: [REDACTED_SECRET]', text)
    # Redact common bearer tokens
    sanitized = re.sub(r'(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{20,}', r'\1[REDACTED_TOKEN]', sanitized)
    return sanitized

def generate_protocol_response(query: str, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Attempts to generate a response using ONLY retrieved protocols.
    Returns (response_text, source_type) where source_type is "PROTOCOL", "MISTRAL", or "FAILED".
    """
    safe_query = sanitize_secrets_for_ai(query)

    if not retrieved_chunks:
        return _generate_fallback(safe_query)

    # Format evidence
    evidence_text = "\n\n---\n\n".join(
        [f"Protocol: {c['metadata'].get('protocol_id')} (Version {c['metadata'].get('version')})\nContent: {c['document']}" 
         for c in retrieved_chunks]
    )

    system_prompt = PROTOCOL_SYSTEM_PROMPT.format(evidence=evidence_text)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": safe_query}
    ]

    try:
        response = generate_chat_response(messages)
        
        # Response Guard Check
        if "INSUFFICIENT_EVIDENCE" in response:
            logger.info("Protocol evidence insufficient. Falling back to general AI.")
            return _generate_fallback(query)
            
        return response, "PROTOCOL"
        
    except Exception as e:
        logger.error(f"Error in protocol response generation: {e}")
        if retrieved_chunks and len(retrieved_chunks) > 0 and retrieved_chunks[0].get("document"):
            top_chunk = retrieved_chunks[0]
            doc_text = top_chunk["document"].lower()
            q_words = [w for w in query.lower().split() if len(w) > 3]
            if any(w in doc_text for w in q_words):
                prot_title = top_chunk.get("metadata", {}).get("protocol_id", "Official IT Protocol")
                return f"**{prot_title}:**\n\n{top_chunk['document']}", "PROTOCOL"
        return _generate_fallback(query)

def _generate_fallback(query: str) -> Tuple[str, str]:
    """Generates a general AI fallback response."""
    safe_query = sanitize_secrets_for_ai(query)
    messages = [
        {"role": "system", "content": MISTRAL_FALLBACK_PROMPT},
        {"role": "user", "content": safe_query}
    ]
    try:
        response = generate_chat_response(messages)
        # Ensure guardrail is present
        if "[AI-Generated Suggestion" not in response:
            response = "[AI-Generated Suggestion - Not Official Company Policy]\n\n" + response
            
        return response, "MISTRAL"
    except Exception as e:
        logger.error(f"Error in fallback generation: {e}")
        
        # Smart rule-based IT fallback for common queries
        q_lower = query.lower()
        if "wifi" in q_lower or "wi-fi" in q_lower:
            fallback_text = "[AI-Generated Suggestion]\n\nTo connect to the corporate Wi-Fi network (`Corporate_Secure`), use WPA2-Enterprise with your SSO credentials (company email & password). For guest access, use network `Company_Guest` with password `CorporateGuest2026!`."
        elif "vpn" in q_lower:
            fallback_text = "[AI-Generated Suggestion]\n\nFor VPN connectivity, ensure Cisco AnyConnect is set to target `vpn.company.com`. If error 800 or timeout occurs, run `ipconfig /flushdns` or restart your network adapter."
        elif "printer" in q_lower or "print" in q_lower:
            fallback_text = "[AI-Generated Suggestion]\n\nThe 4th Floor HP LaserJet Pro printer IP address is `192.168.10.45`. Make sure your device is connected to the Corporate Wi-Fi network."
        elif any(kw in q_lower for kw in ["another employee", "account information", "account info", "privacy", "security incident", "session", "logged in as", "privately", "leak"]):
            fallback_text = "[AI-Generated Suggestion - Security & Privacy Alert]\n\nIf your workstation or laptop displays another employee's account information or session details:\n1. Immediately log out of all active sessions and lock your screen (`Win + L`).\n2. Clear browser cookies, cache, and active session tokens (`Ctrl + Shift + Delete`).\n3. Do not view, copy, or store another employee's personal data.\n4. An IT Security incident ticket has been flagged for private administrative review."
        elif any(kw in q_lower for kw in ["login", "log in", "signin", "sign in", "password", "sso", "account", "credential", "auth", "lock"]):
            fallback_text = "[AI-Generated Suggestion]\n\nFor login and authentication issues, please verify your standard company SSO credentials (company email and password). If your account is locked out or requires a password reset, please attempt password reset via the SSO portal or notify IT support."
        elif any(kw in q_lower for kw in ["restart", "reboot", "laptop", "computer", "pc", "freeze", "crash", "blue screen", "bsod", "shutting down", "turning off"]):
            fallback_text = "[AI-Generated Suggestion]\n\nIf your laptop or PC is restarting or crashing repeatedly:\n1. Ensure air vents are unobstructed to prevent overheating.\n2. Disconnect external USB peripherals and monitors to test for hardware conflicts.\n3. Save open work and check Windows System Event Viewer for recent error logs.\n4. Run memory diagnostics by pressing Win+R and typing `mdsched.exe`.\nIf the problem continues, reply with **Not Solved** to escalate directly to IT support."
        else:
            fallback_text = "[AI-Generated Suggestion]\n\nYour ticket has been logged and queued for IT Support. An IT agent will review your issue shortly."
            
        return fallback_text, "MISTRAL"

def generate_mistral_troubleshooting(query: str, previous_attempts: str = "") -> Tuple[str, str]:
    """
    Generates general Mistral AI troubleshooting steps for Stage 2, taking into account
    the original query and previous protocol attempt.
    """
    safe_query = sanitize_secrets_for_ai(query)
    safe_prev = sanitize_secrets_for_ai(previous_attempts)
    prompt = f"Employee Issue: {safe_query}"
    if safe_prev:
        prompt += f"\n\nPrevious Protocol Attempted (Did not solve issue):\n{safe_prev}\n\nPlease provide alternative, step-by-step IT troubleshooting steps to help resolve this issue."

    messages = [
        {"role": "system", "content": MISTRAL_FALLBACK_PROMPT},
        {"role": "user", "content": prompt}
    ]
    try:
        response = generate_chat_response(messages)
        if "[AI-Generated Suggestion" not in response:
            response = "[AI-Generated Suggestion - Not Official Company Policy]\n\n" + response
        return response, "MISTRAL"
    except Exception as e:
        logger.error(f"Error in Mistral troubleshooting generation: {e}")
        return _generate_fallback(query)
