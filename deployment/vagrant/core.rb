def provision_bootstrap(config)

  # TODO this will break if the environment contains the ' delimiter,
  # so at some point we need to escape the ' character here and unescape
  # it in bootstrap.sh
  config.vm.provision "shell" do |sh|
    sh.path = "bootstrap.sh"
    sh.privileged = true
  end
end

def provider_libvirt(config)
  config.vm.provider :libvirt do |virt, override|
    override.vm.hostname = "SSGBERK-all"
    override.vm.box = "generic/ubuntu1604"

    unless ENV.fetch('SSGBERK_SHOW_VM', false)
      virt.graphics_type = "none"
    end

    virt.memory = ENV.fetch('SSGBERK_KVM_MEM', 3022)
    virt.cpus = ENV.fetch('SSGBERK_KVM_CPU', 2)

    override.vm.synced_folder "../..", "/home/vagrant/StaticSiteGeneratorBenchmarks", type: "nfs", nfs_udp: false
  end
end

def provider_virtualbox(config)
  config.vm.provider :virtualbox do |vb, override|
    override.vm.hostname = "SSGBERK-all"
    override.vm.box = "ubuntu/xenial64"

    if ENV.fetch('SSGBERK_SHOW_VM', false)
      vb.gui = true
    end

    # Improve Windows VirtualBox DNS resolution speed
    # Addresses mitchellh/vagrant#1807 and matheusrv/StaticSiteGeneratorBenchmarks#1288
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
    vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]

    vb.memory = ENV.fetch('SSGBERK_VB_MEM', 3022)
    vb.cpus = ENV.fetch('SSGBERK_VB_CPU', 2)

    # The VirtualBox file system for shared folders (vboxfs)
    # does not support posix's chown/chmod - these can only
    # be set at mount time, and they are uniform for the entire
    # shared directory. To mitigate the effects, we set the
    # folders and files to 777 permissions.
    # With 777 and owner vagrant *most* of the software works ok.
    # Occasional issues are still possible.
    #
    # See mitchellh/vagrant#4997
    # See http://superuser.com/a/640028/136050

    override.vm.synced_folder "../..", "/home/vagrant/StaticSiteGeneratorBenchmarks"
  end
end
