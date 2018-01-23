#!/bin/sh

`cp -f /home/eaizhao/crius.py ~/.local/bin/`
if [ $? -eq 0 ];then
    echo 'fetch crius.py successfully'
else
    echo 'Cannot get crius.py!'
    exit
fi

`sed  -i '$a alias crius python3 ~\/.local\/bin\/crius.py' ~/.cshrc`
