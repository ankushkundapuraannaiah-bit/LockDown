(function() {
                if (window.__LOCKDOWN_EYEDROPPER__) return;
                window.__LOCKDOWN_EYEDROPPER__ = true;
                const badge = document.createElement('div');
                badge.id = 'ld-color-pill';
                badge.style.cssText = 'position: fixed; bottom: 24px; left: 24px; z-index: 999999; background: #18150E; color: #FFFDF5; border: 1.5px solid #E67300; border-radius: 12px; padding: 6px 12px; font-family: monospace; font-size: 12px; pointer-events: none; display: none;';
                document.body.appendChild(badge);

                document.addEventListener('mousemove', (e) => {
                    if (!e.altKey) {
                        badge.style.display = 'none';
                        return;
                    }
                    const el = document.elementFromPoint(e.clientX, e.clientY);
                    if (el) {
                        const style = window.getComputedStyle(el);
                        const color = style.color;
                        const bg = style.backgroundColor;
                        badge.innerHTML = `🎨 Color: <b>${color}</b> | BG: <b>${bg}</b> (Hold Alt)`;
                        badge.style.display = 'block';
                    }
                });
            })();