date
date --date='2147483647'
date --date='2147483647' -I
date --date='not a date'
date --date '12:45'
date -f dates.txt
date -f dates.txt -R

head planets/mars_base/status.txt
head planets/mars_base/status.txt stars/nova_station/readme.txt stars/star_report.txt
head -q planets/mars_log.txt planets/mars_base/status.txt
head -c 10 planets/mars_log.txt planets/mars_base/status.txt
head -c -10 planets/mars_log.txt planets/mars_base/status.txt
head --lines="1kB" dates.txt
head -n 3 dates.txt
head -n -3 dates.txt


history
history 4
history -d 1
history 4
history -w hist.txt
head hist.txt
history -c
history
history -n hist.txt
history
history -s ls "cd ./planets"
history 5

pause
exit