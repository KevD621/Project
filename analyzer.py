import re
import requests
from urllib.parse import urlparse
import imagehash
from PIL import Image
import io
import base64
import json
from config import PHISHTANK_API_KEY  # user-defined

KNOWN_BRAND_LOGOS = {
    "microsoft": imagehash.phash(Image.open("known_brands/microsoft.png")),
    "google": imagehash.phash(Image.open("known_brands/google.png")),
    "dropbox": imagehash.phash(Image.open("known_brands/dropbox.png")),
    # Add more
}

def check_phishtank(url):
    """Check against PhishTank (free API)."""
    try:
        params = {'url': url, 'format': 'json', 'app_key': PHISHTANK_API_KEY}
        resp = requests.post('https://checkurl.phishtank.com/checkurl/', data=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data['results']['in_database'] == '1' and data['results']['valid'] == '1':
                return True, data['results']['phish_detail_url']
        return False, None
    except:
        return False, None

def url_heuristics(url):
    """Lexical features: suspicious TLD, IP address, typosquatting indicators."""
    parsed = urlparse(url)
    domain = parsed.netloc.split(':')[0]
    score = 0
    reasons = []

    if re.match(r'\d+\.\d+\.\d+\.\d+', domain):
        score += 30
        reasons.append("IP address used as domain")
    if domain.count('.') > 3:
        score += 10
        reasons.append("Excessive subdomains")
    if any(kw in domain for kw in ['secure', 'login', 'verify', 'account', 'update']):
        score += 5
        # not always malicious, but common in phishing
    # Brand name typosquatting (simple Levenshtein could be added)
    return score, reasons

def analyze_brand_similarity(screenshot_base64):
    """Compare screenshot perceptual hash with known brand hashes."""
    try:
        img_data = base64.b64decode(screenshot_base64)
        img = Image.open(io.BytesIO(img_data))
        ss_hash = imagehash.phash(img)
        best_score = 0
        matched_brand = None
        for brand, brand_hash in KNOWN_BRAND_LOGOS.items():
            similarity = 1 - (ss_hash - brand_hash) / len(ss_hash.hash) ** 2  # simplistic
            if similarity > 0.7 and similarity > best_score:
                best_score = similarity
                matched_brand = brand
        return matched_brand, best_score
    except:
        return None, 0

def analyze(sandbox_output):
    verdict = "SAFE"
    reasons = []
    indicators = {}

    url = sandbox_output.get('finalUrl') or sandbox_output.get('initialUrl')
    has_login = sandbox_output.get('hasLoginForm', False)

    # 1. Threat intel
    in_db, detail_url = check_phishtank(url)
    if in_db:
        verdict = "MALICIOUS"
        reasons.append("PhishTank confirmed phishing URL")
        indicators['phishtank'] = detail_url

    # 2. URL lexical
    lexical_score, lexical_reasons = url_heuristics(url)
    if lexical_score > 20:
        if verdict != "MALICIOUS":
            verdict = "SUSPICIOUS"
        reasons.extend(lexical_reasons)

    # 3. Login form destination mismatch
    if has_login:
        parsed_orig = urlparse(sandbox_output['initialUrl'])
        parsed_final = urlparse(url)
        if parsed_orig.netloc != parsed_final.netloc:
            reasons.append("Redirect to different domain with login form")
            if verdict != "MALICIOUS":
                verdict = "SUSPICIOUS"

    # 4. Brand spoofing detection (if screenshot)
    if 'screenshotBase64' in sandbox_output:
        brand, sim = analyze_brand_similarity(sandbox_output['screenshotBase64'])
        if brand and sim > 0.75:
            # Check if the domain actually belongs to the brand
            # Very simple: if brand not in urlparse(url).netloc
            if brand not in urlparse(url).netloc:
                reasons.append(f"Detected {brand} brand in screenshot but domain mismatch")
                verdict = "SUSPICIOUS" if verdict != "MALICIOUS" else verdict
        indicators['brand_spoofing'] = (brand, sim)

    report = {
        'verdict': verdict,
        'reasons': reasons,
        'indicators': indicators,
        'sandbox_data': {
            'finalUrl': url,
            'title': sandbox_output.get('title'),
            'postRequests': sandbox_output.get('postRequests', [])
        }
    }
    return report