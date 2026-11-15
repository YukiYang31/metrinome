# Run from the repository root.
sudo docker build -t apcmetrinome/dockerapc -f replication/Dockerfile .
sudo docker login
sudo docker push apcmetrinome/dockerapc
sudo docker run -it apcmetrinome/dockerapc

