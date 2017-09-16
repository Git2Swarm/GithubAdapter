docker container stop github
docker container rm github
docker container run -d -p 7474:5000 --name github github
