#!/usr/bin/env bash
# source this file as superuser!
# suitable to use as a bootstrap.sh provisioning script by vagrant
export USER_=laneh


if [ -z "$0" ]; then
    :
else
	HOME="/home/$0"
fi

yum update -y

mkdir -p ~/tmp ~/bin ~/src


########## linux utilities
yum install -y python-devel nano git git-core ipython dconf-editor meld parcellite


########## linux development
yum install -y "@Development Tools" gcc-c++ dconf-editor
yum install -y open-ssl openssl-libs openssl-devel
yum install -y patch byacc textinfo bison autoconf gettext ncurses-devel
yum install -y libffi-devel  kernel-devel kernel-headers dkms make bzip2 perl ruby ruby-devel rubygems rubygem-execjs


########## VNC Server
yum install -y vnc-server
sudo cp /lib/systemd/system/vncserver@.service /etc/systemd/system/vncserver@:5.service
sudo sed -i 's/<USER>/'$USER_'/g' /lib/systemd/system/vncserver@:5.service


######### Gnome Desktop
sudo yum install -y gnome-session gnome-desktop 
# no automatic updates
gsettings set org.gnome.settings-daemon.plugins.updates active false
# quarterly OS updates/upgrades instead of weekly nags
gsettings set org.gnome.settings-daemon.plugins.updates frequency-get-updates 8640000
gsettings set org.gnome.settings-daemon.plugins.updates frequency-get-upgrades 8640000
gsettings set org.gnome.settings-daemon.plugins.updates frequency-refresh-cache 8640000
gsettings set org.gnome.settings-daemon.plugins.updates frequency-updates-notification 8640000

# parcellite and other notifications in top bar 
sudo yum install -y gnome-tweak-tool
sudo yum install -y gnome-shell-extension-window-list gnome-shell-extension-common gnome-shell-extension-user-theme gnome-shell-extension-launch-new-instance gnome-shell-extension-fedmsg gnome-shell-extension-gpaste gnome-shell-extension-pidgin gnome-shell-extension-remove-bluetooth-icon gnome-shell-extension-remove-volume-icon     

########## dropbox
cd ~ && \
mkdir -p tmp && \
cd ~/tmp && \
wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf - && \
cd .dropbox-dist && \
./dropboxd &


######## web server
yum install -y nginx
systemctl enable nginx.service
systemctl start nginx.service
# rm -rf /usr/share/nginx/html
# ln -fs /vagrant /usr/share/nginx/html

####### GUI desktop
yum install -y "@Administration Tools"
# systemctl enable gdm
# systemctl set-default graphical.target

######## admin
# basics to get started
yum install -y git nano rsync curl wget traceback whois
# database and libs for python bindings


######### Sublime Text 2 ##########
sudo yum install -y pylint
sudo pip install --upgrade pylint
cd ~/tmp && \
rm -f install-sublime-text-x64.sh && \
wget https://gist.githubusercontent.com/hobson/7416d96df16ce4509dae/raw/59d461c6c930b1a8fb5356501c7526f98443cbfa/install-sublime-text-x64.sh && \
chmod +x install-sublime-text-x64.sh && \
./install-sublime-text-x64.sh
# TODO: install package control and pylinter plugin for sublime


# ########## move notification icons to top like in fedora 16
# git clone https://github.com/MrTheodor/gnome-shell-ext-icon-manager.git && \
# cp -r gnome-shell-ext-icon-manager/icon-manager@krajniak.info/ ~/.local/share/gnome-shell/extensions/ && \
# sudo cp gnome-shell-ext-icon-manager/org.gnome.shell.extensions.icon-manager.gschema.xml /usr/share/glib-2.0/schemas/ && \
# sudo glib-compile-schemas /usr/share/glib-2.0/schemas && \
# rm -rf gnome-shell-ext-icon-manager/

########## pip & virtualenvwrapper ################
cd /tmp
# `curl -O` fails
wget http://raw.github.com/pypa/pip/master/contrib/get-pip.py
python get-pip.py
# get the latest version of scipy installed at the system level
pip install virtualenvwrapper
echo '
export WORKON_HOME=$HOME/.virtualenvs
export PROJECT_HOME=$HOME/src
source /usr/bin/virtualenvwrapper.sh 
' >> /etc/profile.d/install_virtualenvwrapper.sh

################ Django apps #################

# postgres
yum install -y postgresql postgresql-devel geos geos-devel
sudo pip install psycopg2

# django-extensions (model_graph)
sudo yum install -y graphviz graphviz-devel

# matplotlib
# sudo yum -y install latex* gtk3-devel pygtk2-devel png agg-devel jpeg8-devel freetype6-devel png12-devel
sudo yum -y install freetype-devel libXft-devel pygtk2-devel tcl-devel tk tk-devel tkinter tkinter-devel python-mtTkinter
sudo pip install pyparsing mock
sudo pip install matplotlib

# scipy 
sudo yum install -y gcc-gfortran blas-static lapack-static numpy-f2py numpy scipy && \
sudo pip install --upgrade numpy && \
sudo pip install --upgrade pytz six && \
sudo pip install --upgrade pandas && \
sudo pip install --upgrade scipy


# ########### ODBC ###############
# # for accessing Microsoft sqlserver databases
# sudo yum install -y unixODBC unixODBC-devel freetds-devel


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


####### git repos
mkdir -p ~/src
mkdir -p ~/bin
mkdir -p ~/tmp
cd ~/src
git config --global user.name "Hobson Lane"
git config --global user.email "$USER_@sharplabs.com"
git config --global receive.denyDeleteCurrent 'warn'
git config --global credential.helper 'cache --timeout 36000'
# attempt to clone repos with write priveleges (will only work if SSH key's have been uploaded to github and stash)
# but fall back to read-only clones if necessary
for repo in "pug.git" "coursera.git" "pycon2015-everyday-ai.git"; do
   git clone "git@github.com:hobson/$repo" || git clone "https://github.com/hobson/$repo" || echo "unable to install $repo"
done
for repo in "sasbd/ssp.git" "sasbd/ssg.git" "bootstrap.git" "sasbd/ansible-django-fedora.git"; do
   # ssh://git@stash.sharplabs.com:7999/sasbd/ansible-django-fedora.git
   git clone "ssh://git@stash.sharplabs.com:7999/$repo" || git clone "http://stash.sharplabs.com:7990/scm/$repo" || echo "unable to install $repo"
done


