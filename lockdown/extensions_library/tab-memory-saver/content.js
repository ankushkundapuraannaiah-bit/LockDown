(function() {
                document.addEventListener('visibilitychange', () => {
                    if (document.hidden) {
                        document.title = '💤 ' + document.title.replace('💤 ', '');
                    } else {
                        document.title = document.title.replace('💤 ', '');
                    }
                });
            })();