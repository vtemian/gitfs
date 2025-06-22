# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Use Bento Ubuntu 24.04 LTS (most trusted third-party box since Canonical stopped providing boxes)
  config.vm.box = "bento/ubuntu-24.04"
  config.vm.box_version = ">= 202404.23.0"
  
  # VM configuration
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "2048"
    vb.cpus = 2
    vb.name = "gitfs-dev"
  end
  
  # Network configuration
  config.vm.network "private_network", type: "dhcp"
  
  # SSH configuration
  config.ssh.forward_agent = true
  config.ssh.insert_key = false
  
  # Synced folders
  config.vm.synced_folder ".", "/vagrant", type: "virtualbox"
  
  # Provisioning
  config.vm.provision "shell", path: "script/provision", privileged: false
  
  # Post-provisioning message
  config.vm.post_up_message = <<-MSG
    GitFS development environment is ready!
    
    To get started:
      vagrant ssh
      cd /vagrant
      source ~/gitfs/bin/activate
      make test
  MSG
end
