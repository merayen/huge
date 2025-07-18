export PYTHONMALLOC=debug
export PYTHONASYNCIODEBUG=1
export PYTHONPATH="/home/merayen/d/huge"

if [[ "$VIM_FILE" = "commands.txt" ]]; then
	bash <(sed "${VIM_LINENO}q;d" $VIM_FILE)
else
	py -W default -X faulthandler $VIM_FILE
fi
