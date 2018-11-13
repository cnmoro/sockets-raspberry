cd libs
sudo apt-get install build-essential python-dev
sudo python3 setup.py install
sudo apt-get install python-pip
cd ..
sudo chmod +x rasp-socket-threads.py
python rasp-socket-threads.py
