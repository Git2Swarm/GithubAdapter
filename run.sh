docker container stop github
docker container rm github
docker container run -d \
           -v /home/ubuntu/GithubAdapter/config.json:/src/config.json \
           -p 7474:5000 --name github github
