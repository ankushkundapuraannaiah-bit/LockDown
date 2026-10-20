(function() {
                const ct = document.contentType || '';
                const isJson = ct.includes('json') || (document.body && document.body.children.length === 1 && document.body.firstElementChild.tagName === 'PRE');
                if (!isJson) return;
                try {
                    const text = (document.body.innerText || '').trim();
                    if ((text.startsWith('{') && text.endsWith('}')) || (text.startsWith('[') && text.endsWith(']'))) {
                        const data = JSON.parse(text);
                        document.body.innerHTML = `
                            <div style="background: #18150E; color: #FFDE59; font-family: 'Consolas', 'Courier New', monospace; padding: 24px; min-height: 100vh; font-size: 14px;">
                                <div style="margin-bottom: 16px; border-bottom: 1px solid #4A3E1F; padding-bottom: 10px; display: flex; justify-content: space-between;">
                                    <span style="font-weight: 800; color: #E67300;">🗂️ JSON Inspector Active</span>
                                    <span style="color: #FAF6ED; font-size: 12px;">Formatted JSON (${Object.keys(data).length} root keys)</span>
                                </div>
                                <pre style="white-space: pre-wrap; word-break: break-all; color: #FAF6ED;">${JSON.stringify(data, null, 2)}</pre>
                            </div>
                        `;
                    }
                } catch(e) {}
            })();