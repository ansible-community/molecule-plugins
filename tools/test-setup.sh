#!/bin/bash
set -euxo pipefail
# Used by Zuul CI to perform extra bootstrapping

sudo dd if=/dev/zero of=/swap.img bs=1024 count=1048576
sudo chmod 600 /swap.img
sudo losetup -f /swap.img
sudo mkswap "$(sudo losetup --associated /swap.img|sed 's,:.*,,')"
sudo swapon "$(sudo losetup --associated /swap.img|sed 's,:.*,,')"

# Platforms coverage:
# Fedora 30 : has vagrant-libvirt no compilation needed
# CentOS 7  : install upstream vagrant rpm and compiles plugin (broken runtime)
# CentOS 8  : install upstream vagrant rpm and compiles plugin (broken runtime)

# Bumping system tox because version from CentOS 7 is too old
# We are not using pip --user due to few bugs in tox role which does not allow
# us to override how is called. Once these are addressed we will switch back
# non-sudo
command -v python3 python

PYTHON=$(command -v python3 python|head -n1)
PKG_CMD=$(command -v dnf yum apt-get|head -n1)

sudo "${PYTHON}" -m pip install -U tox

# === LIBVIRT SETUP ===
sudo systemctl enable --now libvirtd
sudo sed \
    -e 's!^[# ]*unix_sock_rw_perms = .*$!unix_sock_rw_perms = "0777"!g' \
    -e 's!^[# ]*auth_unix_rw = .*$!auth_unix_rw = "polkit"!g' -i /etc/libvirt/libvirtd.conf
# on fedora, looks like virbr0 iface stays there after a restart of libvirt but the network is not
# started back, leading to network failure when the script tries to start the network
if sudo virsh net-list --name | grep -qw default;  then
    sudo virsh net-destroy default
fi
sudo systemctl restart libvirtd
sudo usermod --append --groups libvirt "$(whoami)"
# on some dists, it's auto-started, on some others, it's not
if virsh -c qemu:///system net-list --name --inactive | grep -qw default;  then
    virsh -c qemu:///system net-start default
fi

# only info about the virtualisation is wanted, so no error please.
sudo virt-host-validate qemu || true

# === VAGRANT SETUP ===
# Install Vagrant using their questionable practices, see locked ticket:
# https://github.com/hashicorp/vagrant/issues/11070

# 2.2.10 minimum otherwise setting config.vm.hostname won't work correctly with alpine boxes.
VAGRANT_VERSION=2.2.19

which vagrant || \
    sudo "${PKG_CMD}" install -y vagrant-libvirt || {
        sudo "${PKG_CMD}" install -y https://releases.hashicorp.com/vagrant/${VAGRANT_VERSION}/vagrant_${VAGRANT_VERSION}_x86_64.rpm
    }

if [ -f /etc/os-release ]; then
    source /etc/os-release
    case "$NAME" in
        Ubuntu)
            case "$VERSION_ID" in
                18.04)
                    # ubuntu xenial vagrant is too old so it doesn't support triggers, used by the alpine box
                    sudo apt-get remove --purge -y vagrant
                    wget --no-show-progress https://releases.hashicorp.com/vagrant/${VAGRANT_VERSION}/vagrant_${VAGRANT_VERSION}_x86_64.deb
                    sudo dpkg -i vagrant_${VAGRANT_VERSION}_x86_64.deb
                    ;;
                *)
                    ;;
            esac
            ;;
        Fedora)
            case "$VERSION_ID" in
                31)
                    # https://bugzilla.redhat.com/show_bug.cgi?id=1839651
                    sudo "${PKG_CMD}" upgrade -y --enablerepo=updates-testing --advisory=FEDORA-2020-09c472786c
                    ;;
                *)
                    ;;
            esac
            ;;
        CentOS*)
            # https://github.com/hashicorp/vagrant/issues/11020
            if grep -qi '^CentOS Linux release 8.2.*' /etc/centos-release ; then
                # https://bugs.centos.org/view.php?id=17120
                relver="$(grep -v '^#' /etc/centos-release | awk '{print $4}')"
                sudo sed -i /etc/yum.repos.d/CentOS-Sources.repo -e 's,$contentdir/,,g'
                sudo sed -i /etc/yum.repos.d/CentOS-Sources.repo -e "s,\$releasever,$relver,g"

                sudo dnf install -y rpm-build autoconf libselinux-devel pam-devel bison byacc
                mkdir -p "$HOME/rpmbuild/SOURCES"
                cd "$HOME/rpmbuild/SOURCES"
                # download as root to avoid the "error: [Errno 13] Permission denied: '/var/cache/dnf/expired_repos.json'"
                sudo dnf download --enablerepo=BaseOS-source --disablerepo=epel-source --disablerepo=epel --source krb5-libs
                rpm2cpio krb5-1.17-*.src.rpm | cpio -idv
                # remove patch making incompatible with the openssl bundled with vagrant
                sed -i ./krb5.spec -e 's,Patch.*Use-backported-version-of-OpenSSL-3-KDF-interface.patch,,'
                # depends on previous patch
                sed -i ./krb5.spec -e 's,Patch.*krb5-1.17post2-DES-3DES-fixups.patch,,'
                # not sure why but makes the build fail
                sed -i ./krb5.spec -e 's,Patch.*krb5-1.17post6-FIPS-with-PRNG-and-RADIUS-and-MD4.patch,,'
                rpmbuild -bp krb5.spec --nodeps
                cd ../BUILD/krb5-1.17/src
                # Some flags are missing compared to the spec but these ones seem to be enough
                export CFLAGS="-I/opt/vagrant/embedded/include/ -fPIC -fno-strict-aliasing -fstack-protector-all"
                export LDFLAGS=-L/opt/vagrant/embedded/lib64/
                ./configure --prefix=/opt/vagrant/embedded/
                make
                sudo cp -a lib/crypto/libk5crypto.so.3* /opt/vagrant/embedded/lib64/
            fi
            ;;
        *)
            ;;
    esac
fi

vagrant plugin list | grep vagrant-libvirt || {
    export CONFIGURE_ARGS="with-libvirt-include=/usr/include/libvirt with-libvirt-lib=/usr/lib64"
    if [ -x /opt/vagrant/bin/vagrant ]; then
        # command line from https://github.com/vagrant-libvirt/vagrant-libvirt#installation
        export GEM_HOME=~/.vagrant.d/gems
        export GEM_PATH=$GEM_HOME:/opt/vagrant/embedded/gems
        export PATH=/opt/vagrant/embedded/bin:$PATH
        export CONFIGURE_ARGS='with-ldflags=-L/opt/vagrant/embedded/lib with-libvirt-include=/usr/include/libvirt with-libvirt-lib=/usr/lib'
    fi
    vagrant plugin install vagrant-libvirt
}

if [ -f /etc/debian_version ]; then
    dpkg -l | grep libselinux
    [ -x /usr/bin/aa-enabled ] && echo "Apparmor: $(/usr/bin/aa-enabled)"
else
    rpm -qa | grep libselinux
fi

vagrant version
vagrant global-status

vagrant plugin list | tee >(grep -q "No plugins installed." && {
    echo "FATAL: Vagrant is not usable without any provider plugins."
    exit 1
})

timeout 600 ./tools/create_testbox.sh
