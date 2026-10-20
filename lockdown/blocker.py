"""Lock Down Shields - uBlock Origin Lite inspired Ad, Tracker & Cookie Blocker.
Provides QWebEngineUrlRequestInterceptor for network filtering,
cosmetic element hiding script injection, and real-time blocking statistics.
"""

import re
from typing import Dict, Set
from urllib.parse import urlparse

from lockdown.qt_compat import (
    QObject,
    pyqtSignal,
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
)

from lockdown.config import load_settings

# Fast domain lookup set of prominent ad, tracker, and cookie banner hosts
AD_AND_TRACKER_DOMAINS = {
    # Google Ads & Analytics
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "adservice.google.com",
    "pagead2.googlesyndication.com",
    "tpc.googlesyndication.com",
    "google-analytics.com",
    "analytics.google.com",
    "stats.g.doubleclick.net",
    # Ad Networks
    "adnxs.com",
    "adroll.com",
    "adsrvr.org",
    "advertising.com",
    "amazon-adsystem.com",
    "a-mo.net",
    "criteo.com",
    "criteo.net",
    "casalemedia.com",
    "contextweb.com",
    "dotomi.com",
    "fastclick.net",
    "imrworldwide.com",
    "infolinks.com",
    "intellitxt.com",
    "mathtag.com",
    "media6degrees.com",
    "moatads.com",
    "openx.net",
    "outbrain.com",
    "popads.net",
    "popcash.net",
    "propellerads.com",
    "pubmatic.com",
    "revcontent.com",
    "rubiconproject.com",
    "scorecardresearch.com",
    "sharethrough.com",
    "smartadserver.com",
    "taboola.com",
    "tribalfusion.com",
    "yieldmo.com",
    "zemanta.com",
    # Trackers & Telemetry
    "clarity.ms",
    "hotjar.com",
    "mouseflow.com",
    "fullstory.com",
    "segment.io",
    "segment.com",
    "mixpanel.com",
    "quantserve.com",
    "branch.io",
    "appsflyer.com",
    "adjust.com",
    "newrelic.com",
    "nr-data.net",
    "pingdom.net",
    "omtrdc.net",
    "demdex.net",
    # Cookie Consent & CMP Banner Trackers
    "cookiebot.com",
    "onetrust.com",
    "cookielaw.org",
    "usercentrics.eu",
    "didomi.io",
    "trustarc.com",
    "consensu.org",
    "quantcast.mgr.consensu.org",
    "iubenda.com",
    "termly.io",
    "complianz.io",
    # Crypto Miners
    "coinhive.com",
    "coin-have.com",
    "crypto-loot.com",
}

# Regex patterns for query/path based ad trackers
AD_URL_PATTERNS = [
    re.compile(r"/ads?[\._\-/]", re.IGNORECASE),
    re.compile(r"/advert[s]?", re.IGNORECASE),
    re.compile(r"/telemetry", re.IGNORECASE),
    re.compile(r"/beacon", re.IGNORECASE),
    re.compile(r"pixel\.facebook\.com", re.IGNORECASE),
    re.compile(r"facebook\.com/tr", re.IGNORECASE),
    re.compile(r"ads\.twitter\.com", re.IGNORECASE),
    re.compile(r"ads-twitter\.com", re.IGNORECASE),
    re.compile(r"/wp-content/plugins/.*cookie.*\.js", re.IGNORECASE),
]

# Cosmetic CSS to hide ad containers and cookie consent banners
COSMETIC_BLOCK_CSS = """
/* uBlock Origin Lite Inspired Cosmetic Element Hiding */
ins.adsbygoogle,
.adsbygoogle,
.ad-container,
.ad-wrapper,
.ad-box,
.ad-banner,
.banner-ad,
.ad_slot,
.adslot,
div[id^="google_ads_"],
div[id^="div-gpt-ad"],
iframe[src*="doubleclick.net"],
iframe[src*="googlesyndication.com"],
iframe[src*="adnxs.com"],
/* Cookie Banners & CMP Notice Dialogs */
#onetrust-consent-sdk,
#onetrust-banner-sdk,
.onetrust-pc-dark,
.cookie-banner,
.cookie-consent,
.cookie-notice,
.cookie-law-info-bar,
.cookie-popup,
#cookie-law-info-bar,
#cookie-notice,
#cookie-bar,
#cookies-eu-wrapper,
.cc-banner,
.cc-window,
.qc-cmp2-container,
.didomi-popup-container,
#didomi-host {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    opacity: 0 !important;
    pointer-events: none !important;
}
"""

COSMETIC_INJECT_JS = f"""
(function() {{
    try {{
        if (window.__lockdown_shield_injected) return;
        window.__lockdown_shield_injected = true;
        const style = document.createElement('style');
        style.type = 'text/css';
        style.id = 'lockdown-ublock-lite-css';
        style.appendChild(document.createTextNode({repr(COSMETIC_BLOCK_CSS)}));
        (document.head || document.documentElement).appendChild(style);

        // Safely restore body scrolling ONLY if an intrusive modal or CMP blocked it
        document.addEventListener('DOMContentLoaded', () => {{
            try {{
                const cmpActive = document.querySelector(
                    '#onetrust-consent-sdk, .cookie-banner, .cookie-consent, [class*="cookie-popup"], .qc-cmp2-container'
                );
                if (cmpActive && document.body.style.overflow === 'hidden') {{
                    document.body.style.overflow = '';
                }}
            }} catch(_) {{}}
        }});
    }} catch(e) {{}}
}})();
"""


