#!/bin/sh

`cp -f /home/eaizhao/crius.py ~/.local/bin/`
if [ $? -eq 0 ];then
    echo 'fetch crius.py successfully'
else
    echo 'Cannot get crius.py!'
    exit
fi

`python3 --version > /dev/null`
if [ $? -eq 0 ];then
    echo 'python3 is ready'
else
    `sed -i '$a module add python/3.6.0'  ~/.cshrc`
fi
`sed  -i '$a alias crius python3 ~\/.local\/bin\/crius.py' ~/.cshrc`


