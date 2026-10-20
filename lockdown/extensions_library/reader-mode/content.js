(function() {
                if (document.getElementById('lockdown-reader-btn')) return;
                const btn = document.createElement('button');
                btn.id = 'lockdown-reader-btn';
                btn.innerHTML = '📖 Toggle Reader';
                let active = false;
                btn.onclick = () => {
                    active = !active;
                    if (active) {
                        const article = document.querySelector('article') || document.querySelector('main') || document.body;
                        document.body.setAttribute('data-original-html', document.body.innerHTML);
                        document.body.innerHTML = `
                            <div style="max-width: 760px; margin: 40px auto; padding: 20px 30px; font-family: Georgia, serif; line-height: 1.8; font-size: 19px; color: #18150E; background: #FFFDF5;">
                                <div style="margin-bottom: 24px; border-bottom: 1px solid #F0C000; padding-bottom: 12px;">
                                    <h1 style="font-size: 32px; margin-bottom: 8px;">${document.title}</h1>
                                    <div style="font-size: 13px; color: #6B5920;">Source: ${location.hostname}</div>
                                </div>
                                <div id="ld-reader-content">${article.innerHTML}</div>
                            </div>
                        `;
                        document.body.style.background = '#FFFDF5';
                        document.body.appendChild(btn);
                    } else {
                        const orig = document.body.getAttribute('data-original-html');
                        if (orig) document.body.innerHTML = orig;
                    }
                };
                if (document.body) document.body.appendChild(btn);
            })();