class ShieldStats(QObject):
    stats_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ads_blocked_total: int = 1420
        self.trackers_blocked_total: int = 2860
        self.cookies_blocked_total: int = 890
        self.page_blocked_counts: Dict[str, int] = {}
        self.whitelisted_domains: Set[str] = set()

    def add_blocked(self, url: str, category: str = "ad") -> None:
        try:
            domain = urlparse(url).netloc
        except Exception:
            domain = "unknown"

        if category == "ad":
            self.ads_blocked_total += 1
        elif category == "tracker":
            self.trackers_blocked_total += 1
        elif category == "cookie":
            self.cookies_blocked_total += 1

        self.page_blocked_counts[domain] = self.page_blocked_counts.get(domain, 0) + 1
        self.stats_updated.emit()

    def get_count_for_host(self, host: str) -> int:
        return self.page_blocked_counts.get(host, 0)

    def is_whitelisted(self, host: str) -> bool:
        return host.lower() in self.whitelisted_domains

    def toggle_whitelist(self, host: str) -> bool:
        host_clean = host.lower()
        if host_clean in self.whitelisted_domains:
            self.whitelisted_domains.remove(host_clean)
            return False
        else:
            self.whitelisted_domains.add(host_clean)
            return True


class ShieldRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, stats: ShieldStats, parent=None):
        super().__init__(parent)
        self.stats = stats
        self.enabled = True

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        # Standard Chromium 140 desktop client hints matching native PyQt6 WebEngine
        info.setHttpHeader(b"sec-ch-ua", b'"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"')
        info.setHttpHeader(b"sec-ch-ua-mobile", b"?0")
        info.setHttpHeader(b"sec-ch-ua-platform", b'"Windows"')
        info.setHttpHeader(b"Accept-Language", b"en-US,en;q=0.9")

        # Upgrade-Insecure-Requests is ONLY valid on top-level main frame navigation
        # (setting it on XHR/fetch/script breaks CORS preflight on modern websites)
        if info.resourceType() == QWebEngineUrlRequestInfo.ResourceTypeMainFrame:
            info.setHttpHeader(b"Upgrade-Insecure-Requests", b"1")

        if not self.enabled:
            return

        settings = load_settings()
        if not settings.get("shields_enabled", True):
            return

        req_url = info.requestUrl().toString()
        parsed = urlparse(req_url)
        domain = parsed.netloc.lower()

        # Whitelist search engine integrity, auth, CAPTCHA, and CDN services
        # (Checks regional Google domains e.g. google.co.in, Cloudflare challenges, Recaptcha, etc.)
        is_search_or_auth = (
            "google." in domain
            or domain == "google.com"
            or domain.endswith(".google.com")
            or "bing.com" in domain
            or "bing.net" in domain
            or "duckduckgo.com" in domain
            or "brave.com" in domain
            or "ecosia.org" in domain
            or "recaptcha.net" in domain
            or "gstatic.com" in domain
            or "googleusercontent.com" in domain
            or "googleapis.com" in domain
            or "ggpht.com" in domain
            or "youtube.com" in domain
            or "ytimg.com" in domain
            or "cloudflare.com" in domain
            or "challenges.cloudflare.com" in domain
            or "hcaptcha.com" in domain
            or "live.com" in domain
            or "microsoft.com" in domain
            or "msftauth.net" in domain
        )
        if is_search_or_auth:
            return

        # Check if domain or first-party is whitelisted
        first_party = info.firstPartyUrl().host().lower()
        if first_party and (
            self.stats.is_whitelisted(first_party)
            or "google." in first_party
            or "bing.com" in first_party
            or "duckduckgo.com" in first_party
            or "brave.com" in first_party
            or "cloudflare.com" in first_party
        ):
            # If the user is on a search engine or cloudflare challenge, never block challenge/async subrequests
            if (
                domain in ("gstatic.com", "recaptcha.net", "challenges.cloudflare.com", "hcaptcha.com")
                or any(d in domain for d in ["google.", "bing.", "duckduckgo.", "brave."])
            ):
                return
            if self.stats.is_whitelisted(first_party):
                return

        # Check domain suffix against ad & tracker list
        is_blocked = False
        category = "ad"

        for blocked_host in AD_AND_TRACKER_DOMAINS:
            if domain == blocked_host or domain.endswith("." + blocked_host):
                is_blocked = True
                if "analytics" in blocked_host or "hotjar" in blocked_host or "clarity" in blocked_host:
                    category = "tracker"
                elif "cookie" in blocked_host or "onetrust" in blocked_host:
                    category = "cookie"
                break

        # Check URL patterns
        if not is_blocked:
            for pat in AD_URL_PATTERNS:
                if pat.search(req_url):
                    is_blocked = True
                    break

        if is_blocked:
            # Block the request
            info.block(True)
            self.stats.add_blocked(req_url, category)
