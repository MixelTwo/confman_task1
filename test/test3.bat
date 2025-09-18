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


echo "=== Test 1: Create new file ==="
touch /planets/new_file.txt
ls /planets
stat /planets/new_file.txt

echo "=== Test 2: Update modification time (-m) ==="
stat /planets/mars_log.txt
touch -m /planets/mars_log.txt
stat /planets/mars_log.txt

echo "=== Test 3: Update access time (-a) ==="
stat /planets/mars_log.txt
touch -a /planets/mars_log.txt
stat /planets/mars_log.txt

echo "=== Test 4: Set specific time (-d) ==="
touch -d '2025-09-18T12:34:56' /planets/date_file.txt
stat /planets/date_file.txt

echo "=== Test 5: Use reference file (-r) ==="
stat /planets/mars_log.txt
touch -r /planets/mars_log.txt /planets/ref_file.txt
stat /planets/ref_file.txt

echo "=== Test 6: Set time with -t ==="
stat /planets/t_file.txt
touch -t 202509181234.56 /planets/t_file.txt
stat /planets/t_file.txt

echo "=== Test 7: Update multiple files ==="
touch /planets/file1.txt /planets/file2.txt
stat /planets/file1.txt /planets/file2.txt

echo "=== Test 8: Default behavior ==="
touch /planets/mars_log.txt
stat /planets/mars_log.txt


pause
exit