

ps aux | grep mingyiQOServer | grep -v grep | awk '{print $2}' | xargs kill -9 {}


python bin/mingyiQOServer.py conf/index.ini 1>std 2>err &
