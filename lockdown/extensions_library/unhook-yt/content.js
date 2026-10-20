(function() {
                if (!location.hostname.includes('youtube.com')) return;
                const hideUnhook = () => {
                    const selectors = ['#related', '#comments', 'ytd-rich-grid-renderer', '#secondary'];
                    selectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => {
                            el.style.setProperty('display', 'none', 'important');
                        });
                    });
                };
                hideUnhook();
                setInterval(hideUnhook, 1200);
            })();