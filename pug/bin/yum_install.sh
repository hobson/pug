# don't forget these sort of things to do on the connecting server
#
# ssh-copy-id
# ssh-keygen
# rsync there:.bashrc here:.bashrc

mkdir -p $HOME/bin
mkdir -p /usr/src/projects
sudo chmod o+w /usr/src/projects/
ln -s /usr/src/projects $HOME/src

sudo yum group install -y "Development Tools" "Development Libraries"
sudo yum install -y git nano curl wget traceback whois
sudo yum install -y python-devel libxml2-devel libxslt-devel gcc-gfortran python-scikit-learn 
sudo yum install -y freetds freetds-devel postgresql postgresql-server postgresql-libs postgresql-devel

cd bin
curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
sudo python get-pip.py

cd $HOME/src
git clone git@github.com:hobsonlane/pug.git
cd pug
git pull
sudo pip install -r requirements.txt 


