cd -P -- "$(dirname -- "$0")"
if [ ! -d "env" ] 
then
	virtualenv env && pip install -r requirements.txt
fi
source env/bin/activate && /usr/bin/google-chrome --window-size=1920,1080 --kiosk --window-position=0,0 http://127.0.0.1:5000  --incognito --disable-pinch --overscroll-history-navigation=0 --disable-features=CrossSiteDocumentBlockingAlways,CrossSiteDocumentBlockingIfIsolating &
source env/bin/activate && python flask/application.py 