servers=[
  {
    :hostname => "master",
    :ip => "192.168.56.100",
    :box => "debian/bookworm64",
    :ram => 4096,
    :cpu => 2,
    :provision => "bootstrap-master.sh"
  },
  {
    :hostname => "box01",
    :ip => "192.168.56.10",
    :box => "debian/bookworm64",
    :ram => 2048,
    :cpu => 1,
    :provision => "bootstrap.sh"
  },
  {
    :hostname => "box02",
    :ip => "192.168.56.20",
    :box => "debian/bookworm64",
    :ram => 2048,
    :cpu => 1,
    :provision => "bootstrap.sh"
  }

]

Vagrant.configure(2) do |config|
    config.vm.synced_folder "./token", "/tmp/vagrant", type: "virtualbox"
    config.ssh.insert_key = false
    servers.each do |machine|
        
        config.vm.define machine[:hostname] do |node|
            node.vm.box = machine[:box]
            node.vm.hostname = machine[:hostname]
            node.vm.network "private_network", ip: machine[:ip]
            if machine[:hostname] == "master"
                node.vm.network "forwarded_port", id: "http", guest: 80, guest_ip: "10.0.2.15", host: 80, host_ip: "127.0.0.1"
                node.vm.network "forwarded_port", id: "https", guest: 443, guest_ip: "10.0.2.15", host: 443, host_ip: "127.0.0.1"
                node.vm.network "forwarded_port", id: "argocd", guest: 443, guest_ip: "192.168.56.100", host: 8443, host_ip: "127.0.0.1"
            end
            node.vm.provision :shell, path: machine[:provision]
            node.vm.provider "virtualbox" do |vb|
			          vb.gui = true
                vb.customize ["modifyvm", :id, "--cpus", machine[:cpu]]
                vb.customize ["modifyvm", :id, "--memory", machine[:ram]]
				        vb.customize ["modifyvm", :id, "--natnet1", "10.0.2.0/24"]
                vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
                vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
            end
        end
    end
end
