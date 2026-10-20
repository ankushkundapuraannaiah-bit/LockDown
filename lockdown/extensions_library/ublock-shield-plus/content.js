(function() {
                const hideSelectors = [
                    'ins.adsbygoogle', 'div[id^="google_ads_"]', '.ad-slot', '.sponsored-post',
                    '.banner-ad', '.ad-wrapper', 'div[data-ad-unit]', '.cookie-notice',
                    '#onetrust-banner-sdk', '.trc_related_container', '.taboola-ad'
                ];
                const clean = () => {
                    const sel = hideSelectors.join(', ');
                    document.querySelectorAll(sel).forEach(el => {
                        el.style.setProperty('display', 'none', 'important');
                    });
                };
                clean();
                setInterval(clean, 1500);
            })();