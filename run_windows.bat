setlocal
cd /d %~dp0
start chrome --kiosk http://127.0.0.1:5000 --incognito --disable-pinch --overscroll-history-navigation=0 --disable-features=CrossSiteDocumentBlockingAlways,CrossSiteDocumentBlockingIfIsolating
rem start chrome http://127.0.0.1:5000  --disable-features=CrossSiteDocumentBlockingAlways,CrossSiteDocumentBlockingIfIsolating
C:\Users\%USERNAME%\Anaconda2\Scripts\activate.bat gpt-2 && cd /d flask && python application.py