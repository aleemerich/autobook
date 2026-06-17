import json
import re
import sys


def parse_json_response(text):
    """Extract JSON from a response that might have markdown fences or trailing text."""
    text = text.strip()
    
    # Pre-clean: strip markdown code blocks completely
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    
    # Try parsing directly first
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass
        
    # Find the outermost JSON object
    start = text.find('{')
    if start == -1:
        print(f"DEBUG: raw text that failed JSON parsing:\n{text}", file=sys.stderr)
        raise ValueError("No JSON object found in response")
        
    # Walk forward to find the matching closing brace
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == '\\' and in_string:
            escape = True
            continue
        if c == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                json_candidate = text[start:i+1]
                try:
                    return json.loads(json_candidate, strict=False)
                except json.JSONDecodeError:
                    pass
                
                # Try quote repair
                repaired = re.sub(r',\s*([}\]])', r'\1', json_candidate)
                repaired = repair_json_quotes(repaired)
                try:
                    return json.loads(repaired, strict=False)
                except json.JSONDecodeError:
                    # Try to repair literal newlines
                    fixed_slice = re.sub(r'(?<!\\)\n', '\\n', repaired)
                    try:
                        return json.loads(fixed_slice, strict=False)
                    except json.JSONDecodeError:
                        pass
                        
    # Fallback: find the last closing brace in the text
    end = text.rfind('}')
    if end != -1 and end > start:
        cleaned_text = text[start:end+1]
        try:
            return json.loads(cleaned_text, strict=False)
        except json.JSONDecodeError:
            pass
            
        repaired = re.sub(r',\s*([}\]])', r'\1', cleaned_text)
        repaired = repair_json_quotes(repaired)
        try:
            return json.loads(repaired, strict=False)
        except json.JSONDecodeError:
            fixed_fallback = re.sub(r'(?<!\\)\n', '\\n', repaired)
            try:
                return json.loads(fixed_fallback, strict=False)
            except json.JSONDecodeError:
                pass
                
    # Ultimate fallback: try loading whole text with repairs
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass
        
    repaired = re.sub(r',\s*([}\]])', r'\1', text)
    repaired = repair_json_quotes(repaired)
    try:
        return json.loads(repaired, strict=False)
    except json.JSONDecodeError:
        fixed = re.sub(r'(?<!\\)\n', '\\n', repaired)
        try:
            return json.loads(fixed, strict=False)
        except json.JSONDecodeError as e:
            print(f"DEBUG: raw text that failed JSON parsing (final fallback):\n{text}", file=sys.stderr)
            raise e

def repair_json_quotes(s):
    result = []
    in_string = False
    escape = False
    i = 0
    n = len(s)
    
    while i < n:
        c = s[i]
        if escape:
            result.append(c)
            escape = False
            i += 1
            continue
            
        if c == '\\':
            result.append(c)
            escape = True
            i += 1
            continue
            
        if c == '"':
            is_structural = False
            
            if not in_string:
                is_structural = True
            else:
                next_non_ws = ""
                j = i + 1
                while j < n:
                    if not s[j].isspace():
                        next_non_ws = s[j]
                        break
                    j += 1
                
                if next_non_ws in [':', '}', ']', ','] or next_non_ws == "":
                    is_structural = True
            
            if is_structural:
                in_string = not in_string
                result.append(c)
            else:
                result.append('\\"')
        else:
            result.append(c)
        i += 1
        
    return "".join(result)


def validate_and_repair_json(raw_text, required_key="overall_score"):
    """
    Validate that raw_text is a valid JSON and contains the required_key.
    If standard JSON parsing fails or the key is missing, attempts to extract
    the required key and reconstruct a minimal valid dict.
    Returns the parsed dict if successful/repaired, or None if completely invalid.
    """
    # 1. Try normal parsing
    try:
        data = parse_json_response(raw_text)
        if isinstance(data, dict) and required_key in data:
            # Re-fill missing defaults to prevent downstream KeyError
            if required_key == "overall_score":
                if "top_3_revisions" not in data or not isinstance(data["top_3_revisions"], list):
                    data["top_3_revisions"] = []
                if "canon_compliance" not in data or not isinstance(data["canon_compliance"], dict):
                    data["canon_compliance"] = {"score": data.get("overall_score", 5.0), "violations": [], "note": ""}
                if "prose_quality" not in data or not isinstance(data["prose_quality"], dict):
                    data["prose_quality"] = {"score": data.get("overall_score", 5.0), "fix": "", "weakest_sentence": "", "strongest_sentence": "", "note": ""}
            elif required_key == "continuity_score":
                if "inconsistencies" not in data or not isinstance(data["inconsistencies"], list):
                    data["inconsistencies"] = []
                if "timeline_flow" not in data:
                    data["timeline_flow"] = ""
            return data
    except Exception:
        pass

    # 2. Regex fallback for required_key
    score_match = re.search(rf'"{required_key}"\s*:\s*(\d+(?:\.\d+)?)', raw_text)
    if score_match:
        try:
            score_val = float(score_match.group(1))
            if required_key == "overall_score":
                # Try finding top_3_revisions
                revisions = []
                rev_match = re.search(r'"top_3_revisions"\s*:\s*\[(.*?)\]', raw_text, re.DOTALL)
                if rev_match:
                    revisions = [s.strip().strip('"\'') for s in rev_match.group(1).split(',')]
                    revisions = [s for s in revisions if s]
                # Try finding weakest_moment
                weakest_moment = ""
                wm_match = re.search(r'"weakest_moment"\s*:\s*"(.*?)"', raw_text)
                if wm_match:
                    weakest_moment = wm_match.group(1)
                
                return {
                    "overall_score": score_val,
                    "top_3_revisions": revisions,
                    "weakest_moment": weakest_moment,
                    "canon_compliance": {"score": score_val, "violations": [], "note": "Reconstruído via regex"},
                    "prose_quality": {"score": score_val, "fix": "", "weakest_sentence": "", "strongest_sentence": "", "note": "Reconstruído via regex"},
                    "voice_adherence": {"score": score_val, "weakest_moment": "", "fix": "", "note": "Reconstruído via regex"},
                    "beat_coverage": {"score": score_val, "weakest_moment": "", "fix": "", "note": "Reconstruído via regex"},
                    "character_voice": {"score": score_val, "weakest_moment": "", "fix": "", "note": "Reconstruído via regex"},
                    "plants_seeded": {"score": score_val, "weakest_moment": "", "fix": "", "note": "Reconstruído via regex"},
                    "lore_integration": {"score": score_val, "weakest_moment": "", "fix": "", "note": "Reconstruído via regex"},
                    "engagement": {"score": score_val, "weakest_moment": "", "fix": "", "note": "Reconstruído via regex"},
                    "three_weakest_sentences": [],
                    "three_strongest_sentences": [],
                    "ai_patterns_detected": [],
                    "weakest_dimension": "prose_quality",
                    "new_canon_entries": []
                }
            elif required_key == "continuity_score":
                return {
                    "continuity_score": score_val,
                    "inconsistencies": [],
                    "timeline_flow": "Reconstruído via extração regex."
                }
        except Exception:
            pass
    return None
