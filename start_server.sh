if [[ $HOSTNAME =~ .*MacBook.* ]]; then
    cd /Users/thomas/Work/flask/fotommy
    flask run --port 5000
else
    cd /home/pi/code/flask/fotommy
    ./bkg flask run --host 0.0.0.0 --port 23457 --with-threads
fi