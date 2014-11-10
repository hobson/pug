# source this file as superuser!

########## linux utilities
sudo yum install -y python-devel nano git git-core ipython dconf-editor meld parcellite

########## linux development
sudo yum install -y "@Development Tools" gcc-c++ dconf-editor
sudo yum install -y open-ssl openssl-libs openssl-devel
sudo yum install -y patch byacc textinfo bison autoconf gettext ncurses-devel
sudo yum install -y libffi-devel  kernel-devel kernel-headers dkms make bzip2 perl ruby ruby-devel rubygems rubygem-execjs

######### gnome tweaks like notification in top 
yum install gnome-tweak-tool gnome-shell-extension*


########## move notification icons to top like in fedora 16
git clone https://github.com/MrTheodor/gnome-shell-ext-icon-manager.git && \
cp -r gnome-shell-ext-icon-manager/icon-manager@krajniak.info/ ~/.local/share/gnome-shell/extensions/ && \
sudo cp gnome-shell-ext-icon-manager/org.gnome.shell.extensions.icon-manager.gschema.xml /usr/share/glib-2.0/schemas/ && \
sudo glib-compile-schemas /usr/share/glib-2.0/schemas && \
rm -rf gnome-shell-ext-icon-manager/


########## scipy
sudo yum install gcc-gfortran blas-static lapack-static numpy-f2py numpy scipy && pip install --upgrade scipy


########## dropbox
cd ~ && \
mkdir -P tmp && \
cd ~/tmp && \
wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf - && \
cd .dropbox-dist && \
./dropboxd &


########## node
# node runs javascript apps on the server (instead of client), like bower
wget http://nodejs.org/dist/v0.11.14/node-v0.11.14.tar.gz && \
tar -zxvf node-v0.11.14.tar.gz && \
rm -f node-v0.11.14.tar.gz && \
cd node-v0.11.14/ && \
./configure && \
make && \
sudo make install


########## bower
# bower manages webapp javascript libraries and their versions (jquery, d3.js, bootstrap,...)
# TODO: detect latest version and install it
npm install bower


# jekyll is a static website templating system
# github.io free hosting preprocesses all HTML and javascript with jekyll
gem install jekyll
jekyll new static-jekyll-site
cd static-jekyll-site
jekyll serve
