(function() {
                if (window.__LOCKDOWN_DARK_APPLIED__) return;
                window.__LOCKDOWN_DARK_APPLIED__ = true;
                const applyDark = () => {
                    if (document.documentElement) {
                        document.documentElement.setAttribute('data-lockdown-dark', 'true');
                    }
                };
                applyDark();
                document.addEventListener('DOMContentLoaded', applyDark);
            })();