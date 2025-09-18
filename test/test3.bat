echo "=== Test 1: Copy a single file to a new file ==="
cp /planets/mars_log.txt /planets/mars_log_copy.txt
ls /planets
cat /planets/mars_log_copy.txt

echo "=== Test 2: Copy a single file into a directory ==="
cp /stars/star_report.txt /planets
ls /planets
cat /planets/star_report.txt

echo "=== Test 3: Copy a directory recursively ==="
cp -r /stars/nova_station /planets
ls /planets
ls /planets/nova_station
cat /planets/nova_station/readme.txt

echo "=== Test 4: Copy directory contents only (trailing slash) ==="
cp -r /planets/mars_base/ /stars
ls /stars
cat /stars/status.txt

echo "=== Test 5: No-clobber (-n) and interactive (-i) ==="
cp -n /planets/mars_log.txt /planets/mars_log_copy.txt
cp -i /planets/mars_log.txt /planets/mars_log_copy.txt

echo "=== Test 6: Multiple sources to a directory ==="
cp -v /planets/mars_log.txt /stars/star_report.txt /dates.txt /planets
ls /planets
cat /planets/dates.txt

pause
exit