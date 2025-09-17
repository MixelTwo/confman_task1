@echo off
SETLOCAL
SET test_count=2

IF "%1"=="" (
    echo Error: No index provided.
    echo Usage: test_runner.bat [index]
    exit /B 1
)
IF "%1" LSS "1" (
    echo Error: Index must be between 1 and %test_count%.
    exit /B 1
)
IF "%1" GTR "%test_count%" (
    echo Error: Index must be between 1 and %test_count%.
    exit /B 1
)

SET initial_dir=%CD%

IF EXIST ".\test\" (
    echo Changing directory to: ".\test"
    cd "test"
)

echo Creation of vfsroot folder
mkdir vfsroot
mkdir vfsroot\planets
mkdir vfsroot\stars
mkdir vfsroot\planets\mars_base
mkdir vfsroot\stars\nova_station
mkdir vfsroot\stars\nova_station\main_block

echo 🪐 Welcome to planet Mars. Oxygen tanks are located to the left. > vfsroot\planets\mars_log.txt
echo ☀️ Warning: Alpha-9 star is unstable. Protective glasses required. > vfsroot\stars\star_report.txt
echo 🚀 Mars Base 13 is operational. Next check in 42 orbits. > vfsroot\planets\mars_base\status.txt
echo 🌟 Welcome to Nova Station. Do not feed the black holes. > vfsroot\stars\nova_station\readme.txt
echo 12345 > vfsroot\stars\nova_station\main_block\pwd.txt
echo 2025-09-01 08:00 > vfsroot\dates.txt
echo 09/02/2025 >> vfsroot\dates.txt
echo 01-Sep-2025 14:30 >> vfsroot\dates.txt
echo Sep 04, 2025 21:15 >> vfsroot\dates.txt
echo 2025/09/05 23:59 >> vfsroot\dates.txt
echo in 2 days >> vfsroot\dates.txt
echo 1st of September, 2025 at 08:00 AM >> vfsroot\dates.txt
echo September 2, 2025 >> vfsroot\dates.txt
echo September 1st, 2025 at 14:30 >> vfsroot\dates.txt
echo On the 4th of September, 2025 at 9:15 PM >> vfsroot\dates.txt
echo September 5th, 2025 23:59 >> vfsroot\dates.txt

echo Running emulator
..\dist\emulator.exe vfsroot test%1.bat

echo Clean up
rd vfsroot /S /Q

cd %initial_dir%
ENDLOCAL

echo Test completed