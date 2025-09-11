@echo off
echo Creation of test folder
mkdir test
mkdir test\planets
mkdir test\stars
mkdir test\planets\mars_base
mkdir test\stars\nova_station

echo 🪐 Welcome to planet Mars. Oxygen tanks are located to the left. > test\planets\mars_log.txt
echo ☀️ Warning: Alpha-9 star is unstable. Protective glasses required. > test\stars\star_report.txt
echo 🚀 Mars Base 13 is operational. Next check in 42 orbits. > test\planets\mars_base\status.txt
echo 🌟 Welcome to Nova Station. Do not feed the black holes. > test\stars\nova_station\readme.txt

echo Running emulator
dist\emulator.exe test start_script2
echo Clean up
rd test /S /Q