#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

sudo apt-get update
sudo apt-get -y install ca-certificates curl gnupg open-iscsi git conntrackd conntrack
#sudo apt-get -y dist-upgrade

sudo systemctl start iscsid

sudo install -m 0755 -d /etc/apt/keyrings
#curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
#sudo chmod a+r /etc/apt/keyrings/docker.gpg
#echo \
#  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
#  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
#  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null


#sudo apt-get update
#sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin  || exit 1
#sudo docker ps

mkdir -p /etc/rancher/k3s

#cat <<EOF >>/etc/rancher/k3s/registries.yaml
#mirrors:
#  docker.io:
#    endpoint:
#      - "https://reg.ntl.nc/v2/proxy/"
#EOF

sudo apt-get -y autoremove

#wget https://github.com/k3s-io/k3s/releases/download/v1.30.5%2Bk3s1/k3s -q --show-progress
wget https://github.com/k3s-io/k3s/releases/download/v1.33.0%2Bk3s1/k3s -q --show-progress
chmod +x k3s && sudo mv k3s /usr/local/bin/ 

cd /home/vagrant && echo "alias k=kubectl" >> .bashrc && source .bashrc
wget https://dl.k8s.io/release/v1.33.0/bin/linux/amd64/kubectl && chmod +x kubectl && sudo mv kubectl /usr/local/bin/
wget https://get.helm.sh/helm-v3.18.0-linux-amd64.tar.gz && tar -zxvf helm-v3.18.0-linux-amd64.tar.gz && sudo mv linux-amd64/helm /usr/local/bin/

sudo touch /lib/systemd/system/k3s.service
sudo cat <<EOF >>/lib/systemd/system/k3s.service
[Unit]
Description=k3s server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/k3s server --bind-address 192.168.56.100 --disable-network-policy --disable-kube-proxy --flannel-backend none --disable traefik --disable servicelb --disable local-storage

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable k3s.service && sudo systemctl start k3s.service

echo "k3s started"
sleep 15
cp /var/lib/rancher/k3s/server/node-token /tmp/vagrant/node-token
sudo mkdir /home/vagrant/.kube && sudo cp /etc/rancher/k3s/k3s.yaml /home/vagrant/.kube/config  && sudo chown vagrant:vagrant /home/vagrant/.kube/config
sleep 15
helm upgrade --install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx --namespace ingress-nginx --create-namespace --set controller.service.loadBalancerIP=10.0.2.15
helm repo add argo https://argoproj.github.io/argo-helm
helm upgrade --install argocd argo/argo-cd --namespace argocd --create-namespace
sleep 15
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d > /home/vagrant/argocd.pass

KUBESEAL_VERSION='0.29.0'
# Install Bitnami's Sealed Secrets controller in the sealed-secrets namespace.
helm repo add bitnami-labs https://bitnami-labs.github.io/sealed-secrets/
helm install -n sealed-secrets --create-namespace --wait --version ${KUBESEAL_VERSION:?} sealed-secrets-controller bitnami-labs/sealed-secrets
# for selead-secret first install: kubectl get secret -n sealed-secrets -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > /tmp/vagrant/sealed-secret-key.yaml
# if second install/cluster re-install: kubectl apply -n sealed-secrets -f /tmp/vagrant/sealed-secret-key.yaml
# Beware this is for test purpose. Do not expose your keys if you're on a production cluster.

wget "https://github.com/bitnami-labs/sealed-secrets/releases/download/v${KUBESEAL_VERSION:?}/kubeseal-${KUBESEAL_VERSION:?}-linux-amd64.tar.gz"
tar -xvzf kubeseal-${KUBESEAL_VERSION:?}-linux-amd64.tar.gz kubeseal
sudo install -m 755 kubeseal /usr/local/bin/kubeseal
# to get the public cert: kubeseal --controller-namespace sealed-secrets --controller-name sealed-secrets-controller --fetch-cert

#install cillium CNI
helm repo add cilium https://helm.cilium.io/
helm repo update
helm install cilium cilium/cilium

#echo "nameserver 8.8.8.8" | sudo tee    /etc/resolv.conf
#echo "nameserver 1.1.1.1" | sudo tee -a /etc/resolv.conf
