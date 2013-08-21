LEO_REPO="git@github.com:slomo/leo2.git"

include $(PROFILE)

#result/%: TPTP-v5.5.0 E-1.8 leo-git-master
#	mkdir -p $@

# TPTP
TPTP-%.tgz:
	wget "http://www.cs.miami.edu/~tptp/TPTP/Distribution/$@"

# unpack TPTP and build index over higher order problems
TPTP-%: TPTP-%.tgz
	tar -xmf "$^"
	find $@ /Problems -iname "*\^?.p" -exec sh -c 'echo -n "$(basename {}), ";  sed -n "s/^% Status   : \(\w\+\)$/\1/p" {}' \; > $@/higherOrderStatus.csv

# E-Prover
E-1.8.tgz:
	wget "http://www4.in.tum.de/~schulz/WORK/E_DOWNLOAD/V_1.8/E.tgz" -O "$@"

E-%: E-%.tgz
	tar -xmf $^
	mv E $@
	cd $@ && ./configure
	cd $@ && make

# SPASS-Prover
SPASS-3.5.tgz:
	wget http://www.spass-prover.org/download/binaries/spass35pclinux64.tgz -O "$@"

SPASS-%: SPASS-3.5.tgz
	tar -xmf $^

# LEO-Prover (from git)
leo-git:
	git clone ${LEO_REPO} $@ --bare

leo-git-%: leo-git
	mkdir $@
	cd $^ && git --work-tree=../$@ checkout $* -- .
	cd $@/src && make opt


leo-git-%/bin/leo: leo-git-%
