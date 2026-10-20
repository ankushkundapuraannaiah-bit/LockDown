(function() {
                if (window.__MD_CLIPPER_BTN__) return;
                window.__MD_CLIPPER_BTN__ = true;
                const b = document.createElement('button');
                b.id = 'ld-clip-btn';
                b.innerHTML = '📝 Copy as Markdown';
                b.style.cssText = 'position:fixed;bottom:24px;right:160px;z-index:999999;background:#18150E;color:#FFDE59;border:1.5px solid #E67300;border-radius:18px;padding:6px 14px;font-family:sans-serif;font-size:12px;font-weight:700;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
                b.onclick = () => {
                    const text = `# ${document.title}\n\nSource: ${location.href}\n\n` + (document.querySelector('article') || document.body).innerText;
                    navigator.clipboard.writeText(text).then(() => {
                        b.innerHTML = '✓ Markdown Copied!';
                        setTimeout(() => { b.innerHTML = '📝 Copy as Markdown'; }, 2500);
                    });
                };
                if (document.body) document.body.appendChild(b);
            })();