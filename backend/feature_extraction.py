import re
from urllib.parse import urlparse


SUSPICIOUS_KEYWORDS = [
    "login",
    "verify",
    "verification",
    "account",
    "secure",
    "update",
    "password",
    "bank",
    "confirm",
    "free",
    "winner",
    "claim",
    "reward",
    "bonus",
    "urgent"
]


def extract_features(url):

    url = str(url).strip()

    parsed = urlparse(url)

    domain = parsed.netloc

    path = parsed.path

    features = [

        # 1. URL length
        len(url),

        # 2. Domain length
        len(domain),

        # 3. Number of dots
        url.count("."),

        # 4. Number of hyphens
        url.count("-"),

        # 5. @ symbol
        int("@" in url),

        # 6. ? symbol
        int("?" in url),

        # 7. = symbol
        int("=" in url),

        # 8. & symbol
        int("&" in url),

        # 9. Number of digits
        sum(c.isdigit() for c in url),

        # 10. HTTPS
        int(url.lower().startswith("https://")),

        # 11. Path length
        len(path),

        # 12. Suspicious keywords
        sum(
            word in url.lower()
            for word in SUSPICIOUS_KEYWORDS
        ),

        # 13. IP address detection
        int(
            bool(
                re.match(
                    r"^\d{1,3}(\.\d{1,3}){3}$",
                    domain.split(":")[0]
                )
            )
        )
    ]

    return features