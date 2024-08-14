#! /bin/sh

### BEIN INIT INFO
# Provides:		prusa-shelf-control-unit.py
# Required-Start:	$remote_fs $syslog
# Required-Stop:	$remote_fs $syslog
# Default-Start:	2 3 4 5
# Default-Stop:		0 1 6
### END INIT INFO

# If you want a command to always run, put it here

# Carry out specific functions when asked to by the system
case "$1" in
	start)
		echo "Starting prusa-shelf-control-unit.py"
		/home/gidverksted/env/bin/python3 /usr/local/bin/prusa-shelf-control-unit.py &
		;;
	stop)
		echo "Stopping prusa-shelf-control-unit.py"
		pkill -f /usr/local/bin/prusa-shelf-control-unit.py
		;;
	*)
		echo "Usage: /etc/init.d/prusa-shelf-control-unit.sh {start|stop}"
		exit 1
		;;
esac

exit 0

