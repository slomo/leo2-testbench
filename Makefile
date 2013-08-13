LEO_REPO="git@github.com:slomo/leo2.git"

include $(PROFILE)

#result/%: TPTP-v5.5.0 E-1.8 leo-git-master
#	mkdir -p $@

TPTP-%.tgz:
	wget "http://www.cs.miami.edu/~tptp/TPTP/Distribution/$@"

TPTP-%: TPTP-%.tgz
	tar -xmf "$^"

E-1.8.tgz:
	wget "http://www4.in.tum.de/~schulz/WORK/E_DOWNLOAD/V_1.8/E.tgz" -O "$@"

E-%: E-%.tgz
	tar -xmf $^
	mv E $@
	cd $@ && ./configure
	cd $@ && make


leo-git:
	git clone ${LEO_REPO} $@ --bare

leo-git-%: leo-git
	mkdir $@
	cd $^ && git --work-tree=../$@ checkout $* -- .
	cd $@/src && make opt


leo-git-%/bin/leo: leo-git-%
