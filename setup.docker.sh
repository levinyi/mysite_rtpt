docker build -t levindu11/mysite_rtpt:latest .
docker save -o mysite_rtpt.tar levindu11/mysite_rtpt:latest 
scp mysite_rtpt.tar dushiyi@101.201.235.247:/home/dushiyi/mysite_rtpt/

# docker load -i mysite_rtpt.tar