import os
from datetime import datetime, timedelta

def detect_animal(image_path: str) -> dict:
    """
    Detect animal species/type in the uploaded photo using RF-DETR or a zero-shot fallback.
    """
    # SIMPLIFIED: Mock detection
    filename = os.path.basename(image_path).lower()
    if "dog" in filename:
        return {"animal_type": "Dog", "confidence": 0.89}
    elif "cat" in filename:
        return {"animal_type": "Cat", "confidence": 0.94}
    return {"animal_type": "Unknown", "confidence": 0.75}

def verify_photo_authenticity(image_path: str, user_lat: float, user_lon: float) -> dict:
    """
    Run FFT, CLIP, and EXIF consistency checks. 
    Consensus: flag if >= 2 checks fail.
    """
    # SIMPLIFIED: Mocked implementations of FFT, CLIP, EXIF
    fft_score = 0.95  # 1.0 = real, 0.0 = ai-generated
    clip_score = 0.92
    exif_consistent = 1.0 # 1.0 = consistent with GPS, 0.0 = inconsistent or missing
    
    # Thresholds
    fft_pass = fft_score > 0.6
    clip_pass = clip_score > 0.6
    exif_pass = exif_consistent > 0.5
    
    passes = sum([fft_pass, clip_pass, exif_pass])
    is_authentic = passes >= 2
    
    return {
        "is_authentic": is_authentic,
        "scores": {
            "fft": fft_score,
            "clip": clip_score,
            "exif": exif_consistent
        }
    }

def calculate_priority(description: str, confidence: float) -> dict:
    """
    Rule-based priority scoring.
    """
    if not description:
        description = ""
    desc = description.lower()
    
    emergency_keywords = ["bleeding", "hit by vehicle", "unconscious", "accident", "dying", "severely injured"]
    
    score = confidence * 50 # Base score from AI confidence (max 50)
    
    is_emergency = False
    reasoning = []
    
    for kw in emergency_keywords:
        if kw in desc:
            is_emergency = True
            score += 50
            reasoning.append(f"Emergency keyword detected: '{kw}'")
            break
            
    if not is_emergency:
        reasoning.append("No emergency keywords detected. Normal priority.")
        
    return {
        "is_emergency": is_emergency,
        "score": min(score, 100.0),
        "reasoning": "; ".join(reasoning)
    }

def check_image_similarity(image_path1: str, image_path2: str) -> float:
    """
    SIMPLIFIED: Mock image embedding similarity (e.g. CLIP/CNN distance).
    Returns similarity score between 0.0 and 1.0.
    """
    return 0.85 # Mock high similarity

def verify_animal_match(original_image_path: str, new_image_path: str, original_description: str) -> dict:
    """
    SIMPLIFIED: Single-shot photo comparison fallback for the On-Site Live Video Verification.
    Compares the on-site photo with the original complaint photo using a multimodal model (e.g. Gemini).
    """
    # In a full implementation, we'd send both images and the description to a VLM (like Gemini Live or GPT-4V)
    # and ask: "Is the animal in image 2 the same as the one reported in image 1 (described as {description})?"
    
    similarity = check_image_similarity(original_image_path, new_image_path)
    is_match = similarity > 0.75
    
    explanation = "The animal closely matches the visual characteristics of the originally reported animal." if is_match else "The visual features do not strongly align with the original report."
    
    return {
        "match": is_match,
        "confidence": similarity,
        "explanation": explanation
    }
