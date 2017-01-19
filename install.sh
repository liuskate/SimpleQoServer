# 安装lib下面的依赖包

cd lib
        # [install setuptools]
        python check_setuptools.py
        if [ $? -ne 0 ]; then
                tar xvzf setuptools_20.7.0.tar.gz
                cd cd setuptools-20.7.0/
                        python setup.py build
                        python setup.py install
                cd -
        fi

        # [install singledispatch]
        tar xvzf singledispatch-3.4.0.3.tar.gz 
        cd singledispatch-3.4.0.3
                python setup.py build
                python setup.py install
        cd -

        # [install backports_abc]
        tar xvzf backports_abc-0.5.tar.gz
        cd backports_abc-0.5
                python setup.py build
                python setup.py install
        cd -
        
        # [install certifi]
        tar xzvf certifi.tar.gz  
        cd certifi
                python setup.py build
                python setup.py install
        cd -

        # [install ]
        tar xvzf backports.ssl_match_hostname-3.2a3.tar.gz
        cd backports.ssl_match_hostname-3.2a3
                python setup.py build
                python setup.py install
        cd -


        # [install six]
        tar xvzf six-1.10.0.tar.gz
        cd six-1.10.0
                python setup.py build
                python setup.py install
        cd -


        # [install tornado]
        tar xvzf tornado-4.4.2.tar.gz
        cd tornado-4.4.2
                python setup.py build
                python setup.py install
        cd -
cd -
echo "python require package install done."
