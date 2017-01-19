

ps aux | grep QOServer | grep -v grep | awk '{print $2}' | xargs kill -9 {}


python bin/QOServer.py conf/index.ini 1>std 2>err &
